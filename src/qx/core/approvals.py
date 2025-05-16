import datetime
import logging
import fnmatch # Added for pattern matching
from typing import List, Optional, Tuple, Literal # Added Literal

from rich.console import Console as RichConsole
from rich.panel import Panel
from rich.prompt import Prompt
from rich.text import Text

# Import constants for command checking
from qx.core.constants import DEFAULT_PROHIBITED_COMMANDS, DEFAULT_APPROVED_COMMANDS

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

# Type definitions for clarity
CommandPermissionStatus = Literal["PROHIBITED", "AUTO_APPROVED", "REQUIRES_USER_APPROVAL"]
ApprovalDecision = Literal[
    "PROHIBITED", 
    "AUTO_APPROVED", 
    "SESSION_APPROVED", 
    "USER_APPROVED", 
    "USER_DENIED", 
    "USER_CANCELLED", 
    "USER_MODIFIED"
]


class ApprovalManager:
    """
    Manages user approval for operations, supporting "approve all", modification,
    and specific rules for shell commands.
    """

    def __init__(self, console: Optional[RichConsole] = None):
        self._approve_all_until: Optional[datetime.datetime] = None
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
                    "[warning]INFO:[/] 'Approve All' period has expired.",
                )
                logger.info("'Approve All' period has expired.")
                self._approve_all_until = None
        return False

    def get_command_permission_status(self, command: str) -> CommandPermissionStatus:
        """
        Checks a shell command against prohibited and approved lists.
        """
        # Check prohibited commands first
        for pattern in DEFAULT_PROHIBITED_COMMANDS:
            if fnmatch.fnmatch(command, pattern):
                logger.warning(f"Command '{command}' matches prohibited pattern '{pattern}'. Denying.")
                return "PROHIBITED"

        # Check approved commands next
        for pattern in DEFAULT_APPROVED_COMMANDS:
            if fnmatch.fnmatch(command, pattern):
                logger.info(f"Command '{command}' matches approved pattern '{pattern}'. Auto-approving.")
                return "AUTO_APPROVED"
        
        logger.debug(f"Command '{command}' requires user approval.")
        return "REQUIRES_USER_APPROVAL"

    def _ask_confirmation(
        self, prompt_message: str, available_choices: List[Tuple[str, str, str]]
    ) -> str:
        """
        Asks the user for confirmation using rich.prompt.Prompt.
        """
        choice_map = {key: key for key, _, _ in available_choices}
        for key, _, full_word in available_choices:
            choice_map[full_word.lower()] = key

        full_prompt_text = Text(prompt_message, style="prompt")
        full_prompt_text.append(" (")
        
        choices_for_display_str_list = []
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
                raw_choice = Prompt.ask(
                    full_prompt_text,
                    console=self._console,
                )
                choice = raw_choice.strip().lower()

                if choice in choice_map:
                    return choice_map[choice]

                self._console.print(
                    f"[error]Invalid input.[/] Please enter one of: {choices_display_str_for_error}",
                    style="prompt.invalid"
                )
            except Exception as e:
                logger.error(f"Failed to get user confirmation choice: {e}", exc_info=True)
                self._console.print(
                    "[error]An error occurred during input. Defaulting to Cancel.[/]",
                     style="prompt.invalid"
                )
                return "c"

    def _ask_duration(self, prompt_message: str, default: int) -> int:
        """Asks the user for a duration in minutes."""
        while True:
            try:
                duration_str = Prompt.ask(
                    Text(prompt_message, style="prompt"),
                    default=str(default),
                    console=self._console,
                )
                duration = int(duration_str)
                if duration < 0:
                    self._console.print(
                        "[error]Please enter a non-negative number of minutes.[/]",
                        style="prompt.invalid"
                    )
                    continue
                return duration
            except ValueError:
                self._console.print(
                    "[error]Please enter a valid number of minutes.[/]",
                    style="prompt.invalid"
                )
            except Exception as e:
                logger.error(f"Failed to get duration input: {e}", exc_info=True)
                self._console.print(
                    f"[error]An error occurred. Using default value ({default} minutes).[/]",
                    style="prompt.invalid"
                )
                return default

    def request_approval(
        self,
        operation_description: str,
        item_to_approve: str,
        allow_modify: bool = False, # For generic operations
        content_preview: Optional[str] = None,
        operation_type: Literal["generic", "shell_command"] = "generic",
    ) -> Tuple[ApprovalDecision, str, Optional[str]]:
        """
        Requests user approval for a given operation.
        Returns: (ApprovalDecision, item_string, Optional[modification_reason_string])
        """
        modification_reason: Optional[str] = None

        if operation_type == "shell_command":
            permission_status = self.get_command_permission_status(item_to_approve)
            if permission_status == "PROHIBITED":
                self._console.print(
                    f"[error]COMMAND DENIED (PROHIBITED):[/] {item_to_approve}"
                )
                return "PROHIBITED", item_to_approve, None
            if permission_status == "AUTO_APPROVED":
                self._console.print(
                    f"[success]COMMAND AUTO-APPROVED:[/] {item_to_approve}"
                )
                return "AUTO_APPROVED", item_to_approve, None
            # If REQUIRES_USER_APPROVAL, proceed to general checks / user prompt

        if self._is_approve_all_active():
            self._console.print(
                f"[success]AUTO-APPROVED (SESSION):[/] {operation_description}: [info]{item_to_approve}[/]",
            )
            return "SESSION_APPROVED", item_to_approve, None

        panel_content = Text(f"{operation_description}:\n", style="title")
        panel_content.append(item_to_approve, style="info")

        if content_preview:
            panel_content.append("\n\nContent Preview:\n", style="highlight")
            preview_limit = 200
            if len(content_preview) > preview_limit:
                panel_content.append(content_preview[:preview_limit] + "...", style="code")
            else:
                panel_content.append(content_preview, style="code")

        self._console.print(Panel(panel_content, border_style="prompt.border"))

        current_choices = list(BASE_CHOICES)
        # For shell commands requiring user approval, modify is always an option.
        # For generic, it depends on the allow_modify flag.
        effective_allow_modify = allow_modify or (operation_type == "shell_command")
        if effective_allow_modify:
            # Ensure Modify is not duplicated if already in BASE_CHOICES (it's not, but good practice)
            if not any(c[0] == MODIFY_CHOICE[0] for c in current_choices):
                 # Insert Modify before "Approve All" and "Cancel" for better flow
                current_choices.insert(2, MODIFY_CHOICE)


        user_choice_key = self._ask_confirmation("Proceed?", current_choices)

        if user_choice_key == "y":
            logger.info(f"User approved: {operation_description} for '{item_to_approve}'")
            return "USER_APPROVED", item_to_approve, None
        elif user_choice_key == "n":
            logger.warning(f"User denied: {operation_description} for '{item_to_approve}'")
            self._console.print(f"[warning]Denied by user:[/] {operation_description}")
            return "USER_DENIED", item_to_approve, None
        elif user_choice_key == "c":
            logger.warning(f"User cancelled: {operation_description} for '{item_to_approve}'")
            self._console.print(f"[warning]Cancelled by user:[/] {operation_description}")
            return "USER_CANCELLED", item_to_approve, None
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
                # Current operation is also approved as part of "Approve All"
                return "SESSION_APPROVED", item_to_approve, None
            else:
                logger.info(
                    "User entered 0 or negative duration for 'Approve All'. Not activating. Current operation denied."
                )
                self._console.print(
                    "[warning]Auto-approval not enabled (duration was 0 or less). Current operation denied.[/]"
                )
                return "USER_DENIED", item_to_approve, None # Deny current if "Approve All" is not activated

        elif user_choice_key == "m" and effective_allow_modify:
            logger.info(
                f"User chose 'Modify' for: {operation_description} on '{item_to_approve}'"
            )
            modified_item = Prompt.ask(
                Text("Enter the modified value", style="prompt"),
                default=item_to_approve,
                console=self._console,
            ).strip()

            if not modified_item: # If user enters empty string
                self._console.print("[warning]Modification cancelled (empty value entered). Original operation cancelled.[/]")
                logger.warning("Modification resulted in empty value. Cancelling operation.")
                return "USER_CANCELLED", item_to_approve, None


            if operation_type == "shell_command" and modified_item != item_to_approve :
                modification_reason = Prompt.ask(
                    Text("Reason for modification (optional)", style="prompt"),
                    default="",
                    console=self._console,
                ).strip() or None # Ensure None if empty

            self._console.print(f"[success]Value to be processed:[/] [info]{modified_item}[/]")
            return "USER_MODIFIED", modified_item, modification_reason

        logger.error(f"Unexpected choice key '{user_choice_key}' or scenario in request_approval.")
        # Fallback, should ideally not be reached if logic is correct
        self._console.print(f"[error]An unexpected error occurred in approval. Operation cancelled.[/]")
        return "USER_CANCELLED", item_to_approve, None


    def is_globally_approved(self) -> bool:
        """Public method to check if 'Approve All' is active."""
        return self._is_approve_all_active()

if __name__ == "__main__":
    from rich.theme import Theme
    # test_theme_dark = Theme({ ... }) # Keep theme for testing if desired
    console = RichConsole() 
    
    approval_manager = ApprovalManager(console=console)

    console.rule("[bold bright_magenta]Test 1: Generic Read File Approval (User Approves)[/]")
    decision, item, reason = approval_manager.request_approval(
        "Read file", "/path/to/some/file.txt", operation_type="generic"
    )
    console.print(f"Decision: {decision}, Item: {item}, Reason: {reason}\n")

    console.rule("[bold bright_magenta]Test 2: Shell Command - Prohibited (rm -rf /)[/]")
    decision, command, reason = approval_manager.request_approval(
        "Execute shell command", "rm -rf /", operation_type="shell_command"
    )
    console.print(f"Decision: {decision}, Command: {command}, Reason: {reason}\n")

    console.rule("[bold bright_magenta]Test 3: Shell Command - Auto-Approved (ls -la)[/]")
    # Assuming "ls -la" or "ls *" is in DEFAULT_APPROVED_COMMANDS
    decision, command, reason = approval_manager.request_approval(
        "Execute shell command", "ls -la", operation_type="shell_command"
    )
    console.print(f"Decision: {decision}, Command: {command}, Reason: {reason}\n")

    console.rule("[bold bright_magenta]Test 4: Shell Command - Requires User Approval (e.g., custom_script.sh)[/]")
    decision, command, reason = approval_manager.request_approval(
        "Execute shell command", "./my_custom_script.sh --verbose", operation_type="shell_command"
    )
    console.print(f"Decision: {decision}, Command: {command}, Reason: {reason}\n")
    # Test various inputs: y, n, m (and provide new command + reason), a (and set duration), c

    console.rule("[bold bright_magenta]Test 5: Shell Command - User Modifies[/]")
    # Simulate a scenario where user input for Test 4 was 'm'
    # This test would typically be part of an interactive session.
    # Here, we'll just show how a "USER_MODIFIED" result would look.
    console.print(
        "Imagine user chose 'm' for './my_custom_script.sh --verbose' and entered 'echo hello' with reason 'testing'."
    )
    console.print(f"Example Decision: USER_MODIFIED, Command: echo hello, Reason: testing\n")


    console.rule("[bold bright_magenta]Test 6: Activate 'Approve All' via a shell command[/]")
    # User would choose 'a' for this command
    decision, command, reason = approval_manager.request_approval(
        "Execute shell command", "git pull origin main", operation_type="shell_command"
    )
    console.print(f"Decision: {decision}, Command: {command}, Reason: {reason}\n")


    console.rule("[bold bright_magenta]Test 7: Check 'Approve All' status and subsequent shell command[/]")
    if approval_manager.is_globally_approved():
        console.print("Global approval is ACTIVE.", style="success")
        decision, command, reason = approval_manager.request_approval(
            "Execute shell command", "cat README.md", operation_type="shell_command"
            # This should be SESSION_APPROVED if cat is not in DEFAULT_APPROVED_COMMANDS
            # or AUTO_APPROVED if 'cat *' is in DEFAULT_APPROVED_COMMANDS
        )
        console.print(f"Decision: {decision}, Command: {command}, Reason: {reason}\n")
    else:
        console.print("Global approval is NOT active.", style="warning")

    console.rule("[bold bright_magenta]Test 8: Generic Write File with Modify (User Modifies)[/]")
    file_content_preview = "Line 1.\nLine 2."
    decision, path, mod_reason = approval_manager.request_approval(
        "Write file", "/path/to/doc.md", 
        allow_modify=True, 
        content_preview=file_content_preview,
        operation_type="generic"
    )
    console.print(f"Decision: {decision}, Path: {path}, Reason: {mod_reason}\n")