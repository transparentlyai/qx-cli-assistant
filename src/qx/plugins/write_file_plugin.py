import asyncio
import difflib
import logging
import os
from pathlib import Path
from typing import Optional, Union

from pydantic import BaseModel, Field
from rich.console import Console
from rich.markdown import Markdown
from rich.syntax import Syntax

from qx.core.approval_handler import ApprovalHandler
from qx.core.paths import USER_HOME_DIR, _find_project_root
from qx.cli.console import themed_console

logger = logging.getLogger(__name__)

MAX_PREVIEW_LINES = 50
HEAD_LINES = 20
TAIL_LINES = 20


def is_path_allowed(
    resolved_path: Path, project_root: Optional[Path], user_home: Path
) -> bool:
    path_to_check = resolved_path.resolve()
    if project_root and (
        path_to_check == project_root.resolve()
        or project_root.resolve() in path_to_check.parents
    ):
        return True
    if (
        path_to_check == user_home.resolve()
        or user_home.resolve() in path_to_check.parents
    ):
        return True
    return False


async def _write_file_core_logic(path_str: str, content: str) -> Optional[str]:
    try:
        path = Path(os.path.expanduser(path_str)).resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        await asyncio.to_thread(path.write_text, content, encoding="utf-8")
        return None
    except Exception as e:
        logger.error(f"Error writing to file '{path_str}': {e}", exc_info=True)
        return str(e)


async def _generate_write_preview(
    file_path_str: str, new_content: str
) -> Union[Syntax, Markdown]:
    path = Path(os.path.expanduser(file_path_str))

    if path.exists() and path.is_file():
        try:
            old_content = await asyncio.to_thread(path.read_text, encoding="utf-8")
            if old_content == new_content:
                return Markdown("Content is identical. No changes to apply.")
            diff = difflib.unified_diff(
                old_content.splitlines(keepends=True),
                new_content.splitlines(keepends=True),
                fromfile=f"a/{path.name}",
                tofile=f"b/{path.name}",
            )
            return Syntax("".join(diff), "diff", theme="vim", line_numbers=False)
        except Exception as e:
            logger.error(f"Error generating diff for {path}: {e}")
            # Fallback to full content preview on error

    lines = new_content.splitlines()
    if len(lines) > MAX_PREVIEW_LINES:
        preview = (
            "\n".join(lines[:HEAD_LINES]) + "\n...\n" + "\n".join(lines[-TAIL_LINES:])
        )
        return Syntax(preview, "auto", theme="rrt", line_numbers=True, start_line=1)
    return Syntax(new_content, "auto", theme="rrt", line_numbers=True)


class WriteFilePluginInput(BaseModel):
    path: str = Field(..., description="Path to the file to write.")
    content: str = Field(..., description="Raw content to write to the file.")


class WriteFilePluginOutput(BaseModel):
    path: str
    success: bool
    message: str


async def write_file_tool(
    console: Console, args: WriteFilePluginInput
) -> WriteFilePluginOutput:
    approval_handler = ApprovalHandler(themed_console)
    original_path = args.path
    expanded_path = os.path.expanduser(original_path)
    absolute_path = Path(expanded_path).resolve()

    project_root = _find_project_root(str(Path.cwd()))

    if not is_path_allowed(absolute_path, project_root, USER_HOME_DIR):
        err_msg = f"Access denied by policy for path: {absolute_path}"
        themed_console.print(f"Write (Denied by Policy) path: {absolute_path}")
        approval_handler.print_outcome(
            "Write", "Failed. Policy violation.", success=False
        )
        return WriteFilePluginOutput(path=original_path, success=False, message=err_msg)

    operation = "Update file" if absolute_path.exists() else "Create file"
    preview = await _generate_write_preview(str(absolute_path), args.content)

    status, _ = await approval_handler.request_approval(
        operation=operation,
        parameter_name="path",
        parameter_value=str(absolute_path),
        prompt_message=f"Allow Qx to write to file: '{absolute_path}'?",
        content_to_display=preview,
    )

    if status not in ["approved", "session_approved"]:
        msg = "Operation denied by user."
        approval_handler.print_outcome("Write", "Denied by user.", success=False)
        return WriteFilePluginOutput(path=original_path, success=False, message=msg)

    error = await _write_file_core_logic(str(absolute_path), args.content)

    if error:
        outcome_msg = (
            "Failed to create file."
            if operation == "Create file"
            else "Failed to update file."
        )
        approval_handler.print_outcome(outcome_msg, error, success=False)
        return WriteFilePluginOutput(path=original_path, success=False, message=error)
    else:
        outcome_msg = (
            "File successfully created."
            if operation == "Create file"
            else "File successfully updated."
        )
        approval_handler.print_outcome("File", outcome_msg, success=True)
        return WriteFilePluginOutput(
            path=original_path, success=True, message=outcome_msg
        )
