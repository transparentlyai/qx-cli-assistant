#!/usr/bin/env python3
"""
Rich Markdown Heading Alignment Control

This module demonstrates different approaches to controlling the alignment of headings
in Rich's Markdown component, including a custom BorderedMarkdown class that forces
left alignment for all heading levels.
"""

from rich.console import Console, ConsoleOptions, RenderResult, Segment
from rich.markdown import Markdown
from rich.panel import Panel
from rich.style import Style

class LeftAlignedMarkdown(Markdown):
    """
    Custom Markdown class that forces left alignment for all headings.
    
    This class overrides the Rich Markdown renderer to:
    1. Force H1 headings (rules) to be left-aligned
    2. Force H2/H3 headings (styled text) to be left-aligned
    3. Keep all other content unchanged
    """
    
    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        """Override rendering to force left alignment for headings."""
        segments = list(super().__rich_console__(console, options))
        
        modified_segments = []
        i = 0
        
        while i < len(segments):
            segment = segments[i]
            
            # Handle H1 headings (rendered as rules with ┏━...━┓)
            if segment.text.startswith('┏━'):
                modified_segments.append(segment)  # Top border
                i += 1
                
                # Skip newline after top border
                if i < len(segments) and segments[i].text == '\n':
                    modified_segments.append(segments[i])
                    i += 1
                
                # Process the title line and make it left-aligned
                if i < len(segments) and segments[i].text == '┃':
                    modified_segments.append(segments[i])  # Opening ┃
                    i += 1
                    
                    # Add minimal space
                    modified_segments.append(Segment(' '))
                    
                    # Skip any existing spaces and find the heading text
                    while i < len(segments) and segments[i].text == ' ':
                        i += 1
                    
                    # Add the heading text
                    if i < len(segments) and segments[i].style and segments[i].style.bold:
                        modified_segments.append(segments[i])
                        i += 1
                    
                    # Skip spaces and add minimal space before closing ┃
                    while i < len(segments) and segments[i].text == ' ':
                        i += 1
                    
                    # Add minimal space and closing ┃
                    modified_segments.append(Segment(' '))
                    if i < len(segments) and segments[i].text == '┃':
                        modified_segments.append(segments[i])
                        i += 1
                    
                    # Add newline
                    if i < len(segments) and segments[i].text == '\n':
                        modified_segments.append(segments[i])
                        i += 1
                
                continue
            
            # Handle H2/H3 headings (bold text with centering spaces)
            elif (segment.text and not segment.text.strip() and 
                  i + 1 < len(segments) and 
                  segments[i + 1].style and 
                  segments[i + 1].style.bold and 
                  segments[i + 1].text.strip() and
                  not segments[i + 1].text.startswith('┃')):  # Make sure it's not part of H1
                
                # Skip the leading spaces
                i += 1
                
                # Add the heading text left-aligned (no leading spaces)
                if i < len(segments):
                    heading_segment = segments[i]
                    modified_segments.append(Segment(heading_segment.text.strip(), heading_segment.style))
                    i += 1
                    
                    # Skip trailing spaces and add newline
                    while i < len(segments) and segments[i].text and not segments[i].text.strip():
                        if segments[i].text == '\n':
                            modified_segments.append(segments[i])
                            break
                        i += 1
                
                continue
            
            # For all other segments, keep as is
            modified_segments.append(segment)
            i += 1
        
        yield from modified_segments

def demonstrate_markdown_alignment():
    """Demonstrate the different approaches to controlling markdown heading alignment."""
    console = Console(width=70)
    
    markdown_text = """
# Main Title: This is a Level 1 Heading

This is a paragraph of text that follows the main heading. It should wrap normally and demonstrate how the regular text flows.

## Subtitle: This is a Level 2 Heading

Here's another paragraph to show how H2 headings look compared to H1 headings.

### Section: This is a Level 3 Heading

And here's some text after an H3 heading to complete our example.

#### Small Header: This is a Level 4 Heading

Final text content.
"""
    
    console.print("🔍 [bold blue]Rich Markdown Heading Alignment Demonstration[/bold blue]\n")
    
    # 1. Default Rich Markdown (centered headings)
    console.print("[bold green]1. Default Rich Markdown (Centered Headings):[/bold green]")
    default_md = Markdown(markdown_text)
    console.print(Panel(default_md, border_style="blue", title="Default"))
    console.print()
    
    # 2. Markdown with justify='left' parameter
    console.print("[bold green]2. Rich Markdown with justify='left':[/bold green]")
    left_justified_md = Markdown(markdown_text, justify='left')
    console.print(Panel(left_justified_md, border_style="yellow", title="justify='left'"))
    console.print()
    
    # 3. Custom LeftAlignedMarkdown class
    console.print("[bold green]3. Custom LeftAlignedMarkdown Class:[/bold green]")
    custom_md = LeftAlignedMarkdown(markdown_text)
    console.print(Panel(custom_md, border_style="green", title="LeftAlignedMarkdown"))
    console.print()
    
    # 4. Command line usage example
    console.print("[bold green]4. Command Line Usage Examples:[/bold green]")
    console.print(Panel(
        """[cyan]# Display markdown with default formatting[/cyan]
python -m rich.markdown README.md

[cyan]# Display markdown with full justification[/cyan]
python -m rich.markdown -j README.md

[cyan]# Display markdown with custom width[/cyan]
python -m rich.markdown -w 80 README.md""",
        border_style="magenta",
        title="CLI Examples"
    ))

if __name__ == "__main__":
    demonstrate_markdown_alignment()