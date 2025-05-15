import asyncio
import functools
import logging
import os
from pathlib import Path
from typing import List, Optional, Any, Dict

from pydantic_ai import Agent
from pydantic_ai.messages import ModelMessage
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.providers.google_vertex import GoogleVertexProvider
from rich.console import Console as RichConsole # Keep for type hinting

from qx.core.approvals import ApprovalManager
from qx.core.config_manager import load_runtime_configurations
from qx.tools.execute_shell import execute_shell_impl
from qx.tools.read_file import read_file_impl
from qx.tools.write_file import write_file_impl

# Configure logging for this module
logger = logging.getLogger(__name__)

# No global q_console here anymore, it will be passed in.

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
        formatted_prompt = formatted_prompt.replace("{project_context}", project_context)
        formatted_prompt = formatted_prompt.replace("{project_files}", project_files)
        return formatted_prompt
    except Exception as e:
        logger.error(f"Failed to load or format system prompt: {e}", exc_info=True)
        return "You are a helpful AI assistant."


def initialize_llm_agent(
    model_name_str: str,
    project_id: Optional[str],
    location: Optional[str],
    console: RichConsole, # Accept console instance
) -> Optional[Agent]:
    """
    Initializes the Pydantic-AI Agent.
    The 'location' parameter is used as 'region' for GoogleVertexProvider.
    """
    console.print("Initializing LLM Agent...", style="info") # Use themed style
    # load_runtime_configurations() is called in main.py before this
    system_prompt_content = load_and_format_system_prompt()
    approval_manager = ApprovalManager(console=console) # Pass console to ApprovalManager

    def approved_read_file_tool(path: str) -> Optional[str]:
        approved, final_path = approval_manager.request_approval(
            "Read file", path, allow_modify=False
        )
        if not approved:
            console.print(f"File read denied: {final_path}", style="warning")
            return f"Error: File read operation denied by user for: {final_path}"
        return read_file_impl(final_path)

    def approved_write_file_tool(path: str, content: str) -> bool:
        approved, final_path = approval_manager.request_approval(
            "Write file", path, content_preview=content, allow_modify=False
        )
        if not approved:
            console.print(f"File write denied: {final_path}", style="warning")
            return False
        return write_file_impl(final_path, content)

    def approved_execute_shell_tool(command: str) -> Dict[str, Any]:
        approved, final_command = approval_manager.request_approval(
            "Execute shell command", command, allow_modify=True
        )
        if not approved:
            console.print(f"Shell execution denied: {final_command}", style="warning")
            return {
                "stdout": "", "stderr": "Operation denied by user.",
                "returncode": -1, "error": "Operation denied by user.",
            }
        return execute_shell_impl(final_command)

    registered_tools = [
        approved_read_file_tool,
        approved_write_file_tool,
        approved_execute_shell_tool,
    ]

    try:
        actual_model_name = model_name_str
        if model_name_str.startswith("google-vertex:"):
            actual_model_name = model_name_str.split(":", 1)[1]
        
        provider_config = {}
        if project_id:
            provider_config['project_id'] = project_id
        if location:
            provider_config['region'] = location

        gemini_model_instance = GeminiModel(
            model_name=actual_model_name,
            provider=GoogleVertexProvider(**provider_config) if provider_config else GoogleVertexProvider()
        )

        agent = Agent(
            model=gemini_model_instance,
            system_prompt=system_prompt_content,
            tools=registered_tools,
        )
        
        tool_names = [tool.__name__ for tool in registered_tools]
        console.print(
            f"LLM Agent initialized: [info]{model_name_str}[/] " # Use themed style
            f"Tools: [info]{', '.join(tool_names)}[/].", # Use themed style
            style="success", # Use themed style
        )
        return agent
    except Exception as e:
        logger.error(f"Failed to initialize Pydantic-AI Agent: {e}", exc_info=True)
        console.print(f"[error]Error:[/] Init LLM Agent: {e}") # Use themed style
        return None


async def query_llm(
    agent: Agent,
    user_input: str,
    console: RichConsole, # Accept console instance
    message_history: Optional[List[ModelMessage]] = None,
) -> Optional[Any]:
    """
    Queries the LLM agent. Assumes agent.run() is a coroutine.
    """
    console.print("\nQX is thinking...", style="info") # Use themed style (e.g. "italic green" or similar)
    try:
        if message_history:
            result = await agent.run(user_input, message_history=message_history)
        else:
            result = await agent.run(user_input)
        return result
    except Exception as e:
        logger.error(f"Error during LLM query: {e}", exc_info=True)
        console.print(f"[error]Error:[/] LLM query: {e}") # Use themed style
        return None