import os
from pathlib import Path
from typing import Optional # Optional might be needed if project_root can be None

# Corrected import for file_operations_base
from qx.tools.file_operations_base import is_path_allowed
# Imports for project_root and USER_HOME_DIR determination
from qx.core.config_manager import _find_project_root, USER_HOME_DIR

def write_file(path_str: str, content: str) -> bool:
    """
    Writes content to a file at the specified path,
    after checking if the path is allowed.

    Args:
        path_str: The path to the file (relative or absolute).
        content: The string content to write to the file.

    Returns:
        True if the file was written successfully, False otherwise.
    """
    try:
        absolute_path = Path(path_str).resolve()
        project_root = _find_project_root(str(Path.cwd()))
        parent_dir = absolute_path.parent

        # Check if the parent directory is allowed for writing/creation
        if not is_path_allowed(parent_dir, project_root, USER_HOME_DIR):
            print(f"Error: Path not allowed for writing (directory creation restricted): {parent_dir}")
            return False

        # Check if the file path itself is allowed (even if parent is, file might be special)
        # This also covers cases where parent_dir might be project_root but file is project_root/.git/config
        if not is_path_allowed(absolute_path, project_root, USER_HOME_DIR):
            print(f"Error: Path not allowed for writing: {absolute_path}")
            return False

        # Create parent directories if they don't exist
        # This is safe now because parent_dir was checked by is_path_allowed
        os.makedirs(parent_dir, exist_ok=True)

        with open(absolute_path, 'w', encoding='utf-8') as f:
            f.write(content)
        # print(f"Successfully wrote to {absolute_path}") # Optional: for verbose success
        return True
    except IOError as e:
        print(f"Error writing file at path {absolute_path}: {e}")
        return False
    except Exception as e:
        # Catch any other unexpected errors
        print(f"An unexpected error occurred in write_file: {e}")
        return False

if __name__ == '__main__':
    # Example Usage (for testing this module directly)
    test_project_dir = Path("./temp_test_project_write")
    test_project_dir.mkdir(exist_ok=True)
    (test_project_dir / ".git").mkdir(exist_ok=True) # Simulate project root

    allowed_file_to_write = test_project_dir / "new_allowed_file.txt"
    allowed_subdir = test_project_dir / "subdir"
    allowed_file_in_subdir = allowed_subdir / "another_file.txt"

    dot_q_dir = test_project_dir / ".Q"
    # .Q directory itself is allowed if project_root is defined.
    # We don't need to create it here for is_path_allowed to permit writing *into* it.
    allowed_file_in_dot_q = dot_q_dir / "q_config.txt"


    print(f"Current CWD for test: {Path.cwd()}")
    print(f"USER_HOME_DIR: {USER_HOME_DIR}")

    # Test case 1: Write file within project
    success1 = write_file(str(allowed_file_to_write), "Content for allowed file.")
    print(f"Writing {allowed_file_to_write}: {'Success' if success1 else 'Failed'}")
    if success1 and allowed_file_to_write.exists():
        print(f"  Content: {allowed_file_to_write.read_text(encoding='utf-8')}")

    # Test case 2: Write file in a new subdirectory within project
    success2 = write_file(str(allowed_file_in_subdir), "Content for file in subdir.")
    print(f"Writing {allowed_file_in_subdir}: {'Success' if success2 else 'Failed'}")
    if success2 and allowed_file_in_subdir.exists():
        print(f"  Content: {allowed_file_in_subdir.read_text(encoding='utf-8')}")

    # Test case 3: Write file within .Q directory
    success3 = write_file(str(allowed_file_in_dot_q), "Content for .Q file.")
    print(f"Writing {allowed_file_in_dot_q}: {'Success' if success3 else 'Failed'}")
    if success3 and allowed_file_in_dot_q.exists():
        print(f"  Content: {allowed_file_in_dot_q.read_text(encoding='utf-8')}")


    # Test case 4: Attempt to write to a restricted path (e.g., /etc/new_file.txt)
    # This path will likely be outside any allowed scope
    restricted_path_write = "/etc/test_qx_write.txt"
    success4 = write_file(restricted_path_write, "Attempting to write to /etc.")
    print(f"Writing {restricted_path_write}: {'Success (unexpected)' if success4 else 'Failed (expected)'}")


    # Clean up dummy files and directories
    if allowed_file_to_write.exists(): allowed_file_to_write.unlink()
    if allowed_file_in_subdir.exists(): allowed_file_in_subdir.unlink()
    if allowed_subdir.exists(): allowed_subdir.rmdir()
    if allowed_file_in_dot_q.exists(): allowed_file_in_dot_q.unlink()
    if dot_q_dir.exists(): dot_q_dir.rmdir() # remove only if empty, os.rmdir fails otherwise
                                            # for robust cleanup, shutil.rmtree might be needed if .Q had other files
    if (test_project_dir / ".git").exists(): (test_project_dir / ".git").rmdir()
    if test_project_dir.exists(): test_project_dir.rmdir()