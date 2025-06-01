import logging
from typing import Optional, Any


def show_spinner(
    message: str = "Thinking...",
    spinner_name: str = "dots", 
    speed: float = 1.0,
    style: str = "status.spinner",
):
    """
    Show a spinner message in the console.
    Just prints a simple message now.
    """
    from rich.console import Console
    Console().print(f"[dim]{message}[/dim]")
    return None  # No status object to return
