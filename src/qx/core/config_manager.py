import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional, List

from dotenv import load_dotenv, set_key
import anyio

from qx.core.constants import DEFAULT_TREE_IGNORE_PATTERNS
from qx.core.paths import (
    USER_HOME_DIR,
    _find_project_root,
    QX_CONFIG_DIR,
    QX_SESSIONS_DIR,
)
from qx.core.mcp_manager import MCPManager

# Define minimal config example and locations
MINIMAL_CONFIG_EXAMPLE = """
# Minimal Qx Configuration Example
# Place this in one of the following locations:
# 1. /etc/qx/qx.conf (lowest priority)
# 2. ~/.config/qx/qx.conf (user-level)
# 3. <project-directory>/.Q/qx.conf (highest priority)

# Model Configuration (LiteLLM format)
QX_MODEL_NAME=openrouter/anthropic/claude-3.5-sonnet

# API Key (choose one based on your provider)
OPENROUTER_API_KEY=sk-or-v1-your_openrouter_api_key_here
# OPENAI_API_KEY=sk-your_openai_api_key_here
# ANTHROPIC_API_KEY=sk-ant-your_anthropic_api_key_here

# Optional settings
QX_MODEL_TEMPERATURE=0.7
QX_MODEL_MAX_TOKENS=4096
QX_ENABLE_STREAMING=true
QX_SHOW_SPINNER=true
QX_SHOW_THINKING=true
"""

CONFIG_LOCATIONS = """
Possible configuration file locations (in order of priority, lowest to highest):
1. /etc/qx/qx.conf
2. {user_config_path}
3. <project-directory>/.Q/qx.conf
""".format(user_config_path=QX_CONFIG_DIR / "qx.conf")


class ConfigManager:
    def __init__(self, console: Any, parent_task_group: Optional[anyio.abc.TaskGroup]):
        self.console = console
        self.config: Dict[str, Any] = {}
        self.mcp_manager = MCPManager(console, parent_task_group)

    def _load_dotenv_if_exists(self, path: Path, override: bool = False):
        """Helper to load .env file if it exists."""
        if path.is_file():
            load_dotenv(dotenv_path=path, override=override)

    def _export_qx_configurations(self, original_env: Dict[str, str]):
        """Explicitly export all configurations loaded from config files as environment variables."""
        # Get all new environment variables that were loaded by dotenv
        current_env = dict(os.environ)
        new_env_vars = {k: v for k, v in current_env.items() if k not in original_env}

        # Explicitly ensure all newly loaded variables are exported to subprocesses
        for var, value in new_env_vars.items():
            os.environ[var] = value

    def get_writable_config_path(self) -> Path:
        """
        Determines the appropriate config file path to write to.
        If inside a project with an existing .Q/qx.conf, uses that.
        Otherwise, falls back to the user-level config file.
        """
        project_root = _find_project_root(str(Path.cwd()))
        if project_root:
            project_config_path = project_root / ".Q" / "qx.conf"
            if project_config_path.is_file():
                return project_config_path

        # Fallback to user-level config
        user_config_path = QX_CONFIG_DIR / "qx.conf"
        return user_config_path

    def set_config_value(self, key: str, value: str):
        """
        Sets a key-value pair in the appropriate qx.conf file.
        Creates the file and directories if they don't exist.
        """
        config_path = self.get_writable_config_path()

        # Ensure the directory exists
        config_path.parent.mkdir(parents=True, exist_ok=True)

        # set_key will create the file if it doesn't exist, and update/add the key
        set_key(dotenv_path=str(config_path), key_to_set=key, value_to_set=value)

        # Also update the current environment so the change is reflected immediately
        os.environ[key] = value

    def _get_rg_ignore_patterns(self, project_root: Path) -> List[str]:
        """
        Generates a list of ignore patterns for `rg` command,
        excluding .Q and its contents, and incorporating .gitignore.
        """
        ignore_patterns = []

        # Add default ignore patterns, ensuring .Q is never ignored
        for p in DEFAULT_TREE_IGNORE_PATTERNS:
            if not (
                p == ".Q"
                or p == "/.Q"
                or p == ".Q/"
                or p == "/.Q/"
                or p.startswith(".Q/")
                or p.startswith("/.Q/")
            ):
                ignore_patterns.append(p)

        # Add patterns from .gitignore, ensuring .Q is never ignored
        gitignore_path = project_root / ".gitignore"
        if gitignore_path.is_file():
            try:
                with open(gitignore_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            if not (
                                line == ".Q"
                                or line == "/.Q"
                                or line == ".Q/"
                                or line == "/.Q/"
                                or line.startswith(".Q/")
                                or line.startswith("/.Q/")
                            ):
                                ignore_patterns.append(line)
            except Exception as e:
                from qx.cli.theme import themed_console

                themed_console.print(
                    f"[warning]Warning: Could not read or parse .gitignore file {gitignore_path}: {e}[/]"
                )

        # Deduplicate the final list
        return list(set(ignore_patterns))

    def load_configurations(self):
        """Loads various configurations into environment variables."""
        self._ensure_directories_exist()
        self.mcp_manager.load_mcp_configs()

        # Store original environment variables to preserve user-set env vars
        original_env = dict(os.environ)

        # --- Hierarchical qx.conf loading ---
        # Load in order: system -> user -> project
        # Each level can override the previous, but environment variables have final priority

        # 1. Server-level configuration (lowest priority)
        self._load_dotenv_if_exists(Path("/etc/qx/qx.conf"), override=False)

        # 2. User-level configuration (overrides system settings)
        self._load_dotenv_if_exists(QX_CONFIG_DIR / "qx.conf", override=True)

        # 3. Project-level configuration (overrides user & system settings)
        cwd = Path.cwd()
        project_root = _find_project_root(str(cwd))
        if project_root:
            project_config_path = project_root / ".Q" / "qx.conf"
            self._check_project_config_safety(project_config_path)
            self._load_dotenv_if_exists(project_config_path, override=True)

        # 4. Restore original environment variables (highest priority)
        # This ensures that environment variables set by the user are never overridden
        for key, value in original_env.items():
            os.environ[key] = value

        # Explicitly ensure all QX_ prefixed configurations are in environment
        self._export_qx_configurations(original_env)

        # Set default for QX_SHOW_SPINNER if not set
        if os.getenv("QX_SHOW_SPINNER") is None:
            os.environ["QX_SHOW_SPINNER"] = "true"

        # Check for minimal required variables
        model_name = os.getenv("QX_MODEL_NAME")
        api_keys = [
            "OPENROUTER_API_KEY",
            "OPENAI_API_KEY",
            "ANTHROPIC_API_KEY",
            "AZURE_API_KEY",
            "GOOGLE_API_KEY",
        ]
        has_api_key = any(os.getenv(key) for key in api_keys)

        if not model_name or not has_api_key:
            from qx.cli.theme import themed_console

            themed_console.print(
                "[error]Error: Missing essential configuration variables.[/]"
            )
            if not model_name:
                themed_console.print("Missing QX_MODEL_NAME")
            if not has_api_key:
                themed_console.print(
                    f"Missing API key. Set one of: {', '.join(api_keys)}"
                )
            themed_console.print(MINIMAL_CONFIG_EXAMPLE)
            themed_console.print(CONFIG_LOCATIONS)
            sys.exit(1)

        # --- End Hierarchical qx.conf loading ---

        # Load User Context
        user_context_path = QX_CONFIG_DIR / "user.md"
        qx_user_context = ""
        if user_context_path.is_file():
            try:
                qx_user_context = user_context_path.read_text(encoding="utf-8")
            except Exception as e:
                from qx.cli.theme import themed_console

                themed_console.print(
                    f"[warning]Warning: Could not read user context file {user_context_path}: {e}[/]"
                )
        os.environ["QX_USER_CONTEXT"] = qx_user_context

        # Initialize project-specific variables
        qx_project_context = ""
        qx_project_files = ""

        if project_root:
            # Load Project Context
            project_context_file_path = project_root / ".Q" / "project.md"
            if project_context_file_path.is_file():
                try:
                    qx_project_context = project_context_file_path.read_text(
                        encoding="utf-8"
                    )
                except Exception as e:
                    from qx.cli.theme import themed_console

                    themed_console.print(
                        f"[warning]Warning: Could not read project context file {project_context_file_path}: {e}[/]"
                    )

            # Load Project Files Tree using rg
            if cwd == USER_HOME_DIR:
                qx_project_files = ""  # Explicitly empty if CWD is home
            else:
                ignore_patterns = self._get_rg_ignore_patterns(project_root)

                temp_ignore_file_path = None
                try:
                    with tempfile.NamedTemporaryFile(
                        mode="w", delete=False, encoding="utf-8"
                    ) as temp_ignore_file:
                        temp_ignore_file.write("\n".join(ignore_patterns))
                        temp_ignore_file_path = Path(temp_ignore_file.name)

                    rg_command = [
                        "rg",
                        "--files",
                        "--hidden",
                        "--no-ignore-vcs",  # Crucial: tells rg to ignore .gitignore and other VCS ignore files
                        "--ignore-file",
                        str(temp_ignore_file_path),
                        str(
                            project_root
                        ),  # Explicitly pass project_root as the search path
                    ]

                    process = subprocess.run(
                        rg_command,
                        cwd=project_root,
                        capture_output=True,
                        text=True,
                        check=False,
                    )
                    if process.returncode == 0:
                        qx_project_files = process.stdout.strip()
                    else:
                        # rg might return non-zero if no files are found, but still print output.
                        # Check if output is present, otherwise log stderr.
                        if process.stdout.strip():
                            qx_project_files = process.stdout.strip()
                        else:
                            from qx.cli.theme import themed_console

                            themed_console.print(
                                f"[warning]Warning: rg command returned non-zero exit code {process.returncode}. Stderr: {process.stderr.strip()}[/]"
                            )
                            qx_project_files = f"Error generating project tree (code {process.returncode}): {process.stderr.strip()}"
                except FileNotFoundError:
                    from qx.cli.theme import themed_console

                    themed_console.print(
                        "[error]Error: 'rg' command not found. Please ensure it is installed and in PATH.[/]"
                    )
                    qx_project_files = "Error: 'rg' command not found. Please ensure it is installed and in PATH."
                except Exception as e:
                    themed_console.print(f"[error]Error executing 'rg' command: {e}[/]")
                    qx_project_files = f"Error executing 'rg' command: {e}"
                finally:
                    if temp_ignore_file_path and temp_ignore_file_path.exists():
                        os.remove(temp_ignore_file_path)

        os.environ["QX_PROJECT_CONTEXT"] = qx_project_context
        os.environ["QX_PROJECT_FILES"] = qx_project_files

    def _check_project_config_safety(self, project_config_path: Path):
        """
        Safety check to ensure .Q/qx.conf does not contain any API keys.
        Exits the application if any variables containing 'KEY' are found.
        """
        if not project_config_path.is_file():
            return

        try:
            with open(project_config_path, "r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    # Skip empty lines and comments
                    if not line or line.startswith("#"):
                        continue

                    # Check if line contains a variable assignment with 'KEY' in the name
                    if "=" in line:
                        var_name = line.split("=")[0].strip()
                        if "KEY" in var_name.upper():
                            from qx.cli.theme import themed_console

                            themed_console.print(
                                f"[error]SECURITY ERROR: API key detected in .Q/qx.conf[/]\n"
                                f"File: {project_config_path}\n"
                                f"Line {line_num}: {var_name}\n\n"
                                f"[error]API keys should NEVER be stored in .Q/qx.conf as this file[/]\n"
                                f"[error]may be committed to version control.[/]\n\n"
                                f"Please move API keys to:\n"
                                f"- ~/.config/qx/qx.conf (user-level config)\n"
                                f"- Environment variables\n"
                            )
                            sys.exit(1)
        except Exception as e:
            from qx.cli.theme import themed_console

            themed_console.print(
                f"[warning]Warning: Could not read project config file {project_config_path}: {e}[/]"
            )

    def _ensure_directories_exist(self):
        """Ensures necessary directories exist."""
        QX_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        QX_SESSIONS_DIR.mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    print(
        "This module is now part of a class structure. Direct execution for testing needs update."
    )
    print(
        "Please run tests via the main application entry point or a dedicated test suite."
    )
