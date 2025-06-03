import asyncio
import logging
import subprocess
import sys
from typing import Any, List, Optional

from openai.types.chat import ChatCompletionMessageParam
from prompt_toolkit import PromptSession
from prompt_toolkit.application import run_in_terminal  # Import run_in_terminal
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.filters import Condition
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.styles import Style
from prompt_toolkit.validation import ValidationError, Validator
from rich.markdown import Markdown

from qx.cli.commands import _handle_inline_command
from qx.cli.theme import themed_console
from qx.cli.completer import QXCompleter
from qx.cli.history import QXHistory
from qx.core.history_utils import parse_history_for_fzf
from qx.core.llm import QXLLMAgent, query_llm
from qx.core.paths import QX_HISTORY_FILE
from qx.core.session_manager import clean_old_sessions, save_session
from qx.core.user_prompts import _approve_all_lock  # Import the flag and lock

logger = logging.getLogger("qx")

# State tracking for multiline mode and pending text
is_multiline_mode = [False]  # Use list for mutable reference in closures
pending_text = [""]  # Text to restore when toggling modes


class SingleLineNonEmptyValidator(Validator):
    """Validator that prevents empty input submission only in single-line mode."""

    def validate(self, document):
        # Only validate (prevent empty) in single-line mode
        if not is_multiline_mode[0]:  # Single-line mode
            text = document.text.strip()
            if not text:
                # Prevent submission by raising validation error
                # Using empty message to avoid showing error text
                raise ValidationError(message="")
        # In multiline mode, allow empty submissions (for mode switching)


def get_bottom_toolbar(qx_history: QXHistory):
    """Return formatted text for the bottom toolbar."""
    # Build toolbar content
    toolbar_content = [
        ("class:bottom-toolbar.key", " Ctrl+R "),
        ("class:bottom-toolbar.text", "fzf search  "),
        ("class:bottom-toolbar.key", " Alt+Enter "),
        ("class:bottom-toolbar.text", "toggle mode  "),
        ("class:bottom-toolbar.key", " Tab "),
        ("class:bottom-toolbar.text", "complete  "),
        ("class:bottom-toolbar.key", " Shift+Tab "),  # Add Shift+Tab to toolbar
        ("class:bottom-toolbar.text", "toggle approve all  "),  # Add description
    ]

    return toolbar_content


async def _handle_llm_interaction(
    agent: QXLLMAgent,
    user_input: str,
    current_message_history: Optional[List[ChatCompletionMessageParam]],
    code_theme_to_use: str,
    plain_text_output: bool = False,
) -> Optional[List[ChatCompletionMessageParam]]:
    """
    Handles the interaction with the LLM, including streaming display and response processing.
    Returns the updated message history.
    """
    run_result: Optional[Any] = None

    try:
        run_result = await query_llm(
            agent,
            user_input,
            message_history=current_message_history,
            console=themed_console,  # Provide console for inline mode
        )
    except asyncio.CancelledError:
        # Handle cancellation gracefully
        logger.info("LLM interaction cancelled by user")
        themed_console.print("\nOperation cancelled", style="warning")
        return current_message_history
    except Exception as e:
        logger.error(f"Error during LLM interaction: {e}", exc_info=True)
        themed_console.print(f"Error: {e}", style="error")
        return current_message_history

    if run_result:
        if hasattr(run_result, "output"):
            output_content = (
                str(run_result.output) if run_result.output is not None else ""
            )
            if plain_text_output:
                print(output_content)
            else:
                # For streaming, content is already displayed during the stream
                if not agent.enable_streaming and output_content.strip():
                    themed_console.print()
                    themed_console.print(
                        Markdown(output_content, code_theme="rrt"), markup=True
                    )
                    themed_console.print()
            if hasattr(run_result, "all_messages"):
                return run_result.all_messages()
            else:
                logger.warning("run_result is missing 'all_messages' attribute.")
                return current_message_history
        else:
            logger.error(
                f"run_result is missing 'output' attribute. run_result type: {type(run_result)}, value: {run_result}"
            )
            if plain_text_output:
                sys.stderr.write("Error: Unexpected response structure from LLM.\n")
            else:
                themed_console.print(
                    "Error: Unexpected response structure from LLM.", style="error"
                )
            return current_message_history
    else:
        if plain_text_output:
            sys.stdout.write("Info: No response generated or an error occurred.\n")
        else:
            themed_console.print(
                "Info: No response generated or an error occurred.", style="info"
            )
        return current_message_history


async def _run_inline_mode(
    llm_agent: QXLLMAgent,
    current_message_history: Optional[List[ChatCompletionMessageParam]],
    keep_sessions: int,
):
    """
    Run the interactive inline mode with prompt_toolkit input."""

    # Create custom history that handles Qx format
    qx_history = QXHistory(QX_HISTORY_FILE)

    # Create custom completer that handles both commands and paths
    qx_completer = QXCompleter()

    # Create custom style for input text and bottom toolbar
    input_style = Style.from_dict(
        {
            # Style for the text as user types
            "": "fg:#ff005f",
            # Style for selected text
            "selected": "fg:#ff005f bg:#050505 reverse",
            # Style for the bottom toolbar
            "bottom-toolbar": "bg:#222222 fg:#888888",
            "bottom-toolbar.text": "bg:#222222 fg:#cccccc",
            "bottom-toolbar.key": "bg:#222222 fg:#ff5f00 bold",
        }
    )

    # Create key bindings for enhanced functionality
    bindings = KeyBindings()

    @bindings.add("c-c")
    def _(event):
        """Handle Ctrl+C - Emergency stop without exiting"""
        # Get all current tasks and cancel them
        current_task = asyncio.current_task()
        if current_task:
            current_task.cancel()

        # Cancel the current input and return to prompt
        event.current_buffer.reset()
        event.app.exit(exception=KeyboardInterrupt, style="class:aborting")

    @bindings.add("c-d")
    def _(event):
        """Handle Ctrl+D"""
        event.app.exit(exception=EOFError, style="class:exiting")

    @bindings.add("c-r")
    def _(event):
        """Handle Ctrl+R for fzf history search"""
        try:
            # Get history entries for fzf
            history_entries = parse_history_for_fzf(QX_HISTORY_FILE)
            if not history_entries:
                return

            # Prepare fzf input (display strings)
            fzf_input = "\n".join([display for display, _ in reversed(history_entries)])

            # Run fzf for selection with terminal restoration
            fzf_process = subprocess.run(
                ["fzf", "--ansi", "--reverse", "--height", "40%", "--no-clear"],
                input=fzf_input,
                capture_output=True,
                text=True,
            )

            # Always force redraw after fzf, regardless of selection
            event.app.invalidate()
            event.app.renderer.reset()

            if fzf_process.returncode == 0 and fzf_process.stdout.strip():
                selected_display = fzf_process.stdout.strip()

                # Find the original command for the selected display
                for display, original in history_entries:
                    if display == selected_display:
                        # Set the selected command as current buffer text
                        event.current_buffer.text = original
                        event.current_buffer.cursor_position = len(original)
                        break
        except Exception:
            # Always try to restore terminal state on any error
            try:
                event.app.invalidate()
                event.app.renderer.reset()
            except Exception:
                pass

    @bindings.add("escape", "enter")  # Alt+Enter
    def _(event):
        """Handle Alt+Enter for multiline toggle/submit"""
        buffer = event.current_buffer

        if is_multiline_mode[0]:
            # Submit if in multiline mode
            buffer.validate_and_handle()
        else:
            # Toggle to multiline mode - we need to restart the prompt
            is_multiline_mode[0] = True
            # Store the current text
            current_text = buffer.text
            # Add newline if there's existing text
            if current_text.strip():
                current_text += "\n"
            # Store text for restoration
            pending_text[0] = current_text

            # Exit current prompt and restart with multiline mode
            event.app.exit(result="__TOGGLE_MULTILINE__")

    @bindings.add("s-tab")  # Shift+Tab
    async def _(event):
        """Toggle 'Approve All' mode."""
        import qx.core.user_prompts as user_prompts

        async with _approve_all_lock:
            user_prompts._approve_all_active = not user_prompts._approve_all_active

            def print_status():
                if user_prompts._approve_all_active:
                    themed_console.print(
                        "✓ 'Approve All' mode activated.\n", style="success"
                    )
                else:
                    themed_console.print(
                        "✗ 'Approve All' mode deactivated.\n", style="warning"
                    )

            run_in_terminal(print_status)
        # Invalidate to redraw toolbar and reflect changes immediately
        event.app.invalidate()

    # Create prompt session with enhanced features
    session: PromptSession[str] = PromptSession(
        history=qx_history,
        auto_suggest=AutoSuggestFromHistory(),
        enable_history_search=False,  # Disable built-in search, we use fzf
        completer=qx_completer,  # type: ignore
        complete_style="multi-column",  # type: ignore
        key_bindings=bindings,
        mouse_support=False,  # Disabled to allow terminal scrolling
        wrap_lines=True,
        multiline=Condition(lambda: is_multiline_mode[0]),
        validator=SingleLineNonEmptyValidator(),
        validate_while_typing=False,  # Only validate on submit attempt
        style=input_style,  # Apply custom input text styling
        bottom_toolbar=lambda: get_bottom_toolbar(qx_history),  # Add status footer
    )

    try:
        while True:
            # Start with single-line mode for each new input
            if not is_multiline_mode[0]:
                is_multiline_mode[0] = False

            # Get the appropriate prompt based on current mode
            current_prompt = (
                HTML('<style fg="#0087ff">MULTILINE⏵</style> ')
                if is_multiline_mode[0]
                else HTML('<style fg="#ff5f00">Qx⏵</style> ')
            )

            # Show prompt and get user input with prompt_toolkit
            default_text = pending_text[0] if pending_text[0] else ""
            result = await session.prompt_async(
                current_prompt,
                wrap_lines=True,
                default=default_text,  # Restore text after mode toggle
            )

            # Clear any pending text after successful prompt
            if result != "__TOGGLE_MULTILINE__":
                pending_text[0] = ""

            # Check if this was a mode toggle
            if result == "__TOGGLE_MULTILINE__":
                # Clear the previous prompt line before showing multiline prompt
                try:
                    # Move cursor up and clear the line using Rich console
                    print("\033[1A\r\033[K", end="", flush=True)
                except Exception:
                    pass
                # Continue loop to show multiline prompt with stored text
                continue

            user_input = result.strip()
            logger.debug(f"User input received: '{user_input}'")

            if not user_input:
                # Handle empty input differently based on current mode
                was_multiline = is_multiline_mode[0]
                if was_multiline:
                    # Multiline mode: clear prompt and switch to single line mode
                    try:
                        # Move cursor up and clear the multiline prompt line
                        print("\033[1A\r\033[K", end="", flush=True)
                    except Exception:
                        pass
                    # Reset multiline mode and show new single line prompt
                    is_multiline_mode[0] = False
                # Continue to next prompt iteration (both modes need this)
                continue

            if user_input.lower() in ["exit", "quit"]:
                break

            # Clear multiline prompt if transitioning from multiline to normal mode
            was_multiline = is_multiline_mode[0]
            if was_multiline:
                try:
                    # Move cursor up and clear the multiline prompt line
                    print("\033[1A\r\033[K", end="", flush=True)
                except Exception:
                    pass

            # Reset multiline mode after successful submission
            is_multiline_mode[0] = False

            # Handle commands
            if user_input.startswith("/"):
                await _handle_inline_command(user_input, llm_agent)
                continue

            # Handle LLM query as a cancellable task
            llm_task = asyncio.create_task(
                _handle_llm_interaction(
                    llm_agent,
                    user_input,
                    current_message_history,
                    "rrt",  # code theme
                    plain_text_output=False,
                )
            )

            try:
                current_message_history = await llm_task
            except asyncio.CancelledError:
                themed_console.print("\nOperation cancelled", style="warning")
                llm_task.cancel()
                try:
                    await llm_task
                except asyncio.CancelledError:
                    pass

            # Save session
            if current_message_history:
                save_session(current_message_history)
                clean_old_sessions(keep_sessions)

    except KeyboardInterrupt:
        # Emergency stop - don't exit, just interrupt current operation
        themed_console.print(
            "\nOperation interrupted. Returning to prompt...", style="warning"
        )
        # Continue the loop to show a new prompt
        while True:
            try:
                # Restart the prompt session
                current_prompt = HTML('<style fg="#ff5f00">Qx⏵</style> ')
                result = await session.prompt_async(current_prompt, wrap_lines=True)

                user_input = result.strip()
                if not user_input:
                    continue

                # Handle commands or LLM interaction
                if user_input.startswith("/"):
                    await _handle_inline_command(user_input, llm_agent)
                else:
                    # Handle LLM query as a cancellable task
                    llm_task = asyncio.create_task(
                        _handle_llm_interaction(
                            llm_agent,
                            user_input,
                            current_message_history,
                            "rrt",
                            plain_text_output=False,
                        )
                    )

                    try:
                        current_message_history = await llm_task
                        if current_message_history:
                            save_session(current_message_history)
                            clean_old_sessions(keep_sessions)
                    except asyncio.CancelledError:
                        themed_console.print("\nOperation cancelled", style="warning")
                        llm_task.cancel()
                        try:
                            await llm_task
                        except asyncio.CancelledError:
                            pass

            except KeyboardInterrupt:
                themed_console.print(
                    "\nOperation interrupted. Returning to prompt...", style="warning"
                )
                continue
            except EOFError:
                break
    except EOFError:
        pass
    except Exception as e:
        logger.error(f"Error in inline mode: {e}", exc_info=True)
        themed_console.print(f"Error: {e}", style="error")
    finally:
        # Ensure history is flushed when the session ends
        qx_history.flush_history()
