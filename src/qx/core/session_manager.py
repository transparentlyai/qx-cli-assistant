import asyncio
import json
import logging
import threading
from datetime import datetime
from pathlib import Path
from typing import List, Optional, cast, Any

from openai.types.chat import ChatCompletionMessageParam

from qx.core.paths import QX_SESSIONS_DIR

logger = logging.getLogger(__name__)

# Global variable to track current session filename
_current_session_file = None
_session_lock = asyncio.Lock()  # Protect session file access in async context
_session_lock_sync = threading.Lock()  # Protect session file access in sync context


def get_session_files() -> List[Path]:
    """
    Returns a list of all session files, sorted by modification time (newest first).
    """
    if not QX_SESSIONS_DIR.is_dir():
        return []

    session_files = [
        f
        for f in QX_SESSIONS_DIR.iterdir()
        if f.is_file() and f.name.startswith("qx_session_") and f.suffix == ".json"
    ]

    # Sort by modification time, newest first
    session_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)

    return session_files


def _get_message_role(msg) -> Optional[str]:
    """
    Safely extracts the role from a message, whether it's a dict or Pydantic model.
    """
    if hasattr(msg, "get"):
        # Dict-like object
        return msg.get("role")
    elif hasattr(msg, "role"):
        # Pydantic model or object with role attribute
        return msg.role
    else:
        return None


def _add_system_message_if_missing(
    message_history: List[ChatCompletionMessageParam],
    agent_config: Optional[Any] = None
) -> List[ChatCompletionMessageParam]:
    """
    Adds the system message as the first message if it's not already present.
    
    Args:
        message_history: List of messages
        agent_config: Optional agent configuration for loading system prompt
    """
    # Check if the first message is already a system message
    if message_history and _get_message_role(message_history[0]) == "system":
        return message_history

    # System message will be added dynamically when needed
    # For now, just return the history as-is since we don't have agent config
    return message_history


async def get_or_create_session_filename():
    """
    Returns the current session filename, creating a new one if needed.
    Thread-safe version using asyncio lock.
    """
    global _current_session_file
    async with _session_lock:
        if _current_session_file is None:
            # Only create the sessions directory if the .Q directory exists
            if not QX_SESSIONS_DIR.parent.is_dir():
                logger.info(
                    "'.Q' directory not found. Cannot create session directory."
                )
                return None  # Indicate that a session file cannot be created
            QX_SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[
                :23
            ]  # Include microseconds
            _current_session_file = QX_SESSIONS_DIR / f"qx_session_{timestamp}.json"
    return _current_session_file


async def save_session_async(current_agent_name: str,
                           all_agent_histories: dict):
    """
    Saves all agent message histories to the current session file.
    Creates a new session file only if one doesn't exist for this conversation.
    Thread-safe async version.
    
    Args:
        current_agent_name: Name of the current agent
        all_agent_histories: Dict of all agent histories {agent_name: history}
    """
    # Check if .Q directory exists before attempting to save
    if not QX_SESSIONS_DIR.parent.is_dir():
        logger.info("'.Q' directory not found. Skipping session save.")
        return

    if not all_agent_histories:
        logger.info("No agent histories to save. Skipping session save.")
        return

    session_filename = await get_or_create_session_filename()
    if session_filename is None:
        return

    # Prepare session data
    session_data = {
        "format_version": "2.0",
        "current_agent": current_agent_name,
        "agents": {}
    }
    
    for agent_name, history in all_agent_histories.items():
        # Exclude system messages and serialize
        agent_history = [
            msg for msg in history if _get_message_role(msg) != "system"
        ]
        serializable_history = []
        for msg in agent_history:
            if hasattr(msg, "model_dump") and callable(getattr(msg, "model_dump")):
                serializable_history.append(msg.model_dump())  # type: ignore
            elif hasattr(msg, "__dict__"):
                serializable_history.append(msg.__dict__)
            elif hasattr(msg, "items"):
                serializable_history.append(dict(msg))
            else:
                serializable_history.append(msg)
        session_data["agents"][agent_name] = serializable_history

    try:
        # Use asyncio.to_thread for file I/O to avoid blocking
        await asyncio.to_thread(
            lambda: session_filename.write_text(
                json.dumps(session_data, indent=2), encoding="utf-8"
            )
        )
        logger.info(f"Session saved to {session_filename}")
    except Exception as e:
        logger.error(
            f"Failed to save session to {session_filename}: {e}", exc_info=True
        )


async def reset_session_async():
    """
    Resets the current session, forcing creation of a new session file on next save.
    Thread-safe async version.
    """
    global _current_session_file
    async with _session_lock:
        _current_session_file = None


# Sync wrappers for backward compatibility
def save_session_sync(current_agent_name: str,
                     all_agent_histories: dict):
    """Sync wrapper for save_session."""
    
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # We're in an async context, create a task
            asyncio.create_task(save_session_async(current_agent_name, all_agent_histories))
        else:
            # Sync context - run async version
            loop.run_until_complete(save_session_async(current_agent_name, all_agent_histories))
    except RuntimeError:
        # No event loop - shouldn't happen in normal qx usage
        logger.error("No event loop available for session saving")


def reset_session_sync():
    """Sync wrapper for reset_session."""
    global _current_session_file
    with _session_lock_sync:
        _current_session_file = None


def set_current_session_file(session_path: Path):
    """
    Sets the current session file to an existing file.
    Used when recovering a session to ensure continued use of the same file.
    """
    global _current_session_file
    with _session_lock_sync:
        _current_session_file = session_path


# Keep sync versions for compatibility
save_session = save_session_sync
reset_session = reset_session_sync


async def clean_old_sessions_async(keep_sessions: int):
    """
    Deletes the oldest session files, ensuring only `keep_sessions` number of files remain.
    Async version.
    """
    if keep_sessions < 0:
        logger.warning(
            f"Invalid QX_KEEP_SESSIONS value: {keep_sessions}. Must be non-negative. Skipping session cleanup."
        )
        return

    # Only attempt cleanup if .Q directory exists
    if not QX_SESSIONS_DIR.parent.is_dir():
        logger.info("'.Q' directory not found. Skipping session cleanup.")
        return

    try:
        # Run file operations in thread pool
        def _get_files():
            return get_session_files()

        session_files = await asyncio.to_thread(_get_files)

        if len(session_files) > keep_sessions:
            files_to_delete = session_files[keep_sessions:]
            for file_path in files_to_delete:
                try:
                    await asyncio.to_thread(file_path.unlink)
                    logger.info(f"Deleted old session file: {file_path}")
                except Exception as e:
                    logger.error(f"Failed to delete old session file {file_path}: {e}")
        else:
            logger.info(
                f"Number of sessions ({len(session_files)}) is within the limit ({keep_sessions}). No old sessions to delete."
            )
    except Exception as e:
        logger.error(f"Error during session cleanup: {e}", exc_info=True)


def clean_old_sessions(keep_sessions: int):
    """
    Sync wrapper for clean_old_sessions.
    """
    clean_old_sessions_async_ = clean_old_sessions_async(keep_sessions)
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.create_task(clean_old_sessions_async_)
        else:
            loop.run_until_complete(clean_old_sessions_async_)
    except RuntimeError:
        asyncio.run(clean_old_sessions_async_)


def load_latest_session() -> Optional[List[ChatCompletionMessageParam]]:
    """
    Loads the most recent session from the sessions directory.
    """
    if not QX_SESSIONS_DIR.parent.is_dir():
        logger.info("'.Q' directory not found. Skipping session load.")
        return None

    session_files = get_session_files()

    if not session_files:
        logger.info("No previous sessions found.")
        return None

    latest_session_file = session_files[0]
    loaded_history = load_session_from_path(latest_session_file)
    if loaded_history:
        set_current_session_file(latest_session_file)
    return loaded_history


def load_all_agent_histories_from_session(
    session_path: Path
) -> Optional[dict]:
    """
    Loads all agent histories from a session file (new format only).
    
    Returns:
        Dict mapping agent names to their message histories, or None if not new format
    """
    try:
        if not session_path.is_file():
            logger.error(f"Session file not found: {session_path}")
            return None

        with open(session_path, "r", encoding="utf-8") as f:
            session_data = json.load(f)

        # Check if this is the new format
        if isinstance(session_data, dict) and session_data.get("format_version") == "2.0":
            agents = session_data.get("agents", {})
            
            # Add each agent's history without system message (will be added dynamically)
            all_histories = {}
            for agent_name, history in agents.items():
                message_history = cast(List[ChatCompletionMessageParam], history)
                message_history = _add_system_message_if_missing(message_history)
                all_histories[agent_name] = message_history
            
            return all_histories
        else:
            # Old format doesn't support multiple agents
            return None

    except Exception as e:
        logger.error(f"Error loading all agent histories from {session_path}: {e}", exc_info=True)
        return None


def load_session_from_path(
    session_path: Path,
    agent_name: Optional[str] = None
) -> Optional[List[ChatCompletionMessageParam]]:
    """
    Loads a specific agent's history from a session file.
    
    Args:
        session_path: Path to session file
        agent_name: Specific agent to load history for
        
    Returns:
        Message history for the specified agent or current/default agent
    """
    try:
        if not session_path.is_file():
            logger.error(f"Session file not found: {session_path}")
            return None

        with open(session_path, "r", encoding="utf-8") as f:
            session_data = json.load(f)

        # Validate format
        if not isinstance(session_data, dict) or session_data.get("format_version") != "2.0":
            logger.error(f"Invalid or old session format in {session_path}")
            return None

        agents = session_data.get("agents", {})
        if not agents:
            logger.warning("No agent histories found in session file")
            return None
        
        # Determine which agent to load
        if agent_name and agent_name in agents:
            raw_messages = agents[agent_name]
        elif session_data.get("current_agent") in agents:
            agent_name = session_data["current_agent"]
            raw_messages = agents[agent_name]
        elif "qx" in agents:
            agent_name = "qx"
            raw_messages = agents["qx"]
        else:
            # Use first available agent
            agent_name = list(agents.keys())[0]
            raw_messages = agents[agent_name]
        
        message_history = cast(List[ChatCompletionMessageParam], raw_messages)
        message_history = _add_system_message_if_missing(message_history)
        
        logger.info(f"Loaded session for agent '{agent_name}' from {session_path}")
        set_current_session_file(session_path)
        
        return message_history

    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode JSON from session file {session_path}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error loading session from {session_path}: {e}", exc_info=True)
        return None
