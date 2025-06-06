import asyncio
import logging
import os
from pathlib import Path
from typing import Optional, Tuple

from pydantic import BaseModel, Field
from rich.console import Console as RichConsole

from qx.core.paths import USER_HOME_DIR, _find_project_root
# Removed: from qx.core.user_prompts import request_confirmation

logger = logging.getLogger(__name__)


# --- Duplicated from src/qx/tools/file_operations_base.py ---
def is_path_allowed(
    resolved_path: Path, project_root: Optional[Path], user_home: Path
) -> bool:
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


async def _read_file_core_logic(path_str: str) -> Tuple[Optional[str], Optional[str]]:
    logger.debug(f"_read_file_core_logic received path_str: {path_str}")
    try:
        absolute_path = Path(path_str)
        if not absolute_path.is_file():
            logger.error(f"File not found or not a file (core logic): {absolute_path}")
            return (
                None,
                f"Error: File not found or is not a regular file: {absolute_path}",
            )
        content = await asyncio.to_thread(absolute_path.read_text, encoding="utf-8")
        logger.info(f"Successfully read file (core logic): {absolute_path}")
        return content, None
    except FileNotFoundError:
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


class ReadFilePluginInput(BaseModel):
    path: str = Field(
        ...,
        description="The path to the file to read. Can be relative (resolved from CWD), absolute, or start with '~' for home directory.",
    )


class ReadFilePluginOutput(BaseModel):
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


async def read_file_tool(
    console: RichConsole,
    args: ReadFilePluginInput,
) -> ReadFilePluginOutput:
    """
    Tool to read the content of a specified file.

    File access permissions (policy checks still apply):
    - Approval for files outside project but within home is now handled by terminal layer.
    - Files outside user home: Access denied by policy.

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
            f"[error]Read denied by policy:[/] [warning]{absolute_path_to_evaluate}[/]"
        )
        return ReadFilePluginOutput(path=expanded_path_arg, content=None, error=err_msg)

    # Approval for files outside project but within home is now assumed to be handled by the terminal layer.
    # The logic to determine if confirmation *would have been* needed is removed.
    # We proceed directly to reading if policy allows.

    console.print(f"[info]Reading file:[/info] [info]{absolute_path_to_evaluate}[/]")

    if not absolute_path_to_evaluate.is_file():
        err_msg = (
            f"Error: Path is not a file or does not exist: {absolute_path_to_evaluate}"
        )
        logger.error(err_msg)
        console.print(
            f"[error]Failed to read '{expanded_path_arg}':[/] Path is not a file or does not exist."
        )
        return ReadFilePluginOutput(path=expanded_path_arg, content=None, error=err_msg)

    content, error_from_core = await _read_file_core_logic(
        str(absolute_path_to_evaluate)
    )

    if error_from_core:
        console.print(
            f"[error]Failed to read '{expanded_path_arg}':[/] [error]{error_from_core}[/]"
        )
        return ReadFilePluginOutput(
            path=expanded_path_arg, content=content, error=error_from_core
        )
    else:
        console.print(
            f"[success]Successfully read file:[/success] [success]{absolute_path_to_evaluate}[/]"
        )
        return ReadFilePluginOutput(path=expanded_path_arg, content=content, error=None)
