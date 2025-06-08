import subprocess
from pathlib import Path

from prompt_toolkit.completion import Completer, Completion


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

    def get_completions(self, document, complete_event):
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
