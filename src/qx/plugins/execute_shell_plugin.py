import fnmatch  # For command pattern matching
import logging
import subprocess
from typing import List, Optional

from pydantic import BaseModel, Field
from rich.console import Console as RichConsole # Import RichConsole directly

from qx.core.user_prompts import request_confirmation

logger = logging.getLogger(__name__)

# --- Default command patterns (adapted from qx.core.constants) ---
DEFAULT_PROHIBITED_SHELL_PATTERNS: List[str] = [
    "sudo *",
    "su *",
    "chmod 777 *",
    "chmod -R 777 *",
    "rm -rf /*",
    "dd if=/dev/zero of=/dev/*",
    "> /dev/sda",
    "mkfs.*",
    ":(){:|:&};:",
    "mv /* /dev/null",
    "wget * | bash",
    "curl * | bash",
    "wget * | sh",
    "curl * | sh",
    "*(){ :;};*",
    "echo * > /etc/passwd",
    "echo * > /etc/shadow",
    "rm -rf ~",
    "rm -rf .",
    "find / -delete",
    "find . -delete",
    "shred * /dev/*",
    "wipe /dev/*",
    "fdisk /dev/*",
    "parted /dev/*",
    "gparted /dev/*",
    "userdel root",
    "groupdel root",
    "passwd -d root",
    "passwd -l root",
    "chown root* /*",
    "chown -R * /*",
    "chattr -i *",
    "chattr +i /*",
    "reboot",
    "shutdown *",
    "halt",
    "poweroff",
    "init 0",
    "init 6",
    "iptables -F",
    "iptables -X",
    "iptables -P INPUT DROP",
    "iptables -P FORWARD DROP",
    "iptables -P OUTPUT DROP",
    "ufw disable",
    "systemctl stop firewalld",
    "systemctl disable firewalld",
    "insmod *",
    "rmmod *",
    "modprobe *",
    "sysctl *",
    "echo * > /proc/sys/*",
    "* | base64 -d | bash",
    "* | base64 -d | sh",
    "history -c",
    "echo > ~/.bash_history",
    "kill -9 1",
    "pkill init",
    "mount -o remount,ro /",
    "mount /dev/sd* /mnt; rm -rf /mnt/*",
]
DEFAULT_AUTO_APPROVED_SHELL_PATTERNS: List[str] = [
    "ls",
    "ls *",
    "cd",
    "cd *",
    "pwd",
    "echo",
    "echo *",
    "cat",
    "cat *",
    "head",
    "head *",
    "tail",
    "tail *",
    "grep",
    "grep *",
    "find",
    "find *",
    "mkdir",
    "mkdir *",
    "touch",
    "touch *",
    "cp",
    "cp *",
    "mv",
    "mv *",
    "python --version",
    "python -m *",
    "python3 --version",
    "python3 -m *",
    "pip list",
    "pip show *",
    "pip freeze",
    "uv list",
    "uv pip list",
    "uv pip show *",
    "uv pip freeze",
    "cloc",
    "cloc *",
    "git",
    "git *",
    "date",
    "cal",
    "uptime",
    "whoami",
    "id",
    "uname",
    "uname *",
    "df",
    "df *",
    "du",
    "du *",
    "wc",
    "wc *",
    "less",
    "less *",
    "more",
    "more *",
    "diff",
    "diff *",
    "comm",
    "comm *",
    "sort",
    "sort *",
    "uniq",
    "uniq *",
    "ps",
    "ps *",
    "top",
    "env",
    "printenv",
    "printenv *",
    "export -p",
    "man",
    "man *",
    "info",
    "info *",
    "tldr",
    "tldr *",
    "* --help",
    "stat",
    "stat *",
    "which",
    "which *",
    "whereis",
    "whereis *",
    "type",
    "type *",
    "history",
    "clear",
    "ping",
    "ping *",
    "ip",
    "ip *",
    "ifconfig",
    "ifconfig *",
    "netstat",
    "netstat *",
    "ss",
    "ss *",
    "host",
    "host *",
    "dig",
    "dig *",
    "nslookup",
    "nslookup *",
    "tar -tvf *",
    "zipinfo *",
    "unzip -l *",
    "gzip -l *",
    "gunzip -l *",
    "zcat *",
    "bzcat *",
    "xzcat *",
    "basename *",
    "dirname *",
    "readlink *",
    "test *",
    "[ * ]",
    "alias",
    "jobs",
    "file",
    "file *",
]
# --- End of command patterns ---


class ExecuteShellPluginInput(BaseModel):
    command: str = Field(..., description="The shell command to execute.")


class ExecuteShellPluginOutput(BaseModel):
    command: str = Field(
        description="The command that was attempted (possibly modified)."
    )
    stdout: Optional[str] = Field(None, description="Standard output.")
    stderr: Optional[str] = Field(None, description="Standard error.")
    return_code: Optional[int] = Field(None, description="Return code.")
    error: Optional[str] = Field(None, description="Error message if denied or failed.")


def _is_command_prohibited(command: str) -> bool:
    for pattern in DEFAULT_PROHIBITED_SHELL_PATTERNS:
        if fnmatch.fnmatch(command, pattern):
            logger.warning(
                f"Command '{command}' matches prohibited pattern '{pattern}'."
            )
            return True
    return False


def _is_command_auto_approved(command: str) -> bool:
    for pattern in DEFAULT_AUTO_APPROVED_SHELL_PATTERNS:
        if fnmatch.fnmatch(command, pattern):
            logger.info(
                f"Command '{command}' matches auto-approved pattern '{pattern}'."
            )
            return True
    return False


async def execute_shell_tool( # Made async
    console: RichConsole, args: ExecuteShellPluginInput
) -> ExecuteShellPluginOutput:
    """Tool for executing shell commands."""
    # console is now directly available, no need for ctx.deps.console

    command_to_consider = args.command.strip()

    if not command_to_consider:
        err_msg = "Error: Empty command provided."
        logger.error(err_msg)
        console.print(f"[error]{err_msg}[/error]")
        return ExecuteShellPluginOutput(
            command="", stdout=None, stderr=None, return_code=None, error=err_msg
        )

    if _is_command_prohibited(command_to_consider):
        err_msg = f"Error: Command '{command_to_consider}' is prohibited by policy."
        logger.error(err_msg)
        console.print(
            f"[error]Command prohibited by policy:[/error] '{command_to_consider}'"
        )
        return ExecuteShellPluginOutput(
            command=command_to_consider,
            stdout=None,
            stderr=None,
            return_code=None,
            error=err_msg,
        )

    command_to_execute = command_to_consider
    needs_confirmation = not _is_command_auto_approved(command_to_consider)

    # Initialize decision_status and final_value to safe defaults
    decision_status = (
        "approved" if not needs_confirmation else "pending"
    )  # "pending" is a placeholder, will be overwritten
    final_value = command_to_consider

    if needs_confirmation:
        prompt_msg = f"Allow QX to execute shell command: '{command_to_consider}'?"
        decision_status, final_value = await request_confirmation( # Await
            prompt_message=prompt_msg,
            console=console,
            allow_modify=True,
            current_value_for_modification=command_to_consider,
        )

        if decision_status == "modified" and final_value is not None:
            command_to_execute = final_value.strip()
            if not command_to_execute:
                err_msg = "Error: Command modified to an empty string."
                logger.warning(
                    f"Original command '{command_to_consider}' modified to empty."
                )
                console.print(
                    f"[error]{err_msg}[/error] Original: '{command_to_consider}'"
                )
                return ExecuteShellPluginOutput(
                    command=command_to_consider,
                    stdout=None,
                    stderr=None,
                    return_code=None,
                    error=err_msg,
                )

            logger.info(
                f"Shell command modified by user from '{command_to_consider}' to '{command_to_execute}'."
            )
            # console.print(f"[info]Command modified by user to:[/info] '{command_to_execute}'") # Covered by request_confirmation

            if _is_command_prohibited(command_to_execute):
                err_msg = f"Error: Modified command '{command_to_execute}' is prohibited by policy."
                logger.error(err_msg)
                console.print(
                    f"[error]Modified command prohibited by policy:[/error] '{command_to_execute}'"
                )
                return ExecuteShellPluginOutput(
                    command=command_to_execute,
                    stdout=None,
                    stderr=None,
                    return_code=None,
                    error=err_msg,
                )

        elif decision_status in ["approved", "session_approved"]:
            command_to_execute = command_to_consider
        else:  # denied or cancelled
            error_message = f"Shell command execution for '{command_to_consider}' was {decision_status} by user."
            logger.warning(error_message)
            # request_confirmation already prints user decision (denied/cancelled)
            return ExecuteShellPluginOutput(
                command=command_to_consider,
                stdout=None,
                stderr=None,
                return_code=None,
                error=error_message,
            )
    else:  # Auto-approved
        logger.info(f"Command '{command_to_execute}' is auto-approved. Executing.")
        console.print(
            f"[success]AUTO-APPROVED (PATTERN):[/] Executing: [info]'{command_to_execute}'[/]"
        )

    # If we reach here, command is approved (or auto-approved or session_approved) and not prohibited
    # Message printing for execution start:
    if not needs_confirmation:  # Auto-approved (already printed)
        pass
    elif (
        decision_status == "session_approved"
    ):  # Session approved (already printed by request_confirmation)
        pass
    elif command_to_execute != command_to_consider:  # Manually modified and approved
        console.print(
            f"[info]Executing modified command:[/info] '{command_to_execute}'"
        )
    else:  # Manually approved without modification
        console.print(f"[info]Executing command:[/info] '{command_to_execute}'")

    try:
        process = subprocess.run(
            command_to_execute, shell=True, capture_output=True, text=True, check=False
        )
        logger.info(
            f"Command '{command_to_execute}' executed. Return code: {process.returncode}"
        )

        stdout = process.stdout.strip() if process.stdout else None
        stderr = process.stderr.strip() if process.stderr else None

        if process.returncode == 0:
            # Avoid double printing success if already handled by session_approved or auto_approved messages
            if not (decision_status == "session_approved" or not needs_confirmation):
                console.print(
                    f"[success]Command executed successfully:[/success] '{command_to_execute}'"
                )
            return ExecuteShellPluginOutput(
                command=command_to_execute,
                stdout=stdout,
                stderr=stderr,
                return_code=process.returncode,
                error=None,
            )
        else:
            console.print(
                f"[warning]Command '{command_to_execute}' finished with return code {process.returncode}.[/warning]"
            )
            return ExecuteShellPluginOutput(
                command=command_to_execute,
                stdout=stdout,
                stderr=stderr,
                return_code=process.returncode,
                error=None,
            )

    except Exception as e:
        logger.error(
            f"Failed to execute command '{command_to_execute}': {e}", exc_info=True
        )
        err_msg = f"Error: Failed to execute command '{command_to_execute}': {e}"
        console.print(
            f"[error]Failed to execute command '{command_to_execute}':[/error] {e}"
        )
        return ExecuteShellPluginOutput(
            command=command_to_execute,
            stdout=None,
            stderr=None,
            return_code=None,
            error=err_msg,
        )


if __name__ == "__main__":
    import asyncio
    from rich.console import Console as RichConsole

    logging.basicConfig(level=logging.INFO)
    test_console = RichConsole()

    async def run_tests():
        test_console.rule("Testing execute_shell_tool plugin with direct console passing")

        # Test 1: Auto-approved command
        test_console.print(
            "\n[bold cyan]Test 1: Auto-approved command (echo 'auto hello')[/bold cyan]"
        )
        input1 = ExecuteShellPluginInput(
            command="echo 'auto hello'"
        )  # Using echo for predictable output
        output1 = await execute_shell_tool(test_console, input1) # Updated call
        test_console.print(f"Output 1 STDOUT: {output1.stdout}")
        assert (
            output1.stdout == "auto hello"
            and output1.return_code == 0
            and output1.error is None
        )

        # Test 2: Prohibited command
        test_console.print(
            "\n[bold cyan]Test 2: Prohibited command (sudo reboot)[/bold cyan]"
        )
        input2 = ExecuteShellPluginInput(command="sudo reboot")
        output2 = await execute_shell_tool(test_console, input2) # Updated call
        test_console.print(f"Output 2: {output2}")
        assert output2.error is not None and "prohibited by policy" in output2.error
        assert (
            output2.stdout is None
            and output2.stderr is None
            and output2.return_code is None
        )

        # Test 3: Command requiring confirmation (user approves)
        test_console.print(
            "\n[bold cyan]Test 3: Needs confirmation (echo 'Hello QX Shell') - user approves[/bold cyan]"
        )
        input3 = ExecuteShellPluginInput(command="echo 'Hello QX Shell'")
        test_console.print("Please respond 'y' to the prompt.")
        output3 = await execute_shell_tool(test_console, input3) # Updated call
        test_console.print(f"Output 3 STDOUT: {output3.stdout}")
        assert (
            output3.stdout == "Hello QX Shell"
            and output3.return_code == 0
            and output3.error is None
        )

        # Test 4: Command requiring confirmation (user denies)
        # `request_confirmation` handles console output for denial
        test_console.print(
            "\n[bold cyan]Test 4: Needs confirmation (echo 'wont run') - user denies[/bold cyan]"
        )
        input4 = ExecuteShellPluginInput(command="echo 'wont run'")
        test_console.print("Please respond 'n' to the prompt.")
        output4 = await execute_shell_tool(test_console, input4) # Updated call
        test_console.print(f"Output 4: {output4}")
        assert output4.error is not None and "denied by user" in output4.error
        assert (
            output4.stdout is None
            and output4.stderr is None
            and output4.return_code is None
        )

        # Test 5: Command requiring confirmation (user modifies to an allowed command)
        original_cmd = "echo 'original command'"
        modified_cmd = "echo 'modified command'"
        test_console.print(
            f"\n[bold cyan]Test 5: Needs confirmation ('{original_cmd}') - user modifies to '{modified_cmd}'[/bold cyan]"
        )
        input5 = ExecuteShellPluginInput(command=original_cmd)
        test_console.print(
            f"Please respond 'm', then enter '{modified_cmd}', then 'y' if asked to confirm modified."
        )
        output5 = await execute_shell_tool(test_console, input5) # Updated call
        test_console.print(f"Output 5 STDOUT: {output5.stdout}")
        assert output5.command == modified_cmd and output5.stdout == "modified command"
        assert output5.return_code == 0 and output5.error is None

        # Test 6: Command fails (non-zero exit code)
        failing_cmd = "ls __non_existent_file_for_qx_test__"
        test_console.print(
            f"\n[bold cyan]Test 6: Command fails ({failing_cmd})[/bold cyan]"
        )
        input6 = ExecuteShellPluginInput(command=failing_cmd)
        # This command is not auto-approved, so it will require confirmation
        test_console.print("Please respond 'y' to the prompt for the failing command.")
        output6 = await execute_shell_tool(test_console, input6) # Updated call
        test_console.print(f"Output 6: {output6}")
        assert output6.command == failing_cmd and output6.return_code != 0
        assert output6.stderr is not None  # ls to non-existent usually outputs to stderr
        assert output6.error is None  # Not a pre-execution error

        # Test 7: Command modified to empty string
        test_console.print(
            "\n[bold cyan]Test 7: Command modified to empty string[/bold cyan]"
        )
        input7 = ExecuteShellPluginInput(command="echo 'this will be modified to empty'")
        test_console.print(
            "Please respond 'm', then enter an empty string (just press Enter)."
        )
        output7 = await execute_shell_tool(test_console, input7) # Updated call
        test_console.print(f"Output 7: {output7}")
        assert output7.error == "Error: Command modified to an empty string."
        assert (
            output7.command == "echo 'this will be modified to empty'"
        )  # Original command reported

        # Test 8: Command modified to a prohibited command
        test_console.print(
            "\n[bold cyan]Test 8: Command modified to a prohibited command (sudo false)[/bold cyan]"
        )
        input8 = ExecuteShellPluginInput(
            command="echo 'this will be modified to sudo false'"
        )
        test_console.print("Please respond 'm', then enter 'sudo false'.")
        output8 = await execute_shell_tool(test_console, input8) # Updated call
        test_console.print(f"Output 8: {output8}")
        assert (
            output8.error == "Error: Modified command 'sudo false' is prohibited by policy."
        )
        assert output8.command == "sudo false"

        test_console.print("\n[bold cyan]Test 9: Empty command string input[/bold cyan]")
        input9 = ExecuteShellPluginInput(command="  ")  # Whitespace only
        output9 = await execute_shell_tool(test_console, input9) # Updated call
        test_console.print(f"Output 9: {output9}")
        assert output9.error == "Error: Empty command provided."
        assert output9.command == ""

        test_console.rule("Execute_shell_plugin tests finished.")

    asyncio.run(run_tests())