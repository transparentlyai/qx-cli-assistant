import datetime
import logging
import fnmatch # Added for pattern matching
import difflib # Added for diff generation
import os # For os.path.exists
from pathlib import Path # For Path operations
from typing import List, Optional, Tuple, Literal, Union # Added Union

from rich.console import Console as RichConsole, Group, RenderableType # Added Group, RenderableType
from rich.panel import Panel
from rich.prompt import Prompt
from rich.text import Text
from rich.syntax import Syntax # Added for syntax highlighting
from pygments.lexers import get_lexer_by_name # To check if lexer is valid
from pygments.util import ClassNotFound # To catch invalid lexer error

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

    def _is_approve_all_active(self) -> bool:
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
        choice_map = {key: key for key, _, _ in available_choices}
        for key, _, full_word in available_choices:
            choice_map[full_word.lower()] = key

        full_prompt_text = Text(prompt_message) # Removed style="prompt"
        full_prompt_text.append(" (")

        choices_for_display_str_list = []
        for i, (key, display, _) in enumerate(available_choices):
            full_prompt_text.append(display)
            full_prompt_text.append(f"[{key.upper()}]", style="bold cyan") # Changed style
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
                    style="red" # Changed style
                )
            except Exception as e:
                logger.error(f"Failed to get user confirmation choice: {e}", exc_info=True)
                self._console.print(
                    "[error]An error occurred during input. Defaulting to Cancel.[/]",
                     style="red" # Changed style
                )
                return "c"

    def _ask_duration(self, prompt_message: str, default: int) -> int:
        while True:
            try:
                duration_str = Prompt.ask(
                    Text(prompt_message), # Removed style="prompt"
                    default=str(default),
                    console=self._console,
                )
                duration = int(duration_str)
                if duration < 0:
                    self._console.print(
                        "[error]Please enter a non-negative number of minutes.[/]",
                        style="red" # Changed style
                    )
                    continue
                return duration
            except ValueError:
                self._console.print(
                    "[error]Please enter a valid number of minutes.[/]",
                    style="red" # Changed style
                )
            except Exception as e:
                logger.error(f"Failed to get duration input: {e}", exc_info=True)
                self._console.print(
                    f"[error]An error occurred. Using default value ({default} minutes).[/]",
                    style="red" # Changed style
                )
                return default

    def _get_file_preview_renderables(
        self, file_path_str: str, 
        operation_content_for_preview: str, # Renamed from new_content
        operation_type: OperationType
    ) -> List[RenderableType]:
        renderables: List[RenderableType] = []
        file_path = Path(file_path_str)
        
        file_ext = file_path.suffix.lstrip(".").lower()
        lexer_name = file_ext
        try:
            if not lexer_name: 
                lexer_name = "text"
            get_lexer_by_name(lexer_name)
            logger.debug(f"Determined lexer: '{lexer_name}' for file '{file_path_str}' with theme '{self.syntax_highlight_theme}'")
        except ClassNotFound:
            logger.warning(f"Lexer for extension '{file_ext}' not found. Defaulting to 'text' for preview of '{file_path_str}'.")
            lexer_name = "text"

        if operation_type == "write_file":
            file_exists = file_path.exists() and file_path.is_file()
            if file_exists:
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        old_content = f.read()
                    if old_content == operation_content_for_preview:
                        renderables.append(Text("[bold yellow]No changes detected - file content is identical[/bold yellow]"))
                        return renderables

                    old_lines = old_content.splitlines()
                    new_lines = operation_content_for_preview.splitlines()
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
                        renderables.append(Syntax(
                            diff_text, "diff", # Lexer is 'diff' for diffs
                            theme=self.syntax_highlight_theme,
                            line_numbers=False, word_wrap=True
                        ))
                    else:
                        renderables.append(Text("[bold yellow]No changes detected in diff (content might be identical after normalization)[/bold yellow]"))
                except Exception as e:
                    logger.error(f"Error generating diff preview for {file_path_str}: {e}", exc_info=True)
                    renderables.append(Text(f"[red]Error generating diff: {e}[/red]\nDisplaying new content instead:", style="error"))
                    file_exists = False 
            
            if not file_exists: 
                lines = operation_content_for_preview.splitlines()
                line_count = len(lines)
                display_content: str
                
                if line_count > MAX_PREVIEW_LINES:
                    display_content = "\n".join(lines[:HEAD_LINES])
                    display_content += f"\n\n[dim i]... {line_count - HEAD_LINES - TAIL_LINES} more lines ...[/dim i]\n\n"
                    display_content += "\n".join(lines[-TAIL_LINES:])
                    renderables.append(Syntax(
                        display_content, lexer_name, # Use determined lexer_name
                        theme=self.syntax_highlight_theme,
                        line_numbers=True, word_wrap=False
                    ))
                    renderables.append(Text(f"[dim](Showing head and tail of {line_count} total lines)[/dim]", justify="center"))
                else:
                    display_content = operation_content_for_preview
                    renderables.append(Syntax(
                        display_content, lexer_name, # Use determined lexer_name
                        theme=self.syntax_highlight_theme,
                        line_numbers=True, word_wrap=False
                    ))

        elif operation_type == "generic" and operation_content_for_preview is not None:
            preview_limit = 200 
            if len(operation_content_for_preview) > preview_limit:
                renderables.append(Text(operation_content_for_preview[:preview_limit] + "...")) # Removed style="code"
            else:
                renderables.append(Text(operation_content_for_preview)) # Removed style="code"
        
        return renderables

    def request_approval(
        self,
        operation_description: str,
        item_to_approve: str,
        allow_modify: bool = False,
        content_preview: Optional[str] = None, 
        operation_type: OperationType = "generic",
    ) -> Tuple[ApprovalDecision, str, Optional[str]]:
        modification_reason: Optional[str] = None

        if operation_type == "read_file":
            if self._is_approve_all_active():
                self._console.print(f"[success]AUTO-APPROVED (SESSION):[/] {operation_description}: [info]{item_to_approve}[/]")
                return "SESSION_APPROVED", item_to_approve, None
            else:
                logger.info(f"File read operation auto-approved: {operation_description} for '{item_to_approve}'")
                self._console.print(f"[success]AUTO-APPROVED (READ):[/] {operation_description}: [info]{item_to_approve}[/]")
                return "AUTO_APPROVED", item_to_approve, None

        if operation_type == "shell_command":
            permission_status = self.get_command_permission_status(item_to_approve)
            if permission_status == "PROHIBITED":
                self._console.print(f"[error]COMMAND DENIED (PROHIBITED):[/] {item_to_approve}")
                return "PROHIBITED", item_to_approve, None
            if permission_status == "AUTO_APPROVED":
                self._console.print(f"[success]COMMAND AUTO-APPROVED:[/] {item_to_approve}")
                return "AUTO_APPROVED", item_to_approve, None

        if self._is_approve_all_active():
            self._console.print(f"[success]AUTO-APPROVED (SESSION):[/] {operation_description}: [info]{item_to_approve}[/]")
            return "SESSION_APPROVED", item_to_approve, None

        panel_title_text = Text(f"{operation_description}: ", style="bold") 
        panel_title_text.append(item_to_approve, style="cyan") # Changed style="info" to "cyan"
        
        panel_content_renderables: List[RenderableType] = []

        if content_preview is not None: 
            preview_header_text = "\nContent Preview (Diff or New):\n" if operation_type == "write_file" else "\nContent Preview:\n"
            panel_content_renderables.append(Text(preview_header_text, style="underline")) # Changed style="highlight"
            
            path_for_preview = item_to_approve if operation_type == "write_file" else "generic_item.txt" 
            
            preview_items = self._get_file_preview_renderables(path_for_preview, content_preview, operation_type)
            panel_content_renderables.extend(preview_items)

        panel_display_content: RenderableType
        if len(panel_content_renderables) > 1:
            panel_display_content = Group(*panel_content_renderables)
        elif len(panel_content_renderables) == 1:
            panel_display_content = panel_content_renderables[0]
        else:
            panel_display_content = Text("") 

        self._console.print(Panel(panel_display_content, title=panel_title_text, border_style="blue"))

        current_choices = list(BASE_CHOICES)
        effective_allow_modify = allow_modify or (operation_type == "shell_command") or (operation_type == "write_file")
        if effective_allow_modify:
            if not any(c[0] == MODIFY_CHOICE[0] for c in current_choices):
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
            logger.info(f"User chose 'Approve All' for: {operation_description} on '{item_to_approve}'")
            duration_minutes = self._ask_duration(
                "Approve all subsequent operations for how many minutes?",
                default=self.default_approve_all_duration_minutes,
            )
            if duration_minutes > 0:
                self._approve_all_until = datetime.datetime.now() + datetime.timedelta(minutes=duration_minutes)
                logger.info(f"'Approve All' activated until {self._approve_all_until}")
                self._console.print(f"\n[success]▶▶▶ Auto-approval enabled for {duration_minutes} minutes.[/]\n")
                return "SESSION_APPROVED", item_to_approve, None
            else:
                logger.info("User entered 0 or negative duration for 'Approve All'. Not activating. Current operation denied.")
                self._console.print("[warning]Auto-approval not enabled (duration was 0 or less). Current operation denied.[/]")
                return "USER_DENIED", item_to_approve, None
        elif user_choice_key == "m" and effective_allow_modify:
            prompt_text = "Enter the modified value"
            if operation_type == "write_file":
                prompt_text = "Enter the modified file path"
            
            modified_item = Prompt.ask(
                Text(prompt_text), # Removed style="prompt"
                default=item_to_approve,
                console=self._console,
            ).strip()

            if not modified_item:
                self._console.print("[warning]Modification cancelled (empty value entered). Original operation cancelled.[/]")
                logger.warning("Modification resulted in empty value. Cancelling operation.")
                return "USER_CANCELLED", item_to_approve, None

            if operation_type == "shell_command" and modified_item != item_to_approve:
                modification_reason = Prompt.ask(
                    Text("Reason for modification (optional)"), # Removed style="prompt"
                    default="", console=self._console,
                ).strip() or None
            
            self._console.print(f"[success]Value to be processed:[/] [info]{modified_item}[/]")
            return "USER_MODIFIED", modified_item, modification_reason

        logger.error(f"Unexpected choice key '{user_choice_key}' or scenario in request_approval.")
        self._console.print(f"[error]An unexpected error occurred in approval. Operation cancelled.[/]")
        return "USER_CANCELLED", item_to_approve, None

    def is_globally_approved(self) -> bool:
        return self._is_approve_all_active()

if __name__ == "__main__":
    from qx.core.constants import DEFAULT_SYNTAX_HIGHLIGHT_THEME
    console = RichConsole()
    approval_manager = ApprovalManager(console=console, syntax_highlight_theme=DEFAULT_SYNTAX_HIGHLIGHT_THEME)

    console.rule("[bold bright_magenta]Test 1: Generic Operation (User Approves)[/]")
    approval_manager.request_approval(
        "Some generic task", "generic_item_abc", operation_type="generic", content_preview="This is a short generic preview."
    )
    
    console.rule("[bold bright_magenta]Test 2: Read File Operation (Auto-Approved)[/]")
    approval_manager.request_approval(
        "Read file content", "/path/to/example.txt", operation_type="read_file"
    )
        
    test_dir = Path("/tmp/qx_approval_tests_v3")
    test_dir.mkdir(exist_ok=True)
    existing_file_py = test_dir / "existing_test.py"
    new_file_txt = test_dir / "new_test_file.txt"
    new_file_unknown_ext = test_dir / "new_file.unknownext"
    
    existing_content_v1 = "def old_function():\n    print('hello from old version')\n    return 1"
    existing_file_py.write_text(existing_content_v1)
    
    new_content_for_py = "def new_function():\n    print('world from new version') # changed line\n    # added a comment\n    return 2 # also changed"
    new_content_short_txt = "This is a new short text file."
    new_content_long_txt = "Line " + "\nLine ".join(str(i) for i in range(1, 50))
    new_content_unknown = "<xml><tag>value</tag></xml>"

    console.rule("[bold cyan]Test Write File - Diff Preview (Python)[/]")
    approval_manager.request_approval(
        "Update Python file", str(existing_file_py),
        content_preview=new_content_for_py, operation_type="write_file", allow_modify=True
    )
    
    console.rule("[bold cyan]Test Write File - New Short File Preview (Text)[/]")
    approval_manager.request_approval(
        "Create new text file", str(new_file_txt),
        content_preview=new_content_short_txt, operation_type="write_file", allow_modify=True
    )

    console.rule("[bold cyan]Test Write File - New Long File Preview (Text, Truncated)[/]")
    approval_manager.request_approval(
        "Create new long text file", str(new_file_txt) + "_long",
        content_preview=new_content_long_txt, operation_type="write_file", allow_modify=True
    )

    console.rule("[bold cyan]Test Write File - New File Unknown Extension (Defaults to Text Highlighting)[/]")
    approval_manager.request_approval(
        "Create new file with unknown extension", str(new_file_unknown_ext),
        content_preview=new_content_unknown, operation_type="write_file", allow_modify=True
    )
    console.print(f"\n[dim]Test files created in {test_dir}. Review or delete manually.[/dim]")