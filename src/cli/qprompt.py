import asyncio
from prompt_toolkit.shortcuts import prompt
from prompt_toolkit.formatted_text import HTML # For styled prompt
from rich.console import Console # Kept in signature for potential future use in this module

async def get_user_input(console: Console) -> str:
    """
    Asynchronously gets user input from the QX prompt using prompt_toolkit.

    Args:
        console: The Rich Console object (currently unused by prompt_toolkit.prompt).

    Returns:
        The string entered by the user.
    """
    # Rich markup "[bold cyan]Q⏵[/bold cyan] " translates to
    # prompt_toolkit HTML <style fg="ansicyan" bold="true">Q⏵ </style>
    # Note: 'ansicyan' is a standard ANSI color name.
    prompt_message = HTML('<style fg="ansicyan" bold="true">Q⏵ </style>')
    
    # prompt_toolkit.shortcuts.prompt is synchronous, so we run it in a thread.
    user_input = await asyncio.to_thread(prompt, prompt_message)
    return user_input