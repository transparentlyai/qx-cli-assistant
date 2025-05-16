# src/qx/cli/console.py
# This module handles rich text output using the rich library.

from typing import Optional

from rich.console import Console
from rich.status import Status
from rich.theme import Theme as RichTheme # Renamed to avoid conflict

# Create a standard Rich Console - this will be the base for qx_console
# It can be re-initialized with a theme later.
_initial_rich_console = Console(force_terminal=True)


class QXConsole:
    """
    A wrapper around rich.console.Console to provide QX-specific console utilities.
    This class manages a single Rich Console instance that can be themed.
    """

    def __init__(self, initial_console: Console):
        self._console = initial_console

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
        # Potentially log theme application here if a logger is available/passed

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
    # Ensure spinner uses the potentially themed qx_console
    return qx_console.status(
        message,
        spinner=spinner_name,
        speed=speed,
        spinner_style=style,
    )


if __name__ == "__main__":
    # Example usage:
    import time
    from rich.theme import Theme as RichThemeExample

    # Example of applying a theme (optional)
    custom_theme = RichThemeExample({"status.spinner": "bold blue", "info": "dim cyan"})
    qx_console.apply_theme(custom_theme)

    spinner = show_spinner("Processing your request...", style="status.spinner")
    with spinner:
        time.sleep(3)
        spinner.update("Almost done...")
        time.sleep(2)
    qx_console.print("[green]Done![/green]")

    with show_spinner("Another task...", spinner_name="moon") as status:
        time.sleep(3)
        status.update("Finalizing...")
        time.sleep(2)
    qx_console.print("Task complete.", style="info")
