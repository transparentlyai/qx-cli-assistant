import argparse
import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Any, List, Optional

import anyio # Added import for anyio
from openai.types.chat import ChatCompletionMessageParam
from rich.console import Console # Import Console for plain text output
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text

from qx.cli.console import QXConsole, qx_console, show_spinner
from qx.cli.qprompt import get_user_input
from qx.core.config_manager import ConfigManager # Changed from load_runtime_configurations
from qx.core.constants import DEFAULT_MODEL, DEFAULT_SYNTAX_HIGHLIGHT_THEME
from qx.core.llm import QXLLMAgent, initialize_llm_agent, query_llm
from qx.core.session_manager import save_session, clean_old_sessions, load_session_from_path # Import session management functions
from qx.core.mcp_manager import MCPManager # New import

# --- QX Version ---
QX_VERSION = "0.3.3"
# --- End QX Version ---

# --- Configure logging for the application ---
logger = logging.getLogger("qx")


def _configure_logging():
    """
    Configures the application's logging based on QX_LOG_LEVEL environment variable.
    """
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


async def _initialize_agent_with_mcp(mcp_manager: MCPManager) -> QXLLMAgent:
    """
    Initializes and returns the QXLLMAgent, passing the MCPManager.
    Exits if QX_MODEL_NAME is not set or agent initialization fails.
    """
    model_name_from_env = os.environ.get("QX_MODEL_NAME", DEFAULT_MODEL)

    if not model_name_from_env:
        qx_console.print(
            "[error]Critical Error:[/] QX_MODEL_NAME environment variable not set. Please set it to an OpenRouter model string (e.g., 'google/gemini-2.5-flash-preview-05-20:thinking')."
        )
        sys.exit(1)

    logger.debug(f"Initializing LLM agent with parameters:")
    logger.debug(f"  Model Name: {model_name_from_env}")

    agent: Optional[QXLLMAgent] = initialize_llm_agent(
        model_name_str=model_name_from_env,
        console=qx_console,
        mcp_manager=mcp_manager, # Pass MCPManager
    )

    if agent is None:
        qx_console.print(
            "[error]Critical Error:[/] Failed to initialize LLM agent. Exiting."
        )
        sys.exit(1)
    return agent


def _handle_model_command(agent: QXLLMAgent):
    """
    Displays information about the current LLM model configuration.
    """
    model_info_content = f"[bold]Current LLM Model Configuration:[/bold]\n"
    model_info_content += f"  Model Name: [green]{agent.model_name}[/green]\n"
    # OpenRouter models don't have a direct "provider.base_url" attribute on the agent itself
    # The base_url is part of the internal client configuration.
    # For simplicity, we can just state it's OpenRouter.
    model_info_content += (
        f"  Provider: [green]OpenRouter (https://openrouter.ai/api/v1)[/green]\n"
    )

    # Access model settings directly from agent attributes
    temperature_val = agent.temperature
    max_tokens_val = agent.max_output_tokens
    reasoning_effort_val = agent.reasoning_effort

    model_info_content += f"  Temperature: [green]{temperature_val}[/green]\n"
    model_info_content += f"  Max Output Tokens: [green]{max_tokens_val}[/green]\n"
    model_info_content += f"  Reasoning Effort: [green]{reasoning_effort_val if reasoning_effort_val else 'None'}[/green]\n"

    qx_console.print(
        Panel(model_info_content, title="LLM Model Info", border_style="blue")
    )


def _display_version_info():
    """
    Displays QX version, LLM model, and its parameters, then exits.
    """
    _configure_logging()
    # ConfigManager is now a class, instantiate and load
    # For version info, we don't need a fully functional TaskGroup, so we pass None
    config_manager = ConfigManager(qx_console, parent_task_group=None)
    config_manager.load_configurations()

    qx_console.print(f"[bold]QX Version:[/bold] [green]{QX_VERSION}[/green]")

    try:
        # Need a dummy MCPManager for version info if not fully initialized
        # Or, better, refactor _initialize_agent to not require it for version display
        # For now, create a temporary one if _initialize_agent is called directly
        temp_mcp_manager = MCPManager(qx_console, parent_task_group=None)
        agent = asyncio.run(_initialize_agent_with_mcp(temp_mcp_manager)) # Call async function
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
    Handles the interaction with the LLM, including spinner display and response processing.
    Returns the updated message history.
    """
    run_result: Optional[Any] = None
    spinner_status = None

    if not plain_text_output:
        spinner_status = show_spinner("QX is thinking...")
        QXConsole.set_active_status(spinner_status)

    try:
        if spinner_status:
            with spinner_status:
                run_result = await query_llm(
                    agent,
                    user_input,
                    message_history=current_message_history,
                    console=qx_console,
                )
        else:
            run_result = await query_llm(
                agent,
                user_input,
                message_history=current_message_history,
                console=qx_console,
            )
    finally:
        if not plain_text_output:
            QXConsole.set_active_status(None)

    if run_result:
        if hasattr(run_result, "output"):
            output_content = (
                str(run_result.output) if run_result.output is not None else ""
            )
            if plain_text_output:
                # Create a new Console instance that forces no color/markup
                plain_console = Console(force_terminal=False, no_color=True, highlight=False)
                plain_console.print(output_content)
                # Do NOT print the extra newline from qx_console here, as it would add Rich formatting.
            else:
                markdown_output = Markdown(output_content, code_theme=code_theme_to_use)
                qx_console.print(markdown_output)
                qx_console.print("\n")
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
                qx_console.print("[error]Error:[/] Unexpected response structure from LLM.")
            return current_message_history
    else:
        if plain_text_output:
            sys.stdout.write("Info: No response generated or an error occurred.\n")
        else:
            qx_console.print(
                "[warning]Info:[/] No response generated or an error occurred."
            )
        return current_message_history


async def _async_main(
    initial_prompt: Optional[str] = None, exit_after_response: bool = False, recover_session_path: Optional[Path] = None
):
    """
    Asynchronous main function to handle the QX agent logic.
    """
    _configure_logging()
    
    async with anyio.create_task_group() as tg: # Create a task group for the entire application
        config_manager = ConfigManager(qx_console, parent_task_group=tg) # Pass the task group to ConfigManager
        config_manager.load_configurations() # Load configurations including MCP

        logger.info(
            "CLI theming system has been removed. Using default Rich console styling."
        )

        syntax_theme_from_env = os.getenv("QX_SYNTAX_HIGHLIGHT_THEME")
        code_theme_to_use = (
            syntax_theme_from_env
            if syntax_theme_from_env
            else DEFAULT_SYNTAX_HIGHLIGHT_THEME
        )
        logger.info(
            f"Using syntax highlighting theme for Markdown code blocks: {code_theme_to_use}"
        )

        # Initialize LLM Agent with MCP Manager
        llm_agent: Optional[QXLLMAgent] = await _initialize_agent_with_mcp(
            config_manager.mcp_manager # Pass the MCPManager instance from config_manager
        )

        if not exit_after_response:
            info_text = f"QX ver:{QX_VERSION} - {llm_agent.model_name}"
            qx_console.print(Text(info_text, style="dim"))

        current_message_history: Optional[List[ChatCompletionMessageParam]] = None

        # Get QX_KEEP_SESSIONS from environment, default to 5 if not set or invalid
        try:
            keep_sessions = int(os.getenv("QX_KEEP_SESSIONS", "5"))
            if keep_sessions < 0:
                logger.warning(f"QX_KEEP_SESSIONS must be non-negative. Using default of 5 instead of {keep_sessions}.")
                keep_sessions = 5
        except ValueError:
            logger.warning("Invalid value for QX_KEEP_SESSIONS. Using default of 5.")
            keep_sessions = 5

        if recover_session_path:
            qx_console.print(f"[info]Attempting to recover session from: {recover_session_path}[/info]")
            loaded_history = load_session_from_path(recover_session_path)
            if loaded_history:
                current_message_history = loaded_history
                qx_console.print("[info]Session recovered successfully![/info]")
            else:
                qx_console.print("[error]Failed to recover session. Starting new session.[/error]")

        if initial_prompt:
            if not exit_after_response:
                qx_console.print(f"[bold]Initial Prompt:[/bold] {initial_prompt}")
            current_message_history = await _handle_llm_interaction(
                llm_agent, initial_prompt, current_message_history, code_theme_to_use, plain_text_output=exit_after_response
            )
            if exit_after_response:
                if current_message_history:
                    save_session(current_message_history)
                    clean_old_sessions(keep_sessions)
                sys.exit(0)

        while True:
            try:
                user_input = await get_user_input(qx_console, config_manager.mcp_manager)

                if user_input == "":
                    continue

                if user_input.lower() in ["exit", "quit"]:
                    if current_message_history:
                        save_session(current_message_history)
                        clean_old_sessions(keep_sessions)
                    break
                if not user_input.strip():
                    continue

                # Command handling logic
                if user_input.startswith("/"):
                    parts = user_input.strip().split(maxsplit=1)
                    command_name = parts[0].lower()
                    command_args = parts[1].strip() if len(parts) > 1 else ""

                    if command_name == "/model":
                        _handle_model_command(llm_agent)
                    elif command_name == "/reset":
                        qx_console.clear()
                        current_message_history = None
                        llm_agent = await _initialize_agent_with_mcp(config_manager.mcp_manager) # Reload system prompt and agent
                        qx_console.print("[info]Session reset, system prompt reloaded, and terminal cleared.[/info]")
                    elif command_name == "/compress-context":
                        if not current_message_history:
                            qx_console.print("[warning]No conversation history to compress.[/warning]")
                            continue
                        
                        # Read the context compression prompt
                        try:
                            prompt_path = Path(__file__).parent / "prompts" / "context_compression_prompt.md"
                            with open(prompt_path, 'r', encoding='utf-8') as f:
                                compression_prompt = f.read().strip()
                        except Exception as e:
                            qx_console.print(f"[error]Error reading compression prompt: {e}[/error]")
                            continue
                        
                        qx_console.print("[info]Compressing conversation context...[/info]")
                        
                        # Send the compression prompt to the LLM
                        compressed_result = await _handle_llm_interaction(
                            llm_agent, compression_prompt, current_message_history, code_theme_to_use
                        )
                        
                        if compressed_result and len(compressed_result) > 0:
                            # Extract the compressed context (the last assistant message)
                            compressed_context = ""
                            for msg in reversed(compressed_result):
                                if hasattr(msg, 'role') and msg.role == "assistant":
                                    compressed_context = msg.content if hasattr(msg, 'content') else ""
                                    break
                            
                            if compressed_context:
                                # Reset the session (like /reset command)
                                qx_console.clear()
                                llm_agent = await _initialize_agent_with_mcp(config_manager.mcp_manager)
                                
                                # Start new session with compressed context
                                current_message_history = await _handle_llm_interaction(
                                    llm_agent, compressed_context, None, code_theme_to_use
                                )
                                
                                qx_console.print("[info]Context compressed and session reset with compressed history.[/info]")
                            else:
                                qx_console.print("[error]Failed to extract compressed context from LLM response.[/error]")
                        else:
                            qx_console.print("[error]Failed to compress context.[/error]")
                    elif command_name.startswith("/save-session"):
                        if not current_message_history:
                            qx_console.print("[warning]No conversation history to save.[/warning]")
                            continue
                        
                        # Parse the filename argument
                        if not command_args:
                            qx_console.print("[error]Usage: /save-session <filename>[/error]")
                            continue
                        
                        filename = command_args.strip()
                        if not filename:
                            qx_console.print("[error]Filename cannot be empty.[/error]")
                            continue
                        
                        # Ensure .json extension
                        if not filename.endswith('.json'):
                            filename += '.json'
                        
                        # Create sessions directory if it doesn't exist
                        from qx.core.paths import QX_SESSIONS_DIR
                        QX_SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
                        session_path = QX_SESSIONS_DIR / filename
                        
                        # Convert messages to serializable format
                        serializable_history = [
                            msg.model_dump() if hasattr(msg, 'model_dump') else msg
                            for msg in current_message_history
                        ]
                        
                        try:
                            import json
                            with open(session_path, "w", encoding="utf-8") as f:
                                json.dump(serializable_history, f, indent=2)
                            qx_console.print(f"[info]Session saved to {session_path}[/info]")
                        except Exception as e:
                            qx_console.print(f"[error]Failed to save session: {e}[/error]")
                    elif command_name == "/mcp-connect": # New MCP Connect Command
                        if not command_args:
                            qx_console.print("[error]Usage: /mcp-connect <server_name>[/error]")
                            continue
                        success = await config_manager.mcp_manager.connect_server(command_args)
                        if success:
                            # Re-initialize LLM agent to update tools
                            llm_agent = await _initialize_agent_with_mcp(config_manager.mcp_manager)
                            qx_console.print(f"[success]Successfully connected to MCP server '{command_args}' and reloaded LLM agent tools.[/success]")
                        else:
                            qx_console.print(f"[error]Failed to connect to MCP server '{command_args}'. Check logs for details.[/error]")
                    elif command_name == "/mcp-disconnect": # New MCP Disconnect Command
                        if not command_args:
                            qx_console.print("[error]Usage: /mcp-disconnect <server_name>[/error]")
                            continue
                        success = await config_manager.mcp_manager.disconnect_server(command_args)
                        if success:
                            # Re-initialize LLM agent to update tools
                            llm_agent = await _initialize_agent_with_mcp(config_manager.mcp_manager)
                            qx_console.print(f"[success]Successfully disconnected from MCP server '{command_args}' and reloaded LLM agent tools.[/success]")
                        else:
                            qx_console.print(f"[error]Failed to disconnect from MCP server '{command_args}'. Check logs for details.[/error]")
                    else:
                        qx_console.print(f"[error]Unknown command: {command_name}[/error]")
                    continue

                current_message_history = await _handle_llm_interaction(
                    llm_agent, user_input, current_message_history, code_theme_to_use
                )

            except KeyboardInterrupt:
                qx_console.print(
                    "\nOperation cancelled by Ctrl+C. Returning to prompt.", style="yellow"
                )
                # Save session on Ctrl+C as well
                if current_message_history:
                    save_session(current_message_history)
                    clean_old_sessions(keep_sessions)
                current_message_history = None
                continue
            except asyncio.CancelledError:
                qx_console.print(
                    "\nOperation cancelled (async). Returning to prompt.", style="yellow"
                )
                # Save session on async cancellation as well
                if current_message_history:
                    save_session(current_message_history)
                    clean_old_sessions(keep_sessions)
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
                # Save session on unexpected error as well
                if current_message_history:
                    save_session(current_message_history)
                    clean_old_sessions(keep_sessions)
                break


def main():
    _configure_logging()

    parser = argparse.ArgumentParser(
        description="QX - A terminal-based agentic coding assistant."
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
        qx_console.print("[error]Error:[/] Cannot use --recover-session with an initial prompt. Please choose one.")
        sys.exit(1)

    if args.recover_session and args.exit_after_response:
        qx_console.print("[error]Error:[/] Cannot use --recover-session with --exit-after-response. Recovery implies interactive mode.")
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
