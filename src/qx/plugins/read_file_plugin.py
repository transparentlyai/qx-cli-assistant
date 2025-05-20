import logging
import os
from pathlib import Path
from typing import Optional, Tuple

from pydantic import BaseModel, Field
from pydantic_ai import RunContext  # Import RunContext

from qx.core.context import QXToolDependencies  # Import dependencies context
from qx.core.paths import USER_HOME_DIR, _find_project_root
from qx.core.user_prompts import request_confirmation

logger = logging.getLogger(__name__)


# --- Duplicated from src/qx/tools/file_operations_base.py ---
def is_path_allowed(
    resolved_path: Path, project_root: Optional[Path], user_home: Path
) -> bool:
    """
    Checks if a given resolved path is allowed for file operations.
    A path is allowed if it is within the project_root (or its .Q subdirectory)
    OR if it is within the user_home directory.
    If project_root is defined, checks against it are performed first.
    """
    path_to_check = resolved_path.resolve()

    if project_root:
        project_root_abs = project_root.resolve()
        if (
            path_to_check == project_root_abs
            or project_root_abs in path_to_check.parents
        ):
            return True
        dot_q_path = (project_root_abs / ".Q").resolve()
        if path_to_check == dot_q_path or dot_q_path in path_to_check.parents:
            return True

    user_home_abs = user_home.resolve()
    if path_to_check == user_home_abs or user_home_abs in path_to_check.parents:
        return True
    return False


# --- End of duplicated is_path_allowed ---


# --- Copied and adapted from src/qx/tools/read_file.py (read_file_impl) ---
def _read_file_core_logic(path_str: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Core logic to read file content. Does not handle approval.
    Returns (content, error_message). content is None if error.
    """
    try:
        expanded_path_str = os.path.expanduser(path_str)
        current_working_dir = Path.cwd()
        project_root = _find_project_root(str(current_working_dir))
        absolute_path = Path(expanded_path_str)
        if not absolute_path.is_absolute():
            absolute_path = current_working_dir.joinpath(expanded_path_str).resolve()
        else:
            absolute_path = absolute_path.resolve()

        if not is_path_allowed(absolute_path, project_root, USER_HOME_DIR):
            logger.error(
                f"Read access denied by policy for path: {absolute_path}. "
                f"Project root: {project_root}, User home: {USER_HOME_DIR}"
            )
            return None, f"Error: Access denied by policy for path: {absolute_path}"

        if not absolute_path.is_file():
            logger.error(f"File not found or not a file: {absolute_path}")
            return (
                None,
                f"Error: File not found or is not a regular file: {absolute_path}",
            )

        content = absolute_path.read_text(encoding="utf-8")
        logger.info(f"Successfully read file: {absolute_path}")
        return content, None

    except FileNotFoundError:
        logger.error(f"File not found (exception): {path_str}")
        return None, f"Error: File not found: {path_str}"
    except PermissionError:
        logger.error(f"Permission denied reading file: {path_str}")
        return None, f"Error: Permission denied reading file: {path_str}"
    except IsADirectoryError:
        logger.error(f"Path is a directory, not a file: {path_str}")
        return None, f"Error: Path is a directory, not a file: {path_str}"
    except Exception as e:
        logger.error(f"Error reading file '{path_str}': {e}", exc_info=True)
        return None, f"Error reading file '{path_str}': {e}"


# --- End of _read_file_core_logic ---


class ReadFilePluginInput(BaseModel):
    """Input model for the ReadFilePluginTool."""

    path: str = Field(
        ...,
        description="The path to the file to be read. Can be relative, absolute, or start with '~'.",
    )
    # console field removed


class ReadFilePluginOutput(BaseModel):
    """Output model for the ReadFilePluginTool."""

    path: str = Field(
        description="The (expanded) path of the file attempted to be read."
    )
    content: Optional[str] = Field(
        None, description="The content of the file if successful, otherwise None."
    )
    error: Optional[str] = Field(
        None, description="Error message if the operation failed or was denied."
    )


def read_file_tool(
    ctx: RunContext[QXToolDependencies],  # Added RunContext
    args: ReadFilePluginInput,
) -> ReadFilePluginOutput:
    """
    PydanticAI Tool to read the content of a specified file.
    Path validation ensures reads are restricted to the project directory or user's home directory.
    If the file is outside the project but within the user's home directory, user confirmation is requested.
    """
    console = ctx.deps.console  # Get console from context

    original_path_arg = args.path
    expanded_path_arg = os.path.expanduser(original_path_arg)

    current_working_dir = Path.cwd()
    project_root = _find_project_root(str(current_working_dir))

    absolute_path_to_evaluate = Path(expanded_path_arg)
    if not absolute_path_to_evaluate.is_absolute():
        absolute_path_to_evaluate = current_working_dir.joinpath(
            expanded_path_arg
        ).resolve()
    else:
        absolute_path_to_evaluate = absolute_path_to_evaluate.resolve()

    if not is_path_allowed(absolute_path_to_evaluate, project_root, USER_HOME_DIR):
        err_msg = (
            f"Error: Access denied by policy for path: {absolute_path_to_evaluate}"
        )
        logger.error(
            f"Read access denied by policy (plugin pre-check) for path: {absolute_path_to_evaluate}"
        )
        return ReadFilePluginOutput(path=expanded_path_arg, content=None, error=err_msg)

    needs_confirmation = False
    if project_root:
        project_root_abs = project_root.resolve()
        is_within_project = (
            absolute_path_to_evaluate == project_root_abs
            or project_root_abs in absolute_path_to_evaluate.parents
        )
        dot_q_path_abs = (project_root_abs / ".Q").resolve()
        is_within_dot_q = (
            absolute_path_to_evaluate == dot_q_path_abs
            or dot_q_path_abs in absolute_path_to_evaluate.parents
        )
        if not is_within_project and not is_within_dot_q:
            if (
                USER_HOME_DIR.resolve() in absolute_path_to_evaluate.parents
                or USER_HOME_DIR.resolve() == absolute_path_to_evaluate
            ):
                needs_confirmation = True  # Outside project but inside home
    elif (
        USER_HOME_DIR.resolve() in absolute_path_to_evaluate.parents
        or USER_HOME_DIR.resolve() == absolute_path_to_evaluate
    ):
        needs_confirmation = True  # No project context, but path is in user home

    if needs_confirmation:
        prompt_msg = f"Allow QX to read file: '{expanded_path_arg}' (located outside the project, in your home directory)?"
        decision_status, _ = request_confirmation(
            prompt_message=prompt_msg,
            console=console,  # Use console from context
            allow_modify=False,
        )
        if decision_status not in ["approved"]:  # "modified" is not applicable here
            error_message = f"Read operation for '{expanded_path_arg}' was {decision_status} by user."
            logger.warning(error_message)
            return ReadFilePluginOutput(
                path=expanded_path_arg, content=None, error=error_message
            )

    content, error = _read_file_core_logic(expanded_path_arg)
    return ReadFilePluginOutput(path=expanded_path_arg, content=content, error=error)


if __name__ == "__main__":
    import shutil

    from rich.console import Console as RichConsole

    logging.basicConfig(level=logging.INFO)
    test_console = RichConsole()

    # Create dummy context for testing
    test_deps = QXToolDependencies(console=test_console)

    # Wrap it in a dummy RunContext for the tool signature
    class DummyRunContext(RunContext[QXToolDependencies]):
        def __init__(self, deps: QXToolDependencies):
            super().__init__(deps=deps, usage=None)  # type: ignore

    dummy_ctx = DummyRunContext(deps=test_deps)

    test_base = Path("./tmp_read_plugin_test_ctx").resolve()
    if test_base.exists():
        shutil.rmtree(test_base)
    test_base.mkdir(exist_ok=True)

    test_project = test_base / "test_project_ctx"
    test_project.mkdir(exist_ok=True)
    (test_project / ".Q").mkdir(exist_ok=True)
    (test_project / "project_file.txt").write_text("This is a project file.")
    (test_project / ".Q" / "q_file.txt").write_text("This is a .Q file.")

    original_cwd = Path.cwd()
    os.chdir(test_project)

    test_console.rule("Testing read_file_tool plugin with RunContext")

    test_console.print("\n[bold]Test 1: Read project file[/]")
    input1 = ReadFilePluginInput(path="project_file.txt")
    output1 = read_file_tool(dummy_ctx, input1)
    test_console.print(f"Output 1: {output1}")
    assert output1.content == "This is a project file." and output1.error is None

    test_console.print("\n[bold]Test 2: Read .Q file[/]")
    input2 = ReadFilePluginInput(path=".Q/q_file.txt")
    output2 = read_file_tool(dummy_ctx, input2)
    test_console.print(f"Output 2: {output2}")
    assert output2.content == "This is a .Q file." and output2.error is None

    os.chdir(original_cwd)
    test_console.print("\n[bold]Test 4: Read /etc/hosts (policy denial)[/]")
    input4 = ReadFilePluginInput(path="/etc/hosts")
    output4 = read_file_tool(dummy_ctx, input4)  # CWD is now original_cwd
    test_console.print(f"Output 4: {output4}")
    assert output4.content is None and "Access denied by policy" in output4.error

    home_test_file_path = USER_HOME_DIR / "qx_read_plugin_home_test_ctx.txt"
    home_test_file_path.write_text("Content from user home test file for context test.")

    test_console.print(
        f"\n[bold]Test 5: Read file in user home ('{home_test_file_path}') - requires confirmation[/]"
    )
    # Ensure CWD is such that home file is outside any detected project for this test
    # If original_cwd is the qx project root, this should work.
    os.chdir(original_cwd)  # Make sure we are outside test_project_ctx

    input5 = ReadFilePluginInput(path=f"~/{home_test_file_path.name}")
    test_console.print(f"Please respond to the upcoming prompt (e.g., 'y' or 'n')")
    output5 = read_file_tool(dummy_ctx, input5)
    test_console.print(f"Output 5: {output5}")

    home_test_file_path.unlink(missing_ok=True)
    shutil.rmtree(test_base)
    os.chdir(original_cwd)
    test_console.print("\nRead_file_plugin (with context) tests finished.")
