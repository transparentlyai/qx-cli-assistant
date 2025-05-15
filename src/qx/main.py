import asyncio
import logging
import os
import sys

from rich.console import Console as RichConsole
from rich.panel import Panel
from rich.text import Text
from rich.theme import Theme # New import

from qx.cli.qprompt import get_user_input
from qx.core.config_manager import load_runtime_configurations
from qx.core.constants import ( # New imports
    DEFAULT_MODEL,
    DEFAULT_VERTEXAI_LOCATION,
    CLI_THEMES,
    DEFAULT_CLI_THEME
)
from qx.core.llm import initialize_llm_agent, query_llm
from pydantic_ai.messages import ModelMessage # For type hinting message history
from typing import List, Optional, Any # For AgentRunResult type hint

# Configure logging for the application
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("qx")

# Global console instance - will be themed and potentially reassigned in _async_main
q_console = RichConsole()


async def _async_main():
    """Asynchronous main function to handle the QX agent logic."""
    global q_console # Allow reassignment of the global console instance

    load_runtime_configurations() # Loads env vars including CLI_THEME

    # --- Theme Loading Logic ---
    theme_name_from_env = os.getenv("CLI_THEME")
    selected_theme_name = DEFAULT_CLI_THEME

    if theme_name_from_env:
        if theme_name_from_env in CLI_THEMES:
            selected_theme_name = theme_name_from_env
            logger.info(f"Using CLI theme from environment variable: {selected_theme_name}")
        else:
            # Use the initial q_console for this warning, as the themed one isn't ready
            q_console.print(
                f"[yellow]Warning:[/yellow] CLI_THEME environment variable '{theme_name_from_env}' is invalid. "
                f"Available themes: {list(CLI_THEMES.keys())}. "
                f"Falling back to default theme: {DEFAULT_CLI_THEME}.",
            )
            logger.warning(
                f"CLI_THEME environment variable '{theme_name_from_env}' is invalid. "
                f"Falling back to default theme: {DEFAULT_CLI_THEME}."
            )
            # selected_theme_name remains DEFAULT_CLI_THEME
    else:
        logger.info(f"Using default CLI theme: {selected_theme_name}")

    final_theme_dict = CLI_THEMES.get(selected_theme_name)
    if not final_theme_dict:
        q_console.print(
            f"[bold red]Error:[/bold red] Selected theme '{selected_theme_name}' not found in CLI_THEMES. "
            f"Using a basic console without full custom theming."
        )
        logger.error(
            f"Selected theme '{selected_theme_name}' not found in CLI_THEMES. "
            f"Using basic console."
        )
        # q_console remains as initially defined (basic RichConsole)
    else:
        try:
            rich_theme_obj = Theme(final_theme_dict)
            q_console = RichConsole(theme=rich_theme_obj) # Reassign global q_console with the theme
            logger.info(f"Successfully applied CLI theme: {selected_theme_name}")
        except Exception as e:
            q_console.print(f"[bold red]Error applying theme '{selected_theme_name}': {e}. Using basic console.[/bold red]")
            logger.error(f"Error applying theme '{selected_theme_name}': {e}. Using basic console.", exc_info=True)
            # q_console remains as initially defined (basic RichConsole)
    # --- End Theme Loading Logic ---

    q_console.print(
        Panel(
            Text("Welcome to QX - Your AI Coding Agent by Transparently.AI", justify="center"),
            title="QX Agent",
            border_style="title", # Use a theme-defined style if available, or Rich default
        )
    )

    # This variable holds the full model string, e.g., "google-vertex:gemini-2.0-flash"
    model_name_from_env = os.environ.get("QX_MODEL_NAME", DEFAULT_MODEL)
    project_id = os.environ.get("QX_VERTEX_PROJECT_ID")
    location = os.environ.get("QX_VERTEX_LOCATION", DEFAULT_VERTEXAI_LOCATION if project_id else None)

    if not model_name_from_env:
        q_console.print(
            "[error]Critical Error:[/] QX_MODEL_NAME missing." # Using themed style
        )
        sys.exit(1)

    if project_id and not location:
        q_console.print(
            f"[warning]Warning:[/] QX_VERTEX_PROJECT_ID ('{project_id}') set, "
            f"but QX_VERTEX_LOCATION is not. Using default: '{DEFAULT_VERTEXAI_LOCATION}'.",
        )
        location = DEFAULT_VERTEXAI_LOCATION

    q_console.print(f"Using Model: [info]{model_name_from_env}[/]") # Using themed style
    if project_id:
        q_console.print(f"Vertex AI Project ID: [info]{project_id}[/]")
        q_console.print(f"Vertex AI Location: [info]{location}[/]")

    agent = initialize_llm_agent(
        model_name_str=model_name_from_env,
        project_id=project_id,
        location=location,
        console=q_console # Pass the themed console
    )

    if agent is None:
        q_console.print(
            "[error]Critical Error:[/] Failed to initialize LLM agent. Exiting."
        )
        sys.exit(1)

    current_message_history: Optional[List[ModelMessage]] = None

    while True:
        try:
            user_input = await get_user_input(q_console) # Pass themed console
            if user_input.lower() in ["exit", "quit"]:
                q_console.print("Exiting QX. Goodbye!", style="info") # Using themed style
                break
            if not user_input.strip():
                continue

            run_result: Optional[Any] = await query_llm(
                agent, user_input, message_history=current_message_history, console=q_console
            )

            if run_result:
                q_console.print("\n[title]QX:[/]") # Using themed style
                if hasattr(run_result, 'output'):
                    q_console.print(run_result.output) # Output itself is not styled here, LLM provides markup
                    if hasattr(run_result, 'all_messages'):
                        current_message_history = run_result.all_messages()
                    else:
                        logger.warning("run_result is missing 'all_messages' attribute.")
                else:
                    logger.error(f"run_result is missing 'output' attribute. run_result type: {type(run_result)}, value: {run_result}")
                    q_console.print("[error]Error:[/] Unexpected response structure from LLM.")

            else:
                q_console.print(
                    "[warning]Info:[/] No response generated or an error occurred.",
                )

        except KeyboardInterrupt:
            q_console.print("\nExiting QX due to user interruption. Goodbye!", style="info")
            break
        except Exception as e:
            logger.error(f"An unexpected error occurred in the main loop: {e}", exc_info=True)
            q_console.print(f"[error]Critical Error:[/] An unexpected error occurred: {e}")
            break


def main():
    """Synchronous entry point that runs the asyncio event loop."""
    # Note: q_console used here for critical errors will be the initial, un-themed one
    # if _async_main fails before theme initialization. This is acceptable.
    try:
        asyncio.run(_async_main())
    except Exception as e:
        logger.critical(f"Critical error running QX: {e}", exc_info=True)
        q_console.print(f"[bold red]Critical error running QX:[/bold red] {e}") # Fallback style
        sys.exit(1)
    except KeyboardInterrupt:
        q_console.print("\nQX terminated by user.", style="info") # Fallback style or initial console
        sys.exit(0)


if __name__ == "__main__":
    main()