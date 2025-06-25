import os
import sys
import logging
from typing import Optional, Any

from qx.cli.theme import themed_console

from qx.core.llm import QXLLMAgent, initialize_llm_agent
from qx.core.mcp_manager import MCPManager

logger = logging.getLogger("qx")


async def initialize_agent_with_mcp(
    mcp_manager: MCPManager, agent_config: Optional[Any] = None
) -> QXLLMAgent:
    """
    Initializes and returns the QXLLMAgent, passing the MCPManager.
    Supports both legacy (environment-based) and agent-based configuration.

    Args:
        mcp_manager: MCP manager instance
        agent_config: Optional agent configuration for agent-based initialization

    Returns:
        Initialized QXLLMAgent instance
    """
    # Determine agent context
    agent_mode = "single"  # Default
    current_agent_name = ""
    
    if agent_config:
        current_agent_name = getattr(agent_config, "name", "")
        
        # All agents run in single mode
        agent_mode = "single"
    
    # Determine model name from agent config or environment
    if agent_config is not None:
        try:
            model_name = getattr(agent_config.model, "name", None)
            if not model_name:
                model_name = os.environ.get("QX_MODEL_NAME")
                if not model_name:
                    themed_console.print(
                        "[critical]Critical Error:[/] No model specified in agent configuration and QX_MODEL_NAME environment variable is not set.\n"
                        "[info]Please set QX_MODEL_NAME to your preferred model, for example:[/]\n"
                        "  export QX_MODEL_NAME=openrouter/anthropic/claude-3.5-sonnet\n"
                        "  export QX_MODEL_NAME=openrouter/google/gemini-2.5-pro-preview-06-05\n"
                        "[info]See available models at: https://openrouter.ai/models[/]"
                    )
                    sys.exit(1)
            logger.debug(f"Using agent-based model: {model_name}")
        except AttributeError:
            model_name = os.environ.get("QX_MODEL_NAME")
            if not model_name:
                themed_console.print(
                    "[critical]Critical Error:[/] Agent configuration incomplete and QX_MODEL_NAME environment variable is not set.\n"
                    "[info]Please set QX_MODEL_NAME to your preferred model, for example:[/]\n"
                    "  export QX_MODEL_NAME=openrouter/anthropic/claude-3.5-sonnet\n"
                    "  export QX_MODEL_NAME=openrouter/google/gemini-2.5-pro-preview-06-05\n"
                    "[info]See available models at: https://openrouter.ai/models[/]"
                )
                sys.exit(1)
            logger.debug(
                f"Agent config incomplete, using environment model: {model_name}"
            )
    else:
        model_name = os.environ.get("QX_MODEL_NAME")
        if not model_name:
            themed_console.print(
                "[critical]Critical Error:[/] QX_MODEL_NAME environment variable is not set.\n"
                "[info]Please set QX_MODEL_NAME to your preferred model, for example:[/]\n"
                "  export QX_MODEL_NAME=openrouter/anthropic/claude-3.5-sonnet\n" 
                "  export QX_MODEL_NAME=openrouter/google/gemini-2.5-pro-preview-06-05\n"
                "[info]See available models at: https://openrouter.ai/models[/]"
            )
            sys.exit(1)
        logger.debug(f"Using environment-based model: {model_name}")

    logger.debug("Initializing LLM agent with parameters:")
    logger.debug(f"  Model Name: {model_name}")
    logger.debug(f"  Agent Config: {'Yes' if agent_config else 'No'}")

    # Check if streaming is enabled via environment variable
    enable_streaming = (
        os.environ.get("QX_ENABLE_STREAMING", "true").lower() == "true"
    )

    agent: Optional[QXLLMAgent] = initialize_llm_agent(
        model_name_str=model_name,
        console=None,
        mcp_manager=mcp_manager,
        enable_streaming=enable_streaming,
        agent_config=agent_config,  # Pass agent config to initialization
        agent_mode=agent_mode,
        current_agent_name=current_agent_name,
    )

    if agent is None:
        themed_console.print(
            "[critical]Critical Error:[/] Failed to initialize LLM agent. Exiting."
        )
        sys.exit(1)
    return agent
