import logging
from typing import Callable, List, Literal, Optional, Tuple, Union, Any

from prompt_toolkit import prompt as prompt_toolkit_prompt
from rich.console import Console as RichConsole
from rich.console import RenderableType
from rich.text import Text

logger = logging.getLogger(__name__)

# Define standard choice tuples: (key, display_text, full_word_match)
CHOICE_YES = ("y", "Yes", "yes")
CHOICE_NO = ("n", "No", "no")
CHOICE_MODIFY = ("m", "Modify", "modify")
CHOICE_CANCEL = ("c", "Cancel", "cancel") # Implicitly handled by Ctrl+C/D

ApprovalDecisionStatus = Literal["approved", "denied", "modified", "cancelled"]

def _execute_prompt_with_live_suspend(
    console: RichConsole, prompt_callable: Callable[..., Any], *args: Any, **kwargs: Any
) -> Any:
    """
    Executes a prompt_toolkit prompt, suspending any active Rich Live display.
    """
    live_display = getattr(console, "_live", None) # Safely access _live
    live_was_active_and_started = live_display is not None and getattr(live_display, "is_started", False)
    
    prompt_result = None
    try:
        if live_was_active_and_started:
            live_display.stop()
            if hasattr(console, "clear_live"): # Check if clear_live method exists
                console.clear_live()
            else: # Fallback if clear_live is not available (e.g. older Rich or different setup)
                pass # Or console.print("") to move cursor down if needed
        
        prompt_result = prompt_callable(*args, **kwargs)
    finally:
        if live_was_active_and_started:
            live_display.start(refresh=True)
    return prompt_result

def _ask_basic_confirmation(
    console: RichConsole,
    prompt_query_message: str,
    available_choices: List[Tuple[str, str, str]]
) -> str:
    """
    Internal helper to ask for confirmation using prompt_toolkit.
    Returns the chosen key (e.g., 'y', 'n', 'm').
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
            raw_choice = _execute_prompt_with_live_suspend(
                console,
                prompt_toolkit_prompt,
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
                Text.from_markup(f"[error]Invalid input.[/] Please enter one of {simple_choices_str}{example_guidance}"),
            )
        except EOFError:
            logger.warning("EOFError (Ctrl+D) received during confirmation. Defaulting to Cancel.")
            console.print(Text.from_markup("[warning]Input cancelled (Ctrl+D).[/warning]"),)
            return CHOICE_CANCEL[0] # 'c'
        except KeyboardInterrupt:
            logger.warning("KeyboardInterrupt (Ctrl+C) received during confirmation. Defaulting to Cancel.")
            console.print(Text.from_markup("\n[warning]Input interrupted (Ctrl+C).[/warning]"),)
            return CHOICE_CANCEL[0] # 'c'
        except Exception as e:
            logger.error(f"Failed to get user confirmation choice: {e}", exc_info=True)
            console.print(Text.from_markup("[error]An error occurred during input. Defaulting to Cancel.[/]"),)
            return CHOICE_CANCEL[0] # 'c'

def request_confirmation(
    prompt_message: str,
    console: RichConsole,
    content_to_display: Optional[Union[str, RenderableType]] = None,
    allow_modify: bool = False,
    current_value_for_modification: Optional[str] = None,
) -> Tuple[ApprovalDecisionStatus, Optional[str]]:
    """
    Requests user confirmation for an action.

    Args:
        prompt_message: The main question to ask the user (e.g., "Allow QX to write to /path/to/file?").
        console: The RichConsole instance for UI.
        content_to_display: Optional string or Rich renderable to show before the prompt.
        allow_modify: If True, adds a "Modify" option.
        current_value_for_modification: The current value if modification is allowed, used as default for prompt.

    Returns:
        A tuple: (status: ApprovalDecisionStatus, value: Optional[str])
                 'value' is the item to be processed (original or modified).
                 It's None if denied or cancelled.
    """
    console.print(Text.from_markup(f"[info]ACTION REQUIRED:[/] {prompt_message}"))

    if content_to_display:
        if isinstance(content_to_display, str):
            console.print(Text(content_to_display))
        else:
            console.print(content_to_display)

    choices = [CHOICE_YES, CHOICE_NO]
    if allow_modify:
        choices.append(CHOICE_MODIFY)

    user_choice_key = _ask_basic_confirmation(console, "Confirm?", choices)

    if user_choice_key == CHOICE_YES[0]: # 'y'
        logger.info(f"User approved action: {prompt_message}")
        return "approved", current_value_for_modification if allow_modify else "" # Return current value or empty string if not modifiable
    
    elif user_choice_key == CHOICE_NO[0]: # 'n'
        logger.warning(f"User denied action: {prompt_message}")
        console.print(Text.from_markup(f"[warning]Denied by user:[/] {prompt_message.split('?')[0]}"))
        return "denied", None
        
    elif user_choice_key == CHOICE_MODIFY[0] and allow_modify:
        pt_modify_prompt = "Enter the modified value: "
        try:
            modified_value = _execute_prompt_with_live_suspend(
                console,
                prompt_toolkit_prompt,
                pt_modify_prompt,
                default=current_value_for_modification or "",
            ).strip()

            if not modified_value: # Empty input treated as cancellation of modification
                console.print(Text.from_markup("[warning]Modification cancelled (empty value). Action denied.[/warning]"))
                logger.warning(f"Modification resulted in empty value for: {prompt_message}. Action denied.")
                return "denied", None # Or "cancelled" if preferred for empty modification
            
            if modified_value == current_value_for_modification:
                console.print(Text.from_markup("[info]Value unchanged. Proceeding with original.[/info]"))
                logger.info(f"User chose modify but provided same value for: {prompt_message}")
                return "approved", current_value_for_modification

            logger.info(f"User modified item for action '{prompt_message}'. New value: '{modified_value}'")
            console.print(Text.from_markup(f"[success]Value modified. Proceeding with:[/] [info]{modified_value}[/]"))
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
            console.print(Text.from_markup("[error]An error occurred during modification. Action cancelled.[/]"))
            return "cancelled", None
            
    elif user_choice_key == CHOICE_CANCEL[0]: # 'c' (from _ask_basic_confirmation's error handling)
        logger.warning(f"User cancelled action: {prompt_message}")
        # Message already printed by _ask_basic_confirmation for Ctrl+C/D
        return "cancelled", None

    # Fallback, should not be reached if _ask_basic_confirmation handles all its cases
    logger.error(f"Unexpected choice key '{user_choice_key}' in request_confirmation for '{prompt_message}'.")
    console.print(Text.from_markup("[error]An unexpected error occurred in confirmation. Action cancelled.[/]"))
    return "cancelled", None


if __name__ == "__main__":
    # Basic test for request_confirmation
    logging.basicConfig(level=logging.INFO)
    test_console = RichConsole()

    test_console.rule("[bold green]Testing request_confirmation[/]")

    # Test 1: Simple Yes/No
    test_console.print("\n[bold]Test 1: Simple Yes/No[/]")
    status, val = request_confirmation("Allow simple action?", test_console)
    test_console.print(f"Result: Status='{status}', Value='{val}'")

    # Test 2: With content display
    test_console.print("\n[bold]Test 2: With content display[/]")
    from rich.syntax import Syntax
    code_preview = Syntax("print('Hello World!')", "python", theme="monokai", line_numbers=True)
    status, val = request_confirmation(
        "Allow action with code preview?", 
        test_console, 
        content_to_display=code_preview
    )
    test_console.print(f"Result: Status='{status}', Value='{val}'")

    # Test 3: Allow Modify
    test_console.print("\n[bold]Test 3: Allow Modify[/]")
    original_command = "ls -l"
    status, val = request_confirmation(
        f"Execute command: {original_command}?",
        test_console,
        allow_modify=True,
        current_value_for_modification=original_command
    )
    test_console.print(f"Result: Status='{status}', Value='{val}' (Original was: '{original_command}')")

    # Test 4: Allow Modify, user enters empty string for modification
    test_console.print("\n[bold]Test 4: Allow Modify, user enters empty string[/]")
    original_path = "/tmp/test.txt"
    status, val = request_confirmation(
        f"Write to path: {original_path}?",
        test_console,
        allow_modify=True,
        current_value_for_modification=original_path
    )
    test_console.print(f"Result: Status='{status}', Value='{val}' (Original was: '{original_path}')")
    
    test_console.print("\n[bold green]Finished testing request_confirmation.[/]")
