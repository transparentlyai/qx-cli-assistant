import asyncio
import json
import logging
import os
import time
from typing import Any, Callable, Dict, List, Optional, cast

import httpx
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

    def set_agent_context(self, agent_name: str, agent_color: Optional[str] = None) -> None:
        """Set the current agent context for quote bar rendering."""
        self._current_agent_name = agent_name
        self._current_agent_color = agent_color

    def clear_agent_context(self) -> None:
        """Clear the current agent context."""
        self._current_agent_name = None
        self._current_agent_color = None

    async def handle_streaming_response(
        self,
        chat_params: Dict[str, Any],
        messages: List[ChatCompletionMessageParam],
        user_input: str,
        recursion_depth: int = 0,
    ) -> Any:
        """Handle streaming response from OpenRouter API."""
        from qx.core.llm import QXRunResult  # Import here to avoid circular imports

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

        # Track if we should show agent title for this response
        show_agent_title = True

        # If this is a continuation after tools, add spacing
        if user_input == "__CONTINUE_AFTER_TOOLS__":
            from rich.console import Console
            from qx.cli.theme import custom_theme

            console = self._console if self._console else Console(theme=custom_theme)
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
                    from rich.console import Console
                    from rich.markdown import Markdown
                    from rich.text import Text
                    from qx.cli.theme import custom_theme, default_markdown_theme

                    # Use the main console if available, otherwise create one with theme
                    rich_console = (
                        self._console if self._console else Console(theme=custom_theme)
                    )

                    # Show agent title for the first meaningful content
                    if show_agent_title:
                        color = get_agent_color(agent_name, agent_color)
                        rich_console.print()  # Add blank line before agent title
                        rich_console.print(Text(agent_name, style="bold"))
                        rich_console.print(Text("─" * len(agent_name), style=color))
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
                    from rich.console import Console
                    from rich.markdown import Markdown
                    from qx.cli.theme import custom_theme, default_markdown_theme
                    from qx.cli.quote_bar_component import BorderedMarkdown, LeftAlignedMarkdown

                    # Use the main console if available, otherwise create one with theme
                    rich_console = (
                        self._console if self._console else Console(theme=custom_theme)
                    )
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
            from rich.console import Console
            from qx.cli.theme import custom_theme

            console = self._console if self._console else Console(theme=custom_theme)

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
                        reasoning_text = delta.reasoning

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
                                    from qx.cli.quote_bar_component import BorderedMarkdown, get_agent_color, LeftAlignedMarkdown
                                    from rich.markdown import Markdown
                                    from rich.console import Console, Group
                                    from rich.text import Text
                                    from qx.cli.theme import custom_theme, dimmed_grey_markdown_theme

                                    # Get agent context for proper formatting
                                    agent_name = getattr(self, "_current_agent_name", None)
                                    agent_color = getattr(self, "_current_agent_color", None)
                                    
                                    reasoning_console = (
                                        self._console
                                        if self._console
                                        else Console(theme=custom_theme)
                                    )
                                    
                                    if agent_name:
                                        color = get_agent_color(agent_name, agent_color)
                                        
                                        # Show title and separator only once at the beginning
                                        if not thinking_title_shown:
                                            # Add blank line before first thinking block
                                            reasoning_console.print()
                                            
                                            thinking_title = f"{agent_name} Thinking"
                                            title_text = Text(thinking_title, style="bold")
                                            separator_line = Text("─" * len(thinking_title), style=f"{color} dim")
                                            reasoning_console.print(title_text)
                                            reasoning_console.print(separator_line)
                                            thinking_title_shown = True
                                        
                                        # Create BorderedMarkdown for the thinking content only
                                        reasoning_md = LeftAlignedMarkdown(reasoning_text, code_theme="rrt")
                                        bordered_thinking = BorderedMarkdown(
                                            reasoning_md,
                                            border_style=f"{color} dim",  # Use dim style for thinking
                                            background_color="#0a0a0a",  # Slightly darker background for thinking
                                            markdown_theme=dimmed_grey_markdown_theme,  # Use dimmed grey theme for thinking
                                        )
                                        
                                        reasoning_console.print(bordered_thinking, end="")
                                    else:
                                        # Fallback without agent context
                                        reasoning_console.print(
                                            f"[dim]{reasoning_text}[/dim]", end=""
                                        )
                                except Exception as e:
                                    # Fallback to original method if anything fails
                                    from rich.console import Console
                                    from qx.cli.theme import custom_theme
                                    
                                    reasoning_console = (
                                        self._console
                                        if self._console
                                        else Console(theme=custom_theme)
                                    )
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
                            from rich.console import Console
                            from qx.cli.theme import custom_theme
                            transition_console = (
                                self._console if self._console else Console(theme=custom_theme)
                            )
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
        if accumulated_content.strip() and (has_rendered_content or remaining_content) and not accumulated_tool_calls:
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
                from rich.console import Console
                from qx.cli.theme import custom_theme

                console = (
                    self._console if self._console else Console(theme=custom_theme)
                )
                console.print()  # Add spacing

            # Show agent headers for tool execution
            agent_name = getattr(self, "_current_agent_name", None)
            agent_color = getattr(self, "_current_agent_color", None)

            if agent_name:
                from qx.cli.quote_bar_component import get_agent_color
                from rich.text import Text
                from rich.console import Console
                from qx.cli.theme import custom_theme

                console = (
                    self._console if self._console else Console(theme=custom_theme)
                )
                color = get_agent_color(agent_name, agent_color)
                console.print()  # Add blank line before agent title
                console.print(Text(agent_name, style="bold"))
                console.print(Text("─" * len(agent_name), style=color))

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
