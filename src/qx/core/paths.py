# src/qx/core/paths.py
import os
import logging
from pathlib import Path

logger = logging.getLogger("qx")

# Determine USER_HOME_DIR dynamically at runtime
try:
    USER_HOME_DIR = Path.home().resolve()
    logger.debug(f"USER_HOME_DIR resolved to: {USER_HOME_DIR}")
except Exception as e:
    # Fallback to current directory if home() fails
    USER_HOME_DIR = Path.cwd()
    logger.warning(f"Failed to resolve home directory: {e}")
    logger.warning(f"Using current directory as fallback: {USER_HOME_DIR}")

# Qx Configuration and Data Directory
# Allow override via environment variable
default_config_dir = str(USER_HOME_DIR / ".config" / "qx")
QX_CONFIG_DIR = Path(os.getenv("QX_CONFIG_DIR", default_config_dir))
if os.getenv("QX_CONFIG_DIR"):
    logger.info(f"Using custom QX_CONFIG_DIR from environment: {QX_CONFIG_DIR}")
else:
    logger.debug(f"Using default QX_CONFIG_DIR: {QX_CONFIG_DIR}")

# History file path
# Allow override via environment variable for restricted environments
default_history_file = str(QX_CONFIG_DIR / "history")
QX_HISTORY_FILE = Path(os.getenv("QX_HISTORY_FILE", default_history_file))
if os.getenv("QX_HISTORY_FILE"):
    logger.info(f"Using custom QX_HISTORY_FILE from environment: {QX_HISTORY_FILE}")
else:
    logger.debug(f"Using default QX_HISTORY_FILE: {QX_HISTORY_FILE}")

# Session files directory
QX_SESSIONS_DIR = Path(".Q") / "sessions"

# MCP Server Configuration Paths
SYSTEM_MCP_SERVERS_PATH = Path("/etc/qx/mcp_servers.json")
USER_MCP_SERVERS_PATH = QX_CONFIG_DIR / "mcp_servers.json"
PROJECT_MCP_SERVERS_PATH = Path(".Q/config/mcp_servers.json")


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

        path_to_check = path_to_check.parent  # Move to parent directory


if __name__ == "__main__":
    # Test _find_project_root
    print(f"User home directory: {USER_HOME_DIR}")
    print(f"Qx Config directory: {QX_CONFIG_DIR}")
    print(f"Qx History file: {QX_HISTORY_FILE}")
    print(f"Qx Sessions directory: {QX_SESSIONS_DIR}")

    # Ensure config dir exists for testing other modules that might import this
    os.makedirs(QX_CONFIG_DIR, exist_ok=True)
    print(f"Ensured Qx Config directory exists for testing: {QX_CONFIG_DIR.exists()}")

    # Ensure sessions dir exists for testing
    os.makedirs(QX_SESSIONS_DIR, exist_ok=True)
    print(
        f"Ensured Qx Sessions directory exists for testing: {QX_SESSIONS_DIR.exists()}"
    )

    print(
        f"Project root from CWD ({Path.cwd()}): {_find_project_root(str(Path.cwd()))}"
    )
