import datetime
import logging

from pydantic import BaseModel, Field
from rich.console import (
    Console as RichConsole,
)  # Import RichConsole for consistency in tool signatures

logger = logging.getLogger(__name__)


class CurrentTimeInput(BaseModel):
    """Input model for the GetCurrentTimeTool - no parameters required."""

    pass


class CurrentTimePluginOutput(BaseModel):
    """Output model for the GetCurrentTimeTool."""

    current_time: str = Field(
        description="The current date and time in YYYY-MM-DD HH:MM:SS format."
    )
    timezone: str = Field(
        description="The system's local timezone name (e.g., 'UTC-05:00', 'Local')."
    )


async def get_current_time_tool(
    console: RichConsole, args: CurrentTimeInput
) -> CurrentTimePluginOutput:
    """
    Get the current date and time.

    Features:
    - No user approval required
    - Returns local system time
    - Includes timezone information
    - Format: YYYY-MM-DD HH:MM:SS

    Returns structured output with:
    - current_time: Formatted date/time string (YYYY-MM-DD HH:MM:SS)
    - timezone: System timezone identifier

    Note: This is an async tool for consistency with other Qx tools.
    """
    console.print("[info]Fetching current system time...[/info]")
    try:
        now = datetime.datetime.now()
        # Get local timezone information
        local_tz = datetime.datetime.now(datetime.timezone.utc).astimezone().tzinfo

        formatted_time = now.strftime("%Y-%m-%d %H:%M:%S")
        timezone_name = str(local_tz) if local_tz else "Local"

        logger.debug(
            f"Current time requested. Returning: {formatted_time} {timezone_name}"
        )
        console.print(
            f"[success]Current time retrieved:[/success] [success]{formatted_time} {timezone_name}[/]"
        )
        return CurrentTimePluginOutput(
            current_time=formatted_time, timezone=timezone_name
        )
    except Exception as e:
        logger.error(f"Error getting current time: {e}", exc_info=True)
        err_msg = f"Error: Could not retrieve current time: {e}"
        console.print(f"[error]{err_msg}[/]")
        return CurrentTimePluginOutput(current_time=err_msg, timezone="Unknown")
