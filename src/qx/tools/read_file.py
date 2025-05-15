import os
from pathlib import Path
from typing import Optional, Union # Union is already there, Optional might be needed

# Corrected import for file_operations_base
from qx.tools.file_operations_base import is_path_allowed
# Imports for project_root and USER_HOME_DIR determination
from qx.core.config_manager import _find_project_root, USER_HOME_DIR

def read_file(path_str: str) -> Union[str, None]:
    """
    Reads the content of a file and returns it as a string,
    after checking if the path is allowed.

    Args:
        path_str: The path to the file (relative or absolute).

    Returns:
        The content of the file as a string, or None if an error occurs
        or the path is not allowed.
    """
    try:
        absolute_path = Path(path_str).resolve()
        project_root = _find_project_root(str(Path.cwd()))

        if not is_path_allowed(absolute_path, project_root, USER_HOME_DIR):
            print(f"Error: Path not allowed for reading: {absolute_path}")
            return None

        with open(absolute_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return content
    except FileNotFoundError:
        print(f"Error: File not found at path {absolute_path}")
        return None
    except IOError as e:
        print(f"Error reading file at path {absolute_path}: {e}")
        return None
    except Exception as e:
        # Catch any other unexpected errors during path resolution or permission checks
        print(f"An unexpected error occurred in read_file: {e}")
        return None

if __name__ == '__main__':
    # Example Usage (for testing this module directly)
    # Create dummy files and directories for testing
    # Note: This test assumes it's run from a directory where it can create files/dirs
    # and that config_manager can find a project root or use home.

    test_project_dir = Path("./temp_test_project")
    test_project_dir.mkdir(exist_ok=True)
    (test_project_dir / ".git").mkdir(exist_ok=True) # Simulate project root

    allowed_file_path = test_project_dir / "allowed.txt"
    dot_q_dir = test_project_dir / ".Q"
    dot_q_dir.mkdir(exist_ok=True)
    allowed_dot_q_file_path = dot_q_dir / "allowed_in_q.txt"

    # Create a file outside the project (in user's home, if not project root)
    # This path needs careful handling for tests; for now, let's focus on project files
    # home_file_path = USER_HOME_DIR / "test_home_file.txt"


    with open(allowed_file_path, "w", encoding="utf-8") as f:
        f.write("This is an allowed file.")
    with open(allowed_dot_q_file_path, "w", encoding="utf-8") as f:
        f.write("This is an allowed file in .Q directory.")

    # Test reading allowed file (assuming cwd is parent of temp_test_project or similar)
    # To make this test robust, we might need to temporarily change cwd or use absolute paths
    # For simplicity, let's assume we run this test from project_qx directory
    
    print(f"Current CWD for test: {Path.cwd()}")
    print(f"USER_HOME_DIR: {USER_HOME_DIR}")
    
    # Test case 1: Read file within project
    content1 = read_file(str(allowed_file_path))
    print(f"Reading {allowed_file_path}: {'Success' if content1 else 'Failed'}")
    if content1:
        print(f"Content: {content1}")

    # Test case 2: Read file within .Q
    content2 = read_file(str(allowed_dot_q_file_path))
    print(f"Reading {allowed_dot_q_file_path}: {'Success' if content2 else 'Failed'}")
    if content2:
        print(f"Content: {content2}")

    # Test case 3: Attempt to read a restricted file (e.g., /etc/passwd)
    # This path will likely be outside any allowed scope
    content3 = read_file("/etc/passwd")
    print(f"Reading /etc/passwd: {'Success (unexpected)' if content3 else 'Failed (expected)'}")

    # Clean up dummy files
    allowed_file_path.unlink(missing_ok=True)
    allowed_dot_q_file_path.unlink(missing_ok=True)
    if (test_project_dir / ".git").exists(): (test_project_dir / ".git").rmdir()
    if dot_q_dir.exists(): dot_q_dir.rmdir()
    if test_project_dir.exists(): test_project_dir.rmdir()