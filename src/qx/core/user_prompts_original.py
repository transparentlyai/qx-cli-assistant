import logging
import datetime
from typing import Callable, List, Literal, Optional, Tuple, Union, Any

from typing import Protocol

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


async def _execute_prompt_with_live_suspend( # Made async
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
            console.print(
                Text.from_markup("[yellow]INFO:[/yellow] 'Approve All' session has expired."),
            )
            logger.info("'Approve All' session has expired.")
            _approve_all_until = None
            
            if live_was_active:
                live_display.start(refresh=True)
    return False

async def _ask_duration(console: RichConsole, prompt_message_text: str, default: int) -> int: # Made async
    """
    Asks the user for a duration in minutes. Adapted from old ApprovalManager.
    """
    pt_prompt_message = f"{prompt_message_text}: "
    while True:
        try:
            duration_str = await _execute_prompt_with_live_suspend( # Await
                console,
                pt_prompt_message, 
                default=str(default)
            )
            duration = int(duration_str)
            if duration < 0:
                console.print(
                    Text.from_markup("[red]Please enter a non-negative number of minutes.[/red]"),
                )
                continue
            return duration
        except ValueError:
            console.print(
                Text.from_markup("[red]Please enter a valid number of minutes.[/red]")
            )
        except EOFError:
            logger.warning(f"EOFError (Ctrl+D) received for duration. Using default ({default} minutes).")
            console.print(Text.from_markup(f"[warning]Input cancelled (Ctrl+D). Using default value ({default} minutes).[/warning]"))
            return default
        except KeyboardInterrupt:
            logger.warning(f"KeyboardInterrupt (Ctrl+C) received for duration. Using default ({default} minutes).")
            console.print(Text.from_markup(f"\n[warning]Input interrupted (Ctrl+C). Using default value ({default} minutes).[/warning]"))
            return default
        except Exception as e:
            logger.error(f"Failed to get duration input: {e}", exc_info=True)
            console.print(
                Text.from_markup(f"[red]An error occurred. Using default value ({default} minutes).[/red]"),
            )
            return default

async def _ask_basic_confirmation( # Made async
    console: RichConsole,
    prompt_query_message: str,
    available_choices: List[Tuple[str, str, str]]
) -> str:
    """
    Internal helper to ask for confirmation using prompt_toolkit.
    Returns the chosen key (e.g., 'y', 'n', 'm', 'a').
    """
    choice_map = {key: key for key, _, _ in available_choices}
    for key, _, full_word in available_choices:
        choice_map[full_word.lower()] = key
    
    simple_choices_str = "/".join(
        display_text for _, display_text, _ in available_choices
    )
    pt_prompt_message = f"{prompt_query_message} ({simple_choices_str}): "

    while True:
        try:
            raw_choice = await _execute_prompt_with_live_suspend( # Await
                console,
                pt_prompt_message
            )
            choice = raw_choice.strip().lower()
            if choice in choice_map:
                return choice_map[choice]
            
            example_guidance = ""
            if available_choices:
                first_choice_key, first_choice_display, first_choice_full = available_choices[0]
                example_guidance = f" (e.g., '{first_choice_key}' for {first_choice_display}, or '{first_choice_full}')"
            
            console.print(
                Text.from_markup(f"[red]Invalid input.[/red] Please enter one of {simple_choices_str}{example_guidance}"),
            )
        except EOFError:
            logger.warning("EOFError (Ctrl+D) received during confirmation. Defaulting to Cancel.")
            console.print(Text.from_markup("[warning]Input cancelled (Ctrl+D).[/warning]"),)
            return CHOICE_CANCEL[0] 
        except KeyboardInterrupt:
            logger.warning("KeyboardInterrupt (Ctrl+C) received during confirmation. Defaulting to Cancel.")
            console.print(Text.from_markup("\n[warning]Input interrupted (Ctrl+C).[/warning]"),)
            return CHOICE_CANCEL[0]
        except Exception as e:
            logger.error(f"Failed to get user confirmation choice: {e}", exc_info=True)
            console.print(Text.from_markup("[red]An error occurred during input. Defaulting to Cancel.[/red]"),)
            return CHOICE_CANCEL[0]

async def request_confirmation( # Made async
    prompt_message: str,
    console: RichConsole,
    content_to_display: Optional[Union[str, RenderableType]] = None,
    allow_modify: bool = False,
    current_value_for_modification: Optional[str] = None,
    can_approve_all: bool = True,
) -> Tuple[ApprovalDecisionStatus, Optional[str]]:
    """
    Requests user confirmation for an action. Handles "Approve All" session.
    """
    global _approve_all_until

    # Only auto-approve if can_approve_all is True AND approve_all is active
    if can_approve_all and is_approve_all_active(console):
        logger.info(f"SESSION_APPROVED (via 'Approve All'): {prompt_message}")
        console.print(Text.from_markup(f"[green]SESSION APPROVED:[/green] {prompt_message.split('?')[0]} [dim](Approve All active)[/dim]"))
        return "session_approved", current_value_for_modification if allow_modify else ""

    console.print(Text.from_markup(f"[blue]ACTION REQUIRED:[/blue] {prompt_message}"))

    if content_to_display:
        if isinstance(content_to_display, str):
            console.print(Text(content_to_display))
        else:
            console.print(content_to_display)

    choices = [CHOICE_YES, CHOICE_NO]
    if allow_modify:
        choices.append(CHOICE_MODIFY)
    if can_approve_all:
        choices.append(CHOICE_APPROVE_ALL)

    user_choice_key = await _ask_basic_confirmation(console, "Confirm?", choices) # Await

    if user_choice_key == CHOICE_YES[0]:
        logger.info(f"User approved action: {prompt_message}")
        return "approved", current_value_for_modification if allow_modify else ""
    
    elif user_choice_key == CHOICE_NO[0]:
        logger.warning(f"User denied action: {prompt_message}")
        console.print(Text.from_markup(f"[yellow]Denied by user:[/yellow] {prompt_message.split('?')[0]}"))
        return "denied", None
        
    elif user_choice_key == CHOICE_MODIFY[0] and allow_modify:
        pt_modify_prompt = "Enter the modified value: "
        try:
            modified_value = await _execute_prompt_with_live_suspend( # Await
                console,
                pt_modify_prompt,
                default=current_value_for_modification or "",
            )
            modified_value = modified_value.strip() # Strip after getting value

            if not modified_value:
                console.print(Text.from_markup("[warning]Modification cancelled (empty value). Action denied.[/warning]"))
                logger.warning(f"Modification resulted in empty value for: {prompt_message}. Action denied.")
                return "denied", None
            
            if modified_value == current_value_for_modification:
                console.print(Text.from_markup("[info]Value unchanged. Proceeding with original.[/info]"))
                logger.info(f"User chose modify but provided same value for: {prompt_message}")
                return "approved", current_value_for_modification

            logger.info(f"User modified item for action '{prompt_message}'. New value: '{modified_value}'")
            console.print(Text.from_markup(f"[green]Value modified. Proceeding with:[/green] [blue]{modified_value}[/blue]"))
            return "modified", modified_value
            
        except EOFError:
            logger.warning(f"EOFError (Ctrl+D) during modification for: {prompt_message}. Action cancelled.")
            console.print(Text.from_markup("[warning]Modification cancelled (Ctrl+D). Action cancelled.[/warning]"))
            return "cancelled", None
        except KeyboardInterrupt:
            logger.warning(f"KeyboardInterrupt (Ctrl+C) during modification for: {prompt_message}. Action cancelled.")
            console.print(Text.from_markup("\n[warning]Modification interrupted (Ctrl+C). Action cancelled.[/warning]"))
            return "cancelled", None
        except Exception as e:
            logger.error(f"Error during modification input for '{prompt_message}': {e}", exc_info=True)
            console.print(Text.from_markup("[red]An error occurred during modification. Action cancelled.[/red]"))
            return "cancelled", None

    elif user_choice_key == CHOICE_APPROVE_ALL[0] and can_approve_all:
        logger.info(f"User chose 'Approve All' for: {prompt_message}")
        duration_minutes = await _ask_duration( # Await
            console,
            "Approve all subsequent operations for how many minutes?",
            default=DEFAULT_APPROVE_ALL_DURATION_MINUTES,
        )
        if duration_minutes > 0:
            _approve_all_until = datetime.datetime.now() + datetime.timedelta(minutes=duration_minutes)
            logger.info(f"'Approve All' activated until {_approve_all_until}")
            console.print(Text.from_markup(f"\n[green]▶▶▶ Auto-approval enabled for {duration_minutes} minutes.[/green]\n"))
            return "approved", current_value_for_modification if allow_modify else ""
        else:
            logger.info("User entered 0 or negative duration for 'Approve All'. Not activating. Current operation denied.")
            console.print(Text.from_markup("[warning]Auto-approval not enabled (duration was 0 or less). Current operation denied.[/warning]"))
            return "denied", None
            
    elif user_choice_key == CHOICE_CANCEL[0]:
        logger.warning(f"User cancelled action: {prompt_message}")
        return "cancelled", None

    logger.error(f"Unexpected choice key '{user_choice_key}' in request_confirmation for '{prompt_message}'.")
    console.print(Text.from_markup("[red]An unexpected error occurred in confirmation. Action cancelled.[/red]"))
    return "cancelled", None


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    test_console = RichConsole()
    test_console.rule("[bold green]Testing request_confirmation with Approve All[/bold green]")

    async def run_tests():
        global _approve_all_until # Moved to top of function
        # Test 1: Approve All
        test_console.print("\n[bold]Test 1: Choose 'Approve All'[/bold]")
        status, val = await request_confirmation("Allow critical action (Test 1)?", test_console, can_approve_all=True)
        test_console.print(f"Test 1 Result: Status='{status}', Value='{val}'")
        if status == "approved" and _approve_all_until:
            test_console.print(f"Approve All is active until: {_approve_all_until}")

        # Test 2: Check if Approve All is active
        test_console.print("\n[bold]Test 2: Action during 'Approve All'[/bold]")
        if _approve_all_until:
            status, val = await request_confirmation("Allow another action (Test 2)?", test_console, can_approve_all=True)
            test_console.print(f"Test 2 Result: Status='{status}', Value='{val}'")
            assert status == "session_approved"
        else:
            test_console.print("Skipping Test 2 as 'Approve All' was not activated in Test 1.")

        # Test 3: Test expiry (manual simulation)
        test_console.print("\n[bold]Test 3: Simulate 'Approve All' expiry[/bold]")
        if _approve_all_until:
            _approve_all_until = datetime.datetime.now() - datetime.timedelta(seconds=1)
            is_active_after_expiry = is_approve_all_active(test_console)
            test_console.print(f"Is 'Approve All' active after simulated expiry? {is_active_after_expiry}")
            assert not is_active_after_expiry
            assert _approve_all_until is None
        else:
            test_console.print("Skipping Test 3 as 'Approve All' was not active.")

        # Test 4: Simple Yes/No after expiry
        test_console.print("\n[bold]Test 4: Simple Yes/No after expiry[/bold]")
        status, val = await request_confirmation("Allow simple action post-expiry (Test 4)?", test_console, can_approve_all=True)
        test_console.print(f"Test 4 Result: Status='{status}', Value='{val}'")

        test_console.print("\n[bold green]Finished testing request_confirmation with Approve All.[/bold green]")

    asyncio.run(run_tests())