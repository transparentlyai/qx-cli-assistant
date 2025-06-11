"""
Global hotkey capture implementation for QX.

This module provides the low-level global hotkey capture functionality
using termios and tty for Unix terminals. It's based on the python-hotkeys
library but integrated specifically for QX's architecture.
"""

import sys
import termios
import tty
import threading
import time
import queue
import asyncio
import inspect
import atexit
import select
import os
from codecs import getincrementaldecoder
from typing import Dict, Optional, Callable
import logging

logger = logging.getLogger(__name__)


class KeySequenceParser:
    """
    Robust key sequence parser based on prompt_toolkit patterns.
    Handles multi-character escape sequences with proper timeout and prefix matching.
    """

    # Comprehensive key mappings with terminal variations (based on prompt_toolkit)
    ANSI_SEQUENCES = {
        # Control characters
        "\x00": "ctrl+@",
        "\x01": "ctrl+a",
        "\x02": "ctrl+b",
        "\x03": "ctrl+c",
        "\x04": "ctrl+d",
        "\x05": "ctrl+e",
        "\x06": "ctrl+f",
        "\x07": "ctrl+g",
        "\x08": "ctrl+h",
        "\x09": "ctrl+i",
        "\x0a": "ctrl+j",
        "\x0b": "ctrl+k",
        "\x0c": "ctrl+l",
        "\x0d": "ctrl+m",
        "\x0e": "ctrl+n",
        "\x0f": "f4",
        "\x10": "f1",
        "\x11": "ctrl+q",
        "\x12": "ctrl+r",
        "\x13": "ctrl+s",
        "\x14": "f3",
        "\x15": "f5",
        "\x16": "ctrl+v",
        "\x17": "f2",
        "\x18": "ctrl+x",
        "\x19": "ctrl+y",
        "\x1a": "ctrl+z",
        "\x1b": "escape",
        "\x1c": "ctrl+\\",
        "\x1d": "ctrl+]",
        "\x1e": "ctrl+^",
        "\x1f": "ctrl+_",
        "\x7f": "delete",
        # Function keys - F1-F4 (multiple patterns for terminal compatibility)
        "\x1bOP": "f1",  # Standard xterm
        "\x1b[[A": "f1",  # Linux console
        "\x1b[11~": "f1",  # rxvt-unicode, some xterms
        "\x1bOQ": "f2",  # Standard xterm
        "\x1b[[B": "f2",  # Linux console
        "\x1b[12~": "f2",  # rxvt-unicode, some xterms
        "\x1bOR": "f3",  # Standard xterm
        "\x1b[[C": "f3",  # Linux console
        "\x1b[13~": "f3",  # rxvt-unicode, some xterms
        "\x1bOS": "f4",  # Standard xterm
        "\x1b[[D": "f4",  # Linux console
        "\x1b[14~": "f4",  # rxvt-unicode, some xterms
        # Function keys F5-F12 (consistent across terminals)
        "\x1b[15~": "f5",
        "\x1b[17~": "f6",
        "\x1b[18~": "f7",
        "\x1b[19~": "f8",
        "\x1b[20~": "f9",
        "\x1b[21~": "f10",
        "\x1b[23~": "f11",
        "\x1b[24~": "f12",
        # Extended F keys (F13-F24)
        "\x1b[25~": "f13",
        "\x1b[26~": "f14",
        "\x1b[28~": "f15",
        "\x1b[29~": "f16",
        "\x1b[31~": "f17",
        "\x1b[32~": "f18",
        "\x1b[33~": "f19",
        "\x1b[34~": "f20",
        # Arrow keys
        "\x1b[A": "up",
        "\x1b[B": "down",
        "\x1b[C": "right",
        "\x1b[D": "left",
        "\x1bOA": "up",  # Application mode
        "\x1bOB": "down",  # Application mode
        "\x1bOC": "right",  # Application mode
        "\x1bOD": "left",  # Application mode
        # Navigation keys
        "\x1b[H": "home",
        "\x1b[F": "end",
        "\x1b[1~": "home",  # Alternative
        "\x1b[4~": "end",  # Alternative
        "\x1bOH": "home",  # Application mode
        "\x1bOF": "end",  # Application mode
        # Page navigation
        "\x1b[5~": "pageup",
        "\x1b[6~": "pagedown",
        # Insert/Delete
        "\x1b[2~": "insert",
        "\x1b[3~": "delete",
        # Modified function keys (with Ctrl)
        "\x1b[1;5P": "ctrl+f1",
        "\x1b[1;5Q": "ctrl+f2",
        "\x1b[1;5R": "ctrl+f3",
        "\x1b[1;5S": "ctrl+f4",
        "\x1b[15;5~": "ctrl+f5",
        "\x1b[17;5~": "ctrl+f6",
        "\x1b[18;5~": "ctrl+f7",
        "\x1b[19;5~": "ctrl+f8",
        "\x1b[20;5~": "ctrl+f9",
        "\x1b[21;5~": "ctrl+f10",
        "\x1b[23;5~": "ctrl+f11",
        "\x1b[24;5~": "ctrl+f12",
        # Modified arrow keys
        "\x1b[1;5A": "ctrl+up",
        "\x1b[1;5B": "ctrl+down",
        "\x1b[1;5C": "ctrl+right",
        "\x1b[1;5D": "ctrl+left",
        "\x1b[1;2A": "shift+up",
        "\x1b[1;2B": "shift+down",
        "\x1b[1;2C": "shift+right",
        "\x1b[1;2D": "shift+left",
        "\x1b[1;3A": "alt+up",
        "\x1b[1;3B": "alt+down",
        "\x1b[1;3C": "alt+right",
        "\x1b[1;3D": "alt+left",
    }

    def __init__(self, timeout: float = 0.1):
        self.timeout = timeout
        self.buffer = ""
        self._prefix_cache: Dict[str, bool] = {}

        # Build Alt+key combinations dynamically
        for char_code in range(ord("a"), ord("z") + 1):
            char = chr(char_code)
            self.ANSI_SEQUENCES[f"\x1b{char}"] = f"alt+{char}"
        for num in range(0, 10):
            self.ANSI_SEQUENCES[f"\x1b{num}"] = f"alt+{num}"

        # Add aliases for common keys (avoiding duplicate key errors)
        self._key_aliases = {
            "backspace": "ctrl+h",
            "tab": "ctrl+i",
            "enter": "ctrl+j",
            "return": "ctrl+m",
            "ctrl+space": "ctrl+@",
        }

    def _is_prefix_of_longer_match(self, prefix: str) -> bool:
        """Check if prefix could be the start of a longer sequence."""
        if prefix in self._prefix_cache:
            return self._prefix_cache[prefix]

        result = any(
            seq.startswith(prefix) and seq != prefix
            for seq in self.ANSI_SEQUENCES.keys()
        )
        self._prefix_cache[prefix] = result
        return result

    def feed(self, char: str) -> Optional[str]:
        """
        Feed a character to the parser.
        Returns a key name if a complete sequence is found, None if building.
        """
        self.buffer += char

        # Check if this could be a prefix of something longer FIRST
        if self._is_prefix_of_longer_match(self.buffer):
            # Still building a sequence - don't return anything yet
            return None

        # Check for exact match only if it's not a prefix of something longer
        if self.buffer in self.ANSI_SEQUENCES:
            result = self.ANSI_SEQUENCES[self.buffer]
            self.buffer = ""
            return result

        # No exact match and not a prefix - try to find the longest valid prefix
        for i in range(len(self.buffer), 0, -1):
            prefix = self.buffer[:i]
            if prefix in self.ANSI_SEQUENCES:
                result = self.ANSI_SEQUENCES[prefix]
                self.buffer = self.buffer[i:]
                return result

        # No valid prefix found, return first character as-is
        result = self.buffer[0]
        self.buffer = self.buffer[1:]
        return result

    def flush(self) -> Optional[str]:
        """Force processing of any buffered incomplete sequence."""
        if not self.buffer:
            return None

        # Return the buffer as-is and clear it
        result = self.buffer
        self.buffer = ""
        return result


class GlobalHotkeys:
    """
    A robust terminal hotkey handler using advanced parsing techniques.
    Based on patterns from prompt_toolkit for maximum compatibility.
    """

    def __init__(self, timeout: float = 0.1):
        self.parser = KeySequenceParser(timeout)
        self.timeout = timeout

        self._hotkeys: Dict[str, Callable] = {}
        self._running = False
        self._lock = threading.Lock()
        # Limit queue size to prevent memory issues
        self.unhandled_keys_queue: queue.Queue[str] = queue.Queue(maxsize=1000)

        self._listener_thread: Optional[threading.Thread] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._event_loop_thread: Optional[threading.Thread] = None
        self._flush_task: Optional[asyncio.Task] = None

        # Terminal setup
        self._fd: Optional[int] = None
        self._original_settings = None
        self._decoder = None

        try:
            # Check if we're in a proper TTY before initializing
            if sys.stdin.isatty():
                self._fd = sys.stdin.fileno()
                self._original_settings = termios.tcgetattr(self._fd)
                self._decoder = getincrementaldecoder("utf-8")(errors="surrogateescape")
                atexit.register(self._restore_terminal)
                logger.debug("Terminal initialized for global hotkey capture")
            else:
                logger.debug("Not running in TTY - global hotkeys may not work")
        except (termios.error, OSError) as e:
            logger.debug(f"Could not initialize terminal settings: {e}")

    def _restore_terminal(self):
        """Restore original terminal settings."""
        if self._original_settings and self._fd is not None:
            try:
                termios.tcsetattr(self._fd, termios.TCSADRAIN, self._original_settings)
                logger.debug("Terminal settings restored")
            except (termios.error, OSError) as e:
                logger.warning(f"Could not restore terminal settings: {e}")

    def _get_key_sequence(self, key: str) -> str:
        """Convert key name to sequence (for compatibility)."""
        key_lower = key.lower()

        # Check aliases first
        if key_lower in self.parser._key_aliases:
            aliased_key = self.parser._key_aliases[key_lower]
            key_lower = aliased_key

        # Reverse lookup in our sequences
        for seq, name in self.parser.ANSI_SEQUENCES.items():
            if name == key_lower:
                return seq
        return key

    def register_hotkey(self, key: str, callback: Callable):
        """Register a hotkey with its callback function."""
        key_name = key.lower()

        # Handle aliases
        if key_name in self.parser._key_aliases:
            key_name = self.parser._key_aliases[key_name]

        with self._lock:
            self._hotkeys[key_name] = callback
        logger.debug(f"Registered global hotkey: {key_name}")

    def unregister_hotkey(self, key: str):
        """Unregister a hotkey."""
        key_name = key.lower()

        # Handle aliases
        if key_name in self.parser._key_aliases:
            key_name = self.parser._key_aliases[key_name]

        with self._lock:
            if key_name in self._hotkeys:
                del self._hotkeys[key_name]
                logger.debug(f"Unregistered global hotkey: {key_name}")

    def get_unhandled_key(self) -> Optional[str]:
        """Get an unhandled key from the queue (non-blocking)."""
        try:
            return self.unhandled_keys_queue.get_nowait()
        except queue.Empty:
            return None

    def clear_unhandled_keys(self):
        """Clear all unhandled keys from the queue."""
        while True:
            try:
                self.unhandled_keys_queue.get_nowait()
            except queue.Empty:
                break

    def get_queue_size(self) -> int:
        """Get the current size of the unhandled keys queue."""
        return self.unhandled_keys_queue.qsize()

    def _event_loop_runner(self):
        """Run the async event loop in a separate thread."""
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    async def _timeout_handler(self):
        """Handle parser timeout - flush incomplete sequences."""
        await asyncio.sleep(self.timeout)
        if self.parser.buffer:
            # Flush incomplete sequence
            result = self.parser.flush()
            if result:
                self._process_key(result)

    def _schedule_timeout(self):
        """Schedule a timeout for incomplete sequences."""
        # Cancel any existing timeout task to prevent accumulation
        if self._flush_task and not self._flush_task.done():
            self._flush_task.cancel()

        if self._loop and self._loop.is_running():
            try:
                self._flush_task = self._loop.create_task(self._timeout_handler())
            except RuntimeError:
                # Event loop might be closing, ignore
                pass

    def _process_key(self, key: str):
        """Process a complete key sequence."""
        callback = None
        handled = False

        with self._lock:
            # Try exact match first
            if key in self._hotkeys:
                callback = self._hotkeys[key]
                handled = True
            # Try case-insensitive match
            elif key.lower() in self._hotkeys:
                callback = self._hotkeys[key.lower()]
                handled = True

        if callback:
            try:
                logger.debug(f"Executing global hotkey callback for: {key}")
                if inspect.iscoroutinefunction(callback):
                    if self._loop and self._loop.is_running():
                        asyncio.run_coroutine_threadsafe(callback(), self._loop)
                        logger.debug(f"Scheduled async callback for {key}")
                    else:
                        logger.warning(
                            f"Event loop not running for async callback: {key}"
                        )
                else:
                    callback()
                    logger.debug(f"Executed sync callback for {key}")
            except Exception as e:
                logger.error(
                    f"Error in global hotkey callback for '{key}': {e}", exc_info=True
                )

        if not handled:
            # Only capture keys that are unhandled and not normal input
            # Skip regular printable characters and common editing keys
            if not (len(key) == 1 and key.isprintable()) and key not in [
                "enter",
                "return",
                "tab",
                "space",
                "backspace",
                "delete",
            ]:
                # Add to queue with overflow protection for special keys only
                try:
                    self.unhandled_keys_queue.put_nowait(key)
                except queue.Full:
                    # Queue is full - discard oldest items to make room
                    try:
                        self.unhandled_keys_queue.get_nowait()  # Remove oldest
                        self.unhandled_keys_queue.put_nowait(key)  # Add new
                    except queue.Empty:
                        pass  # Queue became empty, ignore

    def _read_available_input(self) -> str:
        """Read all currently available input without blocking."""
        if self._fd is None:
            return ""

        result = ""
        try:
            while True:
                ready, _, _ = select.select([self._fd], [], [], 0)
                if not ready:
                    break
                data = os.read(self._fd, 1024)
                if not data:
                    break
                # Decode with incremental decoder to handle partial UTF-8
                decoded = (
                    self._decoder.decode(data)
                    if self._decoder
                    else data.decode("utf-8", errors="surrogateescape")
                )
                result += decoded
        except (OSError, UnicodeDecodeError) as e:
            logger.debug(f"Error reading input: {e}")

        return result

    def _listener(self):
        """Main input listener loop with robust parsing."""
        time.sleep(0.01)

        try:
            if self._fd is not None:
                try:
                    tty.setcbreak(self._fd)
                    logger.debug(
                        "Terminal set to cbreak mode for global hotkey capture"
                    )
                except (termios.error, OSError) as e:
                    logger.debug(f"Cannot set terminal to cbreak mode: {e}")
                    logger.debug(
                        "Hotkey functionality may not work properly in this environment"
                    )
                    return

            while self._running:
                try:
                    # Read available input
                    if self._fd is not None:
                        ready, _, _ = select.select([self._fd], [], [], 0.1)
                        if ready:
                            input_data = self._read_available_input()
                            if input_data:
                                # Process each character through the parser
                                for char in input_data:
                                    result = self.parser.feed(char)
                                    if result:
                                        self._process_key(result)
                                    else:
                                        # Still building sequence, schedule timeout
                                        self._schedule_timeout()
                    else:
                        # Fallback for non-TTY environments
                        char = sys.stdin.read(1)
                        result = self.parser.feed(char)
                        if result:
                            self._process_key(result)
                        else:
                            self._schedule_timeout()

                except (OSError, IOError):
                    if self._running:
                        time.sleep(0.01)

        finally:
            self._restore_terminal()

    def start(self):
        """Start the global hotkey listener."""
        if self._running:
            logger.debug("Global hotkey listener already running")
            return

        self._running = True

        # Start async event loop
        self._loop = asyncio.new_event_loop()
        self._event_loop_thread = threading.Thread(
            target=self._event_loop_runner, daemon=True, name="GlobalHotkeys-EventLoop"
        )
        self._event_loop_thread.start()

        # Start input listener
        self._listener_thread = threading.Thread(
            target=self._listener, daemon=True, name="GlobalHotkeys-Listener"
        )
        self._listener_thread.start()

        logger.debug("Global hotkey listener started")

    def stop(self):
        """Stop the global hotkey listener."""
        if not self._running:
            return

        self._running = False
        logger.debug("Stopping global hotkey listener")

        # Cancel any pending timeout
        if self._flush_task and not self._flush_task.done():
            self._flush_task.cancel()

        # Clear any accumulated unhandled keys
        self.clear_unhandled_keys()

        # Stop event loop
        if self._loop and self._loop.is_running():
            self._loop.call_soon_threadsafe(self._loop.stop)

        # Wait for threads
        if self._event_loop_thread:
            self._event_loop_thread.join(timeout=1.0)

        if (
            self._listener_thread
            and threading.current_thread() is not self._listener_thread
        ):
            self._listener_thread.join(timeout=1.0)

        # Final cleanup
        self._flush_task = None

        logger.debug("Global hotkey listener stopped")
