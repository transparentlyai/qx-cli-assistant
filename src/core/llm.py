import os
from pydantic_ai import Agent
from rich.console import Console

console = Console()

def initialize_llm_agent():
    """
    Initializes the PydanticAI LLM agent.

    Retrieves model configuration from environment variables.

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
        agent = Agent(model_name)
        return agent
    except Exception as e:
        console.print(f"[bold red]LLM Error initializing PydanticAI Agent: {e}[/bold red]")
        return None

async def query_llm(agent: Agent, user_input: str):
    """
    Asynchronously queries the LLM agent with the user's input.

    Args:
        agent: The initialized PydanticAI Agent instance.
        user_input: The input string from the user.

    Returns:
        The output string from the LLM, or an error message string if an exception occurs.
    """
    if not agent:
        return "LLM Agent not initialized. Cannot process query."
    try:
        result = await agent.run(user_input)
        return result.output
    except Exception as e:
        console.print(f"[bold red]LLM Error during agent execution: {e}[/bold red]")
        return f"Error during agent execution: {e}"
