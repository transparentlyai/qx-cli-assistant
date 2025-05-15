import asyncio
from prompt_toolkit.shortcuts import prompt
from prompt_toolkit.formatted_text import HTML
from rich.console import Console as RichConsole # Explicit import for type hinting

async def get_user_input(console: RichConsole) -> str: # Use RichConsole for type hint
    """
    Asynchronously gets user input from the QX prompt using prompt_toolkit.

    Args:
        console: The Rich Console object. While prompt_toolkit handles its own
                 prompt styling, this console can be used for any messages
                 printed directly from this module.

    Returns:
        The string entered by the user.
    """
    # Rich markup "[bold cyan]Q⏵[/bold cyan] " translates to
    # prompt_toolkit HTML <style fg="ansicyan" bold="true">Q⏵ </style>
    # Note: 'ansicyan' is a standard ANSI color name.
    # The prompt style is defined by prompt_toolkit's HTML, not directly by the Rich theme.
    # However, if we wanted the prompt to match a theme color, we could fetch it:
    # prompt_style_str = console.theme.styles.get("prompt", "bold ansicyan") # Example
    # For now, keeping the hardcoded style for simplicity of prompt_toolkit integration.
    
    prompt_message = HTML('<style fg="ansicyan" bold="true">Q⏵ </style>')
    
    # prompt_toolkit.shortcuts.prompt is synchronous, so we run it in a thread.
    user_input = await asyncio.to_thread(prompt, prompt_message)
    return user_input