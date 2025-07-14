import logging
import os
from pathlib import Path
from typing import Any, Optional, List, Tuple, Dict, Type

from pydantic import BaseModel

logger = logging.getLogger(__name__)


def get_current_discovered_tools() -> str:
    """
    Get the current discovered tools context by loading from plugin manager and MCP.
    This is a helper function for contexts where tools aren't already loaded.

    Returns:
        Formatted string describing available tools
    """
    try:
        from qx.core.plugin_manager import PluginManager
        from qx.core.config_manager import ConfigManager

        # Get current tools from plugin manager
        plugin_manager = PluginManager()

        # Load plugins
        try:
            import sys

            src_path = Path(__file__).parent.parent.parent
            if str(src_path) not in sys.path:
                sys.path.insert(0, str(src_path))

            registered_tools = plugin_manager.load_plugins(
                plugin_package_path="qx.plugins"
            )
        except Exception as e:
            logger.debug(f"Failed to load plugins for discovered tools: {e}")
            registered_tools = []

        # Add MCP tools if available
        try:
            config_manager = ConfigManager(None, None)
            if config_manager.mcp_manager:
                mcp_tools = config_manager.mcp_manager.get_active_tools()
                if mcp_tools:
                    registered_tools.extend(mcp_tools)
        except Exception as e:
            logger.debug(f"Failed to load MCP tools for discovered tools: {e}")

        return generate_discovered_tools_context(registered_tools)

    except Exception as e:
        logger.debug(f"Failed to get current discovered tools: {e}")
        return "No tools discovered."


def get_current_discovered_models() -> str:
    """
    Get the current discovered models context.
    This is a helper function for contexts where models context is needed.

    Returns:
        Formatted string describing discovered models
    """
    return generate_discovered_models_context()


def get_current_discovered_agents() -> str:
    """
    Get the current discovered agents context.
    This is a helper function for contexts where agents context is needed.

    Returns:
        Formatted string describing discovered agents
    """
    return generate_discovered_agents_context()


def load_base_prompt() -> Optional[str]:
    """
    Load base prompt from hierarchical search paths.
    Priority: project -> user -> system -> development

    Returns:
        Base prompt content if found, None otherwise
    """
    search_paths = [
        Path.cwd() / ".Q" / "prompts" / "base-prompt.md",  # Project level
        Path.home() / ".config" / "qx" / "prompts" / "base-prompt.md",  # User level
        Path("/etc/qx/prompts/base-prompt.md"),  # System level
        Path(__file__).parent.parent.parent
        / "prompts"
        / "base-prompt.md",  # Development
    ]

    for path in search_paths:
        if path.exists() and path.is_file():
            try:
                content = path.read_text(encoding="utf-8").strip()
                if content:
                    logger.debug(f"Loaded base prompt from: {path}")
                    return content
            except Exception as e:
                logger.warning(f"Failed to read base prompt from {path}: {e}")
                continue

    logger.debug("No base prompt found in search paths")
    return None


def generate_discovered_agents_context() -> str:
    """
    Generate a simple list of discovered agents with descriptions.

    Returns:
        Simple list of agents and descriptions
    """
    try:
        from qx.core.agent_manager import get_agent_manager
        import os

        agent_manager = get_agent_manager()

        # Get agents list (this is async, but we'll handle it)
        try:
            import asyncio

            # Check if we're in an async context
            try:
                asyncio.get_running_loop()
                # We're in an async context, can't run async code directly
                # Instead, get the agent info synchronously if possible
                agents_info = agent_manager.get_cached_agents_info(cwd=os.getcwd())
            except RuntimeError:
                # No event loop, we can run async code
                agents_info = asyncio.run(agent_manager.list_agents(cwd=os.getcwd()))
        except Exception:
            # Fallback: try to get from agent loader directly
            try:
                from qx.core.agent_loader import AgentLoader

                loader = AgentLoader()
                agents_info = []

                for search_path in loader.get_agent_search_paths(cwd=os.getcwd()):
                    if search_path.exists():
                        for agent_file in search_path.glob("*.agent.yaml"):
                            agent_name = agent_file.stem.replace(".agent", "")
                            try:
                                import yaml

                                with open(agent_file, "r") as f:
                                    agent_data = yaml.safe_load(f)
                                    if agent_data:
                                        description = agent_data.get(
                                            "description", "Available agent"
                                        )
                                        agents_info.append(
                                            {
                                                "name": agent_name,
                                                "description": description,
                                            }
                                        )
                            except Exception:
                                agents_info.append(
                                    {
                                        "name": agent_name,
                                        "description": "Available agent",
                                    }
                                )
            except Exception:
                agents_info = []

        if not agents_info:
            return "No agents available."

        agent_descriptions = []

        for agent in agents_info:
            agent_name = agent.get("name", "Unknown")
            agent_description = agent.get("description", "Available agent")

            # Simple format: agent_name - description
            agent_descriptions.append(f"- {agent_name}: {agent_description}")

        return "\n".join(agent_descriptions)

    except Exception as e:
        logger.debug(f"Failed to get available agents: {e}")
        return "No agents available."


def generate_available_agents_context() -> str:
    """
    Generate a detailed list of available built-in agents with their descriptions.
    Only includes enabled built-in agents, not project-specific agents.

    Returns:
        Detailed list of enabled built-in agents with descriptions and type
    """
    try:
        from qx.core.agent_loader import AgentLoader

        loader = AgentLoader()
        agents_info = []

        # Get only built-in agents
        builtin_agents = loader.discover_builtin_agents()

        for agent_name in builtin_agents:
            agent_info = loader.get_agent_info(agent_name)
            if agent_info and agent_info.get("enabled", True):
                agents_info.append(agent_info)

        if not agents_info:
            return "No built-in agents available."

        # Sort agents by type (user agents first) and then by name
        agents_info.sort(
            key=lambda x: (x.get("type", "user") == "system", x.get("name", ""))
        )

        agent_descriptions = []

        for agent in agents_info:
            agent_name = agent.get("name", "Unknown")
            agent_description = agent.get("description", "No description available")
            agent_type = agent.get("type", "user")

            # Format: agent_name [type] - description
            type_label = " [system]" if agent_type == "system" else ""

            agent_descriptions.append(
                f"- {agent_name}{type_label}: {agent_description}"
            )

        return "\n".join(agent_descriptions)

    except Exception as e:
        logger.debug(f"Failed to get available agents: {e}")
        return "No built-in agents available."


def generate_discovered_models_context() -> str:
    """
    Generate a simple list of discovered models with descriptions.

    Returns:
        Simple list of models and descriptions
    """
    try:
        from qx.core.constants import MODELS

        if not MODELS:
            return "No models available."

        model_descriptions = []

        for model in MODELS:
            # Use the full model name (the actual model identifier)
            full_model_name = model.get("model", "Unknown")
            model_description = model.get("description", "No description available")

            # Simple format: full_model_name - description
            model_descriptions.append(f"- {full_model_name}: {model_description}")

        return "\n".join(model_descriptions)

    except Exception as e:
        logger.debug(f"Failed to get available models: {e}")
        return "No models available."


def generate_discovered_tools_context(
    tools: List[Tuple[Any, Dict[str, Any], Type[BaseModel]]],
) -> str:
    """
    Generate a simple list of discovered tools with descriptions.

    Args:
        tools: List of (function, schema, model_class) tuples from PluginManager

    Returns:
        Simple list of tools and descriptions
    """
    if not tools:
        return "No tools available."

    tool_descriptions = []

    for func, schema, model_class in tools:
        # Extract tool information
        tool_name = func.__name__

        # Handle different schema formats (regular plugins vs MCP tools)
        if "function" in schema:
            # MCP tools format: {"type": "function", "function": {...}}
            function_def = schema["function"]
        else:
            # Regular plugins format: {"name": ..., "description": ..., "parameters": ...}
            function_def = schema

        tool_description = function_def.get("description", "No description available")

        # Simple format: tool_name - description
        tool_descriptions.append(f"- {tool_name}: {tool_description}")

    return "\n".join(tool_descriptions)


def load_and_format_system_prompt(
    agent_config: Any,
    agent_mode: str = "single",
    current_agent_name: str = "",
    discovered_tools: str = "",
    discovered_models: str = "",
    discovered_agents: str = "",
) -> str:
    """
    Loads the system prompt from agent configuration.
    Formats it with environment variables and runtime information.

    Args:
        agent_config: AgentConfig instance for agent-based prompts
        agent_mode: Type of agent (always "single")
        current_agent_name: Name of the current agent
        discovered_tools: Pre-generated discovered tools context (if empty, will be loaded automatically)
        discovered_models: Pre-generated discovered models context (if empty, will be loaded automatically)
        discovered_agents: Pre-generated discovered agents context (if empty, will be loaded automatically)

    Returns:
        Formatted system prompt string
    """
    try:
        logger.debug(
            f"Loading system prompt for {agent_mode} agent: {current_agent_name}"
        )

        # If no discovered_tools provided, generate it from current state
        if not discovered_tools:
            discovered_tools = get_current_discovered_tools()

        # If no discovered_models provided, generate it from current state
        if not discovered_models:
            discovered_models = get_current_discovered_models()

        # If no discovered_agents provided, generate it from current state
        if not discovered_agents:
            discovered_agents = get_current_discovered_agents()

        return _load_agent_based_prompt(
            agent_config,
            agent_mode,
            current_agent_name,
            discovered_tools,
            discovered_models,
            discovered_agents,
        )
    except Exception as e:
        logger.error(f"Failed to load or format system prompt: {e}", exc_info=True)
        return "You are a helpful AI assistant."


def _load_agent_based_prompt(
    agent_config: Any,
    agent_mode: str = "single",
    current_agent_name: str = "",
    discovered_tools: str = "",
    discovered_models: str = "",
    discovered_agents: str = "",
) -> str:
    """Load and format prompt from agent configuration with base prompt."""
    # Load base prompt first
    base_prompt = load_base_prompt()

    # Build system prompt from agent configuration
    system_prompt_parts = []

    # Add base prompt if available
    if base_prompt:
        system_prompt_parts.append(base_prompt)

    # Add role
    if hasattr(agent_config, "role") and agent_config.role:
        system_prompt_parts.append(agent_config.role)

    # Add instructions
    if hasattr(agent_config, "instructions") and agent_config.instructions:
        system_prompt_parts.append(agent_config.instructions)

    # Add output formatting
    if hasattr(agent_config, "output") and agent_config.output:
        system_prompt_parts.append(agent_config.output)

    # Join parts with triple dashes
    template = "\n\n---\n\n".join(system_prompt_parts)

    # Format with context if available
    if hasattr(agent_config, "context") and agent_config.context:
        template = agent_config.context + "\n\n---\n\n" + template

    # Apply standard context formatting with agent-specific variables
    return _format_prompt_template(
        template,
        agent_mode,
        current_agent_name,
        discovered_tools,
        discovered_models,
        discovered_agents,
    )


def _format_prompt_template(
    template: str,
    agent_mode: str = "single",
    current_agent_name: str = "",
    discovered_tools: str = "",
    discovered_models: str = "",
    discovered_agents: str = "",
) -> str:
    """Apply standard context formatting to a prompt template with agent-specific variables."""
    user_context = os.environ.get("QX_USER_CONTEXT", "")
    project_context = os.environ.get("QX_PROJECT_CONTEXT", "")
    project_files = os.environ.get("QX_PROJECT_FILES", "")

    # Read .gitignore from the runtime CWD
    try:
        # Get the current working directory where the qx command is run
        runtime_cwd = Path(os.getcwd())
        gitignore_path = runtime_cwd / ".gitignore"
        if gitignore_path.exists():
            ignore_paths = gitignore_path.read_text(encoding="utf-8")
        else:
            ignore_paths = "# No .gitignore file found in the current directory."
    except Exception as e:
        logger.warning(f"Could not read .gitignore file: {e}")
        ignore_paths = "# Error reading .gitignore file."

    # Generate available_agents context if template uses it
    available_agents = ""
    if "{available_agents}" in template:
        available_agents = generate_available_agents_context()

    # Apply standard template variables
    formatted_prompt = template.replace("{user_context}", user_context)
    formatted_prompt = formatted_prompt.replace("{project_context}", project_context)
    formatted_prompt = formatted_prompt.replace("{project_files}", project_files)
    formatted_prompt = formatted_prompt.replace("{ignore_paths}", ignore_paths)

    # Apply agent-specific template variables
    formatted_prompt = formatted_prompt.replace("{agent_mode}", agent_mode)
    formatted_prompt = formatted_prompt.replace(
        "{current_agent_name}", current_agent_name
    )
    formatted_prompt = formatted_prompt.replace("{team_context}", "")
    formatted_prompt = formatted_prompt.replace("{discovered_tools}", discovered_tools)
    formatted_prompt = formatted_prompt.replace(
        "{discovered_models}", discovered_models
    )
    formatted_prompt = formatted_prompt.replace(
        "{discovered_agents}", discovered_agents
    )
    formatted_prompt = formatted_prompt.replace("{available_agents}", available_agents)

    logger.debug(f"Final System Prompt Length: {len(formatted_prompt)} characters")

    return formatted_prompt
