import asyncio  # noqa: F401
import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Protocol, Tuple, Type, cast

from litellm import acompletion, RateLimitError
import litellm
from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionToolParam,
    ChatCompletionUserMessageParam,
)
from openai.types.shared_params.function_definition import FunctionDefinition
from pydantic import BaseModel
from rich.console import Console as RichConsoleClass

from qx.cli.theme import themed_console
from qx.core.mcp_manager import MCPManager
from qx.core.plugin_manager import PluginManager
from qx.core.llm_components.prompts import load_and_format_system_prompt
from qx.core.llm_components.config import configure_litellm
from qx.core.llm_components.streaming import StreamingHandler
from qx.core.llm_components.tools import ToolProcessor


class ConsoleProtocol(Protocol):
    def print(self, *args, **kwargs): ...


RichConsole = ConsoleProtocol  # Type alias for backward compatibility

logger = logging.getLogger(__name__)


class QXLLMAgent:
    """
    Encapsulates the LLM client and manages interactions, including tool calling.
    """

    def __init__(
        self,
        model_name: str,
        system_prompt: str,
        tools: List[Tuple[Callable, Dict[str, Any], Type[BaseModel]]],
        console: RichConsole,
        temperature: float = 0.7,
        max_output_tokens: Optional[int] = None,
        reasoning_effort: Optional[str] = None,
        enable_streaming: bool = True,
        agent_name: Optional[str] = None,
        agent_color: Optional[str] = None,
        agent_config: Optional[Dict[str, Any]] = None,
    ):
        self.model_name = model_name
        self.system_prompt = system_prompt
        self.console = console
        self.temperature = temperature
        self.max_output_tokens = max_output_tokens
        self.reasoning_effort = reasoning_effort
        self.enable_streaming = enable_streaming
        self.agent_name = agent_name
        self.agent_color = agent_color
        self.can_delegate = agent_config.get('can_delegate', False) if agent_config else False

        self._tool_functions: Dict[str, Callable] = {}
        self._openai_tools_schema: List[ChatCompletionToolParam] = []
        self._tool_input_models: Dict[str, Type[BaseModel]] = {}
        # Message caching can be implemented here if needed

        for func, schema, input_model_class in tools:
            self._tool_functions[func.__name__] = func

            # Handle different schema formats (regular plugins vs MCP tools)
            if "function" in schema:
                # MCP tools format: {"type": "function", "function": {...}}
                function_def = schema["function"]
            else:
                # Regular plugins format: {"name": ..., "description": ..., "parameters": ...}
                function_def = schema

            # Create a complete function definition with all required fields
            complete_function_def = dict(function_def)  # Start with original
            complete_function_def["name"] = function_def.get("name", func.__name__)
            complete_function_def["description"] = function_def.get(
                "description", f"Tool function {func.__name__}"
            )

            self._openai_tools_schema.append(
                ChatCompletionToolParam(
                    type="function",
                    function=FunctionDefinition(**complete_function_def),  # type: ignore
                )
            )
            self._tool_input_models[func.__name__] = input_model_class
            logger.debug(
                f"QXLLMAgent: Registered tool function '{func.__name__}' with schema name '{function_def.get('name')}'"
            )

        # Configure LiteLLM
        configure_litellm()

        # Initialize handlers
        self._streaming_handler = StreamingHandler(
            self._make_litellm_call,
            self._process_tool_calls_and_continue,
            console,
        )

        # Set agent context for streaming handler if available
        if self.agent_name:
            self._streaming_handler.set_agent_context(self.agent_name, self.agent_color)

            # Set global agent context for approval handlers in plugins
            from qx.core.approval_handler import set_global_agent_context

            set_global_agent_context(self.agent_name, self.agent_color)

        # Use standard tool processor
        self._tool_processor = ToolProcessor(
            self._tool_functions, self._tool_input_models, self.console, self.run
        )

        logger.info(f"QXLLMAgent initialized with model: {self.model_name}")
        logger.info(f"Registered {len(self._tool_functions)} tool functions.")
        
        # Log agent context for debugging
        if self.agent_name:
            logger.debug(f"Agent Context: name={self.agent_name}, color={self.agent_color}, tools={len(self._tool_functions)}")

    async def _make_litellm_call(self, chat_params: Dict[str, Any]) -> Any:
        """Make LiteLLM API call with custom retry logic for rate limit errors."""
        # Remove None values to clean up parameters
        clean_params = {k: v for k, v in chat_params.items() if v is not None}
        
        # Log if debug enabled
        if os.environ.get("QX_LOG_LEVEL", "").upper() == "DEBUG":
            logger.debug(f"Making LiteLLM call with model: {clean_params.get('model')}")
            logger.debug(f"Retries: {clean_params.get('num_retries', 0)}")
            logger.debug(f"Timeout: {clean_params.get('timeout', 'default')}")
        
        # Custom retry logic for rate limit errors
        max_retries = 3
        base_delay = 2.0  # Starting with 2 seconds as requested
        
        for attempt in range(max_retries + 1):
            try:
                return await acompletion(**clean_params)
            except RateLimitError as e:
                if attempt < max_retries:
                    # Calculate delay with exponential backoff
                    delay = base_delay * (attempt + 1)  # 2s, 4s, 6s
                    
                    logger.warning(f"Rate limit error encountered: {e}")
                    logger.info(f"Retrying in {delay} seconds... (Attempt {attempt + 1}/{max_retries})")
                    
                    # Show user-friendly message
                    themed_console.print(f"[yellow]Rate limit reached. Retrying in {delay} seconds... (Attempt {attempt + 1}/{max_retries})[/yellow]")
                    
                    # Wait before retrying
                    await asyncio.sleep(delay)
                else:
                    # All retries exhausted
                    logger.error(f"Rate limit error after {max_retries} retries: {e}")
                    themed_console.print(f"[error]Rate limit error after {max_retries} retries. Please try again later.[/error]")
                    raise
            except Exception as e:
                # Check if this is a rate limit error that wasn't caught properly
                error_str = str(e)
                error_type = type(e).__name__
                
                # Log the actual exception type for debugging
                logger.debug(f"Caught exception type: {error_type}, message: {error_str}")
                
                # Check for various rate limit indicators
                is_rate_limit = any([
                    "429" in error_str,
                    "RESOURCE_EXHAUSTED" in error_str,
                    "rate limit" in error_str.lower(),
                    "quota" in error_str.lower() and "exceeded" in error_str.lower(),
                    # Check if it's a litellm wrapped exception
                    hasattr(litellm, error_type) and "RateLimit" in error_type
                ])
                
                if is_rate_limit and attempt < max_retries:
                    # This is likely a rate limit error
                    delay = base_delay * (attempt + 1)  # 2s, 4s, 6s
                    
                    logger.warning(f"Rate limit error detected (type: {error_type}): {e}")
                    logger.info(f"Retrying in {delay} seconds... (Attempt {attempt + 1}/{max_retries})")
                    
                    # Show user-friendly message
                    themed_console.print(f"[yellow]Rate limit reached. Retrying in {delay} seconds... (Attempt {attempt + 1}/{max_retries})[/yellow]")
                    
                    # Wait before retrying
                    await asyncio.sleep(delay)
                else:
                    # Let other exceptions bubble up (they'll be handled by litellm's built-in retry)
                    raise


    async def _process_tool_calls_and_continue(
        self, response_message, messages, user_input, recursion_depth
    ):
        """Delegate to tool processor."""
        return await self._tool_processor.process_tool_calls_and_continue(
            response_message, messages, user_input, recursion_depth
        )


    def _serialize_messages_efficiently(
        self, messages: List[ChatCompletionMessageParam]
    ) -> List[Dict[str, Any]]:
        """
        Efficiently serialize messages for LLM API calls.
        Simplified version since unified workflow handles message persistence.
        """
        serialized = []
        for msg in messages:
            if hasattr(msg, 'model_dump'):
                serialized.append(msg.model_dump())
            elif isinstance(msg, dict):
                serialized.append(msg)
            else:
                # Fallback for other message types
                serialized.append({"role": "user", "content": str(msg)})
        return serialized

    async def run(
        self,
        user_input: str,
        message_history: Optional[List[ChatCompletionMessageParam]] = None,
        add_user_message_to_history: bool = True,
        _recursion_depth: int = 0,
    ) -> Any:
        """
        Runs the LLM agent, handling conversation turns and tool calls.
        Returns the final message content or tool output.
        """
        # Log recursion depth to help with debugging
        if _recursion_depth > 0:
            logger.debug(f"LLM run() called with recursion depth: {_recursion_depth}")
        
        from qx.core.constants import MAX_TOOL_RECURSION_DEPTH
        
        # Warn when approaching recursion limit (70% of max)
        warning_threshold = int(MAX_TOOL_RECURSION_DEPTH * 0.7)
        if _recursion_depth >= warning_threshold:
            logger.warning(
                f"High recursion depth detected: {_recursion_depth}/{MAX_TOOL_RECURSION_DEPTH}. Possible infinite tool calling loop."
            )
        # Prevent infinite recursion in tool calling
        if _recursion_depth > MAX_TOOL_RECURSION_DEPTH:
            error_msg = f"Maximum recursion depth ({MAX_TOOL_RECURSION_DEPTH}) exceeded in tool calling"
            logger.error(error_msg)
            self.console.print(f"[error]Error:[/] {error_msg}")
            # Create a response that doesn't continue the tool calling loop
            error_content = "I apologize, but I've reached the maximum recursion depth while processing tool calls. This suggests there may be an issue with the tool calling logic that's causing an infinite loop. Please try rephrasing your request or breaking it into smaller steps."
            final_message = cast(
                ChatCompletionMessageParam,
                {
                    "role": "assistant",
                    "content": error_content,
                },
            )
            error_messages = list(message_history) if message_history else []
            error_messages.append(final_message)
            return QXRunResult(error_content, error_messages)
        messages: List[ChatCompletionMessageParam] = []

        # Only add system prompt if not already present in message history
        has_system_message = message_history and any(
            (msg.get("role") if isinstance(msg, dict) else getattr(msg, "role", None))
            == "system"
            for msg in message_history
        )

        if not has_system_message:
            messages.append(
                cast(
                    ChatCompletionSystemMessageParam,
                    {"role": "system", "content": self.system_prompt},
                )
            )

        if message_history:
            messages.extend(message_history)

        # Special handling for continuation after tool calls
        if user_input == "__CONTINUE_AFTER_TOOLS__":
            # Don't add any user message, just continue with existing messages
            pass
        else:
            # Only add user message if not already in the last position of message history and not empty
            should_add_user_message = (
                user_input.strip() != "" and add_user_message_to_history
            )  # Don't add empty messages
            if should_add_user_message and message_history:
                # Check if the last message is already this user input
                last_msg = message_history[-1] if message_history else None
                if last_msg:
                    # Handle both dict and Pydantic model cases
                    msg_role = (
                        last_msg.get("role")
                        if isinstance(last_msg, dict)
                        else getattr(last_msg, "role", None)
                    )
                    msg_content = (
                        last_msg.get("content")
                        if isinstance(last_msg, dict)
                        else getattr(last_msg, "content", None)
                    )
                    if msg_role == "user" and msg_content == user_input:
                        should_add_user_message = False

            if should_add_user_message:
                messages.append(
                    cast(
                        ChatCompletionUserMessageParam,
                        {"role": "user", "content": user_input},
                    )
                )

        # Log the last message being sent if QX_LOG_SENT is set
        if os.getenv("QX_LOG_SENT") and messages:
            # Skip logging if this is a continuation after tools (to avoid duplicate logging)
            if user_input == "__CONTINUE_AFTER_TOOLS__":
                # The tool responses were already logged when they were added
                pass
            else:
                last_message = messages[-1]
                # Convert to dict if it's a BaseModel
                if isinstance(last_message, BaseModel):
                    last_message = last_message.model_dump()
                logger.info(
                    f"Sending message to LLM:\n{json.dumps(last_message, indent=2)}"
                )

                # Also log available tools on first user message
                if last_message.get("role") == "user" and self._openai_tools_schema:
                    logger.info(f"Available tools ({len(self._openai_tools_schema)}):")
                    for tool in self._openai_tools_schema[:3]:  # Show first 3 tools
                        tool_dict: Dict[str, Any]
                        if hasattr(tool, "get"):
                            tool_dict = tool  # type: ignore
                        elif hasattr(tool, "items"):
                            tool_dict = dict(tool)
                        else:
                            tool_dict = vars(tool) if hasattr(tool, "__dict__") else {}
                        logger.info(
                            f"  - {tool_dict.get('function', {}).get('name', 'unknown')}"
                        )

        # Parameters for the chat completion
        # Optimize message serialization to avoid repeated model_dump() calls
        serialized_messages = self._serialize_messages_efficiently(messages)

        chat_params: Dict[str, Any] = {
            "model": self.model_name,
            "messages": serialized_messages,
            "temperature": self.temperature,
            "tools": self._openai_tools_schema if self._openai_tools_schema else None,
            "tool_choice": "auto" if self._openai_tools_schema else None,
        }

        if self.max_output_tokens is not None:
            chat_params["max_tokens"] = self.max_output_tokens

        # Handle reasoning effort (for o1 models)
        if self.reasoning_effort is not None:
            chat_params["reasoning_effort"] = self.reasoning_effort

        # Add timeout
        chat_params["timeout"] = float(os.environ.get("QX_REQUEST_TIMEOUT", "120"))

        # Add retry configuration
        chat_params["num_retries"] = int(os.environ.get("QX_NUM_RETRIES", "3"))


        try:
            if self.enable_streaming:
                # Add streaming parameter
                chat_params["stream"] = True

                # Only add empty line for initial responses, not for tool continuations
                if user_input != "__CONTINUE_AFTER_TOOLS__":
                    # Add an empty line before the streaming response starts
                    from rich.console import Console

                    Console().print("")

                return await self._streaming_handler.handle_streaming_response(
                    chat_params, messages, user_input, _recursion_depth
                )
            else:
                response = await self._make_litellm_call(chat_params)
                response_message = response.choices[0].message

                # Log the received message if QX_LOG_RECEIVED is set
                if os.getenv("QX_LOG_RECEIVED"):
                    response_dict = {
                        "role": response_message.role,
                        "content": response_message.content,
                    }
                    if response_message.tool_calls:
                        response_dict["tool_calls"] = [
                            {
                                "id": tc.id,
                                "type": tc.type,
                                "function": {
                                    "name": tc.function.name,
                                    "arguments": tc.function.arguments,
                                },
                            }
                            for tc in response_message.tool_calls
                        ]
                    logger.info(
                        f"Received message from LLM:\n{json.dumps(response_dict, indent=2)}"
                    )

                messages.append(response_message)

                if response_message.tool_calls:
                    return await self._tool_processor.process_tool_calls_and_continue(
                        response_message, messages, user_input, _recursion_depth
                    )
                else:
                    return QXRunResult(response_message.content or "", messages)

        except Exception as e:
            logger.error(f"Error during LLM chat completion: {e}", exc_info=True)
            from rich.console import Console

            themed_console.print(f"[error]Error:[/] LLM chat completion: {e}")
            return None

    async def cleanup(self):
        """Clean up resources."""
        # Simplified cleanup since unified workflow handles message persistence
        logger.debug(f"🧹 Cleaning up QXLLMAgent: {getattr(self, 'agent_name', 'unknown')}")


class QXRunResult:
    def __init__(
        self,
        output_content: str,
        all_msgs: List[ChatCompletionMessageParam],
    ):
        self.output = output_content
        self._all_messages = all_msgs

    def all_messages(self) -> List[ChatCompletionMessageParam]:
        return self._all_messages


def initialize_llm_agent(
    model_name_str: str,
    console: Optional[RichConsole],
    mcp_manager: MCPManager,  # New parameter
    enable_streaming: bool = True,
    agent_config: Optional[Any] = None,  # New parameter for agent configuration
    agent_mode: str = "single",  # Agent mode (always single)
    current_agent_name: str = "",  # Current agent name
) -> Optional[QXLLMAgent]:
    """
    Initializes the QXLLMAgent with system prompt and discovered tools.
    Supports both legacy (markdown) and agent-based prompt loading.

    Args:
        model_name_str: Model name string
        console: Console for output
        mcp_manager: MCP manager instance
        enable_streaming: Whether to enable streaming
        agent_config: Optional agent configuration for agent-based initialization
        agent_mode: Type of agent (always single)
        current_agent_name: Name of the current agent
    """
    # Will generate discovered tools context after loading tools

    # Use agent configuration for model parameters if available
    if agent_config is not None:
        try:
            # Override model parameters from agent config
            model_name_str = getattr(agent_config.model, "name", model_name_str)
            temperature = getattr(agent_config.model.parameters, "temperature", 
                float(os.environ.get("QX_MODEL_TEMPERATURE", "0.7")))
            max_output_tokens = getattr(
                agent_config.model.parameters, "max_tokens", 
                int(os.environ.get("QX_MODEL_MAX_TOKENS", "4096"))
            )
            reasoning_effort = getattr(
                agent_config.model.parameters, "reasoning_budget", 
                os.environ.get("QX_MODEL_REASONING_EFFORT")
            )
            logger.info(f"Using agent-based model configuration: {model_name_str}")
        except AttributeError as e:
            logger.warning(
                f"Could not extract model config from agent: {e}. Using environment defaults."
            )
            # Fall back to environment variables
            temperature = float(os.environ.get("QX_MODEL_TEMPERATURE", "0.7"))
            max_output_tokens = int(os.environ.get("QX_MODEL_MAX_TOKENS", "4096"))
            reasoning_effort = os.environ.get("QX_MODEL_REASONING_EFFORT")
    else:
        # Use environment variables (legacy behavior)
        temperature = float(os.environ.get("QX_MODEL_TEMPERATURE", "0.7"))
        max_output_tokens = int(os.environ.get("QX_MODEL_MAX_TOKENS", "4096"))
        reasoning_effort = os.environ.get("QX_MODEL_REASONING_EFFORT")

    plugin_manager = PluginManager()
    try:
        import sys

        src_path = Path(__file__).parent.parent.parent
        if str(src_path) not in sys.path:
            sys.path.insert(0, str(src_path))

        registered_tools = plugin_manager.load_plugins(plugin_package_path="qx.plugins")
        if not registered_tools:
            logger.warning(
                "No tools were loaded by the PluginManager. Agent will have no tools."
            )
        else:
            logger.info(f"Loaded {len(registered_tools)} tools via PluginManager.")

    except Exception as e:
        logger.error(f"Failed to load plugins: {e}", exc_info=True)
        if console:
            console.print(f"[error]Error:[/] Failed to load tools: {e}")
        registered_tools = []

    # Add MCP tools to the list of registered tools
    mcp_tools = mcp_manager.get_active_tools()
    if mcp_tools:
        registered_tools.extend(mcp_tools)
        logger.info(f"Added {len(mcp_tools)} tools from active MCP servers.")

    # Generate discovered tools context now that all tools are loaded
    from qx.core.llm_components.prompts import generate_discovered_tools_context, generate_discovered_models_context, generate_discovered_agents_context
    discovered_tools_context = generate_discovered_tools_context(registered_tools)
    
    # Generate discovered models context
    discovered_models_context = generate_discovered_models_context()
    
    # Generate discovered agents context
    discovered_agents_context = generate_discovered_agents_context()
    
    # Load system prompt (agent-based or legacy) with agent context, discovered tools, discovered models, and discovered agents
    system_prompt_content = load_and_format_system_prompt(
        agent_config, agent_mode, current_agent_name, discovered_tools_context, discovered_models_context, discovered_agents_context
    )

    try:
        # Validate reasoning_effort if provided
        if reasoning_effort and reasoning_effort.lower() not in [
            "high",
            "medium",
            "low",
            "none",
        ]:
            logger.warning(
                f"Invalid value for reasoning_effort: '{reasoning_effort}'. Expected 'high', 'medium', 'low', or 'none'. Setting to None."
            )
            reasoning_effort = None
        elif reasoning_effort and reasoning_effort.lower() == "none":
            reasoning_effort = None  # Disable reasoning when "none" is specified

        # Use a default console if none provided
        effective_console = console if console is not None else RichConsoleClass()

        # Extract agent name and color from agent config
        agent_name = None
        agent_color = None
        if agent_config is not None:
            try:
                agent_name = getattr(agent_config, "name", None)
                agent_color = getattr(agent_config, "color", None)
                logger.debug(
                    f"Agent context: name='{agent_name}', color='{agent_color}'"
                )
            except AttributeError:
                logger.debug("No agent name/color found in config")

        # Filter tools based on agent configuration
        filtered_tools = registered_tools
        if (
            agent_config is not None
            and hasattr(agent_config, "tools")
            and agent_config.tools
        ):
            # Create a mapping of tool names to tool objects
            tool_mapping = {}
            for tool in registered_tools:
                # Handle tuple structure from PluginManager: (func, schema_dict, model_class)
                if isinstance(tool, tuple) and len(tool) >= 1:
                    func = tool[0]  # Extract function from tuple
                    if hasattr(func, "__name__"):
                        tool_mapping[func.__name__] = tool
                # Handle direct function objects and other tool types
                elif hasattr(tool, "__name__"):
                    tool_mapping[tool.__name__] = tool
                elif hasattr(tool, "name"):
                    tool_mapping[tool.name] = tool
                elif isinstance(tool, dict) and "name" in tool:
                    tool_mapping[tool["name"]] = tool

            # Add name aliases for common mismatches
            if "get_current_time_tool" in tool_mapping:
                tool_mapping["current_time_tool"] = tool_mapping[
                    "get_current_time_tool"
                ]

            # Filter to only include tools specified in agent config
            filtered_tools = []
            for tool_name in agent_config.tools:
                if tool_name in tool_mapping:
                    filtered_tools.append(tool_mapping[tool_name])
                else:
                    logger.warning(
                        f"Tool '{tool_name}' specified in agent config but not found in available tools. Available tools: {list(tool_mapping.keys())}"
                    )

            logger.info(
                f"Filtered tools for agent '{agent_name}': {len(filtered_tools)} of {len(registered_tools)} available tools"
            )

        agent = QXLLMAgent(
            model_name=model_name_str,
            system_prompt=system_prompt_content,
            tools=filtered_tools,  # Pass filtered tools
            console=effective_console,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            reasoning_effort=reasoning_effort,
            enable_streaming=enable_streaming,
            agent_name=agent_name,
            agent_color=agent_color,
            agent_config=agent_config.__dict__ if agent_config else None,
        )
        return agent

    except Exception as e:
        logger.error(f"Failed to initialize QXLLMAgent: {e}", exc_info=True)
        if console:
            console.print(f"[error]Error:[/] Init LLM Agent: {e}")
        return None


async def query_llm(
    agent: QXLLMAgent,
    user_input: str,
    console: RichConsole,
    message_history: Optional[List[ChatCompletionMessageParam]] = None,
    add_user_message_to_history: bool = True,
    config_manager: Optional[Any] = None,
) -> Optional[Any]:
    """
    Queries the LLM agent.
    """
    try:
        logger.info(f"🎯 query_llm called with config_manager: {config_manager is not None}")
        
        # Default: use main agent
        result = await agent.run(
            user_input,
            message_history=message_history,
            add_user_message_to_history=add_user_message_to_history,
        )
        return result
        
    except Exception as e:
        logger.error(f"Error during LLM query: {e}", exc_info=True)
        console.print(f"[error]Error:[/] LLM query: {e}")
        return None
