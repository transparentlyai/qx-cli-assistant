# src/qx/cli/console.py
# This module handles rich text output using the rich library.

from typing import Optional, Any
from rich.console import Console
from rich.status import Status
from rich.theme import Theme as RichTheme
from rich.text import TextType # For input prompt type hint
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

    def __init__(self, initial_console: Console):
        self._console = initial_console

    @classmethod
    def set_active_status(cls, status: Optional[Status]):
        """Sets or clears the globally active spinner/status object."""
        cls._active_status = status

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
        return self._console.status(*args, **kwargs)

    def apply_theme(self, theme: RichTheme):
        """
        Applies a new theme to the console.
        This re-initializes the internal Rich Console instance.
        """
        self._console = Console(theme=theme, force_terminal=True)

    def input(self, prompt: RenderableType = "", *, password: bool = False, stream: Any = None) -> str:
        """
        Gets input from the user, hiding the global spinner if active.
        Signature matches rich.console.Console.input.
        """
        original_spinner_visibility = False
        spinner_was_active_and_visible = False

        if QXConsole._active_status and QXConsole._active_status.visible:
            spinner_was_active_and_visible = True
            original_spinner_visibility = QXConsole._active_status.visible # Should be True
            QXConsole._active_status.visible = False
            # Force a refresh of the console area where the spinner was.
            # This is a bit of a guess; Rich might handle redraw automatically.
            # If not, printing an empty line or a specific control sequence might be needed.
            # For now, let's assume hiding is enough.
            self._console.line() # Try to ensure spinner area is cleared before prompt

        try:
            # Delegate to the wrapped RichConsole instance's input method
            user_response = self._console.input(prompt, password=password, stream=stream)
        finally:
            if spinner_was_active_and_visible:
                # Restore spinner visibility only if it was active and we hid it
                if QXConsole._active_status: # Check if it wasn't set to None in the meantime
                    QXConsole._active_status.visible = original_spinner_visibility
                    # If the spinner is restored, it might need an update to redraw correctly.
                    # QXConsole._active_status.update() # This might cause a flicker or be unnecessary.
                    # Let's test without explicit update first.

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

    Args:
        message: The message to display alongside the spinner.
        spinner_name: The type of spinner to be used (e.g., "dots", "line", "moon").
        speed: The speed of the spinner.
        style: The style to apply to the spinner.

    Returns:
        A rich.status.Status object that can be updated or stopped.
    """
    return qx_console.status(
        message,
        spinner=spinner_name,
        speed=speed,
        spinner_style=style,
    )


if __name__ == "__main__":
    import time
    from rich.theme import Theme as RichThemeExample
    from rich.prompt import Prompt # For testing input

    custom_theme = RichThemeExample({
        "status.spinner": "bold blue",
        "info": "dim cyan",
        "prompt.choices.key": "bold yellow", # Example for prompt
        "prompt.invalid": "red"
    })
    qx_console.apply_theme(custom_theme)

    qx_console.print("[info]Testing spinner and input interaction...[/info]")

    # Simulate spinner being active
    test_spinner = show_spinner("Simulating background task...")
    QXConsole.set_active_status(test_spinner) # Register the spinner

    with test_spinner: # Context manager for the spinner itself
        qx_console.print("Spinner is active. Now asking for input (spinner should hide):")
        time.sleep(1) # Let spinner show
        
        # Test qx_console.input directly (which Prompt.ask would use)
        # name = qx_console.input("What is your name? ")
        # qx_console.print(f"Hello, {name}!")
        
        # Test with Rich Prompt
        try:
            age_str = Prompt.ask(
                "How old are you?", 
                choices=["10", "20", "30"], 
                default="20", 
                console=qx_console # Crucial: use our qx_console
            )
            qx_console.print(f"You said you are {age_str}. Spinner should have reappeared if it was hidden.")
        except Exception as e:
            qx_console.print(f"[red]Error during prompt: {e}[/red]")

        time.sleep(2) # Let spinner show again
        test_spinner.update("Background task almost done...")
        time.sleep(1)

    QXConsole.set_active_status(None) # Unregister
    qx_console.print("[green]Test finished. Spinner should be gone.[/green]")
