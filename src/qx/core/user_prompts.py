import asyncio
import logging
from typing import List, Literal, Optional, Tuple, Any

from rich.console import RenderableType  # Corrected import
from rich.prompt import Prompt  # For interactive input

# Use Any to avoid type checking issues with Console
RichConsole = Any  # Note: rich.console.Console is the actual type

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
            # This is a simplified version. Rich Prompt.ask is preferred for real use.
            # print(prompt_text, end="", flush=True)
            # line = sys.stdin.readline()
            # return line.strip() if line else ""
            # For async, Prompt.ask needs to be run in a thread or a different approach
            # is needed if Textual app is running.
            # For now, this function is less critical as request_confirmation handles textual/terminal.
            # The new get_user_choice_from_options_async will use Prompt.ask directly.
            logger.warning(
                "_execute_prompt_with_live_suspend fallback used. Consider direct Prompt.ask for new features."
            )
            # Fallback to a simple input for non-textual, non-Prompt.ask scenarios
            # This part might need to be removed or refactored if Textual is always the driver for prompts.
            return await asyncio.to_thread(input, prompt_text)

        else:
            logger.warning(
                "_execute_prompt_with_live_suspend called in non-interactive context or stdin not a TTY. Returning 'c'."
            )
            return "c"  # Default to cancel in non-interactive
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


async def _ask_basic_confirmation(
    console: RichConsole,  # Should be rich.console.Console
    choices: List[Tuple[str, str, str]],
    prompt_message_text: str,
    **_kwargs: Any,
) -> str:
    choices_str_list = [choice[0] for choice in choices]
    choices_display_str = "/".join(choices_str_list)
    full_prompt = f"{prompt_message_text} ({choices_display_str}): "

    # This function is called by _request_confirmation_terminal
    # which already checks for non-interactive. So Prompt.ask should be safe here.
    while True:
        try:
            # Use Rich Prompt for better handling
            user_input = await asyncio.to_thread(
                Prompt.ask,
                full_prompt,
                choices=choices_str_list,  # Pass only the keys
                show_choices=False,  # The prompt already shows them
                console=console,
            )

            if not user_input:
                # Should not happen with Prompt.ask if choices are enforced
                console.print(
                    "[warning]Empty input received. Please try again.[/warning]"
                )
                continue

            user_input_lower = user_input.lower()
            # Prompt.ask with choices should return one of the choices, so direct mapping is fine.
            if user_input_lower in choices_str_list:
                return user_input_lower  # Return the chosen key directly

            # This part should ideally not be reached if Prompt.ask enforces choices
            console.print(
                f"[error]Invalid choice '{user_input_lower}'. Please enter one of: {choices_display_str}[/]"
            )

        except (EOFError, KeyboardInterrupt):
            logger.warning(
                "User cancelled confirmation prompt (_ask_basic_confirmation)."
            )
            console.print("\n[warning]Input cancelled.[/warning]")
            return "c"  # Default to cancel
        except Exception as e:
            logger.error(f"Error in confirmation prompt: {e}", exc_info=True)
            console.print(f"[error]Error: {e}[/]")
            return "c"  # Default to cancel


def _is_textual_environment(console: RichConsole) -> bool:
    return hasattr(console, "_app") and console._app is not None


async def _request_confirmation_textual(
    prompt_message: str,
    console: RichConsole,  # Should be rich.console.Console
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

    app = console._app  # Assuming console is Textual's console wrapper

    logger.debug(f"_request_confirmation_textual: app type: {type(app)}")
    has_req_confirm = hasattr(app, "request_confirmation")
    # has_prompt_text = hasattr(app, "prompt_for_text_input") # Not used in this path anymore
    logger.debug(
        f"_request_confirmation_textual: hasattr(app, 'request_confirmation'): {has_req_confirm}"
    )

    if not app or not has_req_confirm:
        logger.error(
            "Textual app instance or request_confirmation method not found. App: %s, HasReqConfirm: %s",
            app,
            has_req_confirm,
        )
        console.print(
            "[warning]⚠️ AUTO-APPROVED (UI limitation - app.request_confirmation missing).[/]"
        )
        return ("approved", current_value_for_modification)

    textual_choices_param = "ynac"

    try:
        user_selected_key = await app.request_confirmation(
            message=prompt_message,
            choices=textual_choices_param,
            default=default_choice_key,
        )
        if user_selected_key is None:  # User cancelled (e.g. Esc in Textual dialog)
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
        logger.error(f"Error in textual confirmation: {e}", exc_info=True)
        console.print(f"[error]Error during confirmation: {e}[/]")
        return ("cancelled", None)


async def _request_confirmation_terminal(
    prompt_message: str,
    console: RichConsole,  # Should be rich.console.Console
    content_to_display: Optional[RenderableType] = None,
    current_value_for_modification: Optional[str] = None,
    default_choice_key: str = "n",  # Not directly used by Prompt.ask default, but kept for signature
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

    choices_map = [CHOICE_YES, CHOICE_NO, CHOICE_APPROVE_ALL, CHOICE_CANCEL]

    try:
        # _ask_basic_confirmation now uses Prompt.ask, so it handles interaction
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
            logger.warning(
                f"Unexpected choice '{user_choice_key}' from _ask_basic_confirmation. Cancelling."
            )
            return ("cancelled", None)

    except Exception as e:
        logger.error(f"Error in request_confirmation_terminal: {e}", exc_info=True)
        console.print(f"[error]Error during confirmation: {e}[/]")
        return ("cancelled", None)


async def request_confirmation(
    prompt_message: str,
    console: RichConsole,  # Should be rich.console.Console
    content_to_display: Optional[RenderableType] = None,
    current_value_for_modification: Optional[str] = None,
    default_choice_key: str = "n",
) -> Tuple[ApprovalDecisionStatus, Optional[str]]:
    """
    Requests user confirmation for an action, adapting to Textual or terminal environment.

    This function is the main entry point for simple Yes/No/Approve All/Cancel confirmations.
    For more dynamic options, plugins should use ApprovalHandler which in turn might call
    get_user_choice_from_options_async.
    """
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


async def get_user_choice_from_options_async(
    console: RichConsole,  # Should be rich.console.Console
    prompt_text_with_options: str,  # e.g., "Action? ([a])Approve / ([d])Deny / ([c])Cancel: "
    valid_choices: List[str],  # e.g., ['a', 'd', 'c']
    default_choice: Optional[str] = None,  # Optional default choice key
) -> Optional[str]:  # Returns the chosen key (e.g., 'a') or None if cancelled
    """
    Interactively prompts the user to make a choice from a list of valid options.
    This function is intended to be called by ApprovalHandler or other parts of the system
    that require dynamic, character-based choices in a terminal environment.

    Args:
        console: The Rich Console instance for output.
        prompt_text_with_options: The full prompt string, including the options display.
                                  Example: "Your choice? ([y])Yes / ([n])No / ([c])Cancel: "
        valid_choices: A list of lowercase strings representing the valid single-character choices.
                       Example: ['y', 'n', 'c']
        default_choice: An optional character that is the default choice.

    Returns:
        The user's chosen character (lowercase) if a valid choice is made,
        or None if the input is cancelled (e.g., by Ctrl+C, EOFError).
    """
    # Ensure console is the correct type for Prompt.ask if not already checked by caller
    # from rich.console import Console as RichConsoleType
    # if not isinstance(console, RichConsoleType):
    #     logger.error(f"get_user_choice_from_options_async expects rich.console.Console, got {type(console)}")
    #     # Fallback or raise error, for now, we assume it's correct or Prompt.ask handles it.

    # Ensure valid_choices are lowercase for consistent checking
    processed_valid_choices = [choice.lower() for choice in valid_choices]
    processed_default_choice = default_choice.lower() if default_choice else None

    if not processed_valid_choices:
        logger.error("get_user_choice_from_options_async called with no valid_choices.")
        return None  # Or raise an error

    # If a default choice is provided and is valid, make it the default for Prompt.ask
    if (
        processed_default_choice
        and processed_default_choice not in processed_valid_choices
    ):
        logger.warning(
            f"Default choice '{processed_default_choice}' not in valid_choices. Ignoring default."
        )
        processed_default_choice = None

    # Check if running in a non-interactive environment
    import sys
    import os

    if (
        not sys.stdin.isatty()
        or os.environ.get("QX_AUTO_APPROVE", "false").lower() == "true"
    ):
        # In non-interactive mode, or if QX_AUTO_APPROVE is set:
        # - If a default is valid, use it.
        # - Else if 'y' (yes/approve) is an option, use it.
        # - Else if 'a' (approve all) is an option, use it.
        # - Else, pick the first valid option.
        # - If no options, return None (though we check for empty valid_choices earlier).
        auto_choice = None
        if processed_default_choice in processed_valid_choices:
            auto_choice = processed_default_choice
        elif "y" in processed_valid_choices:
            auto_choice = "y"
        elif "a" in processed_valid_choices:
            auto_choice = "a"
        elif processed_valid_choices:  # Pick the first one
            auto_choice = processed_valid_choices[0]

        if auto_choice:
            console.print(
                f"{prompt_text_with_options}[italic dim](Auto-selected: {auto_choice} in non-interactive mode)[/]"
            )
            return auto_choice
        else:
            console.print(
                f"{prompt_text_with_options}[italic dim](No suitable auto-selection in non-interactive mode)[/]"
            )
            return None

    # Interactive mode:
    while True:
        try:
            # Mauro: This is where you'll use rich.prompt.Prompt.ask
            # The `prompt_text_with_options` already contains the full string like "([a])Approve / ([d])Deny: "
            # `processed_valid_choices` is the list of allowed characters e.g. ['a', 'd', 'c']
            # `processed_default_choice` is the default character if one was validly provided.

            # Use Prompt.ask for interactive user input
            user_input = await asyncio.to_thread(
                Prompt.ask,
                prompt_text_with_options,  # This is the full prompt text
                choices=processed_valid_choices,  # List of allowed characters
                default=processed_default_choice,  # The default character, if any
                show_choices=False,  # Set to False because choices are in prompt_text_with_options
                console=console
            )
            return user_input.lower() if user_input else None

        except (EOFError, KeyboardInterrupt):
            logger.warning("User cancelled input via EOF/KeyboardInterrupt.")
            console.print("\n[warning]Input cancelled.[/warning]")
            return None  # Indicate cancellation
        except Exception as e:
            logger.error(f"Error during prompt: {e}", exc_info=True)
            console.print(f"[error]An error occurred: {e}[/]")
            return None  # Indicate error/cancellation
