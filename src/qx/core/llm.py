import asyncio
import logging
import os
from pathlib import Path
from typing import Any, List, Optional

from pydantic_ai import Agent
from pydantic_ai.messages import ModelMessage
from pydantic_ai.models.openai import OpenAIModel  # Import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider  # Import OpenAIProvider
from rich.console import Console as RichConsole

from qx.core.context import QXToolDependencies

# New imports for plugin system and dependencies
from qx.core.plugin_manager import PluginManager

logger = logging.getLogger(__name__)


def load_and_format_system_prompt() -> str:
    """
    Loads the system prompt from the markdown file and formats it with
    environment variables.
    """
    try:
        current_dir = Path(__file__).parent
        prompt_path = current_dir.parent / "prompts" / "system-prompt.md"

        if not prompt_path.exists():
            logger.error(f"System prompt file not found at {prompt_path}")
            return "You are a helpful AI assistant."

        template = prompt_path.read_text(encoding="utf-8")
        user_context = os.environ.get("QX_USER_CONTEXT", "")
        project_context = os.environ.get("QX_PROJECT_CONTEXT", "")
        project_files = os.environ.get("QX_PROJECT_FILES", "")

        formatted_prompt = template.replace("{user_context}", user_context)
        formatted_prompt = formatted_prompt.replace(
            "{project_context}", project_context
        )
        formatted_prompt = formatted_prompt.replace("{project_files}", project_files)
        return formatted_prompt
    except Exception as e:
        logger.error(f"Failed to load or format system prompt: {e}", exc_info=True)
        return "You are a helpful AI assistant."


def initialize_llm_agent(
    model_name_str: str,  # This will now be the full OpenRouter model string
    console: RichConsole,  # Console is kept as it's needed for QXToolDependencies
) -> Optional[Agent]:
    """
    Initializes the Pydantic-AI Agent using the new plugin architecture,
    configured for OpenRouter.
    """
    system_prompt_content = load_and_format_system_prompt()

    # Instantiate PluginManager and load plugins
    plugin_manager = PluginManager()
    try:
        import sys

        src_path = Path(
            __file__
        ).parent.parent.parent  # Assuming llm.py is in src/qx/core
        if str(src_path) not in sys.path:
            sys.path.insert(0, str(src_path))

        registered_tools = plugin_manager.load_plugins(plugin_package_path="qx.plugins")
        if not registered_tools:
            logger.warning(
                "No tools were loaded by the PluginManager. Agent will have no tools."
            )
        else:
            logger.info(f"Loaded {len(registered_tools)} tools via PluginManager.")

    except Exception as e:
        logger.error(f"Failed to load plugins: {e}", exc_info=True)
        console.print(f"[error]Error:[/] Failed to load tools: {e}")
        registered_tools = []

    try:
        openrouter_api_key = os.environ.get("OPENROUTER_API_KEY")
        if not openrouter_api_key:
            console.print(
                "[error]Error:[/] OPENROUTER_API_KEY environment variable not set."
            )
            return None

        # OpenRouter uses the OpenAI-compatible API
        openrouter_base_url = "https://openrouter.ai/api/v1"

        # Initialize OpenAIProvider for OpenRouter
        provider = OpenAIProvider(
            api_key=openrouter_api_key,
            base_url=openrouter_base_url,
        )

        # Initialize OpenAIModel with the full model name from QX_MODEL_NAME
        # and the configured OpenRouter provider.
        model = OpenAIModel(
            model_name=model_name_str,
            provider=provider,
        )

        # Model settings (temperature, max_tokens, thinking_budget) are not directly
        # supported by OpenAIModel in the same way as GeminiModelSettings.
        # If these need to be passed, they would typically be part of the model's
        # extra_body or model_kwargs, which would require a more complex mapping
        # or a custom PydanticAI model wrapper if PydanticAI doesn't expose them
        # uniformly across all OpenAI-compatible models.
        # For now, we omit them as they were specific to GeminiModelSettings.
        model_settings = None

        agent = Agent(
            model=model,
            system_prompt=system_prompt_content,
            tools=registered_tools,
            deps_type=QXToolDependencies,
            model_settings=model_settings,  # This will be None for now
        )
        logger.info(
            f"Pydantic-AI Agent initialized with {len(registered_tools)} tools and deps_type QXToolDependencies."
        )

        if agent.model_settings:
            logger.debug(
                f"Agent initialized with model settings: {agent.model_settings}"
            )
        else:
            logger.debug("Agent initialized without specific model settings.")

        return agent

    except Exception as e:
        logger.error(f"Failed to initialize Pydantic-AI Agent: {e}", exc_info=True)
        console.print(f"[error]Error:[/] Init LLM Agent: {e}")
        return None


async def query_llm(
    agent: Agent,
    user_input: str,
    console: RichConsole,  # Keep console to create QXToolDependencies
    message_history: Optional[List[ModelMessage]] = None,
) -> Optional[Any]:
    """
    Queries the LLM agent.
    Injects QXToolDependencies (containing the console) into the agent run.
    """
    try:
        # Create the dependencies instance to be passed to the agent run
        tool_deps = QXToolDependencies(console=console)

        if message_history:
            result = await agent.run(
                user_input,
                message_history=message_history,
                deps=tool_deps,  # Pass dependencies
            )
        else:
            result = await agent.run(
                user_input,
                deps=tool_deps,  # Pass dependencies
            )
        return result
    except Exception as e:
        logger.error(f"Error during LLM query: {e}", exc_info=True)
        console.print(f"[error]Error:[/] LLM query: {e}")
        return None
