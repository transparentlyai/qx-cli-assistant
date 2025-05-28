import argparse
import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Any, List, Optional

import anyio
from openai.types.chat import ChatCompletionMessageParam

from qx.cli.console import qx_console, show_spinner
from qx.cli.textual_app import QXApp
from qx.core.config_manager import ConfigManager
from qx.core.constants import DEFAULT_MODEL, DEFAULT_SYNTAX_HIGHLIGHT_THEME
from qx.core.llm import QXLLMAgent, initialize_llm_agent, query_llm
from qx.core.session_manager import save_session, clean_old_sessions, load_session_from_path, reset_session
from qx.core.mcp_manager import MCPManager

# QX Version
QX_VERSION = "0.3.3"

# Configure logging for the application
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

    from rich.panel import Panel
    qx_console.print(Panel(model_info_content, title="LLM Model Info", border_style="blue"))


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
    spinner_status = None

    # For streaming, we don't show spinner as content streams in real-time
    if not plain_text_output and not agent.enable_streaming:
        spinner_status = show_spinner("QX is thinking...")

    try:
        if spinner_status:
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
        pass  # No spinner cleanup needed in Textual

    if run_result:
        if hasattr(run_result, "output"):
            output_content = (
                str(run_result.output) if run_result.output is not None else ""
            )
            if plain_text_output:
                from textual.console import Console
                plain_console = Console(force_terminal=False, no_color=True, highlight=False)
                plain_console.print(output_content)
            else:
                # For streaming, content is already displayed during the stream
                if not agent.enable_streaming and output_content.strip():
                    from rich.markdown import Markdown
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
                qx_console.print("[red]Error:[/red] Unexpected response structure from LLM.")
            return current_message_history
    else:
        if plain_text_output:
            sys.stdout.write("Info: No response generated or an error occurred.\n")
        else:
            qx_console.print(
                "[yellow]Info:[/yellow] No response generated or an error occurred."
            )
        return current_message_history


class QXTextualApp(QXApp):
    """Extended QX app with LLM integration."""
    
    def __init__(self, llm_agent: QXLLMAgent, config_manager: ConfigManager, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.llm_agent = llm_agent
        self.config_manager = config_manager
        self.current_message_history: Optional[List[ChatCompletionMessageParam]] = None
        self.code_theme = DEFAULT_SYNTAX_HIGHLIGHT_THEME
        
    async def handle_user_input(self, input_text: str):
        """Handle user input and interact with LLM."""
        if input_text.lower() in ["exit", "quit"]:
            if self.current_message_history:
                save_session(self.current_message_history)
                clean_old_sessions(5)
            self.exit()
            return
            
        if not input_text.strip():
            return

        # Command handling logic
        if input_text.startswith("/"):
            await self.handle_command(input_text)
        else:
            # Regular LLM interaction
            self.current_message_history = await _handle_llm_interaction(
                self.llm_agent, input_text, self.current_message_history, self.code_theme
            )
            
            # Save session after each turn
            if self.current_message_history:
                save_session(self.current_message_history)
                clean_old_sessions(5)
    
    async def handle_command(self, command_input: str):
        """Handle slash commands."""
        parts = command_input.strip().split(maxsplit=1)
        command_name = parts[0].lower()
        command_args = parts[1].strip() if len(parts) > 1 else ""

        if command_name == "/model":
            _handle_model_command(self.llm_agent)
        elif command_name == "/reset":
            qx_console.clear()
            self.current_message_history = None
            reset_session()
            self.llm_agent = await _initialize_agent_with_mcp(self.config_manager.mcp_manager)
            qx_console.print("[info]Session reset, system prompt reloaded, and terminal cleared.[/info]")
        elif command_name == "/compress-context":
            if not self.current_message_history:
                qx_console.print("[warning]No conversation history to compress.[/warning]")
                return
            
            try:
                prompt_path = Path(__file__).parent / "prompts" / "context_compression_prompt.md"
                with open(prompt_path, 'r', encoding='utf-8') as f:
                    compression_prompt = f.read().strip()
            except Exception as e:
                qx_console.print(f"[red]Error reading compression prompt: {e}[/red]")
                return
            
            qx_console.print("[info]Compressing conversation context...[/info]")
            
            compressed_result = await _handle_llm_interaction(
                self.llm_agent, compression_prompt, self.current_message_history, self.code_theme
            )
            
            if compressed_result and len(compressed_result) > 0:
                compressed_context = ""
                for msg in reversed(compressed_result):
                    if hasattr(msg, 'role') and msg.role == "assistant":
                        compressed_context = msg.content if hasattr(msg, 'content') else ""
                        break
                
                if compressed_context:
                    prefix = "This session is being continued from a previous conversation that ran out of context. The conversation is summarized below:\n\n"
                    compressed_context = prefix + compressed_context

                    qx_console.clear()
                    self.llm_agent = await _initialize_agent_with_mcp(self.config_manager.mcp_manager)
                    
                    self.current_message_history = await _handle_llm_interaction(
                        self.llm_agent, compressed_context, None, self.code_theme
                    )
                    
                    qx_console.print("[info]Context compressed and session reset with compressed history.[/info]")
                else:
                    qx_console.print("[red]Failed to extract compressed context from LLM response.[/red]")
            else:
                qx_console.print("[red]Failed to compress context.[/red]")
        elif command_name.startswith("/save-session"):
            if not self.current_message_history:
                qx_console.print("[warning]No conversation history to save.[/warning]")
                return
            
            if not command_args:
                qx_console.print("[red]Usage: /save-session <filename>[/red]")
                return
            
            filename = command_args.strip()
            if not filename:
                qx_console.print("[red]Filename cannot be empty.[/red]")
                return
            
            if not filename.endswith('.json'):
                filename += '.json'
            
            from qx.core.paths import QX_SESSIONS_DIR
            QX_SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
            session_path = QX_SESSIONS_DIR / filename
            
            serializable_history = [
                msg.model_dump() if hasattr(msg, 'model_dump') else msg
                for msg in self.current_message_history
            ]
            
            try:
                import json
                with open(session_path, "w", encoding="utf-8") as f:
                    json.dump(serializable_history, f, indent=2)
                qx_console.print(f"[info]Session saved to {session_path}[/info]")
            except Exception as e:
                qx_console.print(f"[red]Failed to save session: {e}[/red]")
        elif command_name == "/mcp-connect":
            if not command_args:
                qx_console.print("[red]Usage: /mcp-connect <server_name>[/red]")
                return
            success = await self.config_manager.mcp_manager.connect_server(command_args)
            if success:
                self.llm_agent = await _initialize_agent_with_mcp(self.config_manager.mcp_manager)
                qx_console.print(f"[success]Successfully connected to MCP server '{command_args}' and reloaded LLM agent tools.[/success]")
            else:
                qx_console.print(f"[red]Failed to connect to MCP server '{command_args}'. Check logs for details.[/red]")
        elif command_name == "/mcp-disconnect":
            if not command_args:
                qx_console.print("[red]Usage: /mcp-disconnect <server_name>[/red]")
                return
            success = await self.config_manager.mcp_manager.disconnect_server(command_args)
            if success:
                self.llm_agent = await _initialize_agent_with_mcp(self.config_manager.mcp_manager)
                qx_console.print(f"[success]Successfully disconnected from MCP server '{command_args}' and reloaded LLM agent tools.[/success]")
            else:
                qx_console.print(f"[red]Failed to disconnect from MCP server '{command_args}'. Check logs for details.[/red]")
        elif command_name == "/mcp-tools":
            mcp_tools = self.config_manager.mcp_manager.get_active_tools()
            
            if not mcp_tools:
                qx_console.print("[info]No MCP tools are currently active. Connect to an MCP server first using /mcp-connect.[/info]")
                return
            
            tools_info = f"[bold]Active MCP Tools ({len(mcp_tools)}):[/bold]\n"
            
            for tool_func, tool_schema, tool_input_model in mcp_tools:
                if "function" in tool_schema:
                    function_def = tool_schema["function"]
                else:
                    function_def = tool_schema
                
                tool_name = function_def.get("name", tool_func.__name__)
                tool_description = function_def.get("description", "No description available")
                
                tools_info += f"  • [green]{tool_name}[/green]: {tool_description}\n"
            
            from rich.panel import Panel
            qx_console.print(Panel(tools_info.strip(), title="MCP Tools", border_style="blue"))
        else:
            qx_console.print(f"[red]Unknown command: {command_name}[/red]")
    
    async def on_user_input_submitted(self, message) -> None:
        """Handle user input submission."""
        await self.handle_user_input(message.input_text)


async def _async_main(
    initial_prompt: Optional[str] = None, 
    exit_after_response: bool = False, 
    recover_session_path: Optional[Path] = None
):
    """
    Asynchronous main function to handle the QX agent logic.
    """
    _configure_logging()
    
    async with anyio.create_task_group() as tg:
        config_manager = ConfigManager(qx_console, parent_task_group=tg)
        config_manager.load_configurations()

        logger.info(
            "CLI theming system has been removed. Using default styling."
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
            config_manager.mcp_manager
        )

        # Get QX_KEEP_SESSIONS from environment, default to 5 if not set or invalid
        try:
            keep_sessions = int(os.getenv("QX_KEEP_SESSIONS", "5"))
            if keep_sessions < 0:
                logger.warning(f"QX_KEEP_SESSIONS must be non-negative. Using default of 5 instead of {keep_sessions}.")
                keep_sessions = 5
        except ValueError:
            logger.warning("Invalid value for QX_KEEP_SESSIONS. Using default of 5.")
            keep_sessions = 5

        # Handle exit after response mode (non-interactive)
        if exit_after_response and initial_prompt:
            current_message_history = await _handle_llm_interaction(
                llm_agent, initial_prompt, None, code_theme_to_use, plain_text_output=True
            )
            if current_message_history:
                save_session(current_message_history)
                clean_old_sessions(keep_sessions)
            sys.exit(0)

        # Create and run Textual app
        app = QXTextualApp(llm_agent, config_manager)
        app.set_mcp_manager(config_manager.mcp_manager)
        app.code_theme = code_theme_to_use
        
        # Handle session recovery
        if recover_session_path:
            qx_console.print(f"[info]Attempting to recover session from: {recover_session_path}[/info]")
            loaded_history = load_session_from_path(recover_session_path)
            if loaded_history:
                app.current_message_history = loaded_history
                qx_console.print("[info]Session recovered successfully![/info]")
            else:
                qx_console.print("[red]Failed to recover session. Starting new session.[/red]")

        # Handle initial prompt
        if initial_prompt and not exit_after_response:
            qx_console.print(f"[bold]Initial Prompt:[/bold] {initial_prompt}")
            app.current_message_history = await _handle_llm_interaction(
                llm_agent, initial_prompt, app.current_message_history, code_theme_to_use
            )

        # Show version info
        if not exit_after_response:
            info_text = f"QX ver:{QX_VERSION} - {llm_agent.model_name}"
            qx_console.print(f"[dim]{info_text}[/dim]")

        try:
            # Run the Textual app
            await app.run_async()
        except KeyboardInterrupt:
            qx_console.print("\nQX terminated by user.")
        finally:
            # Cleanup: disconnect all active MCP servers
            active_servers = list(config_manager.mcp_manager._active_tasks.keys())
            for server_name in active_servers:
                logger.info(f"Disconnecting MCP server '{server_name}' before exit.")
                await config_manager.mcp_manager.disconnect_server(server_name)


def main():
    _configure_logging()

    parser = argparse.ArgumentParser(
        description="QX - A terminal-based agentic coding assistant with Textual UI."
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
        qx_console.print("[red]Error:[/red] Cannot use --recover-session with an initial prompt. Please choose one.")
        sys.exit(1)

    if args.recover_session and args.exit_after_response:
        qx_console.print("[red]Error:[/red] Cannot use --recover-session with --exit-after-response. Recovery implies interactive mode.")
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
        qx_console.print("\nQX terminated by user.")
        sys.exit(0)
    except Exception as e:
        fallback_logger = logging.getLogger("qx.critical")
        fallback_logger.critical(f"Critical error running QX: {e}", exc_info=True)
        qx_console.print(f"[bold red]Critical error running QX:[/bold red] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()