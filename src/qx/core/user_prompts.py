import logging
import datetime
from typing import Callable, List, Literal, Optional, Tuple, Union, Any, Protocol

class ConsoleProtocol(Protocol):
    def print(self, *args, **kwargs): ...

RichConsole = ConsoleProtocol  # Type alias for backward compatibility
RenderableType = str  # Simplified type

logger = logging.getLogger(__name__)

# --- State for "Approve All" ---
_approve_all_until: Optional[datetime.datetime] = None
DEFAULT_APPROVE_ALL_DURATION_MINUTES: int = 15
# --- End State for "Approve All" ---

# Define standard choice tuples: (key, display_text, full_word_match)
CHOICE_YES = ("y", "Yes", "yes")
CHOICE_NO = ("n", "No", "no")
CHOICE_MODIFY = ("m", "Modify", "modify")
CHOICE_APPROVE_ALL = ("a", "Approve All", "all")
CHOICE_CANCEL = ("c", "Cancel", "cancel")

ApprovalDecisionStatus = Literal["approved", "denied", "modified", "cancelled", "session_approved"]


async def _execute_prompt_with_live_suspend(
    console: RichConsole, *args: Any, **kwargs: Any
) -> Any:
    """
    Simplified prompt execution.
    """
    prompt_text = args[0] if args else "Enter choice: "
    try:
        import sys
        print(prompt_text, end="", flush=True)
        line = sys.stdin.readline()
        return line.strip() if line else ""
    except (EOFError, KeyboardInterrupt):
        return ""


def is_approve_all_active(console: RichConsole) -> bool:
    """
    Checks if the 'Approve All' session is currently active.
    If expired, it resets the state and informs the user.
    """
    global _approve_all_until
    if _approve_all_until:
        if datetime.datetime.now() < _approve_all_until:
            return True
        else:
            console.print("[yellow]INFO:[/yellow] 'Approve All' session has expired.")
            logger.info("'Approve All' session has expired.")
            _approve_all_until = None
    return False


async def _ask_duration(console: RichConsole, prompt_message_text: str, default: int) -> int:
    """
    Asks the user for a duration in minutes.
    """
    pt_prompt_message = f"{prompt_message_text}: "
    while True:
        try:
            duration_str = await _execute_prompt_with_live_suspend(
                console,
                pt_prompt_message, 
                default=str(default)
            )
            duration = int(duration_str)
            if duration < 0:
                console.print("[red]Please enter a non-negative number of minutes.[/red]")
                continue
            return duration
        except ValueError:
            console.print("[red]Please enter a valid number of minutes.[/red]")
        except EOFError:
            logger.warning(f"EOFError (Ctrl+D) received for duration. Using default ({default} minutes).")
            console.print(f"[warning]Input cancelled (Ctrl+D). Using default value ({default} minutes).[/warning]")
            return default
        except KeyboardInterrupt:
            logger.warning(f"KeyboardInterrupt (Ctrl+C) received for duration. Using default ({default} minutes).")
            console.print(f"\n[warning]Input interrupted (Ctrl+C). Using default value ({default} minutes).[/warning]")
            return default
        except Exception as e:
            logger.error(f"Failed to get duration input: {e}", exc_info=True)
            console.print(f"[red]An error occurred. Using default value ({default} minutes).[/red]")
            return default


async def _ask_basic_confirmation(
    console: RichConsole,
    choices: List[Tuple[str, str, str]],
    prompt_message_text: str,
    **_kwargs: Any
) -> str:
    """
    Asks the user to choose from a list of choices.
    """
    choices_str = "/".join([choice[0] for choice in choices])
    full_prompt = f"{prompt_message_text} ({choices_str}): "
    
    while True:
        try:
            user_input = await _execute_prompt_with_live_suspend(console, full_prompt)
            if not user_input:
                continue
                
            user_input_lower = user_input.lower()
            
            for key, display, full_word in choices:
                if user_input_lower == key.lower() or user_input_lower == full_word.lower():
                    return key
                    
            console.print(f"[red]Invalid choice. Please enter one of: {choices_str}[/red]")
            
        except (EOFError, KeyboardInterrupt):
            logger.warning("User cancelled confirmation prompt.")
            console.print("\n[warning]Input cancelled.[/warning]")
            return "c"  # Cancel
        except Exception as e:
            logger.error(f"Error in confirmation prompt: {e}", exc_info=True)
            console.print(f"[red]Error: {e}[/red]")
            return "c"  # Cancel


async def request_confirmation(
    prompt_message: str,
    console: RichConsole,
    content_to_display: Optional[RenderableType] = None,
    allow_modify: bool = False,
    current_value_for_modification: Optional[str] = None,
) -> Tuple[ApprovalDecisionStatus, Optional[str]]:
    """
    Requests user confirmation with optional content display and modification.
    """
    # Check if we're in "approve all" mode
    if is_approve_all_active(console):
        console.print("[info]AUTO-APPROVED due to active 'Approve All' session.[/info]")
        return ("session_approved", current_value_for_modification)

    # Display content if provided
    if content_to_display:
        console.print("\n--- Content Preview ---")
        console.print(content_to_display)
        console.print("--- End Preview ---\n")

    # Build choices
    choices = [CHOICE_YES, CHOICE_NO]
    if allow_modify:
        choices.append(CHOICE_MODIFY)
    choices.extend([CHOICE_APPROVE_ALL, CHOICE_CANCEL])

    try:
        user_choice = await _ask_basic_confirmation(
            console=console,
            choices=choices,
            prompt_message_text=prompt_message
        )

        if user_choice == "y":
            return ("approved", current_value_for_modification)
        elif user_choice == "n":
            console.print("[info]Operation denied by user.[/info]")
            return ("denied", None)
        elif user_choice == "m" and allow_modify:
            # Ask for modification
            modify_prompt = f"Enter new value (current: {current_value_for_modification}): "
            try:
                new_value = await _execute_prompt_with_live_suspend(console, modify_prompt)
                if new_value.strip():
                    console.print(f"[info]Value modified to: {new_value}[/info]")
                    return ("modified", new_value.strip())
                else:
                    console.print("[warning]No modification entered. Using original value.[/warning]")
                    return ("approved", current_value_for_modification)
            except (EOFError, KeyboardInterrupt):
                console.print("\n[warning]Modification cancelled.[/warning]")
                return ("cancelled", None)
        elif user_choice == "a":
            # Set approve all
            duration = await _ask_duration(
                console,
                f"Approve All duration in minutes (default {DEFAULT_APPROVE_ALL_DURATION_MINUTES})",
                DEFAULT_APPROVE_ALL_DURATION_MINUTES
            )
            global _approve_all_until
            _approve_all_until = datetime.datetime.now() + datetime.timedelta(minutes=duration)
            console.print(f"[info]'Approve All' activated for {duration} minutes.[/info]")
            return ("session_approved", current_value_for_modification)
        elif user_choice == "c":
            console.print("[info]Operation cancelled by user.[/info]")
            return ("cancelled", None)
        else:
            console.print("[warning]Unexpected choice. Treating as cancelled.[/warning]")
            return ("cancelled", None)

    except Exception as e:
        logger.error(f"Error in request_confirmation: {e}", exc_info=True)
        console.print(f"[red]Error during confirmation: {e}[/red]")
        return ("cancelled", None)