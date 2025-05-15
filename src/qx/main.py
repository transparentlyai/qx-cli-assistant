import asyncio
import logging
import os
import sys

from rich.console import Console as RichConsole
from rich.panel import Panel
from rich.text import Text

from qx.cli.qprompt import get_user_input
from qx.core.config_manager import load_runtime_configurations
from qx.core.constants import DEFAULT_MODEL, DEFAULT_VERTEXAI_LOCATION
from qx.core.llm import initialize_llm_agent, query_llm
from pydantic_ai.messages import ModelMessage # For type hinting message history
from typing import List, Optional, Any # For AgentRunResult type hint

# Configure logging for the application
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("qx")

# Global console instance
q_console = RichConsole()


async def _async_main():
    """Asynchronous main function to handle the QX agent logic."""
    q_console.print(
        Panel(
            Text("Welcome to QX - Your AI Coding Agent by Transparently.AI", justify="center"),
            title="QX Agent",
            border_style="bold blue",
        )
    )

    load_runtime_configurations()
    # This variable holds the full model string, e.g., "google-vertex:gemini-2.0-flash"
    model_name_from_env = os.environ.get("QX_MODEL_NAME", DEFAULT_MODEL)
    project_id = os.environ.get("QX_VERTEX_PROJECT_ID")
    location = os.environ.get("QX_VERTEX_LOCATION", DEFAULT_VERTEXAI_LOCATION if project_id else None)

    if not model_name_from_env:
        q_console.print(
            "[bold red]Critical Error:[/bold red] QX_MODEL_NAME missing."
        )
        sys.exit(1)

    if project_id and not location:
        q_console.print(
            f"[yellow]Warning:[/yellow] QX_VERTEX_PROJECT_ID ('{project_id}') set, "
            f"but QX_VERTEX_LOCATION is not. Using default: '{DEFAULT_VERTEXAI_LOCATION}'.",
        )
        location = DEFAULT_VERTEXAI_LOCATION

    q_console.print(f"Using Model: [cyan]{model_name_from_env}[/cyan]")
    if project_id:
        q_console.print(f"Vertex AI Project ID: [cyan]{project_id}[/cyan]")
        q_console.print(f"Vertex AI Location: [cyan]{location}[/cyan]")

    agent = initialize_llm_agent(
        model_name_str=model_name_from_env,
        project_id=project_id,
        location=location,
    )

    if agent is None:
        q_console.print(
            "[bold red]Critical Error:[/bold red] Failed to initialize LLM agent. Exiting."
        )
        sys.exit(1)

    current_message_history: Optional[List[ModelMessage]] = None

    while True:
        try:
            user_input = await get_user_input(q_console)
            if user_input.lower() in ["exit", "quit"]:
                q_console.print("Exiting QX. Goodbye!", style="blue")
                break
            if not user_input.strip():
                continue

            run_result: Optional[Any] = await query_llm(
                agent, user_input, message_history=current_message_history
            )

            if run_result:
                q_console.print("\n[bold magenta]QX:[/bold magenta]")
                if hasattr(run_result, 'output'):
                    q_console.print(run_result.output)
                    if hasattr(run_result, 'all_messages'):
                        current_message_history = run_result.all_messages()
                    else:
                        logger.warning("run_result is missing 'all_messages' attribute.")
                else:
                    logger.error(f"run_result is missing 'output' attribute. run_result type: {type(run_result)}, value: {run_result}")
                    q_console.print("[bold red]Error:[/bold red] Unexpected response structure from LLM.")

            else:
                q_console.print(
                    "[yellow]Info:[/yellow] No response generated or an error occurred.",
                    style="yellow"
                )

        except KeyboardInterrupt:
            q_console.print("\nExiting QX due to user interruption. Goodbye!", style="blue")
            break
        except Exception as e:
            logger.error(f"An unexpected error occurred in the main loop: {e}", exc_info=True)
            q_console.print(f"[bold red]Critical Error:[/bold red] An unexpected error occurred: {e}")
            break


def main():
    """Synchronous entry point that runs the asyncio event loop."""
    try:
        asyncio.run(_async_main())
    except Exception as e:
        logger.critical(f"Critical error running QX: {e}", exc_info=True)
        q_console.print(f"[bold red]Critical error running QX:[/bold red] {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        q_console.print("\nQX terminated by user.", style="blue")
        sys.exit(0)


if __name__ == "__main__":
    main()