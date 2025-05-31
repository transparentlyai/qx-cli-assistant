import asyncio
import logging
import shutil
import subprocess
from pathlib import Path
from typing import Optional, List, Tuple

from textual import events # Ensure events is imported
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, Container
from textual.message import Message
from textual.widgets import Input, RichLog, Static # Removed TextArea
from textual import on # Import the 'on' decorator

from qx.cli.commands import CommandCompleter
from qx.cli.console import TextualRichLogHandler, qx_console
from qx.core.async_utils import TaskTracker
from qx.core.llm import query_llm
from qx.core.paths import QX_HISTORY_FILE
from qx.core.session_manager import clean_old_sessions, save_session, save_session_async
from qx.custom_widgets.option_selector import OptionSelector
# Import ExtendedInput and its new messages
from qx.custom_widgets.extended_input import (
    ExtendedInput, 
    UserInputSubmitted,
    LogEmitted,
    MultilineModeToggled,
    DisplayCompletionMenu,
    HideCompletionMenu
)
from qx.custom_widgets.completion_menu import CompletionMenu # For type hinting if needed
from qx.core.llm_messages import RenderStreamContent, StreamingComplete

logger = logging.getLogger(__name__)


class StatusFooter(Static):
    """Custom footer widget that displays status messages."""

    def __init__(self, *args, **kwargs):
        super().__init__("[#00ff00]Ready[/]", *args, **kwargs)
        self.add_class("footer")
        self.spinner_chars = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self.spinner_index = 0
        self.spinner_timer = None
        self.base_message = ""

    def update_status(self, message: str):
        self.base_message = message
        if message == "[#00ff00]Ready[/]":
            self.update(f"{message}")
        else:
            self.update(message)

    def start_spinner(self, message: str = "Thinking..."):
        self.base_message = message
        self.spinner_index = 0
        self.update_spinner()
        self.spinner_timer = self.set_interval(0.1, self.update_spinner)

    def stop_spinner(self):
        if self.spinner_timer:
            self.spinner_timer.stop()
            self.spinner_timer = None

    def update_spinner(self):
        spinner_char = self.spinner_chars[self.spinner_index]
        self.update(f"[orange]{spinner_char} {self.base_message}[/orange]")
        self.spinner_index = (self.spinner_index + 1) % len(self.spinner_chars)


class QXApp(App[None]): 
    CSS_PATH = Path(__file__).parent.parent / "css" / "main.css"
    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit", priority=True), 
        Binding("ctrl+d", "quit", "Quit", priority=True),
        # Binding("alt+enter", "toggle_multiline_or_submit", "Toggle Multiline/Submit", show=False), # Handled by ExtendedInput
        Binding("escape", "handle_escape", "Handle Escape", show=False, priority=True),
    ]
    enable_mouse_support = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.prompt_handler = None
        self.output_log: Optional[RichLog] = None
        self.user_input: Optional[ExtendedInput] = None 
        self.prompt_label: Optional[Static] = None
        self.status_footer: Optional[StatusFooter] = None
        self.mcp_manager = None
        self.llm_agent = None
        self.current_message_history = None
        self.keep_sessions = 5
        
        self.approval_container: Optional[Container] = None
        self.approval_selector_instance: Optional[OptionSelector] = None
        self.approval_future: Optional[asyncio.Future] = None
        
        self.text_input_future: Optional[asyncio.Future] = None
        self.is_awaiting_text_input: bool = False
        self._stored_original_prompt_label: str = "QX⏵ " 
        self._multiline_prompt_label: str = "... " # Prompt for multiline input
        
        self._qx_version: str = ""
        self._llm_model_name: str = ""
        self.is_processing: bool = False
        
        self._task_tracker = TaskTracker()
        
        # For managing the CompletionMenu
        self._active_completion_menu: Optional[CompletionMenu] = None


    @property
    def original_prompt_label(self) -> str:
        return self._stored_original_prompt_label

    def set_mcp_manager(self, mcp_manager):
        self.mcp_manager = mcp_manager

    def set_llm_agent(self, llm_agent):
        self.llm_agent = llm_agent

    def set_version_info(self, qx_version: str, llm_model_name: str):
        self._qx_version = qx_version
        self._llm_model_name = llm_model_name
    
    def set_message_history(self, message_history):
        self.current_message_history = message_history

    async def request_confirmation(
        self,
        message: str, 
        choices: str = "ynac", 
        default: str = "n", 
    ) -> Optional[str]:
        option_map = { "y": "Yes", "n": "No", "a": "Approve All", "c": "Cancel", "s": "Skip", "o": "OK"}
        built_options: List[Tuple[str, str]] = []
        default_option_tuple: Optional[Tuple[str, str]] = None
        if default in choices and default in option_map:
            default_option_tuple = (option_map[default], default)
            built_options.append(default_option_tuple)
        for char_key in choices:
            if char_key == default and default_option_tuple is not None: continue 
            if char_key in option_map: built_options.append((option_map[char_key], char_key))
        if not built_options: return default 
        selected_key = await self.request_approval_with_selector(prompt=message, options=built_options)
        return selected_key if selected_key is not None else default

    async def prompt_for_text_input(self, prompt_message: str, default_value: Optional[str] = None) -> Optional[str]:
        if self.is_awaiting_text_input or (self.text_input_future and not self.text_input_future.done()):
            logger.warning("prompt_for_text_input called while another input is already pending.")
            return None 

        if self.approval_container and self.approval_container.display:
            await self._hide_approval_selector() 

        self._stored_original_prompt_label = str(self.prompt_label.renderable) 
        self.prompt_label.update(f"{prompt_message} (Esc to cancel) ")
        
        input_container = self.query_one("#input-container")
        input_container.display = True

        self.user_input.text = default_value or ""
        self.user_input.disabled = False
        self.user_input.can_focus = True
        self.user_input.focus()
        self.user_input.move_cursor_to_end_of_line()

        self.is_awaiting_text_input = True
        self.text_input_future = asyncio.Future()

        try:
            result = await asyncio.wait_for(self.text_input_future, timeout=300.0)
            return result
        except asyncio.TimeoutError:
            logger.warning("Text input timed out.")
            self.output_log.write("[yellow]Text input timed out.[/yellow]")
            return None
        except asyncio.CancelledError:
            logger.info("Text input cancelled.")
            return None
        finally:
            self.is_awaiting_text_input = False
            self.prompt_label.update(self._stored_original_prompt_label) 
            if self.text_input_future and not self.text_input_future.done():
                 self.text_input_future.cancel()
            self.text_input_future = None
            # ExtendedInput's MultilineModeToggled message will handle prompt updates

    async def _handle_llm_query(self, input_text: str) -> None:
        if self.is_processing: return
        try:
            self.is_processing = True
            if self.user_input: self.user_input.disabled = True; self.user_input.can_focus = False
            
            current_prompt = self._multiline_prompt_label if self.user_input and self.user_input.is_multiline_mode else self._stored_original_prompt_label
            grey_prompt = f"[dim]{current_prompt}[/dim]"
            if self.prompt_label: self.prompt_label.update(grey_prompt)

            if self.status_footer: self.status_footer.start_spinner("[#af00d7 bold]Thinking...[/]")
            run_result = await query_llm(agent=self.llm_agent, user_input=input_text, message_history=self.current_message_history, console=qx_console)
            if run_result and hasattr(run_result, "output"):
                output_content = str(run_result.output) if run_result.output is not None else ""
                if output_content.strip() and not self.llm_agent.enable_streaming:
                    self.output_log.write(""); from rich.markdown import Markdown
                    self.output_log.write(Markdown(output_content, code_theme="rrt")); self.output_log.write("")
                elif self.llm_agent.enable_streaming: self.output_log.write("")
                if hasattr(run_result, "all_messages"): self.current_message_history = run_result.all_messages()
                if self.current_message_history: await save_session_async(self.current_message_history); clean_old_sessions(self.keep_sessions)
            if self.status_footer: self.status_footer.stop_spinner(); self.status_footer.update_status("[#00ff00]Ready[/]")
        except asyncio.CancelledError: self.output_log.write("[yellow]Info:[/yellow] Request cancelled"); 
        except Exception as e: import traceback; logger.error(f"Error in LLM: {e}", exc_info=True); self.output_log.write(f"[red]Error:[/red] {e}\n[dim]{traceback.format_exc()}[/dim]")
        finally:
            self.is_processing = False
            if self.user_input: self.user_input.disabled = False; self.user_input.can_focus = True
            # Prompt label updated by MultilineModeToggled or restored here
            if self.prompt_label and self.user_input:
                 self.prompt_label.update(self._multiline_prompt_label if self.user_input.is_multiline_mode else self._stored_original_prompt_label)
            if self.user_input: self.user_input.focus()

    def compose(self) -> ComposeResult:
        with Vertical(id="main-container"):
            yield RichLog(id="output-log", markup=True, wrap=True)
            self.approval_container = Container(id="approval-selector-container", classes="hidden")
            yield self.approval_container
            # Completion menu container - will be mounted here by DisplayCompletionMenu handler
            # yield Container(id="completion-menu-container", classes="hidden") 
            with Vertical(id="bottom-section"):
                with Horizontal(id="input-container"):
                    yield Static(self.original_prompt_label, id="prompt-label")
                    yield ExtendedInput(id="user-input", history_file_path=QX_HISTORY_FILE)
                yield StatusFooter(id="status-footer")

    async def _show_approval_selector(self, options: list[tuple[str, str]], prompt: str):
        if not self.approval_container: return
        if self.approval_selector_instance: await self.approval_selector_instance.remove(); self.approval_selector_instance = None
        self.approval_selector_instance = OptionSelector(options=options, border_title=prompt, id="approval-selector-active")
        try: self.query_one("#input-container").display = False
        except: pass 
        if self.user_input: self.user_input.can_focus = False
        await self.approval_container.mount(self.approval_selector_instance)
        self.approval_container.display = True
        if self.approval_selector_instance: self.approval_selector_instance.focus()

    async def _hide_approval_selector(self):
        if self.approval_container: self.approval_container.display = False
        if self.approval_selector_instance: await self.approval_selector_instance.remove(); self.approval_selector_instance = None
        try: self.query_one("#input-container").display = True
        except: pass
        if self.user_input: self.user_input.can_focus = True; self.user_input.focus()
        if self.approval_future and not self.approval_future.done(): self.approval_future.cancel()
        self.approval_future = None

    async def request_approval_with_selector(self, prompt: str, options: list[tuple[str, str]]) -> Optional[str]:
        if self.approval_future and not self.approval_future.done(): return None
        self.approval_future = asyncio.Future()
        await self._show_approval_selector(options, prompt)
        try: return await asyncio.wait_for(self.approval_future, timeout=300.0)
        except asyncio.TimeoutError: await self._hide_approval_selector(); return None
        except asyncio.CancelledError: 
            if self.approval_container and self.approval_container.display: await self._hide_approval_selector()
            return None
        finally: 
            if self.approval_container and self.approval_container.display: await self._hide_approval_selector()

    async def on_option_selector_option_selected(self, message: OptionSelector.OptionSelected) -> None:
        if self.approval_future and not self.approval_future.done(): self.approval_future.set_result(message.key)
        await self._hide_approval_selector()
    
    async def _process_user_input(self, input_text: str) -> None:
        if self.prompt_handler and self.prompt_handler._input_future and not self.prompt_handler._input_future.done():
            self.prompt_handler.handle_input(input_text); return
        self.output_log.write(f"[red]⏵ {input_text}[/]")
        if self.user_input: self.user_input.add_to_history(input_text) 
        if input_text.lower() in ["exit", "quit"]: await self._async_quit(); return
        if input_text.startswith("/"): await self.handle_command(input_text); return
        if self.llm_agent: 
            await self._task_tracker.create_task(
                self._handle_llm_query(input_text),
                name="llm_query",
                error_handler=lambda e: self.output_log.write(f"[red]LLM Error: {e}[/red]")
            )

    def on_mount(self) -> None:
        self.output_log = self.query_one("#output-log", RichLog)
        self.output_log.can_focus = False
        self.user_input = self.query_one("#user-input", ExtendedInput)
        self.prompt_label = self.query_one("#prompt-label", Static)
        self.status_footer = self.query_one("#status-footer", StatusFooter)
        self._stored_original_prompt_label = str(self.prompt_label.renderable)
        qx_console.set_widgets(self.output_log, self.user_input); qx_console._app = self
        qx_console.set_logger(logging.getLogger("qx"))
        if self._qx_version and self._llm_model_name: self.output_log.write(f"[dim]QX ver:{self._qx_version} - {self._llm_model_name}[/dim]")
        
        if self.mcp_manager and self.user_input:
            command_completer = CommandCompleter(mcp_manager=self.mcp_manager)
            self.user_input.set_command_completer(command_completer)
        
        if self.user_input: self.user_input.focus()

    # Removed action_toggle_multiline_or_submit as ExtendedInput handles it internally
    # and communicates via MultilineModeToggled message.

    async def on_input_submitted(self, event: Input.Submitted) -> None: 
        if event.input.id == "user-input": await self._handle_submitted_text(str(event.value))

    @on(UserInputSubmitted)
    async def on_user_input_submitted(self, event: UserInputSubmitted) -> None:
        await self._handle_submitted_text(event.input_text)

    async def _handle_submitted_text(self, text: str) -> None:
        try:
            if self.is_awaiting_text_input and self.text_input_future and not self.text_input_future.done():
                self.text_input_future.set_result(text)
                if self.user_input: self.user_input.text = "" 
                return 

            if self.is_processing: return 
            
            input_text = text
            if self.user_input:
                self.user_input.text = "" 
                # If it was multiline, ExtendedInput will post MultilineModeToggled(False)
                # which will be handled by on_multiline_mode_toggled to reset the prompt.
            
            if not input_text.strip(): return 
            await self._process_user_input(input_text)
        except Exception as e:
            import traceback; logger.critical(f"Critical error in input handling: {e}", exc_info=True)
            if self.output_log: self.output_log.write(f"[red]Critical Error in Input Handler:[/red] {e}\n[dim]{traceback.format_exc()}[/dim]")

    async def handle_command(self, command_input: str):
        parts = command_input.strip().split(maxsplit=1); command_name = parts[0].lower()
        # ... (rest of handle_command remains the same)
        if command_name == "/model" and self.llm_agent:
            info = f"[bold]Current LLM Model Configuration:[/bold]\n"
            info += f"  Model Name: [green]{self.llm_agent.model_name}[/green]\n"
            info += f"  Provider: [green]OpenRouter (https://openrouter.ai/api/v1)[/green]\n"
            info += f"  Temperature: [green]{self.llm_agent.temperature}[/green]\n"
            info += f"  Max Output Tokens: [green]{self.llm_agent.max_output_tokens}[/green]\n"
            info += f"  Reasoning Effort: [green]{self.llm_agent.reasoning_effort or 'None'}[/green]"
            self.output_log.write(info)
        elif command_name == "/reset":
            if self.output_log: self.output_log.clear()
            self.current_message_history = None
            from qx.core.session_manager import reset_session; reset_session()
            self.output_log.write("[info]Session reset, system prompt reloaded, and output cleared.[/info]")
        elif command_name == "/approve-all":
            import qx.core.user_prompts
            async with qx.core.user_prompts._approve_all_lock: qx.core.user_prompts._approve_all_active = True
            self.output_log.write("[orange]✓ 'Approve All' mode activated for this session.[/orange]")
        else: self.output_log.write(f"[red]Unknown command: {command_name}[/red]")

    def update_prompt_label(self, new_label: str):
        if self.prompt_label and not self.is_awaiting_text_input: 
            self.prompt_label.update(new_label)
            # Do not update _stored_original_prompt_label here if it's a temporary change like multiline

    @on(LogEmitted)
    def on_log_emitted(self, message: LogEmitted) -> None:
        """Handles log messages from ExtendedInput."""
        if self.output_log:
            if message.level == "error":
                self.output_log.write(f"[red]Input Log Error: {message.text}[/red]")
                logger.error(f"ExtendedInput: {message.text}")
            elif message.level == "warning":
                self.output_log.write(f"[yellow]Input Log Warning: {message.text}[/yellow]")
                logger.warning(f"ExtendedInput: {message.text}")
            else:
                self.output_log.write(f"[dim]Input Log: {message.text}[/dim]")
                logger.info(f"ExtendedInput: {message.text}")

    @on(MultilineModeToggled)
    def on_multiline_mode_toggled(self, message: MultilineModeToggled) -> None:
        """Handles multiline mode changes from ExtendedInput."""
        if self.prompt_label and not self.is_awaiting_text_input:
            if message.is_multiline:
                self.prompt_label.update(self._multiline_prompt_label)
            else:
                self.prompt_label.update(self._stored_original_prompt_label)
        if self.user_input: # Ensure input widget is focused after mode toggle
            self.user_input.focus()

    @on(DisplayCompletionMenu)
    async def on_display_completion_menu(self, message: DisplayCompletionMenu) -> None:
        """Handles request to display the completion menu."""
        if self._active_completion_menu:
            await self._active_completion_menu.remove()
            self._active_completion_menu = None
        
        self._active_completion_menu = message.menu_widget
        
        # Mount the menu to the screen. ExtendedInput has already set styles.
        # We assume ExtendedInput (message.anchor_widget) is within a known layout.
        # For simplicity, mounting to screen for overlay effect.
        await self.screen.mount(self._active_completion_menu)
        self._active_completion_menu.focus() # Focus the menu
        if self.user_input: self.user_input.can_focus = False # Prevent input from stealing focus

    @on(HideCompletionMenu)
    async def on_hide_completion_menu(self, message: HideCompletionMenu) -> None:
        """Handles request to hide the completion menu."""
        # Check if the menu to hide is the one we are currently managing
        if self._active_completion_menu and self._active_completion_menu is message.menu_widget:
            await self._active_completion_menu.remove()
            self._active_completion_menu = None
            if self.user_input: 
                self.user_input.can_focus = True
                self.user_input.focus() # Return focus to input
    
    @on(RenderStreamContent)
    def on_render_stream_content(self, message: RenderStreamContent) -> None:
        """Handles LLM streaming content rendering in a thread-safe manner."""
        if self.output_log:
            try:
                if message.is_markdown:
                    from rich.markdown import Markdown
                    markdown = Markdown(message.content, code_theme="rrt")
                    self.output_log.write(markdown)
                else:
                    self.output_log.write(message.content, end=message.end)
            except Exception as e:
                logger.error(f"Error rendering stream content: {e}")
                # Fallback to plain text
                self.output_log.write(message.content, end=message.end)
    
    @on(StreamingComplete)
    def on_streaming_complete(self, message: StreamingComplete) -> None:
        """Handles LLM streaming completion."""
        if self.output_log and message.add_newline:
            self.output_log.write("")  # Add empty line for spacing

    async def cleanup_tasks(self):
        if self.approval_future and not self.approval_future.done(): self.approval_future.cancel()
        if self.text_input_future and not self.text_input_future.done(): self.text_input_future.cancel()
        await self._task_tracker.cancel_all(timeout=2.0)

    def action_quit(self) -> None: 
        asyncio.create_task(self._async_quit())
    
    async def _async_quit(self):
        try:
            if self.status_footer: self.status_footer.stop_spinner()
            if self.approval_container and self.approval_container.display: await self._hide_approval_selector()
            if self._active_completion_menu: await self._active_completion_menu.remove(); self._active_completion_menu = None
            await self.cleanup_tasks()
        except Exception as e: logger.error(f"Error during pre-exit cleanup: {e}", exc_info=True)
        finally:
            if self.prompt_handler and self.prompt_handler._input_future and not self.prompt_handler._input_future.done():
                self.prompt_handler._input_future.set_result("exit")
            self.exit()
    
    async def action_handle_escape(self) -> None:
        # ExtendedInput's escape handler will post HideCompletionMenu if a menu is active.
        # That message is handled by on_hide_completion_menu.
        # If no menu is active, and we are awaiting text input, cancel it.
        if self._active_completion_menu: # This check might be redundant if ExtendedInput handles it
            # ExtendedInput should have already posted HideCompletionMenu
            pass 
        elif self.is_awaiting_text_input and self.text_input_future and not self.text_input_future.done():
            logger.info("Escape pressed during text input. Cancelling.")
            self.output_log.write("[yellow]Input cancelled.[/yellow]")
            self.text_input_future.set_result(None) 
            return
        # If neither of the above, and user_input is focused, clear its text (Textual's default for escape on Input)
        elif self.user_input and self.user_input.has_focus and self.user_input.text:
            self.user_input.text = ""
            self.user_input.action_delete_left_all() # Ensure text is cleared


async def run_textual_app(mcp_manager=None, initial_prompt: Optional[str] = None) -> QXApp:
    app = QXApp()
    if mcp_manager: app.set_mcp_manager(mcp_manager)
    # await app._startup() # _startup is a private Textual method, app.run() handles this.
    return app
