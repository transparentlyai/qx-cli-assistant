import asyncio  # noqa: F401
import json
import logging
import os
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Protocol, Tuple, Type, cast

import httpx
from openai import AsyncOpenAI
from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionToolMessageParam,
    ChatCompletionToolParam,
    ChatCompletionUserMessageParam,
)
from openai.types.shared_params.function_definition import FunctionDefinition
from pydantic import BaseModel, ValidationError
from rich.console import Console as RichConsoleClass


class ConsoleProtocol(Protocol):
    def print(self, *args, **kwargs): ...


RichConsole = ConsoleProtocol  # Type alias for backward compatibility

from qx.core.mcp_manager import MCPManager  # New import
from qx.core.plugin_manager import PluginManager

logger = logging.getLogger(__name__)


def load_and_format_system_prompt() -> str:
    """
    Loads the system prompt from the markdown file and formats it with
    environment variables.
    """
    try:
        current_dir = Path(__file__).parent
        prompt_path = current_dir.parent / "prompts" / "system-prompt.md"

        if not prompt_path.exists():
            logger.error(f"System prompt file not found at {prompt_path}")
            return "You are a helpful AI assistant."

        template = prompt_path.read_text(encoding="utf-8")
        user_context = os.environ.get("QX_USER_CONTEXT", "")
        project_context = os.environ.get("QX_PROJECT_CONTEXT", "")
        project_files = os.environ.get("QX_PROJECT_FILES", "")

        formatted_prompt = template.replace("{user_context}", user_context)
        formatted_prompt = formatted_prompt.replace(
            "{project_context}", project_context
        )
        formatted_prompt = formatted_prompt.replace("{project_files}", project_files)
        return formatted_prompt
    except Exception as e:
        logger.error(f"Failed to load or format system prompt: {e}", exc_info=True)
        return "You are a helpful AI assistant."


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
        self._http_client: Optional[httpx.AsyncClient] = None

        for func, schema, input_model_class in tools:
            self._tool_functions[func.__name__] = func

            # Handle different schema formats (regular plugins vs MCP tools)
            if "function" in schema:
                # MCP tools format: {"type": "function", "function": {...}}
                function_def = schema["function"]
            else:
                # Regular plugins format: {"name": ..., "description": ..., "parameters": ...}
                function_def = schema

            self._openai_tools_schema.append(
                ChatCompletionToolParam(
                    type="function", function=FunctionDefinition(**function_def)
                )
            )
            self._tool_input_models[func.__name__] = input_model_class
            logger.debug(
                f"QXLLMAgent: Registered tool function '{func.__name__}' with schema name '{function_def.get('name')}'"
            )

        self.client = self._initialize_openai_client()
        logger.info(f"QXLLMAgent initialized with model: {self.model_name}")
        logger.info(f"Registered {len(self._tool_functions)} tool functions.")


    def _initialize_openai_client(self) -> AsyncOpenAI:
        """Initializes the OpenAI client for OpenRouter."""
        openrouter_api_key = os.environ.get("OPENROUTER_API_KEY")
        if not openrouter_api_key:
            from rich.console import Console
            Console().print(
                "[red]Error:[/red] OPENROUTER_API_KEY environment variable not set."
            )
            raise ValueError("OPENROUTER_API_KEY not set.")

        # Create HTTP client with proper configuration
        self._http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(180.0, connect=10.0),  # 180s total, 10s connect
            limits=httpx.Limits(
                max_connections=10,
                max_keepalive_connections=5,
                keepalive_expiry=30.0
            ),
            follow_redirects=True
        )

        return AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=openrouter_api_key,
            http_client=self._http_client,
        )

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
        # Prevent infinite recursion in tool calling
        MAX_RECURSION_DEPTH = 10
        if _recursion_depth > MAX_RECURSION_DEPTH:
            error_msg = f"Maximum recursion depth ({MAX_RECURSION_DEPTH}) exceeded in tool calling"
            logger.error(error_msg)
            return QXRunResult(f"Error: {error_msg}", message_history or [])
        messages: List[ChatCompletionMessageParam] = []
        
        # Only add system prompt if not already present in message history
        has_system_message = message_history and any(
            (msg.get("role") if isinstance(msg, dict) else getattr(msg, "role", None)) == "system" 
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
            should_add_user_message = user_input.strip() != ""  # Don't add empty messages
            if should_add_user_message and message_history:
                # Check if the last message is already this user input
                last_msg = message_history[-1] if message_history else None
                if last_msg:
                    # Handle both dict and Pydantic model cases
                    msg_role = last_msg.get("role") if isinstance(last_msg, dict) else getattr(last_msg, "role", None)
                    msg_content = last_msg.get("content") if isinstance(last_msg, dict) else getattr(last_msg, "content", None)
                    if msg_role == "user" and msg_content == user_input:
                        should_add_user_message = False
            
            if should_add_user_message:
                messages.append(
                    cast(
                        ChatCompletionUserMessageParam, {"role": "user", "content": user_input}
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
                logger.info(f"Sending message to LLM:\\n{json.dumps(last_message, indent=2)}")
                
                # Also log available tools on first user message
                if last_message.get("role") == "user" and self._openai_tools_schema:
                    logger.info(f"Available tools ({len(self._openai_tools_schema)}):")
                    for tool in self._openai_tools_schema[:3]:  # Show first 3 tools
                        tool_dict = tool.model_dump() if hasattr(tool, 'model_dump') else dict(tool)
                        logger.info(f"  - {tool_dict.get('function', {}).get('name', 'unknown')}")

        # Parameters for the chat completion
        chat_params: Dict[str, Any] = {
            "model": self.model_name,
            "messages": [
                msg.model_dump() if isinstance(msg, BaseModel) else msg
                for msg in messages
            ],
            "temperature": self.temperature,
            "tools": self._openai_tools_schema,
            "tool_choice": "auto",
        }

        if self.max_output_tokens is not None:
            chat_params["max_tokens"] = self.max_output_tokens

        # OpenRouter-specific parameters like 'reasoning' go into extra_body
        extra_body_params = {}
        if self.reasoning_effort is not None:
            # Pass reasoning_effort as 'effort' string
            extra_body_params["reasoning"] = {"effort": self.reasoning_effort}

        # Add provider settings from environment variables
        provider_name = os.environ.get("QX_MODEL_PROVIDER")
        allow_fallbacks_str = os.environ.get("QX_ALLOW_PROVIDER_FALLBACK")
        
        if provider_name or allow_fallbacks_str is not None:
            provider_config = {}
            if provider_name:
                provider_config["order"] = [p.strip() for p in provider_name.split(",")]
            
            if allow_fallbacks_str is not None:
                # Convert string to boolean: "true", "1", "yes" -> True; otherwise False
                allow_fallbacks = allow_fallbacks_str.lower() in ("true", "1", "yes")
                provider_config["allow_fallbacks"] = allow_fallbacks
            
            if provider_config:
                extra_body_params["provider"] = provider_config

        if extra_body_params:
            chat_params["extra_body"] = extra_body_params

        try:
            if self.enable_streaming:
                # Add streaming parameter
                chat_params["stream"] = True
                # Add an empty line before the streaming response starts
                from rich.console import Console
                Console().print("")
                return await self._handle_streaming_response(
                    chat_params, messages, user_input, _recursion_depth
                )
            else:
                response = await self.client.chat.completions.create(**chat_params)

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
                                    "arguments": tc.function.arguments
                                }
                            }
                            for tc in response_message.tool_calls
                        ]
                    logger.info(f"Received message from LLM:\\n{json.dumps(response_dict, indent=2)}")
                
                messages.append(response_message)

                if response_message.tool_calls:
                    return await self._process_tool_calls_and_continue(
                        response_message, messages, user_input, retry_count
                    )
                else:
                    return QXRunResult(response_message.content or "", messages)

        except Exception as e:
            logger.error(f"Error during LLM chat completion: {e}", exc_info=True)
            from rich.console import Console
            Console().print(f"[red]Error:[/red] LLM chat completion: {e}")
            return None

    async def _handle_streaming_response(
        self,
        chat_params: Dict[str, Any],
        messages: List[ChatCompletionMessageParam],
        user_input: str,
        recursion_depth: int = 0,
    ) -> Any:
        """Handle streaming response from OpenRouter API."""
        import asyncio
        import time

        accumulated_content = ""
        accumulated_tool_calls = []
        current_tool_call = None
        has_tool_calls = False  # Track if we've seen any tool calls
        has_rendered_content = False  # Track if we've rendered any content during streaming
        total_rendered_content = ""  # Track all content that was rendered for validation

        # Use markdown-aware buffer for streaming
        from qx.core.markdown_buffer import create_markdown_buffer

        markdown_buffer = create_markdown_buffer()

        # Helper function to render content as markdown via rich console
        async def render_content(content: str) -> None:
            nonlocal has_rendered_content, total_rendered_content
            if content and content.strip():
                has_rendered_content = True
                total_rendered_content += content  # Track for validation
                # Output as markdown to rich console
                from rich.console import Console
                from rich.markdown import Markdown
                rich_console = Console()
                rich_console.print(Markdown(content, code_theme="rrt"), end="")

        # Stream content directly to console
        stream = None
        spinner_stopped = False
        try:
            from rich.console import Console
            console = Console()
            
            with console.status("Thinking...", spinner="dots") as status:
                stream = await self.client.chat.completions.create(**chat_params)
                
                async for chunk in stream:
                    if not chunk.choices:
                        continue

                    choice = chunk.choices[0]
                    delta = choice.delta

                    # Handle content streaming
                    if delta.content:
                        accumulated_content += delta.content
                        # Check if buffer returns content to render
                        content_to_render = markdown_buffer.add_content(delta.content)
                        
                        # Stop spinner when markdown buffer actually releases content to render
                        if not spinner_stopped and content_to_render and content_to_render.strip():
                            spinner_stopped = True
                            status.stop()
                        
                        # Only render during streaming if we haven't seen tool calls yet
                        if content_to_render and not has_tool_calls:
                            await render_content(content_to_render)

                    # Handle tool call streaming
                    if delta.tool_calls:
                        # Stop spinner when we start processing tool calls
                        if not spinner_stopped:
                            spinner_stopped = True
                            status.stop()
                        
                        has_tool_calls = True  # Mark that we've seen tool calls
                        if os.getenv("QX_LOG_RECEIVED"):
                            logger.info(f"Received tool call delta: {delta.tool_calls}")
                        for tool_call_delta in delta.tool_calls:
                            # Start new tool call
                            if tool_call_delta.index is not None:
                                # Ensure we have enough space in the list
                                while len(accumulated_tool_calls) <= tool_call_delta.index:
                                    accumulated_tool_calls.append(
                                        {
                                            "id": None,
                                            "type": "function",
                                            "function": {"name": "", "arguments": ""},
                                        }
                                    )

                                current_tool_call = accumulated_tool_calls[
                                    tool_call_delta.index
                                ]

                                if tool_call_delta.id:
                                    current_tool_call["id"] = tool_call_delta.id

                                if tool_call_delta.function:
                                    if tool_call_delta.function.name:
                                        current_tool_call["function"]["name"] = (
                                            tool_call_delta.function.name
                                        )
                                    if tool_call_delta.function.arguments:
                                        current_tool_call["function"]["arguments"] += (
                                            tool_call_delta.function.arguments
                                        )

                    # Check if stream is finished
                    if choice.finish_reason:
                        break
            
            # Stream completed successfully - it should auto-close when exhausted
            # but we'll ensure cleanup just in case
            if stream and hasattr(stream, 'aclose'):
                try:
                    await stream.aclose()
                except Exception:
                    pass  # Stream might already be closed

        except Exception as e:
            logger.error(f"Error during streaming: {e}", exc_info=True)
            
            # Clean up the stream in error case
            if stream and hasattr(stream, 'aclose'):
                try:
                    # Small delay to allow any pending data to be processed
                    await asyncio.sleep(0.1)
                    await stream.aclose()
                except Exception:
                    pass  # Ignore errors closing stream
            
            # Fall back to non-streaming
            chat_params["stream"] = False
            response = await self.client.chat.completions.create(**chat_params)
            response_message = response.choices[0].message
            messages.append(response_message)

            if response_message.tool_calls:
                return await self._process_tool_calls_and_continue(
                    response_message, messages, user_input, recursion_depth
                )
            else:
                return QXRunResult(response_message.content, messages)

        # After streaming, flush any remaining content
        remaining_content = markdown_buffer.flush()
        
        # Render remaining content if:
        # 1. We have remaining content AND
        # 2. Either we haven't rendered anything yet OR we have tool calls
        if remaining_content and remaining_content.strip():
            if not has_rendered_content or has_tool_calls:
                await render_content(remaining_content)
        
        # Validate that all content was rendered
        if accumulated_content:
            # Compare lengths to detect content loss
            accumulated_len = len(accumulated_content)
            rendered_len = len(total_rendered_content)
            
            if accumulated_len != rendered_len:
                logger.warning(
                    f"Content validation mismatch: accumulated {accumulated_len} chars, "
                    f"rendered {rendered_len} chars. Difference: {accumulated_len - rendered_len}"
                )
                
                # Log debug information if content was lost
                if accumulated_len > rendered_len:
                    logger.debug("Content may have been lost during streaming")
                    if os.getenv("QX_DEBUG_STREAMING"):
                        # Only log detailed info if debug flag is set
                        logger.debug(f"Accumulated content: {repr(accumulated_content[:200])}...")
                        logger.debug(f"Rendered content: {repr(total_rendered_content[:200])}...")
            else:
                logger.debug(f"Content validation passed: {accumulated_len} chars rendered successfully")
        
        # Add final newline if we rendered any content
        if accumulated_content.strip() and (has_rendered_content or remaining_content):
            from rich.console import Console
            Console().print()

        # Create response message from accumulated data
        response_message_dict = {
            "role": "assistant",
            "content": accumulated_content if accumulated_content else None,
        }

        if accumulated_tool_calls:
            # Convert accumulated tool calls to proper format
            tool_calls = []
            for tc in accumulated_tool_calls:
                if tc["id"] and tc["function"]["name"]:
                    tool_calls.append(
                        {
                            "id": tc["id"],
                            "type": "function",
                            "function": {
                                "name": tc["function"]["name"],
                                "arguments": tc["function"]["arguments"],
                            },
                        }
                    )
            response_message_dict["tool_calls"] = tool_calls

        # Convert to proper message format
        from openai.types.chat.chat_completion_message import ChatCompletionMessage

        response_message = ChatCompletionMessage(**response_message_dict)
        
        # Log the received message if QX_LOG_RECEIVED is set (for streaming)
        if os.getenv("QX_LOG_RECEIVED"):
            logger.info(f"Received message from LLM (streaming):\\n{json.dumps(response_message_dict, indent=2)}")
        
        messages.append(response_message)


        # Process tool calls if any
        if accumulated_tool_calls:
            # Pass empty content if we cleared narration
            response_message.content = accumulated_content if accumulated_content else None
            return await self._process_tool_calls_and_continue(
                response_message, messages, user_input, recursion_depth
            )
        else:
            return QXRunResult(accumulated_content or "", messages)

    async def _process_tool_calls_and_continue(
        self,
        response_message,
        messages: List[ChatCompletionMessageParam],
        user_input: str,
        recursion_depth: int = 0,
    ) -> Any:
        """Process tool calls and continue the conversation."""
        if not response_message.tool_calls:
            # Ensure we have content to return
            content = response_message.content if response_message.content else ""
            return QXRunResult(content, messages)

        tool_tasks = []
        for tool_call in response_message.tool_calls:
            function_name = tool_call.function.name
            function_args = tool_call.function.arguments
            tool_call_id = tool_call.id

            if function_name not in self._tool_functions:
                error_msg = f"LLM attempted to call unknown tool: {function_name}"
                logger.error(error_msg)
                from rich.console import Console
                Console().print(f"[red]{error_msg}[/red]")
                messages.append(
                    cast(
                        ChatCompletionToolMessageParam,
                        {
                            "role": "tool",
                            "tool_call_id": tool_call_id,
                            "content": f"Error: Unknown tool '{function_name}'",
                        },
                    )
                )
                continue

            tool_func = self._tool_functions[function_name]
            tool_input_model = self._tool_input_models[function_name]

            try:
                parsed_args = {}
                if function_args:
                    try:
                        parsed_args = json.loads(function_args)
                    except json.JSONDecodeError:
                        error_msg = f"LLM provided invalid JSON arguments for tool '{function_name}': {function_args}"
                        logger.error(error_msg)
                        from rich.console import Console
                        Console().print(f"[red]{error_msg}[/red]")
                        messages.append(
                            cast(
                                ChatCompletionToolMessageParam,
                                {
                                    "role": "tool",
                                    "tool_call_id": tool_call_id,
                                    "content": f"Error: Invalid JSON arguments for tool '{function_name}'. Please ensure arguments are valid JSON.",
                                },
                            )
                        )
                        continue

                try:
                    tool_args_instance = tool_input_model(**parsed_args)
                except ValidationError as ve:
                    error_msg = f"LLM provided invalid parameters for tool '{function_name}'. Validation errors: {ve}"
                    logger.error(error_msg, exc_info=True)
                    from rich.console import Console
                    Console().print(f"[red]{error_msg}[/red]")
                    messages.append(
                        cast(
                            ChatCompletionToolMessageParam,
                            {
                                "role": "tool",
                                "tool_call_id": tool_call_id,
                                "content": f"Error: Invalid parameters for tool '{function_name}'. Details: {ve}",
                            },
                        )
                    )
                    continue

                # If validation passes, add the task to the list
                tool_tasks.append(
                    {
                        "tool_call_id": tool_call_id,
                        "function_name": function_name,
                        "coroutine": tool_func(
                            console=RichConsoleClass(), args=tool_args_instance
                        ),
                    }
                )

            except Exception as e:
                # This catch is for errors during parsing/validation, not tool execution
                error_msg = f"Error preparing tool call '{function_name}': {e}"
                logger.error(error_msg, exc_info=True)
                from rich.console import Console
                Console().print(f"[red]{error_msg}[/red]")
                messages.append(
                    cast(
                        ChatCompletionToolMessageParam,
                        {
                            "role": "tool",
                            "tool_call_id": tool_call_id,
                            "content": f"Error: Failed to prepare tool call: {e}",
                        },
                    )
                )

        # Execute all collected tool tasks in parallel with timeout
        if tool_tasks:
            # Create tasks with individual timeouts
            async def run_tool_with_timeout(task_info):
                try:
                    return await asyncio.wait_for(
                        task_info["coroutine"], 
                        timeout=30.0  # 30 second timeout per tool
                    )
                except asyncio.TimeoutError:
                    error_msg = f"Tool '{task_info['function_name']}' timed out after 30 seconds"
                    logger.error(error_msg)
                    return Exception(error_msg)
            
            results = await asyncio.gather(
                *[run_tool_with_timeout(task) for task in tool_tasks], 
                return_exceptions=True
            )

            for i, result in enumerate(results):
                tool_call_info = tool_tasks[i]
                tool_call_id = tool_call_info["tool_call_id"]
                function_name = tool_call_info["function_name"]

                if isinstance(result, Exception):
                    error_msg = f"Error executing tool '{function_name}': {result}"
                    logger.error(error_msg, exc_info=True)
                    from rich.console import Console
                    Console().print(f"[red]{error_msg}[/red]")
                    tool_output_content = f"Error: Tool execution failed: {result}. This might be due to an internal tool error or an unexpected argument type."
                else:
                    if hasattr(result, "model_dump_json"):
                        tool_output_content = result.model_dump_json()
                    else:
                        tool_output_content = str(result)

                tool_message = {
                    "role": "tool",
                    "tool_call_id": tool_call_id,
                    "content": tool_output_content,
                }
                
                # Log tool response if QX_LOG_SENT is set (since we're sending it to the model)
                if os.getenv("QX_LOG_SENT"):
                    logger.info(f"Sending tool response to LLM:\\n{json.dumps(tool_message, indent=2)}")
                
                messages.append(
                    cast(
                        ChatCompletionToolMessageParam,
                        tool_message,
                    )
                )

        # After processing all tool calls (or attempting to), make one recursive call
        # The model needs to generate a response based on the tool outputs
        # We pass a special marker that won't be added to messages but triggers response generation
        return await self.run("__CONTINUE_AFTER_TOOLS__", messages, recursion_depth + 1)
    
    async def cleanup(self):
        """Clean up resources like HTTP client."""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None


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
    console: RichConsole,
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
        console.print(f"[red]Error:[/red] Failed to load tools: {e}")
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
        ]:
            logger.warning(
                f"Invalid value for QX_MODEL_REASONING_EFFORT: '{reasoning_effort}'. Expected 'high', 'medium', or 'low'. Setting to None."
            )
            reasoning_effort = None

        agent = QXLLMAgent(
            model_name=model_name_str,
            system_prompt=system_prompt_content,
            tools=registered_tools,  # Pass combined tools
            console=console,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            reasoning_effort=reasoning_effort,
            enable_streaming=enable_streaming,
        )
        return agent

    except Exception as e:
        logger.error(f"Failed to initialize QXLLMAgent: {e}", exc_info=True)
        console.print(f"[red]Error:[/red] Init LLM Agent: {e}")
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
        console.print(f"[red]Error:[/red] LLM query: {e}")
        return None
