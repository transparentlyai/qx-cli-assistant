import asyncio
from pathlib import Path
from typing import Any, Optional

from textual import events
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.reactive import reactive
from textual.widgets import Footer, Input, RichLog, Static

from qx.cli.commands import CommandCompleter
from qx.cli.console import qx_console
from qx.cli.qprompt import handle_history_search
from qx.core.llm import query_llm
from qx.core.paths import QX_HISTORY_FILE
from qx.core.session_manager import clean_old_sessions, save_session


class StatusFooter(Static):
    """Custom footer widget that displays status messages."""
    
    def __init__(self, *args, **kwargs):
        super().__init__("Ready", *args, **kwargs)
        self.add_class("footer")
        self.spinner_chars = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self.spinner_index = 0
        self.spinner_timer = None
        self.base_message = ""
    
    def update_status(self, message: str):
        """Update the status message."""
        self.base_message = message
        self.update(message)
    
    def start_spinner(self, message: str = "Thinking..."):
        """Start spinner animation with message."""
        self.base_message = message
        self.spinner_index = 0
        self.update_spinner()
        self.spinner_timer = self.set_interval(0.1, self.update_spinner)
    
    def stop_spinner(self):
        """Stop spinner animation."""
        if self.spinner_timer:
            self.spinner_timer.stop()
            self.spinner_timer = None
    
    def update_spinner(self):
        """Update spinner character."""
        spinner_char = self.spinner_chars[self.spinner_index]
        self.update(f"{spinner_char} {self.base_message}")
        self.spinner_index = (self.spinner_index + 1) % len(self.spinner_chars)


class QXInput(Input):
    """Custom input widget with command completion and history support."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.command_completer: Optional[CommandCompleter] = None
        self.completions: list[str] = []
        self.completion_index = -1

    def set_command_completer(self, completer: CommandCompleter):
        """Set the command completer."""
        self.command_completer = completer

    async def key_tab(self) -> None:
        """Handle tab completion."""
        if self.command_completer:
            current_text = str(self.value)
            completions = self.command_completer.get_completions(current_text)

            if completions:
                if len(completions) == 1:
                    # Single completion - use it
                    self.value = completions[0]
                    self.cursor_position = len(self.value)
                else:
                    # Multiple completions - cycle through them
                    if self.completions != completions:
                        self.completions = completions
                        self.completion_index = 0
                    else:
                        self.completion_index = (self.completion_index + 1) % len(
                            completions
                        )

                    self.value = self.completions[self.completion_index]
                    self.cursor_position = len(self.value)

    async def key_ctrl_r(self) -> None:
        """Handle Ctrl+R for history search."""
        selected_command = handle_history_search(qx_console, QX_HISTORY_FILE)
        if selected_command:
            self.value = selected_command
            self.cursor_position = len(self.value)


class UserInputSubmitted(Message):
    """Message sent when user submits input."""

    def __init__(self, input_text: str):
        self.input_text = input_text
        super().__init__()


class QXApp(App):
    """Main QX Textual application."""

    CSS_PATH = Path(__file__).parent.parent / "css" / "main.css"

    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit"),
        Binding("ctrl+d", "quit", "Quit"),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.prompt_handler = None
        self.output_log: Optional[RichLog] = None
        self.user_input: Optional[QXInput] = None
        self.prompt_label: Optional[Static] = None
        self.status_footer: Optional[StatusFooter] = None
        self.mcp_manager = None
        self._input_future: Optional[asyncio.Future] = None
        self.llm_agent = None
        self.current_message_history = None
        self.keep_sessions = 5

    def set_mcp_manager(self, mcp_manager):
        """Set the MCP manager for command completion."""
        self.mcp_manager = mcp_manager

    def set_llm_agent(self, llm_agent):
        """Set the LLM agent for processing user input."""
        self.llm_agent = llm_agent

    def compose(self) -> ComposeResult:
        """Create the UI layout."""
        with Vertical(id="main-container"):
            yield RichLog(id="output-log", markup=True)
            with Horizontal(id="input-container"):
                yield Static("QX⏵ ", id="prompt-label")
                yield QXInput(placeholder="Enter your message...", id="user-input")
            yield StatusFooter(id="status-footer")

    def on_mount(self) -> None:
        """Set up the app after mounting."""
        self.output_log = self.query_one("#output-log", RichLog)
        self.user_input = self.query_one("#user-input", QXInput)
        self.prompt_label = self.query_one("#prompt-label", Static)
        self.status_footer = self.query_one("#status-footer", StatusFooter)

        # Connect console to widgets
        qx_console.set_widgets(self.output_log, self.user_input)
        qx_console._app = self

        # Set up command completion
        if self.mcp_manager:
            command_completer = CommandCompleter(mcp_manager=self.mcp_manager)
            self.user_input.set_command_completer(command_completer)

        # Focus on input
        self.user_input.focus()

        # Display welcome message
        self.output_log.write("Use Ctrl+C or 'exit' to quit.")

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle input submission."""
        try:
            if event.input.id == "user-input":
                input_text = str(event.value).strip()

                # Skip empty input - don't clear or process anything
                if not input_text.strip():
                    return

                # Clear the input
                self.user_input.value = ""

                # Display the input in the output
                self.output_log.write(f"[bold]QX⏵[/bold] [pink]{input_text}[/pink]")

                # Handle exit commands
                if input_text.lower() in ["exit", "quit"]:
                    if self.current_message_history:
                        save_session(self.current_message_history)
                        clean_old_sessions(self.keep_sessions)
                    self.exit()
                    return

                # Handle commands starting with /
                if input_text.startswith("/"):
                    await self.handle_command(input_text)
                    return

                # Process LLM interaction
                if self.llm_agent:
                    try:
                        # Start spinner animation
                        if self.status_footer:
                            self.status_footer.start_spinner("Thinking...")
                        
                        run_result = await query_llm(
                            self.llm_agent,
                            input_text,
                            message_history=self.current_message_history,
                            console=qx_console,
                        )

                        if run_result and hasattr(run_result, "output"):
                            output_content = (
                                str(run_result.output)
                                if run_result.output is not None
                                else ""
                            )
                            # Only render final output if streaming is disabled to avoid duplication
                            if output_content.strip() and not self.llm_agent.enable_streaming:
                                # Render as Markdown
                                from rich.markdown import Markdown
                                markdown = Markdown(output_content, code_theme="monokai")
                                self.output_log.write(markdown)
                                self.output_log.write("")
                            elif self.llm_agent.enable_streaming:
                                # For streaming, just add a newline for spacing
                                self.output_log.write("")

                            if hasattr(run_result, "all_messages"):
                                self.current_message_history = run_result.all_messages()

                            # Save session after each turn
                            if self.current_message_history:
                                save_session(self.current_message_history)
                                clean_old_sessions(self.keep_sessions)
                        
                        # Stop spinner and reset status to ready
                        if self.status_footer:
                            self.status_footer.stop_spinner()
                            self.status_footer.update_status("Ready")

                    except Exception as e:
                        # Log full traceback for debugging
                        import traceback
                        logger.error(f"Error in LLM interaction: {e}", exc_info=True)
                        
                        # Display error with traceback in output log
                        error_details = traceback.format_exc()
                        self.output_log.write(f"[red]Error:[/red] {e}")
                        self.output_log.write(f"[dim]{error_details}[/dim]")
                        
                        # Stop spinner and reset status on error too
                        if self.status_footer:
                            self.status_footer.stop_spinner()
                            self.status_footer.update_status("Ready")

                # Send message to parent components
                self.post_message(UserInputSubmitted(input_text))
                
        except Exception as e:
            # Catch any exceptions in the input handler itself
            import traceback
            logger.critical(f"Critical error in input handler: {e}", exc_info=True)
            if self.output_log:
                error_details = traceback.format_exc()
                self.output_log.write(f"[red]Critical Error in Input Handler:[/red] {e}")
                self.output_log.write(f"[dim]{error_details}[/dim]")
            if self.status_footer:
                self.status_footer.stop_spinner()
                self.status_footer.update_status("Error")

    async def handle_command(self, command_input: str):
        """Handle slash commands."""
        parts = command_input.strip().split(maxsplit=1)
        command_name = parts[0].lower()
        command_args = parts[1].strip() if len(parts) > 1 else ""

        if command_name == "/model" and self.llm_agent:
            model_info_content = f"[bold]Current LLM Model Configuration:[/bold]\n"
            model_info_content += (
                f"  Model Name: [green]{self.llm_agent.model_name}[/green]\n"
            )
            model_info_content += f"  Provider: [green]OpenRouter (https://openrouter.ai/api/v1)[/green]\n"
            model_info_content += (
                f"  Temperature: [green]{self.llm_agent.temperature}[/green]\n"
            )
            model_info_content += f"  Max Output Tokens: [green]{self.llm_agent.max_output_tokens}[/green]\n"
            reasoning_effort = (
                self.llm_agent.reasoning_effort
                if self.llm_agent.reasoning_effort
                else "None"
            )
            model_info_content += (
                f"  Reasoning Effort: [green]{reasoning_effort}[/green]\n"
            )
            self.output_log.write(model_info_content)
        elif command_name == "/reset":
            if self.output_log:
                self.output_log.clear()
            self.current_message_history = None
            # Reset session
            from qx.core.session_manager import reset_session

            reset_session()
            self.output_log.write(
                "[info]Session reset, system prompt reloaded, and output cleared.[/info]"
            )
        else:
            self.output_log.write(f"[red]Unknown command: {command_name}[/red]")
            self.output_log.write("Available commands: /model, /reset")

    def update_prompt_label(self, new_label: str):
        """Update the prompt label."""
        if self.prompt_label:
            self.prompt_label.update(new_label)

    async def get_user_input(self) -> str:
        """Get user input asynchronously."""
        if self._input_future and not self._input_future.done():
            self._input_future.cancel()

        self._input_future = asyncio.Future()
        try:
            result = await self._input_future
            return result
        except asyncio.CancelledError:
            return ""
        finally:
            self._input_future = None

    def action_quit(self) -> None:
        """Handle quit action."""
        if self._input_future and not self._input_future.done():
            self._input_future.set_result("exit")
        self.exit()


async def run_textual_app(
    mcp_manager=None, initial_prompt: Optional[str] = None
) -> QXApp:
    """Run the Textual app and return the app instance."""
    app = QXApp()
    if mcp_manager:
        app.set_mcp_manager(mcp_manager)

    # Run the app in the background
    await app._startup()

    return app
