#!/usr/bin/env python3

import sys
sys.path.insert(0, 'src')
import os

# Force color support
os.environ['FORCE_COLOR'] = '1'
os.environ['COLORTERM'] = 'truecolor'

from rich.console import Console
from rich.markdown import Markdown
from qx.cli.quote_bar_component import BorderedMarkdown

def test_forced_colors():
    print("Testing with forced color support:")
    
    # Create console with forced color support
    console = Console(force_terminal=True, color_system="truecolor")
    
    print(f"Console color system: {console.color_system}")
    print(f"Console is terminal: {console.is_terminal}")
    print("=" * 50)
    
    # Test BorderedMarkdown with background
    print("\nBorderedMarkdown with forced colors:")
    
    md1 = BorderedMarkdown(
        Markdown("**This should have #050505 background**"),
        border_style="blue",
        background_color="#050505"
    )
    console.print(md1)
    
    md2 = BorderedMarkdown(
        Markdown("**This should have red background**"),
        border_style="blue",
        background_color="red"
    )
    console.print(md2)
    
    # Test direct style application
    print("\nDirect style with forced colors:")
    console.print("Direct #050505 background", style="on #050505")
    console.print("Direct red background", style="on red")

if __name__ == "__main__":
    test_forced_colors()