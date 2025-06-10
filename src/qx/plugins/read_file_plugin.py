import asyncio
import logging
import os
from pathlib import Path
from typing import Optional, Tuple

from pydantic import BaseModel, Field
from rich.console import Console as RichConsole

from qx.core.approval_handler import ApprovalHandler
from qx.core.paths import USER_HOME_DIR, _find_project_root
from qx.cli.console import themed_console


def _managed_plugin_print(content: str, use_bordered_markdown: bool = False, **kwargs) -> None:
    """
    Print helper for plugins that uses console manager when available.
    Falls back to themed_console if manager is unavailable.
    
    Args:
        content: The content to print
        use_bordered_markdown: If True, wrap content in BorderedMarkdown with agent styling
        **kwargs: Additional print arguments
    """
    # Check if we should use BorderedMarkdown with agent styling
    if use_bordered_markdown:
        try:
            from qx.core.approval_handler import get_global_agent_context
            from qx.cli.quote_bar_component import BorderedMarkdown, get_agent_color
            from rich.markdown import Markdown
            
            agent_context = get_global_agent_context()
            if agent_context:
                agent_name = agent_context.get("name")
                agent_color = agent_context.get("color")
                
                if agent_name:
                    # Wrap content in BorderedMarkdown with agent styling (dimmed)
                    # Use Rich Text instead of Markdown to support Rich markup
                    from rich.text import Text
                    
                    color = get_agent_color(agent_name, agent_color)
                    rich_text = Text.from_markup(content)
                    bordered_md = BorderedMarkdown(
                        rich_text,
                        border_style=f"dim {color}",
                        background_color="#080808"
                    )
                    
                    # Use console manager or fallback
                    try:
                        from qx.core.console_manager import get_console_manager
                        manager = get_console_manager()
                        if manager and manager._running:
                            manager.print(bordered_md, console=themed_console, markup=True, end="")
                            return
                    except Exception:
                        pass
                    
                    # Fallback to direct themed_console usage
                    themed_console.print(bordered_md, markup=True, end="")
                    return
        except Exception:
            # If BorderedMarkdown fails, fall through to regular printing
            pass
    
    # Regular printing logic
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


async def _read_file_core_logic(path_str: str) -> Tuple[Optional[str], Optional[str]]:
    try:
        absolute_path = Path(path_str)
        if not absolute_path.is_file():
            return None, f"Error: Path is not a file or does not exist: {absolute_path}"
        content = await asyncio.to_thread(absolute_path.read_text, encoding="utf-8")
        return content, None
    except Exception as e:
        logger.error(f"Error reading file '{path_str}': {e}", exc_info=True)
        return None, f"Error reading file '{path_str}': {e}"


class ReadFilePluginInput(BaseModel):
    path: str = Field(..., description="The path to the file to read.")


class ReadFilePluginOutput(BaseModel):
    path: str
    content: Optional[str] = None
    error: Optional[str] = None


async def read_file_tool(
    console: RichConsole,
    args: ReadFilePluginInput,
) -> ReadFilePluginOutput:
    approval_handler = ApprovalHandler(themed_console)
    original_path = args.path
    expanded_path = os.path.expanduser(original_path)
    absolute_path = Path(expanded_path).resolve()

    project_root = _find_project_root(str(Path.cwd()))

    if not is_path_allowed(absolute_path, project_root, USER_HOME_DIR):
        err_msg = f"Access denied by policy for path: {absolute_path}"
        themed_console.print(f"Read (Denied by Policy) path: {absolute_path}")
        approval_handler.print_outcome(
            "Read", "Failed. Policy violation.", success=False
        )
        return ReadFilePluginOutput(path=original_path, error=err_msg)

    is_in_project = project_root and (
        absolute_path == project_root or project_root in absolute_path.parents
    )

    if is_in_project:
        _managed_plugin_print(
            f"[dim]Read (Auto-approved) path:[/dim] [dim cyan]{absolute_path}[/dim cyan]", 
            use_bordered_markdown=True
        )
        status = "approved"
    else:
        status, _ = await approval_handler.request_approval(
            operation="Read file",
            parameter_name="path",
            parameter_value=str(absolute_path),
            prompt_message=f"Allow [primary]Qx[/] to read file: [highlight]'{absolute_path}'[/]?",
        )

    if status not in ["approved", "session_approved"]:
        err_msg = "Operation denied by user."
        approval_handler.print_outcome("Read", "Denied by user.", success=False)
        return ReadFilePluginOutput(path=original_path, error=err_msg)

    content, error = await _read_file_core_logic(str(absolute_path))

    if error:
        approval_handler.print_outcome("Read", f"Failed. {error}", success=False)
        return ReadFilePluginOutput(path=original_path, error=error)
    else:
        approval_handler.print_outcome("File", "Successfully read.")
        return ReadFilePluginOutput(path=original_path, content=content)
