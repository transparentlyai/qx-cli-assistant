import subprocess
from pathlib import Path

from prompt_toolkit.completion import Completer, Completion

from qx.core.constants import MODELS


class QXCompleter(Completer):
    """Custom completer that handles both commands and path completion."""

    def __init__(self):
        self.commands = [
            "/model",
            "/reset",
            "/approve-all",
            "/help",
            "/print",
            "/tools",
        ]
        self.models = MODELS

    def get_completions(self, document, complete_event):
        text = document.text
        word_before_cursor = document.get_word_before_cursor(WORD=True)

        if text.startswith("/model "):
            for model in self.models:
                model_name = model["name"]
                if model_name.startswith(word_before_cursor):
                    yield Completion(
                        model_name,
                        start_position=-len(word_before_cursor),
                        display=model_name,
                        display_meta=model["description"],
                    )
            return

        # Get the current text and cursor position
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
