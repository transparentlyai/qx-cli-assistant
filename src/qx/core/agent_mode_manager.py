"""
Agent Mode Manager for toggling between multi-agent and single-agent modes.

This module provides functionality to switch between:
- Multi-agent mode: All agents are enabled and can work together
- Single-agent mode: Only the main agent is active, others are disabled
"""

import logging
from typing import Optional
from enum import Enum

logger = logging.getLogger(__name__)


class AgentMode(Enum):
    """Enumeration of available agent modes."""

    SINGLE = "single"
    MULTI = "multi"


class AgentModeManager:
    """Manages the agent mode state and transitions."""

    def __init__(self):
        self._mode = AgentMode.MULTI  # Default to multi-agent mode
        logger.debug("Agent mode manager initialized in MULTI mode")

    @property
    def mode(self) -> AgentMode:
        """Get the current agent mode."""
        return self._mode

    @property
    def is_multi(self) -> bool:
        """Check if currently in multi-agent mode."""
        return self._mode == AgentMode.MULTI

    @property
    def is_single(self) -> bool:
        """Check if currently in single-agent mode."""
        return self._mode == AgentMode.SINGLE

    def toggle(self) -> AgentMode:
        """Toggle between multi and single agent modes."""
        if self._mode == AgentMode.MULTI:
            self._mode = AgentMode.SINGLE
            logger.info("Switched to SINGLE agent mode")
        else:
            self._mode = AgentMode.MULTI
            logger.info("Switched to MULTI agent mode")
        return self._mode

    def set_mode(self, mode: AgentMode) -> None:
        """Set the agent mode explicitly."""
        self._mode = mode
        logger.info(f"Agent mode set to {mode.value.upper()}")

    def get_display_text(self) -> str:
        """Get the display text for the current mode."""
        return self._mode.value.upper()


# Global instance
_agent_mode_manager: Optional[AgentModeManager] = None


def get_agent_mode_manager() -> AgentModeManager:
    """Get the global agent mode manager instance."""
    global _agent_mode_manager
    if _agent_mode_manager is None:
        _agent_mode_manager = AgentModeManager()
    return _agent_mode_manager
