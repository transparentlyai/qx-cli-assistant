import asyncio
import logging
import datetime
from typing import Callable, List, Literal, Optional, Tuple, Union, Any, Protocol

class ConsoleProtocol(Protocol):
    def print(self, *args, **kwargs): ...

RichConsole = ConsoleProtocol  # Type alias for backward compatibility
RenderableType = str  # Simplified type

logger = logging.getLogger(__name__)

# --- State for "Approve All" ---
_approve_all_active: bool = False
_approve_all_lock = asyncio.Lock()  # Protect global state
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


async def is_approve_all_active(console: RichConsole) -> bool:
    """
    Checks if the 'Approve All' session is currently active.
    Thread-safe async version.
    """
    global _approve_all_active
    async with _approve_all_lock:
        return _approve_all_active




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


def _is_textual_environment(console: RichConsole) -> bool:
    """Check if we're running in a Textual environment."""
    return hasattr(console, '_app') and console._app is not None


async def _request_confirmation_textual(
    prompt_message: str,
    console: RichConsole,
    content_to_display: Optional[RenderableType] = None,
    allow_modify: bool = False,
    current_value_for_modification: Optional[str] = None,
) -> Tuple[ApprovalDecisionStatus, Optional[str]]:
    """Handle confirmation requests in Textual environment."""
    # Check if we're in "approve all" mode first
    if await is_approve_all_active(console):
        console.print("[info]AUTO-APPROVED due to active 'Approve All' session.[/info]")
        return ("session_approved", current_value_for_modification)
    
    # Display content preview first
    if content_to_display:
        console.print("\n--- Content Preview ---")
        console.print(content_to_display)
        console.print("--- End Preview ---\n")
    
    # Use Textual app's confirmation method
    app = console._app
    if hasattr(app, 'request_confirmation'):
        try:
            # Request confirmation through Textual UI
            user_choice = await app.request_confirmation(prompt_message, "ynmac", "n", allow_modify)
            
            if user_choice == "y":
                return ("approved", current_value_for_modification)
            elif user_choice == "n":
                console.print("[info]Operation denied by user.[/info]")
                return ("denied", None)
            elif user_choice == "m" and allow_modify:
                # For Textual, we'd need a separate input modal for modification
                # For now, fallback to simple approval with current value
                console.print("[info]Modification not yet implemented in Textual UI. Using current value.[/info]")
                return ("approved", current_value_for_modification)
            elif user_choice == "a":
                global _approve_all_active
                async with _approve_all_lock:
                    _approve_all_active = True
                console.print("[info]'Approve All' activated for this session.[/info]")
                return ("session_approved", current_value_for_modification)
            elif user_choice == "c":
                console.print("[info]Operation cancelled by user.[/info]")
                return ("cancelled", None)
            else:
                console.print("[info]Operation denied by user.[/info]")
                return ("denied", None)
        except Exception as e:
            logger.error(f"Error in Textual confirmation: {e}", exc_info=True)
            console.print(f"[red]Error during confirmation: {e}[/red]")
            return ("cancelled", None)
    else:
        # Fallback to auto-approval if app doesn't have the method
        console.print(f"[yellow]⚠️  AUTO-APPROVED (Textual UI limitation):[/yellow] {prompt_message}")
        console.print("[dim]Note: Update to latest version for interactive confirmations[/dim]")
        return ("approved", current_value_for_modification)


async def _request_confirmation_terminal(
    prompt_message: str,
    console: RichConsole,
    content_to_display: Optional[RenderableType] = None,
    allow_modify: bool = False,
    current_value_for_modification: Optional[str] = None,
) -> Tuple[ApprovalDecisionStatus, Optional[str]]:
    """Handle confirmation requests in terminal environment."""
    # Check if we're in "approve all" mode
    if await is_approve_all_active(console):
        console.print("[info]AUTO-APPROVED due to active 'Approve All' session.[/info]")
        return ("session_approved", current_value_for_modification)
        
    # Auto-approve in non-interactive environments (e.g., when stdin is not a tty)
    import sys
    import os
    if not sys.stdin.isatty() or os.environ.get("QX_AUTO_APPROVE", "false").lower() == "true":
        console.print(f"[info]AUTO-APPROVED (non-interactive environment):[/info] {prompt_message}")
        return ("approved", current_value_for_modification)

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
            global _approve_all_active
            async with _approve_all_lock:
                _approve_all_active = True
            console.print("[info]'Approve All' activated for this session.[/info]")
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


async def request_confirmation(
    prompt_message: str,
    console: RichConsole,
    content_to_display: Optional[RenderableType] = None,
    allow_modify: bool = False,
    current_value_for_modification: Optional[str] = None,
) -> Tuple[ApprovalDecisionStatus, Optional[str]]:
    """
    Requests user confirmation with optional content display and modification.
    Automatically detects Textual environment and uses appropriate UI.
    """
    if _is_textual_environment(console):
        return await _request_confirmation_textual(
            prompt_message, console, content_to_display, allow_modify, current_value_for_modification
        )
    else:
        return await _request_confirmation_terminal(
            prompt_message, console, content_to_display, allow_modify, current_value_for_modification
        )