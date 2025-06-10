#!/usr/bin/env python3

import sys
sys.path.insert(0, 'src')

from rich.console import Console
from rich.markdown import Markdown
from qx.cli.quote_bar_component import BorderedMarkdown

def test_background_colors():
    console = Console()
    
    print("Testing BorderedMarkdown background colors:")
    print("=" * 50)
    
    # Test 1: No background
    print("\n1. No background color:")
    md1 = BorderedMarkdown(
        Markdown("This is a test message without background color"),
        border_style="blue"
    )
    console.print(md1)
    
    # Test 2: With #050505 background
    print("\n2. With #050505 background color:")
    md2 = BorderedMarkdown(
        Markdown("This is a test message with #050505 background color"),
        border_style="blue",
        background_color="#050505"
    )
    console.print(md2)
    
    # Test 3: With red background for comparison
    print("\n3. With red background color for comparison:")
    md3 = BorderedMarkdown(
        Markdown("This is a test message with red background color"),
        border_style="blue", 
        background_color="red"
    )
    console.print(md3)
    
    # Test 4: With white background for comparison
    print("\n4. With white background color for comparison:")
    md4 = BorderedMarkdown(
        Markdown("This is a test message with white background color"),
        border_style="blue",
        background_color="white"
    )
    console.print(md4)

if __name__ == "__main__":
    test_background_colors()