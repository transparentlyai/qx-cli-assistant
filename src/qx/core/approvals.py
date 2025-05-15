import datetime
import logging
from typing import List, Optional, Tuple

from rich.console import Console as RichConsole # Use RichConsole for clarity
from rich.panel import Panel
from rich.prompt import Prompt
from rich.text import Text

# Configure logging for this module
logger = logging.getLogger(__name__)

DEFAULT_APPROVE_ALL_DURATION_MINUTES = 15
# Choices mapping: (key, display_text, full_word_alternative)
BASE_CHOICES = [
    ("y", "Yes", "yes"),
    ("n", "No", "no"),
    ("a", "Approve All", "all"),
    ("c", "Cancel", "cancel"),
]
MODIFY_CHOICE = ("m", "Modify", "modify")


class ApprovalManager:
    """
    Manages user approval for operations, supporting "approve all" and modification.
    """

    def __init__(self, console: Optional[RichConsole] = None): # Type hint with RichConsole
        self._approve_all_until: Optional[datetime.datetime] = None
        # If no console is passed, create a basic one. The main app should pass its themed console.
        self._console = console or RichConsole()
        self.default_approve_all_duration_minutes = DEFAULT_APPROVE_ALL_DURATION_MINUTES

    def _is_approve_all_active(self) -> bool:
        """Checks if 'Approve All' is currently active and valid."""
        if self._approve_all_until:
            if datetime.datetime.now() < self._approve_all_until:
                logger.info(
                    f"Operation automatically approved due to 'Approve All' until {self._approve_all_until}"
                )
                return True
            else:
                self._console.print(
                    "[warning]INFO:[/] 'Approve All' period has expired.", # Use themed warning
                )
                logger.info("'Approve All' period has expired.")
                self._approve_all_until = None  # Reset expired timer
        return False

    def _ask_confirmation(
        self, prompt_message: str, available_choices: List[Tuple[str, str, str]]
    ) -> str:
        """
        Asks the user for confirmation using rich.prompt.Prompt.

        Args:
            prompt_message: The message to display before the choices.
            available_choices: A list of tuples, each (key, display_text, full_word_alternative).

        Returns:
            The user's choice as a lowercase single-letter key.
        """
        choice_map = {key: key for key, _, _ in available_choices}
        for key, _, full_word in available_choices:
            choice_map[full_word.lower()] = key

        # Construct the prompt Text object with proper styling
        full_prompt_text = Text(prompt_message, style="prompt")
        full_prompt_text.append(" (")
        
        choices_for_display_str_list = [] # For the error message
        for i, (key, display, _) in enumerate(available_choices):
            full_prompt_text.append(display)
            full_prompt_text.append(f"[{key.upper()}]", style="prompt.choices.key")
            choices_for_display_str_list.append(f"{display}[{key.upper()}]")
            if i < len(available_choices) - 1:
                full_prompt_text.append("/")
        full_prompt_text.append(")")
        
        choices_display_str_for_error = "/".join(choices_for_display_str_list)


        while True:
            try:
                # Prompt.ask uses its own styling for the input part, but the message uses console's theme
                raw_choice = Prompt.ask(
                    full_prompt_text, # Pass Text object
                    console=self._console,
                )
                choice = raw_choice.strip().lower()

                if choice in choice_map:
                    return choice_map[choice]

                self._console.print(
                    f"[error]Invalid input.[/] Please enter one of: {choices_display_str_for_error}", # Use themed error
                    style="prompt.invalid" # A more specific style if defined in theme
                )

            except Exception as e:
                logger.error(f"Failed to get user confirmation choice: {e}", exc_info=True)
                self._console.print(
                    "[error]An error occurred during input. Defaulting to Cancel.[/]", # Use themed error
                     style="prompt.invalid"
                )
                return "c"  # Default to cancel on error

    def _ask_duration(self, prompt_message: str, default: int) -> int:
        """Asks the user for a duration in minutes."""
        while True:
            try:
                duration_str = Prompt.ask(
                    Text(prompt_message, style="prompt"), # Use prompt style
                    default=str(default),
                    console=self._console,
                )
                duration = int(duration_str)
                if duration < 0:
                    self._console.print(
                        "[error]Please enter a non-negative number of minutes.[/]", # Use themed error
                        style="prompt.invalid"
                    )
                    continue
                return duration
            except ValueError:
                self._console.print(
                    "[error]Please enter a valid number of minutes.[/]", # Use themed error
                    style="prompt.invalid"
                )
            except Exception as e:
                logger.error(f"Failed to get duration input: {e}", exc_info=True)
                self._console.print(
                    f"[error]An error occurred. Using default value ({default} minutes).[/]", # Use themed error
                    style="prompt.invalid"
                )
                return default

    def request_approval(
        self,
        operation_description: str,
        item_to_approve: str,
        allow_modify: bool = False,
        content_preview: Optional[str] = None,
    ) -> Tuple[bool, str]:
        """
        Requests user approval for a given operation.
        """
        if self._is_approve_all_active():
            self._console.print(
                # Using semantic styles that the theme will define
                f"[success]AUTO-APPROVED:[/] {operation_description}: [info]{item_to_approve}[/]",
            )
            return True, item_to_approve

        # Panel content uses semantic styles
        panel_content = Text(f"{operation_description}:\n", style="title") # e.g. "title" or "bold"
        panel_content.append(item_to_approve, style="info") # e.g. "info" or "cyan"

        if content_preview:
            panel_content.append("\n\nContent Preview:\n", style="highlight") # e.g. "highlight" or "bold dim"
            preview_limit = 200
            if len(content_preview) > preview_limit:
                panel_content.append(content_preview[:preview_limit] + "...", style="code") # e.g. "code" or "dim"
            else:
                panel_content.append(content_preview, style="code")

        self._console.print(Panel(panel_content, border_style="prompt.border")) # e.g. "prompt.border" or "blue"

        current_choices = list(BASE_CHOICES)
        if allow_modify:
            current_choices.insert(2, MODIFY_CHOICE)

        user_choice_key = self._ask_confirmation("Proceed?", current_choices)

        if user_choice_key == "y":
            logger.info(f"User approved: {operation_description} for '{item_to_approve}'")
            return True, item_to_approve
        elif user_choice_key == "n":
            logger.warning(f"User denied: {operation_description} for '{item_to_approve}'")
            self._console.print(f"[warning]Denied by user:[/] {operation_description}")
            return False, item_to_approve
        elif user_choice_key == "c":
            logger.warning(f"User cancelled: {operation_description} for '{item_to_approve}'")
            self._console.print(f"[warning]Cancelled by user:[/] {operation_description}")
            return False, item_to_approve
        elif user_choice_key == "a":
            logger.info(
                f"User chose 'Approve All' for: {operation_description} on '{item_to_approve}'"
            )
            duration_minutes = self._ask_duration(
                "Approve all subsequent operations for how many minutes?",
                default=self.default_approve_all_duration_minutes,
            )
            if duration_minutes > 0:
                self._approve_all_until = datetime.datetime.now() + datetime.timedelta(
                    minutes=duration_minutes
                )
                logger.info(f"'Approve All' activated until {self._approve_all_until}")
                self._console.print(
                    f"\n[success]▶▶▶ Auto-approval enabled for {duration_minutes} minutes.[/]\n"
                )
                return True, item_to_approve
            else:
                logger.info(
                    "User entered 0 or negative duration for 'Approve All'. Not activating."
                )
                self._console.print(
                    "[warning]Auto-approval not enabled (duration was 0 or less). Current operation still needs choice.[/]"
                )
                return False, item_to_approve


        elif user_choice_key == "m" and allow_modify:
            logger.info(
                f"User chose 'Modify' for: {operation_description} on '{item_to_approve}'"
            )
            modified_item = Prompt.ask(
                Text("Enter the modified value", style="prompt"), # Use prompt style
                default=item_to_approve,
                console=self._console,
            )
            self._console.print(f"[success]Modified value:[/] [info]{modified_item}[/]")
            return True, modified_item

        logger.error(f"Unexpected choice key '{user_choice_key}' received.")
        return False, item_to_approve

    def is_globally_approved(self) -> bool:
        """Public method to check if 'Approve All' is active."""
        return self._is_approve_all_active()

if __name__ == "__main__":
    # Example Usage
    # For testing, create a themed console if you want to see theme effects here
    from rich.theme import Theme
    test_theme_dark = Theme({
        "info": "bright_cyan", "warning": "bright_yellow", "error": "bold bright_red", "success": "bright_green",
        "prompt": "bold bright_blue", "prompt.invalid": "bold red", "prompt.choices.key": "bold bright_yellow",
        "title": "bold bright_magenta", "highlight": "dim white", "code": "grey70", "prompt.border": "blue"
    })
    # console = RichConsole(theme=test_theme_dark)
    console = RichConsole() # Basic console for standalone test
    
    approval_manager = ApprovalManager(console=console)

    console.rule("[title]Test 1: Simple Read File Approval[/]")
    approved, item = approval_manager.request_approval(
        "Read file", "/path/to/some/file.txt"
    )
    console.print(f"Approved: {approved}, Item: {item}\n")

    console.rule("[title]Test 2: Shell Command Approval (with Modify)[/]")
    approved, command = approval_manager.request_approval(
        "Execute shell command", "ls -la /tmp", allow_modify=True
    )
    console.print(f"Approved: {approved}, Command: {command}\n")

    console.rule("[title]Test 3: Write File Approval (with Content Preview)[/]")
    file_content_preview = "Line 1 of the file.\nLine 2 of the file.\nThis is the third line."
    approved, path = approval_manager.request_approval(
        "Write file", "/path/to/new_document.md", content_preview=file_content_preview
    )
    console.print(f"Approved: {approved}, Path: {path}\n")

    console.rule("[title]Test 4: Activate 'Approve All'[/]")
    approved, item = approval_manager.request_approval(
        "Another operation", "some_other_item"
    )
    console.print(f"Approved: {approved}, Item: {item}\n")

    console.rule("[title]Test 5: Check 'Approve All' status and subsequent approval[/]")
    if approval_manager.is_globally_approved():
        console.print("Global approval is ACTIVE.", style="success")
        approved, item = approval_manager.request_approval(
            "Yet another operation", "final_item_test"
        )
        console.print(f"Approved (should be auto): {approved}, Item: {item}\n")
    else:
        console.print("Global approval is NOT active.", style="warning")