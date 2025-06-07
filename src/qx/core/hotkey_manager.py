"""
QX Hotkey Manager - Centralized hotkey handling for QX.

This service provides a centralized registry for hotkey actions.
Hotkeys are designed to work only during prompt input to avoid conflicts
with ongoing operations.
"""

import asyncio
import logging
import os
from typing import Callable, Dict, Optional

logger = logging.getLogger(__name__)


class QXHotkeyManager:
    """
    Manages hotkey action handlers for QX.
    
    This service provides centralized hotkey action handling.
    Hotkeys are active only during prompt input to prevent interference
    with ongoing operations.
    """
    
    def __init__(self):
        self._action_handlers: Dict[str, Callable] = {}
        self.running = False

    def register_action_handler(self, action: str, handler: Callable):
        """Register a handler function for a specific action."""
        self._action_handlers[action] = handler
        logger.debug(f"Registered handler for action: {action}")

    def start(self):
        """Start the hotkey manager (service layer only)."""
        if self.running:
            logger.debug("Hotkey manager already running")
            return True
            
        self.running = True
        logger.info("QX Hotkey Manager service started")
        return True

    def stop(self):
        """Stop the hotkey manager."""
        if not self.running:
            return
            
        self.running = False
        logger.info("QX Hotkey Manager service stopped")

    async def execute_action(self, action: str):
        """Execute a registered action handler."""
        if not self.running:
            logger.warning(f"Hotkey manager not running, ignoring action: {action}")
            return
            
        if action in self._action_handlers:
            try:
                handler = self._action_handlers[action]
                logger.debug(f"Executing action: {action}")
                
                # Handle both sync and async handlers
                if asyncio.iscoroutinefunction(handler):
                    await handler()
                else:
                    handler()
                    
            except Exception as e:
                logger.error(f"Error executing handler for action '{action}': {e}", exc_info=True)
        else:
            logger.warning(f"No handler registered for action: {action}")

    def execute_action_sync(self, action: str):
        """Execute a registered action handler synchronously."""
        if not self.running:
            logger.warning(f"Hotkey manager not running, ignoring action: {action}")
            return
            
        if action in self._action_handlers:
            try:
                handler = self._action_handlers[action]
                logger.debug(f"Executing action (sync): {action}")
                
                # Only handle sync handlers in sync execution
                if not asyncio.iscoroutinefunction(handler):
                    handler()
                else:
                    logger.warning(f"Cannot execute async handler '{action}' in sync context")
                    
            except Exception as e:
                logger.error(f"Error executing handler for action '{action}': {e}", exc_info=True)
        else:
            logger.warning(f"No handler registered for action: {action}")


# Global instance
_hotkey_manager_instance: Optional[QXHotkeyManager] = None


def get_hotkey_manager() -> QXHotkeyManager:
    """Get the global hotkey manager instance."""
    global _hotkey_manager_instance
    if _hotkey_manager_instance is None:
        _hotkey_manager_instance = QXHotkeyManager()
    return _hotkey_manager_instance


def start_hotkey_manager() -> bool:
    """Start the global hotkey manager."""
    manager = get_hotkey_manager()
    return manager.start()


def stop_hotkey_manager():
    """Stop the global hotkey manager."""
    global _hotkey_manager_instance
    if _hotkey_manager_instance is not None:
        _hotkey_manager_instance.stop()


def register_hotkey_handler(action: str, handler: Callable):
    """Register a handler for a specific hotkey action."""
    manager = get_hotkey_manager()
    manager.register_action_handler(action, handler)


# Default action handlers that mirror current prompt_toolkit functionality
def _default_cancel_handler():
    """Default handler for Ctrl+C - cancel current operation."""
    try:
        # Try to cancel the current asyncio task
        current_task = asyncio.current_task()
        if current_task:
            current_task.cancel()
            logger.info("Cancelled current operation via Ctrl+C")
        else:
            logger.debug("No current task to cancel")
    except Exception as e:
        logger.error(f"Error in cancel handler: {e}")


def _default_exit_handler():
    """Default handler for Ctrl+D - exit application."""
    try:
        logger.info("Exit requested via Ctrl+D")
        # Signal exit to the application
        # This should be handled by the main application loop
        os._exit(0)
    except Exception as e:
        logger.error(f"Error in exit handler: {e}")


def _default_history_handler():
    """Default handler for Ctrl+R - history search."""
    try:
        from qx.core.paths import QX_HISTORY_FILE
        from qx.core.history_utils import parse_history_for_fzf
        
        logger.info("History search requested via Ctrl+R")
        
        # This is more complex as it needs to interact with the current prompt
        # For now, we'll just log it - the actual implementation would need
        # to coordinate with the active prompt session
        logger.debug("History search not yet implemented in hotkey manager")
        
    except Exception as e:
        logger.error(f"Error in history handler: {e}")


async def _default_approve_all_handler():
    """Default handler for Ctrl+A - toggle approve all mode."""
    try:
        import qx.core.user_prompts as user_prompts
        from qx.cli.console import themed_console
        
        async with user_prompts._approve_all_lock:
            user_prompts._approve_all_active = not user_prompts._approve_all_active
            status = "activated" if user_prompts._approve_all_active else "deactivated"
            style = "success" if user_prompts._approve_all_active else "warning"
            
            themed_console.print(f"✓ 'Approve All' mode {status}.", style=style)
            logger.info(f"Approve All mode {status} via Ctrl+A")
            
    except Exception as e:
        logger.error(f"Error in approve all handler: {e}")


async def _default_toggle_thinking_handler():
    """Default handler for Ctrl+T - toggle show thinking mode."""
    try:
        from qx.core.state_manager import show_thinking_manager
        from qx.core.config_manager import ConfigManager
        from qx.cli.console import themed_console
        
        new_status = not await show_thinking_manager.is_active()
        await show_thinking_manager.set_status(new_status)
        
        # Update config
        config_manager = ConfigManager(themed_console, None)
        config_manager.set_config_value("QX_SHOW_THINKING", str(new_status).lower())
        
        status_text = "enabled" if new_status else "disabled"
        themed_console.print(f"✓ [dim green]Show Thinking:[/] {status_text}.", style="warning")
        logger.info(f"Show Thinking {status_text} via Ctrl+T")
        
    except Exception as e:
        logger.error(f"Error in toggle thinking handler: {e}")


async def _default_toggle_stdout_handler():
    """Default handler for Ctrl+S - toggle stdout visibility."""
    try:
        from qx.core.output_control import output_control_manager
        from qx.cli.console import themed_console
        
        # Get current status and toggle it
        current_status = await output_control_manager.should_show_stdout()
        new_status = not current_status
        await output_control_manager.set_stdout_visibility(new_status)
        
        status_text = "enabled" if new_status else "disabled"
        themed_console.print(f"✓ [dim green]Show Stdout:[/] {status_text}.", style="warning")
        logger.info(f"Show Stdout {status_text} via Ctrl+S")
        
    except Exception as e:
        logger.error(f"Error in toggle stdout handler: {e}")


def register_default_handlers():
    """Register all default hotkey handlers."""
    register_hotkey_handler('cancel', _default_cancel_handler)
    register_hotkey_handler('exit', _default_exit_handler)
    register_hotkey_handler('history', _default_history_handler)
    register_hotkey_handler('approve_all', _default_approve_all_handler)
    register_hotkey_handler('toggle_thinking', _default_toggle_thinking_handler)
    register_hotkey_handler('toggle_stdout', _default_toggle_stdout_handler)
    logger.debug("Default hotkey handlers registered")


def initialize_hotkey_system():
    """Initialize the hotkey system with default handlers."""
    register_default_handlers()
    return start_hotkey_manager()