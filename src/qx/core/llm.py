import os
from typing import List, Optional
from pathlib import Path # Added for path operations
from pydantic_ai import Agent
from pydantic_ai.messages import ModelMessage
from pydantic_ai.agent import AgentRunResult
from rich.console import Console

from qx.tools.read_file import read_file
from qx.tools.write_file import write_file
from qx.core.paths import _find_project_root # For finding project root to locate prompt

console = Console()

# Define the path to the system prompt template relative to this file's location
# Assuming llm.py is in src/qx/core/ and prompt is in src/qx/prompts/
# Path(__file__).resolve() -> /path/to/project/src/qx/core/llm.py
# .parent -> /path/to/project/src/qx/core/
# .parent -> /path/to/project/src/qx/
# / "prompts" / "system-prompt.md" -> /path/to/project/src/qx/prompts/system-prompt.md
SYSTEM_PROMPT_TEMPLATE_PATH = Path(__file__).resolve().parent.parent / "prompts" / "system-prompt.md"

def load_and_format_system_prompt() -> str:
    """
    Loads the system prompt template, substitutes placeholders with environment variables,
    and returns the formatted system prompt.
    """
    try:
        template_content = SYSTEM_PROMPT_TEMPLATE_PATH.read_text(encoding="utf-8")
    except FileNotFoundError:
        console.print(f"[bold red]LLM Error: System prompt template not found at {SYSTEM_PROMPT_TEMPLATE_PATH}[/bold red]")
        console.print("[bold yellow]LLM Warning: Using a basic default system prompt.[/bold yellow]")
        return "You are a helpful AI assistant." # Basic fallback
    except Exception as e:
        console.print(f"[bold red]LLM Error: Could not read system prompt template: {e}[/bold red]")
        console.print("[bold yellow]LLM Warning: Using a basic default system prompt.[/bold yellow]")
        return "You are a helpful AI assistant." # Basic fallback

    user_context = os.environ.get("QX_USER_CONTEXT", "")
    project_context = os.environ.get("QX_PROJECT_CONTEXT", "")
    project_files = os.environ.get("QX_PROJECT_FILES", "")

    formatted_prompt = template_content.replace("{user_context}", user_context)
    formatted_prompt = formatted_prompt.replace("{project_context}", project_context)
    formatted_prompt = formatted_prompt.replace("{project_files}", project_files)

    return formatted_prompt

def initialize_llm_agent():
    """
    Initializes the PydanticAI LLM agent.

    Retrieves model configuration from environment variables, loads and formats
    the system prompt, and registers tools.

    Returns:
        An initialized Agent instance or None if initialization fails.
    """
    model_name = os.getenv("QX_MODEL_NAME")
    vertex_project_id = os.getenv("QX_VERTEX_PROJECT_ID")
    vertex_location = os.getenv("QX_VERTEX_LOCATION")

    if not model_name:
        console.print("[bold red]LLM Error: QX_MODEL_NAME environment variable not set.[/bold red]")
        return None

    if not vertex_project_id:
        console.print("[bold yellow]LLM Warning: QX_VERTEX_PROJECT_ID not found, relying on PydanticAI/gcloud defaults.[/bold yellow]")
    if not vertex_location:
        console.print("[bold yellow]LLM Warning: QX_VERTEX_LOCATION not found, relying on PydanticAI/gcloud defaults.[/bold yellow]")

    # Load and format the system prompt
    system_prompt_content = load_and_format_system_prompt()

    try:
        agent = Agent(
            model_name,
            tools=[read_file, write_file],
            system_prompt=system_prompt_content
        )
        console.print("[green]LLM Agent initialized successfully with read_file, write_file tools and dynamic system prompt.[/green]")
        return agent
    except Exception as e:
        console.print(f"[bold red]LLM Error initializing PydanticAI Agent: {e}[/bold red]")
        return None

async def query_llm(
    agent: Agent,
    user_input: str,
    message_history: Optional[List[ModelMessage]] = None
) -> Optional[AgentRunResult]:
    """
    Asynchronously queries the LLM agent with the user's input and conversation history.

    Args:
        agent: The initialized PydanticAI Agent instance.
        user_input: The input string from the user.
        message_history: Optional list of previous messages for context.

    Returns:
        The AgentRunResult object from the agent, or None if an error occurs or agent is not initialized.
    """
    if not agent:
        console.print("[bold red]LLM Error: Agent not initialized. Cannot process query.[/bold red]")
        return None
    try:
        result: AgentRunResult = await agent.run(user_input, message_history=message_history)
        return result
    except Exception as e:
        console.print(f"[bold red]LLM Error during agent execution: {e}[/bold red]")
        return None