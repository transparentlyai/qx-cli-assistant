import asyncio
import logging
import os
import sys

from rich.console import Console as RichConsole
from rich.panel import Panel
from rich.text import Text
from rich.theme import Theme

from qx.cli.qprompt import get_user_input
from qx.core.config_manager import load_runtime_configurations
from qx.core.constants import (
    DEFAULT_MODEL,
    DEFAULT_VERTEXAI_LOCATION,
    CLI_THEMES,
    DEFAULT_CLI_THEME
)
from qx.core.llm import initialize_llm_agent, query_llm
from qx.core.approvals import ApprovalManager # Import ApprovalManager
from pydantic_ai.messages import ModelMessage
from typing import List, Optional, Any

# Configure logging for the application
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("qx")

# Global console instance - will be themed and potentially reassigned in _async_main
q_console = RichConsole()


async def _async_main():
    """Asynchronous main function to handle the QX agent logic."""
    global q_console

    load_runtime_configurations()

    theme_name_from_env = os.getenv("CLI_THEME")
    selected_theme_name = DEFAULT_CLI_THEME

    if theme_name_from_env:
        if theme_name_from_env in CLI_THEMES:
            selected_theme_name = theme_name_from_env
            logger.info(f"Using CLI theme from environment variable: {selected_theme_name}")
        else:
            q_console.print(
                f"[yellow]Warning:[/yellow] CLI_THEME environment variable '{theme_name_from_env}' is invalid. "
                f"Available themes: {list(CLI_THEMES.keys())}. "
                f"Falling back to default theme: {DEFAULT_CLI_THEME}.",
            )
            logger.warning(
                f"CLI_THEME environment variable '{theme_name_from_env}' is invalid. "
                f"Falling back to default theme: {DEFAULT_CLI_THEME}."
            )
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
    else:
        try:
            rich_theme_obj = Theme(final_theme_dict)
            q_console = RichConsole(theme=rich_theme_obj)
            logger.info(f"Successfully applied CLI theme: {selected_theme_name}")
        except Exception as e:
            q_console.print(f"[bold red]Error applying theme '{selected_theme_name}': {e}. Using basic console.[/bold red]")
            logger.error(f"Error applying theme '{selected_theme_name}': {e}. Using basic console.", exc_info=True)

    # Instantiate ApprovalManager after the console is potentially themed
    approval_manager = ApprovalManager(console=q_console)

    q_console.print(
        Panel(
            Text("Welcome to QX - Your AI Coding Agent by Transparently.AI", justify="center"),
            title="QX Agent",
            border_style="title",
        )
    )

    model_name_from_env = os.environ.get("QX_MODEL_NAME", DEFAULT_MODEL)
    project_id = os.environ.get("QX_VERTEX_PROJECT_ID")
    location = os.environ.get("QX_VERTEX_LOCATION", DEFAULT_VERTEXAI_LOCATION if project_id else None)

    if not model_name_from_env:
        q_console.print(
            "[error]Critical Error:[/] QX_MODEL_NAME missing."
        )
        sys.exit(1)

    if project_id and not location:
        q_console.print(
            f"[warning]Warning:[/] QX_VERTEX_PROJECT_ID ('{project_id}') set, "
            f"but QX_VERTEX_LOCATION is not. Using default: '{DEFAULT_VERTEXAI_LOCATION}'.",
        )
        location = DEFAULT_VERTEXAI_LOCATION

    q_console.print(f"Using Model: [info]{model_name_from_env}[/]")
    if project_id:
        q_console.print(f"Vertex AI Project ID: [info]{project_id}[/]")
        q_console.print(f"Vertex AI Location: [info]{location}[/]")

    agent = initialize_llm_agent(
        model_name_str=model_name_from_env,
        project_id=project_id,
        location=location,
        console=q_console,
        approval_manager=approval_manager # Pass approval_manager to agent initialization
    )

    if agent is None:
        q_console.print(
            "[error]Critical Error:[/] Failed to initialize LLM agent. Exiting."
        )
        sys.exit(1)

    current_message_history: Optional[List[ModelMessage]] = None

    while True:
        try:
            # Pass both the themed console and the approval_manager to get_user_input
            user_input = await get_user_input(q_console, approval_manager)
            
            # Handle empty input from aborted prompt (e.g. Ctrl+C in prompt)
            if user_input == "" and not approval_manager.is_globally_approved(): # Check if prompt returned empty from interrupt
                # qprompt.py already prints a message for prompt abort.
                # Simply continue to re-display the prompt.
                continue

            if user_input.lower() in ["exit", "quit"]:
                q_console.print("Exiting QX. Goodbye!", style="info")
                break
            if not user_input.strip(): # Handles cases where user just presses Enter on an empty line
                continue

            run_result: Optional[Any] = await query_llm(
                agent, user_input, message_history=current_message_history, console=q_console
            )

            if run_result:
                q_console.print("\n[title]QX:[/]")
                if hasattr(run_result, 'output'):
                    q_console.print(run_result.output)
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
            # This handles Ctrl+C if it occurs during query_llm or other processing
            # within this try block (but not during get_user_input itself, which has its own handling).
            q_console.print("\nOperation cancelled. Returning to prompt. Type 'exit' or 'quit' to exit.", style="warning")
            current_message_history = None # Optionally reset history on cancel
            continue # Continue to the next iteration of the loop, re-displaying the prompt.
        except Exception as e:
            logger.error(f"An unexpected error occurred in the main loop: {e}", exc_info=True)
            q_console.print(f"[error]Critical Error:[/] An unexpected error occurred: {e}")
            q_console.print("Exiting QX due to critical error.", style="error")
            break


def main():
    try:
        asyncio.run(_async_main())
    except Exception as e:
        # This handles errors during asyncio.run() itself or if _async_main re-raises an unhandled exception.
        logger.critical(f"Critical error running QX: {e}", exc_info=True)
        # Ensure q_console is used if initialized, otherwise print basic.
        # This might be redundant if q_console is always initialized early, but safe.
        console_to_use = q_console if 'q_console' in globals() and q_console else RichConsole()
        console_to_use.print(f"[bold red]Critical error running QX:[/bold red] {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        # This handles Ctrl+C if it occurs outside the _async_main loop 
        # (e.g., during initial setup before the loop, or if _async_main exits cleanly and then Ctrl+C).
        console_to_use = q_console if 'q_console' in globals() and q_console else RichConsole()
        console_to_use.print("\nQX terminated by user.", style="info")
        sys.exit(0)


if __name__ == "__main__":
    main()