import logging
import shlex
import subprocess
from typing import Any, Dict, Optional, Type

from pydantic import BaseModel, Field

from qx.core.approvals import ApprovalManager # Changed from approvals_manager
from qx.core.constants import SHELL_COMMAND_TIMEOUT
from rich.console import Console as RichConsole # For __main__

# Configure logging for this module
logger = logging.getLogger(__name__)


class ShellCommandInput(BaseModel):
    """Input model for the ExecuteShellTool."""
    command: str = Field(..., description="The shell command to execute.")


class ShellCommandOutput(BaseModel):
    """Output model for the ExecuteShellTool."""
    command: str = Field(description="The command that was intended for execution or was executed.")
    stdout: str = Field(description="Standard output of the command.")
    stderr: str = Field(description="Standard error of the command.")
    exit_code: int = Field(description="Exit code of the command.")
    error: Optional[str] = Field(None, description="High-level error message if execution was prevented or failed fundamentally (e.g., prohibited, cancelled, timeout).")
    modified_from: Optional[str] = Field(None, description="The original command if it was modified before execution.")
    modification_reason: Optional[str] = Field(None, description="The reason provided for modifying the command.")


class ExecuteShellTool:
    """
    A tool to execute shell commands with a robust approval and security layer.
    It uses ApprovalManager to check against prohibited/approved lists and prompt the user.
    """
    name: str = "execute_shell"
    description: str = (
        "Executes a shell command after going through an approval process. "
        "Handles prohibited commands, auto-approved commands, and prompts the user for others. "
        "Allows command modification during the approval process."
    )
    input_model: Type[BaseModel] = ShellCommandInput
    output_model: Type[BaseModel] = ShellCommandOutput

    def __init__(self, approval_manager: ApprovalManager):
        self.approval_manager = approval_manager

    def _execute_subprocess(self, command_to_run: str) -> Dict[str, Any]:
        """
        Executes the given shell command using subprocess.
        This is called only after the command has been approved.
        """
        logger.info(f"Executing approved command: {command_to_run}")
        try:
            process = subprocess.run(
                command_to_run,
                shell=True, # Allows shell features; use with caution, mitigated by approval.
                capture_output=True,
                text=True,
                timeout=SHELL_COMMAND_TIMEOUT,
                check=False, # Do not raise exception for non-zero exit codes
            )
            stdout = process.stdout.strip()
            stderr = process.stderr.strip()
            returncode = process.returncode

            if stdout:
                logger.debug(f"Command stdout: {stdout}")
            if stderr:
                logger.warning(f"Command stderr: {stderr}")
            logger.info(f"Command return code: {returncode}")

            return {"stdout": stdout, "stderr": stderr, "returncode": returncode}

        except subprocess.TimeoutExpired:
            logger.error(f"Command '{command_to_run}' timed out after {SHELL_COMMAND_TIMEOUT} seconds.")
            return {
                "stdout": "",
                "stderr": f"Command timed out after {SHELL_COMMAND_TIMEOUT} seconds.",
                "returncode": -1, # Standardize timeout exit code
                "error_type": "Timeout",
            }
        except FileNotFoundError:
            cmd_name = shlex.split(command_to_run)[0] if command_to_run else "empty command"
            logger.error(f"Command not found: {cmd_name}")
            return {
                "stdout": "",
                "stderr": f"Command not found: {cmd_name}",
                "returncode": 127, # Common exit code for command not found
                "error_type": "Command not found",
            }
        except Exception as e:
            logger.error(f"Error executing command '{command_to_run}': {e}", exc_info=True)
            return {
                "stdout": "",
                "stderr": f"An unexpected error occurred during execution: {e}",
                "returncode": -2, # Standardize general execution error
                "error_type": f"Execution error: {e}",
            }

    def run(self, args: ShellCommandInput) -> ShellCommandOutput:
        """
        Manages the approval workflow and executes the command if approved.
        """
        current_command = args.command
        original_command = args.command
        is_modified = False
        final_modification_reason: Optional[str] = None
        executed_command: Optional[str] = None # The command that is finally executed

        while True:
            decision, item_after_approval, mod_reason = \
                self.approval_manager.request_approval(
                    operation_description="Execute shell command",
                    item_to_approve=current_command,
                    operation_type="shell_command"
                )

            if decision == "USER_MODIFIED":
                if not item_after_approval: # Handle case where user clears the command during modification
                    logger.warning("Command modification resulted in an empty command. Cancelling.")
                    return ShellCommandOutput(
                        command=original_command, stdout="", stderr="Command modification cancelled (empty command).",
                        exit_code=-1, error="Cancelled",
                        modified_from=original_command if original_command != current_command else None,
                        modification_reason=final_modification_reason
                    )
                current_command = item_after_approval
                final_modification_reason = mod_reason
                is_modified = True
                logger.info(f"Command modified to: '{current_command}'. Re-evaluating approval.")
                continue  # Re-evaluate the modified command

            elif decision in ["AUTO_APPROVED", "SESSION_APPROVED", "USER_APPROVED"]:
                executed_command = current_command # This is the command to execute
                logger.info(f"Command '{executed_command}' approved for execution (Decision: {decision}).")
                break # Proceed to execution

            elif decision == "PROHIBITED":
                logger.warning(f"Command '{current_command}' execution denied: Prohibited by policy.")
                return ShellCommandOutput(
                    command=current_command, stdout="", stderr=f"Command '{current_command}' is prohibited by policy.",
                    exit_code=-1, error="Prohibited command",
                    modified_from=original_command if is_modified and original_command != current_command else None,
                    modification_reason=final_modification_reason if is_modified else None
                )
            elif decision == "USER_DENIED":
                logger.warning(f"Command '{current_command}' execution denied by user.")
                return ShellCommandOutput(
                    command=current_command, stdout="", stderr="Command execution denied by user.",
                    exit_code=-1, error="Denied by user",
                    modified_from=original_command if is_modified and original_command != current_command else None,
                    modification_reason=final_modification_reason if is_modified else None
                )
            elif decision == "USER_CANCELLED":
                logger.warning(f"Command '{current_command}' execution cancelled by user.")
                return ShellCommandOutput(
                    command=current_command, stdout="", stderr="Command execution cancelled by user.",
                    exit_code=-1, error="Cancelled by user",
                    modified_from=original_command if is_modified and original_command != current_command else None,
                    modification_reason=final_modification_reason if is_modified else None
                )
            else: # Should not happen
                logger.error(f"Unexpected approval decision '{decision}' for command '{current_command}'. Denying.")
                return ShellCommandOutput(
                    command=current_command, stdout="", stderr=f"Unexpected approval status: {decision}.",
                    exit_code=-1, error="Internal approval error",
                    modified_from=original_command if is_modified and original_command != current_command else None,
                    modification_reason=final_modification_reason if is_modified else None
                )

        # If loop exited for execution
        if executed_command is None: # Should not happen if logic is correct
             logger.error("Execution block reached without a command to execute. This is a bug.")
             return ShellCommandOutput(
                command=original_command, stdout="", stderr="Internal error: No command identified for execution.",
                exit_code=-1, error="Internal logic error"
             )

        exec_result_dict = self._execute_subprocess(executed_command)

        output_error = None
        if exec_result_dict.get("error_type"):
            output_error = exec_result_dict["error_type"]
        elif exec_result_dict["returncode"] != 0 and exec_result_dict["stderr"]:
             # If there's stderr and non-zero exit, consider it an error at command level
            output_error = f"Command failed with exit code {exec_result_dict['returncode']}"


        return ShellCommandOutput(
            command=executed_command,
            stdout=exec_result_dict["stdout"],
            stderr=exec_result_dict["stderr"],
            exit_code=exec_result_dict["returncode"],
            error=output_error,
            modified_from=original_command if is_modified and original_command != executed_command else None,
            modification_reason=final_modification_reason if is_modified else None
        )


if __name__ == "__main__":
    # Setup for testing
    # This requires user interaction for some tests.
    # For non-interactive tests, you might need to mock ApprovalManager or pre-set its state.
    
    # Basic console for ApprovalManager
    test_console = RichConsole()
    approval_manager_instance = ApprovalManager(console=test_console)
    shell_tool = ExecuteShellTool(approval_manager=approval_manager_instance)

    test_console.rule("[bold bright_blue]Testing ExecuteShellTool[/]")

    def run_test_command(command_str: str, description: str):
        test_console.print(f"\n[bold]Test Case:[/] {description}")
        test_console.print(f"[cyan]Attempting command:[/] '{command_str}'")
        tool_input = ShellCommandInput(command=command_str)
        result = shell_tool.run(tool_input)
        test_console.print(f"[bold yellow]Command Executed:[/] {result.command}")
        test_console.print(f"[bold green]Stdout:[/] {result.stdout if result.stdout else '<empty>'}")
        test_console.print(f"[bold red]Stderr:[/] {result.stderr if result.stderr else '<empty>'}")
        test_console.print(f"[bold magenta]Exit Code:[/] {result.exit_code}")
        if result.error:
            test_console.print(f"[bold red]Tool Error:[/] {result.error}")
        if result.modified_from:
            test_console.print(f"[bold cyan]Modified From:[/] {result.modified_from}")
        if result.modification_reason:
            test_console.print(f"[bold cyan]Modification Reason:[/] {result.modification_reason}")
        test_console.print("-" * 30)

    # --- Test Scenarios ---
    # Note: Some of these will require specific user input during the test run.

    # 1. Prohibited command (e.g., "sudo reboot" if "sudo *" is in DEFAULT_PROHIBITED_COMMANDS)
    run_test_command("sudo reboot", "Prohibited Command (sudo reboot)")
    
    # 2. Auto-approved command (e.g., "ls -la" if "ls *" is in DEFAULT_APPROVED_COMMANDS)
    run_test_command("ls -la", "Auto-Approved Command (ls -la)")
    run_test_command("echo 'Hello from QX test'", "Auto-Approved Command (echo)")


    # 3. Command requiring user approval - User approves (e.g., "date")
    #    (Assuming "date" is not in DEFAULT_APPROVED_COMMANDS or DEFAULT_PROHIBITED_COMMANDS)
    #    INPUT: y
    run_test_command("date", "User Approves 'date'")

    # 4. Command requiring user approval - User denies
    #    INPUT: n
    run_test_command("whoami", "User Denies 'whoami'")

    # 5. Command requiring user approval - User cancels
    #    INPUT: c
    run_test_command("df -h", "User Cancels 'df -h'")
    
    # 6. Command requiring user approval - User modifies, then new command is approved
    #    INPUT for 'sleep 1': m
    #    INPUT for modified command: echo "modified sleep"
    #    INPUT for reason: "testing modification"
    #    INPUT for 'echo "modified sleep"': y
    run_test_command("sleep 1", "User Modifies 'sleep 1' to 'echo \"modified sleep\"', then approves")

    # 7. Command requiring user approval - User modifies to a prohibited command
    #    INPUT for 'pwd': m
    #    INPUT for modified command: rm -rf /
    #    INPUT for reason: "testing modification to prohibited"
    #    (Should be caught as prohibited without further prompt for y/n)
    run_test_command("pwd", "User Modifies 'pwd' to 'rm -rf /' (prohibited)")

    # 8. Command that times out
    #    (Requires SHELL_COMMAND_TIMEOUT to be low for quick testing, e.g., 1-2s)
    #    INPUT for `sleep 5` (if timeout is 2s): y
    #    Make sure SHELL_COMMAND_TIMEOUT is set appropriately in constants.py for this test
    #    Or, approval_manager_instance.default_approve_all_duration_minutes = 0.1 # to make it expire fast
    #    approval_manager_instance._approve_all_until = datetime.datetime.now() + datetime.timedelta(seconds=1) # Temp approve for test
    #    run_test_command(f"sleep {SHELL_COMMAND_TIMEOUT + 3}", f"Command Times Out (sleep {SHELL_COMMAND_TIMEOUT + 3})")
    #    This test is harder to automate without mocking time or approval.
    #    For manual test: set SHELL_COMMAND_TIMEOUT=2 in constants.py, then run this test with 'y'
    test_console.print(f"\n[bold]Note:[/] Timeout test for 'sleep {SHELL_COMMAND_TIMEOUT + 3}' might require manual approval (y) "
                       f"and SHELL_COMMAND_TIMEOUT to be set low (e.g. 2s). Current timeout: {SHELL_COMMAND_TIMEOUT}s.")


    # 9. Command not found
    #    INPUT: y
    run_test_command("thiscommandshouldnotexist123", "Command Not Found")

    # 10. Command with non-zero exit code and stderr
    #     INPUT: y
    run_test_command("ls /nonexistentpath", "Command with stderr and non-zero exit")
    
    # 11. "Approve All" functionality test
    #     INPUT for 'git status': a
    #     INPUT for duration: 1 (minute)
    #     Then, the next command should be SESSION_APPROVED.
    run_test_command("git status", "Activate 'Approve All' with 'git status'")
    run_test_command("cat pyproject.toml", "Test 'Approve All' with 'cat pyproject.toml' (should be session approved or auto-approved if cat * is default)")

    test_console.print("\n[bold bright_blue]Finished ExecuteShellTool Tests[/]")