# pyright: reportPossiblyUnboundVariable=false
import logging
import subprocess
from pathlib import Path # Added
from typing import Optional, Type

from pydantic import BaseModel, Field
from rich.console import Console as RichConsole

from qx.core.approvals import ApprovalManager
from qx.core.paths import _find_project_root # Added

# Configure logging for this module
logger = logging.getLogger(__name__)


class ExecuteShellInput(BaseModel):
    """Input model for the ExecuteShellTool."""

    command: str = Field(
        ...,
        description="The shell command to execute. Must not be a prohibited command (e.g., rm -rf /).",
    )
    # timeout: Optional[int] = Field(
    #     default=60, description="Timeout in seconds for the command execution."
    # )


class ExecuteShellOutput(BaseModel):
    """Output model for the ExecuteShellTool."""

    command: str = Field(description="The command that was attempted.")
    stdout: Optional[str] = Field(None, description="Standard output of the command.")
    stderr: Optional[str] = Field(None, description="Standard error of the command.")
    return_code: Optional[int] = Field(None, description="Return code of the command.")
    error: Optional[str] = Field(
        None, description="Error message if the command was denied or failed to run."
    )


class ExecuteShellTool:
    """
    A tool to execute shell commands.
    Prohibited commands (like 'rm -rf /') are blocked.
    Some safe commands might be auto-approved.
    Most commands require explicit user confirmation, unless 'Approve All' is active.
    """

    name: str = "execute_shell"
    description: str = (
        "Executes a shell command. Risky commands are blocked. "
        "Most commands require user confirmation unless 'Approve All' is active."
    )
    input_model: Type[BaseModel] = ExecuteShellInput
    output_model: Type[BaseModel] = ExecuteShellOutput

    def __init__(self, approval_manager: ApprovalManager, console: Optional[RichConsole] = None):
        self.approval_manager = approval_manager
        self._console = console or RichConsole()

    def run(self, args: ExecuteShellInput) -> ExecuteShellOutput:
        """
        Handles approval and execution of a shell command.
        """
        original_command = args.command
        
        current_project_root = _find_project_root(str(Path.cwd())) # Determine project_root

        decision, command_to_execute, modification_reason = self.approval_manager.request_approval(
            operation_description=f"Execute shell command: {original_command}",
            item_to_approve=original_command,
            allow_modify=True,
            operation_type="shell_command",
            project_root=current_project_root, # Pass project_root
        )

        if decision in ["PROHIBITED", "USER_DENIED", "USER_CANCELLED"]:
            error_msg = f"Command execution '{command_to_execute}' was {decision.lower().replace('_', ' ')}."
            logger.warning(error_msg)
            return ExecuteShellOutput(command=command_to_execute, error=error_msg)

        if decision == "USER_MODIFIED":
            reason_log = f" (Reason: {modification_reason})" if modification_reason else ""
            logger.info(
                f"Command '{command_to_execute}' (original: '{original_command}') approved for execution after modification{reason_log}."
            )
            self._console.print(f"[info]Executing modified command:[/] {command_to_execute}")
        elif decision in ["AUTO_APPROVED", "SESSION_APPROVED", "USER_APPROVED"]:
            logger.info(
                f"Command '{command_to_execute}' approved for execution (Decision: {decision})."
            )
            self._console.print(f"[info]Executing command:[/] {command_to_execute}")
        else: # Should not happen if logic is correct
            error_msg = f"Unexpected approval decision '{decision}' for command '{command_to_execute}'. Aborting."
            logger.error(error_msg)
            return ExecuteShellOutput(command=command_to_execute, error=error_msg)


        try:
            # Simplified execution without timeout for now, can be added back if PydanticAI supports it well
            process = subprocess.run(
                command_to_execute,
                shell=True, # Be cautious with shell=True
                capture_output=True,
                text=True,
                check=False, # Don't raise exception for non-zero exit codes
                # timeout=args.timeout # If timeout is re-added to input
            )
            logger.info(f"Command '{command_to_execute}' executed. Return code: {process.returncode}")
            # self._console.print(f"[info]STDOUT:\n[dim]{process.stdout}[/dim]")
            # if process.stderr:
            #     self._console.print(f"[warning]STDERR:\n[dim]{process.stderr}[/dim]")

            return ExecuteShellOutput(
                command=command_to_execute,
                stdout=process.stdout.strip() if process.stdout else None,
                stderr=process.stderr.strip() if process.stderr else None,
                return_code=process.returncode,
            )
        # except subprocess.TimeoutExpired:
        #     logger.warning(f"Command '{command_to_execute}' timed out after {args.timeout} seconds.")
        #     return ExecuteShellOutput(
        #         command=command_to_execute, error=f"Command timed out after {args.timeout} seconds."
        #     )
        except Exception as e:
            logger.error(f"Failed to execute command '{command_to_execute}': {e}", exc_info=True)
            return ExecuteShellOutput(
                command=command_to_execute, error=f"Failed to execute command: {e}"
            )


if __name__ == "__main__":
    from rich.console import Console as RichConsole
    from qx.core.constants import DEFAULT_PROHIBITED_COMMANDS, DEFAULT_APPROVED_COMMANDS
    from qx.core.paths import USER_HOME_DIR # For dummy is_path_allowed
    from qx.tools.file_operations_base import is_path_allowed # For dummy is_path_allowed

    # Dummy ApprovalManager for testing ExecuteShellTool
    class DummyApprovalManager:
        def __init__(self, console, default_decision="USER_APPROVED"):
            self.console = console
            self._approve_all_active = False
            self.default_decision = default_decision # e.g., "USER_APPROVED", "USER_DENIED"
            self.prohibited_patterns = DEFAULT_PROHIBITED_COMMANDS
            self.approved_patterns = DEFAULT_APPROVED_COMMANDS
            self.last_received_project_root = None


        def get_command_permission_status(self, command: str):
            # Simplified from actual ApprovalManager for testing
            for pattern in self.prohibited_patterns:
                if command.startswith(pattern.split()[0]): # Basic check
                    return "PROHIBITED"
            for pattern in self.approved_patterns:
                if command.startswith(pattern.split()[0]):
                    return "AUTO_APPROVED"
            return "REQUIRES_USER_APPROVAL"

        def request_approval(
            self, operation_description, item_to_approve, operation_type,
            allow_modify=False, content_preview=None, project_root: Optional[Path] = None
        ):
            self.last_received_project_root = project_root
            self.console.print(
                f"DummyApprovalManager: Requesting approval for '{operation_description}' (type: {operation_type}) - Item: '{item_to_approve}'"
            )
            self.console.print(f"DummyApprovalManager: Received project_root: {project_root}")


            if operation_type == "shell_command":
                status = self.get_command_permission_status(item_to_approve)
                if status == "PROHIBITED":
                    self.console.print("DummyApprovalManager: Simulating PROHIBITED for shell command.")
                    return "PROHIBITED", item_to_approve, None
                if status == "AUTO_APPROVED":
                    if self._approve_all_active:
                         self.console.print("DummyApprovalManager: Simulating SESSION_APPROVED (AUTO_APPROVED pattern + Approve All).")
                         return "SESSION_APPROVED", item_to_approve, None
                    self.console.print("DummyApprovalManager: Simulating AUTO_APPROVED for shell command.")
                    return "AUTO_APPROVED", item_to_approve, None
                # If REQUIRES_USER_APPROVAL, falls through to session/default

            if self._approve_all_active:
                # Special handling for write_file if it were used here (it's not for shell)
                # but showing the pattern for completeness if this dummy was reused.
                if operation_type == "write_file" and project_root is not None: # Check project_root exists
                    expanded_path_str = os.path.expanduser(item_to_approve)
                    absolute_path = Path(expanded_path_str)
                    if not absolute_path.is_absolute(): absolute_path = Path.cwd().joinpath(expanded_path_str).resolve()
                    else: absolute_path = absolute_path.resolve()
                    if is_path_allowed(absolute_path, project_root, USER_HOME_DIR):
                        self.console.print(f"DummyApprovalManager: Simulating SESSION_APPROVED for {operation_type} (path OK).")
                        return "SESSION_APPROVED", item_to_approve, None
                    else:
                        self.console.print(f"DummyApprovalManager: Path NOT OK for {operation_type}, bypassing session for this item.")
                        # Fall through to default_decision
                else: # General session approval for other types or if no path check needed
                    self.console.print(f"DummyApprovalManager: Simulating SESSION_APPROVED for {operation_type}.")
                    return "SESSION_APPROVED", item_to_approve, None

            self.console.print(f"DummyApprovalManager: Simulating '{self.default_decision}' as fallback.")
            return self.default_decision, item_to_approve, None # Default if not handled above

        def is_globally_approved(self):
            return self._approve_all_active

    test_console = RichConsole()
    
    # --- Test Cases ---
    def run_shell_test(
        tool: ExecuteShellTool,
        command_str: str,
        description: str,
        expect_success_status: bool, # True if command should run (not denied/prohibited)
        expected_return_code: Optional[int] = 0, # Only if expect_success_status is True
    ):
        test_console.print(f"\n[bold]Test Case:[/] {description}")
        test_console.print(f"[cyan]Attempting to execute:[/] '{command_str}'")

        # Determine what project_root would be passed based on CWD
        # For shell tool, CWD is not changed for tests, so it's always original_cwd's project root
        current_project_root_for_test = _find_project_root(str(Path.cwd()))
        test_console.print(f"[dim]Project Root for approval: {current_project_root_for_test}[/dim]")

        tool_input = ExecuteShellInput(command=command_str)
        result = tool.run(tool_input)

        if isinstance(tool.approval_manager, DummyApprovalManager):
            received_pr = tool.approval_manager.last_received_project_root
            if received_pr != current_project_root_for_test:
                test_console.print(f"[bold red]PROJECT ROOT MISMATCH IN APPROVAL:[/]")
                test_console.print(f"  Expected: {current_project_root_for_test}")
                test_console.print(f"  Received: {received_pr}")


        test_console.print(f"  Command: {result.command}")
        test_console.print(f"  Error: {result.error}")
        test_console.print(f"  Return Code: {result.return_code}")
        test_console.print(f"  Stdout: {result.stdout}")
        test_console.print(f"  Stderr: {result.stderr}")

        command_was_allowed_to_run = not result.error or \
                                   ("denied" not in (result.error or "").lower() and \
                                    "prohibited" not in (result.error or "").lower() and \
                                    "cancelled" not in (result.error or "").lower())


        if command_was_allowed_to_run == expect_success_status:
            if expect_success_status and result.return_code != expected_return_code:
                test_console.print(f"  [bold red]TEST FAILED: Expected return code {expected_return_code}, got {result.return_code}.[/]")
            else:
                test_console.print(f"  [bold green]TEST PASSED: Correctly {'allowed' if expect_success_status else 'disallowed/failed as expected'}.[/]")
        else:
            test_console.print(f"  [bold red]TEST FAILED: Expected command to be {'allowed' if expect_success_status else 'disallowed/failed'}, but it was {'allowed' if command_was_allowed_to_run else 'disallowed/failed'}.[/]")
        test_console.print("-" * 40)

    test_console.rule("[bold]Standard Shell Tests (Dummy default: USER_APPROVED)[/]")
    approval_manager_ua = DummyApprovalManager(test_console, default_decision="USER_APPROVED")
    shell_tool_ua = ExecuteShellTool(approval_manager=approval_manager_ua)

    run_shell_test(shell_tool_ua, "echo 'Hello from test'", "Simple echo (User Approved)", True, 0)
    run_shell_test(shell_tool_ua, "ls -l non_existent_file_for_error", "ls non-existent (User Approved, command fails)", True, expected_return_code=None) # Return code depends on ls version
    run_shell_test(shell_tool_ua, "git status", "git status (Auto-Approved by pattern)", True, 0) # `git` is an approved pattern
    run_shell_test(shell_tool_ua, "rm -rf /", "Prohibited command rm -rf /", False)

    test_console.rule("[bold]'Approve All' Shell Tests[/]")
    approval_manager_aa = DummyApprovalManager(test_console, default_decision="USER_APPROVED")
    approval_manager_aa._approve_all_active = True
    shell_tool_aa = ExecuteShellTool(approval_manager=approval_manager_aa)

    run_shell_test(shell_tool_aa, "echo 'Hello from session approval'", "'Approve All': Simple echo", True, 0)
    run_shell_test(shell_tool_aa, "git log -1", "'Approve All': git log (Auto-Approved pattern + Session)", True, 0)
    run_shell_test(shell_tool_aa, "sudo apt update", "'Approve All': sudo command (Prohibited pattern)", False) # sudo is prohibited
    
    approval_manager_aa._approve_all_active = False # Reset

    test_console.rule("[bold]User Denies Shell Tests[/]")
    approval_manager_ud = DummyApprovalManager(test_console, default_decision="USER_DENIED")
    shell_tool_ud = ExecuteShellTool(approval_manager=approval_manager_ud)
    run_shell_test(shell_tool_ud, "echo 'This should be denied'", "User denies echo", False)


    test_console.print("\n[bold bright_green]Finished ExecuteShellTool Tests[/]")