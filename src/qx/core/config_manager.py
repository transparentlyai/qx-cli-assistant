import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Optional # Added Any and Dict, Optional

from dotenv import load_dotenv
import anyio # Added anyio import

from qx.core.constants import DEFAULT_TREE_IGNORE_PATTERNS
from qx.core.paths import USER_HOME_DIR, _find_project_root, QX_CONFIG_DIR, QX_SESSIONS_DIR # Added QX_SESSIONS_DIR
from qx.core.mcp_manager import MCPManager # New import

# Define minimal config example and locations
MINIMAL_CONFIG_EXAMPLE = """
# Minimal QX Configuration Example
# Place this in one of the following locations:
# 1. /etc/qx/qx.conf (lowest priority)
# 2. ~/.config/qx/qx.conf (user-level)
# 3. <project-directory>/.Q/qx.conf (highest priority)

QX_MODEL_NAME=openrouter/openai/gpt-4o
OPENROUTER_API_KEY=sk-your_openrouter_api_key_here
"""

CONFIG_LOCATIONS = """
Possible configuration file locations (in order of priority, lowest to highest):
1. /etc/qx/qx.conf
2. {user_config_path}
3. <project-directory>/.Q/qx.conf
""".format(user_config_path=QX_CONFIG_DIR / "qx.conf")


class ConfigManager:
    def __init__(self, console: Any, parent_task_group: Optional[anyio.abc.TaskGroup]): # Added parent_task_group
        self.console = console
        self.config: Dict[str, Any] = {}
        self.mcp_manager = MCPManager(console, parent_task_group) # Pass parent_task_group to MCPManager

    def load_configurations(self):
        """Loads various configurations into environment variables."""
        self._ensure_directories_exist()
        self.mcp_manager.load_mcp_configs() # Load MCP configs

        # --- Hierarchical qx.conf loading ---
        # 1. Server-level configuration
        server_conf_path = Path("/etc/qx/qx.conf")
        if server_conf_path.is_file():
            load_dotenv(dotenv_path=server_conf_path, override=False)  # Load, but don't override existing env vars

        # 2. User-level configuration
        user_conf_path = QX_CONFIG_DIR / "qx.conf"
        if user_conf_path.is_file():
            load_dotenv(dotenv_path=user_conf_path, override=True)  # Override server-level

        # 3. Project-level configuration
        cwd = Path.cwd()
        project_root = _find_project_root(str(cwd))
        if project_root:
            project_conf_path = project_root / ".Q" / "qx.conf"
            if project_conf_path.is_file():
                load_dotenv(dotenv_path=project_conf_path, override=True)  # Override all previous

        # Check for minimal required variables
        if not os.getenv("QX_MODEL_NAME") or not os.getenv("OPENROUTER_API_KEY"):
            print("Error: Missing essential configuration variables.")
            print(MINIMAL_CONFIG_EXAMPLE)
            print(CONFIG_LOCATIONS)
            sys.exit(1)

        # --- End Hierarchical qx.conf loading ---

        # 2. Load User Context (existing logic, no change)
        user_context_path = QX_CONFIG_DIR / "user.md"
        qx_user_context = ""
        if user_context_path.is_file():
            try:
                qx_user_context = user_context_path.read_text(encoding="utf-8")
            except Exception as e:
                print(f"Warning: Could not read user context file {user_context_path}: {e}")
        os.environ["QX_USER_CONTEXT"] = qx_user_context

        # Initialize project-specific variables
        qx_project_context = ""
        qx_project_files = ""

        if project_root:  # project_root is already determined above
            # Load Project Context (existing logic, no change)
            project_context_file_path = project_root / ".Q" / "project.md"
            if project_context_file_path.is_file():
                try:
                    qx_project_context = project_context_file_path.read_text(
                        encoding="utf-8"
                    )
                except Exception as e:
                    print(
                        f"Warning: Could not read project context file {project_context_file_path}: {e}"
                    )

            # Load Project Files Tree (existing logic, no change)
            if cwd == USER_HOME_DIR:
                qx_project_files = ""  # Explicitly empty if CWD is home
            else:
                # Use the imported comprehensive list
                ignore_patterns_for_tree = list(DEFAULT_TREE_IGNORE_PATTERNS)

                gitignore_path = project_root / ".gitignore"
                if gitignore_path.is_file():
                    try:
                        with open(gitignore_path, "r", encoding="utf-8") as f:
                            for line in f:
                                line = line.strip()
                                # Skip comments and empty lines
                                if not line or line.startswith("#"):
                                    continue

                                # Basic handling for .Q: if line is .Q or /.Q or /.Q/, don't add to ignore
                                if line == ".Q" or line == "/.Q" or line == "/.Q/":
                                    continue

                                # Remove leading/trailing slashes for tree's -I pattern
                                if line.startswith("/"):
                                    line = line[1:]
                                if line.endswith("/"):
                                    line = line[:-1]

                                if line:  # Add valid, non-.Q patterns
                                    ignore_patterns_for_tree.append(line)
                    except Exception as e:
                        print(
                            f"Warning: Could not read or parse .gitignore file {gitignore_path}: {e}"
                        )

                # Deduplicate and ensure .Q is not in the final list if added by broad wildcard (best effort)
                final_ignore_list = [
                    p for p in list(set(ignore_patterns_for_tree)) if p != ".Q"
                ]

                tree_command = ["tree", "-a"]
                if final_ignore_list:
                    tree_command.extend(["-I", "|".join(final_ignore_list)])

                try:
                    process = subprocess.run(
                        tree_command,
                        cwd=project_root,
                        capture_output=True,
                        text=True,
                        check=False,
                    )
                    if process.returncode == 0:
                        qx_project_files = process.stdout.strip()
                    else:
                        # Tree might return non-zero if dir is empty, but still print output.
                        # Check if output is present, otherwise log stderr.
                        if process.stdout.strip():
                            qx_project_files = process.stdout.strip()
                        else:
                            qx_project_files = f"Error generating project tree (code {process.returncode}): {process.stderr.strip()}"
                except FileNotFoundError:
                    qx_project_files = "Error: 'tree' command not found. Please ensure it is installed and in PATH."
                except Exception as e:
                    qx_project_files = f"Error executing 'tree' command: {e}"

        os.environ["QX_PROJECT_CONTEXT"] = qx_project_context
        os.environ["QX_PROJECT_FILES"] = qx_project_files


    def _ensure_directories_exist(self):
        """Ensures necessary directories exist."""
        QX_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        QX_SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
        # Note: /etc/qx is a system directory and should not be created by the application.
        # It's assumed to exist or be managed by the system's package manager.


# The `load_runtime_configurations` function is now part of ConfigManager class
# and should not be called directly from global scope or `if __name__ == "__main__"`
# unless it's for testing the class itself.

# The `if __name__ == "__main__"` block should be updated to instantiate ConfigManager
# and call its methods.

if __name__ == "__main__":
    # This block needs to be updated to reflect the class structure
    # For now, commenting out to avoid breaking existing tests if run directly.
    # A proper test setup would involve instantiating ConfigManager.
    print("This module is now part of a class structure. Direct execution for testing needs update.")
    print("Please run tests via the main application entry point or a dedicated test suite.")

    # Example of how it *would* be used in a test context:
    # from rich.console import Console
    # test_console = Console()
    # manager = ConfigManager(test_console)
    # manager.load_configurations()
    # print(f"QX_MODEL_NAME: {os.getenv('QX_MODEL_NAME')}")
