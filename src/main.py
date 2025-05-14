import os
import asyncio
from dotenv import load_dotenv
from pydantic_ai import Agent
from rich.console import Console
# Removed: from rich.prompt import Prompt
from src.cli.qprompt import get_user_input # Added import

# Load environment variables from .env file
load_dotenv()

# Get environment variables
model_name = os.getenv("QX_MODEL_NAME")
vertex_project_id = os.getenv("QX_VERTEX_PROJECT_ID")
vertex_location = os.getenv("QX_VERTEX_LOCATION")

# Initialize Rich Console for better output
console = Console()

async def main():
    """
    Main function to run the QX agent.
    """
    if not model_name:
        console.print("[bold red]Error: QX_MODEL_NAME environment variable not set.[/bold red]")
        return

    if not vertex_project_id:
        console.print("[bold red]Error: QX_VERTEX_PROJECT_ID environment variable not set.[/bold red]")
        return

    if not vertex_location:
        console.print("[bold red]Error: QX_VERTEX_LOCATION environment variable not set.[/bold red]")
        return

    # Initialize the PydanticAI Agent
    # For Vertex AI, project and location are typically handled by the Google Cloud client library
    # if GOOGLE_APPLICATION_CREDENTIALS is set correctly.
    # PydanticAI's 'google-vertex' provider string should pick these up automatically.
    try:
        agent = Agent(model_name)
        console.print(f"[green]QX Agent initialized with model: {model_name}[/green]")
        console.print(f"[blue]Using Vertex AI Project: {vertex_project_id}, Location: {vertex_location}[/blue]")
    except Exception as e:
        console.print(f"[bold red]Error initializing PydanticAI Agent: {e}[/bold red]")
        return

    console.print("\nWelcome to QX! Type 'exit' or 'quit' to end the session.")

    while True:
        try:
            # Modified to use the new function
            user_input = await get_user_input(console)

            if user_input.lower() in ["exit", "quit"]:
                console.print("[yellow]Exiting QX. Goodbye![/yellow]")
                break

            if not user_input.strip():
                continue

            # Run the agent with the user input
            console.print("[italic yellow]QX is thinking...[/italic yellow]")
            try:
                result = await agent.run(user_input)
                console.print(f"\n[bold green]QX:[/bold green] {result.output}\n")
            except Exception as e:
                console.print(f"[bold red]Error during agent execution: {e}[/bold red]")

        except KeyboardInterrupt:
            console.print("\n[yellow]Interrupted. Exiting QX. Goodbye![/yellow]")
            break
        except EOFError: # Added to handle Ctrl+D gracefully during prompt
            console.print("\n[yellow]Exiting QX (EOF). Goodbye![/yellow]")
            break
        except Exception as e:
            console.print(f"[bold red]An unexpected error occurred: {e}[/bold red]")
            break

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[yellow]QX terminated by user.[/yellow]")
    except Exception as e:
        console.print(f"[bold red]Critical error starting QX: {e}[/bold red]")
