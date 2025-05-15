import fnmatch
import logging
import shlex
import subprocess
from typing import Any, Dict

from qx.core.constants import (DEFAULT_PROHIBITED_COMMANDS,
                                SHELL_COMMAND_TIMEOUT)

# Configure logging for this module
logger = logging.getLogger(__name__)


def execute_shell_impl(command: str) -> Dict[str, Any]:
    """
    Executes a shell command after validation and returns its output.
    This is the core implementation, intended to be called after approval
    and potential modification.

    Args:
        command: The shell command string to execute.

    Returns:
        A dictionary containing stdout, stderr, returncode, and an optional
        error message if the command is prohibited or an execution error occurs.
    """
    logger.info(f"Attempting to execute shell command: {command}")

    try:
        # Use shlex.split for safer command parsing, especially with quotes
        # However, for `subprocess.run` with `shell=False` (recommended),
        # the command should be a list of arguments.
        # If `shell=True` is used (less safe), `command` can be a string.
        # For now, assuming the command string is as the LLM/user intends for `shell=True`
        # or it's a simple command that works as a string for `shell=False`.
        # A more robust solution would involve `shlex.split()` and then passing
        # the list to `subprocess.run(..., shell=False)`.
        # Let's stick to the original simpler subprocess call for now, assuming
        # the command is well-formed or simple.

        # Check against prohibited commands (this is a redundant check if approval system is robust,
        # but good for defense in depth)
        for pattern in DEFAULT_PROHIBITED_COMMANDS:
            if fnmatch.fnmatch(command, pattern) or fnmatch.fnmatch(shlex.split(command)[0], pattern) :
                error_msg = f"Command '{command}' matches prohibited pattern '{pattern}'."
                logger.warning(f"Execution denied: {error_msg}")
                return {
                    "stdout": "",
                    "stderr": error_msg,
                    "returncode": -1,
                    "error": "Prohibited command",
                }

        # Execute the command
        # Using shell=True can be a security risk if the command is crafted maliciously.
        # However, it allows for shell features like pipes and wildcards directly.
        # Given the approval mechanism, this risk is somewhat mitigated.
        # For better security, shell=False and passing shlex.split(command) is preferred
        # but might break complex commands LLM might generate.
        process = subprocess.run(
            command,
            shell=True, # Be cautious with shell=True
            capture_output=True,
            text=True,
            timeout=SHELL_COMMAND_TIMEOUT,
            check=False, # Don't raise exception for non-zero exit codes
        )

        stdout = process.stdout.strip()
        stderr = process.stderr.strip()
        returncode = process.returncode

        if stdout:
            logger.info(f"Command stdout: {stdout}")
        if stderr:
            logger.warning(f"Command stderr: {stderr}")
        logger.info(f"Command return code: {returncode}")

        return {
            "stdout": stdout,
            "stderr": stderr,
            "returncode": returncode,
        }

    except subprocess.TimeoutExpired:
        logger.error(f"Command '{command}' timed out after {SHELL_COMMAND_TIMEOUT} seconds.")
        return {
            "stdout": "",
            "stderr": f"Command timed out after {SHELL_COMMAND_TIMEOUT} seconds.",
            "returncode": -1,
            "error": "Timeout",
        }
    except FileNotFoundError: # If the command itself is not found by the shell
        logger.error(f"Command not found: {command.split()[0] if command else 'empty command'}")
        return {
            "stdout": "",
            "stderr": f"Command not found: {shlex.split(command)[0] if command else 'empty command'}",
            "returncode": 127, # Common exit code for command not found
            "error": "Command not found",
        }
    except Exception as e:
        logger.error(f"Error executing command '{command}': {e}", exc_info=True)
        return {
            "stdout": "",
            "stderr": f"An unexpected error occurred: {e}",
            "returncode": -1,
            "error": f"Execution error: {e}",
        }

if __name__ == "__main__":
    # Example Usage
    # print("Executing 'ls -la /tmp':")
    # result = execute_shell_impl("ls -la /tmp")
    # print(f"  Stdout: {result['stdout']}")
    # print(f"  Stderr: {result['stderr']}")
    # print(f"  Return Code: {result['returncode']}\n")

    # print("Executing a safe command 'echo Hello QX':")
    # result = execute_shell_impl("echo Hello QX")
    # print(f"  Stdout: {result['stdout']}")
    # print(f"  Stderr: {result['stderr']}")
    # print(f"  Return Code: {result['returncode']}\n")

    # print("Executing a non-existent command 'nonexistentcmd':")
    # result = execute_shell_impl("nonexistentcmd")
    # print(f"  Stdout: {result['stdout']}")
    # print(f"  Stderr: {result['stderr']}")
    # print(f"  Return Code: {result['returncode']}\n")

    # print("Executing a prohibited command (example, adjust DEFAULT_PROHIBITED_COMMANDS for test):")
    # # To test this, you might add "sudo*" to DEFAULT_PROHIBITED_COMMANDS
    # # result = execute_shell_impl("sudo reboot")
    # # print(f"  Stdout: {result['stdout']}")
    # # print(f"  Stderr: {result['stderr']}")
    # # print(f"  Return Code: {result['returncode']}\n")

    # print("Executing a command that times out (sleep longer than timeout):")
    # # Ensure SHELL_COMMAND_TIMEOUT is small for this test, e.g., 1 second
    # # result = execute_shell_impl(f"sleep {SHELL_COMMAND_TIMEOUT + 1}")
    # # print(f"  Stdout: {result['stdout']}")
    # # print(f"  Stderr: {result['stderr']}")
    # # print(f"  Return Code: {result['returncode']}\n")
    pass