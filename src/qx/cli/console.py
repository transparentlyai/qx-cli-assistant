# src/qx/cli/console.py
# This module handles rich text output using the rich library.

import logging # Added for logging within QXConsole
from typing import Optional, Any
from rich.console import Console, RenderableType # For input prompt type hint
from rich.status import Status
from rich.syntax import Syntax # Added for syntax highlighting
from rich.theme import Theme # Import Theme

# Define a custom theme for QX
# These styles can be used with console.print("message", style="stylename")
# or with markup: console.print("[stylename]message[/stylename]")
qx_theme = Theme({
    "info": "dim cyan",
    "warning": "yellow",  # Define the warning style
    "danger": "bold red",
    "success": "green",
    # Add other custom styles here as needed
    # "status.spinner": "blue", # Example if we wanted to customize spinner style via theme
})

# Create a standard Rich Console - this will be the base for qx_console
# Apply the custom theme here
_initial_rich_console = Console(force_terminal=True, theme=qx_theme)


class QXConsole:
    """
    A wrapper around rich.console.Console to provide QX-specific console utilities.
    This class manages a single Rich Console instance that
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

    def input(self, prompt: RenderableType = "", *, password: bool = False, stream: Any = None) -> str:
        """
        Gets input from the user, stopping the global spinner if active and restarting it afterwards.
        Signature matches rich.console.Console.input.
        """
        spinner_needs_restart = False
        if QXConsole._active_status is not None and not QXConsole._spinner_was_stopped_by_input:
            try:
                QXConsole._active_status.stop()
                QXConsole._spinner_was_stopped_by_input = True
                spinner_needs_restart = True # Mark that we stopped it
            except Exception as e:
                logging.getLogger(__name__).error(f"Error stopping QXConsole._active_status: {e}")
                QXConsole._spinner_was_stopped_by_input = False

        try:
            user_response = self._console.input(prompt, password=password, stream=stream)
        finally:
            if spinner_needs_restart: # Only restart if we explicitly stopped it
                if QXConsole._active_status is not None:
                    try:
                        QXConsole._active_status.start()
                    except Exception as e:
                         logging.getLogger(__name__).error(f"Error restarting QXConsole._active_status: {e}")
                QXConsole._spinner_was_stopped_by_input = False # Reset flag

        return user_response

    def print_syntax(
        self,
        code: str,
        lexer_name: str,
        theme: str = "vim", # Default syntax theme
        line_numbers: bool = True,
        word_wrap: bool = False,
        background_color: Optional[str] = None,
        **kwargs: Any
    ):
        """
        Prints code with syntax highlighting.

        Args:
            code (str): The code to highlight.
            lexer_name (str): The name of the lexer (e.g., "python", "json", "bash").
            theme (str, optional): The Pygments theme to use. Defaults to "vim".
            line_numbers (bool, optional): Whether to show line numbers. Defaults to True.
            word_wrap (bool, optional): Whether to wrap lines. Defaults to False.
            background_color (Optional[str], optional): Optional background color for the syntax block.
            **kwargs: Additional arguments to pass to the `Syntax` constructor.
        """
        syntax = Syntax(
            code,
            lexer_name,
            theme=theme, # Syntax theme is used here
            line_numbers=line_numbers,
            word_wrap=word_wrap,
            background_color=background_color,
            **kwargs
        )
        self._console.print(syntax)

    def print_diff(
        self,
        diff_text: str,
        theme: str = "vim", # Default syntax theme, consistent with print_syntax
        line_numbers: bool = False, # Diffs usually don't have line numbers from the start of the diff
        word_wrap: bool = True, # Diffs can have long lines
        **kwargs: Any
    ):
        """
        Prints diff text with syntax highlighting.

        Args:
            diff_text (str): The diff text to highlight.
            theme (str, optional): The Pygments theme to use. Defaults to "vim".
            line_numbers (bool, optional): Whether to show line numbers. Defaults to False for diffs.
            word_wrap (bool, optional): Whether to wrap lines. Defaults to True for diffs.
            **kwargs: Additional arguments to pass to the `Syntax` constructor.
        """
        # Common lexer names for diffs are "diff" or "udiff"
        # Using "diff" as it's generally well-supported.
        self.print_syntax(
            diff_text,
            lexer_name="diff",
            theme=theme,
            line_numbers=line_numbers,
            word_wrap=word_wrap,
            **kwargs
        )

    def __getattr__(self, name):
        """Forward all other attribute access to the underlying console."""
        return getattr(self._console, name)


# Create the global QXConsole instance
qx_console = QXConsole(_initial_rich_console)


def show_spinner(
    message: str = "Thinking...",
    spinner_name: str = "dots",
    speed: float = 1.0,
    style: str = "status.spinner", # This style might be affected if not defined in a default theme
) -> Status:
    """
    Display a spinner with the given message using the global qx_console.
    The returned Status object should be managed (e.g., with a context manager)
    to ensure it's properly started and stopped.
    """
    # If "status.spinner" style was part of a custom theme, it might look different now,
    # or revert to Rich's default.
    # Consider defining a default style directly here if needed, or ensure Rich's default is acceptable.
    # Rich's default theme usually defines "status.spinner". If we added it to qx_theme,
    # that would take precedence.
    return qx_console.status(
        message,
        spinner=spinner_name,
        speed=speed,
        spinner_style=style, # Uses the 'style' argument passed or its default "status.spinner"
    )

# Example of using syntax highlighting (can be run if this file is executed directly)
if __name__ == "__main__":
    # Now uses the "info" style from qx_theme
    qx_console.print("[info]Testing syntax highlighting...[/info]")
    python_code_example = """
def hello_world():
    # This is a comment
    greeting = "Hello, syntax highlighting!"
    print(greeting)
    return 1 + 1
"""
    qx_console.print_syntax(python_code_example, "python", theme="vim", line_numbers=True)

    json_example = """
{
    "name": "QX Agent",
    "version": "1.0",
    "features": ["code generation", "syntax highlighting"],
    "active": true,
    "rating": null
}
"""
    qx_console.print_syntax(json_example, "json", theme="monokai", line_numbers=False, word_wrap=True)
    
    diff_example = """
--- a/file.txt
+++ b/file.txt
@@ -1,3 +1,4 @@
 Some text
 -This line is removed
 +This line is added
 Another line
 +A new line at the end
"""
    # Now uses the "info" style from qx_theme
    qx_console.print("[info]Testing diff highlighting...[/info]")
    qx_console.print_diff(diff_example)

    # Uses the "success" style from qx_theme (or "green" if "success" wasn't defined, but it is)
    qx_console.print("[success]Syntax highlighting and diff test finished.[/success]")
    
    # Test other styles
    qx_console.print("This is a normal print.")
    qx_console.print("This is an info message.", style="info")
    qx_console.print("This is a warning message.", style="warning")
    qx_console.print("This is a danger message.", style="danger")
    qx_console.print("This is a success message.", style="success")

    qx_console.print("[info]Info via markup.[/info]")
    qx_console.print("[warning]Warning via markup.[/warning]")
    qx_console.print("[danger]Danger via markup.[/danger]")
    qx_console.print("[success]Success via markup.[/success]")
