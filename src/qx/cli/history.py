import logging
import os
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

        # Debug logging for initialization
        logger.debug(f"Initializing QXHistory with path: {self.history_file_path}")
        logger.debug(
            f"History file path resolved to: {self.history_file_path.absolute()}"
        )
        logger.debug(f"History file exists: {self.history_file_path.exists()}")
        logger.debug(f"Parent directory: {self.history_file_path.parent}")
        logger.debug(
            f"Parent directory exists: {self.history_file_path.parent.exists()}"
        )

        self.load_history()

    def load_history(self):
        """Load history from the Qx format file."""
        if not self.history_file_path.exists():
            logger.debug(f"History file does not exist yet: {self.history_file_path}")
            return

        history_entries = []
        current_command_lines = []

        try:
            logger.debug(f"Loading history from: {self.history_file_path}")
            file_size = self.history_file_path.stat().st_size
            logger.debug(f"History file size: {file_size} bytes")

            with open(self.history_file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            logger.debug(f"Read {len(lines)} lines from history file")

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
            logger.debug(f"Loaded {len(history_entries)} history entries")

        except PermissionError as e:
            logger.error(f"Permission denied when reading history: {e}")
            logger.error(f"History file path: {self.history_file_path}")
            logger.error(
                f"File permissions: {oct(self.history_file_path.stat().st_mode)[-3:] if self.history_file_path.exists() else 'N/A'}"
            )
        except UnicodeDecodeError as e:
            logger.error(f"Unicode decode error in history file: {e}")
            logger.error("History file might contain invalid UTF-8 characters")
            logger.error("Consider backing up and removing the history file")
        except Exception as e:
            logger.error(
                f"Error loading history from {self.history_file_path}: {type(e).__name__}: {e}"
            )

    def append_string(self, command: str):  # type: ignore[override]
        """Add a new command to history (prompt_toolkit interface)."""
        command = command.strip()
        if command and (
            not self._loaded_strings or self._loaded_strings[-1] != command
        ):
            logger.debug(
                f"Adding new command to history: {command[:50]}{'...' if len(command) > 50 else ''}"
            )
            self._loaded_strings.append(command)
            # Save immediately to disk
            self._save_single_entry(command)
        else:
            logger.debug(
                f"Skipping duplicate or empty command: {command[:50] if command else '(empty)'}"
            )

    def store_string(self, command: str):  # type: ignore[override]
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

    def _save_single_entry(self, command: str):
        """Save a single command to history file immediately."""
        try:
            # Debug logging for directory creation
            parent_dir = self.history_file_path.parent
            if not parent_dir.exists():
                logger.debug(f"Creating history directory: {parent_dir}")
                try:
                    parent_dir.mkdir(parents=True, exist_ok=True)
                    logger.debug(f"Successfully created directory: {parent_dir}")
                except Exception as dir_error:
                    logger.error(
                        f"Failed to create directory {parent_dir}: {dir_error}"
                    )
                    logger.error(
                        f"Directory permissions: Parent of {parent_dir} is writable: {parent_dir.parent.exists() and os.access(parent_dir.parent, os.W_OK)}"
                    )
                    raise

            # Debug logging for file write
            logger.debug(f"Writing to history file: {self.history_file_path}")
            logger.debug(f"Command length: {len(command)} characters")

            with open(self.history_file_path, "a", encoding="utf-8") as f:
                self._write_entry_to_file(f, command)
                logger.debug("Successfully wrote command to history")

        except PermissionError as e:
            logger.error(f"Permission denied when saving to history: {e}")
            logger.error(f"History file path: {self.history_file_path}")
            logger.error(f"Current user: {os.getenv('USER', 'unknown')}")
            logger.error(f"HOME environment variable: {os.getenv('HOME', 'not set')}")
            logger.error(
                "Try setting QX_HISTORY_FILE environment variable to a writable location"
            )
        except OSError as e:
            logger.error(f"OS error when saving to history: {e}")
            logger.error(
                "This might be due to disk full, read-only filesystem, or network issues"
            )
        except Exception as e:
            logger.error(
                f"Unexpected error saving command to history: {type(e).__name__}: {e}"
            )
            logger.error(f"History file path: {self.history_file_path}")

    def flush_history(self):
        """No longer needed - history is saved immediately. Kept for compatibility."""
        pass

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
