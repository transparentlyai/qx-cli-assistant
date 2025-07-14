import asyncio
import json
import logging
import os
import time
from typing import Any, Callable, Dict, List, Optional, cast

from openai.types.chat import ChatCompletionMessageParam
from openai.types.chat.chat_completion_message import ChatCompletionMessage

from qx.core.user_prompts import is_details_active

logger = logging.getLogger(__name__)


def _managed_stream_print(content: Any, use_manager: bool = False, **kwargs) -> None:
    """
    Print helper for streaming that optionally uses console manager.

    For performance-critical streaming content, use_manager should be False.
    For status messages and error reporting, use_manager can be True.
    """
    from rich.console import Console

    if use_manager:
        try:
            from qx.core.console_manager import get_console_manager

            manager = get_console_manager()
            if manager and manager._running:
                style = kwargs.get("style")
                markup = kwargs.get("markup", True)
                end = kwargs.get("end", "\n")
                console = kwargs.get("console")
                if not console:
                    from qx.cli.theme import custom_theme

                    console = Console(theme=custom_theme)
                manager.print(
                    content, style=style, markup=markup, end=end, console=console
                )
                return
        except Exception:
            pass

    # Fallback to direct console creation and printing
    console = kwargs.get("console")
    if not console:
        from qx.cli.theme import custom_theme

        console = Console(theme=custom_theme)

    print_kwargs = {k: v for k, v in kwargs.items() if k != "console"}
    console.print(content, **print_kwargs)


class StreamingHandler:
    """Handles streaming responses from LLM APIs."""

    def __init__(
        self,
        make_litellm_call_func: Callable,
        process_tool_calls_func: Callable,
        console: Any = None,
    ):
        self._make_litellm_call = make_litellm_call_func
        self._process_tool_calls_and_continue = process_tool_calls_func
        self._console = console
        self._current_agent_name: Optional[str] = None
        self._current_agent_color: Optional[str] = None

    def set_agent_context(
        self, agent_name: str, agent_color: Optional[str] = None
    ) -> None:
        """Set the current agent context for quote bar rendering."""
        self._current_agent_name = agent_name
        self._current_agent_color = agent_color

    def clear_agent_context(self) -> None:
        """Clear the current agent context."""
        self._current_agent_name = None
        self._current_agent_color = None

    def _get_console(self) -> Any:
        """Get or create a console instance with custom theme.

        This is a pure function that always returns the same console
        for the same state, ensuring no side effects.
        """
        if self._console:
            return self._console

        from rich.console import Console
        from qx.cli.theme import custom_theme

        return Console(theme=custom_theme)

    def _extract_reasoning_content(self, delta: Any, choice: Any) -> Optional[str]:
        """Extract reasoning content from various possible fields.

        This is a pure function that checks multiple fields for reasoning content
        and returns the first non-None value found, preserving exact behavior.
        """
        # Check delta fields - order matters for compatibility
        if hasattr(delta, "reasoning") and delta.reasoning:
            return delta.reasoning
        elif hasattr(delta, "reasoning_content") and delta.reasoning_content:
            return delta.reasoning_content
        elif hasattr(delta, "thinking") and delta.thinking:
            return delta.thinking

        # Also check at the choice level for non-streaming fields
        if hasattr(choice, "reasoning_content") and choice.reasoning_content:
            return choice.reasoning_content

        return None

    def _is_empty_delta(self, delta: Any) -> bool:
        """Check if delta contains no meaningful content.

        This is a pure predicate function that returns True if the delta
        has no content, reasoning, or tool calls.
        """
        return (
            not delta.content
            and not (hasattr(delta, "reasoning") and delta.reasoning)
            and not (hasattr(delta, "reasoning_content") and delta.reasoning_content)
            and not (hasattr(delta, "thinking") and delta.thinking)
            and not delta.tool_calls
        )

    def _is_malformed_tool_call(self, tool_call: Optional[Dict[str, Any]]) -> bool:
        """Check if a tool call is malformed (missing ID or name).

        This is a pure predicate function that validates tool call structure.
        Returns True if the tool call is malformed.
        """
        if not tool_call:
            return False
        return not tool_call.get("id") or not tool_call.get("function", {}).get("name")

    def _render_agent_header(
        self,
        console: Any,
        agent_name: str,
        agent_color: Optional[str] = None,
        title_suffix: str = "",
        separator_style_suffix: str = "",
    ) -> None:
        """Render agent header with title and separator line.

        This preserves the exact output format including blank lines and Text objects.

        Args:
            console: The console to print to
            agent_name: The agent name to display
            agent_color: Optional agent color override
            title_suffix: Optional suffix to add to the title (e.g., " Thinking")
            separator_style_suffix: Optional style suffix for separator (e.g., " dim")
        """
        from qx.cli.quote_bar_component import get_agent_color
        from rich.text import Text

        color = get_agent_color(agent_name, agent_color)
        console.print()  # Add blank line before agent title

        # Create title with optional suffix
        title = f"{agent_name}{title_suffix}"
        console.print(Text(title, style="bold"))

        # Create separator line with optional style suffix
        separator_style = f"{color}{separator_style_suffix}"
        console.print(Text("─" * len(title), style=separator_style))

    async def _handle_malformed_function_call_retry(
        self,
        messages: List[ChatCompletionMessageParam],
        chat_params: Dict[str, Any],
        user_input: str,
        recursion_depth: int,
        retry_reason: str,
        debug_info: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Handle retry logic for MALFORMED_FUNCTION_CALL errors."""
        from qx.core.llm import QXRunResult  # Import here to avoid circular imports

        logger.warning(f"Detected {retry_reason} (recursion_depth={recursion_depth})")

        # Log debug info if provided
        if debug_info:
            for key, value in debug_info.items():
                logger.debug(f"{key}: {value}")

        # Close the current stream if provided
        if (
            "stream" in debug_info
            and debug_info["stream"]
            and hasattr(debug_info["stream"], "aclose")
        ):
            try:
                await debug_info["stream"].aclose()
            except Exception:
                pass

        # Add retry instruction message
        retry_message = cast(
            ChatCompletionMessageParam,
            {
                "role": "user",
                "content": "last function call was malformed, please try again",
            },
        )
        messages.append(retry_message)

        # Check recursion depth to prevent infinite loops
        if recursion_depth >= 3:  # Allow up to 3 retry attempts
            logger.error(
                f"Max retry attempts for MALFORMED_FUNCTION_CALL reached (recursion_depth={recursion_depth})"
            )
            logger.debug(f"Failed after {recursion_depth} retry attempts")
            logger.debug(f"Final message count: {len(messages)}")
            _managed_stream_print(
                "\n[error]Error: Maximum retry attempts for malformed function call reached[/]",
                use_manager=True,
            )
            return QXRunResult(
                "Failed to execute function call after multiple attempts", messages
            )

        # Recursive call to retry
        logger.info(
            f"Initiating retry attempt {recursion_depth + 1} for {retry_reason}"
        )
        return await self.handle_streaming_response(
            chat_params, messages, user_input, recursion_depth + 1
        )

    async def handle_streaming_response(
        self,
        chat_params: Dict[str, Any],
        messages: List[ChatCompletionMessageParam],
        user_input: str,
        recursion_depth: int = 0,
    ) -> Any:
        """Handle streaming response from OpenRouter API."""
        from litellm import RateLimitError
        import litellm

        # Log entry into streaming handler
        logger.debug(
            f"Entering handle_streaming_response (recursion_depth={recursion_depth})"
        )

        # Retry logic for rate limit errors during streaming
        max_retries = 3
        base_delay = 2.0

        for retry_attempt in range(max_retries + 1):
            try:
                return await self._handle_streaming_with_retry(
                    chat_params, messages, user_input, recursion_depth, retry_attempt
                )
            except RateLimitError as e:
                if retry_attempt < max_retries:
                    delay = base_delay * (retry_attempt + 1)  # 2s, 4s, 6s
                    logger.warning(f"Rate limit error during streaming: {e}")
                    logger.info(
                        f"Retrying in {delay} seconds... (Attempt {retry_attempt + 1}/{max_retries})"
                    )

                    # Show user-friendly message
                    from qx.cli.theme import themed_console

                    themed_console.print(
                        f"[yellow]Rate limit reached during streaming. Retrying in {delay} seconds... (Attempt {retry_attempt + 1}/{max_retries})[/yellow]"
                    )

                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        f"Rate limit error after {max_retries} streaming retries: {e}"
                    )
                    from qx.cli.theme import themed_console

                    themed_console.print(
                        f"[error]Rate limit error after {max_retries} retries. Please try again later.[/error]"
                    )
                    raise
            except Exception as e:
                # Check if this is a rate limit error that wasn't caught properly
                error_str = str(e)
                error_type = type(e).__name__

                logger.debug(
                    f"Caught streaming exception type: {error_type}, message: {error_str}"
                )

                # Check for various rate limit indicators
                is_rate_limit = any(
                    [
                        "429" in error_str,
                        "RESOURCE_EXHAUSTED" in error_str,
                        "rate limit" in error_str.lower(),
                        "quota" in error_str.lower()
                        and "exceeded" in error_str.lower(),
                        hasattr(litellm, error_type) and "RateLimit" in error_type,
                    ]
                )

                if is_rate_limit and retry_attempt < max_retries:
                    delay = base_delay * (retry_attempt + 1)  # 2s, 4s, 6s

                    logger.warning(
                        f"Rate limit error detected during streaming (type: {error_type}): {e}"
                    )
                    logger.info(
                        f"Retrying in {delay} seconds... (Attempt {retry_attempt + 1}/{max_retries})"
                    )

                    from qx.cli.theme import themed_console

                    themed_console.print(
                        f"[yellow]Rate limit reached during streaming. Retrying in {delay} seconds... (Attempt {retry_attempt + 1}/{max_retries})[/yellow]"
                    )

                    await asyncio.sleep(delay)
                else:
                    raise

    async def _handle_streaming_with_retry(
        self,
        chat_params: Dict[str, Any],
        messages: List[ChatCompletionMessageParam],
        user_input: str,
        recursion_depth: int,
        retry_attempt: int,
    ) -> Any:
        """Handle the actual streaming logic (separated for retry wrapper)."""
        from qx.core.llm import QXRunResult  # Import here to avoid circular imports

        if recursion_depth > 0:
            logger.info(
                f"This is retry attempt {recursion_depth} for MALFORMED_FUNCTION_CALL"
            )
            logger.debug(f"Message history length: {len(messages)}")
            if messages:
                last_msg = messages[-1]
                if isinstance(last_msg, dict) and last_msg.get("role") == "user":
                    content = last_msg.get("content", "")
                    if isinstance(content, str):
                        logger.debug(f"Last user message: {content[:100]}...")
                    else:
                        logger.debug("Last user message: [non-string content]")

        # Prevent retry loops - if we're already in a retry and get another malformed call, fail fast
        if recursion_depth > 0:
            # Check if the last message is our retry instruction
            if messages and len(messages) > 0:
                last_msg = messages[-1]
                if (
                    isinstance(last_msg, dict)
                    and last_msg.get("role") == "user"
                    and last_msg.get("content")
                    == "last function call was malformed, please try again"
                ):
                    # We're in a retry loop - this should count against our retry limit
                    logger.warning(
                        f"Detected retry loop at recursion_depth={recursion_depth}"
                    )

        accumulated_content = ""
        accumulated_tool_calls: list[dict[str, Any]] = []
        current_tool_call = None
        has_rendered_content = (
            False  # Track if we've rendered any content during streaming
        )
        total_rendered_content = (
            ""  # Track all content that was rendered for validation
        )
        accumulated_reasoning_content = ""  # Track reasoning/thinking content
        had_empty_choices = False  # Track if we ever got empty choices
        last_finish_reason = None  # Track the last finish reason we saw

        # Use markdown-aware buffer for streaming
        from qx.core.markdown_buffer import create_markdown_buffer

        markdown_buffer = create_markdown_buffer()

        # Track if we should show agent title for this response
        show_agent_title = True

        # If this is a continuation after tools, add spacing
        if user_input == "__CONTINUE_AFTER_TOOLS__":
            console = self._get_console()
            console.print()  # Add spacing before agent response after tools

        # Helper function to render content as markdown via rich console
        async def render_content(content: str) -> None:
            nonlocal has_rendered_content, total_rendered_content, show_agent_title
            if content and content.strip():
                has_rendered_content = True
                total_rendered_content += content  # Track for validation

                # Check if we have agent context for quote bar rendering
                agent_name = getattr(self, "_current_agent_name", None)
                agent_color = getattr(self, "_current_agent_color", None)

                if agent_name:
                    # Use agent quote bar rendering
                    from qx.cli.quote_bar_component import (
                        BorderedMarkdown,
                        get_agent_color,
                        LeftAlignedMarkdown,
                    )
                    from qx.cli.theme import default_markdown_theme

                    # Use the main console if available, otherwise create one with theme
                    rich_console = self._get_console()

                    # Show agent title for the first meaningful content
                    if show_agent_title:
                        self._render_agent_header(rich_console, agent_name, agent_color)
                        show_agent_title = False

                    # Pre-process content to handle Rich markup within markdown
                    processed_content = content

                    # Render with border for all chunks
                    color = get_agent_color(agent_name, agent_color)
                    bordered_md = BorderedMarkdown(
                        LeftAlignedMarkdown(processed_content, code_theme="rrt"),
                        border_style=color,
                        background_color="#080808",
                        markdown_theme=default_markdown_theme,
                    )
                    rich_console.print(bordered_md, end="", markup=True)
                else:
                    # Fallback to standard markdown rendering with BorderedMarkdown
                    from qx.cli.theme import default_markdown_theme
                    from qx.cli.quote_bar_component import (
                        BorderedMarkdown,
                        LeftAlignedMarkdown,
                    )

                    # Use the main console if available, otherwise create one with theme
                    rich_console = self._get_console()
                    # Pre-process content to handle Rich markup within markdown
                    processed_content = content

                    # Use BorderedMarkdown for consistent styling
                    bordered_md = BorderedMarkdown(
                        LeftAlignedMarkdown(processed_content, code_theme="rrt"),
                        border_style="dim blue",
                        background_color="#080808",
                        markdown_theme=default_markdown_theme,
                    )
                    rich_console.print(bordered_md, end="", markup=True)

        # Stream content directly to console
        stream = None
        spinner_stopped = False
        stream_completed = False
        last_chunk_content = ""
        duplicate_chunk_count = 0
        max_duplicate_chunks = 5
        stream_start_time = time.time()
        max_stream_time = 300  # 5 minutes timeout
        last_thinking_message = ""  # Track last thinking message for spinner
        showing_thinking_details = False  # Track if we're showing detailed thinking
        thinking_title_shown = False  # Track if we've already shown the thinking title

        # Helper function to update spinner with thinking message
        def update_spinner_text(thinking_text: str) -> None:
            nonlocal last_thinking_message
            if thinking_text and thinking_text.strip():
                # Get first line of thinking message
                first_line = thinking_text.strip().split("\n")[0]
                # Truncate if too long
                if len(first_line) > 60:
                    first_line = first_line[:57] + "..."
                last_thinking_message = first_line
                status.update(f"[dim]{first_line}[/dim]")

        try:
            console = self._get_console()

            with console.status(
                "[dim]Processing[/dim]", spinner="point", speed=2, refresh_per_second=25
            ) as status:
                stream = await self._make_litellm_call(chat_params)

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

                    # Check for MALFORMED_FUNCTION_CALL in provider-specific fields
                    # This handles cases where LiteLLM doesn't populate choices for certain error conditions
                    if (
                        hasattr(chunk, "provider_specific_fields")
                        and chunk.provider_specific_fields
                    ):
                        logger.debug(
                            f"Provider specific fields present: {chunk.provider_specific_fields}"
                        )
                        # Check if this is a Gemini MALFORMED_FUNCTION_CALL response
                        if isinstance(chunk.provider_specific_fields, dict):
                            candidates = chunk.provider_specific_fields.get(
                                "candidates", []
                            )
                            logger.debug(
                                f"Found {len(candidates)} candidates in provider fields"
                            )
                            for idx, candidate in enumerate(candidates):
                                finish_reason = candidate.get("finishReason")
                                logger.debug(
                                    f"Candidate {idx} finish reason: {finish_reason}"
                                )
                                if finish_reason == "MALFORMED_FUNCTION_CALL":
                                    return await self._handle_malformed_function_call_retry(
                                        messages,
                                        chat_params,
                                        user_input,
                                        recursion_depth,
                                        "MALFORMED_FUNCTION_CALL from Gemini",
                                        {
                                            "Accumulated content before retry": accumulated_content[
                                                :200
                                            ]
                                            if accumulated_content
                                            else "None",
                                            "Accumulated tool calls before retry": accumulated_tool_calls,
                                            "Full candidate data": candidate,
                                            "stream": stream,
                                        },
                                    )

                    if not chunk.choices:
                        # Mark that we got empty choices
                        had_empty_choices = True

                        # Check if this is due to a MALFORMED_FUNCTION_CALL before continuing
                        # Some providers (like Gemini via LiteLLM) may send empty choices for error conditions
                        if os.getenv("QX_LOG_RECEIVED"):
                            logger.debug(
                                "Empty choices in chunk, checking for error conditions"
                            )

                        # If we've been accumulating tool calls but got empty choices, this might be an error
                        if accumulated_tool_calls and len(accumulated_tool_calls) > 0:
                            # Check if the last tool call might be malformed
                            last_tool_call = (
                                accumulated_tool_calls[-1]
                                if accumulated_tool_calls
                                else None
                            )
                            if self._is_malformed_tool_call(last_tool_call):
                                return await self._handle_malformed_function_call_retry(
                                    messages,
                                    chat_params,
                                    user_input,
                                    recursion_depth,
                                    "incomplete tool call with empty choices, possible MALFORMED_FUNCTION_CALL",
                                    {
                                        "Incomplete tool call details": last_tool_call,
                                        "Total accumulated tool calls": len(
                                            accumulated_tool_calls
                                        ),
                                        "Had empty choices": had_empty_choices,
                                        "stream": stream,
                                    },
                                )

                        continue

                    choice = chunk.choices[0]
                    delta = choice.delta

                    # Detect duplicate chunks to prevent infinite loops
                    current_chunk_content = ""
                    if delta.content:
                        current_chunk_content = delta.content
                    else:
                        # Use reasoning content if no regular content
                        reasoning_content = self._extract_reasoning_content(
                            delta, choice
                        )
                        if reasoning_content:
                            current_chunk_content = reasoning_content

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

                    # Handle reasoning streaming (check multiple fields for different providers)
                    reasoning_text = self._extract_reasoning_content(delta, choice)

                    # Debug logging for reasoning content
                    if os.getenv("QX_DEBUG_REASONING"):
                        if reasoning_text:
                            logger.debug(
                                f"Found reasoning text: {reasoning_text[:100]}..."
                            )
                        else:
                            # Log what fields are present for debugging
                            delta_attrs = [
                                attr for attr in dir(delta) if not attr.startswith("_")
                            ]
                            logger.debug(f"Delta attributes: {delta_attrs}")
                            if hasattr(choice, "__dict__"):
                                choice_attrs = [
                                    attr
                                    for attr in dir(choice)
                                    if not attr.startswith("_")
                                ]
                                logger.debug(f"Choice attributes: {choice_attrs}")

                    if reasoning_text:
                        # Accumulate reasoning content for malformed function call detection
                        accumulated_reasoning_content += reasoning_text

                        # Check if we should display thinking messages
                        show_details = await is_details_active()

                        if reasoning_text and reasoning_text.strip():
                            if show_details:
                                # Stop spinner when we first start showing thinking details
                                if not showing_thinking_details and not spinner_stopped:
                                    status.stop()
                                    spinner_stopped = True
                                    showing_thinking_details = True

                                # Use BorderedMarkdown for think messages - render directly
                                try:
                                    from qx.cli.quote_bar_component import (
                                        BorderedMarkdown,
                                        get_agent_color,
                                        LeftAlignedMarkdown,
                                    )
                                    from qx.cli.theme import dimmed_grey_markdown_theme

                                    # Get agent context for proper formatting
                                    agent_name = getattr(
                                        self, "_current_agent_name", None
                                    )
                                    agent_color = getattr(
                                        self, "_current_agent_color", None
                                    )

                                    reasoning_console = self._get_console()

                                    if agent_name:
                                        color = get_agent_color(agent_name, agent_color)

                                        # Show title and separator only once at the beginning
                                        if not thinking_title_shown:
                                            self._render_agent_header(
                                                reasoning_console,
                                                agent_name,
                                                agent_color,
                                                title_suffix=" Thinking",
                                                separator_style_suffix=" dim",
                                            )
                                            thinking_title_shown = True

                                        # Create BorderedMarkdown for the thinking content only
                                        reasoning_md = LeftAlignedMarkdown(
                                            reasoning_text, code_theme="rrt"
                                        )
                                        bordered_thinking = BorderedMarkdown(
                                            reasoning_md,
                                            border_style=f"{color} dim",  # Use dim style for thinking
                                            background_color="#0a0a0a",  # Slightly darker background for thinking
                                            markdown_theme=dimmed_grey_markdown_theme,  # Use dimmed grey theme for thinking
                                        )

                                        reasoning_console.print(
                                            bordered_thinking, end=""
                                        )
                                    else:
                                        # Fallback without agent context
                                        reasoning_console.print(
                                            f"[dim]{reasoning_text}[/dim]", end=""
                                        )
                                except Exception:
                                    # Fallback to original method if anything fails

                                    reasoning_console = self._get_console()
                                    reasoning_console.print(
                                        f"[dim]{reasoning_text}[/dim]", end=""
                                    )
                            else:
                                # Update spinner with current thinking message if not displaying
                                update_spinner_text(reasoning_text)

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

                        # Add visual separation if transitioning from thinking to content
                        if content_to_render and showing_thinking_details:
                            # Add a small separator between thinking and actual response
                            transition_console = self._get_console()
                            transition_console.print()  # Add blank line for separation
                            showing_thinking_details = False  # Reset flag

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
                        last_finish_reason = choice.finish_reason
                        # Handle MALFORMED_FUNCTION_CALL finish reason
                        if choice.finish_reason == "MALFORMED_FUNCTION_CALL":
                            return await self._handle_malformed_function_call_retry(
                                messages,
                                chat_params,
                                user_input,
                                recursion_depth,
                                "MALFORMED_FUNCTION_CALL finish reason",
                                {
                                    "Stream completion state - accumulated_content": f"{len(accumulated_content) if accumulated_content else 0} chars",
                                    "Stream completion state - tool_calls": f"{len(accumulated_tool_calls)} calls",
                                    "Stream completion state - reasoning_content": f"{len(accumulated_reasoning_content) if accumulated_reasoning_content else 0} chars",
                                    "Last tool call state": accumulated_tool_calls[-1]
                                    if accumulated_tool_calls
                                    else "No tool calls",
                                    "stream": stream,
                                },
                            )

                        stream_completed = True
                        break

                    # Additional safeguard: if we get multiple consecutive empty chunks after content/reasoning
                    # this might indicate the stream should end
                    if self._is_empty_delta(delta):
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
                _managed_stream_print(
                    "\n[warning]⚠ Response interrupted[/]", use_manager=True
                )

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
                _managed_stream_print(
                    "\n[warning]Operation cancelled[/]", use_manager=True
                )
                return QXRunResult("Operation cancelled", messages)
        except Exception as e:
            # Special handling for JSON parsing errors from Vertex AI
            if (
                isinstance(e, RuntimeError)
                and "Error parsing chunk" in str(e)
                and "JSONDecodeError" in str(e)
            ):
                logger.warning(f"JSON parsing error in Vertex AI stream: {e}")

                # If we have accumulated content, return what we have
                if accumulated_content or has_rendered_content:
                    logger.info("Returning partial response due to JSON parsing error")

                    # Flush any remaining content
                    if markdown_buffer:
                        remaining_content = markdown_buffer.flush()
                        if remaining_content and remaining_content.strip():
                            await render_content(remaining_content)

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
                    if "tool_calls" in response_message_dict:
                        streaming_response_message = ChatCompletionMessage(
                            role="assistant",
                            content=response_message_dict.get("content"),
                            tool_calls=response_message_dict.get("tool_calls"),
                        )
                    else:
                        streaming_response_message = ChatCompletionMessage(
                            role="assistant",
                            content=response_message_dict.get("content"),
                        )

                    messages.append(
                        cast(ChatCompletionMessageParam, streaming_response_message)
                    )

                    # Add warning about truncated response
                    _managed_stream_print(
                        "\n[warning]Note: Response may be incomplete due to streaming error[/]",
                        use_manager=True,
                    )

                    return QXRunResult(accumulated_content or "", messages)
                else:
                    # No content accumulated, need to fail
                    logger.error(f"JSON parsing error with no accumulated content: {e}")
                    raise
            else:
                # Other exceptions - log and re-raise
                logger.error(f"Error during streaming: {e}", exc_info=True)

            # Clean up the stream in error case
            if stream and hasattr(stream, "aclose") and not stream_completed:
                try:
                    # Small delay to allow any pending data to be processed
                    await asyncio.sleep(0.1)
                    await stream.aclose()
                except Exception:
                    pass  # Ignore errors closing stream

            # Re-raise the exception - no fallbacks
            raise

        # After streaming, comprehensive check for MALFORMED_FUNCTION_CALL patterns
        # This might indicate a MALFORMED_FUNCTION_CALL that wasn't properly detected

        # Log diagnostic info if debug mode
        if os.getenv("QX_LOG_RECEIVED"):
            logger.debug(
                f"Stream ended - content: {bool(accumulated_content)}, tools: {bool(accumulated_tool_calls)}, "
                f"reasoning: {bool(accumulated_reasoning_content)}, empty_choices: {had_empty_choices}, "
                f"finish_reason: {last_finish_reason}"
            )

        # Check 1: Only check for actual malformed tool calls, not content patterns
        # Empty choices alone are not sufficient to trigger retry - models can have reasoning-only responses
        if had_empty_choices and accumulated_tool_calls:
            # Check if we have incomplete tool calls (missing ID or function name)
            last_tool_call = (
                accumulated_tool_calls[-1] if accumulated_tool_calls else None
            )
            if self._is_malformed_tool_call(last_tool_call):
                return await self._handle_malformed_function_call_retry(
                    messages,
                    chat_params,
                    user_input,
                    recursion_depth,
                    "incomplete tool call detected, possible MALFORMED_FUNCTION_CALL",
                    {
                        "Incomplete tool call details": last_tool_call,
                        "Total accumulated tool calls": len(accumulated_tool_calls),
                        "stream": stream,
                    },
                )

        if not accumulated_tool_calls:
            # Check 2: Only retry if we have strong signals of a malformed function call
            # A stream with no content is not necessarily an error - it could be intentional
            # Only retry if we have explicit error indicators
            if (
                not accumulated_content
                and not has_rendered_content
                and last_finish_reason == "MALFORMED_FUNCTION_CALL"
            ):
                return await self._handle_malformed_function_call_retry(
                    messages,
                    chat_params,
                    user_input,
                    recursion_depth,
                    "stream ended with MALFORMED_FUNCTION_CALL finish reason",
                    {
                        "Stream end state - had_empty_choices": had_empty_choices,
                        "Stream end state - last_finish_reason": last_finish_reason,
                        "Stream end state - accumulated_reasoning": f"{len(accumulated_reasoning_content) if accumulated_reasoning_content else 0} chars",
                    },
                )

            # Second check: Removed overly aggressive content-based detection
            # Models can legitimately end streams with explanatory content that doesn't require tools
            # Only rely on explicit MALFORMED_FUNCTION_CALL signals from the provider

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

        # Add final newline if we rendered any content (but not for tool executions)
        # Tool executions should not have trailing newlines to maintain clean formatting
        if (
            accumulated_content.strip()
            and (has_rendered_content or remaining_content)
            and not accumulated_tool_calls
        ):
            _managed_stream_print("", use_manager=True)

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
            # Add spacing and agent headers for tool execution if we haven't shown agent title yet
            # or if we had content rendered (meaning this is a separate tool execution block)
            if has_rendered_content or accumulated_content.strip():
                # Add spacing before tool execution block

                console = self._get_console()
                console.print()  # Add spacing

            # Show agent headers for tool execution
            agent_name = getattr(self, "_current_agent_name", None)
            agent_color = getattr(self, "_current_agent_color", None)

            if agent_name:
                from qx.cli.quote_bar_component import get_agent_color

                console = self._get_console()
                self._render_agent_header(console, agent_name, agent_color)

            # Pass empty content if we cleared narration
            streaming_response_message.content = (
                accumulated_content if accumulated_content else None
            )

            # Set agent context for tools to use BorderedMarkdown
            from qx.core.approval_handler import (
                set_global_agent_context,
                clear_global_agent_context,
            )

            if agent_name:
                set_global_agent_context(agent_name, agent_color)

            try:
                result = await self._process_tool_calls_and_continue(
                    streaming_response_message, messages, user_input, recursion_depth
                )

                # After tool execution, ensure next agent response gets headers
                # Reset the agent title flag for the next response
                if hasattr(result, "_reset_agent_title"):
                    result._reset_agent_title = True

                return result
            finally:
                # Clean up agent context
                if agent_name:
                    clear_global_agent_context()
        else:
            return QXRunResult(accumulated_content or "", messages)
