import datetime
import logging

from pydantic import BaseModel, Field
from rich.console import Console as RichConsole

from qx.cli.console import themed_console


def _managed_plugin_print(
    content: str, use_bordered_markdown: bool = False, **kwargs
) -> None:
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
                        background_color="#080808",
                    )

                    # Use console manager or fallback
                    try:
                        from qx.core.console_manager import get_console_manager

                        manager = get_console_manager()
                        if manager and manager._running:
                            manager.print(
                                bordered_md, console=themed_console, markup=True, end=""
                            )
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


class CurrentTimeInput(BaseModel):
    pass


class CurrentTimePluginOutput(BaseModel):
    current_time: str = Field(description="The current date and time.")
    timezone: str = Field(description="The system's local timezone.")


async def get_current_time_tool(
    console: RichConsole, args: CurrentTimeInput
) -> CurrentTimePluginOutput:
    """Get the current date and time."""
    _managed_plugin_print(
        "[dim]Get Current Time (Auto-approved)[/dim]", use_bordered_markdown=True
    )
    try:
        now = datetime.datetime.now()
        local_tz = datetime.datetime.now(datetime.timezone.utc).astimezone().tzinfo

        formatted_time = now.strftime("%Y-%m-%d %H:%M:%S")
        timezone_name = str(local_tz) if local_tz else "Local"

        _managed_plugin_print(
            f"[dim green]└─ Time: {formatted_time} {timezone_name}[/dim green]",
            use_bordered_markdown=True,
        )
        return CurrentTimePluginOutput(
            current_time=formatted_time, timezone=timezone_name
        )
    except Exception as e:
        logger.error(f"Error getting current time: {e}", exc_info=True)
        err_msg = f"Could not retrieve current time: {e}"
        _managed_plugin_print(
            f"[dim red]└─ Error: {err_msg}[/dim red]", use_bordered_markdown=True
        )
        return CurrentTimePluginOutput(current_time=err_msg, timezone="Unknown")
