import os
import sys
import logging
from typing import Optional, Any

from qx.cli.theme import themed_console

from qx.core.llm import QXLLMAgent, initialize_llm_agent
from qx.core.mcp_manager import MCPManager
from qx.core.constants import DEFAULT_MODEL

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
    team_context = ""
    
    if agent_config:
        current_agent_name = getattr(agent_config, "name", "")
        
        # Determine agent mode based on agent name
        if current_agent_name == "qx-director":
            agent_mode = "supervisor"
        elif current_agent_name == "qx":
            agent_mode = "single"
        else:
            # Other agents are likely team members when in team mode
            from qx.core.team_mode_manager import get_team_mode_manager
            team_mode_manager = get_team_mode_manager()
            if team_mode_manager.is_team_mode_enabled():
                agent_mode = "team_member"
        
        # Get team context if in team mode
        if agent_mode in ["supervisor", "team_member"]:
            try:
                from qx.core.config_manager import ConfigManager
                from qx.core.team_manager import get_team_manager
                
                # Create a minimal config manager to get team context
                config_manager = ConfigManager(None, None)
                team_manager = get_team_manager(config_manager)
                team_status = team_manager.get_team_status()
                
                if team_status['member_count'] > 0:
                    team_members = list(team_status['members'].keys())
                    team_context = f"Team members: {', '.join(team_members)}"
                else:
                    team_context = "No team members currently assigned"
                    
            except Exception as e:
                logger.warning(f"Failed to get team context: {e}")
                team_context = ""
    
    # Determine model name from agent config or environment
    if agent_config is not None:
        try:
            model_name = getattr(agent_config.model, "name", None)
            if not model_name:
                model_name = os.environ.get("QX_MODEL_NAME", DEFAULT_MODEL)
            logger.debug(f"Using agent-based model: {model_name}")
        except AttributeError:
            model_name = os.environ.get("QX_MODEL_NAME", DEFAULT_MODEL)
            logger.debug(
                f"Agent config incomplete, using environment model: {model_name}"
            )
    else:
        model_name = os.environ.get("QX_MODEL_NAME", DEFAULT_MODEL)
        logger.debug(f"Using environment-based model: {model_name}")

    if not model_name:
        themed_console.print(
            "[critical]Critical Error:[/] Model name not available from agent config or QX_MODEL_NAME environment variable."
        )
        sys.exit(1)

    logger.debug("Initializing LLM agent with parameters:")
    logger.debug(f"  Model Name: {model_name}")
    logger.debug(f"  Agent Config: {'Yes' if agent_config else 'No'}")

    # Check if streaming is enabled via environment variable or agent config
    if agent_config is not None:
        # TODO: Add streaming config to agent schema if needed
        enable_streaming = (
            os.environ.get("QX_ENABLE_STREAMING", "true").lower() == "true"
        )
    else:
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
        team_context=team_context,
    )

    if agent is None:
        themed_console.print(
            "[critical]Critical Error:[/] Failed to initialize LLM agent. Exiting."
        )
        sys.exit(1)
    return agent
