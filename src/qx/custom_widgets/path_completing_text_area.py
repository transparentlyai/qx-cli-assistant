from textual.widgets import TextArea
from textual.message import Message
from textual.widget import Widget # Import Widget for type hinting
from textual.binding import Binding
from textual.events import Key
from textual.reactive import reactive
import subprocess
from pathlib import Path

class PathCompletingTextArea(TextArea):
    """
    A TextArea widget that provides bash-like path autocompletion on Tab key press.
    """

    BINDINGS = [
        Binding("tab", "complete_path", "Complete Path", show=False),
    ]

    # Reactive attribute to hold the current completion candidates
    completion_candidates = reactive([])

    class PathCompletion(Message):
        """Message sent when path completion is attempted."""
        def __init__(self, sender: Widget, candidates: list[str], completed_text: str | None = None) -> None:
            super().__init__(sender)
            self.candidates = candidates
            self.completed_text = completed_text

    async def action_complete_path(self) -> None:
        """Action to trigger path completion."""
        current_line_index, current_column_index = self.cursor_location
        current_line = self.text.splitlines()[current_line_index]
        
        # Find the start of the word/path before the cursor
        start_of_word = current_column_index
        while start_of_word > 0 and not current_line[start_of_word - 1].isspace() and current_line[start_of_word - 1] not in ['/', '\\', ' ']:
            start_of_word -= 1
        
        partial_path = current_line[start_of_word:current_column_index]

        if not partial_path:
            # If no partial path, just insert a tab character
            self.insert("    ") # Insert 4 spaces for tab
            return

        # Use subprocess to get completions
        try:
            # Use bash to run compgen
            result = subprocess.run(
                ["bash", "-c", f"compgen -f -- '{partial_path}'"],
                capture_output=True,
                text=True,
                timeout=5
            )
            stdout = result.stdout
            return_code = result.returncode
        except subprocess.TimeoutExpired:
            stdout = ""
            return_code = 1
        except Exception:
            stdout = ""
            return_code = 1

        if return_code == 0:
            candidates = stdout.strip().splitlines()
            self.completion_candidates = candidates # Update reactive attribute

            if len(candidates) == 1:
                completed_text = candidates[0]
                # Calculate the text to insert (only the completion part)
                text_to_insert = completed_text[len(partial_path):]
                
                # If the completion is a directory, add a '/'
                if await self._is_directory(completed_text) and not completed_text.endswith('/'):
                    text_to_insert += '/'

                self.insert(text_to_insert)
                self.post_message(self.PathCompletion(self, candidates, completed_text))
            elif len(candidates) > 1:
                # For multiple candidates, find the common prefix
                common_prefix = self._get_common_prefix(candidates)
                if common_prefix and len(common_prefix) > len(partial_path):
                    text_to_insert = common_prefix[len(partial_path):]
                    self.insert(text_to_insert)
                    self.post_message(self.PathCompletion(self, candidates, common_prefix))
                else:
                    # If no common prefix or already completed to common prefix, list candidates
                    self.post_message(self.PathCompletion(self, candidates))
            else:
                self.post_message(self.PathCompletion(self, []))
        else:
            # Handle error or no completions
            self.post_message(self.PathCompletion(self, []))

    async def _is_directory(self, path: str) -> bool:
        """Helper to check if a path is a directory."""
        return Path(path).is_dir()

    def _get_common_prefix(self, strings: list[str]) -> str:
        """Helper to find the common prefix among a list of strings."""
        if not strings:
            return ""
        
        prefix = strings[0]
        for s in strings[1:]:
            while not s.startswith(prefix):
                prefix = prefix[:-1]
                if not prefix:
                    return ""
        return prefix
