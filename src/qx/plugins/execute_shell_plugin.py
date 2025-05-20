import logging
import subprocess
import fnmatch # For command pattern matching
from pathlib import Path
from typing import Optional, List

from pydantic import BaseModel, Field
from pydantic_ai import RunContext

from qx.core.context import QXToolDependencies
from qx.core.user_prompts import request_confirmation
# _find_project_root might be needed if some shell commands' safety depends on CWD relative to project
# from qx.core.paths import _find_project_root 

logger = logging.getLogger(__name__)

# --- Default command patterns (adapted from qx.core.constants) ---
# These could be loaded from a config file or be part of QXToolDependencies if dynamic
DEFAULT_PROHIBITED_SHELL_PATTERNS: List[str] = [
    "sudo *", "rm -rf /", "rm -rf ~/*", "rm -rf /*", "mkfs*", "fdisk*", 
    "dd *", "shutdown*", "reboot*", "halt*", "poweroff*", 
    "chmod -R 000 *", "chown -R root *", 
    # Network-related commands that might be risky or bypass fetch tool
    # "curl *", "wget *", "ping *", "ssh *", "scp *", "ftp *", "telnet *",
    # "nc *", "netcat *",
    # Potentially dangerous development tools if misused
    "docker run *--privileged*", "kubectl delete *",
    # Alias manipulation that could be persistent
    "alias rm*",
]
DEFAULT_AUTO_APPROVED_SHELL_PATTERNS: List[str] = [
    "ls*", "pwd", "git status", "git diff*", "git log*", "git show*",
    "cloc*", "cat*", "head*", "tail*", "grep*", "find .*", # find restricted to current dir
    "echo*", "printf*", "true", "false", "which*", "type*",
    "uv --version", "python --version", "node --version", "npm --version", # Common version checks
    "pytest*", "make test", # Common testing commands
]
# --- End of command patterns ---

class ExecuteShellPluginInput(BaseModel):
    """Input model for the ExecuteShellPluginTool."""
    command: str = Field(..., description="The shell command to execute.")

class ExecuteShellPluginOutput(BaseModel):
    """Output model for the ExecuteShellPluginTool."""
    command: str = Field(description="The command that was attempted (possibly modified).")
    stdout: Optional[str] = Field(None, description="Standard output.")
    stderr: Optional[str] = Field(None, description="Standard error.")
    return_code: Optional[int] = Field(None, description="Return code.")
    error: Optional[str] = Field(None, description="Error message if denied or failed.")

def _is_command_prohibited(command: str) -> bool:
    for pattern in DEFAULT_PROHIBITED_SHELL_PATTERNS:
        if fnmatch.fnmatch(command, pattern):
            logger.warning(f"Command '{command}' matches prohibited pattern '{pattern}'.")
            return True
    return False

def _is_command_auto_approved(command: str) -> bool:
    for pattern in DEFAULT_AUTO_APPROVED_SHELL_PATTERNS:
        if fnmatch.fnmatch(command, pattern):
            logger.info(f"Command '{command}' matches auto-approved pattern '{pattern}'.")
            return True
    return False

def execute_shell_tool(
    ctx: RunContext[QXToolDependencies],
    args: ExecuteShellPluginInput
) -> ExecuteShellPluginOutput:
    """
    PydanticAI Tool to execute a shell command.
    Prohibited commands are blocked. Some safe commands are auto-approved.
    Most other commands require user confirmation and allow modification.
    """
    console = ctx.deps.console
    command_to_consider = args.command.strip()

    if not command_to_consider:
        return ExecuteShellPluginOutput(command="", error="Error: Empty command provided.")

    if _is_command_prohibited(command_to_consider):
        err_msg = f"Error: Command '{command_to_consider}' is prohibited by policy."
        logger.error(err_msg)
        return ExecuteShellPluginOutput(command=command_to_consider, error=err_msg)

    command_to_execute = command_to_consider
    needs_confirmation = not _is_command_auto_approved(command_to_consider)

    if needs_confirmation:
        prompt_msg = f"Allow QX to execute shell command: '{command_to_consider}'?"
        decision_status, final_value = request_confirmation(
            prompt_message=prompt_msg,
            console=console,
            allow_modify=True,
            current_value_for_modification=command_to_consider
        )

        if decision_status == "modified" and final_value is not None:
            command_to_execute = final_value.strip()
            if not command_to_execute: # User modified to empty string
                 return ExecuteShellPluginOutput(command=command_to_consider, error="Error: Command modified to an empty string.")
            logger.info(f"Shell command modified by user from '{command_to_consider}' to '{command_to_execute}'.")
            # Re-check if the modified command is prohibited
            if _is_command_prohibited(command_to_execute):
                err_msg = f"Error: Modified command '{command_to_execute}' is prohibited by policy."
                logger.error(err_msg)
                return ExecuteShellPluginOutput(command=command_to_execute, error=err_msg)
        elif decision_status == "approved":
            command_to_execute = command_to_consider # Already set, but for clarity
        else: # denied or cancelled
            error_message = f"Shell command execution for '{command_to_consider}' was {decision_status} by user."
            logger.warning(error_message)
            return ExecuteShellPluginOutput(command=command_to_consider, error=error_message)
    else: # Auto-approved
        logger.info(f"Command '{command_to_execute}' is auto-approved. Executing.")
        console.print(f"[success]AUTO-APPROVED (PATTERN):[/] Executing shell command [info]'{command_to_execute}'[/]")


    try:
        # Note: Consider CWD implications. For now, commands run in QX's current CWD.
        # project_root = _find_project_root(str(Path.cwd())) # If needed for context-aware execution
        process = subprocess.run(
            command_to_execute,
            shell=True, # Be cautious with shell=True. Ensure commands are vetted.
            capture_output=True,
            text=True,
            check=False, # We handle return_code manually
        )
        logger.info(f"Command '{command_to_execute}' executed. Return code: {process.returncode}")
        
        stdout = process.stdout.strip() if process.stdout else None
        stderr = process.stderr.strip() if process.stderr else None
        
        # Construct a more informative output message, especially if there's an error or non-zero exit
        if process.return_code != 0:
            msg = (
                f"Command '{command_to_execute}' executed with exit code {process.return_code}.\n"
                f"Stdout: {stdout or '<empty>'}\n"
                f"Stderr: {stderr or '<empty>'}"
            )
            # The LLM might interpret any non-empty string as success.
            # Prepending "Error:" or "Warning:" might be useful for non-zero exits.
            # For now, let's return the raw output and let the LLM decide.
            return ExecuteShellPluginOutput(
                command=command_to_execute,
                stdout=stdout,
                stderr=stderr,
                return_code=process.returncode
            )

        return ExecuteShellPluginOutput(
            command=command_to_execute,
            stdout=stdout,
            stderr=stderr, # Stderr can have content even on success (e.g., warnings)
            return_code=process.returncode,
        )
    except Exception as e:
        logger.error(f"Failed to execute command '{command_to_execute}': {e}", exc_info=True)
        return ExecuteShellPluginOutput(
            command=command_to_execute, error=f"Error: Failed to execute command: {e}"
        )

if __name__ == "__main__":
    import time
    from rich.console import Console as RichConsole
    
    logging.basicConfig(level=logging.INFO)
    test_console = RichConsole()

    test_deps = QXToolDependencies(console=test_console)
    class DummyRunContext(RunContext[QXToolDependencies]):
        def __init__(self, deps: QXToolDependencies):
            super().__init__(deps=deps, usage=None) # type: ignore
    dummy_ctx = DummyRunContext(deps=test_deps)

    test_console.rule("Testing execute_shell_tool plugin with RunContext")

    # Test 1: Auto-approved command
    test_console.print("\n[bold]Test 1: Auto-approved command (ls)[/]")
    input1 = ExecuteShellPluginInput(command="ls -l")
    output1 = execute_shell_tool(dummy_ctx, input1)
    test_console.print(f"Output 1: {output1.stdout[:100]}..." if output1.stdout else output1)
    assert output1.return_code == 0 and output1.error is None

    # Test 2: Prohibited command
    test_console.print("\n[bold]Test 2: Prohibited command (sudo reboot)[/]")
    input2 = ExecuteShellPluginInput(command="sudo reboot")
    output2 = execute_shell_tool(dummy_ctx, input2)
    test_console.print(f"Output 2: {output2}")
    assert output2.error is not None and "prohibited" in output2.error

    # Test 3: Command requiring confirmation (user approves)
    test_console.print("\n[bold]Test 3: Needs confirmation (echo 'hello') - user approves[/]")
    input3 = ExecuteShellPluginInput(command="echo 'Hello QX Shell'")
    test_console.print("Please respond 'y' to the prompt.")
    output3 = execute_shell_tool(dummy_ctx, input3)
    test_console.print(f"Output 3: {output3}")
    assert output3.stdout == "Hello QX Shell" and output3.return_code == 0

    # Test 4: Command requiring confirmation (user denies)
    test_console.print("\n[bold]Test 4: Needs confirmation (date) - user denies[/]")
    input4 = ExecuteShellPluginInput(command="date")
    test_console.print("Please respond 'n' to the prompt.")
    output4 = execute_shell_tool(dummy_ctx, input4)
    test_console.print(f"Output 4: {output4}")
    assert output4.error is not None and "denied by user" in output4.error

    # Test 5: Command requiring confirmation (user modifies)
    original_cmd = "whoami_original"
    modified_cmd = "whoami"
    test_console.print(f"\n[bold]Test 5: Needs confirmation ('{original_cmd}') - user modifies to '{modified_cmd}'[/]")
    input5 = ExecuteShellPluginInput(command=original_cmd)
    test_console.print(f"Please respond 'm', then enter '{modified_cmd}'.")
    output5 = execute_shell_tool(dummy_ctx, input5)
    test_console.print(f"Output 5: {output5}")
    assert output5.command == modified_cmd and output5.return_code == 0 and output5.stdout # stdout should exist

    # Test 6: Command fails (non-zero exit code)
    test_console.print("\n[bold]Test 6: Command fails (ls non_existent_file)[/]")
    input6 = ExecuteShellPluginInput(command="ls __non_existent_file_for_qx_test__")
    # This is auto-approved by "ls*", so no prompt
    output6 = execute_shell_tool(dummy_ctx, input6)
    test_console.print(f"Output 6: {output6}")
    assert output6.return_code != 0 and output6.error is None # Error field is for pre-exec errors
    assert output6.stderr is not None

    test_console.print("\nExecute_shell_plugin tests finished.")