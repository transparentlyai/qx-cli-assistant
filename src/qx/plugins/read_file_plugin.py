import logging
import os
from pathlib import Path
from typing import Optional, Tuple

from pydantic import BaseModel, Field
from rich.console import Console as RichConsole  # Import RichConsole directly

from qx.core.paths import USER_HOME_DIR, _find_project_root
from qx.core.user_prompts import request_confirmation

logger = logging.getLogger(__name__)


# --- Duplicated from src/qx/tools/file_operations_base.py ---
# Note: Consider refactoring to a shared location if not already planned.
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
    Core logic to read file content. Does not handle approval or console output.
    Returns (content, error_message). content is None if error.
    """
    logger.debug(f"_read_file_core_logic received path_str: {path_str}")
    try:
        # Path expansion and resolution are expected to be done by the caller
        # This core logic now assumes path_str is an absolute, resolved path string
        absolute_path = Path(path_str)

        # Basic check, though primary validation is in the calling tool function
        if not absolute_path.is_file():
            logger.error(f"File not found or not a file (core logic): {absolute_path}")
            return (
                None,
                f"Error: File not found or is not a regular file: {absolute_path}",
            )

        content = absolute_path.read_text(encoding="utf-8")
        logger.info(f"Successfully read file (core logic): {absolute_path}")
        return content, None

    except (
        FileNotFoundError
    ):  # Should ideally be caught by pre-check absolute_path.is_file()
        logger.error(f"File not found (exception in core logic): {path_str}")
        return None, f"Error: File not found: {path_str}"
    except PermissionError:
        logger.error(f"Permission denied reading file (core logic): {path_str}")
        return None, f"Error: Permission denied reading file: {path_str}"
    except IsADirectoryError:
        logger.error(f"Path is a directory, not a file (core logic): {path_str}")
        return None, f"Error: Path is a directory, not a file: {path_str}"
    except Exception as e:
        logger.error(
            f"Error reading file \'{path_str}\' (core logic): {e}", exc_info=True
        )
        return None, f"Error reading file \'{path_str}\': {e}"


# --- End of _read_file_core_logic ---


class ReadFilePluginInput(BaseModel):
    """Input model for the ReadFilePluginTool."""

    path: str = Field(
        ...,
        description="The path to the file to be read. Can be relative, absolute, or start with '~'.",
    )


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


async def read_file_tool(  # Made async
    console: RichConsole,
    args: ReadFilePluginInput,
) -> ReadFilePluginOutput:
    """
    Tool to read the content of a specified file.
    """
    # console is now directly available, no need for ctx.deps.console

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

    logger.debug(f"read_file_tool evaluating path: {absolute_path_to_evaluate}")

    if not is_path_allowed(absolute_path_to_evaluate, project_root, USER_HOME_DIR):
        err_msg = (
            f"Error: Access denied by policy for path: {absolute_path_to_evaluate}"
        )
        logger.error(
            f"Read access denied by policy (plugin pre-check) for path: {absolute_path_to_evaluate}"
        )
        console.print(
            f"[red]Read denied by policy:[/red] {absolute_path_to_evaluate}"
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
            # Path is not in project. Check if it's in user home (and not project itself if project is in home)
            user_home_abs = USER_HOME_DIR.resolve()
            if (
                absolute_path_to_evaluate == user_home_abs
                or user_home_abs in absolute_path_to_evaluate.parents
            ):
                # This logic assumes `is_path_allowed` permits it, so it must be in home.
                needs_confirmation = True
    elif (  # No project_root found, check if path is in user home
        USER_HOME_DIR.resolve() in absolute_path_to_evaluate.parents
        or USER_HOME_DIR.resolve() == absolute_path_to_evaluate
    ):
        needs_confirmation = True

    if needs_confirmation:
        prompt_msg = f"Allow QX to read file: \'{expanded_path_arg}\' (located outside the project, in your home directory)?"
        decision_status, _ = await request_confirmation(  # Await
            prompt_message=prompt_msg,
            console=console,
            allow_modify=False,  # Read operations typically don't modify the path
        )
        if decision_status not in ["approved", "session_approved"]:
            error_message = f"Read operation for \'{expanded_path_arg}\' was {decision_status} by user."
            logger.warning(error_message)
            if decision_status == "denied":
                console.print(
                    f"[warning]Read operation denied by user:[/warning] {expanded_path_arg}"
                )
            elif decision_status == "cancelled":
                console.print(
                    f"[warning]Read operation cancelled by user for:[/warning] {expanded_path_arg}"
                )
            else:  # Should not happen with current request_confirmation for non-modify
                console.print(
                    f"[warning]Read operation for \'{expanded_path_arg}\' was {decision_status} by user.[/warning]"
                )
            return ReadFilePluginOutput(
                path=expanded_path_arg, content=None, error=error_message
            )

    # If all checks passed and confirmed (if needed):
    console.print(
        f"[info]Reading file:[/info] {absolute_path_to_evaluate}"
    )  # Use absolute path for clarity

    # Ensure the path passed to core logic is the fully resolved absolute path
    # and that it has been verified to be a file before calling.
    if not absolute_path_to_evaluate.is_file():
        err_msg = (
            f"Error: Path is not a file or does not exist: {absolute_path_to_evaluate}"
        )
        logger.error(err_msg)
        console.print(
            f"[red]Failed to read \'{expanded_path_arg}\':[/red] Path is not a file or does not exist."
        )
        return ReadFilePluginOutput(path=expanded_path_arg, content=None, error=err_msg)

    content, error_from_core = _read_file_core_logic(str(absolute_path_to_evaluate))

    if error_from_core:
        # _read_file_core_logic already logs its specific errors.
        console.print(
            f"[red]Failed to read \'{expanded_path_arg}\':[/red] {error_from_core}"
        )
        return ReadFilePluginOutput(
            path=expanded_path_arg, content=content, error=error_from_core
        )  # content will be None
    else:
        console.print(
            f"[success]Successfully read file:[/success] {absolute_path_to_evaluate}"
        )  # Use absolute path for clarity
        return ReadFilePluginOutput(path=expanded_path_arg, content=content, error=None)


if __name__ == "__main__":
    import asyncio
    import shutil

    from rich.console import Console as RichConsole

    # Setup basic logging for the test
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    # Create a logger instance for this test script, if needed for specific test logs
    # test_logger = logging.getLogger(__name__ + ".test")

    test_console = RichConsole()

    # No RunContext or QXToolDependencies needed for testing tool directly
    # dummy_ctx = DummyRunContext(deps=test_deps) # Removed

    # --- Test Setup ---
    # Use a temporary directory within the project\'s ./tmp for tests
    # This makes paths more predictable and easier to clean up.
    # It also ensures that _find_project_root behaves as expected if tests are run from project root.
    original_cwd = Path.cwd()
    # Assuming the project root has a pyproject.toml or .git folder for _find_project_root
    # For this test, we\'ll simulate a project structure within ./tmp

    # Ensure ./tmp exists
    tmp_dir = Path("./tmp").resolve()
    tmp_dir.mkdir(exist_ok=True)

    test_base_name = "tmp_read_plugin_test_ctx"
    test_base = (tmp_dir / test_base_name).resolve()

    if test_base.exists():
        shutil.rmtree(test_base)
    test_base.mkdir(exist_ok=True)

    # Create a simulated project structure
    test_project_name = "test_project_for_read"
    test_project = test_base / test_project_name
    test_project.mkdir(exist_ok=True)
    (test_project / ".git").mkdir(
        exist_ok=True
    )  # To make _find_project_root identify it
    (test_project / ".Q").mkdir(exist_ok=True)

    project_file_path = test_project / "project_file.txt"
    project_file_path.write_text("This is a project file.")

    dot_q_file_path = test_project / ".Q" / "q_file.txt"
    dot_q_file_path.write_text("This is a .Q file.")

    # File in simulated user home (but outside project)
    # To avoid actually writing to user\'s real home, create a \'fake_home\' inside test_base
    fake_home_dir = test_base / "fake_user_home"
    fake_home_dir.mkdir(exist_ok=True)
    home_test_file_name = "qx_read_plugin_home_test.txt"
    home_test_file_path = fake_home_dir / home_test_file_name
    home_test_file_path.write_text("Content from user home test file for context test.")

    # Temporarily override USER_HOME_DIR for testing purposes
    # This is a bit hacky for a plugin test; ideally, USER_HOME_DIR would be injectable
    # or the test environment would be more isolated. For now, we\'ll patch it.

    # Monkeypatch USER_HOME_DIR for the duration of the tests
    # This is a bit of a hack for testing; in real use, request_confirmation would set this.
    # For this self-contained test, it\'s manageable.

    # To properly test USER_HOME_DIR logic, we need to adjust where `is_path_allowed` and
    # `read_file_tool` get USER_HOME_DIR from. If they import it directly, we\'d need to
    # monkeypatch `qx.plugins.read_file_plugin.USER_HOME_DIR`.

    # For simplicity in this example, we will test reading from the REAL user home
    # and ensure cleanup. This makes the test require user interaction for that case.
    # A more robust test suite might use mocking/patching for USER_HOME_DIR.
    real_home_test_file_path = USER_HOME_DIR / "qx_temp_read_test_file.txt"
    real_home_test_file_path.write_text("Real home test content.")

    test_console.rule("Testing read_file_tool plugin")

    # Change CWD to within the test project for relative path tests
    os.chdir(test_project)
    test_console.print(f"Current CWD for tests: {Path.cwd()}")
    test_console.print(f"Project root for tests should be: {test_project}")
    test_console.print(f"Simulated project file: {project_file_path}")
    test_console.print(f"Simulated .Q file: {dot_q_file_path}")

    async def run_tests():  # Wrapped tests in an async function
        test_console.print("\n[bold cyan]Test 1: Read project file (relative path)[/bold cyan]")
        input1 = ReadFilePluginInput(path="project_file.txt")
        output1 = await read_file_tool(test_console, input1)  # Updated call
        test_console.print(f"Output 1: {output1}")
        assert output1.content == "This is a project file." and output1.error is None

        test_console.print("\n[bold cyan]Test 2: Read .Q file (relative path)[/bold cyan]")
        input2 = ReadFilePluginInput(path=".Q/q_file.txt")
        output2 = await read_file_tool(test_console, input2)  # Updated call
        test_console.print(f"Output 2: {output2}")
        assert output2.content == "This is a .Q file." and output2.error is None

        test_console.print("\n[bold cyan]Test 3: Read non-existent file[/bold cyan]")
        input3 = ReadFilePluginInput(path="non_existent_file.txt")
        output3 = await read_file_tool(test_console, input3)  # Updated call
        test_console.print(f"Output 3: {output3}")
        assert output3.content is None and output3.error is not None
        assert (
            "not a file or does not exist" in output3.error
            or "File not found" in output3.error
        )

        # Test reading from outside project (in actual user home) - requires confirmation
        # Change CWD outside the project to ensure it\'s not resolved as a project path
        os.chdir(original_cwd)
        test_console.print(f"Changed CWD to: {Path.cwd()} for home directory test")

        test_console.print(
            f"\n[bold cyan]Test 4: Read file in user home (\'{real_home_test_file_path}\') - requires confirmation[/bold cyan]"
        )
        input4 = ReadFilePluginInput(
            path=str(real_home_test_file_path)
        )  # Absolute path to real home file
        test_console.print(f"Path for Test 4: {str(real_home_test_file_path)}")
        test_console.print(
            "Please respond \'y\' (approve) to the upcoming prompt for the test to pass."
        )
        output4 = await read_file_tool(test_console, input4)  # Updated call
        test_console.print(f"Output 4: {output4}")
        if output4.error and "denied by user" in output4.error:
            test_console.print(
                "[yellow]Test 4 skipped or user denied - this is acceptable if you chose \'n\'.[/yellow]"
            )
        else:
            assert (
                output4.content == "Real home test content." and output4.error is None
            )

        # Test policy denial (e.g., /etc/hosts)
        # This test might fail on systems where /etc/hosts is not readable by the user,
        # but the policy denial should be caught first.
        test_console.print(
            "\n[bold cyan]Test 5: Read /etc/hosts (expect policy denial)[/bold cyan]"
        )
        # Note: _find_project_root from original_cwd might still find the main QX project.
        # The policy check is absolute, so this should be fine.
        input5 = ReadFilePluginInput(path="/etc/hosts")
        output5 = await read_file_tool(test_console, input5)  # Updated call
        test_console.print(f"Output 5: {output5}")
        assert output5.content is None and output5.error is not None
        assert "Access denied by policy" in output5.error

        # Test reading a directory
        test_console.print("\n[bold cyan]Test 6: Attempt to read a directory[/bold cyan]")
        input6 = ReadFilePluginInput(path=str(test_project))  # Path to the directory
        output6 = await read_file_tool(test_console, input6)  # Updated call
        test_console.print(f"Output 6: {output6}")
        assert output6.content is None and output6.error is not None
        # Error message might vary slightly depending on when the check catches it
        assert (
            "Path is not a file" in output6.error or "is a directory" in output6.error
        )

        # --- Cleanup ---
        test_console.print("\nCleaning up test files and directories...")
        real_home_test_file_path.unlink(missing_ok=True)
        os.chdir(original_cwd)  # Change back to original CWD before removing test_base
        if test_base.exists():
            shutil.rmtree(test_base)

        test_console.print(f"Removed test base: {test_base}")
        test_console.rule("Read_file_plugin tests finished.")

    asyncio.run(run_tests())

