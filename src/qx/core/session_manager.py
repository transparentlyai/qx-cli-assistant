import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional, cast

from openai.types.chat import ChatCompletionMessageParam

from qx.core.paths import QX_SESSIONS_DIR

logger = logging.getLogger(__name__)

# Global variable to track current session filename
_current_session_file = None

def get_or_create_session_filename():
    """
    Returns the current session filename, creating a new one if needed.
    """
    global _current_session_file
    if _current_session_file is None:
        QX_SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        _current_session_file = QX_SESSIONS_DIR / f"qx_session_{timestamp}.json"
    return _current_session_file

def save_session(message_history: List[ChatCompletionMessageParam]):
    """
    Saves the given message history to the current session file.
    Creates a new session file only if one doesn't exist for this conversation.
    """
    if not message_history:
        logger.info("No message history to save. Skipping session save.")
        return

    session_filename = get_or_create_session_filename()

    # Convert ChatCompletionMessageParam objects to dictionaries for JSON serialization
    serializable_history = [
        msg.model_dump() if hasattr(msg, 'model_dump') else msg
        for msg in message_history
    ]

    try:
        with open(session_filename, "w", encoding="utf-8") as f:
            json.dump(serializable_history, f, indent=2)
        logger.info(f"Session saved to {session_filename}")
    except Exception as e:
        logger.error(f"Failed to save session to {session_filename}: {e}", exc_info=True)

def reset_session():
    """
    Resets the current session, forcing creation of a new session file on next save.
    """
    global _current_session_file
    _current_session_file = None

def clean_old_sessions(keep_sessions: int):
    """
    Deletes the oldest session files, ensuring only `keep_sessions` number of files remain.
    """
    if keep_sessions < 0:
        logger.warning(f"Invalid QX_KEEP_SESSIONS value: {keep_sessions}. Must be non-negative. Skipping session cleanup.")
        return

    try:
        session_files = sorted(
            [f for f in QX_SESSIONS_DIR.iterdir() if f.is_file() and f.name.startswith("qx_session_") and f.suffix == ".json"],
            key=lambda f: f.name,
        )

        if len(session_files) > keep_sessions:
            files_to_delete = session_files[: -(keep_sessions)]
            for file_path in files_to_delete:
                try:
                    file_path.unlink()
                    logger.info(f"Deleted old session file: {file_path}")
                except Exception as e:
                    logger.error(f"Failed to delete old session file {file_path}: {e}")
        else:
            logger.info(f"Number of sessions ({len(session_files)}) is within the limit ({keep_sessions}). No old sessions to delete.")
    except Exception as e:
        logger.error(f"Error during session cleanup: {e}", exc_info=True)

def load_latest_session() -> Optional[List[ChatCompletionMessageParam]]:
    """
    Loads the most recent session from the sessions directory.
    """
    try:
        session_files = sorted(
            [f for f in QX_SESSIONS_DIR.iterdir() if f.is_file() and f.name.startswith("qx_session_") and f.suffix == ".json"],
            key=lambda f: f.name,
            reverse=True,  # Get the most recent first
        )

        if not session_files:
            logger.info("No previous sessions found.")
            return None

        latest_session_file = session_files[0]
        return load_session_from_path(latest_session_file)

    except FileNotFoundError:
        logger.info("Session directory or file not found during load.")
        return None
    except Exception as e:
        logger.error(f"Error loading latest session: {e}", exc_info=True)
        return None

def load_session_from_path(session_path: Path) -> Optional[List[ChatCompletionMessageParam]]:
    """
    Loads a session from a specified JSON file path.
    """
    try:
        if not session_path.is_file():
            logger.error(f"Session file not found: {session_path}")
            return None

        with open(session_path, "r", encoding="utf-8") as f:
            raw_messages = json.load(f)

        message_history: List[ChatCompletionMessageParam] = cast(List[ChatCompletionMessageParam], raw_messages)
        logger.info(f"Loaded session from {session_path}")
        return message_history

    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode JSON from session file {session_path}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error loading session from {session_path}: {e}", exc_info=True)
        return None
