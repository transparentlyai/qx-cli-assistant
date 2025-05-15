import os
from typing import List, Optional
from pydantic_ai import Agent
from pydantic_ai.messages import ModelMessage # Corrected import path for ModelMessage
from pydantic_ai.agent import AgentRunResult 
from rich.console import Console

# Import the read_file tool
from ..tools.read_file import read_file

console = Console()

def initialize_llm_agent():
    """
    Initializes the PydanticAI LLM agent.

    Retrieves model configuration from environment variables and registers tools.

    Returns:
        An initialized Agent instance or None if initialization fails.
    """
    model_name = os.getenv("QX_MODEL_NAME")
    vertex_project_id = os.getenv("QX_VERTEX_PROJECT_ID")
    vertex_location = os.getenv("QX_VERTEX_LOCATION")

    if not model_name:
        console.print("[bold red]LLM Error: QX_MODEL_NAME environment variable not set.[/bold red]")
        return None
    
    # These are checked in main.py, but good to be aware of them here too.
    if not vertex_project_id:
        console.print("[bold yellow]LLM Warning: QX_VERTEX_PROJECT_ID not found, relying on PydanticAI/gcloud defaults.[/bold yellow]")
    if not vertex_location:
        console.print("[bold yellow]LLM Warning: QX_VERTEX_LOCATION not found, relying on PydanticAI/gcloud defaults.[/bold yellow]")

    try:
        # Register the read_file tool with the agent
        agent = Agent(model_name, tools=[read_file])
        console.print("[green]LLM Agent initialized successfully with read_file tool.[/green]")
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
        # The agent.run() method returns an AgentRunResult for async non-streaming runs
        result: AgentRunResult = await agent.run(user_input, message_history=message_history)
        return result
    except Exception as e:
        console.print(f"[bold red]LLM Error during agent execution: {e}[/bold red]")
        return None