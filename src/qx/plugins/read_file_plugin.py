import asyncio
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
async def _read_file_core_logic(path_str: str) -> Tuple[Optional[str], Optional[str]]:
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

        # Run blocking I/O in thread pool to avoid blocking the event loop
        content = await asyncio.to_thread(absolute_path.read_text, encoding="utf-8")
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
            f"Error reading file '{path_str}' (core logic): {e}", exc_info=True
        )
        return None, f"Error reading file '{path_str}': {e}"


# --- End of _read_file_core_logic ---


class ReadFilePluginInput(BaseModel):
    """Input model for the ReadFilePluginTool."""

    path: str = Field(
        ...,
        description="The path to the file to read. Can be relative (resolved from CWD), absolute, or start with '~' for home directory.",
    )


class ReadFilePluginOutput(BaseModel):
    """Output model for the ReadFilePluginTool."""

    path: str = Field(
        description="The expanded path that was attempted to be read (may include ~ expansion)."
    )
    content: Optional[str] = Field(
        None,
        description="The complete file content if read was successful. None if operation failed or was denied.",
    )
    error: Optional[str] = Field(
        None,
        description="Error message explaining why the read failed (e.g., 'file not found', 'permission denied', 'denied by user'). None if successful.",
    )


async def read_file_tool(  # Made async
    console: RichConsole,
    args: ReadFilePluginInput,
) -> ReadFilePluginOutput:
    """
    Tool to read the content of a specified file.

    File access permissions:
    - Files within project directory: Auto-approved
    - Files outside project but within user home: Requires approval
    - Files outside user home: Access denied by policy

    Returns structured output with:
    - path: The attempted file path (with expansions)
    - content: File contents if successful
    - error: Explanation if read failed
    """
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
            f"[red]Read denied by policy:[/red] [yellow]{absolute_path_to_evaluate}[/yellow]"
        )
        return ReadFilePluginOutput(path=expanded_path_arg, content=None, error=err_msg)

    needs_confirmation = False
    # Determine if confirmation is needed (i.e., if it's outside the project but within user home)
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
                needs_confirmation = True
    elif (  # No project_root found, check if path is in user home
        USER_HOME_DIR.resolve() in absolute_path_to_evaluate.parents
        or USER_HOME_DIR.resolve() == absolute_path_to_evaluate
    ):
        needs_confirmation = True

    if needs_confirmation:
        console.print(
            "[info]File is outside project directory but within home. Confirmation required.[/info]"
        )
        prompt_msg = f"Allow Qx to read file: '{expanded_path_arg}' (located outside the project, in your home directory)?"
        decision_status, _ = await request_confirmation(  # Await
            prompt_message=prompt_msg,
            console=console,
        )
        if decision_status not in ["approved", "session_approved"]:
            error_message = f"Read operation for '{expanded_path_arg}' was {decision_status} by user."
            logger.warning(error_message)
            # request_confirmation already prints a message for denied/cancelled
            return ReadFilePluginOutput(
                path=expanded_path_arg, content=None, error=error_message
            )

    # If all checks passed and confirmed (if needed):
    console.print(
        f"[info]Reading file:[/info] [blue]{absolute_path_to_evaluate}[/blue]"
    )  # Use absolute path for clarity

    # Ensure the path passed to core logic is the fully resolved absolute path
    # and that it has been verified to be a file before calling.
    if not absolute_path_to_evaluate.is_file():
        err_msg = (
            f"Error: Path is not a file or does not exist: {absolute_path_to_evaluate}"
        )
        logger.error(err_msg)
        console.print(
            f"[red]Failed to read '{expanded_path_arg}':[/red] Path is not a file or does not exist."
        )
        return ReadFilePluginOutput(path=expanded_path_arg, content=None, error=err_msg)

    content, error_from_core = await _read_file_core_logic(
        str(absolute_path_to_evaluate)
    )

    if error_from_core:
        # _read_file_core_logic already logs its specific errors.
        console.print(
            f"[red]Failed to read '{expanded_path_arg}':[/red] [red]{error_from_core}[/red]"
        )
        return ReadFilePluginOutput(
            path=expanded_path_arg, content=content, error=error_from_core
        )  # content will be None
    else:
        console.print(
            f"[success]Successfully read file:[/success] [green]{absolute_path_to_evaluate}[/green]"
        )  # Use absolute path for clarity
        return ReadFilePluginOutput(path=expanded_path_arg, content=content, error=None)
