# src/qx/cli/console.py
# This module handles rich text output using the rich library.

from typing import Optional, Any
from rich.console import Console
from rich.status import Status
from rich.theme import Theme as RichTheme
from rich.console import RenderableType # For input prompt type hint

# Create a standard Rich Console - this will be the base for qx_console
_initial_rich_console = Console(force_terminal=True)


class QXConsole:
    """
    A wrapper around rich.console.Console to provide QX-specific console utilities.
    This class manages a single Rich Console instance that can be themed and
    is aware of the currently active global spinner/status.
    """
    _active_status: Optional[Status] = None  # Class attribute for the global spinner
    _spinner_was_stopped_by_input: bool = False # Flag to track if input method stopped the spinner

    def __init__(self, initial_console: Console):
        self._console = initial_console

    @classmethod
    def set_active_status(cls, status: Optional[Status]):
        """Sets or clears the globally active spinner/status object."""
        cls._active_status = status
        # Reset flag when status is newly set or cleared
        cls._spinner_was_stopped_by_input = False


    def print(self, *args, **kwargs):
        """
        Prints to the console using the underlying rich Console.
        """
        return self._console.print(*args, **kwargs)

    def status(self, *args, **kwargs) -> Status:
        """
        Displays a status message with a spinner.
        Forwards to the underlying rich Console's status method.
        """
        # When a new status is created, ensure our flag is reset
        QXConsole._spinner_was_stopped_by_input = False
        return self._console.status(*args, **kwargs)

    def apply_theme(self, theme: RichTheme):
        """
        Applies a new theme to the console.
        This re-initializes the internal Rich Console instance.
        """
        self._console = Console(theme=theme, force_terminal=True)

    def input(self, prompt: RenderableType = "", *, password: bool = False, stream: Any = None) -> str:
        """
        Gets input from the user, stopping the global spinner if active and restarting it afterwards.
        Signature matches rich.console.Console.input.
        """
        # Check if there's an active status object.
        # The status object's own context manager in main.py handles its primary start/stop.
        # Here, we only intervene if it's currently "active" from QXConsole's perspective.
        if QXConsole._active_status is not None and not QXConsole._spinner_was_stopped_by_input:
            try:
                QXConsole._active_status.stop()
                QXConsole._spinner_was_stopped_by_input = True
                # Attempt to clear the line where the spinner might have been.
                # This can be tricky. A simple newline might be sufficient.
                self._console.line()
            except Exception as e:
                # Log this, as it's unexpected behavior if _active_status is set.
                # For now, we'll proceed without spinner management if stop fails.
                logging.getLogger(__name__).error(f"Error stopping QXConsole._active_status: {e}")
                QXConsole._spinner_was_stopped_by_input = False # Ensure it's false if stop failed

        try:
            user_response = self._console.input(prompt, password=password, stream=stream)
        finally:
            if QXConsole._spinner_was_stopped_by_input:
                if QXConsole._active_status is not None:
                    try:
                        QXConsole._active_status.start()
                    except Exception as e:
                         logging.getLogger(__name__).error(f"Error restarting QXConsole._active_status: {e}")
                QXConsole._spinner_was_stopped_by_input = False # Reset flag

        return user_response

    def __getattr__(self, name):
        """Forward all other attribute access to the underlying console."""
        return getattr(self._console, name)


# Create the global QXConsole instance
qx_console = QXConsole(_initial_rich_console)


def show_spinner(
    message: str = "Thinking...",
    spinner_name: str = "dots",
    speed: float = 1.0,
    style: str = "status.spinner",
) -> Status:
    """
    Display a spinner with the given message using the global qx_console.
    The returned Status object should be managed (e.g., with a context manager)
    to ensure it's properly started and stopped.
    """
    # This function creates and returns a status.
    # The QXConsole.set_active_status will be called by the caller (e.g. main.py)
    return qx_console.status(
        message,
        spinner=spinner_name,
        speed=speed,
        spinner_style=style,
    )


if __name__ == "__main__":
    import time
    import logging
    from rich.theme import Theme as RichThemeExample
    from rich.prompt import Prompt

    logging.basicConfig(level=logging.DEBUG) # For seeing logs from console.py

    custom_theme = RichThemeExample({
        "status.spinner": "bold blue",
        "info": "dim cyan",
        "prompt.choices.key": "bold yellow",
        "prompt.invalid": "red"
    })
    qx_console.apply_theme(custom_theme)

    qx_console.print("[info]Testing spinner and input interaction (fixed)...[/info]")

    # Simulate spinner being active
    # In real use, show_spinner() returns a Status, which is then started by its context manager
    test_spinner_status_obj = show_spinner("Simulating background task...")
    QXConsole.set_active_status(test_spinner_status_obj) # Register the spinner

    # The `with` statement on the status object calls .start() on enter and .stop() on exit
    with test_spinner_status_obj:
        qx_console.print("Spinner is active. Now asking for input (spinner should stop):")
        time.sleep(1.5) # Let spinner show

        try:
            # Prompt.ask uses the console's input method.
            # We pass our qx_console instance to it.
            age_str = Prompt.ask(
                "How old are you?",
                choices=["10", "20", "30"],
                default="20",
                console=qx_console # Crucial: use our qx_console
            )
            qx_console.print(f"You said you are {age_str}. Spinner should have restarted.")
        except Exception as e:
            qx_console.print(f"[red]Error during prompt: {e}[/red]")

        time.sleep(2) # Let spinner show again if it restarted
        test_spinner_status_obj.update("Background task almost done...")
        time.sleep(1.5)

    QXConsole.set_active_status(None) # Unregister
    qx_console.print("[green]Test finished. Spinner should be gone.[/green]")

    qx_console.print("\n[info]Testing input without an active global spinner...[/info]")
    # Ensure _active_status is None
    QXConsole.set_active_status(None)
    name = Prompt.ask("What is your name again (no spinner active)?", console=qx_console)
    qx_console.print(f"Hello again, {name}!")
    qx_console.print("[green]Test finished.[/green]")
