import logging
from typing import Optional, Any
from textual.app import App
from textual.containers import Vertical, Horizontal
from textual.widgets import Static, Input, RichLog
from textual.message import Message
from textual.reactive import reactive
from textual.binding import Binding
from textual import events

class QXConsole:
    """
    A wrapper around Textual widgets to provide QX-specific console utilities.
    """
    
    def __init__(self, app: Optional[App] = None):
        self._app = app
        self._output_widget: Optional[RichLog] = None
        self._input_widget: Optional[Input] = None
        
    def set_widgets(self, output_widget: RichLog, input_widget: Input):
        """Set the output and input widgets."""
        self._output_widget = output_widget
        self._input_widget = input_widget

    def print(self, *args, **kwargs):
        """
        Prints to the console using the RichLog widget or standard output.
        """
        if self._output_widget:
            # Convert args to a single string message
            message = " ".join(str(arg) for arg in args)
            self._output_widget.write(message, **kwargs)
        else:
            # Fallback to standard print
            print(*args, **kwargs)

    def clear(self):
        """
        Clears the output widget or terminal.
        """
        if self._output_widget:
            self._output_widget.clear()
        else:
            # Fallback to clearing terminal
            import os
            os.system('clear' if os.name == 'posix' else 'cls')

    def print_syntax(
        self,
        code: str,
        lexer_name: str,
        theme: str = "vim",
        line_numbers: bool = True,
        word_wrap: bool = False,
        background_color: Optional[str] = None,
        **kwargs: Any
    ):
        """
        Prints code with syntax highlighting using RichLog.
        """
        if self._output_widget:
            from rich.syntax import Syntax
            syntax = Syntax(
                code,
                lexer_name,
                theme=theme,
                line_numbers=line_numbers,
                word_wrap=word_wrap,
                background_color=background_color,
                **kwargs
            )
            self._output_widget.write(syntax)

    def print_diff(
        self,
        diff_text: str,
        theme: str = "vim",
        line_numbers: bool = False,
        word_wrap: bool = True,
        **kwargs: Any
    ):
        """
        Prints diff text with syntax highlighting.
        """
        self.print_syntax(
            diff_text,
            lexer_name="diff",
            theme=theme,
            line_numbers=line_numbers,
            word_wrap=word_wrap,
            **kwargs
        )

    def input(self, prompt: str = "", *, password: bool = False) -> str:
        """
        Gets input from the user using the Input widget.
        This is a placeholder - actual input handling is done in the app.
        """
        if self._input_widget:
            if prompt:
                self.print(prompt)
            return ""  # This will be handled by the app's input handling
        return ""


# Global console instance - will be initialized by the app
qx_console = QXConsole()


def show_spinner(
    message: str = "Thinking...",
    spinner_name: str = "dots",
    speed: float = 1.0,
    style: str = "status.spinner",
):
    """
    Show a spinner message in the console.
    In Textual, this is just a print message.
    """
    qx_console.print(f"[dim]{message}[/dim]")
    return None  # No status object to return