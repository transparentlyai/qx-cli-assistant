import asyncio
import logging
import os
from typing import List, Literal, Optional, Tuple, Any

from rich.console import RenderableType
import signal
from rich.prompt import Prompt

from qx.core.state_manager import details_manager

RichConsole = Any

logger = logging.getLogger(__name__)
_approve_all_active: bool = False
_approve_all_lock = asyncio.Lock()

# Flag to control console manager usage (disabled when called from ConsoleManager)
_disable_console_manager = False


def _managed_print(console: RichConsole, content: Any, **kwargs) -> None:
    """
    Print helper that optionally uses console manager for thread-safe output.
    
    This is disabled when called from within the ConsoleManager to prevent
    circular dependencies.
    """
    global _disable_console_manager
    
    if _disable_console_manager:
        # Direct print when called from ConsoleManager
        console.print(content, **kwargs)
        return
    
    try:
        # Try to use console manager for thread-safe printing
        from qx.core.console_manager import get_console_manager
        manager = get_console_manager()
        if manager and manager._running:
            style = kwargs.get('style')
            markup = kwargs.get('markup', True)
            end = kwargs.get('end', '\n')
            manager.print(content, style=style, markup=markup, end=end, console=console)
        else:
            console.print(content, **kwargs)
    except Exception:
        # Fallback to direct print if manager unavailable
        console.print(content, **kwargs)

CHOICE_YES = ("y", "Yes", "yes")
CHOICE_NO = ("n", "No", "no")
CHOICE_APPROVE_ALL = ("a", "Approve All", "all")
CHOICE_CANCEL = ("c", "Cancel", "cancel")

ApprovalDecisionStatus = Literal["approved", "denied", "cancelled", "session_approved"]


def _disable_ctrl_c():
    """Temporarily disable Ctrl+C signal handling"""
    try:
        return signal.signal(signal.SIGINT, signal.SIG_IGN)
    except ValueError:
        # Signal handling only works in main thread
        return None


def _restore_ctrl_c(old_handler):
    """Restore previous Ctrl+C signal handling"""
    if old_handler is not None:
        try:
            signal.signal(signal.SIGINT, old_handler)
        except ValueError:
            # Signal handling only works in main thread
            pass


def _suspend_global_hotkeys():
    """Suspend global hotkeys during approval prompts."""
    try:
        from qx.core.hotkey_manager import get_hotkey_manager

        manager = get_hotkey_manager()
        if manager and manager.running:
            manager.stop()
            logger.debug("Suspended global hotkeys for approval prompt")
            return True
    except Exception as e:
        logger.debug(f"Could not suspend global hotkeys: {e}")
    return False


def _resume_global_hotkeys():
    """Resume global hotkeys after approval prompts."""
    try:
        from qx.core.hotkey_manager import get_hotkey_manager

        manager = get_hotkey_manager()
        if manager and not manager.running:
            manager.start()
            logger.debug("Resumed global hotkeys after approval prompt")
    except Exception as e:
        logger.debug(f"Could not resume global hotkeys: {e}")


async def _execute_prompt_with_live_suspend(
    console: RichConsole, *args: Any, **kwargs: Any
) -> Any:
    prompt_text = args[0] if args else "Enter choice: "
    try:
        import sys

        if hasattr(sys, "stdin") and sys.stdin.isatty():
            return await asyncio.to_thread(input, prompt_text)
        else:
            logger.warning(
                "_execute_prompt_with_live_suspend called in non-interactive context. Returning 'c'."
            )
            return "c"
    except (EOFError, KeyboardInterrupt):
        logger.warning(
            "Input cancelled via EOF/KeyboardInterrupt in _execute_prompt_with_live_suspend."
        )
        return "c"
    except Exception as e:
        logger.error(f"Error in _execute_prompt_with_live_suspend: {e}")
        return "c"


async def is_approve_all_active() -> bool:
    global _approve_all_active
    async with _approve_all_lock:
        return _approve_all_active


async def is_details_active() -> bool:
    return await details_manager.is_active()


async def _ask_basic_confirmation(
    console: RichConsole,
    choices: List[Tuple[str, str, str]],
    prompt_message_text: str,
    **_kwargs: Any,
) -> str:
    choices_str_list = [choice[0] for choice in choices]
    choices_display_str = "/".join(choices_str_list)
    full_prompt = f"{prompt_message_text} ({choices_display_str}): "

    # Create mapping of all valid inputs to their canonical choice keys
    choice_mapping = {}
    for choice_tuple in choices:
        canonical_key = choice_tuple[0].lower()
        for variant in choice_tuple:
            choice_mapping[variant.lower()] = canonical_key

    # Suspend global hotkeys during approval prompt
    hotkeys_suspended = _suspend_global_hotkeys()

    try:
        while True:
            try:
                old_handler = _disable_ctrl_c()
                try:
                    user_input = await asyncio.to_thread(
                        input,
                        full_prompt
                    )
                finally:
                    _restore_ctrl_c(old_handler)
                if user_input:
                    user_input_lower = user_input.strip().lower()
                    if user_input_lower in choice_mapping:
                        return choice_mapping[user_input_lower]
                    else:
                        console.print(f"[dim red]Invalid choice '{user_input}'. Please choose from: {choices_display_str}[/dim red]")
                        continue
            except Exception as e:
                try:
                    _restore_ctrl_c(old_handler)
                except Exception:
                    pass
                logger.error(f"Error in confirmation prompt: {e}", exc_info=True)
                console.print("[dim red]Error with prompt, please try again.[/dim red]")
                continue
    finally:
        # Always resume global hotkeys
        if hotkeys_suspended:
            _resume_global_hotkeys()




async def _request_confirmation_terminal(
    prompt_message: str,
    console: RichConsole,
    content_to_display: Optional[RenderableType] = None,
    current_value_for_modification: Optional[str] = None,
    default_choice_key: str = "n",
) -> Tuple[ApprovalDecisionStatus, Optional[str]]:
    if await is_approve_all_active():
        _managed_print(console, "[info]AUTO-APPROVED due to active 'Approve All' session.[/info]")
        return ("session_approved", current_value_for_modification)

    import sys

    if (
        not sys.stdin.isatty()
        or os.environ.get("QX_AUTO_APPROVE", "false").lower() == "true"
    ):
        console.print(f"[info]AUTO-APPROVED (non-interactive):[/info] {prompt_message}")
        return ("approved", current_value_for_modification)

    if content_to_display:
        console.print("\n--- Content Preview ---")
        console.print(content_to_display)
        console.print("--- End Preview ---\n")

    choices_map = [CHOICE_YES, CHOICE_NO, CHOICE_APPROVE_ALL, CHOICE_CANCEL]

    try:
        user_choice_key = await _ask_basic_confirmation(
            console=console,
            choices=choices_map,
            prompt_message_text=prompt_message,
        )
        if user_choice_key == "y":
            return ("approved", current_value_for_modification)
        elif user_choice_key == "n":
            console.print("[info]Operation denied by user.[/info]")
            return ("denied", None)
        elif user_choice_key == "a":
            global _approve_all_active
            async with _approve_all_lock:
                _approve_all_active = True
            _managed_print(console, "[info]'Approve All' activated for this session.[/info]")
            return ("session_approved", current_value_for_modification)
        elif user_choice_key == "c":
            console.print("[info]Operation cancelled by user.[/info]")
            return ("cancelled", None)
        else:
            logger.warning(f"Unexpected choice '{user_choice_key}'. Cancelling.")
            return ("cancelled", None)
    except Exception as e:
        logger.error(f"Error in request_confirmation_terminal: {e}", exc_info=True)
        console.print(f"[error]Error during confirmation: {e}[/]")
        return ("cancelled", None)


async def request_confirmation(
    prompt_message: str,
    console: RichConsole,
    content_to_display: Optional[RenderableType] = None,
    current_value_for_modification: Optional[str] = None,
    default_choice_key: str = "n",
) -> Tuple[ApprovalDecisionStatus, Optional[str]]:
    return await _request_confirmation_terminal(
        prompt_message,
        console,
        content_to_display,
        current_value_for_modification,
        default_choice_key,
    )


async def get_user_choice_from_options_async(
    console: RichConsole,
    prompt_text_with_options: str,
    valid_choices: List[str],
    default_choice: Optional[str] = None,
) -> Optional[str]:
    processed_valid_choices = [choice.lower() for choice in valid_choices]
    processed_default_choice = default_choice.lower() if default_choice else None

    if not processed_valid_choices:
        logger.error("get_user_choice_from_options_async called with no valid_choices.")
        return None

    if (
        processed_default_choice
        and processed_default_choice not in processed_valid_choices
    ):
        logger.warning(
            f"Default choice '{processed_default_choice}' not in valid_choices. Ignoring."
        )
        processed_default_choice = None

    import sys

    if (
        not sys.stdin.isatty()
        or os.environ.get("QX_AUTO_APPROVE", "false").lower() == "true"
    ):
        auto_choice = None
        if processed_default_choice in processed_valid_choices:
            auto_choice = processed_default_choice
        elif "y" in processed_valid_choices:
            auto_choice = "y"
        elif "a" in processed_valid_choices:
            auto_choice = "a"
        elif processed_valid_choices:
            auto_choice = processed_valid_choices[0]

        if auto_choice:
            console.print(
                f"{prompt_text_with_options}[italic dim](Auto-selected: {auto_choice})[/]"
            )
            return auto_choice
        else:
            console.print(
                f"{prompt_text_with_options}[italic dim](No auto-selection)[/]"
            )
            return None

    # Suspend global hotkeys during approval prompt
    hotkeys_suspended = _suspend_global_hotkeys()

    try:
        while True:
            try:
                old_handler = _disable_ctrl_c()
                try:
                    user_input = await asyncio.to_thread(
                        input,
                        prompt_text_with_options
                    )
                finally:
                    _restore_ctrl_c(old_handler)
                if user_input:
                    user_input_lower = user_input.strip().lower()
                    if user_input_lower in processed_valid_choices:
                        return user_input_lower
                    else:
                        console.print(f"[dim red]Invalid choice '{user_input}'. Please choose from: {', '.join(valid_choices)}[/dim red]")
                        continue
                else:
                    console.print("[dim red]Please select an option.[/dim red]")
                    continue
            except Exception as e:
                try:
                    _restore_ctrl_c(old_handler)
                except Exception:
                    pass
                logger.error(f"Error during prompt: {e}", exc_info=True)
                console.print("[dim red]Error with prompt, please try again.[/dim red]")
                continue
    finally:
        # Always resume global hotkeys
        if hotkeys_suspended:
            _resume_global_hotkeys()
