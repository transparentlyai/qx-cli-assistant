from typing import Iterable

from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.document import Document

# Define a list of example commands QX might support
# In a real application, this list would be more dynamic or comprehensive
DEFAULT_COMMANDS = [
    "/save-last-response",
    "/model", # Added new /model command
]


class CommandCompleter(Completer):
    def __init__(self, commands: list = None):
        self.commands = commands if commands is not None else DEFAULT_COMMANDS

    def get_completions(
        self, document: Document, complete_event
    ) -> Iterable[Completion]:
        text_before_cursor = document.text_before_cursor
        word_before_cursor = document.get_word_before_cursor(WORD=True)

        # Only offer command completions if the input starts with /
        # or if the line is empty (to show initial commands like /help)
        # and there's no space in the text_before_cursor (meaning we are completing the command itself)
        if text_before_cursor.startswith("/") and " " not in text_before_cursor:
            for cmd in self.commands:
                if cmd.startswith(word_before_cursor):
                    yield Completion(
                        cmd,
                        start_position=-len(word_before_cursor),
                        display=cmd,
                        display_meta="command",
                    )
        elif not text_before_cursor.strip():  # If the line is empty or just whitespace
            for cmd in self.commands:
                if cmd.startswith("/"):  # Only suggest commands that start with /
                    yield Completion(
                        cmd, start_position=0, display=cmd, display_meta="command"
                    )
