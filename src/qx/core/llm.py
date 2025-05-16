import asyncio
# import functools # No longer needed
import logging
import os
from pathlib import Path
from typing import List, Optional, Any, Dict

from pydantic_ai import Agent
from pydantic_ai.messages import ModelMessage
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.providers.google_vertex import GoogleVertexProvider
from rich.console import Console as RichConsole

from qx.core.approvals import ApprovalManager
from qx.core.config_manager import load_runtime_configurations
from qx.tools.execute_shell import ExecuteShellTool, ShellCommandInput, ShellCommandOutput
from qx.tools.read_file import read_file_impl
from qx.tools.write_file import write_file_impl

# Configure logging for this module
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
    console: RichConsole,
    approval_manager: ApprovalManager, # Accept ApprovalManager instance
) -> Optional[Agent]:
    """
    Initializes the Pydantic-AI Agent.
    The 'location' parameter is used as 'region' for GoogleVertexProvider.
    The 'approval_manager' is used for tool approval.
    """
    console.print("Initializing LLM Agent...", style="info")
    system_prompt_content = load_and_format_system_prompt()

    shell_tool_instance = ExecuteShellTool(approval_manager=approval_manager)

    def approved_read_file_tool(path: str) -> str:
        decision, final_path, _ = approval_manager.request_approval(
            operation_description="Read file",
            item_to_approve=path,
            allow_modify=False,
            operation_type="generic"
        )
        if decision not in ["AUTO_APPROVED", "SESSION_APPROVED", "USER_APPROVED"]:
            denial_reason = f"File read operation for '{final_path}' was {decision.lower().replace('_', ' ')}."
            console.print(denial_reason, style="warning")
            return f"Error: {denial_reason}"
        
        file_content = read_file_impl(final_path)
        if file_content is None:
            return f"Error: Could not read file at '{final_path}'. File may not exist or an error occurred."
        return file_content

    def approved_write_file_tool(path: str, content: str) -> str:
        decision, final_path, _ = approval_manager.request_approval(
            operation_description="Write file",
            item_to_approve=path,
            content_preview=content,
            allow_modify=False,
            operation_type="generic"
        )
        if decision not in ["AUTO_APPROVED", "SESSION_APPROVED", "USER_APPROVED"]:
            denial_reason = f"File write operation for '{final_path}' was {decision.lower().replace('_', ' ')}."
            console.print(denial_reason, style="warning")
            return f"Error: {denial_reason}"

        success = write_file_impl(final_path, content)
        if success:
            return f"Successfully wrote to file: {final_path}"
        else:
            return f"Error: Failed to write to file: {final_path}"

    def approved_execute_shell_tool_wrapper(command: str) -> str:
        tool_input = ShellCommandInput(command=command)
        output: ShellCommandOutput = shell_tool_instance.run(tool_input)

        if output.error:
            return f"Error executing command '{output.command}': {output.error}. Stderr: {output.stderr or '<empty>'}"
        elif output.exit_code != 0:
            return (
                f"Command '{output.command}' executed with exit code {output.exit_code}.\n"
                f"Stdout: {output.stdout or '<empty>'}\n"
                f"Stderr: {output.stderr or '<empty>'}"
            )
        else:
            return (
                f"Command '{output.command}' executed successfully.\n"
                f"Stdout: {output.stdout or '<empty>'}\n"
                f"Stderr: {output.stderr or '<empty>'}"
            )

    registered_tools = [
        approved_read_file_tool,
        approved_write_file_tool,
        approved_execute_shell_tool_wrapper,
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
            f"LLM Agent initialized: [info]{model_name_str}[/] "
            f"Tools: [info]{', '.join(tool_names)}[/].",
            style="success",
        )
        return agent
    except Exception as e:
        logger.error(f"Failed to initialize Pydantic-AI Agent: {e}", exc_info=True)
        console.print(f"[error]Error:[/] Init LLM Agent: {e}")
        return None


async def query_llm(
    agent: Agent,
    user_input: str,
    console: RichConsole,
    message_history: Optional[List[ModelMessage]] = None,
) -> Optional[Any]:
    """
    Queries the LLM agent. Assumes agent.run() is a coroutine.
    """
    console.print("\nQX is thinking...", style="info")
    try:
        if message_history:
            # agent.run() is an async method, so it should be awaited directly.
            result = await agent.run(user_input, message_history=message_history)
        else:
            result = await agent.run(user_input)
        return result
    except Exception as e:
        logger.error(f"Error during LLM query: {e}", exc_info=True)
        console.print(f"[error]Error:[/] LLM query: {e}")
        return None