import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional, List

from dotenv import load_dotenv
import anyio

from qx.core.constants import DEFAULT_TREE_IGNORE_PATTERNS
from qx.core.paths import USER_HOME_DIR, _find_project_root, QX_CONFIG_DIR, QX_SESSIONS_DIR
from qx.core.mcp_manager import MCPManager

# Define minimal config example and locations
MINIMAL_CONFIG_EXAMPLE = """
# Minimal QX Configuration Example
# Place this in one of the following locations:
# 1. /etc/qx/qx.conf (lowest priority)
# 2. ~/.config/qx/qx.conf (user-level)
# 3. <project-directory>/.Q/qx.conf (highest priority)

QX_MODEL_NAME=openrouter/openai/gpt-4o
OPENROUTER_API_KEY=sk-your_openrouter_api_key_here
QX_MODEL_PROVIDER=Together # Optional: Specify preferred provider(s), comma-separated
QX_ALLOW_PROVIDER_FALLBACK=False # Optional: Set to true/false to allow/disallow fallbacks
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

    def _get_rg_ignore_patterns(self, project_root: Path) -> List[str]:
        """
        Generates a list of ignore patterns for `rg` command,
        excluding .Q and its contents, and incorporating .gitignore.
        """
        ignore_patterns = []

        # Add default ignore patterns, ensuring .Q is never ignored
        for p in DEFAULT_TREE_IGNORE_PATTERNS:
            if not (p == ".Q" or p == "/.Q" or p == ".Q/" or p == "/.Q/" or p.startswith(".Q/") or p.startswith("/.Q/")):
                ignore_patterns.append(p)

        # Add patterns from .gitignore, ensuring .Q is never ignored
        gitignore_path = project_root / ".gitignore"
        if gitignore_path.is_file():
            try:
                with open(gitignore_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            if not (line == ".Q" or line == "/.Q" or line == ".Q/" or line == "/.Q/" or line.startswith(".Q/") or line.startswith("/.Q/")):
                                ignore_patterns.append(line)
            except Exception as e:
                from rich.console import Console
                Console().print(f"[yellow]Warning: Could not read or parse .gitignore file {gitignore_path}: {e}[/yellow]")

        # Deduplicate the final list
        return list(set(ignore_patterns))

    def load_configurations(self):
        """Loads various configurations into environment variables."""
        self._ensure_directories_exist()
        self.mcp_manager.load_mcp_configs()

        # Store original environment to track what we've loaded
        original_env = dict(os.environ)

        # --- Hierarchical qx.conf loading ---
        # 1. Server-level configuration (lowest priority)
        self._load_dotenv_if_exists(Path("/etc/qx/qx.conf"), override=False)

        # 2. User-level configuration
        self._load_dotenv_if_exists(QX_CONFIG_DIR / "qx.conf", override=True)

        # 3. Project-level configuration (highest priority)
        cwd = Path.cwd()
        project_root = _find_project_root(str(cwd))
        if project_root:
            self._load_dotenv_if_exists(project_root / ".Q" / "qx.conf", override=True)

        # Explicitly ensure all QX_ prefixed configurations are in environment
        self._export_qx_configurations(original_env)

        # Check for minimal required variables
        if not os.getenv("QX_MODEL_NAME") or not os.getenv("OPENROUTER_API_KEY"):
            from rich.console import Console
            rich_console = Console()
            rich_console.print("[red]Error: Missing essential configuration variables.[/red]")
            rich_console.print(MINIMAL_CONFIG_EXAMPLE)
            rich_console.print(CONFIG_LOCATIONS)
            sys.exit(1)

        # --- End Hierarchical qx.conf loading ---

        # Load User Context
        user_context_path = QX_CONFIG_DIR / "user.md"
        qx_user_context = ""
        if user_context_path.is_file():
            try:
                qx_user_context = user_context_path.read_text(encoding="utf-8")
            except Exception as e:
                Console().print(f"[yellow]Warning: Could not read user context file {user_context_path}: {e}[/yellow]")
        os.environ["QX_USER_CONTEXT"] = qx_user_context

        # Initialize project-specific variables
        qx_project_context = ""
        qx_project_files = ""

        if project_root:
            # Load Project Context
            project_context_file_path = project_root / ".Q" / "project.md"
            if project_context_file_path.is_file():
                try:
                    qx_project_context = project_context_file_path.read_text(encoding="utf-8")
                except Exception as e:
                    Console().print(f"[yellow]Warning: Could not read project context file {project_context_file_path}: {e}[/yellow]")

            # Load Project Files Tree using rg
            if cwd == USER_HOME_DIR:
                qx_project_files = ""  # Explicitly empty if CWD is home
            else:
                ignore_patterns = self._get_rg_ignore_patterns(project_root)

                temp_ignore_file_path = None
                try:
                    with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8') as temp_ignore_file:
                        temp_ignore_file.write("\n".join(ignore_patterns))
                    temp_ignore_file_path = Path(temp_ignore_file.name)

                    rg_command = [
                        "rg",
                        "--files",
                        "--hidden",
                        "--no-ignore-vcs", # Crucial: tells rg to ignore .gitignore and other VCS ignore files
                        "--ignore-file", str(temp_ignore_file_path),
                        str(project_root) # Explicitly pass project_root as the search path
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
                            Console().print(f"[yellow]Warning: rg command returned non-zero exit code {process.returncode}. Stderr: {process.stderr.strip()}[/yellow]")
                            qx_project_files = f"Error generating project tree (code {process.returncode}): {process.stderr.strip()}"
                except FileNotFoundError:
                    Console().print("[red]Error: 'rg' command not found. Please ensure it is installed and in PATH.[/red]")
                    qx_project_files = "Error: 'rg' command not found. Please ensure it is installed and in PATH."
                except Exception as e:
                    Console().print(f"[red]Error executing 'rg' command: {e}[/red]")
                    qx_project_files = f"Error executing 'rg' command: {e}"
                finally:
                    if temp_ignore_file_path and temp_ignore_file_path.exists():
                        os.remove(temp_ignore_file_path)

        os.environ["QX_PROJECT_CONTEXT"] = qx_project_context
        os.environ["QX_PROJECT_FILES"] = qx_project_files

    def _ensure_directories_exist(self):
        """Ensures necessary directories exist."""
        QX_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        QX_SESSIONS_DIR.mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    print("This module is now part of a class structure. Direct execution for testing needs update.")
    print("Please run tests via the main application entry point or a dedicated test suite.")
