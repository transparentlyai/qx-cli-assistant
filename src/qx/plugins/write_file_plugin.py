import asyncio
import difflib
import logging
import os
from pathlib import Path
from typing import Optional, Union

from pydantic import BaseModel, Field
from rich.console import Console  # Corrected import
from rich.markdown import Markdown
from rich.syntax import Syntax

from qx.core.paths import USER_HOME_DIR, _find_project_root
from qx.core.approval_handler import ApprovalHandler  # New import

logger = logging.getLogger(__name__)

# Constants for preview
MAX_PREVIEW_LINES = 30
HEAD_LINES = 12
TAIL_LINES = 12


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


async def _write_file_core_logic(path_str: str, content: str) -> Optional[str]:
    """
    Core logic to write content to a file. Does not handle approval.
    Returns None if successful, or an error message string.
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
            logger.error(f"Write access denied by policy (core logic): {absolute_path}")
            return f"Error: Access denied by policy for path: {absolute_path}"

        def _write_file_sync():
            absolute_path.parent.mkdir(parents=True, exist_ok=True)
            absolute_path.write_text(content, encoding="utf-8")

        await asyncio.to_thread(_write_file_sync)
        logger.info(f"Successfully wrote to file: {absolute_path}")
        return None
    except PermissionError:
        logger.error(f"Permission denied writing to file: {path_str}")
        return f"Error: Permission denied writing to file: {path_str}"
    except IsADirectoryError:
        logger.error(f"Path is a directory, cannot write: {path_str}")
        return f"Error: Path is a directory, cannot write: {path_str}"
    except Exception as e:
        logger.error(f"Error writing to file '{path_str}': {e}", exc_info=True)
        return f"Error writing to file '{path_str}': {e}"


async def _generate_write_preview(
    file_path_str: str,
    new_content: str,
    diff_theme: str = "vim",
    new_file_theme: str = "rrt",
) -> Union[Syntax, Markdown]:
    file_path = Path(os.path.expanduser(file_path_str))
    lexer_name = file_path.suffix.lstrip(".") or "text"
    if lexer_name == "py":
        lexer_name = "python"
    elif lexer_name == "md":
        lexer_name = "markdown"

    if file_path.exists() and file_path.is_file():
        try:
            old_content = await asyncio.to_thread(file_path.read_text, encoding="utf-8")
            if old_content == new_content:
                return Markdown(
                    "[bold yellow]No changes detected - file content is identical.[/bold yellow]"
                )
            old_lines = old_content.splitlines(keepends=True)
            new_lines = new_content.splitlines(keepends=True)
            diff_lines = list(
                difflib.unified_diff(
                    old_lines,
                    new_lines,
                    fromfile=f"a/{file_path_str}",
                    tofile=f"b/{file_path_str}",
                    lineterm="\n",
                    n=3,
                )
            )
            if diff_lines:
                return Syntax(
                    "".join(diff_lines), "diff", theme=diff_theme, line_numbers=False
                )
            return Markdown(
                "[bold yellow]No textual changes detected in diff.[/bold yellow]"
            )
        except Exception as e:
            logger.error(
                f"Error generating diff for {file_path_str}: {e}", exc_info=True
            )

    all_lines = new_content.splitlines()
    line_count = len(all_lines)
    if line_count > MAX_PREVIEW_LINES:
        head_str = "\n".join(all_lines[:HEAD_LINES])
        tail_str = "\n".join(all_lines[-TAIL_LINES:])
        display_content_str = f"{head_str}\n\n... {line_count - HEAD_LINES - TAIL_LINES} more lines ...\n\n{tail_str}"
        return Syntax(
            display_content_str, lexer_name, theme=new_file_theme, line_numbers=True
        )
    else:
        return Syntax(new_content, lexer_name, theme=new_file_theme, line_numbers=True)


class WriteFilePluginInput(BaseModel):
    path: str = Field(
        ...,
        description="Path to the file to write. Can be relative (from CWD), absolute, or start with '~'. Parent directories will be created if needed.",
    )
    content: str = Field(..., description="Raw content to write to the file.")


class WriteFilePluginOutput(BaseModel):
    path: str = Field(description="The path where content was written.")
    success: bool = Field(
        description="True if the write operation completed successfully, False otherwise."
    )
    message: str = Field(
        description="Descriptive message about the operation result. Contains success confirmation or error details."
    )


async def write_file_tool(
    console: Console, args: WriteFilePluginInput
) -> WriteFilePluginOutput:
    """
    Use this tool to update and create files in the filesystem.
    Directories will be created if they do not exist based on the provided path.
    Approval is handled by the terminal layer via ApprovalHandler.
    """
    original_path_arg = args.path
    path_to_consider = os.path.expanduser(original_path_arg)

    console.print(
        f"[info]Preparing to write to file:[/info] [info]'{path_to_consider}'[/]"
    )

    current_working_dir = Path.cwd()
    project_root = _find_project_root(str(current_working_dir))
    absolute_path_to_evaluate = Path(path_to_consider)
    if not absolute_path_to_evaluate.is_absolute():
        absolute_path_to_evaluate = current_working_dir.joinpath(
            path_to_consider
        ).resolve()
    else:
        absolute_path_to_evaluate = absolute_path_to_evaluate.resolve()

    if not is_path_allowed(absolute_path_to_evaluate, project_root, USER_HOME_DIR):
        err_msg = f"Error: Access denied by policy for path: {path_to_consider}"
        logger.error(
            f"Write access denied by policy (plugin pre-check) for path: {path_to_consider}"
        )
        console.print(
            f"[error]Access denied by policy for path:[/] [warning]'{path_to_consider}'[/]"
        )
        return WriteFilePluginOutput(
            path=path_to_consider, success=False, message=err_msg
        )

    # --- Approval Handling using ApprovalHandler ---
    approval_handler = ApprovalHandler(console)
    preview_renderable = await _generate_write_preview(
        path_to_consider, args.content, diff_theme="vim", new_file_theme="rrt"
    )

    approval_options = [
        ("a", "Approve", "approved"),
        ("d", "Deny", "denied"),
        ("s", "Approve for Session", "session_approved"),
    ]

    prompt_msg = f"Allow Qx to write to file: '{path_to_consider}'?"

    decision_status, _ = await approval_handler.request_approval(
        prompt_message=prompt_msg,
        options=approval_options,
        content_to_display=preview_renderable,
    )
    # --- End of Approval Handling ---

    path_to_write: str
    if decision_status in ["approved", "session_approved"]:
        path_to_write = path_to_consider
        if decision_status == "approved":
            console.print(
                f"[info]Proceeding to write to:[/info] [info]'{path_to_write}'[/]"
            )

    else:
        error_message = (
            f"Write operation for '{path_to_consider}' was {decision_status} by user."
        )
        logger.warning(error_message)
        return WriteFilePluginOutput(
            path=path_to_consider, success=False, message=error_message
        )

    error_from_impl = await _write_file_core_logic(path_to_write, args.content)

    if error_from_impl:
        console.print(
            f"[error]Failed to write to '{path_to_write}':[/error] [error]{error_from_impl}[/]"
        )
        return WriteFilePluginOutput(
            path=path_to_consider, success=False, message=error_from_impl
        )
    else:
        console.print(
            f"[success]Successfully wrote to:[/success] [success]'{path_to_write}'[/]"
        )
        return WriteFilePluginOutput(
            path=path_to_consider,
            success=True,
            message=f"Successfully wrote to {path_to_write}",
        )
