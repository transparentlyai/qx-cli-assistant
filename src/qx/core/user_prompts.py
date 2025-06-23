import asyncio
import logging
import os
from typing import List, Literal, Optional, Tuple, Any

from rich.console import RenderableType
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
CHOICE_APPROVE_ALL = ("a", "All", "all")

ApprovalDecisionStatus = Literal["approved", "denied", "cancelled", "session_approved"]




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
                "_execute_prompt_with_live_suspend called in non-interactive context. Returning 'n'."
            )
            return "n"
    except (EOFError, KeyboardInterrupt):
        logger.warning(
            "Input cancelled via EOF/KeyboardInterrupt in _execute_prompt_with_live_suspend."
        )
        return "n"
    except Exception as e:
        logger.error(f"Error in _execute_prompt_with_live_suspend: {e}")
        return "n"


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
    valid_canonical_keys = []
    for choice_tuple in choices:
        canonical_key = choice_tuple[0].lower()
        valid_canonical_keys.append(canonical_key)
        for variant in choice_tuple:
            choice_mapping[variant.lower()] = canonical_key

    # Suspend global hotkeys during approval prompt
    hotkeys_suspended = _suspend_global_hotkeys()

    try:
        # Use prompt_toolkit for input to avoid terminal conflicts
        from prompt_toolkit import PromptSession
        from prompt_toolkit.key_binding import KeyBindings
        from prompt_toolkit.validation import Validator, ValidationError
        
        # Create key bindings for the approval prompt
        bindings = KeyBindings()
        
        # Add Ctrl+C handler
        @bindings.add('c-c')
        def _(event):
            # Set the buffer to 'n' and accept it
            event.app.current_buffer.text = 'n'
            event.app.current_buffer.validate_and_handle()
        
        # Create a validator for valid choices
        class ChoiceValidator(Validator):
            def validate(self, document):
                text = document.text.strip().lower()
                if text and text not in choice_mapping:
                    raise ValidationError(
                        message=f"Please choose from: {choices_display_str}"
                    )
        
        # Create a new prompt session for this approval
        session = PromptSession(
            key_bindings=bindings,
            validator=ChoiceValidator(),
            validate_while_typing=False,
            enable_history_search=False,
            mouse_support=False
        )
        
        try:
            # Get input using prompt_toolkit
            user_input = await session.prompt_async(
                full_prompt,
                default=""
            )
            
            if user_input:
                user_input_lower = user_input.strip().lower()
                if user_input_lower in choice_mapping:
                    return choice_mapping[user_input_lower]
            
            # Empty input - return 'n' as default
            return "n"
                
        except (KeyboardInterrupt, EOFError):
            # Handle Ctrl+C as cancel/deny
            console.print("\n[dim red]Operation cancelled by user (Ctrl+C)[/dim red]")
            return "n"  # Return "no" as the choice
            
    except Exception as e:
        logger.error(f"Error in prompt_toolkit confirmation: {e}", exc_info=True)
        # Fall back to basic input if prompt_toolkit fails
        try:
            user_input = await asyncio.to_thread(
                input,
                full_prompt
            )
            if user_input:
                user_input_lower = user_input.strip().lower()
                if user_input_lower in choice_mapping:
                    return choice_mapping[user_input_lower]
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim red]Operation cancelled by user (Ctrl+C)[/dim red]")
            return "n"
                
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

    choices_map = [CHOICE_YES, CHOICE_NO, CHOICE_APPROVE_ALL]

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
        else:
            logger.warning(f"Unexpected choice '{user_choice_key}'. Denying.")
            return ("denied", None)
    except Exception as e:
        logger.error(f"Error in request_confirmation_terminal: {e}", exc_info=True)
        console.print(f"[error]Error during confirmation: {e}[/]")
        return ("denied", None)


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
        # Use prompt_toolkit for input to avoid terminal conflicts
        from prompt_toolkit import PromptSession
        from prompt_toolkit.key_binding import KeyBindings
        from prompt_toolkit.filters import Condition
        from prompt_toolkit.validation import Validator, ValidationError
        
        # Create key bindings for the approval prompt
        bindings = KeyBindings()
        
        # Add Ctrl+C handler
        @bindings.add('c-c')
        def _(event):
            # Set the buffer to 'n' and accept it
            event.app.current_buffer.text = 'n'
            event.app.current_buffer.validate_and_handle()
        
        # Create a validator for valid choices
        class ChoiceValidator(Validator):
            def validate(self, document):
                text = document.text.strip().lower()
                if text and text not in processed_valid_choices:
                    raise ValidationError(
                        message=f"Please choose from: {', '.join(valid_choices)}"
                    )
        
        # Create a new prompt session for this approval
        session = PromptSession(
            key_bindings=bindings,
            validator=ChoiceValidator(),
            validate_while_typing=False,
            enable_history_search=False,
            mouse_support=False
        )
        
        try:
            # Get input using prompt_toolkit
            user_input = await session.prompt_async(
                prompt_text_with_options,
                default=processed_default_choice or ""
            )
            
            if user_input:
                return user_input.strip().lower()
            else:
                # Empty input - treat as no selection
                if "n" in processed_valid_choices:
                    return "n"
                return None
                
        except (KeyboardInterrupt, EOFError):
            # Handle Ctrl+C as cancel/deny
            console.print("\n[dim red]Operation cancelled by user (Ctrl+C)[/dim red]")
            if "n" in processed_valid_choices:
                return "n"
            return None
            
    except Exception as e:
        logger.error(f"Error in prompt_toolkit approval: {e}", exc_info=True)
        # Fall back to basic input if prompt_toolkit fails
        try:
            user_input = await asyncio.to_thread(
                input,
                prompt_text_with_options
            )
            if user_input:
                user_input_lower = user_input.strip().lower()
                if user_input_lower in processed_valid_choices:
                    return user_input_lower
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim red]Operation cancelled by user (Ctrl+C)[/dim red]")
            if "n" in processed_valid_choices:
                return "n"
            return None
                
    finally:
        # Always resume global hotkeys
        if hotkeys_suspended:
            _resume_global_hotkeys()
