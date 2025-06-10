#!/usr/bin/env python3

import sys
sys.path.insert(0, 'src')

from rich.console import Console
from rich.markdown import Markdown
from rich.style import Style
from qx.cli.quote_bar_component import BorderedMarkdown

def test_rich_background():
    console = Console()
    
    print("Testing if Rich background colors work at all:")
    print("=" * 50)
    
    # Test Rich's built-in background support
    print("\n1. Rich built-in background test:")
    console.print("This should have yellow background", style="on yellow")
    console.print("This should have red background", style="on red")
    console.print("This should have blue background", style="on blue")
    
    # Test BorderedMarkdown with obvious colors
    print("\n2. BorderedMarkdown with obvious background colors:")
    
    md_yellow = BorderedMarkdown(
        Markdown("**Yellow background test**"),
        border_style="black",
        background_color="yellow"
    )
    console.print(md_yellow)
    
    md_cyan = BorderedMarkdown(
        Markdown("**Cyan background test**"),
        border_style="black", 
        background_color="cyan"
    )
    console.print(md_cyan)
    
    md_magenta = BorderedMarkdown(
        Markdown("**Magenta background test**"),
        border_style="white",
        background_color="magenta"
    )
    console.print(md_magenta)
    
    # Test the actual #050505 color
    print("\n3. Testing the actual #050505 color:")
    md_dark = BorderedMarkdown(
        Markdown("**#050505 background test - this might be hard to see**"),
        border_style="white",
        background_color="#050505"
    )
    console.print(md_dark)

if __name__ == "__main__":
    test_rich_background()