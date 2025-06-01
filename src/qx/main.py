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

# No console imports needed anymore
from qx.core.config_manager import ConfigManager
from qx.core.constants import DEFAULT_MODEL, DEFAULT_SYNTAX_HIGHLIGHT_THEME
from qx.core.llm import QXLLMAgent, initialize_llm_agent, query_llm
from qx.core.mcp_manager import MCPManager
from qx.core.paths import QX_HISTORY_FILE
from qx.core.session_manager import (
    clean_old_sessions,
    load_latest_session,
    load_session_from_path,
    reset_session,
    save_session,
)

# QX Version
QX_VERSION = "0.3.42"

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
        from rich.console import Console

        Console().print(
            "[red]Critical Error:[/red] QX_MODEL_NAME environment variable not set. Please set it to an OpenRouter model string."
        )
        sys.exit(1)

    logger.debug(f"Initializing LLM agent with parameters:")
    logger.debug(f"  Model Name: {model_name_from_env}")

    # Check if streaming is enabled via environment variable
    enable_streaming = os.environ.get("QX_ENABLE_STREAMING", "true").lower() == "true"

    agent: Optional[QXLLMAgent] = initialize_llm_agent(
        model_name_str=model_name_from_env,
        console=None,
        mcp_manager=mcp_manager,
        enable_streaming=enable_streaming,
    )

    if agent is None:
        from rich.console import Console

        Console().print(
            "[red]Critical Error:[/red] Failed to initialize LLM agent. Exiting."
        )
        sys.exit(1)
    return agent


def _handle_model_command(agent: QXLLMAgent):
    """
    Displays information about the current LLM model configuration.
    """
    from rich.console import Console

    rich_console = Console()

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

    rich_console.print(model_info_content)


def _display_version_info():
    """
    Displays QX version, LLM model, and its parameters, then exits.
    """
    _configure_logging()
    config_manager = ConfigManager(None, parent_task_group=None)
    config_manager.load_configurations()

    from rich.console import Console

    Console().print(f"[bold]QX Version:[/bold] [green]{QX_VERSION}[/green]")

    try:
        temp_mcp_manager = MCPManager(None, parent_task_group=None)
        agent = asyncio.run(_initialize_agent_with_mcp(temp_mcp_manager))
        _handle_model_command(agent)
    except SystemExit:
        Console().print(
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

    # Spinner is now handled within the LLM agent itself

    try:
        run_result = await query_llm(
            agent,
            user_input,
            message_history=current_message_history,
            console=None,  # No console needed for inline mode
        )
    except Exception as e:
        logger.error(f"Error during LLM interaction: {e}", exc_info=True)
        from rich.console import Console

        Console().print(f"[red]Error:[/red] {e}")
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
                    from rich.console import Console
                    from rich.markdown import Markdown

                    rich_console = Console()
                    rich_console.print()
                    rich_console.print(Markdown(output_content, code_theme="rrt"))
                    rich_console.print()
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
                from rich.console import Console

                Console().print(
                    "[red]Error:[/red] Unexpected response structure from LLM."
                )
            return current_message_history
    else:
        if plain_text_output:
            sys.stdout.write("Info: No response generated or an error occurred.\n")
        else:
            from rich.console import Console

            Console().print(
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
            config_manager = ConfigManager(None, parent_task_group=tg)
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
                if recover_session_path == "LATEST":
                    from rich.console import Console

                    Console().print("Attempting to recover latest session...")
                    loaded_history = load_latest_session()
                    if loaded_history:
                        current_message_history = loaded_history
                        Console().print("Latest session recovered successfully!")
                    else:
                        Console().print(
                            "[red]No previous sessions found. Starting new session.[/red]"
                        )
                else:
                    Console().print(
                        f"[info]Attempting to recover session from: {recover_session_path}[/info]"
                    )
                    loaded_history = load_session_from_path(Path(recover_session_path))
                    if loaded_history:
                        current_message_history = loaded_history
                        Console().print("[info]Session recovered successfully![/info]")
                    else:
                        Console().print(
                            "[red]Failed to recover session. Starting new session.[/red]"
                        )

            # Handle initial prompt
            if initial_prompt and not exit_after_response:
                from rich.console import Console

                Console().print(f"[bold]Initial Prompt:[/bold] {initial_prompt}")
                current_message_history = await _handle_llm_interaction(
                    llm_agent,
                    initial_prompt,
                    current_message_history,
                    code_theme_to_use,
                )

            # Run inline interactive mode (only if not in exit-after-response mode)
            if not exit_after_response:
                # Remove the temporary stream handler for inline mode
                if temp_stream_handler and temp_stream_handler in logger.handlers:
                    logger.removeHandler(temp_stream_handler)
                    temp_stream_handler = None

                # Print version info
                from rich.console import Console

                rich_console = Console()
                rich_console.print(
                    f"[dim]QX ver:{QX_VERSION} - {llm_agent.model_name}[/dim]"
                )

                try:
                    # Run inline interactive loop
                    await _run_inline_mode(
                        llm_agent, current_message_history, keep_sessions
                    )
                except KeyboardInterrupt:
                    logger.debug("QX terminated by user (Ctrl+C)")
                    rich_console.print("\nQX terminated by user.")
                except Exception as e:
                    logger.error(f"Error running inline mode: {e}", exc_info=True)
                    rich_console.print(f"[red]App Error:[/red] {e}")
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


class QXHistory:
    """Custom history class that reads/writes QX's specific history file format."""

    def __init__(self, history_file_path: Path):
        self.history_file_path = history_file_path
        self._entries = []
        self.load_history()

    def load_history(self):
        """Load history from the QX format file."""
        if not self.history_file_path.exists():
            return

        history_entries = []
        current_command_lines = []

        try:
            with open(self.history_file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            for line in lines:
                stripped_line = line.strip()
                if stripped_line.startswith("# "):  # Timestamp line
                    # If we were accumulating a command, save it before starting a new one
                    if current_command_lines:
                        history_entries.append("\n".join(current_command_lines))
                        current_command_lines = []
                elif stripped_line.startswith("+"):
                    current_command_lines.append(
                        stripped_line[1:]
                    )  # Remove '+' and add
                elif (
                    not stripped_line and current_command_lines
                ):  # Blank line signifies end of entry
                    history_entries.append("\n".join(current_command_lines))
                    current_command_lines = []

            # Add any remaining command after loop (if file doesn't end with blank line)
            if current_command_lines:
                history_entries.append("\n".join(current_command_lines))

            # Reverse the order so newest entries come first (for arrow up navigation)
            self._entries = list(reversed(history_entries))

        except Exception as e:
            print(f"Error loading history from {self.history_file_path}: {e}")

    def append_string(self, command: str):
        """Add a new command to history (prompt_toolkit interface)."""
        command = command.strip()
        if command and (not self._entries or self._entries[-1] != command):
            self._entries.append(command)
            self.save_to_file(command)

    def store_string(self, command: str):
        """Store a string in the history (alternative prompt_toolkit interface)."""
        self.append_string(command)

    def save_to_file(self, command: str):
        """Save a command to the history file in QX format."""
        try:
            self.history_file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.history_file_path, "a", encoding="utf-8") as f:
                from datetime import datetime

                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
                f.write(f"\n# {timestamp}\n")  # Start with a newline for separation

                command_lines = command.split("\n")
                if len(command_lines) == 1 and not command_lines[0]:  # Empty command
                    f.write("+\n")
                else:  # Command has newlines or is non-empty single line
                    for line in command_lines:
                        f.write(f"+{line}\n")
        except Exception as e:
            print(f"Error saving history to {self.history_file_path}: {e}")

    # prompt_toolkit History interface methods
    def get_strings(self):
        """Return all history strings (prompt_toolkit interface)."""
        return self._entries

    async def load(self):
        """Async load method (prompt_toolkit interface)."""
        for entry in self._entries:
            yield entry

    def __iter__(self):
        """Iterator for prompt_toolkit compatibility."""
        return iter(self._entries)

    def __getitem__(self, index):
        """Index access for prompt_toolkit compatibility."""
        return self._entries[index]

    def __len__(self):
        """Length for prompt_toolkit compatibility."""
        return len(self._entries)


class QXCompleter:
    """Custom completer that handles both commands and path completion."""

    def __init__(self):
        self.commands = ["/model", "/reset", "/approve-all", "/help"]

    def get_completions(self, document, complete_event):
        import subprocess
        from pathlib import Path

        from prompt_toolkit.completion import Completion

        # Get the current text and cursor position
        text = document.text
        cursor_position = document.cursor_position

        # Find the start of the current word
        current_word_start = cursor_position
        while current_word_start > 0 and not text[current_word_start - 1].isspace():
            current_word_start -= 1

        current_word = text[current_word_start:cursor_position]

        # Command completion for slash commands
        if current_word.startswith("/"):
            for command in self.commands:
                if command.startswith(current_word):
                    yield Completion(
                        command,
                        start_position=-len(current_word),
                        display=f"{command}  [cmd]",
                    )
            return

        # Path completion using bash compgen (like ExtendedInput)
        if current_word:
            try:
                cmd = ["bash", "-c", f"compgen -f -- '{current_word}'"]
                result = subprocess.run(
                    cmd, capture_output=True, text=True, timeout=1, check=False
                )

                if result.returncode == 0:
                    candidates = result.stdout.strip().splitlines()
                    for candidate in candidates:
                        try:
                            # Check if it's a directory
                            is_dir = Path(candidate).is_dir()
                            display_suffix = "/" if is_dir else ""
                            completion_text = candidate + (
                                "/" if is_dir and not candidate.endswith("/") else ""
                            )

                            yield Completion(
                                completion_text,
                                start_position=-len(current_word),
                                display=f"{candidate}{display_suffix}  [{'dir' if is_dir else 'file'}]",
                            )
                        except OSError:
                            # Handle permission errors or other OS errors
                            yield Completion(
                                candidate,
                                start_position=-len(current_word),
                                display=f"{candidate}  [file]",
                            )
            except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
                # Fall back to no completions on error
                pass

    async def get_completions_async(self, document, complete_event):
        """Async version for prompt_toolkit compatibility."""
        for completion in self.get_completions(document, complete_event):
            yield completion


async def _run_inline_mode(
    llm_agent: QXLLMAgent,
    current_message_history: Optional[List[ChatCompletionMessageParam]],
    keep_sessions: int,
):
    """Run the interactive inline mode with prompt_toolkit input."""
    from prompt_toolkit import PromptSession
    from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
    from prompt_toolkit.filters import Condition
    from prompt_toolkit.formatted_text import HTML
    from prompt_toolkit.key_binding import KeyBindings
    from prompt_toolkit.styles import Style
    from prompt_toolkit.validation import ValidationError, Validator
    from rich.console import Console

    rich_console = Console()

    # Create custom history that handles QX format
    qx_history = QXHistory(QX_HISTORY_FILE)

    # Create custom completer that handles both commands and paths
    qx_completer = QXCompleter()

    # State tracking for multiline mode and pending text
    is_multiline_mode = [False]  # Use list for mutable reference in closures
    pending_text = [""]  # Text to restore when toggling modes

    # Create validator to prevent empty submissions in single-line mode
    class SingleLineNonEmptyValidator(Validator):
        """Validator that prevents empty input submission only in single-line mode."""

        def validate(self, document):
            # Only validate (prevent empty) in single-line mode
            if not is_multiline_mode[0]:  # Single-line mode
                text = document.text.strip()
                if not text:
                    # Prevent submission by raising validation error
                    # Using empty message to avoid showing error text
                    raise ValidationError(message="")
            # In multiline mode, allow empty submissions (for mode switching)

    # Create custom style for input text and bottom toolbar
    input_style = Style.from_dict(
        {
            # Style for the text as user types
            "": "fg:#ff005f bg:#050505",
            # Style for selected text
            "selected": "fg:#ff005f bg:#050505 reverse",
            # Style for the bottom toolbar
            "bottom-toolbar": "bg:#222222 fg:#888888",
            "bottom-toolbar.text": "bg:#222222 fg:#cccccc",
            "bottom-toolbar.key": "bg:#222222 fg:#ff5f00 bold",
        }
    )

    # Create bottom toolbar function
    def get_bottom_toolbar():
        """Return formatted text for the bottom toolbar."""
        from prompt_toolkit.formatted_text import HTML

        # Get current mode
        mode = "MULTILINE" if is_multiline_mode[0] else "SINGLE"

        # Build toolbar content
        toolbar_content = [
            ("class:bottom-toolbar.key", " Ctrl+R "),
            ("class:bottom-toolbar.text", "fzf search  "),
            ("class:bottom-toolbar.key", " Alt+Enter "),
            ("class:bottom-toolbar.text", f"toggle mode  "),
            ("class:bottom-toolbar.key", " Tab "),
            ("class:bottom-toolbar.text", "complete  "),
            ("class:bottom-toolbar.text", f"Mode: {mode}  "),
            (
                "class:bottom-toolbar.text",
                f"History: {len(qx_history._entries)} entries",
            ),
        ]

        return toolbar_content

    # Create key bindings for enhanced functionality
    bindings = KeyBindings()

    @bindings.add("c-c")
    def _(event):
        """Handle Ctrl+C"""
        event.app.exit(exception=KeyboardInterrupt, style="class:aborting")

    @bindings.add("c-d")
    def _(event):
        """Handle Ctrl+D"""
        event.app.exit(exception=EOFError, style="class:exiting")

    @bindings.add("c-r")
    def _(event):
        """Handle Ctrl+R for fzf history search"""
        try:
            import subprocess

            from qx.core.history_utils import parse_history_for_fzf
            from qx.core.paths import QX_HISTORY_FILE

            # Get history entries for fzf
            history_entries = parse_history_for_fzf(QX_HISTORY_FILE)
            if not history_entries:
                return

            # Prepare fzf input (display strings)
            fzf_input = "\n".join([display for display, _ in reversed(history_entries)])

            # Run fzf for selection with terminal restoration
            fzf_process = subprocess.run(
                ["fzf", "--ansi", "--reverse", "--height", "40%", "--no-clear"],
                input=fzf_input,
                capture_output=True,
                text=True,
            )

            # Always force redraw after fzf, regardless of selection
            event.app.invalidate()
            event.app.renderer.reset()

            if fzf_process.returncode == 0 and fzf_process.stdout.strip():
                selected_display = fzf_process.stdout.strip()

                # Find the original command for the selected display
                for display, original in history_entries:
                    if display == selected_display:
                        # Set the selected command as current buffer text
                        event.current_buffer.text = original
                        event.current_buffer.cursor_position = len(original)
                        break
        except Exception as e:
            # Always try to restore terminal state on any error
            try:
                event.app.invalidate()
                event.app.renderer.reset()
            except:
                pass

    @bindings.add("escape", "enter")  # Alt+Enter
    def _(event):
        """Handle Alt+Enter for multiline toggle/submit"""
        buffer = event.current_buffer

        if is_multiline_mode[0]:
            # Submit if in multiline mode
            buffer.validate_and_handle()
        else:
            # Toggle to multiline mode - we need to restart the prompt
            is_multiline_mode[0] = True
            # Store the current text
            current_text = buffer.text
            # Add newline if there's existing text
            if current_text.strip():
                current_text += "\n"
            # Store text for restoration
            pending_text[0] = current_text

            # Exit current prompt and restart with multiline mode
            event.app.exit(result="__TOGGLE_MULTILINE__")

    # Create prompt session with enhanced features
    session = PromptSession(
        history=qx_history,
        auto_suggest=AutoSuggestFromHistory(),
        enable_history_search=False,  # Disable built-in search, we use fzf
        completer=qx_completer,
        complete_style="multi-column",
        key_bindings=bindings,
        mouse_support=True,
        wrap_lines=True,
        multiline=Condition(lambda: is_multiline_mode[0]),
        validator=SingleLineNonEmptyValidator(),
        validate_while_typing=False,  # Only validate on submit attempt
        style=input_style,  # Apply custom input text styling
        bottom_toolbar=get_bottom_toolbar,  # Add status footer
    )

    while True:
        try:
            # Start with single-line mode for each new input
            if not is_multiline_mode[0]:
                is_multiline_mode[0] = False

            # Get the appropriate prompt based on current mode
            current_prompt = (
                HTML('<style fg="#0087ff">MULTILINE⏵</style> ')
                if is_multiline_mode[0]
                else HTML('<style fg="#ff5f00">QX⏵</style> ')
            )

            # Show prompt and get user input with prompt_toolkit
            default_text = pending_text[0] if pending_text[0] else ""
            result = await session.prompt_async(
                current_prompt,
                wrap_lines=True,
                default=default_text,  # Restore text after mode toggle
            )

            # Clear any pending text after successful prompt
            if result != "__TOGGLE_MULTILINE__":
                pending_text[0] = ""

            # Check if this was a mode toggle
            if result == "__TOGGLE_MULTILINE__":
                # Clear the previous prompt line before showing multiline prompt
                from rich.console import Console

                console = Console()
                try:
                    # Move cursor up and clear the line using Rich console
                    print("\033[1A\r\033[K", end="", flush=True)  # More direct approach
                except Exception:
                    pass
                # Continue loop to show multiline prompt with stored text
                continue

            user_input = result.strip()

            if not user_input:
                # Handle empty input differently based on current mode
                was_multiline = is_multiline_mode[0]
                if was_multiline:
                    # Multiline mode: clear prompt and switch to single line mode
                    try:
                        # Move cursor up and clear the multiline prompt line
                        print("\033[1A\r\033[K", end="", flush=True)
                    except Exception:
                        pass
                    # Reset multiline mode and show new single line prompt
                    is_multiline_mode[0] = False
                # Continue to next prompt iteration (both modes need this)
                continue

            if user_input.lower() in ["exit", "quit"]:
                break

            # Clear multiline prompt if transitioning from multiline to normal mode
            was_multiline = is_multiline_mode[0]
            if was_multiline:
                try:
                    # Move cursor up and clear the multiline prompt line
                    print("\033[1A\r\033[K", end="", flush=True)
                except Exception:
                    pass

            # Add to history (both in-memory and to file)
            qx_history.append_string(user_input)

            # Reset multiline mode after successful submission
            is_multiline_mode[0] = False

            # Handle commands
            if user_input.startswith("/"):
                await _handle_inline_command(user_input, llm_agent)
                continue

            # Handle LLM query
            current_message_history = await _handle_llm_interaction(
                llm_agent,
                user_input,
                current_message_history,
                "rrt",  # code theme
                plain_text_output=False,
            )

            # Save session
            if current_message_history:
                save_session(current_message_history)
                clean_old_sessions(keep_sessions)

        except KeyboardInterrupt:
            rich_console.print("\nQX terminated by user.")
            break
        except EOFError:
            break
        except Exception as e:
            logger.error(f"Error in inline mode: {e}", exc_info=True)
            rich_console.print(f"[red]Error:[/red] {e}")


async def _handle_inline_command(command_input: str, llm_agent: QXLLMAgent):
    """Handle slash commands in inline mode."""
    from rich.console import Console

    rich_console = Console()

    parts = command_input.strip().split(maxsplit=1)
    command_name = parts[0].lower()

    if command_name == "/model":
        _handle_model_command(llm_agent)
    elif command_name == "/reset":
        # Just reset message history in inline mode
        reset_session()
        rich_console.print("[info]Session reset, system prompt reloaded.[/info]")
    elif command_name == "/approve-all":
        import qx.core.user_prompts

        async with qx.core.user_prompts._approve_all_lock:
            qx.core.user_prompts._approve_all_active = True
        rich_console.print(
            "[orange]✓ 'Approve All' mode activated for this session.[/orange]"
        )
    elif command_name == "/help":
        rich_console.print("[bold]Available Commands:[/bold]")
        rich_console.print(
            "  [green]/model[/green]      - Show current LLM model configuration"
        )
        rich_console.print(
            "  [green]/reset[/green]      - Reset session and clear message history"
        )
        rich_console.print(
            "  [green]/approve-all[/green] - Activate 'approve all' mode for tool confirmations"
        )
        rich_console.print("  [green]/help[/green]       - Show this help message")
        rich_console.print("\n[bold]Input Modes:[/bold]")
        rich_console.print(
            "  • [yellow]Single-line mode[/yellow] (default): [#ff5f00]QX⏵[/#ff5f00] prompt"
        )
        rich_console.print("    - [cyan]Enter[/cyan]: Submit input")
        rich_console.print("    - [cyan]Alt+Enter[/cyan]: Switch to multiline mode")
        rich_console.print(
            "  • [yellow]Multiline mode[/yellow]: [#0087ff]MULTILINE⏵[/#0087ff] prompt"
        )
        rich_console.print("    - [cyan]Enter[/cyan]: Add newline (continue editing)")
        rich_console.print(
            "    - [cyan]Alt+Enter[/cyan]: Submit input and return to single-line"
        )
        rich_console.print("\n[bold]Features:[/bold]")
        rich_console.print("  • [cyan]Tab completion[/cyan] for commands and paths")
        rich_console.print(
            "  • [cyan]Fuzzy history search[/cyan] with Ctrl+R (using fzf)"
        )
        rich_console.print("  • [cyan]Auto-suggestions[/cyan] from history")
        rich_console.print("  • [cyan]Ctrl+C or Ctrl+D[/cyan] to exit")
    else:
        rich_console.print(f"[red]Unknown command: {command_name}[/red]")
        rich_console.print("Available commands: /model, /reset, /approve-all, /help")


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
        # No console to clear in inline mode
        current_message_history = None
        reset_session()
        llm_agent = await _initialize_agent_with_mcp(config_manager.mcp_manager)
        from rich.console import Console

        Console().print("[info]Session reset, system prompt reloaded.[/info]")
    else:
        from rich.console import Console

        Console().print(f"[red]Unknown command: {command_name}[/red]")
        Console().print("Available commands: /model, /reset")


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
        nargs="?",
        const="LATEST",
        help="Path to a JSON session file to recover and continue the conversation. If no path is provided, recovers the latest session.",
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
        from rich.console import Console

        Console().print(
            "[red]Error:[/red] Cannot use --recover-session with an initial prompt. Please choose one."
        )
        sys.exit(1)

    if args.recover_session and args.exit_after_response:
        Console().print(
            "[red]Error:[/red] Cannot use --recover-session with --exit-after-response. Recovery implies interactive mode."
        )
        sys.exit(1)

    recover_path = (
        args.recover_session
        if args.recover_session == "LATEST"
        else (Path(args.recover_session) if args.recover_session else None)
    )

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
        from rich.console import Console

        Console().print("\nQX terminated by user.")
        sys.exit(0)
    except Exception as e:
        fallback_logger = logging.getLogger("qx.critical")
        fallback_logger.critical(f"Critical error running QX: {e}", exc_info=True)
        Console().print(f"[bold red]Critical error running QX:[/bold red] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
