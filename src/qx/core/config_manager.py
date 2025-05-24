import os
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv

from qx.core.constants import DEFAULT_TREE_IGNORE_PATTERNS
from qx.core.paths import USER_HOME_DIR, _find_project_root, QX_CONFIG_DIR

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


def load_runtime_configurations():
    """
    Loads various configurations into environment variables.
    - Ensures ~/.config/qx directory exists.
    - Hierarchical qx.conf loading: /etc/qx/qx.conf < ~/.config/qx/qx.conf < project_root/.Q/qx.conf
    - User context: ~/.config/qx/user.md -> QX_USER_CONTEXT
    - Project context: project_root/.Q/project.md -> QX_PROJECT_CONTEXT
    - Project files tree: project_root tree -> QX_PROJECT_FILES
    """
    # 0. Ensure QX config directory exists
    try:
        os.makedirs(QX_CONFIG_DIR, exist_ok=True)
    except OSError as e:
        print(f"Warning: Could not create QX config directory {QX_CONFIG_DIR}: {e}")

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


if __name__ == "__main__":
    print(f"Current PWD: {Path.cwd()}")
    print(f"User Home: {USER_HOME_DIR}")
    print(f"QX Config Dir (from paths.py): {QX_CONFIG_DIR}")

    # --- Setup for testing ---
    # Create dummy directories for testing
    test_etc_qx_dir = Path("/tmp/etc/qx")
    test_user_config_dir = Path("/tmp/user_home/.config/qx")
    test_project_root_dir = Path("/tmp/test_project")
    test_project_q_dir = test_project_root_dir / ".Q"

    os.makedirs(test_etc_qx_dir, exist_ok=True)
    os.makedirs(test_user_config_dir, exist_ok=True)
    os.makedirs(test_project_q_dir, exist_ok=True)

    # Define dummy config file paths
    dummy_server_conf = test_etc_qx_dir / "qx.conf"
    dummy_user_conf = test_user_config_dir / "qx.conf"
    dummy_project_conf = test_project_q_dir / "qx.conf"

    # --- Test Case 1: All configs present, project config should win ---
    print("\n--- Test Case 1: All configs present, project config wins ---")
    dummy_server_conf.write_text("QX_MODEL_NAME=server_model\nOPENROUTER_API_KEY=server_key\nCOMMON_VAR=server_common\n")
    dummy_user_conf.write_text("QX_MODEL_NAME=user_model\nOPENROUTER_API_KEY=user_key\nCOMMON_VAR=user_common\nUSER_ONLY_VAR=user_val\n")
    dummy_project_conf.write_text("QX_MODEL_NAME=project_model\nOPENROUTER_API_KEY=project_key\nCOMMON_VAR=project_common\nPROJECT_ONLY_VAR=project_val\n")

    # Simulate being in the project directory
    original_cwd = Path.cwd()
    os.chdir(test_project_root_dir)

    # Clear environment variables before loading to ensure a clean test
    # Only clear variables that might be set by previous runs or system
    for var in ["QX_MODEL_NAME", "OPENROUTER_API_KEY", "COMMON_VAR", "USER_ONLY_VAR", "PROJECT_ONLY_VAR"]:
        if var in os.environ:
            del os.environ[var]

    load_runtime_configurations()
    print(f"QX_MODEL_NAME: {os.getenv('QX_MODEL_NAME')}")  # Should be project_model
    print(f"OPENROUTER_API_KEY: {os.getenv('OPENROUTER_API_KEY')}")  # Should be project_key
    print(f"COMMON_VAR: {os.getenv('COMMON_VAR')}")  # Should be project_common
    print(f"USER_ONLY_VAR: {os.getenv('USER_ONLY_VAR')}")  # Should be user_val
    print(f"PROJECT_ONLY_VAR: {os.getenv('PROJECT_ONLY_VAR')}")  # Should be project_val
    os.chdir(original_cwd)

    # --- Test Case 2: Only user config present ---
    print("\n--- Test Case 2: Only user config present ---")
    dummy_server_conf.unlink(missing_ok=True)
    dummy_project_conf.unlink(missing_ok=True)
    dummy_user_conf.write_text("QX_MODEL_NAME=user_model_only\nOPENROUTER_API_KEY=user_key_only\n")

    # Clear environment variables
    for var in ["QX_MODEL_NAME", "OPENROUTER_API_KEY", "COMMON_VAR", "USER_ONLY_VAR", "PROJECT_ONLY_VAR"]:
        if var in os.environ:
            del os.environ[var]

    load_runtime_configurations()
    print(f"QX_MODEL_NAME: {os.getenv('QX_MODEL_NAME')}")  # Should be user_model_only
    print(f"OPENROUTER_API_KEY: {os.getenv('OPENROUTER_API_KEY')}")  # Should be user_key_only

    # --- Test Case 3: Only server config present ---
    print("\n--- Test Case 3: Only server config present ---")
    dummy_user_conf.unlink(missing_ok=True)
    dummy_server_conf.write_text("QX_MODEL_NAME=server_model_only\nOPENROUTER_API_KEY=server_key_only\n")

    # Clear environment variables
    for var in ["QX_MODEL_NAME", "OPENROUTER_API_KEY", "COMMON_VAR", "USER_ONLY_VAR", "PROJECT_ONLY_VAR"]:
        if var in os.environ:
            del os.environ[var]

    load_runtime_configurations()
    print(f"QX_MODEL_NAME: {os.getenv('QX_MODEL_NAME')}")  # Should be server_model_only
    print(f"OPENROUTER_API_KEY: {os.getenv('OPENROUTER_API_KEY')}")  # Should be server_key_only

    # --- Test Case 4: Missing essential variables (should cause exit) ---
    print("\n--- Test Case 4: Missing essential variables (should cause exit) ---")
    dummy_server_conf.unlink(missing_ok=True)
    dummy_user_conf.unlink(missing_ok=True)
    dummy_project_conf.unlink(missing_ok=True)

    # Clear environment variables
    for var in ["QX_MODEL_NAME", "OPENROUTER_API_KEY", "COMMON_VAR", "USER_ONLY_VAR", "PROJECT_ONLY_VAR"]:
        if var in os.environ:
            del os.environ[var]

    try:
        load_runtime_configurations()
    except SystemExit as e:
        print(f"Caught SystemExit as expected: {e}")
    print("Script continued after expected exit (for testing purposes).")

    # --- Cleanup ---
    dummy_server_conf.unlink(missing_ok=True)
    dummy_user_conf.unlink(missing_ok=True)
    dummy_project_conf.unlink(missing_ok=True)

    # Clean up dummy directories. rmdir only works on empty directories.
    # Need to remove files first, then directories.
    # For robustness in testing, it's better to use shutil.rmtree if available, but not in this context.
    # So, I'll just unlink the files and leave the empty dirs if they are not empty.
    # The test setup creates them with exist_ok=True, so it's fine if they persist.
    # If they were created solely for this test, they would be empty after unlinking.
    # For now, I'll just unlink the files.

    # Attempt to remove directories if they are empty
    try:
        test_etc_qx_dir.rmdir()
    except OSError:
        pass
    try:
        test_user_config_dir.rmdir()
    except OSError:
        pass
    try:
        test_project_q_dir.rmdir()
    except OSError:
        pass
    try:
        test_project_root_dir.rmdir()
    except OSError:
        pass
