import logging
from pathlib import Path
from datetime import datetime

from qx.core.paths import QX_HISTORY_FILE

logger = logging.getLogger("qx")

class QXHistory:
    """Custom history class that reads/writes QX's specific history file format."""

    def __init__(self, history_file_path: Path = QX_HISTORY_FILE):
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
            logger.error(f"Error loading history from {self.history_file_path}: {e}")

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
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
                f.write(f"\n# {timestamp}\n")  # Start with a newline for separation

                command_lines = command.split("\n")
                if len(command_lines) == 1 and not command_lines[0]:  # Empty command
                    f.write("+\n")
                else:  # Command has newlines or is non-empty single line
                    for line in command_lines:
                        f.write(f"+{line}\n")
        except Exception as e:
            logger.error(f"Error saving history to {self.history_file_path}: {e}")

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
