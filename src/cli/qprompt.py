import asyncio # Added import
from rich.prompt import Prompt
from rich.console import Console

async def get_user_input(console: Console) -> str:
    """
    Asynchronously gets user input from the QX prompt.

    Args:
        console: The Rich Console object for displaying the prompt.

    Returns:
        The string entered by the user.
    """
    # Changed to use asyncio.to_thread for the synchronous Prompt.ask
    user_input = await asyncio.to_thread(Prompt.ask, "[bold cyan]Q⏵[/bold cyan] ", console=console)
    return user_input