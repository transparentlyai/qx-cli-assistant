import argparse
import asyncio
import logging
import os
import sys
import traceback
from pathlib import Path
from typing import Any, List, Optional

import anyio
from openai.types.chat import ChatCompletionMessageParam

from qx.cli.console import TextualRichLogHandler, qx_console, show_spinner
from qx.cli.textual_app import QXApp
from qx.core.config_manager import ConfigManager
from qx.core.constants import DEFAULT_MODEL, DEFAULT_SYNTAX_HIGHLIGHT_THEME
from qx.core.llm import QXLLMAgent, initialize_llm_agent, query_llm
from qx.core.mcp_manager import MCPManager
from qx.core.session_manager import (
    clean_old_sessions,
    load_session_from_path,
    reset_session,
    save_session,
)

# QX Version
QX_VERSION = "0.3.3"

# Configure logging for the application
logger = logging.getLogger("qx")

# Global variable to hold the temporary stream handler
temp_stream_handler: Optional[logging.Handler] = None


def _configure_logging():
    """
    Configures the application's logging based on QX_LOG_LEVEL environment variable.
    Initially logs to file and console (for INFO and above). Console logging for INFO
    will be redirected to Textual RichLog once the app starts.
    """
    global temp_stream_handler

    from pathlib import Path

    log_level_name = os.getenv("QX_LOG_LEVEL", "ERROR").upper()  # Default to INFO
    LOG_LEVELS = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }
    effective_log_level = LOG_LEVELS.get(log_level_name, logging.ERROR)

    # Create log file in ~/tmp directory
    log_dir = Path.home() / "tmp"
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "qx.log"

    # Clear existing handlers to prevent duplicates on re-configuration
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Add file handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    logger.addHandler(file_handler)

    # Add a temporary StreamHandler for INFO and above, to be removed later
    temp_stream_handler = logging.StreamHandler()
    temp_stream_handler.setLevel(effective_log_level)
    temp_stream_handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
    logger.addHandler(temp_stream_handler)

    # Ensure critical errors always go to stderr
    critical_stream_handler = logging.StreamHandler(sys.stderr)
    critical_stream_handler.setLevel(logging.CRITICAL)
    critical_stream_handler.setFormatter(
        logging.Formatter("%(levelname)s: %(message)s")
    )
    logger.addHandler(critical_stream_handler)

    logger.setLevel(effective_log_level)

    # Set up global exception handler
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        logger.critical(
            "Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback)
        )
        # Also write to file directly in case logger fails
        with open(log_file, "a") as f:
            f.write(f"\n=== UNCAUGHT EXCEPTION ===\n")
            traceback.print_exception(exc_type, exc_value, exc_traceback, file=f)
            f.write(f"=== END EXCEPTION ===\n\n")

    sys.excepthook = handle_exception

    logger.debug(
        f"QX application log level set to: {logging.getLevelName(effective_log_level)} ({effective_log_level})"
    )
    logger.debug(f"Logging to file: {log_file}")
    logger.debug("Global exception handler installed")


async def _initialize_agent_with_mcp(mcp_manager: MCPManager) -> QXLLMAgent:
    """
    Initializes and returns the QXLLMAgent, passing the MCPManager.
    Exits if QX_MODEL_NAME is not set or agent initialization fails.
    """
    model_name_from_env = os.environ.get("QX_MODEL_NAME", DEFAULT_MODEL)

    if not model_name_from_env:
        qx_console.print(
            "[red]Critical Error:[/red] QX_MODEL_NAME environment variable not set. Please set it to an OpenRouter model string."
        )
        sys.exit(1)

    logger.debug(f"Initializing LLM agent with parameters:")
    logger.debug(f"  Model Name: {model_name_from_env}")

    # Check if streaming is enabled via environment variable
    enable_streaming = os.environ.get("QX_ENABLE_STREAMING", "true").lower() == "true"

    agent: Optional[QXLLMAgent] = initialize_llm_agent(
        model_name_str=model_name_from_env,
        console=qx_console,
        mcp_manager=mcp_manager,
        enable_streaming=enable_streaming,
    )

    if agent is None:
        qx_console.print(
            "[red]Critical Error:[/red] Failed to initialize LLM agent. Exiting."
        )
        sys.exit(1)
    return agent


def _handle_model_command(agent: QXLLMAgent):
    """
    Displays information about the current LLM model configuration.
    """
    model_info_content = f"[bold]Current LLM Model Configuration:[/bold]\n"
    model_info_content += f"  Model Name: [green]{agent.model_name}[/green]\n"
    model_info_content += (
        f"  Provider: [green]OpenRouter (https://openrouter.ai/api/v1)[/green]\n"
    )

    temperature_val = agent.temperature
    max_tokens_val = agent.max_output_tokens
    reasoning_effort_val = agent.reasoning_effort

    model_info_content += f"  Temperature: [green]{temperature_val}[/green]\n"
    model_info_content += f"  Max Output Tokens: [green]{max_tokens_val}[/green]\n"
    model_info_content += f"  Reasoning Effort: [green]{reasoning_effort_val if reasoning_effort_val else 'None'}[/green]\n"

    qx_console.print(model_info_content)


def _display_version_info():
    """
    Displays QX version, LLM model, and its parameters, then exits.
    """
    _configure_logging()
    config_manager = ConfigManager(qx_console, parent_task_group=None)
    config_manager.load_configurations()

    qx_console.print(f"[bold]QX Version:[/bold] [green]{QX_VERSION}[/green]")

    try:
        temp_mcp_manager = MCPManager(qx_console, parent_task_group=None)
        agent = asyncio.run(_initialize_agent_with_mcp(temp_mcp_manager))
        _handle_model_command(agent)
    except SystemExit:
        qx_console.print(
            "[yellow]Note:[/yellow] Could not display LLM model information as QX_MODEL_NAME is not configured."
        )
    sys.exit(0)


async def _handle_llm_interaction(
    agent: QXLLMAgent,
    user_input: str,
    current_message_history: Optional[List[ChatCompletionMessageParam]],
    code_theme_to_use: str,
    plain_text_output: bool = False,
) -> Optional[List[ChatCompletionMessageParam]]:
    """
    Handles the interaction with the LLM, including streaming display and response processing.
    Returns the updated message history.
    """
    run_result: Optional[Any] = None

    # For streaming, we don't show spinner as content streams in real-time
    if not plain_text_output and not agent.enable_streaming:
        show_spinner("QX is thinking...")

    try:
        run_result = await query_llm(
            agent,
            user_input,
            message_history=current_message_history,
            console=qx_console,
        )
    except Exception as e:
        logger.error(f"Error during LLM interaction: {e}", exc_info=True)
        qx_console.print(f"[red]Error:[/red] {e}")
        return current_message_history

    if run_result:
        if hasattr(run_result, "output"):
            output_content = (
                str(run_result.output) if run_result.output is not None else ""
            )
            if plain_text_output:
                print(output_content)
            else:
                # For streaming, content is already displayed during the stream
                if not agent.enable_streaming and output_content.strip():
                    qx_console.print(output_content)
                    qx_console.print("")
            if hasattr(run_result, "all_messages"):
                return run_result.all_messages()
            else:
                logger.warning("run_result is missing 'all_messages' attribute.")
                return current_message_history
        else:
            logger.error(
                f"run_result is missing 'output' attribute. run_result type: {type(run_result)}, value: {run_result}"
            )
            if plain_text_output:
                sys.stderr.write("Error: Unexpected response structure from LLM.\n")
            else:
                qx_console.print(
                    "[red]Error:[/red] Unexpected response structure from LLM."
                )
            return current_message_history
    else:
        if plain_text_output:
            sys.stdout.write("Info: No response generated or an error occurred.\n")
        else:
            qx_console.print(
                "[yellow]Info:[/yellow] No response generated or an error occurred."
            )
        return current_message_history


async def get_simple_input() -> str:
    """Simple input function that just reads from stdin."""
    import sys

    prompt = "QX⏵ "

    try:
        # Use input() instead of sys.stdin.readline() to avoid blocking issues
        return input(prompt).strip()
    except (EOFError, KeyboardInterrupt):
        return "exit"


async def _async_main(
    initial_prompt: Optional[str] = None,
    exit_after_response: bool = False,
    recover_session_path: Optional[Path] = None,
):
    """
    Asynchronous main function to handle the QX agent logic.
    """
    global temp_stream_handler

    try:
        _configure_logging()
    except Exception as e:
        print(f"Failed to configure logging: {e}")
        traceback.print_exc()
        return

    try:
        async with anyio.create_task_group() as tg:
            config_manager = ConfigManager(qx_console, parent_task_group=tg)
            config_manager.load_configurations()

            logger.debug("Using Textual interface.")

            syntax_theme_from_env = os.getenv("QX_SYNTAX_HIGHLIGHT_THEME")
            code_theme_to_use = (
                syntax_theme_from_env
                if syntax_theme_from_env
                else DEFAULT_SYNTAX_HIGHLIGHT_THEME
            )
            logger.debug(
                f"Using syntax highlighting theme for Markdown code blocks: {code_theme_to_use}"
            )

            # Initialize LLM Agent with MCP Manager
            llm_agent: Optional[QXLLMAgent] = await _initialize_agent_with_mcp(
                config_manager.mcp_manager
            )

            # Get QX_KEEP_SESSIONS from environment, default to 5 if not set or invalid
            try:
                keep_sessions = int(os.getenv("QX_KEEP_SESSIONS", "5"))
                if keep_sessions < 0:
                    logger.warning(
                        f"QX_KEEP_SESSIONS must be non-negative. Using default of 5 instead of {keep_sessions}."
                    )
                    keep_sessions = 5
            except ValueError:
                logger.warning(
                    "Invalid value for QX_KEEP_SESSIONS. Using default of 5."
                )
                keep_sessions = 5

            # Handle exit after response mode (non-interactive)
            if exit_after_response and initial_prompt:
                current_message_history = await _handle_llm_interaction(
                    llm_agent,
                    initial_prompt,
                    None,
                    code_theme_to_use,
                    plain_text_output=True,
                )
                if current_message_history:
                    save_session(current_message_history)
                    clean_old_sessions(keep_sessions)
                return  # Return instead of sys.exit() to avoid issues with async context

            current_message_history: Optional[List[ChatCompletionMessageParam]] = None

            # Handle session recovery
            if recover_session_path:
                qx_console.print(
                    f"[info]Attempting to recover session from: {recover_session_path}[/info]"
                )
                loaded_history = load_session_from_path(recover_session_path)
                if loaded_history:
                    current_message_history = loaded_history
                    qx_console.print("[info]Session recovered successfully![/info]")
                else:
                    qx_console.print(
                        "[red]Failed to recover session. Starting new session.[/red]"
                    )

            # Handle initial prompt
            if initial_prompt and not exit_after_response:
                qx_console.print(f"[bold]Initial Prompt:[/bold] {initial_prompt}")
                current_message_history = await _handle_llm_interaction(
                    llm_agent,
                    initial_prompt,
                    current_message_history,
                    code_theme_to_use,
                )

            # Run Textual app (only if not in exit-after-response mode)
            if not exit_after_response:
                app = QXApp()
                app.set_mcp_manager(config_manager.mcp_manager)
                app.set_llm_agent(llm_agent)
                app.set_version_info(
                    QX_VERSION, llm_agent.model_name
                )  # Pass version info

                # Remove the temporary stream handler before running Textual app
                if temp_stream_handler and temp_stream_handler in logger.handlers:
                    logger.removeHandler(temp_stream_handler)
                    temp_stream_handler = None  # Clear the global reference

                # Add TextualRichLogHandler to the logger
                textual_handler = TextualRichLogHandler(qx_console)
                textual_handler.setLevel(
                    logger.level
                )  # Set level to match logger's effective level
                logger.addHandler(textual_handler)
                qx_console.set_logger(logger)  # Set the logger in qx_console

                try:
                    # Enable console debugging if QX_DEBUG is set
                    debug_mode = os.environ.get("QX_DEBUG", "false").lower() == "true"
                    if debug_mode:
                        # Run with console redirected for debugging
                        await app.run_async(headless=False)
                    else:
                        await app.run_async()
                except KeyboardInterrupt:
                    logger.debug("QX terminated by user (Ctrl+C)")
                    qx_console.print("\nQX terminated by user.")
                except Exception as e:
                    logger.error(f"Error running Textual app: {e}", exc_info=True)
                    qx_console.print(f"[red]App Error:[/red] {e}")
                finally:
                    # Cleanup: disconnect all active MCP servers
                    try:
                        logger.debug("Disconnecting all MCP servers before exit.")
                        await config_manager.mcp_manager.disconnect_all()
                    except Exception as e:
                        logger.error(f"Error during MCP cleanup: {e}", exc_info=True)
                    
                    # Clean up LLM agent resources
                    try:
                        if llm_agent:
                            await llm_agent.cleanup()
                    except Exception as e:
                        logger.error(f"Error during LLM cleanup: {e}", exc_info=True)
                    
                    

    except Exception as e:
        logger.critical(f"Critical error in _async_main: {e}", exc_info=True)
        print(f"Critical error: {e}")
        traceback.print_exc()


async def handle_command(
    command_input: str,
    llm_agent: QXLLMAgent,
    config_manager: ConfigManager,
    current_message_history,
):
    """Handle slash commands."""
    parts = command_input.strip().split(maxsplit=1)
    command_name = parts[0].lower()
    command_args = parts[1].strip() if len(parts) > 1 else ""

    if command_name == "/model":
        _handle_model_command(llm_agent)
    elif command_name == "/reset":
        qx_console.clear()
        current_message_history = None
        reset_session()
        llm_agent = await _initialize_agent_with_mcp(config_manager.mcp_manager)
        qx_console.print(
            "[info]Session reset, system prompt reloaded, and terminal cleared.[/info]"
        )
    else:
        qx_console.print(f"[red]Unknown command: {command_name}[/red]")
        qx_console.print("Available commands: /model, /reset")


def main():
    _configure_logging()

    parser = argparse.ArgumentParser(
        description="QX - A terminal-based agentic coding assistant with simplified interface."
    )
    parser.add_argument(
        "-v",
        "--version",
        action="store_true",
        help="Show QX version, LLM model, and parameters, then exit.",
    )
    parser.add_argument(
        "-x",
        "--exit-after-response",
        action="store_true",
        help="Exit immediately after responding to an initial prompt.",
    )
    parser.add_argument(
        "-r",
        "--recover-session",
        type=str,
        help="Path to a JSON session file to recover and continue the conversation.",
    )
    parser.add_argument(
        "initial_prompt",
        nargs=argparse.REMAINDER,
        help="Initial prompt for QX. If provided, QX will process this once and then either exit (with -x) or enter interactive mode.",
    )
    args = parser.parse_args()

    if args.version:
        _display_version_info()

    initial_prompt_str = " ".join(args.initial_prompt).strip()

    # Handle mutually exclusive arguments
    if args.recover_session and initial_prompt_str:
        qx_console.print(
            "[red]Error:[/red] Cannot use --recover-session with an initial prompt. Please choose one."
        )
        sys.exit(1)

    if args.recover_session and args.exit_after_response:
        qx_console.print(
            "[red]Error:[/red] Cannot use --recover-session with --exit-after-response. Recovery implies interactive mode."
        )
        sys.exit(1)

    recover_path = Path(args.recover_session) if args.recover_session else None

    try:
        asyncio.run(
            _async_main(
                initial_prompt=initial_prompt_str if initial_prompt_str else None,
                exit_after_response=args.exit_after_response,
                recover_session_path=recover_path,
            )
        )

        # If exit_after_response is True, we should exit here
        if args.exit_after_response:
            sys.exit(0)

    except KeyboardInterrupt:
        qx_console.print("\nQX terminated by user.")
        sys.exit(0)
    except Exception as e:
        fallback_logger = logging.getLogger("qx.critical")
        fallback_logger.critical(f"Critical error running QX: {e}", exc_info=True)
        qx_console.print(f"[bold red]Critical error running QX:[/bold red] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
