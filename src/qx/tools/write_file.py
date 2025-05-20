import logging
import os
from pathlib import Path
from typing import Optional, Type

from pydantic import BaseModel, Field
from qx.core.approvals import ApprovalManager # Assuming WriteFileTool will use this
from qx.core.paths import USER_HOME_DIR, _find_project_root
from qx.tools.file_operations_base import is_path_allowed

# Configure logging for this module
logger = logging.getLogger(__name__)


def write_file_impl(path_str: str, content: str) -> tuple[bool, str]:
    """
    Writes content to a file after path validation. Tilde expansion is performed.
    This is the core implementation, intended to be called after approval.

    Args:
        path_str: The relative or absolute path to the file. Tilde expansion is performed.
        content: The string content to write to the file.

    Returns:
        A tuple (success: bool, message_or_path: str).
        If successful, (True, absolute_path_str).
        If failed, (False, error_message_str).
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

        # Check if the target path is allowed for writing
        if not is_path_allowed(absolute_path, project_root, USER_HOME_DIR, allow_home_subdir=True, allow_project_subdir=True):
            error_msg = f"Error: Write access denied by policy for path: {absolute_path}"
            logger.error(f"{error_msg}. Project root: {project_root}, User home: {USER_HOME_DIR}")
            return False, error_msg

        parent_dir = absolute_path.parent
        if not parent_dir.exists():
            # Check if creating the parent directory is allowed
            if not is_path_allowed(parent_dir, project_root, USER_HOME_DIR, allow_home_subdir=True, allow_project_subdir=True):
                error_msg = f"Error: Write access denied by policy for creating parent directory: {parent_dir}"
                logger.error(error_msg)
                return False, error_msg
            try:
                parent_dir.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created parent directory: {parent_dir}")
            except Exception as e_mkdir:
                error_msg = f"Error creating parent directory '{parent_dir}': {e_mkdir}"
                logger.error(error_msg, exc_info=True)
                return False, error_msg
        
        if absolute_path.is_dir():
            error_msg = f"Error: Path is a directory, cannot write file: {absolute_path}"
            logger.error(error_msg)
            return False, error_msg

        absolute_path.write_text(content, encoding="utf-8")
        logger.info(f"Successfully wrote to file: {absolute_path}")
        return True, str(absolute_path)

    except PermissionError:
        error_msg = f"Error: Permission denied writing to file: {expanded_path_str}"
        logger.error(error_msg)
        return False, error_msg
    except IsADirectoryError: # Should be caught by absolute_path.is_dir() earlier
        error_msg = f"Error: Path is a directory, cannot write file: {expanded_path_str}"
        logger.error(error_msg)
        return False, error_msg
    except Exception as e:
        error_msg = f"Error writing file '{expanded_path_str}': {e}"
        logger.error(error_msg, exc_info=True)
        return False, error_msg

class WriteFileInput(BaseModel):
    path: str = Field(..., description="The path to the file to be written. Can be relative, absolute, or start with '~'.")
    content: str = Field(..., description="The content to write to the file. Do not use triple quotes for the content argument passed to the tool.")

class WriteFileOutput(BaseModel):
    path: str = Field(description="The (expanded) path of the file attempted to be written.")
    success: bool = Field(description="True if the file was written successfully, False otherwise.")
    message: Optional[str] = Field(None, description="Message detailing the outcome, error if any.")

class WriteFileTool:
    name: str = "write_file"
    description: str = (
        "Writes content to a specified file. Creates parent directories if they don't exist. "
        "Provide a relative, absolute, or tilde-based path (e.g., ~/file.txt). "
        "Access is restricted to project files or files within the user's home directory. "
        "Requires user approval unless 'Approve All' is active."
    )
    input_model: Type[BaseModel] = WriteFileInput
    output_model: Type[BaseModel] = WriteFileOutput

    def __init__(self, approval_manager: ApprovalManager):
        self.approval_manager = approval_manager

    def run(self, args: WriteFileInput) -> WriteFileOutput:
        original_path_arg = args.path
        expanded_path_arg = os.path.expanduser(original_path_arg)
        content_to_write = args.content

        approval_item = {"path": expanded_path_arg, "content_preview": content_to_write[:200] + ("..." if len(content_to_write) > 200 else "")}
        operation_desc = f"Write file: {original_path_arg} (expanded: {expanded_path_arg})"

        decision, item_after_approval, notes = \
            self.approval_manager.request_approval(
                operation_description=operation_desc,
                item_to_approve=approval_item,
                operation_type="write_file",
                current_content_getter=lambda p=expanded_path_arg: Path(p).read_text(encoding='utf-8') if Path(p).is_file() else None
            )
        
        # item_after_approval for write_file could potentially allow content modification by user.
        # For now, we assume it's primarily for path confirmation or content approval.
        # If content can be modified, need to extract it from item_after_approval.
        # Current approval logic seems to return the original item if approved, or a modified one.
        # Let's assume item_after_approval is still the dict or just the path if not modified.

        final_path_to_write = expanded_path_arg # Default to expanded path
        final_content_to_write = content_to_write

        if isinstance(item_after_approval, dict) and item_after_approval.get("path") == expanded_path_arg:
            # Potentially user could have edited content if approval system supports it.
            # For now, let's assume if item_after_approval is a dict and path matches, the content is either original or approved as is.
            # If the approval mechanism could change the content, we'd use item_after_approval.get('content', content_to_write)
            pass # Stick with original content unless approval explicitly modifies it.
        elif isinstance(item_after_approval, str) and item_after_approval != expanded_path_arg:
            # This case implies the path itself might have been altered during approval, which is less common for write.
            logger.warning(f"Path was unexpectedly altered during approval from '{expanded_path_arg}' to '{item_after_approval}'. This is not typical for write_file. Proceeding with original expanded path: '{expanded_path_arg}'")
            # Sticking to expanded_path_arg, as path modification by approval is tricky here.

        if decision not in ["USER_APPROVED", "SESSION_APPROVED"]:
            msg = f"Write operation for '{expanded_path_arg}' (original: '{original_path_arg}') was {decision.lower().replace('_', ' ')}. {notes or ''}"
            logger.warning(msg)
            return WriteFileOutput(path=expanded_path_arg, success=False, message=msg)

        logger.info(f"Write operation for '{final_path_to_write}' (original: '{original_path_arg}') approved (Decision: {decision}). Proceeding to write.")
        
        success, message_or_path = write_file_impl(final_path_to_write, final_content_to_write)
        
        if success:
            return WriteFileOutput(path=message_or_path, success=True, message=f"Successfully wrote to file: {message_or_path}")
        else:
            # message_or_path is an error message here
            return WriteFileOutput(path=final_path_to_write, success=False, message=message_or_path)


if __name__ == "__main__":
    from rich.console import Console as RichConsole
    import shutil

    class DummyApprovalManager:
        def __init__(self, console, approve_all=False, user_decision="USER_APPROVED"):
            self.console = console
            self._approve_all_active = approve_all
            self.user_decision = user_decision

        def request_approval(self, operation_description, item_to_approve, operation_type, **kwargs):
            self.console.print(
                f"DummyApprovalManager: Requesting approval for '{operation_description}' (type: {operation_type}) - Item: '{item_to_approve}'"
            )
            if self._approve_all_active:
                return "SESSION_APPROVED", item_to_approve, "Session approved"
            # Simulate user approval for write operations if not approve_all
            if operation_type == "write_file":
                if self.user_decision == "USER_APPROVED":
                    return "USER_APPROVED", item_to_approve, "User approved"
                else:
                    return self.user_decision, item_to_approve, "User denied / other"
            return "USER_DENIED", item_to_approve, "Denied by default rule" 

        def is_globally_approved(self):
            return self._approve_all_active

    test_console = RichConsole()
    
    base_test_dir = Path("/tmp/qx_tool_tests_write") 
    test_project_dir = base_test_dir / "qx_write_tool_test_project"
    test_home_dir_for_write = USER_HOME_DIR / "qx_write_tool_test_home_files"

    def setup_test_dirs():
        for p_dir in [test_project_dir, test_home_dir_for_write]:
            p_dir.mkdir(parents=True, exist_ok=True)
        (test_project_dir / ".Q").mkdir(exist_ok=True) # Mark as project

    def cleanup_test_dirs():
        # shutil.rmtree(base_test_dir, ignore_errors=True)
        # shutil.rmtree(test_home_dir_for_write, ignore_errors=True)
        test_console.print(f"[dim]Manual cleanup: rm -rf {base_test_dir} {test_home_dir_for_write}[/dim]")
        pass

    original_cwd = Path.cwd()

    def run_write_test(path_str: str, content: str, description: str, expect_success: bool, 
                         approval_manager_override: Optional[DummyApprovalManager] = None, 
                         set_cwd_to_project: bool = False):
        test_console.print(f"\n[bold]Test Case:[/] {description}")
        test_console.print(f"[cyan]Attempting to write to:[/] '{path_str}', Content: '{content[:30]}...'")
        
        current_approval_manager = approval_manager_override or DummyApprovalManager(test_console)
        write_tool = WriteFileTool(approval_manager=current_approval_manager)

        if set_cwd_to_project:
            os.chdir(test_project_dir)
            test_console.print(f"[dim]Changed CWD to: {test_project_dir}[/dim]")

        tool_input = WriteFileInput(path=path_str, content=content)
        result = write_tool.run(tool_input)

        if Path.cwd() != original_cwd:
            os.chdir(original_cwd)
            test_console.print(f"[dim]Restored CWD to: {original_cwd}[/dim]")

        test_console.print(f"  Path Reported: {result.path}")
        test_console.print(f"  Success: {result.success}")
        test_console.print(f"  Message: {result.message}")

        final_path_obj = Path(os.path.expanduser(result.path)) # Use result.path as it is what the tool reports
        
        content_matches = False
        if result.success and final_path_obj.is_file():
            written_content = final_path_obj.read_text(encoding="utf-8")
            content_matches = written_content == content
            if not content_matches:
                test_console.print(f"  [bold red]Content Mismatch! Expected: '{content}', Got: '{written_content}'[/]")

        if expect_success and not result.success:
            test_console.print("  [bold red]TEST FAILED: Expected success, got failure.[/]")
        elif not expect_success and result.success:
            test_console.print("  [bold red]TEST FAILED: Expected failure, got success.[/]")
        elif expect_success and result.success and not content_matches:
            test_console.print("  [bold red]TEST FAILED: Write reported success, but content mismatch or file not readable.[/]")
        elif expect_success and result.success and content_matches:
            test_console.print("  [bold green]TEST PASSED: Successfully wrote and content matches.[/]")
        elif not expect_success and not result.success:
            test_console.print("  [bold green]TEST PASSED: Correctly failed as expected.[/]")
        test_console.print("-" * 40)

    # --- TEST EXECUTION ---
    test_console.rule("[bold bright_blue]Testing WriteFileTool with Tilde Expansion[/]")
    setup_test_dirs()

    # Test successful writes
    run_write_test("project_file.txt", "Project content.", "Write to project file (relative)", True, set_cwd_to_project=True)
    run_write_test(str(test_project_dir / "abs_project_file.txt"), "Absolute project content.", "Write to project file (absolute)", True)
    run_write_test("~/home_test_file.txt", "Home tilde content.", "Write to user home (tilde path)", True)
    run_write_test(str(test_home_dir_for_write / "abs_home_file.txt"), "Absolute home content.", "Write to user home (absolute path)", True)
    run_write_test("~/new_dir/new_file_in_home.txt", "Nested new file in home.", "Write to new nested dir in home (tilde)", True)
    run_write_test(str(test_project_dir / "new_proj_subdir" / "new_file.txt"), "Nested new file in project.", "Write to new nested dir in project (absolute)", True)

    # Test denied writes (policy)
    run_write_test("/etc/system_file_attempt.txt", "System content.", "Write to system path (denied by policy)", False)
    
    # Test denied by user
    denied_approval_manager = DummyApprovalManager(test_console, user_decision="USER_DENIED")
    run_write_test("~/denied_by_user.txt", "Content for denied.", "Write to user home (user denies)", False, approval_manager_override=denied_approval_manager)

    # Test 'Approve All' (Session Approved)
    session_approval_manager = DummyApprovalManager(test_console, approve_all=True)
    run_write_test("~/session_approved_file.txt", "Session approved content.", "Write to user home ('Approve All' active)", True, approval_manager_override=session_approval_manager)
    
    # Test writing to a directory path (should fail)
    run_write_test(str(test_project_dir), "Content for dir.", "Attempt to write to a directory path", False)
    run_write_test("~", "Content for home dir.", "Attempt to write to home directory itself as file", False)

    cleanup_test_dirs()
    test_console.print("\n[bold bright_blue]Finished WriteFileTool Tests[/]")
