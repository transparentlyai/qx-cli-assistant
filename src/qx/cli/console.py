import os

from qx.cli.theme import themed_console


def show_spinner(
    message: str = " ",
    spinner_name: str = "point",
    speed: float = 2.0,
    style: str = "status.spinner",
):
    """
    Show a spinner message in the console.
    Respects the QX_SHOW_SPINNER environment variable.
    """
    if os.getenv("QX_SHOW_SPINNER", "true").lower() == "true":
        themed_console.print(message, style="spinner")
    return None  # No status object to return


__all__ = ["themed_console", "show_spinner"]
