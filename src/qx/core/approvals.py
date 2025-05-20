import datetime
import difflib  # Added for diff generation
import fnmatch  # Added for pattern matching
import logging
import os  # For os.path.exists and os.path.expanduser
from pathlib import Path  # For Path operations
from typing import List, Literal, Optional, Tuple, Union  # Added Union

from pygments.lexers import get_lexer_by_name  # To check if lexer is valid
from pygments.util import ClassNotFound  # To catch invalid lexer error
from rich.console import Console as RichConsole
from rich.console import RenderableType
from rich.prompt import Prompt
from rich.syntax import Syntax  # Added for syntax highlighting
from rich.text import Text

# Import constants for command checking
from qx.core.constants import DEFAULT_APPROVED_COMMANDS, DEFAULT_PROHIBITED_COMMANDS
from qx.core.paths import USER_HOME_DIR  # For path validation during session approval

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
CommandPermissionStatus = Literal[
    "PROHIBITED", "AUTO_APPROVED", "REQUIRES_USER_APPROVAL"
]
ApprovalDecision = Literal[
    "PROHIBITED",
    "AUTO_APPROVED",
    "SESSION_APPROVED",
    "USER_APPROVED",
    "USER_DENIED",
    "USER_CANCELLED",
    "USER_MODIFIED",
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
    "Approve All" for write operations is conditional on the path being within
    project or user home.
    """

    def __init__(
        self, console: Optional[RichConsole] = None, syntax_highlight_theme: str = "vim"
    ):
        self._approve_all_until: Optional[datetime.datetime] = None
        self._console = console or RichConsole()
        self.default_approve_all_duration_minutes = DEFAULT_APPROVE_ALL_DURATION_MINUTES
        self.syntax_highlight_theme = (
            syntax_highlight_theme  # This remains for non-diff previews
        )

    def _is_approve_all_active(self) -> bool:
        if self._approve_all_until:
            if datetime.datetime.now() < self._approve_all_until:
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
                logger.warning(
                    f"Command '{command}' matches prohibited pattern '{pattern}'. Denying."
                )
                return "PROHIBITED"

        for pattern in DEFAULT_APPROVED_COMMANDS:
            if fnmatch.fnmatch(command, pattern):
                logger.info(
                    f"Command '{command}' matches approved pattern '{pattern}'. Auto-approving."
                )
                return "AUTO_APPROVED"

        logger.debug(f"Command '{command}' requires user approval.")
        return "REQUIRES_USER_APPROVAL"

    def _ask_confirmation(self, available_choices: List[Tuple[str, str, str]]) -> str:
        choice_map = {key: key for key, _, _ in available_choices}
        for key, _, full_word in available_choices:
            choice_map[full_word.lower()] = key

        simple_choices_str = "/".join(
            display_text for _, display_text, _ in available_choices
        )
        # Rich's Prompt.ask will add the colon and space
        prompt_text = f"{simple_choices_str}"

        while True:
            try:
                raw_choice = Prompt.ask(
                    prompt_text,
                    console=self._console,
                )
                choice = raw_choice.strip().lower()

                if choice in choice_map:
                    return choice_map[choice]

                example_guidance = ""
                if available_choices:
                    first_choice_key, first_choice_display, first_choice_full = (
                        available_choices[0]
                    )
                    example_guidance = f" (e.g., '{first_choice_key}' for {first_choice_display}, or the full word '{first_choice_full}')"

                self._console.print(
                    f"[error]Invalid input.[/] Please enter one of {simple_choices_str}{example_guidance}.",
                    style="red",
                )
            except Exception as e:
                logger.error(
                    f"Failed to get user confirmation choice: {e}", exc_info=True
                )
                self._console.print(
                    "[error]An error occurred during input. Defaulting to Cancel.[/]",
                    style="red",
                )
                return "c"

    def _ask_duration(self, prompt_message: str, default: int) -> int:
        while True:
            try:
                duration_str = Prompt.ask(
                    Text(prompt_message),
                    default=str(default),
                    console=self._console,
                )
                duration = int(duration_str)
                if duration < 0:
                    self._console.print(
                        "[error]Please enter a non-negative number of minutes.[/]",
                        style="red",
                    )
                    continue
                return duration
            except ValueError:
                self._console.print(
                    "[error]Please enter a valid number of minutes.[/]", style="red"
                )
            except Exception as e:
                logger.error(f"Failed to get duration input: {e}", exc_info=True)
                self._console.print(
                    f"[error]An error occurred. Using default value ({default} minutes).[/]",
                    style="red",
                )
                return default

    def _get_file_preview_renderables(
        self,
        file_path_str: str,
        operation_content_for_preview: str,
        operation_type: OperationType,
    ) -> List[RenderableType]:
        renderables: List[RenderableType] = []
        file_path = Path(file_path_str)

        file_ext = file_path.suffix.lstrip(".").lower()
        lexer_name_for_new_file_preview = file_ext
        try:
            if not lexer_name_for_new_file_preview:
                lexer_name_for_new_file_preview = "text"  # Default lexer
            get_lexer_by_name(lexer_name_for_new_file_preview)  # Validate lexer
            logger.debug(
                f"Determined lexer: '{lexer_name_for_new_file_preview}' for file '{file_path_str}' with theme '{self.syntax_highlight_theme}'"
            )
        except ClassNotFound:
            logger.warning(
                f"Lexer for extension '{file_ext}' not found. Defaulting to 'text' for preview of '{file_path_str}'."
            )
            lexer_name_for_new_file_preview = "text"

        if operation_type == "write_file":
            file_exists = file_path.exists() and file_path.is_file()
            if file_exists:
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        old_content = f.read()
                    if old_content == operation_content_for_preview:
                        renderables.append(
                            Text(
                                "[bold yellow]No changes detected - file content is identical[/bold yellow]"
                            )
                        )
                        return renderables

                    old_content_lines = old_content.splitlines(keepends=True)
                    new_content_lines = operation_content_for_preview.splitlines(
                        keepends=True
                    )

                    diff_lines = list(
                        difflib.unified_diff(
                            old_content_lines,
                            new_content_lines,
                            fromfile=f"Current: {file_path_str}",
                            tofile=f"New: {file_path_str}",
                            lineterm="\n",
                            n=3,
                        )
                    )
                    if diff_lines:
                        diff_text = "".join(diff_lines)

                        self._console.print(
                            "[bold red]DEBUG: TESTING COLORS -> RED[/] [green]GREEN[/] [blue]BLUE[/]"
                        )
                        debug_repr_diff_text = (
                            f"DEBUG: diff_text for Syntax: {repr(diff_text)}"
                        )
                        self._console.print(debug_repr_diff_text)
                        logger.debug(debug_repr_diff_text)

                        renderables.append(
                            Syntax(
                                diff_text,
                                "diff",
                                theme="vim",  # Explicitly use rrt for diffs
                                line_numbers=False,
                            )
                        )
                    else:
                        renderables.append(
                            Text(
                                "[bold yellow]No changes detected in diff (content might be identical after normalization)[/bold yellow]"
                            )
                        )
                except Exception as e:
                    logger.error(
                        f"Error generating diff preview for {file_path_str}: {e}",
                        exc_info=True,
                    )
                    renderables.append(
                        Text(
                            f"[red]Error generating diff: {e}[/red]\nDisplaying new content instead:",
                            style="error",
                        )
                    )
                    file_exists = False

            if not file_exists:  # New file or diff failed
                all_lines_for_new_preview = operation_content_for_preview.splitlines()
                line_count = len(all_lines_for_new_preview)
                display_content_str: str

                # Determine background_color based on the theme
                bg_color_for_new_preview = "default"
                if self.syntax_highlight_theme.lower() in ["rrt", "dimmed_monokai"]:
                    bg_color_for_new_preview = None

                if line_count > MAX_PREVIEW_LINES:
                    head_str = "\n".join(all_lines_for_new_preview[:HEAD_LINES])
                    tail_str = "\n".join(all_lines_for_new_preview[-TAIL_LINES:])
                    display_content_str = (
                        f"{head_str}\n\n"
                        f"[dim i]... {line_count - HEAD_LINES - TAIL_LINES} more lines ...[/dim i]\n\n"
                        f"{tail_str}"
                    )
                    renderables.append(
                        Syntax(
                            display_content_str,
                            lexer_name_for_new_file_preview,
                            theme=self.syntax_highlight_theme,
                            line_numbers=True,
                            word_wrap=True,
                            background_color=bg_color_for_new_preview,
                        )
                    )
                    renderables.append(
                        Text(
                            f"[dim](Showing head and tail of {line_count} total lines)[/dim]",
                            justify="center",
                        )
                    )
                else:
                    renderables.append(
                        Syntax(
                            operation_content_for_preview,
                            lexer_name_for_new_file_preview,
                            theme=self.syntax_highlight_theme,
                            line_numbers=True,
                            word_wrap=True,
                            background_color=bg_color_for_new_preview,
                        )
                    )

        elif operation_type == "generic" and operation_content_for_preview is not None:
            preview_limit = 200
            if len(operation_content_for_preview) > preview_limit:
                renderables.append(
                    Text(
                        operation_content_for_preview[:preview_limit]
                        + "... [dim](truncated)[/dim]"
                    )
                )
            else:
                renderables.append(Text(operation_content_for_preview))

        return renderables

    def request_approval(
        self,
        operation_description: str,
        item_to_approve: str,
        allow_modify: bool = False,
        content_preview: Optional[str] = None,
        operation_type: OperationType = "generic",
        project_root: Optional[Path] = None,
    ) -> Tuple[ApprovalDecision, str, Optional[str]]:
        from qx.tools.file_operations_base import is_path_allowed

        modification_reason: Optional[str] = None

        if operation_type == "read_file":
            if self._is_approve_all_active():
                logger.info(f"Session approval for read_file: {item_to_approve}")
                self._console.print(
                    f"[success]SESSION_APPROVED:[/] {operation_description} [info]{item_to_approve}[/]"
                )
                return "SESSION_APPROVED", item_to_approve, None
            else:
                logger.info(f"Auto-approval for read_file: {item_to_approve}")
                self._console.print(
                    f"[success]AUTO-APPROVED:[/] {operation_description} [info]{item_to_approve}[/]"
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
                if self._is_approve_all_active():
                    logger.info(
                        f"Session approval for shell_command (auto-pattern): {item_to_approve}"
                    )
                    self._console.print(
                        f"[success]SESSION_APPROVED (AUTO PATTERN):[/] {operation_description} [info]{item_to_approve}[/]"
                    )
                    return "SESSION_APPROVED", item_to_approve, None
                self._console.print(
                    f"[success]COMMAND AUTO-APPROVED (PATTERN):[/] {item_to_approve}"
                )
                return "AUTO_APPROVED", item_to_approve, None

        if self._is_approve_all_active():
            logger.info(f"Session approval for {operation_type}: {item_to_approve}")
            if operation_type == "write_file":
                expanded_path_str = os.path.expanduser(item_to_approve)
                absolute_path = Path(expanded_path_str)
                if not absolute_path.is_absolute():
                    absolute_path = Path.cwd().joinpath(expanded_path_str).resolve()
                else:
                    absolute_path = absolute_path.resolve()

                if is_path_allowed(absolute_path, project_root, USER_HOME_DIR):
                    self._console.print(
                        f"[success]SESSION_APPROVED (PATH OK):[/] {operation_description} [info]{item_to_approve}[/]"
                    )
                    return "SESSION_APPROVED", item_to_approve, None
                else:
                    self._console.print(
                        f"[warning]Session approval for write to '{item_to_approve}' bypassed:[/] Path is outside project/home. Explicit confirmation required."
                    )
            else:
                self._console.print(
                    f"[success]SESSION_APPROVED:[/] {operation_description} [info]{item_to_approve}[/]"
                )
                return "SESSION_APPROVED", item_to_approve, None

        self._console.print(
            f"QX wants to {operation_description.lower()}: {item_to_approve}"
        )

        content_renderables: List[RenderableType] = []
        if content_preview is not None:
            preview_header_text = (
                "\nContent Preview (Diff or New):\n"
                if operation_type == "write_file"
                else "\nContent Preview:\n"
            )
            content_renderables.append(
                Text.from_markup(preview_header_text.replace("\\n", "\n"))
            )

            path_for_preview = (
                item_to_approve
                if operation_type == "write_file"
                else "generic_item_preview.txt"
            )
            preview_items = self._get_file_preview_renderables(
                path_for_preview, content_preview, operation_type
            )
            content_renderables.extend(preview_items)

        if content_renderables:
            for renderable in content_renderables:
                self._console.print(renderable)

        current_choices = list(BASE_CHOICES)
        effective_allow_modify = (
            allow_modify
            or (operation_type == "shell_command")
            or (operation_type == "write_file")
        )
        if effective_allow_modify:
            if not any(c[0] == MODIFY_CHOICE[0] for c in current_choices):
                current_choices.insert(2, MODIFY_CHOICE)

        user_choice_key = self._ask_confirmation(current_choices)

        if user_choice_key == "y":
            logger.info(
                f"User approved: {operation_description} for '{item_to_approve}'"
            )
            return "USER_APPROVED", item_to_approve, None
        elif user_choice_key == "n":
            logger.warning(
                f"User denied: {operation_description} for '{item_to_approve}'"
            )
            self._console.print(
                f"[warning]Denied by user:[/] {operation_description} [info]{item_to_approve}[/]"
            )
            return "USER_DENIED", item_to_approve, None
        elif user_choice_key == "c":
            logger.warning(
                f"User cancelled: {operation_description} for '{item_to_approve}'"
            )
            self._console.print(
                f"[warning]Cancelled by user:[/] {operation_description} [info]{item_to_approve}[/]"
            )
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
                return "USER_APPROVED", item_to_approve, None
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
            elif operation_type == "shell_command":
                prompt_text = "Enter the modified command"

            modified_item = Prompt.ask(
                Text(prompt_text),
                default=item_to_approve,
                console=self._console,
            ).strip()

            if not modified_item:
                self._console.print(
                    "[warning]Modification cancelled (empty value entered). Original operation cancelled.[/]"
                )
                logger.warning(
                    "Modification resulted in empty value. Cancelling operation."
                )
                return "USER_CANCELLED", item_to_approve, None

            if operation_type == "shell_command" and modified_item != item_to_approve:
                modification_reason = (
                    Prompt.ask(
                        Text("Reason for modification (optional)"),
                        default="",
                        console=self._console,
                    ).strip()
                    or None
                )

            self._console.print(
                f"[success]Value to be processed:[/] [info]{modified_item}[/]"
            )
            return "USER_MODIFIED", modified_item, modification_reason

        logger.error(
            f"Unexpected choice key '{user_choice_key}' or scenario in request_approval for '{operation_description}'."
        )
        self._console.print(
            f"[error]An unexpected error occurred in approval. Operation cancelled.[/]"
        )
        return "USER_CANCELLED", item_to_approve, None

    def is_globally_approved(self) -> bool:
        return self._is_approve_all_active()


if __name__ == "__main__":
    from qx.core.constants import DEFAULT_SYNTAX_HIGHLIGHT_THEME

    console = RichConsole()
    temp_base_test_dir = Path("temp_approval_manager_tests_dir")
    temp_base_test_dir.mkdir(exist_ok=True)
    test_project_root_for_main = temp_base_test_dir / "dummy_project_for_am_main"
    test_project_root_for_main.mkdir(parents=True, exist_ok=True)
    (test_project_root_for_main / ".Q").mkdir(exist_ok=True)

    approval_manager = ApprovalManager(
        console=console, syntax_highlight_theme=DEFAULT_SYNTAX_HIGHLIGHT_THEME
    )

    console.rule("[bold bright_magenta]Test 1: Generic Operation (User Approves)[/]")
    approval_manager.request_approval(
        operation_description="Perform generic task",
        item_to_approve="generic_item_abc",
        operation_type="generic",
        content_preview="This is a short generic preview.",
        project_root=test_project_root_for_main,
    )

    console.rule(
        "[bold bright_magenta]Test 2: Read File Operation (Auto-Approved by type)[/]"
    )
    approval_manager.request_approval(
        operation_description="Read file",
        item_to_approve=str(test_project_root_for_main / "example.txt"),
        operation_type="read_file",
        project_root=test_project_root_for_main,
    )

    project_file_for_write = test_project_root_for_main / "project_write_test.py"
    home_file_for_write = USER_HOME_DIR / "home_write_test_qx_am.py"
    outside_parent_dir = temp_base_test_dir / "outside_files_dir"
    outside_parent_dir.mkdir(exist_ok=True)
    outside_all_file_for_write = outside_parent_dir / "outside_project_home_test.txt"

    existing_content_v1 = (
        "def old_function():\n    print('hello from old version')\n    return 1"
    )
    project_file_for_write.write_text(existing_content_v1)
    new_content_for_py = "def new_function():\n    print('world from new version') # changed line\n    # added a comment\n    return 2 # also changed"

    console.rule(
        "[bold cyan]Test Write File - Diff Preview (In Project) - Approve All OFF[/]"
    )
    approval_manager.request_approval(
        operation_description="Write to file",
        item_to_approve=str(project_file_for_write),
        content_preview=new_content_for_py,
        operation_type="write_file",
        allow_modify=True,
        project_root=test_project_root_for_main,
    )

    console.rule(
        "[bold cyan]Test Write File - New File Preview (In Project) - Approve All OFF[/]"
    )
    new_project_file = test_project_root_for_main / "newly_created_file.txt"
    if new_project_file.exists():
        new_project_file.unlink()
    approval_manager.request_approval(
        operation_description="Write to file",
        item_to_approve=str(new_project_file),
        content_preview="Line 1\nLine 2\nLine 3 - this is a new file.",
        operation_type="write_file",
        allow_modify=True,
        project_root=test_project_root_for_main,
    )

    console.rule(
        "[bold cyan]Test Write File - Approve All ON - Path OK (In Project)[/]"
    )
    approval_manager._approve_all_until = datetime.datetime.now() + datetime.timedelta(
        minutes=5
    )
    approval_manager.request_approval(
        operation_description="Write to file",
        item_to_approve=str(project_file_for_write),
        content_preview=new_content_for_py.replace(
            "new version", "session approved version"
        ),
        operation_type="write_file",
        allow_modify=True,
        project_root=test_project_root_for_main,
    )
    approval_manager._approve_all_until = None

    console.rule(
        "[bold cyan]Test Write File - Approve All ON - Path OK (In User Home)[/]"
    )
    if home_file_for_write.exists():
        home_file_for_write.unlink(missing_ok=True)
    approval_manager._approve_all_until = datetime.datetime.now() + datetime.timedelta(
        minutes=5
    )
    approval_manager.request_approval(
        operation_description="Write to file",
        item_to_approve=str(home_file_for_write),
        content_preview=new_content_for_py.replace(
            "new_function", "home_session_function"
        ),
        operation_type="write_file",
        allow_modify=True,
        project_root=test_project_root_for_main,
    )
    approval_manager._approve_all_until = None

    console.rule(
        "[bold cyan]Test Write File - Approve All ON - Path NOT OK (Outside Project/Home)[/]"
    )
    if outside_all_file_for_write.exists():
        outside_all_file_for_write.unlink(missing_ok=True)
    approval_manager._approve_all_until = datetime.datetime.now() + datetime.timedelta(
        minutes=5
    )
    approval_manager.request_approval(
        operation_description="Write to file",
        item_to_approve=str(outside_all_file_for_write),
        content_preview="Content for a file written outside allowed session approval zones.",
        operation_type="write_file",
        allow_modify=True,
        project_root=test_project_root_for_main,
    )
    approval_manager._approve_all_until = None

    console.rule("[bold magenta]Test Shell Command - Requires User Approval[/]")
    approval_manager.request_approval(
        operation_description="Execute shell command",
        item_to_approve="echo 'Hello from approvals test'",
        operation_type="shell_command",
        allow_modify=True,
        project_root=test_project_root_for_main,
    )

    console.rule(
        "[bold magenta]Test Shell Command - Auto-Approved by Pattern (e.g. 'git status')[/]"
    )
    approval_manager.request_approval(
        operation_description="Execute shell command",
        item_to_approve="git status",
        operation_type="shell_command",
        project_root=test_project_root_for_main,
    )

    console.rule(
        "[bold magenta]Test Shell Command - Prohibited (e.g. 'sudo rm -rf /')[/]"
    )
    approval_manager.request_approval(
        operation_description="Execute shell command",
        item_to_approve="sudo rm -rf /",
        operation_type="shell_command",
        project_root=test_project_root_for_main,
    )

    console.print(
        f"\n[dim]Simulated project root for main tests: {test_project_root_for_main}[/dim]"
    )
    console.print(
        f"[dim]Other test files might be in {temp_base_test_dir}, {USER_HOME_DIR}[/dim]"
    )
    console.print(
        f"[dim]Files created/modified: {project_file_for_write}, {new_project_file}, {home_file_for_write}, {outside_all_file_for_write}[/dim]"
    )
    console.print(
        f"[dim]To clean up, you might need to remove: {temp_base_test_dir} and {home_file_for_write}[/dim]"
    )

    # import shutil
    # shutil.rmtree(temp_base_test_dir, ignore_errors=True)
    # if home_file_for_write.exists(): home_file_for_write.unlink(missing_ok=True)
