import asyncio
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic_ai import Agent
from pydantic_ai.messages import ModelMessage
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.providers.google_vertex import GoogleVertexProvider
from rich.console import Console as RichConsole

from qx.core.approvals import ApprovalManager
from qx.core.config_manager import load_runtime_configurations
from qx.tools.execute_shell import (
    ExecuteShellTool,
    ExecuteShellInput,  # Corrected name
    ExecuteShellOutput, # Corrected name
)

# Import the new ReadFileTool and its Pydantic models
from qx.tools.read_file import ReadFileInput, ReadFileOutput, ReadFileTool
from qx.tools.write_file import (
    write_file_impl,
)  # write_file_impl is still used directly in its wrapper

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
    console: RichConsole,
    approval_manager: ApprovalManager,
) -> Optional[Agent]:
    """
    Initializes the Pydantic-AI Agent.
    """
    system_prompt_content = load_and_format_system_prompt()

    # Instantiate tools
    shell_tool_instance = ExecuteShellTool(approval_manager=approval_manager)
    read_file_tool_instance = ReadFileTool(approval_manager=approval_manager)

    # Wrapper for ReadFileTool, now named 'read_file'
    def read_file(path: str) -> str:
        tool_input = ReadFileInput(path=path)
        output: ReadFileOutput = read_file_tool_instance.run(tool_input)

        if output.error:
            # output.error from ReadFileOutput should be a comprehensive message
            return output.error
        elif output.content is not None:
            return output.content
        else:
            # This case should ideally not be reached if output.error covers all failures
            # and output.content is present on success.
            logger.warning(
                f"ReadFileTool returned no content and no error for path: {path}"
            )
            return f"Error: An unexpected issue occurred while reading file '{path}'. No content or error reported by tool."

    # Wrapper for write_file_impl, now named 'write_file'
    def write_file(path: str, content: str) -> str:
        # Determine project_root to pass to approval_manager
        # This is crucial for the conditional session approval logic for write_file
        current_project_root = _find_project_root(str(Path.cwd()))

        decision, final_path, _ = approval_manager.request_approval(
            operation_description="Write file",
            item_to_approve=path,
            content_preview=content,  # This is the full new content
            allow_modify=True,  # Allow modifying the path
            operation_type="write_file",  # Use "write_file" type for specific preview
            project_root=current_project_root, # Pass project_root
        )
        if decision not in [
            "AUTO_APPROVED",
            "SESSION_APPROVED",
            "USER_APPROVED",
            "USER_MODIFIED",
        ]:
            denial_reason = f"File write operation for '{final_path}' was {decision.lower().replace('_', ' ')}."
            # If USER_MODIFIED, final_path is already the modified path.
            # If denied/cancelled, final_path is the original or last considered path.
            console.print(denial_reason, style="warning")
            return f"Error: {denial_reason}"

        # If USER_MODIFIED, final_path is the new path to write to.
        # Content remains the original 'content' argument passed to this tool function.
        # Note: write_file_impl is the raw implementation, does not involve approval_manager again.
        error_message_from_impl = write_file_impl(final_path, content)
        if error_message_from_impl is None: # write_file_impl returns None on success
            return f"Successfully wrote to file: {final_path}"
        else:
            # error_message_from_impl contains the error string
            return f"Error: {error_message_from_impl}"


    # Wrapper for ExecuteShellTool, now named 'execute_shell'
    def execute_shell(command: str) -> str:
        tool_input = ExecuteShellInput(command=command) # Corrected name
        output: ExecuteShellOutput = shell_tool_instance.run(tool_input) # Corrected name

        if output.error:
            return f"Error executing command '{output.command}': {output.error}. Stderr: {output.stderr or '<empty>'}"
        elif output.return_code != 0: # Check if return_code is not None before comparing
            return (
                f"Command '{output.command}' executed with exit code {output.return_code}.\n"
                f"Stdout: {output.stdout or '<empty>'}\n"
                f"Stderr: {output.stderr or '<empty>'}"
            )
        else: # Command succeeded (return_code is 0)
            return (
                f"Command '{output.command}' executed successfully.\n"
                f"Stdout: {output.stdout or '<empty>'}\n"
                f"Stderr: {output.stderr or '<empty>'}" # Stderr might still have content on success
            )

    registered_tools = [
        read_file,
        write_file,
        execute_shell,
    ]

    try:
        actual_model_name = model_name_str
        if model_name_str.startswith("google-vertex:"):
            actual_model_name = model_name_str.split(":", 1)[1]

        provider_config = {}
        if project_id:
            provider_config["project_id"] = project_id
        if location:
            provider_config["region"] = location # Gemini uses 'region' not 'location'

        gemini_model_instance = GeminiModel(
            model_name=actual_model_name,
            provider=GoogleVertexProvider(**provider_config)
            if provider_config
            else GoogleVertexProvider(),
        )

        agent = Agent(
            model=gemini_model_instance,
            system_prompt=system_prompt_content,
            tools=registered_tools,
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
    Spinner is handled in main.py around this call.
    """
    try:
        if message_history:
            result = await agent.run(user_input, message_history=message_history)
        else:
            result = await agent.run(user_input)
        return result
    except Exception as e:
        logger.error(f"Error during LLM query: {e}", exc_info=True)
        console.print(f"[error]Error:[/] LLM query: {e}")
        return None

# Helper import for write_file wrapper, if not already available globally in this module
# This is to ensure _find_project_root is available for the write_file wrapper.
# It might already be available if another import pulls it in, but explicit is safer.
try:
    from qx.core.paths import _find_project_root
except ImportError:
    # This case should ideally not happen if project structure is correct
    # and qx.core.paths is always accessible.
    logger.error("Failed to import _find_project_root directly in llm.py for write_file wrapper.")
    # Define a dummy or raise error if critical
    def _find_project_root(path_str: str) -> Optional[Path]:
        logger.warning("_find_project_root is a dummy in llm.py due to import error.")
        return None
