import asyncio
import os

from dotenv import load_dotenv
from rich.console import Console

from .cli.qprompt import get_user_input  # Updated import
from .core.llm import initialize_llm_agent, query_llm  # Updated import

# Load environment variables from .env file
load_dotenv()

# Get environment variables for display and initial checks
model_name_env = os.getenv("QX_MODEL_NAME")
vertex_project_id_env = os.getenv("QX_VERTEX_PROJECT_ID")
vertex_location_env = os.getenv("QX_VERTEX_LOCATION")

# Initialize Rich Console for better output
console = Console()


async def main():
    """
    Main function to run the QX agent.
    """
    if not model_name_env:
        console.print(
            "[bold red]Error: QX_MODEL_NAME environment variable not set.[/bold red]"
        )
        return

    if not vertex_project_id_env:
        console.print(
            "[bold red]Error: QX_VERTEX_PROJECT_ID environment variable not set.[/bold red]"
        )
        return

    if not vertex_location_env:
        console.print(
            "[bold red]Error: QX_VERTEX_LOCATION environment variable not set.[/bold red]"
        )
        return

    # Initialize the PydanticAI Agent via the new module
    agent = initialize_llm_agent()
    if not agent:
        # Error message already printed by initialize_llm_agent
        return

    console.print(f"[green]QX Agent initialized with model: {model_name_env}[/green]")
    console.print(
        f"[blue]Using Vertex AI Project: {vertex_project_id_env}, Location: {vertex_location_env}[/blue]"
    )
    console.print("\nWelcome to QX! Type 'exit' or 'quit' to end the session.")

    while True:
        try:
            user_input = await get_user_input(console)

            if user_input.lower() in ["exit", "quit"]:
                console.print("[yellow]Exiting QX. Goodbye![/yellow]")
                break

            if not user_input.strip():
                continue

            console.print("[italic yellow]QX is thinking...[/italic yellow]")
            # Query the LLM using the new module function
            response_output = await query_llm(agent, user_input)

            # The query_llm function now returns the output directly or an error string
            if (
                "Error during agent execution:" in response_output
                or "LLM Agent not initialized" in response_output
            ):
                console.print(f"\n[bold red]QX Error:[/bold red] {response_output}\n")
            else:
                console.print(f"\n[bold green]QX:[/bold green] {response_output}\n")

        except KeyboardInterrupt:
            console.print("\n[yellow]Interrupted. Exiting QX. Goodbye![/yellow]")
            break
        except EOFError:
            console.print("\n[yellow]Exiting QX (EOF). Goodbye![/yellow]")
            break
        except Exception as e:
            console.print(
                f"[bold red]An unexpected error occurred in main loop: {e}[/bold red]"
            )
            break


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[yellow]QX terminated by user.[/yellow]")
    except Exception as e:
        console.print(f"[bold red]Critical error starting QX: {e}[/bold red]")