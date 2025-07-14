"""
Console Manager for Producer-Consumer Pattern

This module implements a thread-safe console manager that allows multiple
concurrent processes to safely access console output and input functionality
through a producer-consumer pattern.

The system preserves all existing Rich theming, signal handling, hotkey
suspension, and approval flow functionality while enabling concurrent access.
"""

import asyncio
import logging
import queue
import threading
import time
import uuid
from abc import ABC
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union
from rich.console import Console, RenderableType

logger = logging.getLogger(__name__)


class CommandType(Enum):
    """Types of console commands."""

    PRINT = "print"
    INPUT = "input"
    SHUTDOWN = "shutdown"


class InputType(Enum):
    """Types of input requests."""

    SIMPLE_PROMPT = "simple_prompt"
    APPROVAL_REQUEST = "approval_request"
    CHOICE_SELECTION = "choice_selection"


@dataclass
class ConsoleCommand(ABC):
    """Base class for console commands."""

    command_id: str
    command_type: CommandType
    created_at: float
    source_identifier: Optional[str] = None

    def __post_init__(self):
        if not self.command_id:
            self.command_id = str(uuid.uuid4())
        if not self.created_at:
            self.created_at = time.time()


@dataclass
class PrintCommand(ConsoleCommand):
    """Command to print content to console."""

    content: Union[str, RenderableType] = ""
    style: Optional[str] = None
    markup: bool = True
    end: str = "\n"
    console: Optional[Console] = None

    def __post_init__(self):
        super().__post_init__()
        self.command_type = CommandType.PRINT


@dataclass
class InputCommand(ConsoleCommand):
    """Base class for input commands."""

    input_type: InputType = InputType.SIMPLE_PROMPT
    blocking: bool = True
    timeout: Optional[float] = None
    callback: Optional[Callable[[Any], None]] = None
    response_queue: Optional[queue.Queue] = None

    def __post_init__(self):
        super().__post_init__()
        self.command_type = CommandType.INPUT
        if self.blocking and not self.response_queue:
            self.response_queue = queue.Queue()


def create_simple_prompt_command(
    prompt_text: str,
    default: Optional[str] = None,
    console: Optional[Console] = None,
    blocking: bool = True,
    timeout: Optional[float] = None,
    callback: Optional[Callable[[Any], None]] = None,
    source_identifier: Optional[str] = None,
) -> InputCommand:
    """Factory function to create SimplePromptCommand."""
    cmd = InputCommand(
        command_id=str(uuid.uuid4()),
        command_type=CommandType.INPUT,
        created_at=time.time(),
        input_type=InputType.SIMPLE_PROMPT,
        blocking=blocking,
        timeout=timeout,
        callback=callback,
        source_identifier=source_identifier,
    )
    cmd.prompt_text = prompt_text
    cmd.default = default
    cmd.console = console
    return cmd


def create_approval_request_command(
    prompt_message: str,
    console: Console,
    content_to_display: Optional[RenderableType] = None,
    current_value_for_modification: Optional[str] = None,
    default_choice_key: str = "n",
    blocking: bool = True,
    timeout: Optional[float] = None,
    callback: Optional[Callable[[tuple], None]] = None,
    source_identifier: Optional[str] = None,
) -> InputCommand:
    """Factory function to create ApprovalRequestCommand."""
    cmd = InputCommand(
        command_id=str(uuid.uuid4()),
        command_type=CommandType.INPUT,
        created_at=time.time(),
        input_type=InputType.APPROVAL_REQUEST,
        blocking=blocking,
        timeout=timeout,
        callback=callback,
        source_identifier=source_identifier,
    )
    cmd.prompt_message = prompt_message
    cmd.console = console
    cmd.content_to_display = content_to_display
    cmd.current_value_for_modification = current_value_for_modification
    cmd.default_choice_key = default_choice_key
    return cmd


def create_choice_selection_command(
    prompt_text_with_options: str,
    valid_choices: List[str],
    console: Console,
    default_choice: Optional[str] = None,
    blocking: bool = True,
    timeout: Optional[float] = None,
    callback: Optional[Callable[[Optional[str]], None]] = None,
    source_identifier: Optional[str] = None,
) -> InputCommand:
    """Factory function to create ChoiceSelectionCommand."""
    cmd = InputCommand(
        command_id=str(uuid.uuid4()),
        command_type=CommandType.INPUT,
        created_at=time.time(),
        input_type=InputType.CHOICE_SELECTION,
        blocking=blocking,
        timeout=timeout,
        callback=callback,
        source_identifier=source_identifier,
    )
    cmd.prompt_text_with_options = prompt_text_with_options
    cmd.valid_choices = valid_choices
    cmd.console = console
    cmd.default_choice = default_choice
    return cmd


@dataclass
class ShutdownCommand(ConsoleCommand):
    """Command to shut down the console manager."""

    def __post_init__(self):
        super().__post_init__()
        self.command_type = CommandType.SHUTDOWN


class ConsoleManager:
    """
    Thread-safe console manager implementing producer-consumer pattern.

    This manager allows multiple concurrent processes to safely access console
    output and input functionality. It maintains a single consumer thread that
    processes all console interactions sequentially while supporting both
    blocking and non-blocking input patterns.

    Features:
    - Thread-safe print operations with Rich styling support
    - Simple input requests with optional defaults
    - Approval requests (y/n/a/c pattern)
    - Multiple choice selections
    - Source identifier support for component attribution
    - Both blocking and async (callback-based) interaction patterns
    - Automatic fallback to direct console usage when manager not running

    Usage:
        manager = get_console_manager()

        # Print with source identification
        manager.print("Task completed", source_identifier="TaskRunner")

        # Input requests
        name = manager.request_input_blocking("Enter name:", source_identifier="Setup")

        # Approval requests
        result = manager.request_approval_blocking("Continue?", console, source_identifier="Tool")

        # Choice selection
        choice = manager.request_choice_blocking("Select:", options, console, source_identifier="Config")
    """

    def __init__(self, default_console: Optional[Console] = None):
        self._command_queue: queue.Queue = queue.Queue()
        self._consumer_thread: Optional[threading.Thread] = None
        self._running = False
        self._shutdown_event = threading.Event()
        self._pending_responses: Dict[str, Any] = {}
        self._response_lock = threading.Lock()
        self._default_console = default_console

        # Import here to avoid circular imports
        if not self._default_console:
            from qx.cli.theme import themed_console

            self._default_console = themed_console

    def start(self) -> None:
        """Start the console manager consumer thread."""
        if self._running:
            logger.warning("ConsoleManager is already running")
            return

        self._running = True
        self._shutdown_event.clear()
        self._consumer_thread = threading.Thread(
            target=self._consumer_loop, name="ConsoleManager-Consumer", daemon=True
        )
        self._consumer_thread.start()
        logger.debug("ConsoleManager started")

    def stop(self, timeout: float = 5.0) -> None:
        """Stop the console manager consumer thread."""
        if not self._running:
            return

        # Send shutdown command
        shutdown_cmd = ShutdownCommand(
            command_id=str(uuid.uuid4()),
            command_type=CommandType.SHUTDOWN,
            created_at=time.time(),
        )
        self._command_queue.put(shutdown_cmd)

        # Wait for consumer thread to finish
        if self._consumer_thread:
            self._consumer_thread.join(timeout=timeout)
            if self._consumer_thread.is_alive():
                logger.warning(
                    "ConsoleManager consumer thread did not stop within timeout"
                )

        self._running = False
        logger.debug("ConsoleManager stopped")

    def _consumer_loop(self) -> None:
        """Main consumer loop that processes console commands."""
        logger.debug("ConsoleManager consumer loop started")

        while self._running:
            try:
                # Wait for command with timeout to allow periodic checks
                try:
                    command = self._command_queue.get(timeout=1.0)
                except queue.Empty:
                    continue

                if command.command_type == CommandType.SHUTDOWN:
                    logger.debug("Received shutdown command")
                    break
                elif command.command_type == CommandType.PRINT:
                    self._handle_print_command(command)
                elif command.command_type == CommandType.INPUT:
                    asyncio.run(self._handle_input_command(command))

                self._command_queue.task_done()

            except Exception as e:
                logger.error(
                    f"Error in console manager consumer loop: {e}", exc_info=True
                )

        logger.debug("ConsoleManager consumer loop ended")

    def _handle_print_command(self, command: PrintCommand) -> None:
        """Handle print commands."""
        try:
            console = command.console or self._default_console

            # Prepare content with source identifier if provided
            content = command.content
            if command.source_identifier:
                # Prepend the source identifier with styling
                if isinstance(content, str):
                    content = f"[dim]\\[{command.source_identifier}][/dim] {content}"
                else:
                    # For rich renderables, we'll prefix with the identifier
                    from rich.text import Text

                    identifier_text = Text(
                        f"[{command.source_identifier}] ", style="dim"
                    )
                    if hasattr(content, "__rich__"):
                        # Create a group to combine identifier and content
                        from rich.console import Group

                        content = Group(identifier_text, content)
                    else:
                        content = (
                            f"[dim]\\[{command.source_identifier}][/dim] {content}"
                        )

            if command.style:
                console.print(
                    content, style=command.style, markup=command.markup, end=command.end
                )
            else:
                console.print(content, markup=command.markup, end=command.end)
        except Exception as e:
            logger.error(f"Error handling print command: {e}", exc_info=True)

    async def _handle_input_command(self, command: InputCommand) -> None:
        """Handle input commands asynchronously."""
        try:
            response = None

            if command.input_type == InputType.SIMPLE_PROMPT:
                response = await self._handle_simple_prompt(command)
            elif command.input_type == InputType.APPROVAL_REQUEST:
                response = await self._handle_approval_request(command)
            elif command.input_type == InputType.CHOICE_SELECTION:
                response = await self._handle_choice_selection(command)

            # Store response and notify waiting processes
            with self._response_lock:
                self._pending_responses[command.command_id] = response

            if command.blocking and command.response_queue:
                command.response_queue.put(response)

            if command.callback:
                try:
                    command.callback(response)
                except Exception as e:
                    logger.error(f"Error in input command callback: {e}", exc_info=True)

        except Exception as e:
            logger.error(f"Error handling input command: {e}", exc_info=True)

            # Provide error response
            error_response = None
            if command.input_type == InputType.APPROVAL_REQUEST:
                error_response = ("cancelled", None)

            with self._response_lock:
                self._pending_responses[command.command_id] = error_response

            if command.blocking and command.response_queue:
                command.response_queue.put(error_response)

    async def _handle_simple_prompt(self, command: InputCommand) -> Optional[str]:
        """Handle simple prompt input."""
        from rich.prompt import Prompt

        try:
            console = getattr(command, "console", None) or self._default_console
            prompt_text = getattr(command, "prompt_text", "Enter input: ")
            default = getattr(command, "default", None)

            # Prepare prompt text with source identifier if provided
            if command.source_identifier:
                prompt_text = (
                    f"[dim]\\[{command.source_identifier}][/dim] {prompt_text}"
                )

            return await asyncio.to_thread(
                Prompt.ask, prompt_text, default=default, console=console
            )
        except Exception as e:
            logger.error(f"Error in simple prompt: {e}", exc_info=True)
            return None

    async def _handle_approval_request(self, command: InputCommand) -> tuple:
        """Handle approval request using existing user_prompts logic."""
        # Import here to avoid circular imports
        from qx.core.user_prompts import request_confirmation
        import qx.core.user_prompts as user_prompts

        try:
            # Disable console manager usage in user_prompts to prevent circular calls
            old_flag = user_prompts._disable_console_manager
            user_prompts._disable_console_manager = True

            try:
                # Prepare prompt message with source identifier if provided
                prompt_message = getattr(command, "prompt_message", "Approve?")
                if command.source_identifier:
                    prompt_message = (
                        f"[dim]\\[{command.source_identifier}][/dim] {prompt_message}"
                    )

                return await request_confirmation(
                    prompt_message=prompt_message,
                    console=getattr(command, "console", self._default_console),
                    content_to_display=getattr(command, "content_to_display", None),
                    current_value_for_modification=getattr(
                        command, "current_value_for_modification", None
                    ),
                    default_choice_key=getattr(command, "default_choice_key", "n"),
                )
            finally:
                # Restore original flag
                user_prompts._disable_console_manager = old_flag

        except Exception as e:
            logger.error(f"Error in approval request: {e}", exc_info=True)
            return ("cancelled", None)

    async def _handle_choice_selection(self, command: InputCommand) -> Optional[str]:
        """Handle choice selection using existing user_prompts logic."""
        # Import here to avoid circular imports
        from qx.core.user_prompts import get_user_choice_from_options_async
        import qx.core.user_prompts as user_prompts

        try:
            # Disable console manager usage in user_prompts to prevent circular calls
            old_flag = user_prompts._disable_console_manager
            user_prompts._disable_console_manager = True

            try:
                # Prepare prompt message with source identifier if provided
                prompt_text = getattr(command, "prompt_text_with_options", "Choose: ")
                if command.source_identifier:
                    prompt_text = (
                        f"[dim]\\[{command.source_identifier}][/dim] {prompt_text}"
                    )

                return await get_user_choice_from_options_async(
                    console=getattr(command, "console", self._default_console),
                    prompt_text_with_options=prompt_text,
                    valid_choices=getattr(command, "valid_choices", ["y", "n"]),
                    default_choice=getattr(command, "default_choice", None),
                )
            finally:
                # Restore original flag
                user_prompts._disable_console_manager = old_flag

        except Exception as e:
            logger.error(f"Error in choice selection: {e}", exc_info=True)
            return None

    # Public API methods

    def print(
        self,
        content: Union[str, RenderableType],
        style: Optional[str] = None,
        markup: bool = True,
        end: str = "\n",
        console: Optional[Console] = None,
        source_identifier: Optional[str] = None,
    ) -> None:
        """Queue a print command."""
        if not self._running:
            # Fallback to direct printing if manager not running
            target_console = console or self._default_console
            target_console.print(content, style=style, markup=markup, end=end)
            return

        command = PrintCommand(
            command_id=str(uuid.uuid4()),
            command_type=CommandType.PRINT,
            created_at=time.time(),
            content=content,
            style=style,
            markup=markup,
            end=end,
            console=console,
            source_identifier=source_identifier,
        )
        self._command_queue.put(command)

    def request_approval_blocking(
        self,
        prompt_message: str,
        console: Console,
        content_to_display: Optional[RenderableType] = None,
        current_value_for_modification: Optional[str] = None,
        default_choice_key: str = "n",
        timeout: Optional[float] = None,
        source_identifier: Optional[str] = None,
    ) -> tuple:
        """Request approval with blocking wait for response."""
        if not self._running:
            # Fallback to direct call if manager not running
            import asyncio
            from qx.core.user_prompts import request_confirmation

            return asyncio.run(
                request_confirmation(
                    prompt_message,
                    console,
                    content_to_display,
                    current_value_for_modification,
                    default_choice_key,
                )
            )

        command = create_approval_request_command(
            prompt_message=prompt_message,
            console=console,
            content_to_display=content_to_display,
            current_value_for_modification=current_value_for_modification,
            default_choice_key=default_choice_key,
            blocking=True,
            timeout=timeout,
            source_identifier=source_identifier,
        )

        self._command_queue.put(command)

        try:
            response = command.response_queue.get(timeout=timeout)
            return response
        except queue.Empty:
            logger.warning("Approval request timed out")
            return ("cancelled", None)

    def request_approval_async(
        self,
        prompt_message: str,
        console: Console,
        callback: Callable[[tuple], None],
        content_to_display: Optional[RenderableType] = None,
        current_value_for_modification: Optional[str] = None,
        default_choice_key: str = "n",
        source_identifier: Optional[str] = None,
    ) -> str:
        """Request approval with async callback for response."""
        command = create_approval_request_command(
            prompt_message=prompt_message,
            console=console,
            content_to_display=content_to_display,
            current_value_for_modification=current_value_for_modification,
            default_choice_key=default_choice_key,
            blocking=False,
            callback=callback,
            source_identifier=source_identifier,
        )

        self._command_queue.put(command)
        return command.command_id

    def request_choice_blocking(
        self,
        prompt_text_with_options: str,
        valid_choices: List[str],
        console: Console,
        default_choice: Optional[str] = None,
        timeout: Optional[float] = None,
        source_identifier: Optional[str] = None,
    ) -> Optional[str]:
        """Request choice selection with blocking wait for response."""
        if not self._running:
            # Fallback to direct call if manager not running
            import asyncio
            from qx.core.user_prompts import get_user_choice_from_options_async

            return asyncio.run(
                get_user_choice_from_options_async(
                    console, prompt_text_with_options, valid_choices, default_choice
                )
            )

        command = create_choice_selection_command(
            prompt_text_with_options=prompt_text_with_options,
            valid_choices=valid_choices,
            console=console,
            default_choice=default_choice,
            blocking=True,
            timeout=timeout,
            source_identifier=source_identifier,
        )

        self._command_queue.put(command)

        try:
            response = command.response_queue.get(timeout=timeout)
            return response
        except queue.Empty:
            logger.warning("Choice selection timed out")
            return None

    def request_choice_async(
        self,
        prompt_text_with_options: str,
        valid_choices: List[str],
        console: Console,
        callback: Callable[[Optional[str]], None],
        default_choice: Optional[str] = None,
        source_identifier: Optional[str] = None,
    ) -> str:
        """Request choice selection with async callback for response."""
        command = create_choice_selection_command(
            prompt_text_with_options=prompt_text_with_options,
            valid_choices=valid_choices,
            console=console,
            default_choice=default_choice,
            blocking=False,
            callback=callback,
            source_identifier=source_identifier,
        )

        self._command_queue.put(command)
        return command.command_id

    def request_input_blocking(
        self,
        prompt_text: str,
        default: Optional[str] = None,
        console: Optional[Console] = None,
        timeout: Optional[float] = None,
        source_identifier: Optional[str] = None,
    ) -> Optional[str]:
        """Request simple input with blocking wait for response."""
        if not self._running:
            # Fallback to direct call if manager not running
            from rich.prompt import Prompt

            target_console = console or self._default_console
            return Prompt.ask(prompt_text, default=default, console=target_console)

        command = create_simple_prompt_command(
            prompt_text=prompt_text,
            default=default,
            console=console,
            blocking=True,
            timeout=timeout,
            source_identifier=source_identifier,
        )

        self._command_queue.put(command)

        try:
            response = command.response_queue.get(timeout=timeout)
            return response
        except queue.Empty:
            logger.warning("Input request timed out")
            return None

    def request_input_async(
        self,
        prompt_text: str,
        callback: Callable[[Optional[str]], None],
        default: Optional[str] = None,
        console: Optional[Console] = None,
        source_identifier: Optional[str] = None,
    ) -> str:
        """Request simple input with async callback for response."""
        command = create_simple_prompt_command(
            prompt_text=prompt_text,
            default=default,
            console=console,
            blocking=False,
            callback=callback,
            source_identifier=source_identifier,
        )

        self._command_queue.put(command)
        return command.command_id

    def get_response(self, command_id: str) -> Optional[Any]:
        """Get response for a given command ID (for polling pattern)."""
        with self._response_lock:
            return self._pending_responses.get(command_id)

    def is_response_ready(self, command_id: str) -> bool:
        """Check if response is ready for a given command ID."""
        with self._response_lock:
            return command_id in self._pending_responses

    def clear_response(self, command_id: str) -> None:
        """Clear stored response for a given command ID."""
        with self._response_lock:
            self._pending_responses.pop(command_id, None)


# Global console manager instance
_console_manager: Optional[ConsoleManager] = None
_manager_lock = threading.Lock()


def get_console_manager() -> ConsoleManager:
    """Get the global console manager instance."""
    global _console_manager

    with _manager_lock:
        if _console_manager is None:
            _console_manager = ConsoleManager()
            _console_manager.start()
        return _console_manager


def shutdown_console_manager() -> None:
    """Shutdown the global console manager."""
    global _console_manager

    with _manager_lock:
        if _console_manager is not None:
            _console_manager.stop()
            _console_manager = None
