import os
import sys
import logging
from typing import Optional

from qx.cli.theme import themed_console

from qx.core.llm import QXLLMAgent, initialize_llm_agent
from qx.core.mcp_manager import MCPManager
from qx.core.constants import DEFAULT_MODEL

logger = logging.getLogger("qx")


async def initialize_agent_with_mcp(mcp_manager: MCPManager) -> QXLLMAgent:
    """
    Initializes and returns the QXLLMAgent, passing the MCPManager.
    Exits if QX_MODEL_NAME is not set or agent initialization fails.
    """
    model_name_from_env = os.environ.get("QX_MODEL_NAME", DEFAULT_MODEL)

    if not model_name_from_env:
        themed_console.print(
            "[critical]Critical Error:[/] QX_MODEL_NAME environment variable not set. Please set it to an OpenRouter model string."
        )
        sys.exit(1)

    logger.debug("Initializing LLM agent with parameters:")
    logger.debug(f"  Model Name: {model_name_from_env}")

    # Check if streaming is enabled via environment variable
    enable_streaming = os.environ.get("QX_ENABLE_STREAMING", "true").lower() == "true"

    agent: Optional[QXLLMAgent] = initialize_llm_agent(
        model_name_str=model_name_from_env,
        console=None,
        mcp_manager=mcp_manager,
        enable_streaming=enable_streaming,
    )

    if agent is None:
        themed_console.print(
            "[critical]Critical Error:[/] Failed to initialize LLM agent. Exiting."
        )
        sys.exit(1)
    return agent
