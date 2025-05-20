# pyright: reportPossiblyUnboundVariable=false
import logging
import os
from pathlib import Path
from typing import Optional, Type

from pydantic import BaseModel, Field
from rich.console import Console as RichConsole

from qx.core.approvals import ApprovalManager
from qx.core.paths import USER_HOME_DIR
from qx.core.paths import (
    _find_project_root,
)
from qx.tools.file_operations_base import is_path_allowed

# Configure logging for this module
logger = logging.getLogger(__name__)


def write_file_impl(path_str: str, content: str) -> Optional[str]:
    """
    Writes content to a file after path validation.
    This is the core implementation, intended to be called after approval.

    Args:
        path_str: The relative or absolute path to the file. Tilde expansion is performed.
        content: The content to write to the file.

    Returns:
        None if successful, or an error message string if an error occurs.
    """
    try:
        expanded_path_str = os.path.expanduser(path_str)

        current_working_dir = Path.cwd()
        project_root = _find_project_root(str(current_working_dir))

        absolute_path = Path(expanded_path_str)
        if not absolute_path.is_absolute():
            absolute_path = current_working_dir.joinpath(expanded_path_str).resolve()
        else:
            absolute_path = absolute_path.resolve()

        if not is_path_allowed(absolute_path, project_root, USER_HOME_DIR):
            logger.error(
                f"Write access denied by policy for path: {absolute_path}. "
                f"Project root: {project_root}, User home: {USER_HOME_DIR}"
            )
            return f"Error: Access denied by policy for path: {absolute_path}"

        absolute_path.parent.mkdir(parents=True, exist_ok=True)

        absolute_path.write_text(content, encoding="utf-8")
        logger.info(f"Successfully wrote to file: {absolute_path}")
        return None

    except PermissionError:
        logger.error(f"Permission denied writing to file: {expanded_path_str}")
        return f"Error: Permission denied writing to file: {expanded_path_str}"
    except IsADirectoryError:
        logger.error(f"Path is a directory, cannot write: {expanded_path_str}")
        return f"Error: Path is a directory, cannot write: {expanded_path_str}"
    except Exception as e:
        logger.error(f"Error writing to file '{expanded_path_str}': {e}", exc_info=True)
        return f"Error writing to file '{expanded_path_str}': {e}"


class WriteFileInput(BaseModel):
    """Input model for the WriteFileTool."""

    path: str = Field(
        ...,
        description="The path to the file to be written. Can be relative, absolute, or start with '~'. Parent directories will be created if they don't exist.",
    )
    content: str = Field(..., description="The content to write to the file.")


class WriteFileOutput(BaseModel):
    """Output model for the WriteFileTool."""

    path: str = Field(
        description="The (expanded) path of the file attempted to be written."
    )
    success: bool = Field(
        description="True if the write operation was successful, False otherwise."
    )
    message: Optional[str] = Field(
        None, description="A message indicating the result or error."
    )


class WriteFileTool:
    """
    A tool to write content to a specified file.
    This operation ALWAYS requires user confirmation unless 'Approve All' is active AND
    the path is within the project or user's home directory.
    Path validation ensures writes are restricted to the project directory or user's home directory.
    Tilde (~) in the path is expanded to the user's home directory.
    Parent directories are created if they do not exist.
    """

    name: str = "write_file"
    description: str = (
        "Writes content to a specified file. Provide a relative, absolute, or tilde-based path (e.g., ~/file.txt). "
        "User confirmation is ALWAYS required, unless 'Approve All' is active AND the path is safe (project/home). "
        "Access is restricted by policy. Parent directories will be created."
    )
    input_model: Type[BaseModel] = WriteFileInput
    output_model: Type[BaseModel] = WriteFileOutput

    def __init__(
        self, approval_manager: ApprovalManager, console: Optional[RichConsole] = None
    ):
        self.approval_manager = approval_manager
        self._console = (
            console or RichConsole()
        )

    def run(self, args: WriteFileInput) -> WriteFileOutput:
        """
        Handles approval and execution of writing a file.
        Performs tilde expansion and passes project_root for conditional session approval.
        """
        original_path_arg = args.path
        expanded_path_arg = os.path.expanduser(original_path_arg)
        current_project_root = _find_project_root(str(Path.cwd()))
        
        op_desc_for_prompt = "Write to file"

        decision, item_after_approval, modification_reason = (
            self.approval_manager.request_approval(
                operation_description=op_desc_for_prompt, # Standardized description
                item_to_approve=expanded_path_arg,
                allow_modify=True,
                content_preview=args.content,
                operation_type="write_file",
                project_root=current_project_root,
            )
        )

        path_to_write = item_after_approval

        if decision in ["USER_APPROVED", "SESSION_APPROVED", "USER_MODIFIED"]:
            if decision == "USER_MODIFIED":
                reason_log = (
                    f" (Reason: {modification_reason})" if modification_reason else ""
                )
                logger.info(
                    f"Write operation for '{path_to_write}' (original: '{original_path_arg}') approved after modification{reason_log}. Proceeding to write."
                )
            else:
                logger.info(
                    f"Write operation for '{path_to_write}' (original: '{original_path_arg}') approved (Decision: {decision}). Proceeding to write."
                )

            error_message_from_impl = write_file_impl(path_to_write, args.content)

            if error_message_from_impl:
                logger.warning(
                    f"Failed to write file '{path_to_write}': {error_message_from_impl}"
                )
                return WriteFileOutput(
                    path=path_to_write, success=False, message=error_message_from_impl
                )
            else:
                return WriteFileOutput(
                    path=path_to_write,
                    success=True,
                    message=f"Successfully wrote to {path_to_write}",
                )
        else:
            error_msg = f"{op_desc_for_prompt} for '{path_to_write}' (original: '{original_path_arg}') was {decision.lower().replace('_', ' ')}."
            logger.warning(error_msg)
            return WriteFileOutput(path=path_to_write, success=False, message=error_msg)


if __name__ == "__main__":
    import shutil
    from rich.console import Console as RichConsole
    from qx.core.paths import _ensure_project_q_dir_exists

    class DummyApprovalManager:
        def __init__(self, console, default_decision="USER_APPROVED"):
            self.console = console
            self._approve_all_active = False
            self.default_decision = default_decision
            self.last_received_project_root = None
            self.last_operation_description = None # To check the description passed

        def request_approval(
            self,
            operation_description,
            item_to_approve,
            operation_type,
            allow_modify=False,
            content_preview=None,
            project_root: Optional[Path] = None,
        ):
            self.last_received_project_root = project_root
            self.last_operation_description = operation_description # Store it
            self.console.print(
                f"DummyApprovalManager: Requesting approval for '{operation_description}' (type: {operation_type}) - Item: '{item_to_approve}'"
            )
            self.console.print(
                f"DummyApprovalManager: Received project_root: {project_root}"
            )

            if self._approve_all_active:
                if operation_type == "write_file":
                    expanded_path_str = os.path.expanduser(item_to_approve)
                    absolute_path = Path(expanded_path_str)
                    if not absolute_path.is_absolute():
                        absolute_path = Path.cwd().joinpath(expanded_path_str).resolve()
                    else:
                        absolute_path = absolute_path.resolve()
                    if is_path_allowed(absolute_path, project_root, USER_HOME_DIR):
                        self.console.print(
                            "DummyApprovalManager: Simulating SESSION_APPROVED (path OK for write)"
                        )
                        return "SESSION_APPROVED", item_to_approve, None
                    else:
                        self.console.print(
                            "DummyApprovalManager: Path NOT OK for write, falling back from session to configured default."
                        )
                else:
                    self.console.print(
                        f"DummyApprovalManager: Simulating SESSION_APPROVED for {operation_type}"
                    )
                    return "SESSION_APPROVED", item_to_approve, None
            
            self.console.print(
                f"DummyApprovalManager: Simulating '{self.default_decision}'"
            )
            return self.default_decision, item_to_approve, None

        def is_globally_approved(self):
            return self._approve_all_active

    test_console = RichConsole()
    base_test_dir_name = "tmp_qx_write_tool_tests_v2" # New version for new tests
    Path(base_test_dir_name).mkdir(exist_ok=True)
    base_test_dir = Path(base_test_dir_name).resolve()
    test_project_sim_dir = base_test_dir / "write_tool_project_sim_v2"
    _ensure_project_q_dir_exists(str(test_project_sim_dir))
    original_cwd = Path.cwd()

    def run_write_test(
        tool: WriteFileTool,
        path_str: str,
        content: str,
        description: str,
        expect_success: bool,
        change_cwd_to_project_sim: bool = False,
        expected_op_desc_in_approval: str = "Write to file" # Check this
    ):
        test_console.print(f"\n[bold]Test Case:[/] {description}")
        test_console.print(f"[cyan]Attempting to write to:[/] '{path_str}'")

        expected_project_root_in_approval = None
        if change_cwd_to_project_sim:
            os.chdir(test_project_sim_dir)
            expected_project_root_in_approval = test_project_sim_dir.resolve()
            test_console.print(
                f"[dim]Changed CWD to: {test_project_sim_dir} (Project Root for this test)[/dim]"
            )
        else:
            expected_project_root_in_approval = _find_project_root(str(original_cwd))
            test_console.print(
                f"[dim]CWD is: {original_cwd} (Project Root for approval: {expected_project_root_in_approval})[/dim]"
            )

        tool_input = WriteFileInput(path=path_str, content=content)
        result = tool.run(tool_input)

        if isinstance(tool.approval_manager, DummyApprovalManager):
            received_pr = tool.approval_manager.last_received_project_root
            received_op_desc = tool.approval_manager.last_operation_description
            if received_pr != expected_project_root_in_approval:
                test_console.print(f"[bold red]PROJECT ROOT MISMATCH IN APPROVAL:[/]")
                test_console.print(f"  Expected: {expected_project_root_in_approval}, Received: {received_pr}")
            if received_op_desc != expected_op_desc_in_approval:
                test_console.print(f"[bold red]OPERATION DESCRIPTION MISMATCH IN APPROVAL:[/]")
                test_console.print(f"  Expected: '{expected_op_desc_in_approval}', Received: '{received_op_desc}'")


        if Path.cwd() != original_cwd:
            os.chdir(original_cwd)
            test_console.print(f"[dim]Restored CWD to: {original_cwd}[/dim]")

        test_console.print(f"  Path Reported by Tool: {result.path}")
        test_console.print(f"  Success: {result.success}, Message: {result.message}")

        final_path_abs = Path(os.path.expanduser(result.path))
        if not final_path_abs.is_absolute():
            final_path_abs = (
                Path.cwd().joinpath(final_path_abs).resolve()
            )

        content_matches = False
        if result.success and final_path_abs.is_file():
            written_content = final_path_abs.read_text()
            if written_content == content:
                content_matches = True
            else:
                test_console.print(
                    f"  [red]Content Mismatch! Expected: '{content}', Got: '{written_content}'[/]"
                )

        actual_success_for_test = result.success and (
            not expect_success or content_matches
        )

        if actual_success_for_test == expect_success:
            test_console.print(
                f"  [bold green]TEST PASSED: Expected success={expect_success} and got it.[/]"
            )
        else:
            test_console.print(
                f"  [bold red]TEST FAILED: Expected success={expect_success}, but got success={result.success} (content match: {content_matches}).[/]"
            )
        test_console.print("-" * 40)

    # --- Test Cases ---
    test_console.rule("[bold]Standard Write Tests (Default: USER_APPROVED by Dummy)[/]")
    approval_manager_user_approves = DummyApprovalManager(
        console=test_console, default_decision="USER_APPROVED"
    )
    write_tool_user_approves = WriteFileTool(
        approval_manager=approval_manager_user_approves
    )

    run_write_test(
        write_tool_user_approves, "project_file.txt", "content1",
        "Write to project file (CWD in project)", True, True
    )
    home_test_file = f"~/{base_test_dir_name}_home_write_test.txt"
    run_write_test(
        write_tool_user_approves, home_test_file, "content2",
        "Write to home file (tilde, CWD in project)", True, True
    )
    abs_home_path = USER_HOME_DIR / f"{base_test_dir_name}_abs_home_write.txt"
    run_write_test(
        write_tool_user_approves, str(abs_home_path), "content3",
        "Write to home file (absolute, CWD in project)", True, True
    )
    run_write_test(
        write_tool_user_approves, "/etc/qx_test_dummy_write.txt", "content4",
        "Write to /etc/ (CWD in project, should fail policy)", False, True
    )

    test_console.rule("[bold]'Approve All' Tests (Dummy simulates conditional session approval)[/]")
    approval_manager_approve_all = DummyApprovalManager(
        console=test_console, default_decision="USER_APPROVED"
    )
    approval_manager_approve_all._approve_all_active = True
    write_tool_approve_all = WriteFileTool(
        approval_manager=approval_manager_approve_all
    )

    run_write_test(
        write_tool_approve_all, "project_file_session.txt", "content_session1",
        "'Approve All': Write to project file (CWD in project)", True, True
    )
    home_session_test_file = f"~/{base_test_dir_name}_home_session_write.txt"
    run_write_test(
        write_tool_approve_all, home_session_test_file, "content_session2",
        "'Approve All': Write to home file (tilde, CWD in project)", True, True
    )
    run_write_test(
        write_tool_approve_all, "/etc/qx_test_dummy_session_write_forbidden.txt", "content_session3",
        "'Approve All': Write to /etc/ (should fail policy despite Approve All)", False, True
    )
    approval_manager_approve_all._approve_all_active = False

    test_console.rule("[bold]Test with User Denying (Dummy set to USER_DENIED)[/]")
    approval_manager_user_denies = DummyApprovalManager(
        console=test_console, default_decision="USER_DENIED"
    )
    write_tool_user_denies = WriteFileTool(
        approval_manager=approval_manager_user_denies
    )
    run_write_test(
        write_tool_user_denies, "project_file_denied.txt", "content_denied",
        "User denies write to project file (CWD in project)", False, True
    )

    test_console.print(
        f"\n[dim]Test project simulation dir: {test_project_sim_dir}.[/dim]"
    )
    test_console.print(
        f"[dim]Other test files may be in USER_HOME_DIR prefixed with '{base_test_dir_name}'.[/dim]"
    )
    test_console.print("\n[bold bright_green]Finished WriteFileTool Tests[/]")

    # shutil.rmtree(base_test_dir_name, ignore_errors=True)
    # for f_path_str_cleanup in [home_test_file, str(abs_home_path), home_session_test_file]:
    #     p_cleanup = Path(os.path.expanduser(f_path_str_cleanup))
    #     if p_cleanup.exists(): p_cleanup.unlink(missing_ok=True)
    # print(f"To cleanup, run: rm -rf {base_test_dir_name}")
    # print(f"And potentially: rm -f {USER_HOME_DIR}/{base_test_dir_name}*")
