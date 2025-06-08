import asyncio
import fnmatch
import logging
import subprocess
from typing import List, Optional

from pydantic import BaseModel, Field
from rich.console import Console as RichConsole

from qx.core.approval_handler import ApprovalHandler
from qx.cli.console import themed_console
from qx.core.output_control import should_show_stdout, should_show_stderr


def _managed_plugin_print(content: str, **kwargs) -> None:
    """
    Print helper for plugins that uses console manager when available.
    Falls back to themed_console if manager is unavailable.
    """
    try:
        from qx.core.console_manager import get_console_manager
        manager = get_console_manager()
        if manager and manager._running:
            style = kwargs.get('style')
            markup = kwargs.get('markup', True)
            end = kwargs.get('end', '\n')
            manager.print(content, style=style, markup=markup, end=end, console=themed_console)
            return
    except Exception:
        pass
    
    # Fallback to direct themed_console usage
    themed_console.print(content, **kwargs)

logger = logging.getLogger(__name__)

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


class ExecuteShellPluginInput(BaseModel):
    command: str = Field(..., description="The shell command to execute.")


class ExecuteShellPluginOutput(BaseModel):
    command: str
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    return_code: Optional[int] = None
    error: Optional[str] = None


def _is_command_prohibited(command: str) -> bool:
    return any(
        fnmatch.fnmatch(command, pattern)
        for pattern in DEFAULT_PROHIBITED_SHELL_PATTERNS
    )


def _is_command_auto_approved(command: str) -> bool:
    return any(
        fnmatch.fnmatch(command, pattern)
        for pattern in DEFAULT_AUTO_APPROVED_SHELL_PATTERNS
    )


async def execute_shell_tool(
    console: RichConsole, args: ExecuteShellPluginInput
) -> ExecuteShellPluginOutput:
    approval_handler = ApprovalHandler(themed_console)
    command = args.command.strip()

    if not command:
        err_msg = "Empty command provided."
        _managed_plugin_print(f"Execute Shell Command (Error): {err_msg}")
        return ExecuteShellPluginOutput(command="", error=err_msg)

    if _is_command_prohibited(command):
        err_msg = f"Command '{command}' is prohibited by policy."
        _managed_plugin_print(f"Execute Shell Command (Denied by Policy): {command}")
        approval_handler.print_outcome(
            "Execution", "Failed. Command is prohibited.", success=False
        )
        return ExecuteShellPluginOutput(command=command, error=err_msg)

    status = "approved"
    if _is_command_auto_approved(command):
        _managed_plugin_print(f"Execute Shell Command (Auto-approved): {command}")
    else:
        status, _ = await approval_handler.request_approval(
            operation="Execute Shell Command",
            parameter_name="command",
            parameter_value=command,
            prompt_message=f"Allow [primary]Qx[/] to execute command: [highlight]'{command}'[/]?",
        )

    if status not in ["approved", "session_approved"]:
        err_msg = "Operation denied by user."
        approval_handler.print_outcome("Execution", "Denied by user.", success=False)
        return ExecuteShellPluginOutput(command=command, error=err_msg)

    try:

        def run_sync_command():
            return subprocess.run(
                command, shell=True, capture_output=True, text=True, check=False
            )

        process = await asyncio.to_thread(run_sync_command)

        stdout = process.stdout.strip() if process.stdout else None
        stderr = process.stderr.strip() if process.stderr else None
        return_code = process.returncode

        if return_code == 0:
            approval_handler.print_outcome("Command", "Executed successfully.")
        else:
            approval_handler.print_outcome(
                "Command", f"Failed with return code {return_code}.", success=False
            )

        # Show stdout only if output control allows it
        if stdout and await should_show_stdout():
            _managed_plugin_print(stdout, style="dim white")
        # Show stderr only if output control allows it (usually always shown)
        if stderr and await should_show_stderr():
            _managed_plugin_print(stderr, style="dim red")

        return ExecuteShellPluginOutput(
            command=command,
            stdout=stdout,
            stderr=stderr,
            return_code=return_code,
        )

    except Exception as e:
        logger.error(f"Failed to execute command '{command}': {e}", exc_info=True)
        err_msg = f"Failed to execute command: {e}"
        approval_handler.print_outcome("Execution", err_msg, success=False)
        return ExecuteShellPluginOutput(command=command, error=err_msg)
