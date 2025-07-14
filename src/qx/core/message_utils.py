"""
Common utilities for message conversion between QX and LangChain formats.

This module provides shared functions for converting messages between
different formats used in the system.
"""

import logging
from typing import List, Dict, Any
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage

logger = logging.getLogger(__name__)


def qx_to_langchain_messages(
    qx_messages: List[Dict[str, Any]],
    include_system: bool = True,
    system_prompt: str = "",
) -> List[BaseMessage]:
    """
    Convert QX message format to LangChain messages.

    Args:
        qx_messages: List of QX format messages with 'role' and 'content'
        include_system: Whether to include a system message
        system_prompt: System prompt to include if include_system is True

    Returns:
        List of LangChain BaseMessage objects
    """
    langchain_messages = []

    # Add system message if requested
    if include_system and system_prompt:
        langchain_messages.append(SystemMessage(content=system_prompt))

    # Convert each message
    for msg in qx_messages:
        role = msg.get("role", "")
        content = msg.get("content", "")

        if role == "user":
            langchain_messages.append(HumanMessage(content=content))
        elif role == "assistant":
            langchain_messages.append(AIMessage(content=content))
        elif role == "system":
            langchain_messages.append(SystemMessage(content=content))
        else:
            logger.warning(f"Unknown message role: {role}")

    return langchain_messages


def langchain_to_qx_messages(
    langchain_messages: List[BaseMessage],
) -> List[Dict[str, Any]]:
    """
    Convert LangChain messages to QX message format.

    Args:
        langchain_messages: List of LangChain BaseMessage objects

    Returns:
        List of QX format messages with 'role' and 'content'
    """
    qx_messages = []

    for msg in langchain_messages:
        if isinstance(msg, HumanMessage):
            qx_messages.append({"role": "user", "content": msg.content})
        elif isinstance(msg, AIMessage):
            qx_messages.append({"role": "assistant", "content": msg.content})
        elif isinstance(msg, SystemMessage):
            qx_messages.append({"role": "system", "content": msg.content})
        else:
            logger.warning(f"Unknown message type: {type(msg)}")

    return qx_messages


def extract_last_user_input(messages: List[Dict[str, Any]]) -> str:
    """
    Extract the last user input from a list of messages.

    Args:
        messages: List of messages in QX format

    Returns:
        The content of the last user message, or empty string if none found
    """
    for msg in reversed(messages):
        if msg.get("role") == "user":
            return msg.get("content", "")
    return ""


def prepare_messages_for_model(
    messages: List[BaseMessage],
    system_prompt: str = "",
    skip_system_messages: bool = False,
) -> List[BaseMessage]:
    """
    Prepare messages for model invocation with optional system prompt handling.

    Args:
        messages: List of LangChain messages
        system_prompt: System prompt to prepend
        skip_system_messages: Whether to skip existing system messages

    Returns:
        Prepared list of messages
    """
    prepared_messages = []

    # Add system prompt if provided
    if system_prompt:
        prepared_messages.append(SystemMessage(content=system_prompt))

    # Process existing messages
    for msg in messages:
        if isinstance(msg, SystemMessage) and skip_system_messages:
            continue
        prepared_messages.append(msg)

    return prepared_messages
