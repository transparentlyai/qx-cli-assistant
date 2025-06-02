import logging
from pathlib import Path
from datetime import datetime

from prompt_toolkit.history import History  # Import History

from qx.core.paths import QX_HISTORY_FILE

logger = logging.getLogger("qx")


class QXHistory(History):  # Inherit from History
    """Custom history class that reads/writes QX's specific history file format."""

    def __init__(self, history_file_path: Path = QX_HISTORY_FILE):
        super().__init__()  # Call parent constructor
        self.history_file_path = history_file_path
        self._loaded_strings = []
        self.load_history()

    def load_history(self):
        """Load history from the Qx format file."""
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
                    if current_command_lines:
                        history_entries.append("\n".join(current_command_lines))
                        current_command_lines = []
                elif stripped_line.startswith("+"):
                    current_command_lines.append(stripped_line[1:])
                elif not stripped_line and current_command_lines:
                    history_entries.append("\n".join(current_command_lines))
                    current_command_lines = []

            if current_command_lines:
                history_entries.append("\n".join(current_command_lines))

            self._loaded_strings = history_entries

        except Exception as e:
            logger.error(f"Error loading history from {self.history_file_path}: {e}")

    def append_string(self, command: str):
        """Add a new command to history (prompt_toolkit interface)."""
        command = command.strip()
        if command and (
            not self._loaded_strings or self._loaded_strings[-1] != command
        ):
            self._loaded_strings.append(command)

    def store_string(self, command: str):
        """Store a string in the history (alternative prompt_toolkit interface)."""
        self.append_string(command)

    def _write_entry_to_file(self, f, command: str):
        """Helper to write a single command to the history file."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        f.write(f"\n# {timestamp}\n")

        command_lines = command.split("\n")
        if len(command_lines) == 1 and not command_lines[0]:
            f.write("+\n")
        else:
            for line in command_lines:
                f.write(f"+{line}\n")

    def flush_history(self):
        """Save all current in-memory history entries to the file."""
        try:
            self.history_file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.history_file_path, "w", encoding="utf-8") as f:
                pass

            with open(self.history_file_path, "a", encoding="utf-8") as f:
                for command in self._loaded_strings:
                    self._write_entry_to_file(f, command)
        except Exception as e:
            logger.error(f"Error flushing history to {self.history_file_path}: {e}")

    def load_history_strings(self):
        """Load and return history strings (prompt_toolkit abstract method)."""
        return self._loaded_strings

    def get_strings(self):
        """Return all history strings (prompt_toolkit interface)."""
        return self._loaded_strings

    async def load(self):
        """Async load method (prompt_toolkit interface)."""
        # Yield entries in reverse order (newest first) for proper Up arrow navigation
        for entry in reversed(self._loaded_strings):
            yield entry

    def __iter__(self):
        """Iterator for prompt_toolkit compatibility."""
        return iter(self._loaded_strings)

    def __getitem__(self, index):
        """Index access for prompt_toolkit compatibility."""
        return self._loaded_strings[index]

    def __len__(self):
        """Length for prompt_toolkit compatibility."""
        return len(self._loaded_strings)
