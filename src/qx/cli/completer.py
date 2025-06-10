import subprocess
import logging
from pathlib import Path
from typing import List, Dict, Any

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
            "/agents",
        ]
        self.models = MODELS
        self.agent_subcommands = [
            {"name": "list", "description": "List all available agents"},
            {"name": "switch", "description": "Switch to a different agent"},
            {"name": "info", "description": "Show current agent information"},
            {"name": "reload", "description": "Reload agent configuration"},
            {"name": "refresh", "description": "Refresh agent discovery (find new project agents)"},
        ]
        self._cached_agents: List[Dict[str, Any]] = []
        self._cache_timestamp = 0
        self.logger = logging.getLogger(__name__)

    def _get_available_agents(self) -> List[Dict[str, str]]:
        """Get list of available agents with metadata and caching."""
        import time
        import yaml
        import os

        current_time = time.time()
        current_cwd = os.getcwd()

        # Cache for 10 seconds to avoid repeated filesystem access
        # Also refresh if working directory changed (for project agents)
        cache_expired = current_time - self._cache_timestamp > 10
        cwd_changed = getattr(self, '_last_cwd', None) != current_cwd
        
        if cache_expired or cwd_changed:
            try:
                # This is a synchronous version, so we'll use a simple approach
                from qx.core.agent_loader import AgentLoader

                loader = AgentLoader()

                # Get all agent files from all search paths with metadata
                agents_info = []
                agent_names_seen = set()

                # Use current working directory for project-aware discovery
                for search_path in loader.get_agent_search_paths(cwd=current_cwd):
                    if search_path.exists():
                        for agent_file in search_path.glob("*.agent.yaml"):
                            agent_name = agent_file.stem.replace(".agent", "")
                            if agent_name not in agent_names_seen:
                                agent_names_seen.add(agent_name)

                                # Try to read basic metadata
                                description = "Available agent"
                                mode = "interactive"
                                try:
                                    with open(agent_file, "r") as f:
                                        agent_data = yaml.safe_load(f)
                                        if agent_data:
                                            # Extract description from role field
                                            role = agent_data.get("role", "")
                                            if role:
                                                # Get first line of role as description
                                                description = role.split("\n")[
                                                    0
                                                ].strip()
                                                if len(description) > 50:
                                                    description = (
                                                        description[:47] + "..."
                                                    )

                                            # Get execution mode
                                            execution = agent_data.get("execution", {})
                                            mode = execution.get("mode", "interactive")
                                except Exception:
                                    # If we can't read metadata, just use defaults
                                    pass

                                # Mark project agents
                                is_project_agent = ".Q/agents" in str(search_path)
                                agent_info = {
                                    "name": agent_name,
                                    "description": description,
                                    "mode": mode,
                                }
                                if is_project_agent:
                                    agent_info["description"] = f"📁 {description}"  # Project folder emoji
                                
                                agents_info.append(agent_info)

                self._cached_agents = agents_info
                self._cache_timestamp = current_time
                self._last_cwd = current_cwd

            except Exception as e:
                self.logger.debug(f"Failed to load agents for completion: {e}")
                # Fallback to common agent names with basic info
                self._cached_agents = [
                    {
                        "name": "qx",
                        "description": "General-purpose software engineering agent",
                        "mode": "interactive",
                    },
                    {
                        "name": "code_reviewer",
                        "description": "Security-focused code analysis",
                        "mode": "interactive",
                    },
                    {
                        "name": "devops_automation",
                        "description": "Infrastructure automation specialist",
                        "mode": "interactive",
                    },
                    {
                        "name": "documentation_writer",
                        "description": "Technical writing specialist",
                        "mode": "interactive",
                    },
                    {
                        "name": "data_processor",
                        "description": "Data analysis and processing",
                        "mode": "interactive",
                    },
                ]

        return self._cached_agents

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

        # Agent command completion
        if text.startswith("/agents "):
            # Split the text after "/agents " to get the parts
            agent_text = text[8:]  # Remove "/agents " prefix
            parts = agent_text.split()

            if not parts or (len(parts) == 1 and not agent_text.endswith(" ")):
                # Complete subcommands
                for subcommand_info in self.agent_subcommands:
                    subcommand = subcommand_info["name"]
                    if subcommand.startswith(word_before_cursor):
                        yield Completion(
                            subcommand,
                            start_position=-len(word_before_cursor),
                            display=f"{subcommand}  [agent cmd]",
                            display_meta=subcommand_info["description"],
                        )
            elif len(parts) >= 1:
                # Complete agent names for 'switch' and 'reload' commands
                subcommand = parts[0]
                if subcommand in ["switch", "reload"]:
                    if len(parts) == 1 or (
                        len(parts) == 2 and not agent_text.endswith(" ")
                    ):
                        # Complete agent names with metadata
                        available_agents = self._get_available_agents()
                        for agent_info in available_agents:
                            agent_name = agent_info["name"]
                            if agent_name.startswith(word_before_cursor):
                                yield Completion(
                                    agent_name,
                                    start_position=-len(word_before_cursor),
                                    display=f"{agent_name}  [{agent_info['mode']}]",
                                    display_meta=agent_info["description"],
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
            command_descriptions = {
                "/model": "Show or update LLM model configuration",
                "/reset": "Reset session and clear message history",
                "/approve-all": "Activate 'approve all' mode for tool confirmations",
                "/help": "Show available commands and help",
                "/print": "Print text to the console",
                "/tools": "List active tools with descriptions",
                "/agents": "Manage agents (list, switch, info, reload)",
            }

            for command in self.commands:
                if command.startswith(current_word):
                    yield Completion(
                        command,
                        start_position=-len(current_word),
                        display=f"{command}  [cmd]",
                        display_meta=command_descriptions.get(command, "Command"),
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
