import asyncio  # noqa: F401
import json
import logging
import os
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Protocol, Tuple, Type, cast

import httpx
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
from qx.core.llm_components.messages import MessageCache
from qx.core.llm_components.streaming import StreamingHandler
from qx.core.llm_components.tools import ToolProcessor
from qx.core.llm_components.fallbacks import FallbackHandler, LiteLLMCaller


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
    ):
        self.model_name = model_name
        self.system_prompt = system_prompt
        self.console = console
        self.temperature = temperature
        self.max_output_tokens = max_output_tokens
        self.reasoning_effort = reasoning_effort
        self.enable_streaming = enable_streaming

        self._tool_functions: Dict[str, Callable] = {}
        self._openai_tools_schema: List[ChatCompletionToolParam] = []
        self._tool_input_models: Dict[str, Type[BaseModel]] = {}
        self._message_cache = MessageCache()  # Use new MessageCache class

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

        # Configure LiteLLM and get reliability settings
        self._reliability_config = configure_litellm()

        # Initialize handlers
        self._litellm_caller = LiteLLMCaller(self._reliability_config)
        self._streaming_handler = StreamingHandler(
            self._litellm_caller.make_litellm_call,
            self._handle_timeout_fallback,
            self._process_tool_calls_and_continue,
        )
        self._tool_processor = ToolProcessor(
            self._tool_functions, self._tool_input_models, self.console, self.run
        )
        self._fallback_handler = FallbackHandler(
            self.model_name,
            self.temperature,
            self.max_output_tokens,
            self._openai_tools_schema,
            self._serialize_messages_efficiently,
            self._process_tool_calls_and_continue,
            self.console,
        )

        logger.info(f"QXLLMAgent initialized with model: {self.model_name}")
        logger.info(f"Registered {len(self._tool_functions)} tool functions.")

    async def _handle_timeout_fallback(self, messages, user_input, recursion_depth):
        """Delegate to fallback handler."""
        return await self._fallback_handler.handle_timeout_fallback(
            messages, user_input, recursion_depth
        )

    async def _process_tool_calls_and_continue(
        self, response_message, messages, user_input, recursion_depth
    ):
        """Delegate to tool processor."""
        return await self._tool_processor.process_tool_calls_and_continue(
            response_message, messages, user_input, recursion_depth
        )

    async def _make_litellm_call(self, chat_params):
        """Delegate to LiteLLM caller."""
        return await self._litellm_caller.make_litellm_call(chat_params)

    def _serialize_messages_efficiently(
        self, messages: List[ChatCompletionMessageParam]
    ) -> List[Dict[str, Any]]:
        """
        Efficiently serialize messages to avoid repeated model_dump() calls.
        Delegates to MessageCache for implementation.
        """
        return self._message_cache.serialize_messages_efficiently(messages)

    async def run(
        self,
        user_input: str,
        message_history: Optional[List[ChatCompletionMessageParam]] = None,
        _recursion_depth: int = 0,
    ) -> Any:
        """
        Runs the LLM agent, handling conversation turns and tool calls.
        Returns the final message content or tool output.
        """
        # Log recursion depth to help with debugging
        if _recursion_depth > 0:
            logger.debug(f"LLM run() called with recursion depth: {_recursion_depth}")
        # Warn when approaching recursion limit
        if _recursion_depth >= 7:
            logger.warning(
                f"High recursion depth detected: {_recursion_depth}/10. Possible infinite tool calling loop."
            )
        # Prevent infinite recursion in tool calling
        MAX_RECURSION_DEPTH = 10
        if _recursion_depth > MAX_RECURSION_DEPTH:
            error_msg = f"Maximum recursion depth ({MAX_RECURSION_DEPTH}) exceeded in tool calling"
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
                user_input.strip() != ""
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

        # Add fallback models if configured
        if self._reliability_config.fallback_models:
            chat_params["fallbacks"] = self._reliability_config.fallback_models

        # Add context window fallback if configured
        if self._reliability_config.context_window_fallbacks:
            chat_params["context_window_fallback_dict"] = (
                self._reliability_config.context_window_fallbacks
            )

        try:
            if self.enable_streaming:
                # Add streaming parameter
                chat_params["stream"] = True
                # Add an empty line before the streaming response starts
                from rich.console import Console

                Console().print("")
                return await self._streaming_handler.handle_streaming_response(
                    chat_params, messages, user_input, _recursion_depth
                )
            else:
                try:
                    response = await self._litellm_caller.make_litellm_call(chat_params)
                    response_message = response.choices[0].message
                except (asyncio.TimeoutError, httpx.TimeoutException):
                    # After retries failed, try "try again" message
                    return await self._fallback_handler.handle_timeout_fallback(
                        messages, user_input, _recursion_depth
                    )
                except Exception as e:
                    logger.error(f"Non-streaming API call failed: {e}")
                    raise

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
        """Clean up resources and message cache."""
        # Clear message cache to free memory
        self._message_cache.clear()


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
) -> Optional[QXLLMAgent]:
    """
    Initializes the QXLLMAgent with system prompt and discovered tools.
    """
    system_prompt_content = load_and_format_system_prompt()

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

    try:
        temperature = float(os.environ.get("QX_MODEL_TEMPERATURE", "0.7"))
        max_output_tokens = int(os.environ.get("QX_MODEL_MAX_TOKENS", "4096"))

        # Retrieve reasoning_effort as a string directly
        reasoning_effort: Optional[str] = os.environ.get("QX_MODEL_REASONING_EFFORT")
        if reasoning_effort and reasoning_effort.lower() not in [
            "high",
            "medium",
            "low",
            "none",
        ]:
            logger.warning(
                f"Invalid value for QX_MODEL_REASONING_EFFORT: '{reasoning_effort}'. Expected 'high', 'medium', 'low', or 'none'. Setting to None."
            )
            reasoning_effort = None
        elif reasoning_effort and reasoning_effort.lower() == "none":
            reasoning_effort = None  # Disable reasoning when "none" is specified

        # Use a default console if none provided
        effective_console = console if console is not None else RichConsoleClass()

        agent = QXLLMAgent(
            model_name=model_name_str,
            system_prompt=system_prompt_content,
            tools=registered_tools,  # Pass combined tools
            console=effective_console,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            reasoning_effort=reasoning_effort,
            enable_streaming=enable_streaming,
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
) -> Optional[Any]:
    """
    Queries the LLM agent.
    """
    try:
        result = await agent.run(
            user_input,
            message_history=message_history,
        )
        return result
    except Exception as e:
        logger.error(f"Error during LLM query: {e}", exc_info=True)
        console.print(f"[error]Error:[/] LLM query: {e}")
        return None
