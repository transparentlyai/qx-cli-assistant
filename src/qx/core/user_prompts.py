import asyncio
import logging
from typing import List, Literal, Optional, Tuple, Any

from rich.console import RenderableType  # Corrected import


# Use Any to avoid type checking issues with Console
RichConsole = Any

logger = logging.getLogger(__name__)
_approve_all_active: bool = False
_approve_all_lock = asyncio.Lock()

CHOICE_YES = ("y", "Yes", "yes")
CHOICE_NO = ("n", "No", "no")
CHOICE_APPROVE_ALL = ("a", "Approve All", "all")
CHOICE_CANCEL = ("c", "Cancel", "cancel")

ApprovalDecisionStatus = Literal["approved", "denied", "cancelled", "session_approved"]


async def _execute_prompt_with_live_suspend(
    console: RichConsole, *args: Any, **kwargs: Any
) -> Any:
    prompt_text = args[0] if args else "Enter choice: "
    try:
        import sys

        if hasattr(sys, "stdin") and sys.stdin.isatty():
            print(prompt_text, end="", flush=True)
            line = sys.stdin.readline()
            return line.strip() if line else ""
        else:
            logger.warning(
                "_execute_prompt_with_live_suspend called in non-interactive context"
            )
            return "c"
    except (EOFError, KeyboardInterrupt):
        return "c"
    except Exception as e:
        logger.error(f"Error in _execute_prompt_with_live_suspend: {e}")
        return "c"


async def is_approve_all_active() -> bool:
    global _approve_all_active
    async with _approve_all_lock:
        return _approve_all_active


async def _ask_basic_confirmation(
    console: RichConsole,
    choices: List[Tuple[str, str, str]],
    prompt_message_text: str,
    **_kwargs: Any,
) -> str:
    choices_str = "/".join([choice[0] for choice in choices])
    full_prompt = f"{prompt_message_text} ({choices_str}): "
    while True:
        try:
            user_input = await _execute_prompt_with_live_suspend(console, full_prompt)
            if not user_input:
                continue
            user_input_lower = user_input.lower()
            for key, display, full_word in choices:
                if (
                    user_input_lower == key.lower()
                    or user_input_lower == full_word.lower()
                ):
                    return key
            if user_input_lower == "c" and any(choice[0] == "c" for choice in choices):
                return "c"
            console.print(
                f"[red]Invalid choice. Please enter one of: {choices_str}[/red]"
            )
        except (EOFError, KeyboardInterrupt):
            logger.warning(
                "User cancelled confirmation prompt (_ask_basic_confirmation)."
            )
            console.print("\n[warning]Input cancelled.[/warning]")
            return "c"
        except Exception as e:
            logger.error(f"Error in confirmation prompt: {e}", exc_info=True)
            console.print(f"[red]Error: {e}[/red]")
            return "c"


def _is_textual_environment(console: RichConsole) -> bool:
    return hasattr(console, "_app") and console._app is not None


async def _request_confirmation_textual(
    prompt_message: str,
    console: RichConsole,
    content_to_display: Optional[RenderableType] = None,
    current_value_for_modification: Optional[str] = None,
    default_choice_key: str = "n",
) -> Tuple[ApprovalDecisionStatus, Optional[str]]:
    if await is_approve_all_active():
        console.print("[info]AUTO-APPROVED due to active 'Approve All' session.[/info]")
        return ("session_approved", current_value_for_modification)

    if content_to_display:
        console.print("\n--- Content Preview ---")
        console.print(content_to_display)
        console.print("--- End Preview ---\n")

    app = console._app

    logger.debug(f"_request_confirmation_textual: app type: {type(app)}")
    has_req_confirm = hasattr(app, "request_confirmation")
    has_prompt_text = hasattr(app, "prompt_for_text_input")
    logger.debug(
        f"_request_confirmation_textual: hasattr(app, 'request_confirmation'): {has_req_confirm}"
    )
    logger.debug(
        f"_request_confirmation_textual: hasattr(app, 'prompt_for_text_input'): {has_prompt_text}"
    )

    if not app or not has_req_confirm or not has_prompt_text:
        logger.error(
            "Textual app instance or required methods not found. App: %s, HasReqConfirm: %s, HasPromptText: %s",
            app,
            has_req_confirm,
            has_prompt_text,
        )
        console.print(
            "[yellow]⚠️ AUTO-APPROVED (UI limitation - app methods missing).[/yellow]"
        )
        return ("approved", current_value_for_modification)

    textual_choices_param = "ynac"  # Removed 'm' from choices

    try:
        user_selected_key = await app.request_confirmation(
            message=prompt_message,
            choices=textual_choices_param,
            default=default_choice_key,  # Removed allow_modify argument
        )
        if user_selected_key is None:
            console.print("[info]Operation cancelled or timed out.[/info]")
            return ("cancelled", None)
        if user_selected_key == "y":
            return ("approved", current_value_for_modification)
        elif user_selected_key == "n":
            console.print("[info]Operation denied by user.[/info]")
            return ("denied", None)
        elif user_selected_key == "a":
            global _approve_all_active
            async with _approve_all_lock:
                _approve_all_active = True
            console.print("[info]'Approve All' activated for this session.[/info]")
            return ("session_approved", current_value_for_modification)
        elif user_selected_key == "c":
            console.print("[info]Operation cancelled by user.[/info]")
            return ("cancelled", None)
        else:
            logger.warning(
                f"Unexpected choice '{user_selected_key}' from app.request_confirmation. Denying."
            )
            console.print("[info]Operation denied by user (unexpected choice).[/info]")
            return ("denied", None)
    except Exception as e:
        logger.error(f"Error in confirmation: {e}", exc_info=True)
        console.print(f"[red]Error during confirmation: {e}[/red]")
        return ("cancelled", None)


async def _request_confirmation_terminal(
    prompt_message: str,
    console: RichConsole,
    content_to_display: Optional[RenderableType] = None,
    current_value_for_modification: Optional[str] = None,
    default_choice_key: str = "n",
) -> Tuple[ApprovalDecisionStatus, Optional[str]]:
    if await is_approve_all_active():
        console.print("[info]AUTO-APPROVED due to active 'Approve All' session.[/info]")
        return ("session_approved", current_value_for_modification)
    import sys
    import os

    if (
        not sys.stdin.isatty()
        or os.environ.get("QX_AUTO_APPROVE", "false").lower() == "true"
    ):
        console.print(
            f"[info]AUTO-APPROVED (non-interactive environment):[/info] {prompt_message}"
        )
        return ("approved", current_value_for_modification)
    if content_to_display:
        console.print("\n--- Content Preview ---")
        console.print(content_to_display)
        console.print("--- End Preview ---\n")
    choices_map = [CHOICE_YES, CHOICE_NO]
    choices_map.extend([CHOICE_APPROVE_ALL, CHOICE_CANCEL])
    try:
        user_choice_key = await _ask_basic_confirmation(
            console=console, choices=choices_map, prompt_message_text=prompt_message
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
            console.print("[info]'Approve All' activated for this session.[/info]")
            return ("session_approved", current_value_for_modification)
        elif user_choice_key == "c":
            console.print("[info]Operation cancelled by user.[/info]")
            return ("cancelled", None)
        else:
            logger.warning(f"Unexpected choice '{user_choice_key}'. Cancelling.")
            return ("cancelled", None)
    except Exception as e:
        logger.error(f"Error in request_confirmation_terminal: {e}", exc_info=True)
        console.print(f"[red]Error during confirmation: {e}[/red]")
        return ("cancelled", None)


async def request_confirmation(
    prompt_message: str,
    console: RichConsole,
    content_to_display: Optional[RenderableType] = None,
    current_value_for_modification: Optional[str] = None,
    default_choice_key: str = "n",
) -> Tuple[ApprovalDecisionStatus, Optional[str]]:
    if _is_textual_environment(console):
        return await _request_confirmation_textual(
            prompt_message,
            console,
            content_to_display,
            current_value_for_modification,
            default_choice_key=default_choice_key,
        )
    else:
        return await _request_confirmation_terminal(
            prompt_message,
            console,
            content_to_display,
            current_value_for_modification,
            default_choice_key=default_choice_key,
        )
