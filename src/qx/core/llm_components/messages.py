import logging
from typing import Any, Dict, List

from openai.types.chat import ChatCompletionMessageParam
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class MessageCache:
    """Handles efficient message serialization with caching."""

    def __init__(self):
        self._cache: Dict[int, Dict[str, Any]] = {}

    def serialize_messages_efficiently(
        self, messages: List[ChatCompletionMessageParam]
    ) -> List[Dict[str, Any]]:
        """
        Efficiently serialize messages to avoid repeated model_dump() calls.
        Converts BaseModel messages to dicts once and caches the result.
        """
        serialized: List[Dict[str, Any]] = []
        for msg in messages:
            if isinstance(msg, BaseModel):
                # Use object id as cache key
                msg_id = id(msg)
                if msg_id in self._cache:
                    # Use cached version
                    serialized.append(self._cache[msg_id])
                else:
                    # Convert BaseModel to dict and cache it
                    msg_dict = msg.model_dump()
                    self._cache[msg_id] = msg_dict
                    serialized.append(msg_dict)
                    # Limit cache size to prevent memory leaks
                    if len(self._cache) > 1000:
                        # Remove oldest entries (simple cleanup)
                        oldest_keys = list(self._cache.keys())[:500]
                        for key in oldest_keys:
                            del self._cache[key]
            else:
                # Already a dict, use as-is
                serialized.append(dict(msg) if hasattr(msg, "items") else msg)  # type: ignore
        return serialized

    def clear(self):
        """Clear the message cache to free memory."""
        self._cache.clear()


def get_message_role(msg) -> str:
    """
    Safely extracts the role from a message, whether it's a dict or Pydantic model.
    """
    if hasattr(msg, "get"):
        # Dict-like object
        return msg.get("role", "")
    elif hasattr(msg, "role"):
        # Pydantic model or object with role attribute
        return msg.role
    else:
        return ""


def has_system_message(messages: List[ChatCompletionMessageParam]) -> bool:
    """Check if the first message is a system message."""
    if not messages:
        return False
    return get_message_role(messages[0]) == "system"
