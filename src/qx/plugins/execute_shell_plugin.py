import fnmatch  # For command pattern matching
import logging
import subprocess
from typing import List, Optional

from pydantic import BaseModel, Field
from rich.console import Console as RichConsole  # Import RichConsole directly

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
    command: str = Field(
        ..., description="The shell command to execute. Non-interactive commands only."
    )


class ExecuteShellPluginOutput(BaseModel):
    command: str = Field(
        description="The command that was actually executed (may differ from requested if user modified during approval)."
    )
    stdout: Optional[str] = Field(None, description="Standard output from the command. Only present if command was executed.")
    stderr: Optional[str] = Field(None, description="Standard error from the command. Only present if command was executed.")
    return_code: Optional[int] = Field(None, description="Exit code from command execution. 0 indicates success, non-zero indicates failure. None if command was not executed.")
    error: Optional[str] = Field(None, description="Error message explaining why command was not executed (e.g., 'prohibited', 'denied by user', 'empty command'). None if command was executed.")


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
            logger.debug(
                f"Command '{command}' matches auto-approved pattern '{pattern}'."
            )
            return True
    return False


async def execute_shell_tool(  # Made async
    console: RichConsole, args: ExecuteShellPluginInput
) -> ExecuteShellPluginOutput:
    """Tool for executing shell commands.
    
    Executes non-interactive shell commands with user approval flow:
    - Auto-approved commands (ls, pwd, etc.) execute immediately
    - Other commands require user confirmation
    - Users can modify commands during approval
    - Prohibited commands are blocked
    
    Returns structured output with:
    - command: The actual command executed (may differ if user modified)
    - stdout/stderr: Command output (only if executed)
    - return_code: Exit code (0=success, only if executed)
    - error: Explanation if command was not executed
    """
    # console is now directly available, no need for ctx.deps.console

    command_to_consider = args.command.strip()

    if not command_to_consider:
        err_msg = "Error: Empty command provided."
        logger.error(err_msg)
        console.print(f"[red]{err_msg}[/red]")
        return ExecuteShellPluginOutput(
            command="", stdout=None, stderr=None, return_code=None, error=err_msg
        )

    if _is_command_prohibited(command_to_consider):
        err_msg = f"Error: Command '{command_to_consider}' is prohibited by policy."
        logger.error(err_msg)
        console.print(
            f"[red]Command prohibited by policy:[/red] '{command_to_consider}'"
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
        decision_status, final_value = await request_confirmation(  # Await
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
                console.print(f"[red]{err_msg}[/red] Original: '{command_to_consider}'")
                return ExecuteShellPluginOutput(
                    command=command_to_consider,
                    stdout=None,
                    stderr=None,
                    return_code=None,
                    error=err_msg,
                )

            logger.debug(
                f"Shell command modified by user from '{command_to_consider}' to '{command_to_execute}'."
            )
            # console.print(f"[info]Command modified by user to:[/info] '{command_to_execute}'") # Covered by request_confirmation

            if _is_command_prohibited(command_to_execute):
                err_msg = f"Error: Modified command '{command_to_execute}' is prohibited by policy."
                logger.error(err_msg)
                console.print(
                    f"[red]Modified command prohibited by policy:[/red] '{command_to_execute}'"
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
        logger.debug(f"Command '{command_to_execute}' is auto-approved. Executing.")
        console.print(
            f"[green]AUTO-APPROVED (PATTERN):[/green] Executing: [blue]'{command_to_execute}'[/blue]"
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
        logger.debug(
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
            f"[red]Failed to execute command '{command_to_execute}':[/red] {e}"
        )
        return ExecuteShellPluginOutput(
            command=command_to_execute,
            stdout=None,
            stderr=None,
            return_code=None,
            error=err_msg,
        )
