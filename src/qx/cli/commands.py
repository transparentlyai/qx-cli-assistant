from typing import Iterable, List, Optional, Any

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


class MCPServerNameCompleter:
    def __init__(self, mcp_manager: Optional[Any] = None):
        self.mcp_manager = mcp_manager

    def get_completions(self, text_before_cursor: str) -> List[str]:
        """Get MCP server name completions."""
        if not self.mcp_manager:
            return []

        words = text_before_cursor.split()
        
        if len(words) > 1 and (words[0] == "/mcp-connect" or words[0] == "/mcp-disconnect"):
            current_word = words[-1]
            available_servers = self.mcp_manager.get_available_server_names()
            
            return [
                server_name for server_name in available_servers
                if server_name.startswith(current_word)
            ]
        return []


class CommandCompleter:
    def __init__(self, commands: list = None, mcp_manager: Optional[Any] = None):
        self.commands = commands if commands is not None else DEFAULT_COMMANDS
        self.mcp_server_name_completer = MCPServerNameCompleter(mcp_manager)

    def get_completions(self, text_before_cursor: str) -> List[str]:
        """Get command completions."""
        # Check if we are completing a command argument (like server name for /mcp-connect)
        if text_before_cursor.startswith(tuple([cmd + " " for cmd in ["/mcp-connect", "/mcp-disconnect"]])):
            return self.mcp_server_name_completer.get_completions(text_before_cursor)

        # Only offer command completions if the input starts with /
        if text_before_cursor.startswith("/") and " " not in text_before_cursor:
            return [cmd for cmd in self.commands if cmd.startswith(text_before_cursor)]
        elif not text_before_cursor.strip():  # If the line is empty or just whitespace
            return [cmd for cmd in self.commands if cmd.startswith("/")]
        
        return []