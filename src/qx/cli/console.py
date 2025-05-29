import logging
from typing import Optional, Any
from textual.app import App
from textual.containers import Vertical, Horizontal
from textual.widgets import Static, Input, RichLog
from textual.message import Message
from textual.reactive import reactive
from textual.binding import Binding
from textual import events

class TextualRichLogHandler(logging.Handler):
    """
    A logging handler that directs log records to a Textual RichLog widget
    via the QXConsole instance.
    """
    def __init__(self, qx_console_instance: 'QXConsole', level=logging.NOTSET):
        super().__init__(level=level)
        self.qx_console = qx_console_instance

    def emit(self, record):
        try:
            msg = self.format(record)
            # Use qx_console.print to output to the RichLog
            # We can add styling based on log level if needed
            if record.levelno >= logging.ERROR:
                self.qx_console.print(f"[red]{msg}[/red]")
            elif record.levelno >= logging.WARNING:
                self.qx_console.print(f"[yellow]{msg}[/yellow]")
            elif record.levelno >= logging.INFO:
                self.qx_console.print(f"[blue]{msg}[/blue]")
            else:
                self.qx_console.print(f"[dim]{msg}[/dim]")
        except Exception:
            self.handleError(record)

class QXConsole:
    """
    A wrapper around Textual widgets to provide QX-specific console utilities.
    """
    
    def __init__(self, app: Optional[App] = None):
        self._app = app
        self._output_widget: Optional[RichLog] = None
        self._input_widget: Optional[Input] = None
        self._logger: Optional[logging.Logger] = None # Add a logger attribute
        
    def set_widgets(self, output_widget: RichLog, input_widget: Input):
        """Set the output and input widgets."""
        self._output_widget = output_widget
        self._input_widget = input_widget

    def set_logger(self, logger: logging.Logger):
        """Set the logger instance to be used by the console."""
        self._logger = logger

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
