import logging
import os
from pathlib import Path
from typing import Optional

from qx.core.paths import USER_HOME_DIR, _find_project_root
from qx.tools.file_operations_base import is_path_allowed

# Configure logging for this module
logger = logging.getLogger(__name__)


def write_file_impl(path_str: str, content: str) -> bool:
    """
    Writes content to a file after path validation.
    This is the core implementation, intended to be called after approval.

    Args:
        path_str: The relative or absolute path to the file.
        content: The string content to write to the file. Do not wrap the content in triples quotes.

    Returns:
        True if the write was successful, False otherwise.
    """
    try:
        project_root = _find_project_root(str(Path.cwd()))
        absolute_path = Path(path_str).resolve()

        # Check if the target path (and its parent for directory creation) is allowed
        if not is_path_allowed(absolute_path, project_root, USER_HOME_DIR):
            logger.error(
                f"Write access denied by policy for path: {absolute_path}. "
                f"Project root: {project_root}, User home: {USER_HOME_DIR}"
            )
            # Consider returning a more descriptive error message if the LLM needs it
            return False  # Or raise an exception / return error string

        # Also check if creating the parent directory is allowed, if it doesn't exist
        parent_dir = absolute_path.parent
        if not parent_dir.exists():
            if not is_path_allowed(parent_dir, project_root, USER_HOME_DIR):
                logger.error(
                    f"Write access denied by policy for creating parent directory: {parent_dir}."
                )
                return False

        # Create parent directories if they don't exist
        # This check is now implicitly covered by is_path_allowed(parent_dir, ...)
        # if the parent_dir itself is outside allowed scope.
        # os.makedirs will fail if it tries to create a dir where it's not allowed.
        parent_dir.mkdir(parents=True, exist_ok=True)

        absolute_path.write_text(content, encoding="utf-8")
        logger.info(f"Successfully wrote to file: {absolute_path}")
        return True

    except PermissionError:
        logger.error(f"Permission denied writing to file: {path_str}")
    except IsADirectoryError:
        logger.error(f"Path is a directory, cannot write file: {path_str}")
    except Exception as e:
        logger.error(f"Error writing file '{path_str}': {e}", exc_info=True)

    return False


if __name__ == "__main__":
    # Example usage for direct testing
    # Ensure you have appropriate permissions in /tmp or a test directory
    # current_dir = Path("/tmp/qx_test_project_write")
    # current_dir.mkdir(parents=True, exist_ok=True)
    # (current_dir / ".Q").mkdir(exist_ok=True) # Simulate a project

    # print(f"Testing write_file_impl from {current_dir}")
    # test_file_path = current_dir / "test_write.txt"
    # content_to_write = "Hello from write_file_impl test."

    # print(f"Writing to '{test_file_path}': {write_file_impl(str(test_file_path), content_to_write)}")
    # if test_file_path.exists():
    #     print(f"Content of '{test_file_path}': {test_file_path.read_text()}")
    # else:
    #     print(f"File '{test_file_path}' was not created.")

    # print(f"Attempting to write to a restricted path (e.g., /etc/test_write.txt - should fail): {write_file_impl('/etc/test_write.txt', 'restricted content')}")
    pass

