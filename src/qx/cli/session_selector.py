import json
import os
from pathlib import Path
from typing import Optional

import arrow
import inquirer
from inquirer.themes import GreenPassion

from qx.core.session_manager import get_session_files


def get_session_preview(session_file: Path) -> str:
    """
    Gets the first line of the last message from a session file.
    """
    try:
        with open(session_file, "r") as f:
            session_data = json.load(f)
            
            # Handle v2.0 format
            if isinstance(session_data, dict) and session_data.get("format_version") == "2.0":
                agents = session_data.get("agents", {})
                if not agents:
                    return "(empty session)"
                
                # Try to get messages from current agent or first available agent
                current_agent = session_data.get("current_agent")
                if current_agent and current_agent in agents:
                    messages = agents[current_agent]
                elif "qx" in agents:
                    messages = agents["qx"]
                else:
                    # Use first available agent
                    messages = list(agents.values())[0] if agents else []
                
                # Find last user message for preview
                for msg in reversed(messages):
                    if msg.get("role") == "user" and msg.get("content"):
                        first_line = msg["content"].split("\n")[0]
                        if len(first_line) > 80:
                            return first_line[:77] + "..."
                        return first_line
                return "(no user messages)"
            
            # Handle old format (backwards compatibility)
            elif isinstance(session_data, list) and session_data:
                last_message = session_data[-1]
                if "content" in last_message and last_message["content"]:
                    first_line = last_message["content"].split("\n")[0]
                    if len(first_line) > 80:
                        return first_line[:77] + "..."
                    return first_line
                    
    except (json.JSONDecodeError, IndexError, KeyError):
        return "(empty session)"
    return "(no message preview)"


def select_session() -> Optional[Path]:
    """
    Displays an interactive list of sessions for the user to choose from.
    """
    session_files = get_session_files()
    if not session_files:
        return None

    choices = []
    for session_file in session_files:
        last_modified = os.path.getmtime(session_file)
        time_ago = arrow.get(last_modified).humanize()
        preview = get_session_preview(session_file)
        choice_title = f"{time_ago} - {preview}"
        choices.append((choice_title, session_file))

    questions = [
        inquirer.List(
            "session",
            message="Choose a session to resume",
            choices=choices,
            carousel=True,
        ),
    ]

    answers = inquirer.prompt(questions, theme=GreenPassion())
    return answers.get("session") if answers else None
