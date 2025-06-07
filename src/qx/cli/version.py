import sys
import asyncio

from qx.cli.theme import themed_console
from qx.core.config_manager import ConfigManager
from qx.core.llm_utils import initialize_agent_with_mcp
from qx.cli.commands import _handle_model_command
from qx.core.logging_config import configure_logging

# Qx Version
QX_VERSION = "0.3.45"


def display_version_info():
    """
    Displays Qx version, LLM model, and its parameters, then exits.
    """
    configure_logging()
    config_manager = ConfigManager(None, parent_task_group=None)
    config_manager.load_configurations()

    themed_console.print(f"Qx Version: {QX_VERSION}", style="app.header")

    try:
        # Temporarily create an MCPManager for version display
        # This is a bit of a hack, but avoids passing the full task group
        # when only version info is needed.
        class TempMCPManager:
            async def disconnect_all(self):
                pass  # No-op for temp manager

        temp_mcp_manager = TempMCPManager()
        agent = asyncio.run(initialize_agent_with_mcp(temp_mcp_manager))
        _handle_model_command(agent)
    except SystemExit:
        themed_console.print(
            "Note: Could not display LLM model information as QX_MODEL_NAME is not configured.",
            style="warning",
        )
    sys.exit(0)
