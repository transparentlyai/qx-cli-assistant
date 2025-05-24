from typing import Iterable, List, Optional, Any

from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.document import Document

# Define a list of example commands QX might support
# In a real application, this list would be more dynamic or comprehensive
DEFAULT_COMMANDS = [
    "/save-last-response",
    "/model",
    "/reset",
    "/compress-context",
    "/save-session",
    "/mcp-connect",
    "/mcp-disconnect",
    "/mcp-tools",
]


class MCPServerNameCompleter(Completer):
    def __init__(self, mcp_manager: Optional[Any] = None):
        self.mcp_manager = mcp_manager

    def get_completions(
        self, document: Document, complete_event
    ) -> Iterable[Completion]:
        if not self.mcp_manager:
            return

        text_before_cursor = document.text_before_cursor.lstrip()
        words = text_before_cursor.split()

        # Only provide completions if we are after the command (e.g., /mcp-connect <server_name>)
        if len(words) > 1 and (words[0] == "/mcp-connect" or words[0] == "/mcp-disconnect"):
            current_word = words[-1]
            available_servers = self.mcp_manager.get_available_server_names()

            for server_name in available_servers:
                if server_name.startswith(current_word):
                    yield Completion(
                        server_name,
                        start_position=-len(current_word),
                        display=server_name,
                        display_meta="MCP Server",
                    )


class CommandCompleter(Completer):
    def __init__(self, commands: list = None, mcp_manager: Optional[Any] = None):
        self.commands = commands if commands is not None else DEFAULT_COMMANDS
        self.mcp_server_name_completer = MCPServerNameCompleter(mcp_manager)

    def get_completions(
        self, document: Document, complete_event
    ) -> Iterable[Completion]:
        text_before_cursor = document.text_before_cursor
        word_before_cursor = document.get_word_before_cursor(WORD=True)

        # Check if we are completing a command argument (like server name for /mcp-connect)
        if text_before_cursor.startswith(tuple([cmd + " " for cmd in ["/mcp-connect", "/mcp-disconnect"]])):
            yield from self.mcp_server_name_completer.get_completions(document, complete_event)
            return

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
