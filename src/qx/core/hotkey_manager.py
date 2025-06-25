"""
QX Hotkey Manager - Centralized hotkey handling for QX.

This service provides a centralized registry for hotkey actions.
Hotkeys are designed to work only during prompt input to avoid conflicts
with ongoing operations.
"""

import asyncio
import logging
import os
import signal
from typing import Callable, Dict, Optional

from .global_hotkeys import GlobalHotkeys

logger = logging.getLogger(__name__)


class QXHotkeyManager:
    """
    Manages hotkey action handlers for QX.

    This service provides centralized hotkey action handling with global
    hotkey capture that works at any time, not just during prompt input.
    """

    def __init__(self):
        self._action_handlers: Dict[str, Callable] = {}
        self._global_hotkeys = GlobalHotkeys()
        self._hotkey_mappings: Dict[str, str] = {}
        self.running = False

    def register_action_handler(self, action: str, handler: Callable):
        """Register a handler function for a specific action."""
        self._action_handlers[action] = handler
        logger.debug(f"Registered handler for action: {action}")

    def register_global_hotkey(self, key_combination: str, action: str):
        """Register a global hotkey that maps to an action."""
        if action not in self._action_handlers:
            logger.warning(
                f"No handler registered for action '{action}' when mapping hotkey '{key_combination}'"
            )
            return

        # Create a callback that executes the action
        def hotkey_callback():
            logger.info(
                f"Global hotkey '{key_combination}' pressed, executing action '{action}'"
            )
            self.execute_action_sync(action)

        self._global_hotkeys.register_hotkey(key_combination, hotkey_callback)
        self._hotkey_mappings[key_combination] = action
        logger.debug(
            f"Registered global hotkey '{key_combination}' -> action '{action}'"
        )

    def unregister_global_hotkey(self, key_combination: str):
        """Unregister a global hotkey."""
        self._global_hotkeys.unregister_hotkey(key_combination)
        if key_combination in self._hotkey_mappings:
            del self._hotkey_mappings[key_combination]
        logger.debug(f"Unregistered global hotkey: {key_combination}")

    def start(self):
        """Start the hotkey manager with global hotkey capture."""
        if self.running:
            logger.debug("Hotkey manager already running")
            return True

        try:
            # Start global hotkey capture
            self._global_hotkeys.start()
            self.running = True
            logger.info("QX Hotkey Manager with global capture started")
            return True
        except Exception as e:
            logger.warning(f"Failed to start global hotkey capture: {e}")
            logger.info(
                "QX will continue without global hotkeys (prompt_toolkit hotkeys will still work)"
            )
            self.running = True
            return True

    def stop(self):
        """Stop the hotkey manager."""
        if not self.running:
            return

        # Stop global hotkey capture
        self._global_hotkeys.stop()
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
                logger.error(
                    f"Error executing handler for action '{action}': {e}", exc_info=True
                )
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

                # Handle both sync and async handlers - for async, create a task
                if asyncio.iscoroutinefunction(handler):
                    try:
                        # Try to get the current event loop and schedule the coroutine
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            asyncio.create_task(handler())
                            logger.debug(
                                f"Scheduled async handler for action: {action}"
                            )
                        else:
                            logger.warning(
                                f"Event loop not running for async action: {action}"
                            )
                    except RuntimeError:
                        # No event loop, try to run directly
                        logger.warning(
                            f"No event loop available for async action: {action}"
                        )
                        asyncio.run(handler())
                else:
                    handler()
                    logger.debug(f"Executed sync handler for action: {action}")

            except Exception as e:
                logger.error(
                    f"Error executing handler for action '{action}': {e}", exc_info=True
                )
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


def register_global_hotkey(key_combination: str, action: str):
    """Register a global hotkey that maps to an action."""
    manager = get_hotkey_manager()
    manager.register_global_hotkey(key_combination, action)


# Default action handlers that mirror current prompt_toolkit functionality
def _default_cancel_handler():
    """Default handler for Ctrl+C - cancel current operation."""
    try:
        # This will be caught by the main application loop
        os.kill(os.getpid(), signal.SIGINT)
        logger.info("Sent SIGINT for Ctrl+C")
    except Exception as e:
        logger.error(f"Error in cancel handler: {e}")


def _default_exit_handler():
    """Default handler for Ctrl+D - exit application."""
    try:
        logger.info("Exit requested via Ctrl+D")
        # Raise EOFError which will be caught by the main loop
        raise EOFError("Ctrl+D pressed")
    except Exception as e:
        logger.error(f"Error in exit handler: {e}")


def _default_history_handler():
    """Default handler for Ctrl+R - history search."""
    try:
        from qx.cli.console import themed_console

        logger.info("History search requested via global hotkey")

        # During LLM operations, just show a message that history search is available during input
        themed_console.print(
            "✓ [dim green]History Search:[/] Available during prompt input (Ctrl+R).",
            style="warning",
        )

    except Exception as e:
        logger.error(f"Error in history handler: {e}")


def _default_approve_all_handler():
    """Default handler for Ctrl+A - toggle approve all mode."""
    try:
        import qx.core.user_prompts as user_prompts

        # Simple toggle without any external dependencies or Rich formatting
        user_prompts._approve_all_active = not user_prompts._approve_all_active
        status = "activated" if user_prompts._approve_all_active else "deactivated"
        
        # Use managed stream print with newline to avoid spinner overlap
        try:
            from qx.core.llm_components.streaming import _managed_stream_print
            _managed_stream_print(
                f"\n✓ [dim green]Approve All mode[/] {status}.", 
                use_manager=True, 
                style="warning"
            )
        except Exception:
            # Fallback to plain print if managed print not available
            print(f"\n✓ Approve All mode {status}")
        logger.info(f"Approve All mode {status} via global hotkey")

    except Exception as e:
        logger.error(f"Error in approve all handler: {e}")


def _default_toggle_details_handler():
    """Default handler for Ctrl+T - toggle details mode."""
    try:
        from qx.core.state_manager import details_manager
        import asyncio

        async def toggle_details():
            new_status = not await details_manager.is_active()
            await details_manager.set_status(new_status)

            # Update toolbar state if available
            try:
                from qx.cli.qprompt import _details_active_for_toolbar
                _details_active_for_toolbar[0] = new_status
            except ImportError:
                pass  # Module not imported yet

            status_text = "enabled" if new_status else "disabled"
            try:
                from qx.core.llm_components.streaming import _managed_stream_print
                _managed_stream_print(
                    f"\n✓ [dim green]Details:[/] {status_text}.", 
                    use_manager=True, 
                    style="warning"
                )
            except Exception:
                print(f"\n✓ Details: {status_text}")
            logger.info(f"Details {status_text} via global hotkey")

        asyncio.run(toggle_details())

    except Exception as e:
        logger.error(f"Error in toggle details handler: {e}")


def _default_toggle_stdout_handler():
    """Default handler for Ctrl+O - toggle stdout visibility."""
    try:
        from qx.core.output_control import output_control_manager
        import asyncio

        async def toggle_stdout():
            current_status = await output_control_manager.should_show_stdout()
            new_status = not current_status
            await output_control_manager.set_stdout_visibility(new_status)

            # Update toolbar state if available
            try:
                from qx.cli.qprompt import _stdout_active_for_toolbar
                _stdout_active_for_toolbar[0] = new_status
            except ImportError:
                pass  # Module not imported yet

            status_text = "enabled" if new_status else "disabled"
            try:
                from qx.core.llm_components.streaming import _managed_stream_print
                _managed_stream_print(
                    f"\n✓ [dim green]Show Stdout:[/] {status_text}.", 
                    use_manager=True, 
                    style="warning"
                )
            except Exception:
                print(f"\n✓ Show Stdout: {status_text}")
            logger.info(f"Show Stdout {status_text} via Ctrl+O")

        asyncio.run(toggle_stdout())

    except Exception as e:
        logger.error(f"Error in toggle stdout handler: {e}")


def register_default_handlers():
    """Register all default hotkey handlers."""
    register_hotkey_handler("cancel", _default_cancel_handler)
    register_hotkey_handler("exit", _default_exit_handler)
    register_hotkey_handler("history", _default_history_handler)
    register_hotkey_handler("approve_all", _default_approve_all_handler)
    register_hotkey_handler("toggle_details", _default_toggle_details_handler)
    register_hotkey_handler("toggle_stdout", _default_toggle_stdout_handler)
    logger.debug("Default hotkey handlers registered")


def initialize_hotkey_system():
    """Initialize the hotkey system with default handlers and global hotkeys."""
    register_default_handlers()
    # Don't auto-start - let the application control when to start/stop
    logger.debug("Hotkey system initialized (handlers registered)")


def register_default_global_hotkeys():
    """Register default global hotkey mappings."""
    # Only register function keys as global hotkeys to avoid conflicts with prompt_toolkit
    # Function keys are less likely to interfere with text input
    register_global_hotkey("f12", "cancel")  # F12 as emergency interrupt
    logger.debug("Default global hotkeys registered (F12 for emergency cancel)")
