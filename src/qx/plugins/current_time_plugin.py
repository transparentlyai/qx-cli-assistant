import datetime
import logging

from pydantic import BaseModel, Field
from rich.console import (
    Console as RichConsole,
)  # Import RichConsole for consistency in tool signatures

logger = logging.getLogger(__name__)


class CurrentTimePluginOutput(BaseModel):
    """Output model for the GetCurrentTimeTool."""

    current_time: str = Field(description="The current date and time, formatted.")
    timezone: str = Field(
        description="The timezone of the reported time (local system timezone)."
    )


# No input model is strictly necessary if the tool takes no arguments.
# The PluginManager will generate an empty schema for tools with no Pydantic input.
# For consistency in tool signatures, we'll add a 'console' parameter, even if not used.
# This allows the PluginManager to pass the console to all tools uniformly.
def get_current_time_tool(console: RichConsole) -> CurrentTimePluginOutput:
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
    test_console = RichConsole()  # Create a dummy console for testing

    # Test the tool function directly
    output = get_current_time_tool(test_console)  # Pass dummy console
    print("Testing GetCurrentTimeTool directly:")
    print(f"  Time: {output.current_time}")
    print(f"  Timezone: {output.timezone}")

    assert "Error" not in output.current_time

    # Example of how it might be used with a dummy agent (conceptual)
    # from qx.core.llm import QXLLMAgent
    # from qx.core.plugin_manager import PluginManager
    #
    # # This part is illustrative and won't run without a configured QXLLMAgent
    # # and proper environment setup.
    #
    # # Temporarily patch os.environ for testing QXLLMAgent init
    # import os
    # original_openrouter_key = os.environ.get("OPENROUTER_API_KEY")
    # os.environ["OPENROUTER_API_KEY"] = "dummy_key_for_test"
    #
    # try:
    #     # Need to ensure the plugin manager can find the plugin
    #     # This is a bit complex for a simple __main__ block,
    #     # but conceptually, the agent would be initialized with this tool.
    #     # For a real test, you'd mock the agent's tool loading.
    #
    #     # Simulate plugin loading
    #     class MockPluginManager(PluginManager):
    #         def load_plugins(self, plugin_package_path: str = "qx.plugins"):
    #             # Return the tool function and a dummy schema
    #             return [(get_current_time_tool, {"name": "get_current_time_tool", "description": "Get current time", "parameters": {"type": "object", "properties": {}}})]
    #
    #     # Patch the PluginManager in llm.py for this test
    #     import sys
    #     from unittest.mock import patch
    #     sys.path.insert(0, str(Path(__file__).parent.parent.parent)) # Add src to path
    #
    #     with patch('qx.core.llm.PluginManager', new=MockPluginManager):
    #         from qx.core.llm import initialize_llm_agent
    #         agent = initialize_llm_agent(model_name_str="test/model", console=test_console)
    #         if agent:
    #             print("\nAgent initialized with get_current_time_tool.")
    #             # To actually run, you'd need a mock OpenAI client
    #             # result = await agent.run("What time is it?")
    #             # print(f"Agent conceptual result: {result.output}")
    #         else:
    #             print("\nAgent initialization failed.")
    # finally:
    #     if original_openrouter_key is not None:
    #         os.environ["OPENROUTER_API_KEY"] = original_openrouter_key
    #     else:
    #         del os.environ["OPENROUTER_API_KEY"]
    #     if str(Path(__file__).parent.parent.parent) in sys.path:
    #         sys.path.remove(str(Path(__file__).parent.parent.parent))
