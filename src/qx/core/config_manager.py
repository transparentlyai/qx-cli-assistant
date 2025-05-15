import os
import subprocess
from pathlib import Path

from dotenv import load_dotenv

from src.qx.core.constants import DEFAULT_TREE_IGNORE_PATTERNS  # Updated import

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


def load_runtime_configurations():
    """
    Loads various configurations into environment variables.
    - User-specific .env: ~/.config/q/q.conf
    - Project-specific .env: project_root/.env
    - User context: ~/.config/q/user.md -> QX_USER_CONTEXT
    - Project context: project_root/.Q/project.md -> QX_PROJECT_CONTEXT
    - Project files tree: project_root tree -> QX_PROJECT_FILES
    """
    # 1. Load User-Specific Dotenv Configuration
    user_conf_path = USER_HOME_DIR / ".config" / "q" / "q.conf"
    if user_conf_path.is_file():
        load_dotenv(dotenv_path=user_conf_path, override=True)

    # 2. Load User Context
    user_context_path = USER_HOME_DIR / ".config" / "q" / "user.md"
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

    cwd = Path.cwd()
    project_root = _find_project_root(str(cwd))

    if project_root:
        # Load Project-Specific .env file
        # This is loaded after q.conf and with override=True, so project .env vars take precedence.
        project_env_path = project_root / ".env"
        if project_env_path.is_file():
            load_dotenv(dotenv_path=project_env_path, override=True)

        # Load Project Context
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

        # Load Project Files Tree
        # Rule: "if the user is at the home directory, then do not load the QX_PROJECT_FILES."
        # This check should be against CWD, not project_root.
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


if __name__ == "__main__":
    # Example usage for testing
    print(f"Current PWD: {Path.cwd()}")
    print(f"User Home: {USER_HOME_DIR}")

    # Create dummy files for testing if they don't exist
    dummy_q_conf = USER_HOME_DIR / ".config" / "q" / "q.conf"
    dummy_user_md = USER_HOME_DIR / ".config" / "q" / "user.md"

    dummy_q_conf.parent.mkdir(parents=True, exist_ok=True)
    if not dummy_q_conf.exists():
        dummy_q_conf.write_text("TEST_Q_CONF_VAR=hello_from_q_conf\n")
        print(f"Created dummy {dummy_q_conf}")

    if not dummy_user_md.exists():
        dummy_user_md.write_text("This is the dummy user context from user.md.")
        print(f"Created dummy {dummy_user_md}")

    # Simulate a project .env for testing
    # In a real scenario, this would be in the project root.
    # For this test, we'll create one in the current dir if it's a "project"
    # or skip if we can't determine a project root easily for the test script.
    current_dir_as_project_root = _find_project_root(str(Path.cwd()))
    if current_dir_as_project_root:
        dummy_project_env = current_dir_as_project_root / ".env"
        if not dummy_project_env.exists():
            dummy_project_env.write_text(
                "TEST_PROJECT_ENV_VAR=hello_from_project_env\n"
                "QX_MODEL_NAME=project_model_override\n" # Example of overriding
            )
            print(f"Created dummy {dummy_project_env} for testing")

    load_runtime_configurations()

    print(f"TEST_Q_CONF_VAR: {os.getenv('TEST_Q_CONF_VAR')}")
    print(f"TEST_PROJECT_ENV_VAR: {os.getenv('TEST_PROJECT_ENV_VAR')}")
    print(f"QX_MODEL_NAME (after all loads): {os.getenv('QX_MODEL_NAME')}")
    print(f"QX_USER_CONTEXT: '{os.getenv('QX_USER_CONTEXT')}'")
    print(f"QX_PROJECT_CONTEXT: '{os.getenv('QX_PROJECT_CONTEXT')}'")
    print(f"QX_PROJECT_FILES:\n{os.getenv('QX_PROJECT_FILES')}")