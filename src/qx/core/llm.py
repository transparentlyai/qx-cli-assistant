import asyncio
import logging
import os
from pathlib import Path
from typing import Any, List, Optional

from pydantic_ai import Agent
from pydantic_ai.messages import ModelMessage
from pydantic_ai.models.gemini import GeminiModel, GeminiModelSettings # Import GeminiModelSettings
from pydantic_ai.providers.google_vertex import GoogleVertexProvider
from rich.console import Console as RichConsole

# New imports for plugin system and dependencies
from qx.core.plugin_manager import PluginManager
from qx.core.context import QXToolDependencies

# Old tool imports are no longer needed here as plugins are self-contained
# from qx.tools.execute_shell import ...
# from qx.tools.read_file import ...
# from qx.tools.write_file import ... # write_file_impl was used, but now plugin handles its core logic

# ApprovalManager is no longer directly used by llm.py for tool setup
# from qx.core.approvals import ApprovalManager 

# _find_project_root might still be needed by load_and_format_system_prompt or other parts if they exist
# For now, assuming it's not directly needed by the refactored parts of this file.
# If plugins need it internally, they import it themselves.
# from qx.core.paths import _find_project_root 

logger = logging.getLogger(__name__)


def load_and_format_system_prompt() -> str:
    """
    Loads the system prompt from the markdown file and formats it with
    environment variables. (This function remains largely unchanged)
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
    model_name_str: str,
    project_id: Optional[str],
    location: Optional[str],
    console: RichConsole, # Console is kept as it's needed for QXToolDependencies
    # approval_manager: ApprovalManager, # No longer needed here
) -> Optional[Agent]:
    """
    Initializes the Pydantic-AI Agent using the new plugin architecture.
    """
    system_prompt_content = load_and_format_system_prompt()

    # Instantiate PluginManager and load plugins
    plugin_manager = PluginManager()
    # Plugins are expected in "qx.plugins" package
    # Ensure this path is discoverable (e.g., src is in PYTHONPATH or project installed)
    try:
        # Ensure qx.plugins is discoverable. If qx is in src/, and src/ is in sys.path:
        import sys
        src_path = Path(__file__).parent.parent.parent # Assuming llm.py is in src/qx/core
        if str(src_path) not in sys.path:
            sys.path.insert(0, str(src_path))
        
        registered_tools = plugin_manager.load_plugins(plugin_package_path="qx.plugins")
        if not registered_tools:
            logger.warning("No tools were loaded by the PluginManager. Agent will have no tools.")
        else:
            logger.info(f"Loaded {len(registered_tools)} tools via PluginManager.")

    except Exception as e:
        logger.error(f"Failed to load plugins: {e}", exc_info=True)
        console.print(f"[error]Error:[/] Failed to load tools: {e}")
        registered_tools = []


    # Old tool instantiations and wrappers are removed.
    # e.g., no more shell_tool_instance, read_file_tool_instance, or wrapper functions here.

    try:
        actual_model_name = model_name_str
        if model_name_str.startswith("google-vertex:"):
            actual_model_name = model_name_str.split(":", 1)[1]

        provider_config = {}
        if project_id:
            provider_config["project_id"] = project_id
        if location:
            provider_config["region"] = location

        gemini_model_instance = GeminiModel(
            model_name=actual_model_name,
            provider=GoogleVertexProvider(**provider_config)
            if provider_config
            else GoogleVertexProvider(),
        )

        # Read model settings from environment variables
        model_settings: Optional[GeminiModelSettings] = None
        try:
            temperature = os.environ.get("QX_VERTEX_TEMPERATURE")
            max_tokens = os.environ.get("QX_VERTEX_MAX_TOKENS")
            thinking_budget = os.environ.get("QX_VERTEX_THINKING_BUDGET")

            settings_kwargs = {}
            if temperature is not None:
                settings_kwargs["temperature"] = float(temperature)
            if max_tokens is not None:
                settings_kwargs["max_output_tokens"] = int(max_tokens)
            if thinking_budget is not None:
                settings_kwargs["thinking_budget"] = int(thinking_budget)

            if settings_kwargs:
                model_settings = GeminiModelSettings(**settings_kwargs)
                logger.info(f"Gemini model settings loaded: {model_settings}")

        except ValueError as e:
            logger.error(f"Invalid value for Gemini model setting: {e}", exc_info=True)
            console.print(f"[error]Error:[/] Invalid Gemini model setting: {e}")
        except Exception as e:
            logger.error(f"Failed to load Gemini model settings: {e}", exc_info=True)
            console.print(f"[error]Error:[/] Failed to load Gemini model settings: {e}")


        agent = Agent(
            model=gemini_model_instance,
            system_prompt=system_prompt_content,
            tools=registered_tools, # Use tools loaded by PluginManager
            deps_type=QXToolDependencies, # Set the dependency type for RunContext
            model_settings=model_settings, # Pass the loaded model settings
        )
        logger.info(f"Pydantic-AI Agent initialized with {len(registered_tools)} tools and deps_type QXToolDependencies.")
        
        # Add debug logging for the agent's model settings
        if agent.model_settings:
            logger.debug(f"Agent initialized with model settings: {agent.model_settings}")
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
    console: RichConsole, # Keep console to create QXToolDependencies
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
                deps=tool_deps # Pass dependencies
            )
        else:
            result = await agent.run(
                user_input, 
                deps=tool_deps # Pass dependencies
            )
        return result
    except Exception as e:
        logger.error(f"Error during LLM query: {e}", exc_info=True)
        console.print(f"[error]Error:[/] LLM query: {e}")
        return None

# Removed the direct import and dummy definition of _find_project_root at the end,
# as it's not directly used by the refactored llm.py logic.
# Plugins needing it will import it from qx.core.paths.