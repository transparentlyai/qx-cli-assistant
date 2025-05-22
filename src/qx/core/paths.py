# src/qx/core/paths.py
import os
from pathlib import Path

# Determine USER_HOME_DIR dynamically at runtime
USER_HOME_DIR = Path.home().resolve()

# QX Configuration and Data Directory
Q_CONFIG_DIR = USER_HOME_DIR / ".config" / "q"

# History file path
Q_HISTORY_FILE = Q_CONFIG_DIR / "history"


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

        path_to_check = path_to_check.to_parent() # Use to_parent() for clarity and robustness


if __name__ == "__main__":
    # Test _find_project_root
    print(f"User home directory: {USER_HOME_DIR}")
    print(f"QX Config directory: {Q_CONFIG_DIR}")
    print(f"QX History file: {Q_HISTORY_FILE}")

    # Ensure config dir exists for testing other modules that might import this
    os.makedirs(Q_CONFIG_DIR, exist_ok=True)
    print(f"Ensured QX Config directory exists for testing: {Q_CONFIG_DIR.exists()}")

    print(
        f"Project root from CWD ({Path.cwd()}): {_find_project_root(str(Path.cwd()))}"
    )
