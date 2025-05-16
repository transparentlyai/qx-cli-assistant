import asyncio
import logging
import os
import sys

from rich.panel import Panel
from rich.text import Text
from rich.theme import Theme as RichTheme

# QX imports
from qx.cli.qprompt import get_user_input
from qx.cli.console import qx_console, show_spinner, QXConsole # Import QXConsole for set_active_status
from qx.core.config_manager import load_runtime_configurations
from qx.core.constants import (
    DEFAULT_MODEL,
    DEFAULT_VERTEXAI_LOCATION,
    CLI_THEMES,
    DEFAULT_CLI_THEME
)
from qx.core.llm import initialize_llm_agent, query_llm
from qx.core.approvals import ApprovalManager
from pydantic_ai.messages import ModelMessage
from typing import List, Optional, Any

# --- Configure logging for the application ---
log_level_name = os.getenv("QX_LOG_LEVEL", "ERROR").upper()
LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}
effective_log_level = LOG_LEVELS.get(log_level_name, logging.ERROR)

logging.basicConfig(
    level=effective_log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("qx")
logger.info(f"QX application log level set to: {logging.getLevelName(effective_log_level)} ({effective_log_level})")
# --- End logging configuration ---


async def _async_main():
    """Asynchronous main function to handle the QX agent logic."""
    load_runtime_configurations()

    theme_name_from_env = os.getenv("CLI_THEME")
    selected_theme_name = DEFAULT_CLI_THEME

    if theme_name_from_env:
        if theme_name_from_env in CLI_THEMES:
            selected_theme_name = theme_name_from_env
            logger.info(f"Using CLI theme from environment variable: {selected_theme_name}")
        else:
            qx_console.print(
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
        qx_console.print(
            f"[bold red]Error:[/bold red] Selected theme '{selected_theme_name}' not found in CLI_THEMES. "
            f"Using a basic console without full custom theming."
        )
        logger.error(
            f"Selected theme '{selected_theme_name}' not found in CLI_THEMES. "
            f"Using basic console."
        )
    else:
        try:
            rich_theme_obj = RichTheme(final_theme_dict)
            qx_console.apply_theme(rich_theme_obj)
            logger.info(f"Successfully applied CLI theme: {selected_theme_name}")
        except Exception as e:
            qx_console.print(f"[bold red]Error applying theme '{selected_theme_name}': {e}. Using basic console.[/bold red]")
            logger.error(f"Error applying theme '{selected_theme_name}': {e}. Using basic console.", exc_info=True)

    approval_manager = ApprovalManager(console=qx_console)

    qx_console.print(
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
        qx_console.print("[error]Critical Error:[/] QX_MODEL_NAME missing.")
        sys.exit(1)

    if project_id and not location:
        qx_console.print(
            f"[warning]Warning:[/] QX_VERTEX_PROJECT_ID ('{project_id}') set, "
            f"but QX_VERTEX_LOCATION is not. Using default: '{DEFAULT_VERTEXAI_LOCATION}'.",
        )
        location = DEFAULT_VERTEXAI_LOCATION

    qx_console.print(f"Using Model: [info]{model_name_from_env}[/]")
    if project_id:
        qx_console.print(f"Vertex AI Project ID: [info]{project_id}[/]")
        qx_console.print(f"Vertex AI Location: [info]{location}[/]")

    agent = initialize_llm_agent(
        model_name_str=model_name_from_env,
        project_id=project_id,
        location=location,
        console=qx_console,
        approval_manager=approval_manager
    )

    if agent is None:
        qx_console.print("[error]Critical Error:[/] Failed to initialize LLM agent. Exiting.")
        sys.exit(1)

    current_message_history: Optional[List[ModelMessage]] = None

    while True:
        try:
            user_input = await get_user_input(qx_console, approval_manager)

            if user_input == "" and not approval_manager.is_globally_approved():
                continue

            if user_input.lower() in ["exit", "quit"]:
                qx_console.print("Exiting QX. Goodbye!", style="info")
                break
            if not user_input.strip():
                continue

            run_result: Optional[Any] = None
            spinner_status = show_spinner("QX is thinking...")
            QXConsole.set_active_status(spinner_status) # Register the spinner
            try:
                with spinner_status: # Use context manager for the spinner
                    run_result = await query_llm(
                        agent, user_input, message_history=current_message_history, console=qx_console
                    )
            finally:
                QXConsole.set_active_status(None) # Unregister the spinner

            if run_result:
                qx_console.print("\n[title]QX:[/]")
                if hasattr(run_result, 'output'):
                    qx_console.print(run_result.output)
                    if hasattr(run_result, 'all_messages'):
                        current_message_history = run_result.all_messages()
                    else:
                        logger.warning("run_result is missing 'all_messages' attribute.")
                else:
                    logger.error(f"run_result is missing 'output' attribute. run_result type: {type(run_result)}, value: {run_result}")
                    qx_console.print("[error]Error:[/] Unexpected response structure from LLM.")
            else:
                qx_console.print("[warning]Info:[/] No response generated or an error occurred.")

        except KeyboardInterrupt:
            qx_console.print("\nOperation cancelled by Ctrl+C. Returning to prompt.", style="warning")
            current_message_history = None
            continue
        except asyncio.CancelledError:
            qx_console.print("\nOperation cancelled (async). Returning to prompt.", style="warning")
            current_message_history = None
            continue
        except Exception as e:
            logger.error(f"An unexpected error occurred in the main loop: {e}", exc_info=True)
            qx_console.print(f"[error]Critical Error:[/] An unexpected error occurred: {e}")
            qx_console.print("Exiting QX due to critical error.", style="error")
            break


def main():
    try:
        asyncio.run(_async_main())
    except KeyboardInterrupt:
        qx_console.print("\nQX terminated by user.", style="info")
        sys.exit(0)
    except Exception as e:
        fallback_logger = logging.getLogger("qx.critical")
        fallback_logger.critical(f"Critical error running QX: {e}", exc_info=True)
        qx_console.print(f"[bold red]Critical error running QX:[/bold red] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()