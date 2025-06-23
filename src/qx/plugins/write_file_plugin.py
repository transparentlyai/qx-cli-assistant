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

from qx.cli.console import themed_console
from qx.core.approval_handler import ApprovalHandler
from qx.core.paths import USER_HOME_DIR, _find_project_root


def _managed_plugin_print(content: str, **kwargs) -> None:
    """
    Print helper for plugins that uses console manager when available.
    Falls back to themed_console if manager is unavailable.
    """
    try:
        from qx.core.console_manager import get_console_manager

        manager = get_console_manager()
        if manager and manager._running:
            style = kwargs.get("style")
            markup = kwargs.get("markup", True)
            end = kwargs.get("end", "\n")
            manager.print(
                content, style=style, markup=markup, end=end, console=themed_console
            )
            return
    except Exception:
        pass

    # Fallback to direct themed_console usage
    themed_console.print(content, **kwargs)


logger = logging.getLogger(__name__)

MAX_PREVIEW_LINES = 50
HEAD_LINES = 20
TAIL_LINES = 20


def _get_lexer_from_path(file_path: Path) -> str:
    """Determine the appropriate lexer based on file extension."""
    suffix = file_path.suffix.lower()
    lexer_map = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".jsx": "jsx",
        ".tsx": "tsx",
        ".html": "html",
        ".css": "css",
        ".scss": "scss",
        ".less": "less",
        ".json": "json",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".xml": "xml",
        ".md": "markdown",
        ".sh": "bash",
        ".bash": "bash",
        ".zsh": "zsh",
        ".fish": "fish",
        ".rs": "rust",
        ".go": "go",
        ".java": "java",
        ".c": "c",
        ".cpp": "cpp",
        ".cc": "cpp",
        ".cxx": "cpp",
        ".h": "c",
        ".hpp": "cpp",
        ".sql": "sql",
        ".r": "r",
        ".rb": "ruby",
        ".php": "php",
        ".swift": "swift",
        ".kt": "kotlin",
        ".scala": "scala",
        ".clj": "clojure",
        ".vim": "vim",
        ".lua": "lua",
        ".pl": "perl",
        ".ps1": "powershell",
        ".dockerfile": "dockerfile",
        ".toml": "toml",
        ".ini": "ini",
        ".cfg": "ini",
        ".conf": "ini",
    }
    return lexer_map.get(suffix, "text")


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
        # remove tripple ``` if present from beginning and end of content
        if content.startswith("```") and content.endswith("```"):
            content = content[3:-3].strip()
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
    lexer = _get_lexer_from_path(path)

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
        return Syntax(preview, lexer, theme="rrt", line_numbers=True, start_line=1)
    return Syntax(new_content, lexer, theme="rrt", line_numbers=True)


class WriteFilePluginInput(BaseModel):
    path: str = Field(..., description="Path to the file to write.")
    content: str = Field(
        ...,
        description="Content to write to the file wrpaped in ```. e.g. ```\nprint('Hello, World!')\n```",
    )


class WriteFilePluginOutput(BaseModel):
    path: str
    success: bool
    message: str


async def write_file_tool(
    console: Console, args: WriteFilePluginInput
) -> WriteFilePluginOutput:
    approval_handler = ApprovalHandler(themed_console, use_console_manager=True)
    original_path = args.path
    expanded_path = os.path.expanduser(original_path)
    absolute_path = Path(expanded_path).resolve()

    project_root = _find_project_root(str(Path.cwd()))

    if not is_path_allowed(absolute_path, project_root, USER_HOME_DIR):
        err_msg = f"Access denied by policy for path: {absolute_path}"
        _managed_plugin_print(f"Write (Denied by Policy) path: {absolute_path}")
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
        prompt_message=f"Allow [primary]Qx[/] to write to file: [highlight]'{absolute_path}'[/]?",
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
        approval_handler.print_outcome("Write", f"{outcome_msg} {error}", success=False)
        return WriteFilePluginOutput(path=original_path, success=False, message=error)
    else:
        outcome_msg = (
            "File successfully created."
            if operation == "Create file"
            else "File successfully updated."
        )
        approval_handler.print_outcome("", outcome_msg, success=True)
        return WriteFilePluginOutput(
            path=original_path, success=True, message=outcome_msg
        )
