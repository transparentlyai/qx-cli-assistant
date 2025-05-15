import datetime
import logging
from typing import List, Optional, Tuple

from rich.console import Console
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

    def __init__(self, console: Optional[Console] = None):
        self._approve_all_until: Optional[datetime.datetime] = None
        self._console = console or Console()
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
                    "[yellow]INFO:[/] 'Approve All' period has expired.", # Direct style
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

        choices_display_parts = [
            f"{display}[{key.upper()}]" for key, display, _ in available_choices
        ]
        choices_str = "/".join(choices_display_parts)
        full_prompt = f"{prompt_message} ({choices_str})"

        while True:
            try:
                raw_choice = Prompt.ask(
                    full_prompt,
                    console=self._console,
                )
                choice = raw_choice.strip().lower()

                if choice in choice_map:
                    return choice_map[choice]

                self._console.print(
                    f"[prompt.invalid]Invalid input. Please enter one of: {choices_str}"
                )

            except Exception as e:
                logger.error(f"Failed to get user confirmation choice: {e}", exc_info=True)
                self._console.print(
                    "[prompt.invalid]An error occurred during input. Defaulting to Cancel."
                )
                return "c"  # Default to cancel on error

    def _ask_duration(self, prompt_message: str, default: int) -> int:
        """Asks the user for a duration in minutes."""
        while True:
            try:
                duration_str = Prompt.ask(
                    prompt_message,
                    default=str(default),
                    console=self._console,
                )
                duration = int(duration_str)
                if duration < 0:
                    self._console.print(
                        "[prompt.invalid]Please enter a non-negative number of minutes."
                    )
                    continue
                return duration
            except ValueError:
                self._console.print(
                    "[prompt.invalid]Please enter a valid number of minutes."
                )
            except Exception as e:
                logger.error(f"Failed to get duration input: {e}", exc_info=True)
                self._console.print(
                    f"[prompt.invalid]An error occurred. Using default value ({default} minutes)."
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

        Args:
            operation_description: A human-readable description of the operation
                                   (e.g., "Execute shell command", "Write file").
            item_to_approve: The specific item needing approval (e.g., the command string, the file path).
            allow_modify: If True, allows the user to modify `item_to_approve`.
            content_preview: Optional string to display as a preview (e.g., file content for write).

        Returns:
            A tuple (approved: bool, final_item: str).
            `approved` is True if the user approved, False otherwise.
            `final_item` is the original `item_to_approve` or its modified version.
        """
        if self._is_approve_all_active():
            self._console.print(
                f"[green]AUTO-APPROVED:[/] {operation_description}: [cyan]{item_to_approve}[/]",
            )
            return True, item_to_approve

        panel_content = Text(f"{operation_description}:\n", style="bold yellow")
        panel_content.append(item_to_approve, style="cyan")

        if content_preview:
            panel_content.append("\n\nContent Preview:\n", style="bold dim")
            # Limit preview length for display
            preview_limit = 200
            if len(content_preview) > preview_limit:
                panel_content.append(content_preview[:preview_limit] + "...", style="dim")
            else:
                panel_content.append(content_preview, style="dim")

        self._console.print(Panel(panel_content, border_style="blue"))

        current_choices = list(BASE_CHOICES)  # Make a mutable copy
        if allow_modify:
            current_choices.insert(2, MODIFY_CHOICE) # Insert Modify before Approve All

        user_choice_key = self._ask_confirmation("Proceed?", current_choices)

        if user_choice_key == "y":
            logger.info(f"User approved: {operation_description} for '{item_to_approve}'")
            return True, item_to_approve
        elif user_choice_key == "n":
            logger.warning(f"User denied: {operation_description} for '{item_to_approve}'")
            self._console.print(f"[yellow]Denied by user:[/] {operation_description}") # Direct style
            return False, item_to_approve
        elif user_choice_key == "c":
            logger.warning(f"User cancelled: {operation_description} for '{item_to_approve}'")
            self._console.print(f"[yellow]Cancelled by user:[/] {operation_description}") # Direct style
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
                    f"\n[bold green]▶▶▶ Auto-approval enabled for {duration_minutes} minutes.[/]\n"
                )
                return True, item_to_approve  # Approve current operation
            else:
                logger.info(
                    "User entered 0 or negative duration for 'Approve All'. Not activating."
                )
                self._console.print(
                    "[yellow]Auto-approval not enabled (duration was 0 or less). Current operation still needs choice.[/]"
                )
                return False, item_to_approve


        elif user_choice_key == "m" and allow_modify:
            logger.info(
                f"User chose 'Modify' for: {operation_description} on '{item_to_approve}'"
            )
            modified_item = Prompt.ask(
                "Enter the modified value",
                default=item_to_approve,
                console=self._console,
            )
            self._console.print(f"[green]Modified value:[/] [cyan]{modified_item}[/]")
            return True, modified_item

        logger.error(f"Unexpected choice key '{user_choice_key}' received.")
        return False, item_to_approve

    def is_globally_approved(self) -> bool:
        """Public method to check if 'Approve All' is active."""
        return self._is_approve_all_active()

if __name__ == "__main__":
    # Example Usage
    console = Console()
    approval_manager = ApprovalManager(console=console)

    # Test 1: Simple approval
    console.rule("[bold blue]Test 1: Simple Read File Approval")
    approved, item = approval_manager.request_approval(
        "Read file", "/path/to/some/file.txt"
    )
    console.print(f"Approved: {approved}, Item: {item}\n")

    # Test 2: Shell command with modify option
    console.rule("[bold blue]Test 2: Shell Command Approval (with Modify)")
    approved, command = approval_manager.request_approval(
        "Execute shell command", "ls -la /tmp", allow_modify=True
    )
    console.print(f"Approved: {approved}, Command: {command}\n")

    # Test 3: Write file with content preview
    console.rule("[bold blue]Test 3: Write File Approval (with Content Preview)")
    file_content_preview = "Line 1 of the file.\nLine 2 of the file.\nThis is the third line."
    approved, path = approval_manager.request_approval(
        "Write file", "/path/to/new_document.md", content_preview=file_content_preview
    )
    console.print(f"Approved: {approved}, Path: {path}\n")

    # Test 4: Activate "Approve All"
    console.rule("[bold blue]Test 4: Activate 'Approve All'")
    approved, item = approval_manager.request_approval(
        "Another operation", "some_other_item"
    )
    console.print(f"Approved: {approved}, Item: {item}\n")

    # Test 5: Check if "Approve All" is active
    console.rule("[bold blue]Test 5: Check 'Approve All' status and subsequent approval")
    if approval_manager.is_globally_approved():
        console.print("Global approval is ACTIVE.", style="bold green")
        approved, item = approval_manager.request_approval(
            "Yet another operation", "final_item_test"
        )
        console.print(f"Approved (should be auto): {approved}, Item: {item}\n")
    else:
        console.print("Global approval is NOT active.", style="bold yellow")