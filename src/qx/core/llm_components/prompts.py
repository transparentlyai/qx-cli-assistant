import logging
import os
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


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
        Path(__file__).parent.parent.parent / "prompts" / "base-prompt.md"  # Development
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


def load_and_format_system_prompt(agent_config: Any, agent_mode: str = "single", current_agent_name: str = "", team_context: str = "") -> str:
    """
    Loads the system prompt from agent configuration.
    Formats it with environment variables and runtime information.

    Args:
        agent_config: AgentConfig instance for agent-based prompts
        agent_mode: Type of agent ("single", "supervisor", "team_member")
        current_agent_name: Name of the current agent
        team_context: Team composition and context information

    Returns:
        Formatted system prompt string
    """
    try:
        logger.debug(f"Loading system prompt for {agent_mode} agent: {current_agent_name}")
        return _load_agent_based_prompt(agent_config, agent_mode, current_agent_name, team_context)
    except Exception as e:
        logger.error(f"Failed to load or format system prompt: {e}", exc_info=True)
        return "You are a helpful AI assistant."


def _load_agent_based_prompt(agent_config: Any, agent_mode: str = "single", current_agent_name: str = "", team_context: str = "") -> str:
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
    template = "\n---\n".join(system_prompt_parts)

    # Format with context if available
    if hasattr(agent_config, "context") and agent_config.context:
        template = agent_config.context + "\n---\n" + template

    # Apply standard context formatting with agent-specific variables
    return _format_prompt_template(template, agent_mode, current_agent_name, team_context)


def _format_prompt_template(template: str, agent_mode: str = "single", current_agent_name: str = "", team_context: str = "") -> str:
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

    # Apply standard template variables
    formatted_prompt = template.replace("{user_context}", user_context)
    formatted_prompt = formatted_prompt.replace("{project_context}", project_context)
    formatted_prompt = formatted_prompt.replace("{project_files}", project_files)
    formatted_prompt = formatted_prompt.replace("{ignore_paths}", ignore_paths)
    
    # Apply agent-specific template variables
    formatted_prompt = formatted_prompt.replace("{agent_mode}", agent_mode)
    formatted_prompt = formatted_prompt.replace("{current_agent_name}", current_agent_name)
    formatted_prompt = formatted_prompt.replace("{team_context}", team_context)

    logger.debug(f"Final System Prompt Length: {len(formatted_prompt)} characters")

    return formatted_prompt
