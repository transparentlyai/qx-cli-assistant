# src/qx/core/paths.py
from pathlib import Path

# Determine USER_HOME_DIR dynamically at runtime
USER_HOME_DIR = Path.home().resolve()


def _find_project_root(cwd_str: str) -> Path | None:
    """
    Finds the project root by searching for a .Q or .git directory.
    Searches upwards from cwd_str, stopping at USER_HOME_DIR (inclusive for check)
    or if user_home_dir.parent would be the next directory to check.
    """
    current_path = Path(cwd_str).resolve()

    # Iterate upwards from current_path
    path_to_check = current_path
    while True:
        # Check if current path_to_check is a project root
        if (path_to_check / ".Q").is_dir() or (path_to_check / ".git").is_dir():
            return path_to_check

        # Stop conditions:
        # 1. If path_to_check is the user's home directory (and it wasn't a project root from the check above)
        if path_to_check == USER_HOME_DIR:
            return None

        # 2. If path_to_check is the filesystem root (its parent is itself)
        if path_to_check.parent == path_to_check:
            return None

        # 3. If the parent of path_to_check is USER_HOME_DIR.parent,
        #    it means path_to_check is a sibling of USER_HOME_DIR or USER_HOME_DIR.parent itself.
        #    This signifies we've searched up to the level of USER_HOME_DIR's parent,
        #    and USER_HOME_DIR itself was the last directory in its lineage to be checked.
        #    We should not go to USER_HOME_DIR.parent.
        if (
            path_to_check.parent == USER_HOME_DIR.parent
            and path_to_check != USER_HOME_DIR
        ):
            return None

        path_to_check = path_to_check.parent

if __name__ == '__main__':
    # Test _find_project_root
    print(f"User home directory: {USER_HOME_DIR}")
    # To test this effectively, you'd need to run it from various directories
    # For example, from within a dummy project with a .git or .Q folder
    # And from outside such a project.
    print(f"Project root from CWD ({Path.cwd()}): {_find_project_root(str(Path.cwd()))}")
    # Example: Create a dummy project structure for testing
    # (Path.cwd() / "temp_proj_for_paths_test" / ".git").mkdir(parents=True, exist_ok=True)
    # print(f"Project root from temp_proj_for_paths_test: {_find_project_root(str(Path.cwd() / 'temp_proj_for_paths_test'))}")
    # (Path.cwd() / "temp_proj_for_paths_test" / ".git").rmdir()
    # (Path.cwd() / "temp_proj_for_paths_test").rmdir()
