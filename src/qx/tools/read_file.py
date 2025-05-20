# pyright: reportPossiblyUnboundVariable=false
import logging
import os
from pathlib import Path
from typing import Optional, Type

from pydantic import BaseModel, Field

from qx.core.approvals import ApprovalManager
from qx.core.approvals import OperationType
from qx.core.paths import USER_HOME_DIR
from qx.core.paths import _find_project_root
from qx.tools.file_operations_base import is_path_allowed

# Configure logging for this module
logger = logging.getLogger(__name__)


def read_file_impl(path_str: str) -> str:
    """
    Reads the content of a file after path validation.
    This is the core implementation, intended to be called after approval.

    Args:
        path_str: The relative or absolute path to the file. Tilde expansion is performed.

    Returns:
        The file content as a string, or an error message string if an error occurs
        or the path is not allowed.
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
                f"Read access denied by policy for path: {absolute_path}. "
                f"Project root: {project_root}, User home: {USER_HOME_DIR}"
            )
            return f"Error: Access denied by policy for path: {absolute_path}"

        if not absolute_path.is_file():
            logger.error(f"File not found or not a file: {absolute_path}")
            return f"Error: File not found or is not a regular file: {absolute_path}"

        content = absolute_path.read_text(encoding="utf-8")
        logger.info(f"Successfully read file: {absolute_path}")
        return content

    except FileNotFoundError:
        logger.error(f"File not found (exception): {expanded_path_str}")
        return f"Error: File not found: {expanded_path_str}"
    except PermissionError:
        logger.error(f"Permission denied reading file: {expanded_path_str}")
        return f"Error: Permission denied reading file: {expanded_path_str}"
    except IsADirectoryError:
        logger.error(f"Path is a directory, not a file: {expanded_path_str}")
        return f"Error: Path is a directory, not a file: {expanded_path_str}"
    except Exception as e:
        logger.error(f"Error reading file '{expanded_path_str}': {e}", exc_info=True)
        return f"Error reading file '{expanded_path_str}': {e}"


class ReadFileInput(BaseModel):
    """Input model for the ReadFileTool."""

    path: str = Field(
        ...,
        description="The path to the file to be read. Can be relative, absolute, or start with '~'.",
    )


class ReadFileOutput(BaseModel):
    """Output model for the ReadFileTool."""

    path: str = Field(
        description="The (expanded) path of the file attempted to be read."
    )
    content: Optional[str] = Field(
        None, description="The content of the file if successful, otherwise None."
    )
    error: Optional[str] = Field(
        None,
        description="Error message if the operation was denied, failed, or the file was not found.",
    )


class ReadFileTool:
    """
    A tool to read the content of a specified file.
    If the file is within the current project, this operation is automatically approved by the system
    (logged as AUTO_APPROVED or SESSION_APPROVED).
    If the file is outside the project but within the user's home directory, explicit user confirmation is required.
    Path validation ensures reads are ultimately restricted to the project directory or user's home directory.
    Tilde (~) in the path is expanded to the user's home directory.
    """

    name: str = "read_file"
    description: str = (
        "Reads the content of a specified file. Provide a relative, absolute, or tilde-based path (e.g., ~/file.txt). "
        "If the file is within the current project, the operation is auto-approved. "
        "If the file is outside the project but within your home directory, user confirmation will be requested. "
        "Access is ultimately restricted by policy to project files or files within the user's home directory."
    )
    input_model: Type[BaseModel] = ReadFileInput
    output_model: Type[BaseModel] = ReadFileOutput

    def __init__(self, approval_manager: ApprovalManager):
        self.approval_manager = approval_manager

    def run(self, args: ReadFileInput) -> ReadFileOutput:
        """
        Handles approval and execution of reading a file.
        Performs tilde expansion and determines approval type based on path location.
        """
        original_path_arg = args.path
        expanded_path_arg = os.path.expanduser(original_path_arg)

        current_working_dir = Path.cwd()
        path_to_evaluate_abs = Path(expanded_path_arg)
        if not path_to_evaluate_abs.is_absolute():
            path_to_evaluate_abs = current_working_dir.joinpath(
                expanded_path_arg
            ).resolve()
        else:
            path_to_evaluate_abs = path_to_evaluate_abs.resolve()

        project_root_path_obj = _find_project_root(str(current_working_dir))

        # Default operation_description for the prompt
        op_desc_for_prompt = "Read file"
        
        operation_type_for_approval: OperationType = "read_file"
        is_within_project = False

        if project_root_path_obj:
            project_root_abs = project_root_path_obj.resolve()
            if (
                path_to_evaluate_abs == project_root_abs
                or project_root_abs in path_to_evaluate_abs.parents
            ):
                is_within_project = True

            dot_q_path_abs = (project_root_abs / ".Q").resolve()
            if (
                path_to_evaluate_abs == dot_q_path_abs
                or dot_q_path_abs in path_to_evaluate_abs.parents
            ):
                is_within_project = True

        if not is_within_project and project_root_path_obj:
            # If outside project, it's treated as a generic operation needing explicit approval
            # unless it's auto-denied by is_path_allowed later.
            operation_type_for_approval = "generic"
            # op_desc_for_prompt remains "Read file" as that's what QX wants to do.
            logger.info(
                f"Path '{expanded_path_arg}' is outside project '{project_root_path_obj}'. Requesting generic approval for read."
            )
        elif is_within_project:
            # Stays as "read_file" type, which is auto-approved by ApprovalManager
            logger.info(
                f"Path '{expanded_path_arg}' is within project '{project_root_path_obj}'. Using 'read_file' auto-approval type."
            )
        else: # No project context, but still a "read_file" operation type for ApprovalManager
            logger.info(
                f"No project context for '{expanded_path_arg}'. Using 'read_file' auto-approval type."
            )

        decision, item_after_approval, _ = self.approval_manager.request_approval(
            operation_description=op_desc_for_prompt, # Standardized description
            item_to_approve=expanded_path_arg,
            operation_type=operation_type_for_approval,
            project_root=project_root_path_obj,
        )

        if item_after_approval != expanded_path_arg:
            logger.warning(
                f"File path changed during 'read_file' approval from '{expanded_path_arg}' to '{item_after_approval}'. "
                f"This is unexpected for read_file. Using the originally expanded path: {expanded_path_arg}."
            )

        path_to_read = expanded_path_arg

        if decision in ["AUTO_APPROVED", "SESSION_APPROVED", "USER_APPROVED"]:
            logger.info(
                f"Read operation for '{path_to_read}' (original: '{original_path_arg}') approved (Decision: {decision}). Proceeding to read."
            )

            file_content_or_error_str = read_file_impl(path_to_read)

            if file_content_or_error_str.startswith("Error:"):
                logger.warning(
                    f"Failed to read file '{path_to_read}': {file_content_or_error_str}"
                )
                return ReadFileOutput(
                    path=path_to_read, content=None, error=file_content_or_error_str
                )
            else:
                return ReadFileOutput(
                    path=path_to_read, content=file_content_or_error_str, error=None
                )
        else:
            error_message = f"{op_desc_for_prompt} for '{path_to_read}' (original: '{original_path_arg}') was {decision.lower().replace('_', ' ')}."
            if decision == "PROHIBITED": # This specific case might not be hit if is_path_allowed catches it first in impl
                error_message = f"{op_desc_for_prompt} for '{path_to_read}' (original: '{original_path_arg}') prohibited by policy."

            logger.warning(error_message)
            return ReadFileOutput(path=path_to_read, content=None, error=error_message)


if __name__ == "__main__":
    import shutil
    from rich.console import Console as RichConsole
    from qx.core.paths import _ensure_project_q_dir_exists

    class DummyApprovalManager:
        def __init__(self, console):
            self.console = console
            self._approve_all_active = False
            self.last_received_project_root = None
            self.last_operation_description = None

        def request_approval(
            self,
            operation_description,
            item_to_approve,
            operation_type,
            project_root: Optional[Path] = None,
            **kwargs,
        ):
            self.last_received_project_root = project_root
            self.last_operation_description = operation_description # Store for verification
            self.console.print(
                f"DummyApprovalManager: Requesting approval for '{operation_description}' (type: {operation_type}) - Item: '{item_to_approve}'"
            )
            self.console.print(
                f"DummyApprovalManager: Received project_root: {project_root}"
            )

            if operation_type == "read_file":
                if self._approve_all_active:
                    return "SESSION_APPROVED", item_to_approve, None
                return "AUTO_APPROVED", item_to_approve, None
            elif operation_type == "generic":
                if self._approve_all_active:
                    self.console.print(
                        "DummyApprovalManager: Simulating SESSION_APPROVED for 'generic' type due to Approve All."
                    )
                    return "SESSION_APPROVED", item_to_approve, None
                self.console.print(
                    "DummyApprovalManager: Simulating USER_APPROVED for 'generic' type."
                )
                return "USER_APPROVED", item_to_approve, None
            return "USER_DENIED", item_to_approve, None

        def is_globally_approved(self):
            return self._approve_all_active

    test_console = RichConsole()
    approval_manager_instance = DummyApprovalManager(console=test_console)
    read_tool = ReadFileTool(approval_manager=approval_manager_instance)

    test_console.rule(
        "[bold bright_green]Testing ReadFileTool with Standardized Descriptions[/]"
    )

    base_test_dir_name = "tmp_qx_read_tool_tests_v3"
    Path(base_test_dir_name).mkdir(exist_ok=True)
    base_test_dir = Path(base_test_dir_name).resolve()
    test_project_dir = base_test_dir / "qx_read_tool_test_project_v3"
    _ensure_project_q_dir_exists(str(test_project_dir))
    test_home_file_relative_path = "qx_test_home_file_for_readtool_v3.txt"
    home_file_path_obj = USER_HOME_DIR / test_home_file_relative_path

    if test_project_dir.exists():
        shutil.rmtree(test_project_dir)
    test_project_dir.mkdir(parents=True, exist_ok=True)
    _ensure_project_q_dir_exists(str(test_project_dir))
    (test_project_dir / "project_file.txt").write_text("Content of project_file.txt")
    home_file_path_obj.write_text("Content of home_file.txt in actual user home")
    (test_project_dir / "forbidden_dir").mkdir(exist_ok=True)

    original_cwd = Path.cwd()

    def run_read_test(
        path_str: str,
        description: str,
        expect_success: bool,
        change_cwd_to_project_root: bool = False,
        expected_op_desc_in_approval: str = "Read file" # New check
    ):
        test_console.print(f"\n[bold]Test Case:[/] {description}")
        test_console.print(f"[cyan]Attempting to read:[/] '{path_str}'")

        expected_project_root_in_approval = None
        if change_cwd_to_project_root:
            os.chdir(test_project_dir)
            expected_project_root_in_approval = test_project_dir.resolve()
            test_console.print(
                f"[dim]Changed CWD to: {test_project_dir} (Project Root for this test)[/dim]"
            )
        else:
            expected_project_root_in_approval = _find_project_root(str(original_cwd))
            test_console.print(
                f"[dim]CWD is: {original_cwd} (Project Root for approval: {expected_project_root_in_approval})[/dim]"
            )

        tool_input = ReadFileInput(path=path_str)
        result = read_tool.run(tool_input)

        if isinstance(read_tool.approval_manager, DummyApprovalManager):
            received_pr = read_tool.approval_manager.last_received_project_root
            received_op_desc = read_tool.approval_manager.last_operation_description
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
        if result.content:
            preview = (
                result.content[:70] + "..."
                if len(result.content) > 70
                else result.content
            )
            test_console.print(f"  [green]Content:[/] '{preview}'")
        if result.error:
            test_console.print(f"  [red]Error:[/] {result.error}")

        success = not result.error
        if success == expect_success:
            test_console.print(
                f"  [bold green]TEST PASSED: Expected {'success' if expect_success else 'failure'} and got it.[/]"
            )
        else:
            test_console.print(
                f"  [bold red]TEST FAILED: Expected {'success' if expect_success else 'failure'}, but got {'success' if success else 'failure'}.[/]"
            )
        test_console.print("-" * 40)

    # --- Test Cases ---
    test_console.rule("[bold]Tests with CWD = Test Project Root[/]")
    run_read_test(
        str(test_project_dir / "project_file.txt"),
        "Read project file (absolute path, CWD in project)", True, True
    )
    run_read_test(
        "project_file.txt",
        "Read project file (relative path, CWD in project)", True, True
    )
    (test_project_dir / ".Q" / "q_internal.txt").write_text("Internal Q file")
    run_read_test(
        ".Q/q_internal.txt",
        "Read .Q file (relative path, CWD in project)", True, True
    )
    run_read_test(
        f"~/{test_home_file_relative_path}",
        "Read user home file (tilde path, CWD in project - outside project, needs generic approval)", True, True
    )
    run_read_test(
        str(home_file_path_obj),
        "Read user home file (absolute path, CWD in project - outside project, needs generic approval)", True, True
    )
    run_read_test(
        "non_existent.txt", "Read non-existent file (CWD in project)", False, True
    )
    run_read_test(
        "~/non_existent_home_file.txt", "Read non-existent tilde file (CWD in project)", False, True
    )
    run_read_test(
        str(test_project_dir / "forbidden_dir"), "Attempt to read a directory (CWD in project)", False, True
    )
    run_read_test(
        "/etc/passwd", "Read system file /etc/passwd (CWD in project - outside project & home, denied by policy)", False, True
    )

    test_console.rule("[bold]Tests with CWD = Original CWD (Outside Test Project Root)[/]")
    is_test_project_in_home = (
        USER_HOME_DIR.resolve() in test_project_dir.resolve().parents
        or USER_HOME_DIR.resolve() == test_project_dir.resolve().parent
    )
    run_read_test(
        str(test_project_dir / "project_file.txt"),
        f"Read file from test_project_dir (abs path, CWD is original) - outside current project, needs generic. Expected success: {is_test_project_in_home}",
        is_test_project_in_home, False
    )

    test_console.rule("[bold]Testing with 'Approve All' active[/]")
    approval_manager_instance._approve_all_active = True
    run_read_test(
        f"~/{test_home_file_relative_path}",
        "Read tilde path (CWD in project, 'Approve All' active - should be SESSION_APPROVED for generic)", True, True
    )
    approval_manager_instance._approve_all_active = False

    test_console.print(f"\n[dim]Test project files are in {test_project_dir}.[/dim]")
    test_console.print(f"[dim]Test home file is {home_file_path_obj}.[/dim]")
    test_console.print("\n[bold bright_green]Finished ReadFileTool Tests[/]")

    # shutil.rmtree(base_test_dir_name, ignore_errors=True)
    # if home_file_path_obj.exists() and test_home_file_relative_path in str(home_file_path_obj):
    #     home_file_path_obj.unlink(missing_ok=True)
    # print(f"To cleanup, run: rm -rf {base_test_dir_name} && rm -f {home_file_path_obj}")
