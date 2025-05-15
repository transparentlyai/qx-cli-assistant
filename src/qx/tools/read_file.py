import logging
from pathlib import Path
from typing import Optional

from qx.core.paths import USER_HOME_DIR, _find_project_root
from qx.tools.file_operations_base import is_path_allowed

# Configure logging for this module
logger = logging.getLogger(__name__)


def read_file_impl(path_str: str) -> Optional[str]:
    """
    Reads the content of a file after path validation.
    This is the core implementation, intended to be called after approval.

    Args:
        path_str: The relative or absolute path to the file.

    Returns:
        The file content as a string, or None if an error occurs or
        the path is not allowed.
    """
    try:
        # Determine project_root based on current working directory at the time of the call
        # This ensures context is fresh for each tool invocation if CWD could change.
        # However, for QX, CWD is generally stable during a session.
        # For simplicity and consistency with how project_root is determined elsewhere (e.g. config_manager)
        # we could pass project_root if it's already determined, or re-determine it.
        # Here, we re-determine to keep the tool self-contained regarding path validation context.
        project_root = _find_project_root(str(Path.cwd()))
        absolute_path = Path(path_str).resolve()

        if not is_path_allowed(absolute_path, project_root, USER_HOME_DIR):
            logger.error(
                f"Read access denied by policy for path: {absolute_path}. "
                f"Project root: {project_root}, User home: {USER_HOME_DIR}"
            )
            # To provide feedback to the LLM, an error message could be returned.
            # For now, returning None as per original design for errors.
            return f"Error: Access denied by policy for path: {absolute_path}"


        if not absolute_path.is_file():
            logger.error(f"File not found or not a file: {absolute_path}")
            return f"Error: File not found or is not a regular file: {absolute_path}"

        content = absolute_path.read_text(encoding="utf-8")
        logger.info(f"Successfully read file: {absolute_path}")
        return content

    except FileNotFoundError:
        logger.error(f"File not found: {path_str}")
        return f"Error: File not found: {path_str}"
    except PermissionError:
        logger.error(f"Permission denied reading file: {path_str}")
        return f"Error: Permission denied reading file: {path_str}"
    except IsADirectoryError:
        logger.error(f"Path is a directory, not a file: {path_str}")
        return f"Error: Path is a directory, not a file: {path_str}"
    except Exception as e:
        logger.error(f"Error reading file '{path_str}': {e}", exc_info=True)
        return f"Error reading file '{path_str}': {e}"

if __name__ == "__main__":
    # Example usage for direct testing (ensure you have appropriate files/permissions)
    # Create a dummy project structure for testing
    # mkdir -p /tmp/qx_test_project/.Q
    # echo "hello from project file" > /tmp/qx_test_project/test.txt
    # echo "user details" > ~/.config/q/user.md (if not exists)

    # Test within a "project"
    # current_dir = Path("/tmp/qx_test_project")
    # current_dir.mkdir(parents=True, exist_ok=True)
    # (current_dir / ".Q").mkdir(exist_ok=True)
    # (current_dir / "example.txt").write_text("Project file content.")

    # print(f"Testing read_file_impl from {current_dir}")
    # print(f"Reading 'example.txt': {read_file_impl(str(current_dir / 'example.txt'))}")
    # print(f"Reading './example.txt' (relative): {read_file_impl('example.txt')}") # Needs CWD to be /tmp/qx_test_project
    # print(f"Reading non_existent.txt: {read_file_impl('non_existent.txt')}")
    # print(f"Reading outside project (e.g., /etc/hosts - should be denied by policy if not in home and no project): {read_file_impl('/etc/hosts')}")

    # To run this test effectively, you might need to adjust CWD or use absolute paths
    # that align with your test setup and the logic in _find_project_root and is_path_allowed.
    pass