import asyncio
import shutil
import subprocess
from pathlib import Path
from typing import Optional, List, Callable, Any, Protocol
from datetime import datetime # Added for timestamping

from textual import events, on
from textual.binding import Binding
from textual.message import Message
from textual.reactive import reactive
from textual.widgets import TextArea
from textual.widget import Widget

# Assuming CompletionMenu is or will be a self-contained component
from qx.custom_widgets.completion_menu import CompletionMenu


# --- Messages for decoupling ---
class UserInputSubmitted(Message):
    """Posted when user submits input."""
    def __init__(self, input_text: str):
        self.input_text = input_text
        super().__init__()

class LogEmitted(Message):
    """Posted when the widget wants to log a message."""
    def __init__(self, text: str, level: str = "info"):
        self.text = text
        self.level = level
        super().__init__()

class MultilineModeToggled(Message):
    """Posted when multiline mode is toggled."""
    def __init__(self, is_multiline: bool):
        self.is_multiline = is_multiline
        super().__init__()

class DisplayCompletionMenu(Message):
    """Requests the parent to display the completion menu."""
    def __init__(self, menu_widget: Widget, anchor_widget: Widget):
        self.menu_widget = menu_widget
        self.anchor_widget = anchor_widget # The ExtendedInput instance
        super().__init__()

class HideCompletionMenu(Message):
    """Requests the parent to hide the completion menu."""
    def __init__(self, menu_widget: Widget):
        self.menu_widget = menu_widget
        super().__init__()

# --- Protocols for configurable components ---
class CommandCompleterProtocol(Protocol):
    def get_completions(self, partial_input: str) -> List[str]:
        ...

class HistoryLoadFunction(Protocol):
    def __call__(self, path: Path) -> List[str]:
        ...

class HistorySaveFunction(Protocol):
    def __call__(self, path: Path, command: str) -> None:
        ...

class ExtendedInput(TextArea):
    BINDINGS = [
        Binding("tab", "complete_path_or_command", "Complete Path/Command", show=False),
        Binding("up", "navigate_up_or_history", "Navigate Up / History Previous", show=False, priority=True),
        Binding("down", "navigate_down_or_history", "Navigate Down / History Next", show=False, priority=True),
        Binding("alt+enter", "toggle_multiline_or_submit", "Toggle Multiline/Submit", show=False),
        Binding("ctrl+r", "search_history_fzf", "Search History (fzf)", show=False),
        Binding("escape", "handle_escape", "Handle Escape", show=False, priority=True),
    ]

    completion_candidates = reactive([])
    _completion_start: Optional[int] = None
    _completion_partial_path: Optional[str] = None
    _selector_widget: Optional[CompletionMenu] = None
    is_multiline_mode = reactive(False)
    is_input_globally_active = reactive(True) # New property

    class PathCompletion(Message):
        """Posted when path completion occurs (internal or for parent)."""
        def __init__(self, candidates: list[str], completed_text: str | None = None) -> None:
            super().__init__()
            self.candidates = candidates
            self.completed_text = completed_text

    def __init__(
        self,
        *args: Any,
        command_completer: Optional[CommandCompleterProtocol] = None,
        history_file_path: Optional[Path] = None,
        history_load_fn: Optional[HistoryLoadFunction] = None,
        history_save_fn: Optional[HistorySaveFunction] = None,
        **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)
        self.command_completer = command_completer
        self.history_file_path = history_file_path
        self.history_load_fn = history_load_fn
        self.history_save_fn = history_save_fn
        
        self.completions: list[str] = []
        self.completion_index = -1
        self._history: list[str] = []
        self._history_index: int = -1
        
        if self.history_file_path and self.history_load_fn:
            self.load_history()
        elif not self.history_load_fn and self.history_file_path:
            # Default file-based history if path provided but no custom load/save
            self.history_load_fn = self._default_load_history
            self.history_save_fn = self._default_save_history
            self.load_history()

    def _default_load_history(self, path: Path) -> List[str]:
        if not path.exists():
            return []
        
        history_entries = []
        current_command_lines = []
        try:
            with open(path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            
            for line in lines:
                stripped_line = line.strip()
                if stripped_line.startswith("# "): # Timestamp line
                    # If we were accumulating a command, save it before starting a new one
                    if current_command_lines:
                        history_entries.append("\n".join(current_command_lines))
                        current_command_lines = []
                    # We don't need to store the timestamp itself for in-memory history
                elif stripped_line.startswith("+"):
                    current_command_lines.append(stripped_line[1:]) # Remove '+' and add
                elif not stripped_line and current_command_lines: # Blank line signifies end of entry
                    history_entries.append("\n".join(current_command_lines))
                    current_command_lines = []
            
            # Add any remaining command after loop (if file doesn't end with blank line)
            if current_command_lines:
                history_entries.append("\n".join(current_command_lines))

        except Exception as e:
            self.post_message(LogEmitted(f"Error loading history from {path}: {e}", "error"))
        return history_entries

    def _default_save_history(self, path: Path, command: str) -> None:
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "a", encoding="utf-8") as f:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
                f.write(f"\n# {timestamp}\n") # Start with a newline for separation
                command_lines = command.splitlines()
                if not command_lines and command == "": # Handle truly empty command string
                    f.write("+\n") # Save as an empty command line
                elif not command_lines and command != "": # Command is not empty but has no newlines (e.g. "foo")
                    f.write(f"+{command}\n")
                else: # Command has newlines or is non-empty single line
                    for line in command_lines:
                        f.write(f"+{line}\n")
                # The example shows a blank line after, which is achieved by the initial \n for the next entry
        except Exception as e:
            self.post_message(LogEmitted(f"Error saving history to {path}: {e}", "error"))

    def set_command_completer(self, completer: CommandCompleterProtocol) -> None:
        """Set the command completer after initialization."""
        self.command_completer = completer

    def load_history(self) -> None:
        if self.history_file_path and self.history_load_fn:
            self._history = self.history_load_fn(self.history_file_path)
            self._history_index = len(self._history)
            if not self.history_file_path.exists() and self.history_save_fn: # Ensure dir exists for default save
                 try:
                    self.history_file_path.parent.mkdir(parents=True, exist_ok=True)
                 except Exception as e:
                    self.post_message(LogEmitted(f"Error creating history directory {self.history_file_path.parent}: {e}", "error"))


    def add_to_history(self, command: str) -> None:
        # command here is expected to be the raw string, possibly multiline
        processed_command_for_comparison = command.strip() # For duplicate check
        # Avoid adding if it's the same as the last command (even if original had different whitespace)
        if processed_command_for_comparison and (not self._history or self._history[-1].strip() != processed_command_for_comparison):
            self._history.append(command) # Store the original command
            self._history_index = len(self._history)
            if self.history_file_path and self.history_save_fn:
                self.history_save_fn(self.history_file_path, command) # Pass original command

    def _adjust_multiline_mode_for_text(self, text_content: str) -> None:
        """Adjusts multiline mode based on the presence of newlines in text_content."""
        is_multiline_content = "\n" in text_content
        if self.is_multiline_mode != is_multiline_content:
            self.is_multiline_mode = is_multiline_content
            self.post_message(MultilineModeToggled(self.is_multiline_mode))

    async def on_key(self, event: events.Key) -> None:
        if self._selector_widget and self._selector_widget.display:
            if event.key not in ("enter", "escape", "tab"):
                pass # Allow selector to handle other keys like up/down
            event.stop() # Stop further processing for enter, escape, tab if menu is up
            return

        if event.key == "enter":
            if not self.is_input_globally_active or not self.is_multiline_mode:
                text_content = str(self.text)
                self.post_message(UserInputSubmitted(text_content))
                event.prevent_default()
                event.stop()
                return
            # If in multiline mode, Enter key is handled by TextArea default behavior (insert newline)
            # unless specifically overridden for submission (e.g., Ctrl+Enter or specific logic)

    async def action_navigate_up_or_history(self) -> None:
        """Handles up arrow key press.
        In multiline mode, navigates text up, or to previous history if at the first line.
        In single-line mode, always navigates to previous history.
        """
        if self._selector_widget and self._selector_widget.display:
             # If completion menu is active, let it handle the up arrow
            self._selector_widget.action_move_up()
            return

        if not self.is_input_globally_active:
            return

        if self.is_multiline_mode:
            current_row, _ = self.cursor_location
            if current_row == 0:
                await self.action_history_previous()
            else:
                self.action_cursor_up()
        else:
            await self.action_history_previous()

    async def action_navigate_down_or_history(self) -> None:
        """Handles down arrow key press.
        In multiline mode, navigates text down, or to next history if at the last line.
        In single-line mode, always navigates to next history.
        """
        if self._selector_widget and self._selector_widget.display:
            # If completion menu is active, let it handle the down arrow
            self._selector_widget.action_move_down()
            return
            
        if not self.is_input_globally_active:
            return

        if self.is_multiline_mode:
            current_row, _ = self.cursor_location
            # self.document.line_count gives total lines. Last line index is line_count - 1.
            if current_row == self.document.line_count - 1:
                await self.action_history_next()
            else:
                self.action_cursor_down()
        else:
            await self.action_history_next()

    async def action_complete_path_or_command(self) -> None:
        if self._selector_widget and self._selector_widget.display:
            self._selector_widget.action_move_down() # Or a specific "select current" if that's the tab behavior for menu
            return
            
        current_line_index, current_column_index = self.cursor_location
        current_line_text = self.document.get_line(current_line_index) # Use document API
        
        start_of_word = current_column_index
        while start_of_word > 0 and not current_line_text[start_of_word - 1].isspace():
            start_of_word -= 1
        partial_input = current_line_text[start_of_word:current_column_index]

        if self.command_completer and (start_of_word == 0 or (start_of_word > 0 and current_line_text[start_of_word-1].isspace())):
            completions = self.command_completer.get_completions(partial_input)
            if completions:
                if len(completions) == 1:
                    self.replace(completions[0], start=(current_line_index, start_of_word), end=(current_line_index, current_column_index))
                    self.move_cursor(self.document.end_of_line((current_line_index, self.cursor_location[1] + len(completions[0]) - len(partial_input))))
                    self.scroll_cursor_visible()
                else:
                    self.completion_candidates = completions
                    await self._show_completion_selector(completions, start_of_word, partial_input, is_command=True)
                return

        if not partial_input: # Default tab behavior: insert spaces if no partial input for path completion
            self.insert("    ") 
            return

        # Path completion using bash compgen
        try:
            cmd = ["bash", "-c", f"compgen -f -- '{partial_input}'"]
            result = subprocess.run(
                cmd,
                capture_output=True, text=True, timeout=1, check=False 
            )
            stdout, return_code = result.stdout, result.returncode
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            stdout, return_code = "", 1
            self.post_message(LogEmitted(f"Path completion error: {e}", "warning"))
        except Exception as e: 
            stdout, return_code = "", 1
            self.post_message(LogEmitted(f"Path completion general error: {e}", "error"))


        if return_code == 0:
            candidates = stdout.strip().splitlines()
            self.completion_candidates = candidates
            if len(candidates) == 1:
                completed_text = candidates[0]
                self.replace(completed_text, start=(current_line_index, start_of_word), end=(current_line_index, current_column_index))
                if await self._is_directory(completed_text) and not completed_text.endswith('/'):
                    self.insert('/') 
                else: 
                    self.move_cursor((current_line_index, start_of_word + len(completed_text)))
                self.scroll_cursor_visible()
                self.post_message(self.PathCompletion(candidates, completed_text))

            elif len(candidates) > 1:
                common_prefix = self._get_common_prefix(candidates)
                if common_prefix and len(common_prefix) > len(partial_input):
                    self.replace(common_prefix, start=(current_line_index, start_of_word), end=(current_line_index, current_column_index))
                    self.move_cursor((current_line_index, start_of_word + len(common_prefix)))
                    self.scroll_cursor_visible()
                    self.post_message(self.PathCompletion(candidates, common_prefix))
                else: 
                    await self._show_completion_selector(candidates, start_of_word, partial_input)
                    self.post_message(self.PathCompletion(candidates))
            else: 
                self.post_message(self.PathCompletion([]))
        else: 
            self.post_message(self.PathCompletion([]))


    async def action_history_previous(self) -> None:
        if self._selector_widget and self._selector_widget.display: return
        if not self.is_input_globally_active: return
        if self._history:
            if self._history_index > 0: 
                self._history_index -= 1
                self.text = self._history[self._history_index]
                self._adjust_multiline_mode_for_text(self.text)
                self.move_cursor(self.document.end)
                self.scroll_cursor_visible()

    async def action_history_next(self) -> None:
        if self._selector_widget and self._selector_widget.display: return
        if not self.is_input_globally_active: return
        if self._history:
            if self._history_index < len(self._history) - 1:
                self._history_index += 1
                self.text = self._history[self._history_index]
            else: # At the newest history item or beyond
                self._history_index = len(self._history) # Point to one past the end (for new input)
                self.text = ""
            self._adjust_multiline_mode_for_text(self.text)
            self.move_cursor(self.document.end)
            self.scroll_cursor_visible()

    def action_toggle_multiline_or_submit(self) -> None:
        if self._selector_widget and self._selector_widget.display: return
        if not self.is_input_globally_active: return
        if self.is_multiline_mode:
            self.post_message(UserInputSubmitted(str(self.text)))
            self.is_multiline_mode = False # Toggle mode first
        else:
            self.is_multiline_mode = True  # Toggle mode first
            if str(self.text).strip(): # If there's text, add a newline to start editing on the next line
                self.insert("\n")
        self.post_message(MultilineModeToggled(self.is_multiline_mode))

    async def action_search_history_fzf(self) -> None:
        if self._selector_widget and self._selector_widget.display:
            return
        if not self.is_input_globally_active:
            return
        if not self.history_file_path or not self.history_load_fn:
            self.post_message(LogEmitted("History path or load function not configured for fzf search.", "warning"))
            return
        if not shutil.which("fzf"):
            self.post_message(LogEmitted("fzf not found. Ctrl-R history search disabled.", "warning"))
            return

        history_commands = self.history_load_fn(self.history_file_path)
        if not history_commands:
            self.post_message(LogEmitted("No history found for fzf search.", "info"))
            return

        history_commands.reverse()  # fzf typically shows newest first

        selected_command_str: Optional[str] = None
        
        # Use the App.suspend() context manager to handle terminal suspension and resumption
        with self.app.suspend():
            try:
                process = await asyncio.create_subprocess_exec(
                    "fzf",
                    "--height=40%",
                    "--header=[History Search]",
                    "--prompt=Search> ",
                    "--select-1",  # Automatically select the highlighted item on Enter
                    "--exit-0",    # Exit with 0 if an item is selected, 1 if no match/Esc
                    "--no-sort",   # Use the input order (we've reversed it)
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                fzf_input = "\n".join(history_commands).encode("utf-8")
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(input=fzf_input),
                    timeout=300.0  # Generous timeout for user interaction
                )
                
                fzf_return_code = process.returncode

                if fzf_return_code == 0 and stdout:
                    selected_command_str = stdout.decode("utf-8").strip()
                elif fzf_return_code == 1: # User pressed Esc or no match
                    self.post_message(LogEmitted("fzf: No selection made or Esc pressed.", "info"))
                elif fzf_return_code == 130: # User pressed Ctrl+C
                    self.post_message(LogEmitted("fzf: Cancelled by user (Ctrl+C).", "info"))
                elif fzf_return_code is not None and fzf_return_code > 1 : # Other fzf errors
                    error_output = stderr.decode('utf-8').strip() if stderr else "Unknown fzf error"
                    self.post_message(LogEmitted(f"fzf error (code {fzf_return_code}): {error_output}", "error"))

            except asyncio.TimeoutError:
                self.post_message(LogEmitted("fzf search timed out.", "error"))
            except FileNotFoundError:
                self.post_message(LogEmitted("fzf command not found. Please ensure it's installed and in your PATH.", "error"))
            except Exception as e:
                self.post_message(LogEmitted(f"An unexpected error occurred with fzf: {e}", "error"))
        
        # Textual automatically resumes after the 'with self.app.suspend():' block.

        if selected_command_str:
            self.text = selected_command_str
            self._adjust_multiline_mode_for_text(self.text)
            self.move_cursor(self.document.end)
            self.scroll_cursor_visible()
        
        self.focus() # Re-focus the input field after fzf interaction

    async def action_handle_escape(self) -> None:
        if self._selector_widget and self._selector_widget.display:
            await self._hide_completion_selector()
            return

    async def _is_directory(self, path_str: str) -> bool: 
        try:
            return Path(path_str).is_dir()
        except Exception:
            return False

    def _get_common_prefix(self, strings: list[str]) -> str:
        if not strings: return ""
        prefix = strings[0]
        for s in strings[1:]:
            while not s.startswith(prefix):
                prefix = prefix[:-1]
                if not prefix: return ""
        return prefix

    async def _show_completion_selector(self, candidates: list[str], start_pos: int, partial_text: str, is_command: bool = False) -> None:
        await self._hide_completion_selector() 
        self._completion_start = start_pos
        self._completion_partial_path = partial_text
        self.completion_candidates = candidates

        items_for_menu = []
        for candidate in candidates:
            display_name = candidate.split('/')[-1] if '/' in candidate and not is_command else candidate
            item_type = "cmd" if is_command else ("dir" if await self._is_directory(candidate) else "file")
            items_for_menu.append((display_name, item_type))
        
        self._selector_widget = CompletionMenu(items_for_menu, owner=self, id=f"{self.id or 'ext_input'}_completion_menu")
        
        self.can_focus = False 
        self.post_message(DisplayCompletionMenu(self._selector_widget, self))

    async def _hide_completion_selector(self) -> None:
        if self._selector_widget:
            menu_to_hide = self._selector_widget
            self._selector_widget = None 
            self.post_message(HideCompletionMenu(menu_to_hide))
            self._completion_start = None
            self._completion_partial_path = None
            self.can_focus = True 

    
    @on(CompletionMenu.ItemSelected)
    async def handle_completion_menu_item_selected(self, message: CompletionMenu.ItemSelected) -> None:
        if message.owner_widget is not self: return

        self.log(f"ExtendedInput received ItemSelected: {message.item} (index {message.index})")
        if 0 <= message.index < len(self.completion_candidates): 
            selected_full_candidate = self.completion_candidates[message.index]
            
            current_row, _ = self.cursor_location 
            start_col = self._completion_start if self._completion_start is not None else 0
            original_partial_len = len(self._completion_partial_path if self._completion_partial_path is not None else "")
            end_col = start_col + original_partial_len

            start_replace_coords = (current_row, start_col)
            end_replace_coords = (current_row, end_col)

            self.replace(selected_full_candidate, start=start_replace_coords, end=end_replace_coords)
            
            new_cursor_col = start_col + len(selected_full_candidate)
            self.move_cursor((current_row, new_cursor_col))
            
            is_path_completion = '/' in selected_full_candidate or Path(selected_full_candidate).exists() 
            if is_path_completion and await self._is_directory(selected_full_candidate) and not selected_full_candidate.endswith('/'):
                self.insert('/') 
            
            self.scroll_cursor_visible() 
            
            await self._hide_completion_selector() 
            message.stop()
    
    @on(CompletionMenu.Cancelled)
    async def handle_completion_menu_cancelled(self, message: CompletionMenu.Cancelled) -> None:
        if message.owner_widget is not self: return
        self.log(f"ExtendedInput received Cancelled")
        if self._selector_widget: 
            await self._hide_completion_selector()
            message.stop()

    def on_mount(self) -> None:
        pass
