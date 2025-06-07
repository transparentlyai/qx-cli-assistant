import asyncio  # noqa: F401
import json
import logging
import os
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Protocol, Tuple, Type, cast

import httpx
import litellm
from litellm import acompletion
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

from qx.cli.theme import themed_console
from qx.core.mcp_manager import MCPManager
from qx.core.plugin_manager import PluginManager
from qx.core.user_prompts import is_show_thinking_active


class ConsoleProtocol(Protocol):
    def print(self, *args, **kwargs): ...


RichConsole = ConsoleProtocol  # Type alias for backward compatibility

logger = logging.getLogger(__name__)


def load_and_format_system_prompt() -> str:
    """
    Loads the system prompt from the markdown file and formats it with
    environment variables and runtime information.
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

        # Read .gitignore from the runtime CWD
        try:
            # Get the current working directory where the qx command is run
            runtime_cwd = Path(os.getcwd())
            gitignore_path = runtime_cwd / ".gitignore"
            if gitignore_path.exists():
                ignore_paths = gitignore_path.read_text(encoding="utf-8")
            else:
                ignore_paths = "# No .gitignore file found in the current directory."
        except Exception as e:
            logger.warning(f"Could not read .gitignore file: {e}")
            ignore_paths = "# Error reading .gitignore file."

        formatted_prompt = template.replace("{user_context}", user_context)
        formatted_prompt = formatted_prompt.replace(
            "{project_context}", project_context
        )
        formatted_prompt = formatted_prompt.replace("{project_files}", project_files)
        formatted_prompt = formatted_prompt.replace("{ignore_paths}", ignore_paths)

        logger.debug(f"Final System Prompt:\n{formatted_prompt}")

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
        self._message_cache: Dict[
            int, Dict[str, Any]
        ] = {}  # Cache for serialized messages

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

        self._configure_litellm()
        logger.info(f"QXLLMAgent initialized with model: {self.model_name}")
        logger.info(f"Registered {len(self._tool_functions)} tool functions.")

    def _serialize_messages_efficiently(
        self, messages: List[ChatCompletionMessageParam]
    ) -> List[Dict[str, Any]]:
        """
        Efficiently serialize messages to avoid repeated model_dump() calls.
        Converts BaseModel messages to dicts once and caches the result.
        """
        serialized: List[Dict[str, Any]] = []
        for msg in messages:
            if isinstance(msg, BaseModel):
                # Use object id as cache key
                msg_id = id(msg)
                if msg_id in self._message_cache:
                    # Use cached version
                    serialized.append(self._message_cache[msg_id])
                else:
                    # Convert BaseModel to dict and cache it
                    msg_dict = msg.model_dump()
                    self._message_cache[msg_id] = msg_dict
                    serialized.append(msg_dict)
                    # Limit cache size to prevent memory leaks
                    if len(self._message_cache) > 1000:
                        # Remove oldest entries (simple cleanup)
                        oldest_keys = list(self._message_cache.keys())[:500]
                        for key in oldest_keys:
                            del self._message_cache[key]
            else:
                # Already a dict, use as-is
                serialized.append(dict(msg) if hasattr(msg, "items") else msg)  # type: ignore
        return serialized

    def _configure_litellm(self) -> None:
        """Configure LiteLLM settings."""
        # Set up debugging if enabled
        if os.environ.get("QX_LOG_LEVEL", "ERROR").upper() == "DEBUG":
            litellm.set_verbose = True

        # Configure timeout settings
        litellm.request_timeout = float(os.environ.get("QX_REQUEST_TIMEOUT", "120"))

        # Configure retries
        litellm.num_retries = int(os.environ.get("QX_NUM_RETRIES", "3"))

        # Configure drop unsupported params behavior
        litellm.drop_params = True

        # Set up API key validation
        self._validate_api_keys()

        # Parse reliability configuration
        self._setup_reliability_config()

    def _validate_api_keys(self) -> None:
        """Validate that required API keys are present."""
        # Check for any provider API key
        api_keys = [
            "OPENROUTER_API_KEY",
            "OPENAI_API_KEY",
            "ANTHROPIC_API_KEY",
            "AZURE_API_KEY",
            "GOOGLE_API_KEY",
        ]

        has_valid_key = any(os.environ.get(key) for key in api_keys)

        if not has_valid_key:
            from rich.console import Console

            Console().print(
                "[error]Error:[/] No valid API key found. Please set one of: "
                + ", ".join(api_keys)
            )
            raise ValueError("No valid API key found.")

    def _setup_reliability_config(self) -> None:
        """Parse and setup reliability configuration from environment variables."""
        import json

        # Parse fallback models
        fallback_models_str = os.environ.get("QX_FALLBACK_MODELS", "")
        self.fallback_models = []
        if fallback_models_str:
            self.fallback_models = [
                model.strip() for model in fallback_models_str.split(",")
            ]

        # Parse context window fallbacks
        context_fallbacks_str = os.environ.get("QX_CONTEXT_WINDOW_FALLBACKS", "{}")
        try:
            self.context_window_fallbacks = json.loads(context_fallbacks_str)
        except json.JSONDecodeError:
            logger.warning(
                "Invalid JSON for QX_CONTEXT_WINDOW_FALLBACKS, using empty dict"
            )
            self.context_window_fallbacks = {}

        # Parse fallback API keys
        fallback_keys_str = os.environ.get("QX_FALLBACK_API_KEYS", "{}")
        try:
            self.fallback_api_keys = json.loads(fallback_keys_str)
        except json.JSONDecodeError:
            logger.warning("Invalid JSON for QX_FALLBACK_API_KEYS, using empty dict")
            self.fallback_api_keys = {}

        # Parse fallback API bases
        fallback_bases_str = os.environ.get("QX_FALLBACK_API_BASES", "{}")
        try:
            self.fallback_api_bases = json.loads(fallback_bases_str)
        except json.JSONDecodeError:
            logger.warning("Invalid JSON for QX_FALLBACK_API_BASES, using empty dict")
            self.fallback_api_bases = {}

        # Set up timeout and retry configuration
        self.fallback_timeout = float(os.environ.get("QX_FALLBACK_TIMEOUT", "45"))
        self.fallback_cooldown = float(os.environ.get("QX_FALLBACK_COOLDOWN", "60"))
        self.retry_delay = float(os.environ.get("QX_RETRY_DELAY", "1.0"))
        self.max_retry_delay = float(os.environ.get("QX_MAX_RETRY_DELAY", "60.0"))
        self.backoff_factor = float(os.environ.get("QX_BACKOFF_FACTOR", "2.0"))

        logger.debug(f"Reliability config - Fallback models: {self.fallback_models}")
        logger.debug(f"Context window fallbacks: {self.context_window_fallbacks}")
        logger.debug(f"Fallback timeout: {self.fallback_timeout}s")

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
            logger.warning(f"High recursion depth detected: {_recursion_depth}/10. Possible infinite tool calling loop.")
        # Prevent infinite recursion in tool calling
        MAX_RECURSION_DEPTH = 10
        if _recursion_depth > MAX_RECURSION_DEPTH:
            error_msg = f"Maximum recursion depth ({MAX_RECURSION_DEPTH}) exceeded in tool calling"
            logger.error(error_msg)
            self.console.print(f"[error]Error:[/] {error_msg}")
            # Create a response that doesn't continue the tool calling loop
            final_message = cast(
                ChatCompletionMessageParam,
                {"role": "assistant", "content": f"I apologize, but I've reached the maximum recursion depth while processing tool calls. This suggests there may be an issue with the tool calling logic that's causing an infinite loop. Please try rephrasing your request or breaking it into smaller steps."},
            )
            messages = list(message_history) if message_history else []
            messages.append(final_message)
            return QXRunResult(final_message["content"], messages)
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
        if hasattr(self, "fallback_models") and self.fallback_models:
            chat_params["fallbacks"] = self.fallback_models

        # Add context window fallback if configured
        if hasattr(self, "context_window_fallbacks") and self.context_window_fallbacks:
            chat_params["context_window_fallback_dict"] = self.context_window_fallbacks

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
                try:
                    response = await self._make_litellm_call(chat_params)
                    response_message = response.choices[0].message
                except (asyncio.TimeoutError, httpx.TimeoutException):
                    # After retries failed, try "try again" message
                    return await self._handle_timeout_fallback(
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
                    return await self._process_tool_calls_and_continue(
                        response_message, messages, user_input, _recursion_depth
                    )
                else:
                    return QXRunResult(response_message.content or "", messages)

        except Exception as e:
            logger.error(f"Error during LLM chat completion: {e}", exc_info=True)
            from rich.console import Console

            themed_console.print(f"[error]Error:[/] LLM chat completion: {e}")
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
        accumulated_tool_calls: list[dict[str, Any]] = []
        current_tool_call = None
        has_rendered_content = (
            False  # Track if we've rendered any content during streaming
        )
        total_rendered_content = (
            ""  # Track all content that was rendered for validation
        )

        # Use markdown-aware buffer for streaming
        from qx.core.markdown_buffer import create_markdown_buffer

        markdown_buffer = create_markdown_buffer()

        # Helper function to render content as markdown via rich console
        async def render_content(content: str) -> None:
            nonlocal has_rendered_content, total_rendered_content
            if content and content.strip():
                has_rendered_content = True
                total_rendered_content += content  # Track for validation
                # Output as markdown with Rich markup support
                from rich.console import Console
                from rich.markdown import Markdown

                from ..cli.theme import custom_theme

                rich_console = Console(theme=custom_theme)
                # Pre-process content to handle Rich markup within markdown
                processed_content = content
                # Use Rich's markup parsing capabilities by printing with markup=True
                # This allows both markdown and Rich markup to coexist
                rich_console.print(
                    Markdown(processed_content, code_theme="rrt"), end="", markup=True
                )

        # Stream content directly to console
        stream = None
        spinner_stopped = False
        stream_completed = False
        last_chunk_content = ""
        duplicate_chunk_count = 0
        max_duplicate_chunks = 5
        stream_start_time = time.time()
        max_stream_time = 300  # 5 minutes timeout

        try:
            from rich.console import Console

            console = Console()

            with console.status("", spinner="point",speed=2, refresh_per_second=25) as status:
                try:
                    stream = await self._make_litellm_call(chat_params)
                except (asyncio.TimeoutError, httpx.TimeoutException):
                    status.stop()
                    return await self._handle_timeout_fallback(
                        messages, user_input, recursion_depth
                    )

                async for chunk in stream:
                    # Check for cancellation
                    current_task = asyncio.current_task()
                    if current_task and current_task.cancelled():
                        logger.info("Stream cancelled by user")
                        break

                    # Check for stream timeout
                    if time.time() - stream_start_time > max_stream_time:
                        logger.warning("Stream timeout exceeded, breaking stream")
                        break
                    # Log the complete response chunk object
                    logger.debug(f"LLM Response Chunk: {chunk}")

                    if not chunk.choices:
                        continue

                    choice = chunk.choices[0]
                    delta = choice.delta

                    # Detect duplicate chunks to prevent infinite loops
                    current_chunk_content = ""
                    if delta.content:
                        current_chunk_content = delta.content
                    elif hasattr(delta, "reasoning") and delta.reasoning:
                        current_chunk_content = delta.reasoning

                    if (
                        current_chunk_content
                        and current_chunk_content == last_chunk_content
                    ):
                        duplicate_chunk_count += 1
                        if duplicate_chunk_count >= max_duplicate_chunks:
                            logger.warning(
                                f"Detected {duplicate_chunk_count} duplicate chunks, terminating stream"
                            )
                            break
                    else:
                        duplicate_chunk_count = 0
                        last_chunk_content = current_chunk_content

                    # Handle reasoning streaming (OpenRouter specific)
                    if hasattr(delta, "reasoning") and delta.reasoning:
                        # Stop spinner when we start processing reasoning
                        if not spinner_stopped:
                            spinner_stopped = True
                            status.stop()

                        # Display reasoning content in faded color
                        reasoning_text = delta.reasoning
                        if (
                            reasoning_text
                            and reasoning_text.strip()
                            and await is_show_thinking_active()
                        ):
                            from rich.console import Console

                            reasoning_console = Console()
                            reasoning_console.print(
                                f"[dim]{reasoning_text}[/dim]", end=""
                            )

                    # Handle content streaming
                    if delta.content:
                        accumulated_content += delta.content
                        # Check if buffer returns content to render
                        content_to_render = markdown_buffer.add_content(delta.content)

                        # Stop spinner when markdown buffer actually releases content to render
                        if (
                            not spinner_stopped
                            and content_to_render
                            and content_to_render.strip()
                        ):
                            spinner_stopped = True
                            status.stop()

                        # Continue rendering content even if tool calls are detected
                        # This prevents content loss when responses contain both text and tool calls
                        if content_to_render:
                            await render_content(content_to_render)

                    # Handle tool call streaming
                    if delta.tool_calls:
                        # Stop spinner when we start processing tool calls
                        if not spinner_stopped:
                            spinner_stopped = True
                            status.stop()

                        if os.getenv("QX_LOG_RECEIVED"):
                            logger.info(f"Received tool call delta: {delta.tool_calls}")
                        for tool_call_delta in delta.tool_calls:
                            # Start new tool call
                            if tool_call_delta.index is not None:
                                # Ensure we have enough space in the list
                                while (
                                    len(accumulated_tool_calls) <= tool_call_delta.index
                                ):
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
                        stream_completed = True
                        break

                    # Additional safeguard: if we get multiple consecutive empty chunks after content/reasoning
                    # this might indicate the stream should end
                    if (
                        not delta.content
                        and not (hasattr(delta, "reasoning") and delta.reasoning)
                        and not delta.tool_calls
                    ):
                        if (
                            accumulated_content or has_rendered_content
                        ):  # Only count empty chunks if we've seen content
                            duplicate_chunk_count += 1
                            if duplicate_chunk_count >= max_duplicate_chunks:
                                logger.warning(
                                    "Too many consecutive empty chunks, terminating stream"
                                )
                                break

            # Mark stream as completed and attempt graceful close
            stream_completed = True
            if stream and hasattr(stream, "aclose"):
                try:
                    await stream.aclose()
                except Exception:
                    pass  # Stream might already be closed

        except asyncio.CancelledError:
            logger.info("LLM operation cancelled by user")
            if stream and hasattr(stream, "aclose") and not stream_completed:
                try:
                    await stream.aclose()
                except Exception:
                    pass
            # Return partial response if any content was accumulated
            if accumulated_content:
                from rich.console import Console

                console = Console()
                console.print("\n[warning]⚠ Response interrupted[/]")

                response_message = cast(
                    ChatCompletionMessageParam,
                    {
                        "role": "assistant",
                        "content": accumulated_content,
                    },
                )
                messages.append(response_message)
                logger.debug(
                    f"Returning partial response due to cancellation: {response_message}"
                )
                return QXRunResult(accumulated_content, messages)
            else:
                # No content was generated before cancellation
                console = Console()
                console.print("\n[warning]Operation cancelled[/]")
                return QXRunResult("Operation cancelled", messages)
        except Exception as e:
            logger.error(f"Error during streaming: {e}", exc_info=True)

            # Clean up the stream in error case
            if stream and hasattr(stream, "aclose") and not stream_completed:
                try:
                    # Small delay to allow any pending data to be processed
                    await asyncio.sleep(0.1)
                    await stream.aclose()
                except Exception:
                    pass  # Ignore errors closing stream

            # Only fall back to non-streaming if we haven't accumulated any content
            # This prevents losing partial responses that were already streamed
            if not accumulated_content:
                # Fall back to non-streaming
                chat_params["stream"] = False
                try:
                    response = await self._make_litellm_call(chat_params)
                    response_message = response.choices[0].message
                    messages.append(response_message)

                    if response_message.tool_calls:
                        return await self._process_tool_calls_and_continue(
                            response_message, messages, user_input, recursion_depth
                        )
                    else:
                        return QXRunResult(response_message.content, messages)
                except (asyncio.TimeoutError, httpx.TimeoutException):
                    return await self._handle_timeout_fallback(
                        messages, user_input, recursion_depth
                    )
                except Exception as fallback_error:
                    logger.error(
                        f"Fallback non-streaming also failed: {fallback_error}",
                        exc_info=True,
                    )
                    return QXRunResult(
                        "Error: Both streaming and fallback failed", messages
                    )
            else:
                # We have partial content from streaming, continue with that
                logger.warning(
                    f"Streaming failed but recovered {len(accumulated_content)} characters of content"
                )

        # After streaming, flush any remaining content
        remaining_content = markdown_buffer.flush()

        # Always render remaining content if present
        if remaining_content and remaining_content.strip():
            await render_content(remaining_content)

        # Validate that all content was rendered and attempt recovery
        if accumulated_content:
            # Compare lengths to detect content loss
            accumulated_len = len(accumulated_content)
            rendered_len = len(total_rendered_content)

            if accumulated_len != rendered_len:
                content_loss = accumulated_len - rendered_len
                logger.warning(
                    f"Content validation mismatch: accumulated {accumulated_len} chars, "
                    f"rendered {rendered_len} chars. Difference: {content_loss}"
                )

                # Attempt to recover lost content
                if content_loss > 0:
                    # Try to find and render the missing content
                    if rendered_len < accumulated_len:
                        missing_content = accumulated_content[rendered_len:]
                        if missing_content.strip():
                            logger.info(
                                f"Attempting to recover {len(missing_content)} characters of lost content"
                            )
                            await render_content(missing_content)
                            total_rendered_content += missing_content

                    # Log debug information if content was lost
                    if os.getenv("QX_DEBUG_STREAMING"):
                        # Only log detailed info if debug flag is set
                        logger.debug(
                            f"Accumulated content: {repr(accumulated_content[:200])}..."
                        )
                        logger.debug(
                            f"Original rendered content: {repr(total_rendered_content[:200])}..."
                        )
            else:
                logger.debug(
                    f"Content validation passed: {accumulated_len} chars rendered successfully"
                )

        # Add final newline if we rendered any content
        if accumulated_content.strip() and (has_rendered_content or remaining_content):
            from rich.console import Console

            Console().print()

        # Create response message from accumulated data
        response_message_dict: Dict[str, Any] = {
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

        # Create message with explicit parameters to satisfy type checker
        if "tool_calls" in response_message_dict:
            streaming_response_message = ChatCompletionMessage(
                role="assistant",
                content=response_message_dict.get("content"),
                tool_calls=response_message_dict.get("tool_calls"),
            )
        else:
            streaming_response_message = ChatCompletionMessage(
                role="assistant", content=response_message_dict.get("content")
            )

        # Log the received message if QX_LOG_RECEIVED is set (for streaming)
        if os.getenv("QX_LOG_RECEIVED"):
            logger.info(
                f"Received message from LLM (streaming):\n{json.dumps(response_message_dict, indent=2)}"
            )

        messages.append(cast(ChatCompletionMessageParam, streaming_response_message))

        # Process tool calls if any
        if accumulated_tool_calls:
            # Pass empty content if we cleared narration
            streaming_response_message.content = (
                accumulated_content if accumulated_content else None
            )
            return await self._process_tool_calls_and_continue(
                streaming_response_message, messages, user_input, recursion_depth
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

                themed_console.print(f"[error]{error_msg}[/]")
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

                        themed_console.print(f"[error]{error_msg}[/]")
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

                    themed_console.print(f"[error]{error_msg}[/]")

                    # Create a more actionable error message for the LLM
                    error_details = []
                    for error in ve.errors():
                        field_path = " -> ".join(str(loc) for loc in error["loc"])
                        error_type = error["type"]
                        msg = error["msg"]
                        error_details.append(
                            f"Field '{field_path}': {msg} ({error_type})"
                        )

                    actionable_error = (
                        f"Tool '{function_name}' validation failed:\n"
                        + "\n".join(error_details)
                    )
                    if hasattr(tool_input_model, "model_fields"):
                        required_fields = [
                            name
                            for name, field in tool_input_model.model_fields.items()
                            if field.is_required()
                        ]
                        if required_fields:
                            actionable_error += (
                                f"\n\nRequired fields: {', '.join(required_fields)}"
                            )

                    messages.append(
                        cast(
                            ChatCompletionToolMessageParam,
                            {
                                "role": "tool",
                                "tool_call_id": tool_call_id,
                                "content": actionable_error,
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

                themed_console.print(f"[error]{error_msg}[/]")
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
                        timeout=120.0,  # 2 minute timeout per tool to allow for complex operations
                    )
                except asyncio.TimeoutError:
                    error_msg = (
                        f"Tool '{task_info['function_name']}' timed out after 2 minutes"
                    )
                    logger.error(error_msg)
                    return Exception(error_msg)

            results = await asyncio.gather(
                *[run_tool_with_timeout(task) for task in tool_tasks],
                return_exceptions=True,
            )

            for i, result in enumerate(results):
                tool_call_info = tool_tasks[i]
                tool_call_id = tool_call_info["tool_call_id"]
                function_name = tool_call_info["function_name"]

                if isinstance(result, Exception):
                    error_msg = f"Error executing tool '{function_name}': {result}"
                    logger.error(error_msg, exc_info=True)

                    themed_console.print(f"[error]{error_msg}[/]")
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
                    logger.info(
                        f"Sending tool response to LLM:\n{json.dumps(tool_message, indent=2)}"
                    )

                messages.append(
                    cast(
                        ChatCompletionToolMessageParam,
                        tool_message,
                    )
                )

        # After processing all tool calls (or attempting to), make one recursive call
        # The model needs to generate a response based on the tool outputs
        # We pass a special marker that won't be added to messages but triggers response generation
        try:
            tool_count = 0
            for m in messages:
                role = (
                    m.get("role") if isinstance(m, dict) else getattr(m, "role", None)
                )
                if role == "tool":
                    tool_count += 1
            logger.debug(f"Sending {tool_count} tool responses to LLM")
            
            # Check if we're approaching recursion limit before continuing
            if recursion_depth >= 8:
                logger.warning(f"Approaching recursion limit (depth {recursion_depth}), forcing final response")
                # Add a system message to encourage the LLM to provide a final response
                final_system_msg = cast(
                    ChatCompletionMessageParam,
                    {"role": "user", "content": "Please provide a final response based on the tool results above. Do not make any more tool calls."}
                )
                messages.append(final_system_msg)
            
            result = await self.run(
                "__CONTINUE_AFTER_TOOLS__", messages, recursion_depth + 1
            )
            logger.debug("Tool response continuation completed successfully")
            return result
        except (asyncio.TimeoutError, httpx.TimeoutException) as e:
            # Handle timeout specifically to avoid excessive retries
            logger.warning(f"Timeout during tool continuation: {e}")
            self.console.print(
                "[warning]Warning:[/] Tool execution completed but response generation timed out"
            )
            # Return partial result with tool responses included
            return QXRunResult(
                "Tool execution completed but response generation timed out", messages
            )
        except Exception as e:
            logger.error(f"Error continuing after tool execution: {e}", exc_info=True)
            self.console.print(
                f"[error]Error:[/] Failed to continue after tool execution: {e}"
            )
            # Return partial result with tool responses included
            return QXRunResult(
                "Tool execution completed but continuation failed", messages
            )

    async def _handle_timeout_fallback(
        self,
        messages: List[ChatCompletionMessageParam],
        user_input: str,
        recursion_depth: int,
    ) -> Any:
        """Handle timeout by trying 'try again' message as fallback."""
        logger.warning("Attempting timeout fallback with 'try again' message")
        self.console.print(
            "[warning]Request timed out after retries. Asking model to try again...[/]"
        )

        try:
            # Add "try again" as user message and retry once more
            fallback_messages = messages.copy()
            fallback_messages.append({"role": "user", "content": "try again"})

            fallback_params = {
                "model": self.model_name,
                "messages": self._serialize_messages_efficiently(fallback_messages),
                "temperature": self.temperature,
                "tools": self._openai_tools_schema,
                "tool_choice": "auto",
                "stream": False,  # Use non-streaming for fallback
            }

            if self.max_output_tokens is not None:
                fallback_params["max_tokens"] = self.max_output_tokens

            # Use timeout for fallback but allow sufficient time for model response
            response = await asyncio.wait_for(
                acompletion(**fallback_params),
                timeout=240.0,  # 4 minute timeout for fallback (slightly less than main timeout)
            )
            response_message = response.choices[0].message
            fallback_messages.append(response_message)

            if response_message.tool_calls:
                return await self._process_tool_calls_and_continue(
                    response_message, fallback_messages, "try again", recursion_depth
                )
            else:
                return QXRunResult(
                    response_message.content or "Request timed out", fallback_messages
                )

        except Exception as e:
            logger.error(f"Timeout fallback also failed: {e}", exc_info=True)
            self.console.print(
                "[error]Error:[/] Request timed out and fallback failed. Please try again."
            )
            return QXRunResult("Request timed out and retry failed", messages)

    async def _make_litellm_call(self, chat_params: Dict[str, Any]) -> Any:
        """Make LiteLLM API call with enhanced error handling and logging."""
        try:
            # Remove None values to clean up parameters
            clean_params = {k: v for k, v in chat_params.items() if v is not None}

            # Log reliability configuration if debug enabled
            if os.environ.get("QX_LOG_LEVEL", "").upper() == "DEBUG":
                logger.debug(
                    f"Making LiteLLM call with model: {clean_params.get('model')}"
                )
                if "fallbacks" in clean_params:
                    logger.debug(
                        f"Fallback models configured: {clean_params['fallbacks']}"
                    )
                if "context_window_fallback_dict" in clean_params:
                    logger.debug(
                        f"Context window fallbacks: {clean_params['context_window_fallback_dict']}"
                    )
                logger.debug(f"Retries: {clean_params.get('num_retries', 0)}")
                logger.debug(f"Timeout: {clean_params.get('timeout', 'default')}")

            return await acompletion(**clean_params)

        except Exception as e:
            error_type = type(e).__name__
            logger.error(f"LiteLLM API call failed ({error_type}): {e}")

            # Log which model/fallbacks were attempted if available
            if hasattr(self, "fallback_models") and self.fallback_models:
                logger.debug(f"Fallback models were available: {self.fallback_models}")

            raise

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
