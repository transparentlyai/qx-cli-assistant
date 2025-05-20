import asyncio
import logging
import os
import sys
from typing import Any, List, Optional

from pydantic_ai.messages import ModelMessage
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text

from qx.cli.console import QXConsole, qx_console, show_spinner

# QX imports
from qx.cli.qprompt import get_user_input
from qx.core.approvals import ApprovalManager
from qx.core.config_manager import load_runtime_configurations
from qx.core.constants import (
    DEFAULT_MODEL,
    DEFAULT_SYNTAX_HIGHLIGHT_THEME,
    DEFAULT_VERTEXAI_LOCATION,
)
from qx.core.llm import initialize_llm_agent, query_llm

# --- QX Version ---
QX_VERSION = "0.3.2"
# --- End QX Version ---

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
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("qx")
logger.info(
    f"QX application log level set to: {logging.getLevelName(effective_log_level)} ({effective_log_level})"
)
# --- End logging configuration ---


async def _async_main():
    """Asynchronous main function to handle the QX agent logic."""
    load_runtime_configurations()

    logger.info("CLI theming system has been removed. Using default Rich console styling.")

    # Determine syntax highlighting theme for Markdown code blocks AND ApprovalManager previews
    syntax_theme_from_env = os.getenv("QX_SYNTAX_HIGHLIGHT_THEME")
    code_theme_to_use = (
        syntax_theme_from_env
        if syntax_theme_from_env
        else DEFAULT_SYNTAX_HIGHLIGHT_THEME
    )
    logger.info(
        f"Using syntax highlighting theme for Markdown code blocks and previews: {code_theme_to_use}"
    )

    # Pass the determined theme to ApprovalManager
    approval_manager = ApprovalManager(
        console=qx_console, syntax_highlight_theme=code_theme_to_use
    )

    model_name_from_env = os.environ.get("QX_MODEL_NAME", DEFAULT_MODEL)
    project_id = os.environ.get("QX_VERTEX_PROJECT_ID")
    location = os.environ.get(
        "QX_VERTEX_LOCATION", DEFAULT_VERTEXAI_LOCATION if project_id else None
    )

    if not model_name_from_env:
        qx_console.print("[error]Critical Error:[/] QX_MODEL_NAME missing.")
        sys.exit(1)

    if project_id and not location:
        qx_console.print(
            f"[warning]Warning:[/] QX_VERTEX_PROJECT_ID ('{project_id}') set, "
            f"but QX_VERTEX_LOCATION is not. Using default: '{DEFAULT_VERTEXAI_LOCATION}'.",
        )
        location = DEFAULT_VERTEXAI_LOCATION

    agent = initialize_llm_agent(
        model_name_str=model_name_from_env,
        project_id=project_id,
        location=location,
        console=qx_console,
        approval_manager=approval_manager,
    )

    if agent is None:
        qx_console.print(
            "[error]Critical Error:[/] Failed to initialize LLM agent. Exiting."
        )
        sys.exit(1)

    # Display QX version and model information
    info_text = f"QX ver:{QX_VERSION} - {model_name_from_env}"
    qx_console.print(Text(info_text, style="dim"))

    current_message_history: Optional[List[ModelMessage]] = None

    while True:
        try:
            user_input = await get_user_input(qx_console, approval_manager)

            if user_input == "" and not approval_manager.is_globally_approved():
                continue

            if user_input.lower() in ["exit", "quit"]:
                break
            if not user_input.strip():
                continue

            run_result: Optional[Any] = None
            spinner_status = show_spinner("QX is thinking...")
            QXConsole.set_active_status(spinner_status)
            try:
                with spinner_status:
                    run_result = await query_llm(
                        agent,
                        user_input,
                        message_history=current_message_history,
                        console=qx_console,
                    )
            finally:
                QXConsole.set_active_status(None)

            if run_result:
                if hasattr(run_result, "output"):
                    markdown_output = Markdown(
                        run_result.output, code_theme=code_theme_to_use
                    )
                    qx_console.print(markdown_output)
                    qx_console.print("\n")
                    if hasattr(run_result, "all_messages"):
                        current_message_history = run_result.all_messages()
                    else:
                        logger.warning(
                            "run_result is missing 'all_messages' attribute."
                        )
                else:
                    logger.error(
                        f"run_result is missing 'output' attribute. run_result type: {type(run_result)}, value: {run_result}"
                    )
                    qx_console.print(
                        "[error]Error:[/] Unexpected response structure from LLM."
                    )
            else:
                qx_console.print(
                    "[warning]Info:[/] No response generated or an error occurred."
                )

        except KeyboardInterrupt:
            qx_console.print(
                "\nOperation cancelled by Ctrl+C. Returning to prompt.", style="yellow" # Changed style
            )
            current_message_history = None
            continue
        except asyncio.CancelledError:
            qx_console.print(
                "\nOperation cancelled (async). Returning to prompt.", style="yellow" # Changed style
            )
            current_message_history = None
            continue
        except Exception as e:
            logger.error(
                f"An unexpected error occurred in the main loop: {e}", exc_info=True
            )
            qx_console.print(
                f"[error]Critical Error:[/] An unexpected error occurred: {e}"
            )
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