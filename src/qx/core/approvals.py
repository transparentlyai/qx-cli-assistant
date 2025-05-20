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
from prompt_toolkit import prompt as prompt_toolkit_prompt
from rich.syntax import Syntax  # Added for syntax highlighting
from rich.text import Text

# Import constants for command checking
from qx.core.constants import DEFAULT_APPROVED_COMMANDS, DEFAULT_PROHIBITED_COMMANDS
from qx.core.paths import USER_HOME_DIR  # For path validation during session approval

# Configure logging for this module
logger = logging.getLogger(__name__)

DEFAULT_APPROVE_ALL_DURATION_MINUTES = 15
BASE_CHOICES = [
    ("y", "Yes", "yes"),
    ("n", "No", "no"),
    ("a", "Approve All", "all"),
    ("c", "Cancel", "cancel"),
]
MODIFY_CHOICE = ("m", "Modify", "modify")

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

MAX_PREVIEW_LINES = 30
HEAD_LINES = 12
TAIL_LINES = 12


class ApprovalManager:
    def __init__(
        self, console: Optional[RichConsole] = None, syntax_highlight_theme: str = "vim"
    ):
        self._approve_all_until: Optional[datetime.datetime] = None
        self._console = console or RichConsole()
        self.default_approve_all_duration_minutes = DEFAULT_APPROVE_ALL_DURATION_MINUTES
        self.syntax_highlight_theme = syntax_highlight_theme

    def _is_approve_all_active(self) -> bool:
        if self._approve_all_until:
            if datetime.datetime.now() < self._approve_all_until:
                return True
            else:
                live_was_active = self._console._live is not None and self._console._live.is_started
                if live_was_active:
                    self._console._live.stop()
                    self._console.clear_live() # Clear the space the live object was using
                
                self._console.print(
                    "[warning]INFO:[/] 'Approve All' period has expired.",
                )
                logger.info("'Approve All' period has expired.")
                self._approve_all_until = None
                
                if live_was_active:
                    self._console._live.start(refresh=True) # Resume the live display if it was active
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

    def _execute_prompt_with_live_suspend(self, prompt_callable, *args, **kwargs):
        # Check if a Live display (e.g., spinner from console.status) is active.
        # The `_live` attribute holds the current Live object if one is active.
        live_display = self._console._live
        live_was_active_and_started = live_display is not None and live_display.is_started
        
        prompt_result = None
        try:
            if live_was_active_and_started:
                live_display.stop() # Stop the live display
                self._console.clear_live() # Crucial: clear the space Rich thinks live is using
            
            prompt_result = prompt_callable(*args, **kwargs)
        finally:
            if live_was_active_and_started:
                # self._console.clear_live() # May also be needed here if prompt leaves artifacts
                live_display.start(refresh=True) # Restart the live display and refresh it
        return prompt_result

    def _ask_confirmation(self, available_choices: List[Tuple[str, str, str]]) -> str:
        choice_map = {key: key for key, _, _ in available_choices}
        for key, _, full_word in available_choices:
            choice_map[full_word.lower()] = key
        simple_choices_str = "/".join(
            display_text for _, display_text, _ in available_choices
        )
        prompt_message = f"{simple_choices_str}: "

        while True:
            try:
                raw_choice = self._execute_prompt_with_live_suspend(prompt_toolkit_prompt, prompt_message)
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
            except EOFError:
                logger.warning("EOFError (Ctrl+D) received during confirmation. Defaulting to Cancel.")
                self._console.print("[warning]Input cancelled (Ctrl+D). Defaulting to Cancel.[/warning]", style="yellow")
                return "c"
            except KeyboardInterrupt:
                logger.warning("KeyboardInterrupt (Ctrl+C) received during confirmation. Defaulting to Cancel.")
                self._console.print("\n[warning]Input interrupted (Ctrl+C). Defaulting to Cancel.[/warning]", style="yellow")
                return "c"
            except Exception as e:
                logger.error(f"Failed to get user confirmation choice: {e}", exc_info=True)
                self._console.print(
                    "[error]An error occurred during input. Defaulting to Cancel.[/]",
                    style="red",
                )
                return "c"

    def _ask_duration(self, prompt_message_text: str, default: int) -> int:
        pt_prompt_message = f"{prompt_message_text}: "
        while True:
            try:
                duration_str = self._execute_prompt_with_live_suspend(
                    prompt_toolkit_prompt, 
                    pt_prompt_message, 
                    default=str(default)
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
            except EOFError:
                logger.warning(f"EOFError (Ctrl+D) received for duration. Using default ({default} minutes).")
                self._console.print(f"[warning]Input cancelled (Ctrl+D). Using default value ({default} minutes).[/warning]", style="yellow")
                return default
            except KeyboardInterrupt:
                logger.warning(f"KeyboardInterrupt (Ctrl+C) received for duration. Using default ({default} minutes).")
                self._console.print(f"\n[warning]Input interrupted (Ctrl+C). Using default value ({default} minutes).[/warning]", style="yellow")
                return default
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
                lexer_name_for_new_file_preview = "text"
            get_lexer_by_name(lexer_name_for_new_file_preview)
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
                            Text("[bold yellow]No changes detected - file content is identical[/bold yellow]")
                        )
                        return renderables
                    old_content_lines = old_content.splitlines(keepends=True)
                    new_content_lines = operation_content_for_preview.splitlines(keepends=True)
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
                        renderables.append(
                            Syntax(diff_text, "diff", theme="vim", line_numbers=False)
                        )
                    else:
                        renderables.append(
                            Text("[bold yellow]No changes detected in diff (content might be identical after normalization)[/bold yellow]")
                        )
                except Exception as e:
                    logger.error(f"Error generating diff preview for {file_path_str}: {e}", exc_info=True)
                    renderables.append(
                        Text(f"[red]Error generating diff: {e}[/red]\nDisplaying new content instead:", style="error")
                    )
                    file_exists = False
            if not file_exists:
                all_lines_for_new_preview = operation_content_for_preview.splitlines()
                line_count = len(all_lines_for_new_preview)
                display_content_str: str
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
                        Text(f"[dim](Showing head and tail of {line_count} total lines)[/dim]", justify="center")
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
                    Text(operation_content_for_preview[:preview_limit] + "... [dim](truncated)[/dim]")
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
                self._console.print(f"[success]SESSION_APPROVED:[/] {operation_description} [info]{item_to_approve}[/]")
                return "SESSION_APPROVED", item_to_approve, None
            else:
                logger.info(f"Auto-approval for read_file: {item_to_approve}")
                self._console.print(f"[success]AUTO-APPROVED:[/] {operation_description} [info]{item_to_approve}[/]")
                return "AUTO_APPROVED", item_to_approve, None

        if operation_type == "shell_command":
            permission_status = self.get_command_permission_status(item_to_approve)
            if permission_status == "PROHIBITED":
                self._console.print(f"[error]COMMAND DENIED (PROHIBITED):[/] {item_to_approve}")
                return "PROHIBITED", item_to_approve, None
            if permission_status == "AUTO_APPROVED":
                if self._is_approve_all_active():
                    logger.info(f"Session approval for shell_command (auto-pattern): {item_to_approve}")
                    self._console.print(f"[success]SESSION_APPROVED (AUTO PATTERN):[/] {operation_description} [info]{item_to_approve}[/]")
                    return "SESSION_APPROVED", item_to_approve, None
                self._console.print(f"[success]COMMAND AUTO-APPROVED (PATTERN):[/] {item_to_approve}")
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
                    self._console.print(f"[success]SESSION_APPROVED (PATH OK):[/] {operation_description} [info]{item_to_approve}[/]")
                    return "SESSION_APPROVED", item_to_approve, None
                else:
                    self._console.print(f"[warning]Session approval for write to '{item_to_approve}' bypassed:[/] Path is outside project/home. Explicit confirmation required.")
            else:
                self._console.print(f"[success]SESSION_APPROVED:[/] {operation_description} [info]{item_to_approve}[/]")
                return "SESSION_APPROVED", item_to_approve, None

        self._console.print(f"QX wants to {operation_description.lower()}: {item_to_approve}")
        content_renderables: List[RenderableType] = []
        if content_preview is not None:
            preview_header_text = (
                "\nContent Preview (Diff or New):\n"
                if operation_type == "write_file"
                else "\nContent Preview:\n"
            )
            content_renderables.append(Text.from_markup(preview_header_text.replace("\\n", "\n")))
            path_for_preview = item_to_approve if operation_type == "write_file" else "generic_item_preview.txt"
            preview_items = self._get_file_preview_renderables(path_for_preview, content_preview, operation_type)
            content_renderables.extend(preview_items)

        if content_renderables:
            for renderable in content_renderables:
                self._console.print(renderable)

        current_choices = list(BASE_CHOICES)
        effective_allow_modify = (allow_modify or (operation_type == "shell_command") or (operation_type == "write_file"))
        if effective_allow_modify:
            if not any(c[0] == MODIFY_CHOICE[0] for c in current_choices):
                current_choices.insert(2, MODIFY_CHOICE)

        user_choice_key = self._ask_confirmation(current_choices)

        if user_choice_key == "y":
            logger.info(f"User approved: {operation_description} for '{item_to_approve}'")
            return "USER_APPROVED", item_to_approve, None
        elif user_choice_key == "n":
            logger.warning(f"User denied: {operation_description} for '{item_to_approve}'")
            self._console.print(f"[warning]Denied by user:[/] {operation_description} [info]{item_to_approve}[/]")
            return "USER_DENIED", item_to_approve, None
        elif user_choice_key == "c":
            logger.warning(f"User cancelled: {operation_description} for '{item_to_approve}'")
            self._console.print(f"[warning]Cancelled by user:[/] {operation_description} [info]{item_to_approve}[/]")
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
                return "USER_APPROVED", item_to_approve, None
            else:
                logger.info("User entered 0 or negative duration for 'Approve All'. Not activating. Current operation denied.")
                self._console.print("[warning]Auto-approval not enabled (duration was 0 or less). Current operation denied.[/]")
                return "USER_DENIED", item_to_approve, None
        elif user_choice_key == "m" and effective_allow_modify:
            prompt_text_str = "Enter the modified value"
            if operation_type == "write_file":
                prompt_text_str = "Enter the modified file path"
            elif operation_type == "shell_command":
                prompt_text_str = "Enter the modified command"
            pt_prompt_message = f"{prompt_text_str}: "
            try:
                modified_item = self._execute_prompt_with_live_suspend(
                    prompt_toolkit_prompt,
                    pt_prompt_message,
                    default=item_to_approve,
                ).strip()
            except EOFError:
                logger.warning("EOFError (Ctrl+D) received during modification. Cancelling operation.")
                self._console.print("[warning]Modification cancelled (Ctrl+D). Original operation cancelled.[/warning]", style="yellow")
                return "USER_CANCELLED", item_to_approve, None
            except KeyboardInterrupt:
                logger.warning("KeyboardInterrupt (Ctrl+C) received during modification. Cancelling operation.")
                self._console.print("\n[warning]Modification interrupted (Ctrl+C). Original operation cancelled.[/warning]", style="yellow")
                return "USER_CANCELLED", item_to_approve, None

            if not modified_item:
                self._console.print("[warning]Modification cancelled (empty value entered). Original operation cancelled.[/]")
                logger.warning("Modification resulted in empty value. Cancelling operation.")
                return "USER_CANCELLED", item_to_approve, None

            if operation_type == "shell_command" and modified_item != item_to_approve:
                try:
                    modification_reason = (self._execute_prompt_with_live_suspend(
                            prompt_toolkit_prompt,
                            "Reason for modification (optional): ",
                            default="",
                        ).strip() or None
                    )
                except EOFError:
                    modification_reason = None
                    logger.info("EOFError (Ctrl+D) received for modification reason. Proceeding without reason.")
                    self._console.print("[info]No reason provided for modification (Ctrl+D).[/info]", style="dim")
                except KeyboardInterrupt:
                    modification_reason = None
                    logger.info("KeyboardInterrupt (Ctrl+C) received for modification reason. Proceeding without reason.")
                    self._console.print("\n[info]No reason provided for modification (Ctrl+C).[/info]", style="dim")
            self._console.print(f"[success]Value to be processed:[/] [info]{modified_item}[/]"
            )
            return "USER_MODIFIED", modified_item, modification_reason

        logger.error(f"Unexpected choice key '{user_choice_key}' or scenario in request_approval for '{operation_description}'.")
        self._console.print(f"[error]An unexpected error occurred in approval. Operation cancelled.[/]")
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

    console.rule("[bold bright_magenta]Test 0: Approve All Expiry Check (with status)[/]")
    approval_manager._approve_all_until = datetime.datetime.now() - datetime.timedelta(seconds=1)
    with console.status("[bold yellow]Testing expiry message with live...[/]"):
        import time
        time.sleep(0.5) # allow status to render
        assert not approval_manager.is_globally_approved() # This should trigger the expiry print
        time.sleep(0.5) # allow status to resume if it does
    approval_manager._approve_all_until = None # Clear for other tests
    console.print("[green]Expiry test with status complete.[/green]")


    console.rule("[bold bright_magenta]Test 1: Generic Operation (User Approves)[/]")
    with console.status("[bold green]Doing some setup before asking...[/]"):
        import time
        time.sleep(1.5) # Simulate work

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
    with console.status("[bold blue]Checking read permissions...[/]"):
        time.sleep(1)
    approval_manager.request_approval(
        operation_description="Read file",
        item_to_approve=str(test_project_root_for_main / "example.txt"),
        operation_type="read_file",
        project_root=test_project_root_for_main,
    )

    project_file_for_write = test_project_root_for_main / "project_write_test.py"
    home_file_for_write = USER_HOME_DIR / "home_write_test_qx_am.py"

    existing_content_v1 = (
        "def old_function():\n    print('hello from old version')\n    return 1"
    )
    project_file_for_write.write_text(existing_content_v1)
    new_content_for_py = "def new_function():\n    print('world from new version') # changed line\n    # added a comment\n    return 2 # also changed"

    console.rule(
        "[bold cyan]Test Write File - Diff Preview (In Project) - Approve All OFF[/]"
    )
    with console.status("[bold yellow]Preparing file diff...[/]"):
        time.sleep(1)
    approval_manager.request_approval(
        operation_description="Write to file",
        item_to_approve=str(project_file_for_write),
        content_preview=new_content_for_py,
        operation_type="write_file",
        allow_modify=True,
        project_root=test_project_root_for_main,
    )

    console.print(
        f"\n[dim]Simulated project root for main tests: {test_project_root_for_main}[/dim]"
    )
    console.print(
        f"[dim]To clean up, you might need to remove: {temp_base_test_dir} and {home_file_for_write}[/dim]"
    )
