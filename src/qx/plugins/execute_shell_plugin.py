import fnmatch  # For command pattern matching
import logging
import subprocess
from typing import List, Optional

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
    "sudo *",  # General privilege escalation
    "su *",  # General privilege escalation
    "chmod 777 *",  # Excessive permissions
    "chmod -R 777 *",  # Recursive excessive permissions
    "rm -rf /*",  # Deleting root filesystem
    "dd if=/dev/zero of=/dev/*",  # Overwriting block devices
    "> /dev/sda",  # Overwriting specific block device (example)
    "mkfs.*",  # Formatting filesystems
    ":(){:|:&};:",  # Fork bomb (resource exhaustion)
    "mv /* /dev/null",  # Moving root filesystem contents to null
    "wget * | bash",  # Downloading and executing scripts
    "curl * | bash",  # Downloading and executing scripts
    "wget * | sh",  # Downloading and executing scripts
    "curl * | sh",  # Downloading and executing scripts
    "*(){ :;};*",  # Shellshock vulnerability pattern
    "echo * > /etc/passwd",  # Overwriting password file
    "echo * > /etc/shadow",  # Overwriting shadow password file
    "rm -rf ~",  # Deleting user's home directory
    "rm -rf .",  # Deleting current directory (dangerous if in critical path)
    "find / -delete",  # Find and delete everything from root
    "find . -delete",  # Find and delete everything from current dir
    "shred * /dev/*",  # Securely wiping block devices
    "wipe /dev/*",  # Wiping block devices
    "fdisk /dev/*",  # Disk partitioning tool (interactive)
    "parted /dev/*",  # Disk partitioning tool (interactive/scriptable)
    "gparted /dev/*",  # GUI Disk partitioning tool (can be scripted)
    "userdel root",  # Attempting to delete root user
    "groupdel root",  # Attempting to delete root group
    "passwd -d root",  # Removing root password (security risk)
    "passwd -l root",  # Locking root account
    "chown root* /*",  # Changing ownership of root files (potential breakage)
    "chown -R * /*",  # Recursively changing ownership from root
    "chattr -i *",  # Removing immutable flag (could allow modification of protected files)
    "chattr +i /*",  # Making critical files immutable (could break updates/recovery)
    "reboot",  # System reboot
    "shutdown *",  # System shutdown/reboot/halt
    "halt",  # Halting the system
    "poweroff",  # Powering off the system
    "init 0",  # Halting the system (runlevel)
    "init 6",  # Rebooting the system (runlevel)
    "iptables -F",  # Flushing all firewall rules
    "iptables -X",  # Deleting all non-default firewall chains
    "iptables -P INPUT DROP",  # Setting default input policy to DROP (can lock out)
    "iptables -P FORWARD DROP",  # Setting default forward policy to DROP
    "iptables -P OUTPUT DROP",  # Setting default output policy to DROP (can break connectivity)
    "ufw disable",  # Disabling Uncomplicated Firewall
    "systemctl stop firewalld",  # Stopping firewalld service
    "systemctl disable firewalld",  # Disabling firewalld service
    "insmod *",  # Inserting kernel modules
    "rmmod *",  # Removing kernel modules
    "modprobe *",  # Kernel module management (loading/unloading)
    "sysctl *",  # Modifying kernel parameters at runtime
    "echo * > /proc/sys/*",  # Writing directly to kernel parameters
    "* | base64 -d | bash",  # Pattern for executing base64 encoded scripts
    "* | base64 -d | sh",  # Pattern for executing base64 encoded scripts
    "history -c",  # Clearing command history
    "echo > ~/.bash_history",  # Clearing bash history file
    "kill -9 1",  # Attempting to kill init process (PID 1)
    "pkill init",  # Attempting to kill init process by name
    "mount -o remount,ro /",  # Remounting root filesystem as read-only (can cause issues)
    "mount /dev/sd* /mnt; rm -rf /mnt/*",  # Mounting and deleting files
]
DEFAULT_AUTO_APPROVED_SHELL_PATTERNS: List[str] = [
    # Basic commands without arguments
    "ls",  # List directory contents (no args)
    "ls *",  # List directory contents (with args)
    "cd",  # Change to home directory (no args)
    "cd *",  # Change directory (with args)
    "pwd",  # Print working directory
    "echo",  # Display empty line (no args)
    "echo *",  # Display text (with args)
    "cat",  # Wait for stdin (no args)
    "cat *",  # Concatenate and display files
    "head",  # Wait for stdin (no args)
    "head *",  # Display first part of files
    "tail",  # Wait for stdin (no args)
    "tail *",  # Display last part of files
    "grep",  # Wait for stdin (no args)
    "grep *",  # Search text using patterns
    "find",  # Find in current directory (no args)
    "find *",  # Search for files
    "mkdir",  # Error but harmless (no args)
    "mkdir *",  # Create directories
    "touch",  # Error but harmless (no args)
    "touch *",  # Change file timestamps / create empty files
    "cp",  # Error but harmless (no args)
    "cp *",  # Copy files and directories
    "mv",  # Error but harmless (no args)
    "mv *",  # Move/rename files and directories
    "python --version",  # Check Python version
    "python -m *",  # Run Python module
    "python3 --version",  # Check Python 3 version
    "python3 -m *",  # Run Python 3 module
    "pip list",  # List installed Python packages
    "pip show *",  # Show details about Python packages
    "pip freeze",  # Output installed packages in requirements format
    "uv list",  # List installed Python packages (using uv)
    "uv pip list",  # List installed Python packages (using uv)
    "uv pip show *",  # Show details about Python packages (using uv)
    "uv pip freeze",  # Output installed packages (using uv)
    "cloc",  # Count lines of code (current dir)
    "cloc *",  # Count lines of code
    "git",  # Show git help (no args)
    "git *",  # Git version control commands
    "date",  # Display current date and time
    "cal",  # Display calendar
    "uptime",  # Show how long system has been running
    "whoami",  # Display current user ID
    "id",  # Display user and group IDs
    "uname",  # Print system information (no args)
    "uname *",  # Print system information
    "df",  # Report file system disk space usage (no args)
    "df *",  # Report file system disk space usage
    "du",  # Estimate file space usage (current dir)
    "du *",  # Estimate file space usage
    "wc",  # Wait for stdin (no args)
    "wc *",  # Print newline, word, and byte counts for files
    "less",  # Wait for stdin (no args)
    "less *",  # Pager for viewing files (interactive)
    "more",  # Wait for stdin (no args)
    "more *",  # Pager for viewing files (interactive)
    "diff",  # Error but harmless (no args)
    "diff *",  # Compare files line by line
    "comm",  # Error but harmless (no args)
    "comm *",  # Compare two sorted files line by line
    "sort",  # Wait for stdin (no args)
    "sort *",  # Sort lines of text files
    "uniq",  # Wait for stdin (no args)
    "uniq *",  # Report or omit repeated lines
    "ps",  # Report process status (no args)
    "ps *",  # Report process status
    "top",  # Display system processes (interactive)
    "env",  # Display environment variables
    "printenv",  # Print all environment variables (no args)
    "printenv *",  # Print environment variables
    "export -p",  # List exported environment variables
    "man",  # Error but harmless (no args)
    "man *",  # Display manual pages
    "info",  # Show info directory (no args)
    "info *",  # Display command information (GNU)
    "tldr",  # Show tldr pages index (no args)
    "tldr *",  # Simplified man pages
    "* --help",  # Common pattern for command help
    "stat",  # Error but harmless (no args)
    "stat *",  # Display file or file system status
    "which",  # Error but harmless (no args)
    "which *",  # Locate a command
    "whereis",  # Error but harmless (no args)
    "whereis *",  # Locate binary, source, and manual page for command
    "type",  # Error but harmless (no args)
    "type *",  # Describe how a command name would be interpreted
    "history",  # Display command history
    "clear",  # Clear the terminal screen
    "ping",  # Error but harmless (no args)
    "ping *",  # Check network connectivity to a host
    "ip",  # Show IP commands (no args)
    "ip *",  # Show / manipulate routing, network devices, interfaces (read-only use like 'ip addr')
    "ifconfig",  # Show network interfaces (no args)
    "ifconfig *",  # Configure network interfaces (often used read-only)
    "netstat",  # Print network connections (no args)
    "netstat *",  # Print network connections, routing tables, interface stats (read-only options often safe)
    "ss",  # Display socket statistics (no args)
    "ss *",  # Socket statistics (modern replacement for netstat, read-only options safe)
    "host",  # Error but harmless (no args)
    "host *",  # DNS lookup utility
    "dig",  # Show dig help (no args)
    "dig *",  # DNS lookup utility (more detailed)
    "nslookup",  # Interactive mode (no args)
    "nslookup *",  # DNS lookup utility (interactive/non-interactive)
    "tar -tvf *",  # List contents of a tar archive
    "zipinfo *",  # List detailed information about a ZIP archive
    "unzip -l *",  # List contents of a ZIP archive
    "gzip -l *",  # Display compression statistics for gzip files
    "gunzip -l *",  # Display compression statistics for gzip files (same as gzip -l)
    "zcat *",  # Display contents of gzipped files
    "bzcat *",  # Display contents of bzip2 compressed files
    "xzcat *",  # Display contents of xz compressed files
    "basename *",  # Strip directory and suffix from filenames
    "dirname *",  # Strip last component from file name
    "readlink *",  # Read value of a symbolic link
    "test *",  # Check file types and compare values (shell builtin)
    "[ * ]",  # Alternate syntax for 'test' (shell builtin)
    "alias",  # List defined aliases
    "jobs",  # List active jobs
    "file",  # Error but harmless (no args)
    "file *",  # Determine file type
]
# --- End of command patterns ---


class ExecuteShellPluginInput(BaseModel):
    """Input model for the ExecuteShellPluginTool."""

    command: str = Field(..., description="The shell command to execute.")


class ExecuteShellPluginOutput(BaseModel):
    """Output model for the ExecuteShellPluginTool."""

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


def execute_shell_tool(
    ctx: RunContext[QXToolDependencies], args: ExecuteShellPluginInput
) -> ExecuteShellPluginOutput:
    """
    PydanticAI Tool to execute a shell command.
    Prohibited commands are blocked. Some safe commands are auto-approved.
    Most other commands require user confirmation and allow modification.
    """
    console = ctx.deps.console
    command_to_consider = args.command.strip()

    if not command_to_consider:
        return ExecuteShellPluginOutput(
            command="",
            stdout=None,
            stderr=None,
            return_code=None,
            error="Error: Empty command provided.",
        )

    if _is_command_prohibited(command_to_consider):
        err_msg = f"Error: Command '{command_to_consider}' is prohibited by policy."
        logger.error(err_msg)
        return ExecuteShellPluginOutput(
            command=command_to_consider,
            stdout=None,
            stderr=None,
            return_code=None,
            error=err_msg,
        )

    command_to_execute = command_to_consider
    needs_confirmation = not _is_command_auto_approved(command_to_consider)

    if needs_confirmation:
        prompt_msg = f"Allow QX to execute shell command: '{command_to_consider}'?"
        decision_status, final_value = request_confirmation(
            prompt_message=prompt_msg,
            console=console,
            allow_modify=True,
            current_value_for_modification=command_to_consider,
        )

        if decision_status == "modified" and final_value is not None:
            command_to_execute = final_value.strip()
            if not command_to_execute:  # User modified to empty string
                return ExecuteShellPluginOutput(
                    command=command_to_consider,  # Original command for context in output
                    stdout=None,
                    stderr=None,
                    return_code=None,
                    error="Error: Command modified to an empty string.",
                )
            logger.info(
                f"Shell command modified by user from '{command_to_consider}' to '{command_to_execute}'."
            )
            # Re-check if the modified command is prohibited
            if _is_command_prohibited(command_to_execute):
                err_msg = f"Error: Modified command '{command_to_execute}' is prohibited by policy."
                logger.error(err_msg)
                return ExecuteShellPluginOutput(
                    command=command_to_execute,
                    stdout=None,
                    stderr=None,
                    return_code=None,
                    error=err_msg,
                )
        elif decision_status == "approved":
            command_to_execute = command_to_consider  # Already set, but for clarity
        else:  # denied or cancelled
            error_message = f"Shell command execution for '{command_to_consider}' was {decision_status} by user."
            logger.warning(error_message)
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
            f"[success]AUTO-APPROVED (PATTERN):[/] Executing shell command [info]'{command_to_execute}'[/]"
        )

    try:
        # Note: Consider CWD implications. For now, commands run in QX's current CWD.
        # project_root = _find_project_root(str(Path.cwd())) # If needed for context-aware execution
        process = subprocess.run(
            command_to_execute,
            shell=True,  # Be cautious with shell=True. Ensure commands are vetted.
            capture_output=True,
            text=True,
            check=False,  # We handle returncode manually
        )
        logger.info(
            f"Command '{command_to_execute}' executed. Return code: {process.returncode}"
        )

        stdout = process.stdout.strip() if process.stdout else None
        stderr = process.stderr.strip() if process.stderr else None

        if process.returncode != 0:
            return ExecuteShellPluginOutput(
                command=command_to_execute,
                stdout=stdout,
                stderr=stderr,
                return_code=process.returncode,
                error=None,  # Explicitly None as this is not a pre-execution error
            )

        return ExecuteShellPluginOutput(
            command=command_to_execute,
            stdout=stdout,
            stderr=stderr,
            return_code=process.returncode,
            error=None,  # Explicitly None for successful execution
        )
    except Exception as e:
        logger.error(
            f"Failed to execute command '{command_to_execute}': {e}", exc_info=True
        )
        return ExecuteShellPluginOutput(
            command=command_to_execute,
            stdout=None,
            stderr=None,
            return_code=None,
            error=f"Error: Failed to execute command: {e}",
        )


if __name__ == "__main__":
    from rich.console import Console as RichConsole

    logging.basicConfig(level=logging.INFO)
    test_console = RichConsole()

    test_deps = QXToolDependencies(console=test_console)

    class DummyRunContext(RunContext[QXToolDependencies]):
        def __init__(self, deps: QXToolDependencies):
            super().__init__(deps=deps, usage=None)  # type: ignore

    dummy_ctx = DummyRunContext(deps=test_deps)

    test_console.rule("Testing execute_shell_tool plugin with RunContext")

    # Test 1: Auto-approved command
    test_console.print("\n[bold]Test 1: Auto-approved command (ls)[/]")
    input1 = ExecuteShellPluginInput(command="ls -l")
    output1 = execute_shell_tool(dummy_ctx, input1)
    test_console.print(
        f"Output 1: {output1.stdout[:100]}..." if output1.stdout else output1
    )
    assert output1.return_code == 0 and output1.error is None

    # Test 2: Prohibited command
    test_console.print("\n[bold]Test 2: Prohibited command (sudo reboot)[/]")
    input2 = ExecuteShellPluginInput(command="sudo reboot")
    output2 = execute_shell_tool(dummy_ctx, input2)
    test_console.print(f"Output 2: {output2}")
    assert output2.error is not None and "prohibited" in output2.error
    assert output2.stdout is None
    assert output2.stderr is None
    assert output2.return_code is None

    # Test 3: Command requiring confirmation (user approves)
    test_console.print(
        "\n[bold]Test 3: Needs confirmation (echo 'hello') - user approves[/]"
    )
    input3 = ExecuteShellPluginInput(command="echo 'Hello QX Shell'")
    test_console.print("Please respond 'y' to the prompt.")
    output3 = execute_shell_tool(dummy_ctx, input3)
    test_console.print(f"Output 3: {output3}")
    assert (
        output3.stdout == "Hello QX Shell"
        and output3.return_code == 0
        and output3.error is None
    )

    # Test 4: Command requiring confirmation (user denies)
    test_console.print("\n[bold]Test 4: Needs confirmation (date) - user denies[/]")
    input4 = ExecuteShellPluginInput(command="date")
    test_console.print("Please respond 'n' to the prompt.")
    output4 = execute_shell_tool(dummy_ctx, input4)
    test_console.print(f"Output 4: {output4}")
    assert output4.error is not None and "denied by user" in output4.error
    assert output4.stdout is None
    assert output4.stderr is None
    assert output4.return_code is None

    # Test 5: Command requiring confirmation (user modifies)
    original_cmd = "whoami_original"
    modified_cmd = "whoami"
    test_console.print(
        f"\n[bold]Test 5: Needs confirmation ('{original_cmd}') - user modifies to '{modified_cmd}'[/]"
    )
    input5 = ExecuteShellPluginInput(command=original_cmd)
    test_console.print(f"Please respond 'm', then enter '{modified_cmd}'.")
    output5 = execute_shell_tool(dummy_ctx, input5)
    test_console.print(f"Output 5: {output5}")
    assert (
        output5.command == modified_cmd
        and output5.return_code == 0
        and output5.stdout
        and output5.error is None
    )

    # Test 6: Command fails (non-zero exit code)
    test_console.print("\n[bold]Test 6: Command fails (ls non_existent_file)[/]")
    input6 = ExecuteShellPluginInput(command="ls __non_existent_file_for_qx_test__")
    output6 = execute_shell_tool(dummy_ctx, input6)
    test_console.print(f"Output 6: {output6}")
    assert output6.return_code != 0 and output6.error is None
    assert output6.stderr is not None

    # Test 7: Command modified to empty string
    test_console.print("\n[bold]Test 7: Command modified to empty string[/]")
    input7 = ExecuteShellPluginInput(command="echo 'this will be modified to empty'")
    test_console.print(
        "Please respond 'm', then enter an empty string (just press Enter)."
    )
    output7 = execute_shell_tool(dummy_ctx, input7)
    test_console.print(f"Output 7: {output7}")
    assert output7.error == "Error: Command modified to an empty string."
    assert output7.command == "echo 'this will be modified to empty'"
    assert output7.stdout is None
    assert output7.stderr is None
    assert output7.return_code is None

    # Test 8: Command modified to a prohibited command
    test_console.print("\n[bold]Test 8: Command modified to a prohibited command[/]")
    input8 = ExecuteShellPluginInput(
        command="echo 'this will be modified to sudo reboot'"
    )
    test_console.print("Please respond 'm', then enter 'sudo reboot'.")
    output8 = execute_shell_tool(dummy_ctx, input8)
    test_console.print(f"Output 8: {output8}")
    assert (
        output8.error
        == "Error: Modified command 'sudo reboot' is prohibited by policy."
    )
    assert output8.command == "sudo reboot"
    assert output8.stdout is None
    assert output8.stderr is None
    assert output8.return_code is None

    test_console.print("\nExecute_shell_plugin tests finished.")

