"""
Output control service for QX plugins.

This module provides a standalone service that plugins can use to determine
whether they should display verbose output (like stdout, stderr, debug info, etc.).
The service integrates with the thinking mechanism while keeping plugins independent.
"""

import asyncio
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)


class OutputControlManager:
    """
    Manages output verbosity settings for plugins.
    
    This service allows plugins to check whether they should display verbose output
    like stdout from shell commands, debug information, etc. It integrates with
    the thinking mechanism but remains standalone so plugins don't have tight coupling.
    """
    
    _instance = None
    _lock = asyncio.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(OutputControlManager, cls).__new__(cls)
            cls._instance._show_stdout_override = None
            cls._instance._show_stderr_override = None
        return cls._instance

    async def should_show_stdout(self) -> bool:
        """
        Determine if stdout should be displayed for tool executions.
        
        Returns:
            bool: True if stdout should be shown, False otherwise
        """
        async with self._lock:
            # If an override is set, use it
            if self._show_stdout_override is not None:
                return self._show_stdout_override
            
            # Check for specific stdout environment variable first
            stdout_setting = os.getenv("QX_SHOW_STDOUT")
            if stdout_setting is not None:
                return stdout_setting.lower() == "true"
            
            # Fall back to thinking mechanism
            try:
                from qx.core.user_prompts import is_show_thinking_active
                return await is_show_thinking_active()
            except ImportError:
                # If thinking module isn't available, default to showing stdout
                logger.warning("Thinking module not available, defaulting to show stdout")
                return True

    async def should_show_stderr(self) -> bool:
        """
        Determine if stderr should be displayed for tool executions.
        
        stderr is generally always shown for debugging purposes, but this
        provides a way to control it if needed.
        
        Returns:
            bool: True if stderr should be shown, False otherwise
        """
        async with self._lock:
            # If an override is set, use it
            if self._show_stderr_override is not None:
                return self._show_stderr_override
            
            # Check for specific stderr environment variable
            stderr_setting = os.getenv("QX_SHOW_STDERR")
            if stderr_setting is not None:
                return stderr_setting.lower() == "true"
            
            # Default to always showing stderr for debugging
            return True

    async def set_stdout_visibility(self, visible: bool):
        """
        Override stdout visibility setting.
        
        Args:
            visible: Whether stdout should be visible
        """
        async with self._lock:
            self._show_stdout_override = visible
            os.environ["QX_SHOW_STDOUT"] = str(visible).lower()

    async def set_stderr_visibility(self, visible: bool):
        """
        Override stderr visibility setting.
        
        Args:
            visible: Whether stderr should be visible
        """
        async with self._lock:
            self._show_stderr_override = visible
            os.environ["QX_SHOW_STDERR"] = str(visible).lower()

    async def reset_overrides(self):
        """Reset all output control overrides to use default behavior."""
        async with self._lock:
            self._show_stdout_override = None
            self._show_stderr_override = None
            # Remove environment overrides
            if "QX_SHOW_STDOUT" in os.environ:
                del os.environ["QX_SHOW_STDOUT"]
            if "QX_SHOW_STDERR" in os.environ:
                del os.environ["QX_SHOW_STDERR"]


# Global instance for easy access by plugins
output_control_manager = OutputControlManager()


# Convenience functions for plugins to use
async def should_show_stdout() -> bool:
    """
    Convenience function for plugins to check if stdout should be displayed.
    
    This function can be imported directly by plugins without needing to 
    import the manager class.
    
    Returns:
        bool: True if stdout should be shown, False otherwise
    """
    return await output_control_manager.should_show_stdout()


async def should_show_stderr() -> bool:
    """
    Convenience function for plugins to check if stderr should be displayed.
    
    Returns:
        bool: True if stderr should be shown, False otherwise
    """
    return await output_control_manager.should_show_stderr()


def should_show_stdout_sync() -> bool:
    """
    Synchronous version of should_show_stdout for plugins that can't use async.
    
    This is a fallback for plugins that need immediate output decisions.
    It checks environment variables and defaults to showing stdout.
    
    Returns:
        bool: True if stdout should be shown, False otherwise
    """
    # Check specific stdout setting first
    stdout_setting = os.getenv("QX_SHOW_STDOUT")
    if stdout_setting is not None:
        return stdout_setting.lower() == "true"
    
    # Fall back to thinking setting
    thinking_setting = os.getenv("QX_SHOW_THINKING", "true")
    return thinking_setting.lower() == "true"


def should_show_stderr_sync() -> bool:
    """
    Synchronous version of should_show_stderr for plugins that can't use async.
    
    Returns:
        bool: True if stderr should be shown, False otherwise
    """
    stderr_setting = os.getenv("QX_SHOW_STDERR", "true")
    return stderr_setting.lower() == "true"