import asyncio
import logging
import os
import sys
from typing import Any, List, Optional

from openai.types.chat import ChatCompletionMessageParam # Import for message history type
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text

from qx.cli.console import QXConsole, qx_console, show_spinner
from qx.cli.qprompt import get_user_input
from qx.core.config_manager import load_runtime_configurations
from qx.core.constants import (
    DEFAULT_MODEL,
    DEFAULT_SYNTAX_HIGHLIGHT_THEME,
)
from qx.core.llm import initialize_llm_agent, query_llm, QXLLMAgent # Import QXLLMAgent

# --- QX Version ---
QX_VERSION = "0.3.3" # Updated for this refactor
# --- End QX Version ---

# --- Configure logging for the application ---
logger = logging.getLogger("qx") # Initialize logger globally

def _configure_logging():
    """Configures the application's logging based on QX_LOG_LEVEL environment variable."""
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
    logger.info(
        f"QX application log level set to: {logging.getLevelName(effective_log_level)} ({effective_log_level})"
    )
# --- End logging configuration ---

def _initialize_agent() -> QXLLMAgent:
    """
    Initializes and returns the QXLLMAgent.
    Exits if QX_MODEL_NAME is not set or agent initialization fails.
    """
    model_name_from_env = os.environ.get("QX_MODEL_NAME", DEFAULT_MODEL)
    
    if not model_name_from_env:
        qx_console.print("[error]Critical Error:[/] QX_MODEL_NAME environment variable not set. Please set it to an OpenRouter model string (e.g., 'google/gemini-2.5-flash-preview-05-20:thinking').")
        sys.exit(1)

    logger.debug(f"Initializing LLM agent with parameters:")
    logger.debug(f"  Model Name: {model_name_from_env}")

    agent: Optional[QXLLMAgent] = initialize_llm_agent(
        model_name_str=model_name_from_env,
        console=qx_console,
    )

    if agent is None:
        qx_console.print(
            "[error]Critical Error:[/] Failed to initialize LLM agent. Exiting."
        )
        sys.exit(1)
    return agent

def _handle_model_command(agent: QXLLMAgent):
    """Displays information about the current LLM model configuration."""
    model_info_content = f"[bold]Current LLM Model Configuration:[/bold]\n"
    model_info_content += f"  Model Name: [green]{agent.model_name}[/green]\n"
    # OpenRouter models don't have a direct "provider.base_url" attribute on the agent itself
    # The base_url is part of the internal client configuration.
    # For simplicity, we can just state it's OpenRouter.
    model_info_content += f"  Provider: [green]OpenRouter (https://openrouter.ai/api/v1)[/green]\n"
    
    # Access model settings directly from agent attributes
    temperature_val = agent.temperature
    max_tokens_val = agent.max_output_tokens
    reasoning_effort_val = agent.reasoning_effort # Changed from thinking_budget

    model_info_content += f"  Temperature: [green]{temperature_val}[/green]\n"
    model_info_content += f"  Max Output Tokens: [green]{max_tokens_val}[/green]\n"
    model_info_content += f"  Reasoning Effort: [green]{reasoning_effort_val if reasoning_effort_val else 'None'}[/green]\n" # Changed from Thinking Budget

    qx_console.print(Panel(model_info_content, title="LLM Model Info", border_style="blue"))

async def _handle_llm_interaction(
    agent: QXLLMAgent,
    user_input: str,
    current_message_history: Optional[List[ChatCompletionMessageParam]],
    code_theme_to_use: str,
) -> Optional[List[ChatCompletionMessageParam]]:
    """
    Handles the interaction with the LLM, including spinner display and response processing.
    Returns the updated message history.
    """
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
            output_content = str(run_result.output) if run_result.output is not None else ""
            markdown_output = Markdown(
                output_content, code_theme=code_theme_to_use
            )
            qx_console.print(markdown_output)
            qx_console.print("\n")
            if hasattr(run_result, "all_messages"):
                return run_result.all_messages()
            else:
                logger.warning(
                    "run_result is missing 'all_messages' attribute."
                )
                return current_message_history # Return original if no new messages
        else:
            logger.error(
                f"run_result is missing 'output' attribute. run_result type: {type(run_result)}, value: {run_result}"
            )
            qx_console.print(
                "[error]Error:[/] Unexpected response structure from LLM."
            )
            return current_message_history
    else:
        qx_console.print(
            "[warning]Info:[/] No response generated or an error occurred."
        )
        return current_message_history


async def _async_main():
    """Asynchronous main function to handle the QX agent logic."""
    _configure_logging()
    load_runtime_configurations()

    logger.info("CLI theming system has been removed. Using default Rich console styling.")

    syntax_theme_from_env = os.getenv("QX_SYNTAX_HIGHLIGHT_THEME")
    code_theme_to_use = (
        syntax_theme_from_env
        if syntax_theme_from_env
        else DEFAULT_SYNTAX_HIGHLIGHT_THEME
    )
    logger.info(
        f"Using syntax highlighting theme for Markdown code blocks: {code_theme_to_use}"
    )

    agent = _initialize_agent()

    info_text = f"QX ver:{QX_VERSION} - {agent.model_name}"
    qx_console.print(Text(info_text, style="dim"))

    current_message_history: Optional[List[ChatCompletionMessageParam]] = None

    while True:
        try:
            user_input = await get_user_input(qx_console) 

            if user_input == "": 
                continue

            if user_input.lower() in ["exit", "quit"]:
                break
            if not user_input.strip():
                continue

            if user_input.strip().lower() == "/model":
                _handle_model_command(agent)
                continue

            current_message_history = await _handle_llm_interaction(
                agent, user_input, current_message_history, code_theme_to_use
            )

        except KeyboardInterrupt:
            qx_console.print(
                "\nOperation cancelled by Ctrl+C. Returning to prompt.", style="yellow"
            )
            current_message_history = None
            continue
        except asyncio.CancelledError:
            qx_console.print(
                "\nOperation cancelled (async). Returning to prompt.", style="yellow"
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
            qx_console.print("Exiting QX due to critical error.", style="bold red")
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