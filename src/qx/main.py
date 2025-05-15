import asyncio
import os
from typing import List, Optional  # Added for type hinting

from pydantic_ai.agent import AgentRunResult  # For type hinting run_result
from pydantic_ai.messages import ModelMessage  # Added for type hinting
from rich.console import Console

from .cli.qprompt import get_user_input
from .core.config_manager import load_runtime_configurations
from .core.llm import initialize_llm_agent, query_llm

# Load all runtime configurations, including .env files
load_runtime_configurations()

# Get environment variables for display and initial checks
# These are now fetched *after* load_runtime_configurations has run
model_name_env = os.getenv("QX_MODEL_NAME")
vertex_project_id_env = os.getenv("QX_VERTEX_PROJECT_ID")
vertex_location_env = os.getenv("QX_VERTEX_LOCATION")

# Initialize Rich Console for better output
console = Console()


async def _async_main():
    """
    Core asynchronous logic for the QX agent.
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

    agent = initialize_llm_agent()
    if not agent:
        return

    console.print(f"[green]QX Agent initialized with model: {model_name_env}[/green]")
    console.print(
        f"[blue]Using Vertex AI Project: {vertex_project_id_env}, Location: {vertex_location_env}[/blue]"
    )
    console.print("\nWelcome to QX! Type 'exit' or 'quit' to end the session.")

    current_message_history: Optional[List[ModelMessage]] = None

    while True:
        try:
            user_input = await get_user_input(console)

            if user_input.lower() in ["exit", "quit"]:
                console.print("[yellow]Exiting QX. Goodbye![/yellow]")
                break

            if not user_input.strip():
                continue

            console.print("[italic yellow]QX is thinking...[/italic yellow]")

            run_result: Optional[AgentRunResult] = await query_llm(
                agent, user_input, message_history=current_message_history
            )

            if run_result:
                console.print(f"\n[bold green]QX:[/bold green] {run_result.output}\n")
                # Use all_messages() to accumulate the entire conversation history
                current_message_history = run_result.all_messages()
            else:
                console.print(
                    f"\n[bold red]QX Error:[/bold red] Failed to get a response from the LLM.\n"
                )
                # Optionally, decide how to handle history on error (e.g., reset or keep)
                # current_message_history = None

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


def main():
    """
    Main synchronous entry point function to run the QX agent.
    This function initializes and runs the asyncio event loop.
    """
    try:
        asyncio.run(_async_main())
    except KeyboardInterrupt:
        console.print("\n[yellow]QX terminated by user.[/yellow]")
    except Exception as e:
        console.print(f"[bold red]Critical error running QX: {e}[/bold red]")


if __name__ == "__main__":
    main()