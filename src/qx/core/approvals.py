import datetime
import logging
import fnmatch # Added for pattern matching
import difflib # Added for diff generation
import os # For os.path.exists
from pathlib import Path # For Path operations
from typing import List, Optional, Tuple, Literal

from rich.console import Console as RichConsole
from rich.panel import Panel
from rich.prompt import Prompt
from rich.text import Text
from rich.syntax import Syntax # Added for syntax highlighting

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
# Added "read_file" and "write_file" to OperationType
OperationType = Literal["generic", "shell_command", "read_file", "write_file"]

# Constants for content preview truncation
MAX_PREVIEW_LINES = 30
HEAD_LINES = 12
TAIL_LINES = 12


class ApprovalManager:
    """
    Manages user approval for operations, supporting "approve all", modification,
    and specific rules for shell commands, file reading, and file writing previews.
    """

    def __init__(self, console: Optional[RichConsole] = None, syntax_highlight_theme: str = "vim"):
        self._approve_all_until: Optional[datetime.datetime] = None
        self._console = console or RichConsole()
        self.default_approve_all_duration_minutes = DEFAULT_APPROVE_ALL_DURATION_MINUTES
        self.syntax_highlight_theme = syntax_highlight_theme
        self._code_syntax_theme_for_preview = syntax_highlight_theme # Store for preview use

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
        for pattern in DEFAULT_PROHIBITED_COMMANDS:
            if fnmatch.fnmatch(command, pattern):
                logger.warning(f"Command '{command}' matches prohibited pattern '{pattern}'. Denying.")
                return "PROHIBITED"

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
                return "c" # Default to cancel on error

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

    def _get_file_preview_renderable(
        self, file_path_str: str, new_content: str, operation_type: OperationType
    ) -> Optional[Syntax | Text]:
        """
        Generates a Rich renderable for file content preview (diff or new content).
        """
        file_path = Path(file_path_str)
        file_exists = file_path.exists() and file_path.is_file()
        file_ext = file_path.suffix.lstrip(".") or "text"

        preview_renderable: Optional[Syntax | Text] = None

        if operation_type == "write_file":
            if file_exists:
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        old_content = f.read()

                    if old_content == new_content:
                        return Text("[bold yellow]No changes detected - file content is identical[/bold yellow]")

                    old_lines = old_content.splitlines()
                    new_lines = new_content.splitlines()
                    diff_lines = list(
                        difflib.unified_diff(
                            old_lines, new_lines,
                            fromfile=f"Current: {file_path_str}",
                            tofile=f"New: {file_path_str}",
                            lineterm="", n=3
                        )
                    )
                    if diff_lines:
                        diff_text = "\n".join(diff_lines)
                        preview_renderable = Syntax(
                            diff_text, "diff",
                            theme=self._code_syntax_theme_for_preview,
                            line_numbers=False # Diffs usually don't need line numbers from Syntax
                        )
                    else:
                        return Text("[bold yellow]No changes detected in diff (content might be identical after normalization)[/bold yellow]")
                except Exception as e:
                    logger.error(f"Error generating diff preview for {file_path_str}: {e}", exc_info=True)
                    # Fallback to showing new content if diff fails
                    file_exists = False # Treat as new file for preview logic below
            
            if not file_exists: # New file or diff failed
                lines = new_content.splitlines()
                line_count = len(lines)
                display_content: str
                truncation_message = ""

                if line_count > MAX_PREVIEW_LINES:
                    display_content = "\n".join(lines[:HEAD_LINES])
                    display_content += f"\n\n[... {line_count - HEAD_LINES - TAIL_LINES} more lines ...]\n\n"
                    display_content += "\n".join(lines[-TAIL_LINES:])
                    truncation_message = f"[dim](Showing {HEAD_LINES} lines from start and {TAIL_LINES} lines from end of {line_count} total lines)[/dim]"
                else:
                    display_content = new_content
                
                preview_renderable = Syntax(
                    display_content,
                    lexer_name=file_ext,
                    theme=self._code_syntax_theme_for_preview,
                    line_numbers=True, # Show line numbers for new content preview
                    word_wrap=False # Usually better for code not to wrap
                )
                if truncation_message:
                    # This is a bit tricky, as Syntax is a single renderable.
                    # We might need to print the truncation message separately after the Syntax object.
                    # For now, let's return the Syntax and the main function can print the message.
                    # Or, we can return a Group. For simplicity, let's assume the caller handles it or we print it here.
                    # For now, the truncation message is just prepared.
                    pass


        elif operation_type == "generic" and content_preview is not None: # Generic preview
            preview_limit = 200 # Simple char limit for generic preview
            if len(content_preview) > preview_limit:
                preview_renderable = Text(content_preview[:preview_limit] + "...", style="code")
            else:
                preview_renderable = Text(content_preview, style="code")
        
        return preview_renderable


    def request_approval(
        self,
        operation_description: str,
        item_to_approve: str,
        allow_modify: bool = False,
        content_preview: Optional[str] = None, # For write_file, this is the new full content
        operation_type: OperationType = "generic",
    ) -> Tuple[ApprovalDecision, str, Optional[str]]:
        """
        Requests user approval for a given operation.
        Returns: (ApprovalDecision, item_string, Optional[modification_reason_string])
        """
        modification_reason: Optional[str] = None

        if operation_type == "read_file":
            if self._is_approve_all_active():
                self._console.print(
                    f"[success]AUTO-APPROVED (SESSION):[/] {operation_description}: [info]{item_to_approve}[/]",
                )
                return "SESSION_APPROVED", item_to_approve, None
            else:
                logger.info(f"File read operation auto-approved: {operation_description} for '{item_to_approve}'")
                self._console.print(
                    f"[success]AUTO-APPROVED (READ):[/] {operation_description}: [info]{item_to_approve}[/]",
                )
                return "AUTO_APPROVED", item_to_approve, None

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

        if self._is_approve_all_active(): # General "Approve All"
            self._console.print(
                f"[success]AUTO-APPROVED (SESSION):[/] {operation_description}: [info]{item_to_approve}[/]",
            )
            return "SESSION_APPROVED", item_to_approve, None

        # --- Panel Content Construction ---
        panel_title = Text(f"{operation_description}: ", style="title")
        panel_title.append(item_to_approve, style="info")
        
        panel_elements: List[Text | Syntax] = []

        if operation_type == "write_file" and content_preview is not None:
            preview_renderable = self._get_file_preview_renderable(item_to_approve, content_preview, operation_type)
            if preview_renderable:
                panel_elements.append(Text("\nContent Preview (Diff or New):\n", style="highlight"))
                panel_elements.append(preview_renderable)
                
                # Add truncation message if applicable (for new files)
                file_path_obj = Path(item_to_approve)
                if not (file_path_obj.exists() and file_path_obj.is_file()):
                    lines = content_preview.splitlines()
                    line_count = len(lines)
                    if line_count > MAX_PREVIEW_LINES:
                        trunc_msg = Text(f"\n[dim](Showing {HEAD_LINES} lines from start and {TAIL_LINES} lines from end of {line_count} total lines)[/dim]")
                        panel_elements.append(trunc_msg)
        elif content_preview is not None: # Generic content preview
            panel_elements.append(Text("\nContent Preview:\n", style="highlight"))
            preview_limit = 200
            if len(content_preview) > preview_limit:
                panel_elements.append(Text(content_preview[:preview_limit] + "...", style="code"))
            else:
                panel_elements.append(Text(content_preview, style="code"))

        # Display the panel
        self._console.print(Panel(Text("\n").join(panel_elements) if panel_elements else Text(""), title=panel_title, border_style="prompt.border"))
        # --- End Panel Content Construction ---

        current_choices = list(BASE_CHOICES)
        effective_allow_modify = allow_modify or (operation_type == "shell_command") or (operation_type == "write_file") # Allow modify for write_file
        if effective_allow_modify:
            if not any(c[0] == MODIFY_CHOICE[0] for c in current_choices):
                current_choices.insert(2, MODIFY_CHOICE) # Insert Modify before Approve All

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
                return "SESSION_APPROVED", item_to_approve, None
            else:
                logger.info(
                    "User entered 0 or negative duration for 'Approve All'. Not activating. Current operation denied."
                )
                self._console.print(
                    "[warning]Auto-approval not enabled (duration was 0 or less). Current operation denied.[/]"
                )
                return "USER_DENIED", item_to_approve, None

        elif user_choice_key == "m" and effective_allow_modify:
            prompt_text = "Enter the modified value"
            if operation_type == "write_file":
                prompt_text = "Enter the modified file path"
            
            modified_item = Prompt.ask(
                Text(prompt_text, style="prompt"),
                default=item_to_approve, # Default to current item (path for write, command for shell)
                console=self._console,
            ).strip()

            if not modified_item:
                self._console.print("[warning]Modification cancelled (empty value entered). Original operation cancelled.[/]")
                logger.warning("Modification resulted in empty value. Cancelling operation.")
                return "USER_CANCELLED", item_to_approve, None # item_to_approve is the original one

            # For write_file, if path is modified, content_preview remains the same for the new path.
            # For shell_command, if command is modified, ask for reason.
            if operation_type == "shell_command" and modified_item != item_to_approve:
                modification_reason = Prompt.ask(
                    Text("Reason for modification (optional)", style="prompt"),
                    default="",
                    console=self._console,
                ).strip() or None
            
            # If it was a write_file and path changed, the 'item_to_approve' (path) is now 'modified_item'.
            # The content to write is still `content_preview`.
            # The LLM will be informed of the new path.
            self._console.print(f"[success]Value to be processed:[/] [info]{modified_item}[/]")
            return "USER_MODIFIED", modified_item, modification_reason

        logger.error(f"Unexpected choice key '{user_choice_key}' or scenario in request_approval.")
        self._console.print(f"[error]An unexpected error occurred in approval. Operation cancelled.[/]")
        return "USER_CANCELLED", item_to_approve, None

    def is_globally_approved(self) -> bool:
        """Public method to check if 'Approve All' is active."""
        return self._is_approve_all_active()

if __name__ == "__main__":
    from qx.core.constants import DEFAULT_SYNTAX_HIGHLIGHT_THEME
    console = RichConsole()
    # Pass the default theme for testing
    approval_manager = ApprovalManager(console=console, syntax_highlight_theme=DEFAULT_SYNTAX_HIGHLIGHT_THEME)

    console.rule("[bold bright_magenta]Test 1: Generic Operation (User Approves)[/]")
    decision, item, reason = approval_manager.request_approval(
        "Some generic task", "generic_item_abc", operation_type="generic"
    )
    console.print(f"Decision: {decision}, Item: {item}, Reason: {reason}\n")

    console.rule("[bold bright_magenta]Test 2: Read File Operation (Auto-Approved)[/]")
    decision, item, reason = approval_manager.request_approval(
        "Read file content", "/path/to/example.txt", operation_type="read_file"
    )
    console.print(f"Decision: {decision}, Item: {item}, Reason: {reason}\n")
    
    # --- Test Write File Previews ---
    test_dir = Path("/tmp/qx_approval_tests")
    test_dir.mkdir(exist_ok=True)
    existing_file_path = test_dir / "existing.py"
    new_file_path = test_dir / "new_file.txt"
    
    existing_content_v1 = "def old_function():\n    print('hello')\n    return 1"
    existing_file_path.write_text(existing_content_v1)
    
    new_content_for_existing = "def new_function():\n    print('world') # changed\n    return 2 # also changed"
    new_content_for_new_file_short = "This is a new short file."
    new_content_for_new_file_long = "Line " + "\nLine ".join(str(i) for i in range(1, 50))

    console.rule("[bold bright_magenta]Test Write File - Diff Preview[/]")
    approval_manager.request_approval(
        "Update Python file", str(existing_file_path),
        content_preview=new_content_for_existing, operation_type="write_file", allow_modify=True
    )
    
    console.rule("[bold bright_magenta]Test Write File - New Short File Preview[/]")
    approval_manager.request_approval(
        "Create new text file", str(new_file_path),
        content_preview=new_content_for_new_file_short, operation_type="write_file", allow_modify=True
    )

    console.rule("[bold bright_magenta]Test Write File - New Long File Preview (Truncated)[/]")
    approval_manager.request_approval(
        "Create new long text file", str(new_file_path) + "_long", # different path
        content_preview=new_content_for_new_file_long, operation_type="write_file", allow_modify=True
    )
    
    # Clean up test files
    # existing_file_path.unlink(missing_ok=True)
    # new_file_path.unlink(missing_ok=True)
    # (test_dir / (new_file_path.name + "_long")).unlink(missing_ok=True)
    # if not any(test_dir.iterdir()):
    #     test_dir.rmdir()
    # --- End Test Write File Previews ---


    console.rule("[bold bright_magenta]Test 3: Shell Command - Prohibited (rm -rf /)[/]")
    decision, command, reason = approval_manager.request_approval(
        "Execute shell command", "rm -rf /", operation_type="shell_command"
    )
    console.print(f"Decision: {decision}, Command: {command}, Reason: {reason}\n")

    console.rule("[bold bright_magenta]Test 4: Shell Command - Auto-Approved (ls -la)[/]")
    decision, command, reason = approval_manager.request_approval(
        "Execute shell command", "ls -la", operation_type="shell_command"
    )
    console.print(f"Decision: {decision}, Command: {command}, Reason: {reason}\n")

    console.rule("[bold bright_magenta]Test 5: Shell Command - Requires User Approval (e.g., custom_script.sh)[/]")
    decision, command, reason = approval_manager.request_approval(
        "Execute shell command", "./my_custom_script.sh --verbose", operation_type="shell_command"
    )
    console.print(f"Decision: {decision}, Command: {command}, Reason: {reason}\n")

    console.rule("[bold bright_magenta]Test 6: Activate 'Approve All' via a shell command[/]")
    decision, command, reason = approval_manager.request_approval(
        "Execute shell command", "git pull origin main", operation_type="shell_command"
    )
    console.print(f"Decision: {decision}, Command: {command}, Reason: {reason}\n")

    console.rule("[bold bright_magenta]Test 7: Read File Operation (SESSION_APPROVED if 'Approve All' active)[/]")
    if approval_manager.is_globally_approved():
        console.print("Global approval is ACTIVE.", style="success")
        decision, item, reason = approval_manager.request_approval(
            "Read another file", "/path/to/another.log", operation_type="read_file"
        )
        console.print(f"Decision: {decision}, Item: {item}, Reason: {reason}\n")
    else:
        console.print("Global approval is NOT active. Test 7 for read_file under 'Approve All' skipped.", style="warning")

    console.rule("[bold bright_magenta]Test 8: Generic Write File with Modify (User Modifies)[/]")
    file_content_preview = "Line 1.\nLine 2." # This is for generic, not write_file type
    decision, path, mod_reason = approval_manager.request_approval(
        "Write file (generic type)", "/path/to/doc.md",
        allow_modify=True,
        content_preview=file_content_preview,
        operation_type="generic" # Note: this test is for "generic" type, not "write_file"
    )
    console.print(f"Decision: {decision}, Path: {path}, Reason: {mod_reason}\n")
