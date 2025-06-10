import asyncio
import fnmatch
import logging
import subprocess
from typing import Optional

from pydantic import BaseModel, Field
from rich.console import Console as RichConsole

from qx.cli.console import themed_console
from qx.core.approval_handler import ApprovalHandler
from qx.core.output_control import should_show_stderr, should_show_stdout
from qx.core.constants import (
    DEFAULT_PROHIBITED_COMMANDS,
    DEFAULT_APPROVED_COMMANDS,
    APPROVAL_STATUSES_OK,
)


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
                    color = get_agent_color(agent_name, agent_color)
                    bordered_md = BorderedMarkdown(
                        Markdown(content, code_theme="rrt"),
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


class ExecuteShellPluginInput(BaseModel):
    command: str = Field(..., description="The shell command to execute.")


class ExecuteShellPluginOutput(BaseModel):
    command: str
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    return_code: Optional[int] = None
    error: Optional[str] = None


def _is_command_prohibited(command: str) -> bool:
    return any(
        fnmatch.fnmatch(command, pattern) for pattern in DEFAULT_PROHIBITED_COMMANDS
    )


def _is_command_auto_approved(command: str) -> bool:
    return any(
        fnmatch.fnmatch(command, pattern) for pattern in DEFAULT_APPROVED_COMMANDS
    )


async def execute_shell_tool(
    console: RichConsole, args: ExecuteShellPluginInput
) -> ExecuteShellPluginOutput:
    approval_handler = ApprovalHandler(themed_console)
    command = args.command.strip()

    if not command:
        err_msg = "Empty command provided."
        _managed_plugin_print(f"Execute Shell Command (Error): {err_msg}")
        return ExecuteShellPluginOutput(command="", error=err_msg)

    if _is_command_prohibited(command):
        err_msg = f"Command '{command}' is prohibited by policy."
        _managed_plugin_print(f"Execute Shell Command (Denied by Policy): {command}")
        approval_handler.print_outcome(
            "Execution", "Failed. Command is prohibited.", success=False
        )
        return ExecuteShellPluginOutput(command=command, error=err_msg)

    status = "approved"
    if _is_command_auto_approved(command):
        _managed_plugin_print(
            f"**Execute Shell Command (Auto-approved):** `{command}`", 
            use_bordered_markdown=True
        )
    else:
        status, _ = await approval_handler.request_approval(
            operation="Execute Shell Command",
            parameter_name="command",
            parameter_value=command,
            prompt_message=f"Allow [primary]Qx[/] to execute command: [highlight]'{command}'[/]?",
        )

    if status not in APPROVAL_STATUSES_OK:
        err_msg = "Operation denied by user."
        approval_handler.print_outcome("Execution", "Denied by user.", success=False)
        return ExecuteShellPluginOutput(command=command, error=err_msg)

    try:

        def run_sync_command():
            return subprocess.run(
                command, shell=True, capture_output=True, text=True, check=False
            )

        process = await asyncio.to_thread(run_sync_command)

        stdout = process.stdout.strip() if process.stdout else None
        stderr = process.stderr.strip() if process.stderr else None
        return_code = process.returncode

        if return_code == 0:
            approval_handler.print_outcome("Command", "Executed successfully.")
        else:
            approval_handler.print_outcome(
                "Command", f"Failed with return code {return_code}.", success=False
            )

        # Show stdout only if output control allows it
        if stdout and await should_show_stdout():
            _managed_plugin_print(stdout, style="dim white")
        # Show stderr only if output control allows it (usually always shown)
        if stderr and await should_show_stderr():
            _managed_plugin_print(stderr, style="dim red")

        return ExecuteShellPluginOutput(
            command=command,
            stdout=stdout,
            stderr=stderr,
            return_code=return_code,
        )

    except Exception as e:
        logger.error(f"Failed to execute command '{command}': {e}", exc_info=True)
        err_msg = f"Failed to execute command: {e}"
        approval_handler.print_outcome("Execution", err_msg, success=False)
        return ExecuteShellPluginOutput(command=command, error=err_msg)
