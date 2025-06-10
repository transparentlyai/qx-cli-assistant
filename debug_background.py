#!/usr/bin/env python3

import sys
sys.path.insert(0, 'src')
import os

from rich.console import Console
from rich.style import Style
from rich.segment import Segment

def debug_background_style():
    print("Terminal Environment Debug:")
    print(f"TERM: {os.environ.get('TERM', 'not set')}")
    print(f"COLORTERM: {os.environ.get('COLORTERM', 'not set')}")
    print(f"FORCE_COLOR: {os.environ.get('FORCE_COLOR', 'not set')}")
    
    console = Console()
    print(f"Console color system: {console.color_system}")
    print(f"Console legacy windows: {console.legacy_windows}")
    print(f"Console is terminal: {console.is_terminal}")
    print("=" * 50)
    
    # Test Style creation
    print("\nStyle object debug:")
    style1 = Style(bgcolor="#050505")
    style2 = Style(bgcolor="red") 
    style3 = Style(bgcolor="yellow")
    
    print(f"Style with #050505: {style1}")
    print(f"Style with red: {style2}")
    print(f"Style with yellow: {style3}")
    
    # Test rendering these styles directly
    print("\nDirect style rendering:")
    console.print("Text with #050505 background", style=style1)
    console.print("Text with red background", style=style2)
    console.print("Text with yellow background", style=style3)
    
    # Test segment creation
    print("\nSegment debug:")
    seg1 = Segment("Test text", style1)
    seg2 = Segment("Test text", style2)
    seg3 = Segment("Test text", style3)
    
    print(f"Segment 1 style: {seg1.style}")
    print(f"Segment 2 style: {seg2.style}")  
    print(f"Segment 3 style: {seg3.style}")
    
    console.print(seg1, end="")
    print(" <- #050505")
    console.print(seg2, end="")
    print(" <- red")
    console.print(seg3, end="")
    print(" <- yellow")

if __name__ == "__main__":
    debug_background_style()