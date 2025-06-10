import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def load_and_format_system_prompt(agent_config: Any) -> str:
    """
    Loads the system prompt from agent configuration.
    Formats it with environment variables and runtime information.

    Args:
        agent_config: AgentConfig instance for agent-based prompts

    Returns:
        Formatted system prompt string
    """
    try:
        logger.debug("Loading system prompt from agent configuration")
        return _load_agent_based_prompt(agent_config)
    except Exception as e:
        logger.error(f"Failed to load or format system prompt: {e}", exc_info=True)
        return "You are a helpful AI assistant."


def _load_agent_based_prompt(agent_config: Any) -> str:
    """Load and format prompt from agent configuration."""
    # Build system prompt from agent configuration
    system_prompt_parts = []

    # Add role
    if hasattr(agent_config, "role") and agent_config.role:
        system_prompt_parts.append(agent_config.role)

    # Add instructions
    if hasattr(agent_config, "instructions") and agent_config.instructions:
        system_prompt_parts.append(agent_config.instructions)

    # Add output formatting
    if hasattr(agent_config, "output") and agent_config.output:
        system_prompt_parts.append(agent_config.output)

    # Join parts with double newlines
    template = "\n\n".join(system_prompt_parts)

    # Format with context if available
    if hasattr(agent_config, "context") and agent_config.context:
        template = agent_config.context + "\n\n" + template

    # Apply standard context formatting
    return _format_prompt_template(template)


def _format_prompt_template(template: str) -> str:
    """Apply standard context formatting to a prompt template."""
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

    formatted_prompt = template.replace("{user_context}", user_context)
    formatted_prompt = formatted_prompt.replace("{project_context}", project_context)
    formatted_prompt = formatted_prompt.replace("{project_files}", project_files)
    formatted_prompt = formatted_prompt.replace("{ignore_paths}", ignore_paths)

    logger.debug(f"Final System Prompt Length: {len(formatted_prompt)} characters")

    return formatted_prompt
