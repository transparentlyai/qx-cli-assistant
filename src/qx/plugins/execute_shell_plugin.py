import fnmatch  # For command pattern matching
import logging
import subprocess
from typing import List, Optional

from pydantic import BaseModel, Field
from rich.console import Console as RichConsole  # Import RichConsole directly

# Removed: from qx.core.user_prompts import request_confirmation

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
    command: str = Field(description="The command that was executed.")
    stdout: Optional[str] = Field(
        None,
        description="Standard output from the command. Only present if command was executed.",
    )
    stderr: Optional[str] = Field(
        None,
        description="Standard error from the command. Only present if command was executed.",
    )
    return_code: Optional[int] = Field(
        None,
        description="Exit code from command execution. 0 indicates success, non-zero indicates failure. None if command was not executed.",
    )
    error: Optional[str] = Field(
        None,
        description="Error message explaining why command was not executed (e.g., 'prohibited', 'denied by user', 'empty command'). None if command was executed.",
    )


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


async def execute_shell_tool(
    console: RichConsole, args: ExecuteShellPluginInput
) -> ExecuteShellPluginOutput:
    """Tool for executing shell commands.

    Executes non-interactive shell commands. Approval is handled by the terminal layer.
    - Prohibited commands are blocked.
    - Auto-approved patterns are logged as such.

    Returns structured output with:
    - command: The actual command executed
    - stdout/stderr: Command output (only if executed)
    - return_code: Exit code (0=success, only if executed)
    - error: Explanation if command was not executed
    """
    command_to_execute = args.command.strip()

    if not command_to_execute:
        err_msg = "Error: Empty command provided."
        logger.error(err_msg)
        console.print(f"[error]{err_msg}[/]")
        return ExecuteShellPluginOutput(
            command="", stdout=None, stderr=None, return_code=None, error=err_msg
        )

    if _is_command_prohibited(command_to_execute):
        err_msg = f"Error: Command '{command_to_execute}' is prohibited by policy."
        logger.error(err_msg)
        console.print(f"[error]Command prohibited by policy:[/] '{command_to_execute}'")
        return ExecuteShellPluginOutput(
            command=command_to_execute,
            stdout=None,
            stderr=None,
            return_code=None,
            error=err_msg,
        )

    # Approval is now assumed to be handled by the terminal layer.
    # We still check for auto-approved patterns for logging/messaging.
    is_auto_approved = _is_command_auto_approved(command_to_execute)

    if is_auto_approved:
        logger.debug(
            f"Command '{command_to_execute}' matches an auto-approved pattern. Executing."
        )
        console.print(
            f"[success]AUTO-APPROVED (PATTERN):[/] Executing: [info]'{command_to_execute}'[/]"
        )
    else:
        logger.debug(
            f"Command '{command_to_execute}' requires approval (handled by terminal). Executing."
        )
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
            if (
                not is_auto_approved
            ):  # Only print success if not already covered by auto-approve message
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
                error=None,  # Error is for non-execution, stderr for command errors
            )

    except Exception as e:
        logger.error(
            f"Failed to execute command '{command_to_execute}': {e}", exc_info=True
        )
        err_msg = f"Error: Failed to execute command '{command_to_execute}': {e}"
        console.print(
            f"[error]Failed to execute command '{command_to_execute}':[/] {e}"
        )
        return ExecuteShellPluginOutput(
            command=command_to_execute,
            stdout=None,
            stderr=None,
            return_code=None,
            error=err_msg,
        )
