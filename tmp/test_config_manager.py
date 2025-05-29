import os
import subprocess
import sys
import tempfile
from pathlib import Path

# Add the src directory to the Python path to allow importing qx modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from qx.core.config_manager import ConfigManager
from qx.core.constants import DEFAULT_TREE_IGNORE_PATTERNS # Import for debugging
from qx.core.paths import USER_HOME_DIR, _find_project_root, QX_CONFIG_DIR, QX_SESSIONS_DIR # Import for debugging
from rich.console import Console
import anyio

async def main():
    console = Console()
    async with anyio.create_task_group() as tg:
        manager = ConfigManager(console, tg)
        manager.load_configurations()

    print("\n--- QX_PROJECT_FILES Content ---")
    project_files = os.getenv("QX_PROJECT_FILES")
    if project_files:
        print(project_files)
    else:
        print("QX_PROJECT_FILES is empty or not set.")

    print("\n--- Debugging rg command construction ---")
    cwd = Path.cwd()
    project_root = _find_project_root(str(cwd))

    if project_root:
        ignore_patterns_for_rg = list(DEFAULT_TREE_IGNORE_PATTERNS)
        gitignore_path = project_root / ".gitignore"
        if gitignore_path.is_file():
            try:
                with open(gitignore_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith("#"):
                            continue
                        if line == ".Q" or line == "/.Q" or line == "/.Q/":
                            continue
                        if line: # Add valid, non-.Q patterns
                            ignore_patterns_for_rg.append(line)
            except Exception as e:
                print(f"Warning: Could not read or parse .gitignore file {gitignore_path}: {e}")

        final_ignore_list = [p for p in list(set(ignore_patterns_for_rg)) if p != ".Q"]
        print(f"Final ignore list for rg: {final_ignore_list}")

        temp_ignore_file_path = None
        try:
            with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8') as temp_ignore_file:
                temp_ignore_file.write("\n".join(final_ignore_list))
            temp_ignore_file_path = Path(temp_ignore_file.name)

            rg_command = [
                "rg",
                "--files",
                "--hidden",
                "--no-ignore-vcs", # Crucial: tells rg to ignore .gitignore and other VCS ignore files
                "--ignore-file", str(temp_ignore_file_path),
                str(project_root) # Explicitly pass project_root as the search path
            ]
            print(f"rg command to be executed: {' '.join(rg_command)}")

            process = subprocess.run(
                rg_command,
                cwd=project_root,
                capture_output=True,
                text=True,
                check=False,
            )
            if process.returncode == 0:
                print("rg direct output:\n", process.stdout.strip())
            else:
                print(f"rg direct error (code {process.returncode}): {process.stderr.strip()}")
        finally:
            if temp_ignore_file_path and temp_ignore_file_path.exists():
                os.remove(temp_ignore_file_path)

    print("\n--- QX_MODEL_NAME (from config) ---")
    print(os.getenv("QX_MODEL_NAME"))

    print("\n--- OPENROUTER_API_KEY (from config) ---")
    api_key = os.getenv("OPENROUTER_API_KEY")
    if api_key:
        print(f"OPENROUTER_API_KEY is set (starts with {api_key[:5]}...)")
    else:
        print("OPENROUTER_API_KEY is not set.")

if __name__ == "__main__":
    anyio.run(main)
