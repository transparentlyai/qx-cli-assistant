import logging
import os
from pathlib import Path
from typing import Optional, Type

from pydantic import BaseModel, Field
from qx.core.approvals import ApprovalManager
from qx.core.paths import USER_HOME_DIR, _find_project_root # Used by read_file_impl
from qx.tools.file_operations_base import is_path_allowed # Used by read_file_impl

# Configure logging for this module
logger = logging.getLogger(__name__)


def read_file_impl(path_str: str) -> str: # Changed Optional[str] to str
    """
    Reads the content of a file after path validation.
    This is the core implementation, intended to be called after approval.

    Args:
        path_str: The relative or absolute path to the file.

    Returns:
        The file content as a string, or an error message string if an error occurs
        or the path is not allowed.
    """
    try:
        # project_root determination is crucial for is_path_allowed
        # Assuming Path.cwd() is the intended base for resolving project_root if path_str is relative
        # and project_root isn't explicitly passed.
        current_working_dir = Path.cwd()
        project_root = _find_project_root(str(current_working_dir))
        
        # Resolve path_str. If path_str is absolute, it's used as is.
        # If path_str is relative, it's resolved against current_working_dir.
        absolute_path = current_working_dir.joinpath(path_str).resolve()
        # An alternative for explicit relative-to-project:
        # if project_root and not Path(path_str).is_absolute():
        #    absolute_path = project_root.joinpath(path_str).resolve()
        # else:
        #    absolute_path = Path(path_str).resolve()


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
        # This might be redundant if absolute_path.is_file() check is robust
        logger.error(f"File not found (exception): {path_str}")
        return f"Error: File not found: {path_str}"
    except PermissionError:
        logger.error(f"Permission denied reading file: {path_str}")
        return f"Error: Permission denied reading file: {path_str}"
    except IsADirectoryError:
        logger.error(f"Path is a directory, not a file: {path_str}")
        return f"Error: Path is a directory, not a file: {path_str}"
    except Exception as e:
        logger.error(f"Error reading file '{path_str}': {e}", exc_info=True)
        return f"Error reading file '{path_str}': {e}"


class ReadFileInput(BaseModel):
    """Input model for the ReadFileTool."""
    path: str = Field(..., description="The path to the file to be read. Can be relative or absolute.")
    # Future enhancements:
    # from_line: Optional[int] = Field(None, description="Optional line number to start reading from (1-indexed).")
    # to_line: Optional[int] = Field(None, description="Optional line number to end reading at (inclusive).")

class ReadFileOutput(BaseModel):
    """Output model for the ReadFileTool."""
    path: str = Field(description="The path of the file attempted to be read.")
    content: Optional[str] = Field(None, description="The content of the file if successful, otherwise None.")
    error: Optional[str] = Field(None, description="Error message if the operation was denied, failed, or the file was not found.")


class ReadFileTool:
    """
    A tool to read the content of a specified file.
    This operation is automatically approved by the system (logged as AUTO_APPROVED or SESSION_APPROVED)
    and does not require explicit user confirmation unless 'Approve All' is active.
    Path validation ensures reads are restricted to the project directory or user's home directory.
    """
    name: str = "read_file"
    description: str = (
        "Reads the content of a specified file. Provide a relative or absolute path. "
        "Access is restricted to project files or files within the user's home directory. "
        "This operation is auto-approved."
    )
    input_model: Type[BaseModel] = ReadFileInput
    output_model: Type[BaseModel] = ReadFileOutput

    def __init__(self, approval_manager: ApprovalManager):
        self.approval_manager = approval_manager

    def run(self, args: ReadFileInput) -> ReadFileOutput:
        """
        Handles the (auto)approval and execution of reading a file.
        """
        file_path_arg = args.path

        decision, item_after_approval, _ = \
            self.approval_manager.request_approval(
                operation_description="Read file",
                item_to_approve=file_path_arg,
                operation_type="read_file"
            )

        # For "read_file", item_after_approval should be the same as file_path_arg
        # as modification is not supported for this operation type.
        if item_after_approval != file_path_arg:
            logger.warning(
                f"File path changed during 'read_file' approval from '{file_path_arg}' to '{item_after_approval}'. "
                "This is unexpected. Using the original path argument."
            )
            # Sticking to file_path_arg as modification isn't a feature here.

        if decision in ["AUTO_APPROVED", "SESSION_APPROVED"]:
            logger.info(f"Read operation for '{file_path_arg}' approved (Decision: {decision}). Proceeding to read.")
            
            file_content_or_error_str = read_file_impl(file_path_arg)

            if file_content_or_error_str.startswith("Error:"):
                logger.warning(f"Failed to read file '{file_path_arg}': {file_content_or_error_str}")
                return ReadFileOutput(path=file_path_arg, content=None, error=file_content_or_error_str)
            else:
                # Success
                return ReadFileOutput(path=file_path_arg, content=file_content_or_error_str, error=None)
        
        # Defensive handling for unexpected decisions (should not occur for "read_file" type)
        else:
            error_message = f"File read for '{file_path_arg}' was unexpectedly {decision.lower().replace('_', ' ')}."
            if decision == "PROHIBITED":
                 error_message = f"File read for '{file_path_arg}' prohibited by policy (unexpected for read operations)."
            
            logger.warning(error_message)
            return ReadFileOutput(path=file_path_arg, content=None, error=error_message)


if __name__ == "__main__":
    from rich.console import Console as RichConsole
    import shutil

    # Dummy ApprovalManager for testing
    class DummyApprovalManager:
        def __init__(self, console):
            self.console = console
            self._approve_all_active = False

        def request_approval(self, operation_description, item_to_approve, operation_type, **kwargs):
            self.console.print(
                f"DummyApprovalManager: Requesting approval for '{operation_description}: {item_to_approve}' (type: {operation_type})"
            )
            if operation_type == "read_file":
                if self._approve_all_active:
                    return "SESSION_APPROVED", item_to_approve, None
                return "AUTO_APPROVED", item_to_approve, None
            return "USER_DENIED", item_to_approve, None # Fallback

        def is_globally_approved(self):
            return self._approve_all_active

    test_console = RichConsole()
    approval_manager_instance = DummyApprovalManager(console=test_console)
    read_tool = ReadFileTool(approval_manager=approval_manager_instance)

    test_console.rule("[bold bright_green]Testing ReadFileTool[/]")

    # Setup test environment
    base_test_dir = Path("/tmp/qx_tool_tests")
    test_project_dir = base_test_dir / "qx_read_tool_test_project"
    user_home_files_dir = Path(USER_HOME_DIR) / "qx_read_tool_test_home_files" # Assumes USER_HOME_DIR is sensible

    for p_dir in [test_project_dir, user_home_files_dir]:
        p_dir.mkdir(parents=True, exist_ok=True)
    
    (test_project_dir / ".Q").mkdir(exist_ok=True)
    (test_project_dir / "project_file.txt").write_text("Content of project_file.txt")
    (user_home_files_dir / "home_file.txt").write_text("Content of home_file.txt")
    (test_project_dir / "forbidden_dir").mkdir(exist_ok=True) # For directory read attempt

    original_cwd = Path.cwd()

    def run_read_test(path_str: str, description: str, expect_success: bool, set_cwd_to_project: bool = False):
        test_console.print(f"\n[bold]Test Case:[/] {description}")
        test_console.print(f"[cyan]Attempting to read:[/] '{path_str}'")
        
        if set_cwd_to_project:
            os.chdir(test_project_dir)
            test_console.print(f"[dim]Changed CWD to: {test_project_dir}[/dim]")
        
        tool_input = ReadFileInput(path=path_str)
        result = read_tool.run(tool_input)
        
        if Path.cwd() != original_cwd:
            os.chdir(original_cwd)
            test_console.print(f"[dim]Restored CWD to: {original_cwd}[/dim]")

        test_console.print(f"  Path Attempted: {result.path}")
        if result.content:
            preview = result.content[:70] + "..." if len(result.content) > 70 else result.content
            test_console.print(f"  [green]Content:[/] '{preview}'")
        if result.error:
            test_console.print(f"  [red]Error:[/] {result.error}")

        if expect_success and result.error:
            test_console.print("  [bold red]TEST FAILED: Expected success, got error.[/]")
        elif not expect_success and not result.error:
            test_console.print("  [bold red]TEST FAILED: Expected error, got success.[/]")
        elif expect_success and not result.error:
            test_console.print("  [bold green]TEST PASSED: Successfully read as expected.[/]")
        elif not expect_success and result.error:
            test_console.print("  [bold green]TEST PASSED: Correctly failed as expected.[/]")
        test_console.print("-" * 40)

    # Test cases
    run_read_test(str(test_project_dir / "project_file.txt"), "Read project file (absolute path)", True)
    run_read_test("project_file.txt", "Read project file (relative path from project root)", True, set_cwd_to_project=True)
    run_read_test(str(user_home_files_dir / "home_file.txt"), "Read user home file (absolute path)", True)
    
    # Test relative path from non-project CWD to a home file (requires careful path construction)
    # This depends on how USER_HOME_DIR and path_str are combined.
    # Assuming path_str can be relative to CWD and then resolved.
    # For robustness, absolute paths or paths relative to known roots (project/home) are better for LLM.
    # Let's test a relative path that should resolve correctly if CWD is user's actual home.
    # This test is a bit fragile depending on CWD of test execution.
    # os.chdir(USER_HOME_DIR)
    # run_read_test("qx_read_tool_test_home_files/home_file.txt", "Read user home file (relative from user home CWD)", True)
    # os.chdir(original_cwd)

    run_read_test(str(test_project_dir / "non_existent.txt"), "Read non-existent file", False)
    run_read_test(str(test_project_dir / "forbidden_dir"), "Attempt to read a directory", False)
    run_read_test("/etc/passwd", "Read system file (e.g., /etc/passwd - should be denied by policy)", False)
    
    # Test with "Approve All" active
    test_console.rule("[bold]Testing with 'Approve All' active[/]")
    approval_manager_instance._approve_all_active = True
    run_read_test(str(test_project_dir / "project_file.txt"), "Read project file ('Approve All' active)", True)
    approval_manager_instance._approve_all_active = False # Reset

    test_console.print(f"\n[dim]Test files are in {base_test_dir} and {user_home_files_dir}. Clean up manually if needed.[/dim]")
    test_console.print("\n[bold bright_green]Finished ReadFileTool Tests[/]")

    # shutil.rmtree(base_test_dir, ignore_errors=True)
    # if user_home_files_dir.exists() and "qx_read_tool_test_home_files" in str(user_home_files_dir): # Safety check
    #     shutil.rmtree(user_home_files_dir, ignore_errors=True)
