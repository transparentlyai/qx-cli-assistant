import datetime
import logging
from typing import Optional  # For potential future use, not strictly needed now

from pydantic import BaseModel, Field

# No RunContext needed for this simple tool

logger = logging.getLogger(__name__)


class CurrentTimePluginOutput(BaseModel):
    """Output model for the GetCurrentTimeTool."""

    current_time: str = Field(description="The current date and time, formatted.")
    timezone: str = Field(
        description="The timezone of the reported time (local system timezone)."
    )


# No input model is strictly necessary if the tool takes no arguments.
# PydanticAI can often handle tools with no input arguments directly.
# If an input model were required by a specific registration pattern, it would be:
# class CurrentTimePluginInput(BaseModel):
#     pass # No actual input fields needed


def get_current_time_tool() -> CurrentTimePluginOutput:
    """
    Tool to get the current system date and time.
    This operation does not require any user approval.
    """
    try:
        now = datetime.datetime.now()
        # Get local timezone information
        local_tz = datetime.datetime.now(datetime.timezone.utc).astimezone().tzinfo

        formatted_time = now.strftime("%Y-%m-%d %H:%M:%S")
        timezone_name = str(local_tz) if local_tz else "Local"

        logger.info(
            f"Current time requested. Returning: {formatted_time} {timezone_name}"
        )
        return CurrentTimePluginOutput(
            current_time=formatted_time, timezone=timezone_name
        )
    except Exception as e:
        logger.error(f"Error getting current time: {e}", exc_info=True)
        # Fallback in case of unexpected error
        return CurrentTimePluginOutput(
            current_time="Error: Could not retrieve current time.", timezone="Unknown"
        )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Test the tool function directly
    output = get_current_time_tool()
    print("Testing GetCurrentTimeTool directly:")
    print(f"  Time: {output.current_time}")
    print(f"  Timezone: {output.timezone}")

    assert "Error" not in output.current_time

    # Example of how it might be used with a dummy agent (conceptual)
    # from pydantic_ai import Agent
    # agent = Agent(tools=[get_current_time_tool])
    # result = agent.run_sync("What time is it?") # LLM would need to call the tool
    # print(f"Agent conceptual result: {result.output}")
    # (This part is illustrative and won't run without a configured PydanticAI agent)

