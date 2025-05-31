import asyncio
import shutil
import subprocess
from pathlib import Path
from typing import Optional, List, Callable, Any, Protocol

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
        Binding("up", "history_previous", "History Previous", show=False, priority=True),
        Binding("down", "history_next", "History Next", show=False, priority=True),
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
        try:
            with open(path, "r", encoding="utf-8") as f:
                # Basic parsing: one command per line, ignore empty lines
                return [line.strip() for line in f if line.strip()]
        except Exception as e:
            self.post_message(LogEmitted(f"Error loading history from {path}: {e}", "error"))
            return []

    def _default_save_history(self, path: Path, command: str) -> None:
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "a", encoding="utf-8") as f:
                f.write(command + "\\n")
        except Exception as e:
            self.post_message(LogEmitted(f"Error saving history to {path}: {e}", "error"))

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
        command = command.strip()
        if command and (not self._history or self._history[-1] != command):
            self._history.append(command)
            self._history_index = len(self._history)
            if self.history_file_path and self.history_save_fn:
                self.history_save_fn(self.history_file_path, command)

    async def on_key(self, event: events.Key) -> None:
        if self._selector_widget and self._selector_widget.display:
            if event.key not in ("enter", "escape", "tab"):
                pass
            event.stop()
            return

        if event.key == "enter":
            if not self.is_input_globally_active or not self.is_multiline_mode:
                text_content = str(self.text)
                self.post_message(UserInputSubmitted(text_content))
                event.prevent_default()
                event.stop()
                return

    async def action_complete_path_or_command(self) -> None:
        if self._selector_widget and self._selector_widget.display:
            self._selector_widget.action_move_down()
            return
            
        current_line_index, current_column_index = self.cursor_location
        current_line = self.text.splitlines()[current_line_index] if self.text else ""
        start_of_word = current_column_index
        while start_of_word > 0 and start_of_word <= len(current_line) and not current_line[start_of_word - 1].isspace():
            start_of_word -= 1
        partial_input = current_line[start_of_word:current_column_index]

        if self.command_completer and (start_of_word == 0 or (start_of_word > 0 and current_line[start_of_word-1].isspace())):
            completions = self.command_completer.get_completions(partial_input)
            if completions:
                if len(completions) == 1:
                    self.replace(completions[0], start=(current_line_index, start_of_word), end=(current_line_index, current_column_index))
                    self.action_go_to_end()
                else:
                    self.completion_candidates = completions
                    await self._show_completion_selector(completions, start_of_word, partial_input, is_command=True)
                return

        if not partial_input: # Default tab behavior: insert spaces if no partial input for path completion
            self.insert("    ") 
            return

        # Path completion using bash compgen
        try:
            escaped_path = partial_input.replace("'", "'\\\"'\\\"'")
            result = subprocess.run(
                ["bash", "-c", f"compgen -f -- '{escaped_path}'"],
                capture_output=True, text=True, timeout=1
            )
            stdout, return_code = result.stdout, result.returncode
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e: # Added FileNotFoundError
            stdout, return_code = "", 1
            self.post_message(LogEmitted(f"Path completion error: {e}", "warning"))


        if return_code == 0:
            candidates = stdout.strip().splitlines()
            self.completion_candidates = candidates
            if len(candidates) == 1:
                completed_text = candidates[0]
                self.replace(completed_text, start=(current_line_index, start_of_word), end=(current_line_index, current_column_index))
                if await self._is_directory(completed_text) and not completed_text.endswith(\'/\'):
                    self.insert(\'/\')
                self.post_message(self.PathCompletion(candidates, completed_text))
            elif len(candidates) > 1:
                common_prefix = self._get_common_prefix(candidates)
                if common_prefix and len(common_prefix) > len(partial_input):
                    self.replace(common_prefix, start=(current_line_index, start_of_word), end=(current_line_index, current_column_index))
                    self.post_message(self.PathCompletion(candidates, common_prefix))
                else:
                    await self._show_completion_selector(candidates, start_of_word, partial_input)
                    self.post_message(self.PathCompletion(candidates))
            else: self.post_message(self.PathCompletion([]))
        else: self.post_message(self.PathCompletion([]))

    async def action_history_previous(self) -> None:
        if self._selector_widget and self._selector_widget.display: return
        if not self.is_input_globally_active: return
        if self._history:
            if self._history_index > 0: self._history_index -= 1
            self.text = self._history[self._history_index]
            self.action_go_to_end()

    async def action_history_next(self) -> None:
        if self._selector_widget and self._selector_widget.display: return
        if not self.is_input_globally_active: return
        if self._history:
            if self._history_index < len(self._history) - 1:
                self._history_index += 1
                self.text = self._history[self._history_index]
            else:
                self._history_index = len(self._history)
                self.text = ""
            self.action_go_to_end()

    def action_toggle_multiline_or_submit(self) -> None:
        if self._selector_widget and self._selector_widget.display: return
        if not self.is_input_globally_active: return
        if self.is_multiline_mode:
            self.post_message(UserInputSubmitted(str(self.text)))
            self.is_multiline_mode = False
        else:
            self.is_multiline_mode = True
            if str(self.text).strip(): self.insert("\\n")
        self.post_message(MultilineModeToggled(self.is_multiline_mode))


    async def action_search_history_fzf(self) -> None:
        if self._selector_widget and self._selector_widget.display: return
        if not self.is_input_globally_active: return
        if not self.history_file_path or not self.history_load_fn:
            self.post_message(LogEmitted("History path or load function not configured for fzf search.", "warning"))
            return
        if not shutil.which("fzf"): 
            self.post_message(LogEmitted("fzf not found. Ctrl-R history search disabled.", "warning")); return
        
        history_commands = self.history_load_fn(self.history_file_path) # Reload fresh history
        if not history_commands: 
            self.post_message(LogEmitted("No history found for fzf search.", "info")); return
        
        history_commands.reverse() # fzf typically shows newest first
        try:
            process = await asyncio.create_subprocess_exec(
                "fzf", "--height", "40%", "--header=[History Search]",
                "--prompt=Search> ", "--select-1", "--exit-0", "--no-sort",
                stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(
                process.communicate(input="\\n".join(history_commands).encode("utf-8")),
                timeout=10.0
            )
            if process.returncode == 0:
                selected_command = stdout.decode("utf-8").strip()
                if selected_command: 
                    self.text = selected_command
                    self.action_go_to_end()
            elif process.returncode == 130: pass # User exited fzf (e.g. Ctrl-C)
            else: self.post_message(LogEmitted(f"Error running fzf: {stderr.decode(\'utf-8\').strip()}", "error"))
        except asyncio.TimeoutError: self.post_message(LogEmitted("fzf search timed out", "error"))
        except FileNotFoundError: self.post_message(LogEmitted("fzf command not found.", "error"))
        except Exception as e: self.post_message(LogEmitted(f"Error running fzf: {e}", "error"))

    async def action_handle_escape(self) -> None:
        if self._selector_widget and self._selector_widget.display:
            await self._hide_completion_selector()
            return

    async def _is_directory(self, path_str: str) -> bool: # Renamed path to path_str to avoid conflict
        return Path(path_str).is_dir()

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
            display_name = candidate.split(\'/\')[-1] if \'/\' in candidate and not is_command else candidate
            # Basic type detection, can be enhanced
            item_type = "cmd" if is_command else ("dir" if Path(candidate).is_dir() else "file")
            items_for_menu.append((display_name, item_type))
        
        self._selector_widget = CompletionMenu(items_for_menu, owner=self, id=f"{self.id or \'ext_input\'}_completion_menu")
        # Styling and positioning should ideally be handled by the parent via DisplayCompletionMenu
        # For now, keeping basic positioning logic, but parent should override/manage
        self._selector_widget.styles.position = "absolute"
        self._selector_widget.styles.left = 0 
        self._selector_widget.styles.top = self.cursor_location[0] + 1 # Relative to this widget
        self._selector_widget.styles.layer = "above" # Ensure it's on top
        
        self.can_focus = False 
        self.post_message(DisplayCompletionMenu(self._selector_widget, self))
        # self._selector_widget.focus() # Parent should handle focus after mounting

    async def _hide_completion_selector(self) -> None:
        if self._selector_widget:
            menu_to_hide = self._selector_widget
            self._selector_widget = None # Clear reference first
            self.post_message(HideCompletionMenu(menu_to_hide))
            self._completion_start = None
            self._completion_partial_path = None
            self.can_focus = True 
            self.focus() # Refocus self
    
    @on(CompletionMenu.ItemSelected)
    async def handle_completion_menu_item_selected(self, message: CompletionMenu.ItemSelected) -> None:
        # Ensure the message is from our owned menu if multiple ExtendedInputs exist
        if message.owner_widget is not self: return

        self.log(f"ExtendedInput received ItemSelected: {message.item} (index {message.index})")
        if self._selector_widget and 0 <= message.index < len(self.completion_candidates):
            selected_full_candidate = self.completion_candidates[message.index]
            
            current_row, current_col = self.cursor_location
            # start_replace_coords should be where the partial input started
            start_replace_coords = (current_row, self._completion_start if self._completion_start is not None else current_col)
            # end_replace_coords is where the cursor was when completion was triggered (before common prefix insertion)
            # or the end of the common prefix if one was inserted.
            # For simplicity, using current_col might be problematic if text was inserted (e.g. common prefix)
            # A more robust way would be to track the length of the text that triggered the menu.
            # Using self._completion_partial_path length for now.
            end_replace_col = (self._completion_start if self._completion_start is not None else 0) + \
                              len(self._completion_partial_path if self._completion_partial_path is not None else "")
            end_replace_coords = (current_row, end_replace_col)

            self.replace(selected_full_candidate, start=start_replace_coords, end=end_replace_coords)
            
            is_path_completion = \'/\' in selected_full_candidate or Path(selected_full_candidate).exists()
            if is_path_completion and Path(selected_full_candidate).is_dir() and not selected_full_candidate.endswith(\'/\'):
                self.insert(\'/\')
            
            await self._hide_completion_selector()
            message.stop()
    
    @on(CompletionMenu.Cancelled)
    async def handle_completion_menu_cancelled(self, message: CompletionMenu.Cancelled) -> None:
        if message.owner_widget is not self: return
        self.log(f"ExtendedInput received Cancelled")
        if self._selector_widget: # Check if it's our menu
            await self._hide_completion_selector()
            message.stop()

    def on_mount(self) -> None:
        # Ensure CompletionMenu knows its owner if it needs to send messages back directly
        # This is done by passing `owner=self` when creating CompletionMenu
        pass
