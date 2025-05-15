import subprocess
import shlex
import fnmatch
from typing import Dict, Union, List

from qx.core.constants import DEFAULT_PROHIBITED_COMMANDS

SHELL_COMMAND_TIMEOUT = 60  # seconds

def _is_command_prohibited(command: str, prohibited_patterns: List[str]) -> bool:
    """
    Checks if the given command matches any of the prohibited patterns.
    """
    command_stripped = command.strip()
    if not command_stripped: # Empty command is not prohibited but won't do anything
        return False
    for pattern in prohibited_patterns:
        if fnmatch.fnmatch(command_stripped, pattern):
            return True
    return False

def execute_shell(command: str) -> Dict[str, Union[str, int, None]]:
    """
    Executes a shell command after checking against a list of prohibited patterns.

    Args:
        command: The command string to execute.

    Returns:
        A dictionary containing:
        - "stdout": The standard output of the command.
        - "stderr": The standard error of the command.
        - "returncode": The exit code of the command.
        - "error": A string describing an error within the tool itself (e.g., prohibited, timeout),
                   or None if the command executed (even if it failed).
    """
    if _is_command_prohibited(command, DEFAULT_PROHIBITED_COMMANDS):
        error_message = "Error: Command execution denied by security policy."
        return {
            "stdout": "",
            "stderr": error_message,
            "returncode": -1,  # Using -1 to indicate a tool-level pre-execution failure
            "error": "Command prohibited",
        }

    try:
        # shlex.split is used for safer command parsing than shell=True
        args = shlex.split(command)
        if not args: # Handle empty or whitespace-only commands that shlex.split might return empty list for
            return {
                "stdout": "",
                "stderr": "Error: No command provided.",
                "returncode": -1,
                "error": "Empty command",
            }

        process = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=SHELL_COMMAND_TIMEOUT,
            check=False,  # We handle the return code manually
        )
        return {
            "stdout": process.stdout.strip(),
            "stderr": process.stderr.strip(),
            "returncode": process.returncode,
            "error": None,
        }
    except subprocess.TimeoutExpired:
        error_message = f"Error: Command '{command}' timed out after {SHELL_COMMAND_TIMEOUT} seconds."
        return {
            "stdout": "",
            "stderr": error_message,
            "returncode": -1, # Indicate timeout
            "error": "Timeout",
        }
    except FileNotFoundError:
        # This occurs if the command executable itself is not found
        executable = shlex.split(command)[0] if shlex.split(command) else "Unknown"
        error_message = f"Error: Command not found: '{executable}'. Please ensure it is installed and in PATH."
        return {
            "stdout": "",
            "stderr": error_message,
            "returncode": -1, # Indicate command not found by OS
            "error": "Command not found",
        }
    except Exception as e:
        # Catch any other unexpected errors during subprocess execution
        error_message = f"An unexpected error occurred while trying to execute command '{command}': {e}"
        return {
            "stdout": "",
            "stderr": error_message,
            "returncode": -1, # Indicate generic tool error
            "error": f"Execution error: {str(e)}",
        }

if __name__ == '__main__':
    # Example Usage for direct testing
    print("Testing execute_shell tool...")

    # Test 1: Safe command
    print("\nTest 1: Safe command (ls -l)")
    result1 = execute_shell("ls -l __init__.py") # Assuming this file exists where test is run
    print(f"  Stdout: {result1['stdout']}")
    print(f"  Stderr: {result1['stderr']}")
    print(f"  Return Code: {result1['returncode']}")
    print(f"  Error: {result1['error']}")

    # Test 2: Prohibited command (exact match)
    print("\nTest 2: Prohibited command (rm -rf /)")
    # Add a specific pattern for testing if not already present or too dangerous
    # For this test, let's assume 'rm -rf /' is in DEFAULT_PROHIBITED_COMMANDS
    if not _is_command_prohibited("rm -rf /", DEFAULT_PROHIBITED_COMMANDS):
        print("  WARNING: 'rm -rf /' not in DEFAULT_PROHIBITED_COMMANDS for this test, results may vary.")
    result2 = execute_shell("rm -rf /")
    print(f"  Stdout: {result2['stdout']}")
    print(f"  Stderr: {result2['stderr']}")
    print(f"  Return Code: {result2['returncode']}")
    print(f"  Error: {result2['error']}")

    # Test 3: Prohibited command (wildcard match, e.g., sudo *)
    print("\nTest 3: Prohibited command (sudo apt update)")
    if not _is_command_prohibited("sudo apt update", DEFAULT_PROHIBITED_COMMANDS):
         print("  WARNING: 'sudo *' pattern might not be effectively catching 'sudo apt update' for this test.")
    result3 = execute_shell("sudo apt update")
    print(f"  Stdout: {result3['stdout']}")
    print(f"  Stderr: {result3['stderr']}")
    print(f"  Return Code: {result3['returncode']}")
    print(f"  Error: {result3['error']}")

    # Test 4: Command not found
    print("\nTest 4: Command not found (nonexistentcommand)")
    result4 = execute_shell("nonexistentcommand arg1 arg2")
    print(f"  Stdout: {result4['stdout']}")
    print(f"  Stderr: {result4['stderr']}")
    print(f"  Return Code: {result4['returncode']}")
    print(f"  Error: {result4['error']}")

    # Test 5: Command that produces stderr
    print("\nTest 5: Command producing stderr (ls /nonexistentdir)")
    result5 = execute_shell("ls /nonexistentdir")
    print(f"  Stdout: {result5['stdout']}")
    print(f"  Stderr: {result5['stderr']}")
    print(f"  Return Code: {result5['returncode']}")
    print(f"  Error: {result5['error']}")

    # Test 6: Timeout
    print("\nTest 6: Timeout (sleep command)")
    # Note: SHELL_COMMAND_TIMEOUT needs to be short for this test to run quickly.
    # Temporarily reduce for test if needed, or accept the wait.
    # For now, assume SHELL_COMMAND_TIMEOUT is long, this test will take time.
    # result6 = execute_shell(f"sleep {SHELL_COMMAND_TIMEOUT + 5}")
    # print(f"  Stdout: {result6['stdout']}")
    # print(f"  Stderr: {result6['stderr']}")
    # print(f"  Return Code: {result6['returncode']}")
    # print(f"  Error: {result6['error']}")
    print(f"  (Skipping timeout test for brevity, ensure SHELL_COMMAND_TIMEOUT={SHELL_COMMAND_TIMEOUT}s is appropriate)")

    # Test 7: Empty command
    print("\nTest 7: Empty command")
    result7 = execute_shell("")
    print(f"  Stdout: {result7['stdout']}")
    print(f"  Stderr: {result7['stderr']}")
    print(f"  Return Code: {result7['returncode']}")
    print(f"  Error: {result7['error']}")

    # Test 8: Command with quotes and arguments
    print("\nTest 8: Command with quotes and arguments (echo 'hello world')")
    result8 = execute_shell("echo 'hello world to a file.txt'") # This will create file if not careful
    result8 = execute_shell("echo 'hello world'")
    print(f"  Stdout: {result8['stdout']}")
    print(f"  Stderr: {result8['stderr']}")
    print(f"  Return Code: {result8['returncode']}")
    print(f"  Error: {result8['error']}")