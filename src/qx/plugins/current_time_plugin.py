import datetime
import logging

from pydantic import BaseModel, Field
from rich.console import Console as RichConsole

from qx.cli.console import themed_console

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
    themed_console.print("Get Current Time (Auto-approved)")
    try:
        now = datetime.datetime.now()
        local_tz = datetime.datetime.now(datetime.timezone.utc).astimezone().tzinfo

        formatted_time = now.strftime("%Y-%m-%d %H:%M:%S")
        timezone_name = str(local_tz) if local_tz else "Local"

        themed_console.print(f"  └─ Time: {formatted_time} {timezone_name}")
        return CurrentTimePluginOutput(
            current_time=formatted_time, timezone=timezone_name
        )
    except Exception as e:
        logger.error(f"Error getting current time: {e}", exc_info=True)
        err_msg = f"Could not retrieve current time: {e}"
        themed_console.print(f"  └─ Error: {err_msg}", style="error")
        return CurrentTimePluginOutput(current_time=err_msg, timezone="Unknown")
