from rich.console import Console, Group
from rich.markdown import Markdown
from rich.segment import Segment
from rich.style import Style
from rich.text import Text
from rich.theme import Theme
import hashlib
from typing import Optional


class BorderedMarkdown:
    """A class to render Markdown with a left border."""

    def __init__(
        self, markdown, border_char="▊", border_style="none", background_color=None
    ):
        self.markdown = markdown
        self.border_char = border_char
        self.border_style = Style.parse(border_style)
        self.background_style = (
            Style(bgcolor=background_color) if background_color else Style()
        )

    def __rich_console__(self, console, options):
        lines = console.render_lines(self.markdown, options)
        border_segment = Segment(
            self.border_char + " ", self.border_style + self.background_style
        )

        for line in lines:
            yield border_segment
            for segment in line:
                yield Segment(segment.text, self.background_style + segment.style)

            # Fill the rest of the line with the background color
            line_length = Segment.get_line_length(line)
            fill_width = options.max_width - line_length - (len(self.border_char) + 1)
            if fill_width > 0:
                yield Segment(" " * fill_width, self.background_style)
            yield Segment.line()


def render_markdown_with_left_border(
    markdown_text: str,
    border_color: str,
    background_color: str | None = None,
    border_char: str = "▊",
    title: str | None = None,
):
    """
    Renders Markdown text with a left border that spans the full height.

    Args:
        markdown_text (str): The Markdown text to render.
        border_color (str): The color of the left border.
        background_color (str | None): The background color.
        border_char (str): The character to use for the border.
        title (str | None): An optional title to display.
    """
    # Create a custom theme to override the h1 style and define the code style.
    custom_theme = Theme(
        {
            "markdown.h1": Style(bold=True, underline=True),
            "markdown.code": Style(bold=True, color="cyan"),
        }
    )
    console = Console(theme=custom_theme)

    if title:
        console.print(Text(title, style="bold"))
        console.print(Text("─" * len(title), style=border_color))

    # Manually process heading to avoid the default box
    lines = markdown_text.strip().split("\n")
    heading = None
    if lines and lines[0].startswith("# "):
        heading_text = lines[0][2:]
        heading = Text(heading_text, style="bold underline")
        lines = lines[1:]
        markdown_text = "\n".join(lines)

    md = Markdown(markdown_text)
    renderable = Group(heading, md) if heading else md

    bordered_md = BorderedMarkdown(
        renderable,
        border_char=border_char,
        border_style=border_color,
        background_color=background_color,
    )
    console.print(bordered_md)


def get_agent_color(agent_name: str, agent_color: Optional[str] = None) -> str:
    """
    Get the color for an agent, using the provided color or picking from random colors.
    
    Args:
        agent_name (str): The name of the agent
        agent_color (Optional[str]): The color from agent YAML config (if any)
    
    Returns:
        str: The color to use for the agent
    """
    if agent_color:
        return agent_color
    
    # Import here to avoid circular imports
    from qx.core.constants import RANDOM_AGENT_COLORS
    
    # Use hash of agent name to consistently pick the same color
    name_hash = hashlib.md5(agent_name.encode()).hexdigest()
    color_index = int(name_hash[:8], 16) % len(RANDOM_AGENT_COLORS)
    return RANDOM_AGENT_COLORS[color_index]


def render_agent_markdown(
    markdown_text: str,
    agent_name: str,
    agent_color: Optional[str] = None,
    background_color: Optional[str] = None,
    border_char: str = "▊",
    console: Optional[Console] = None,
) -> None:
    """
    Renders agent markdown with a left border and agent name as title.
    
    Args:
        markdown_text (str): The Markdown text to render.
        agent_name (str): The name of the agent.
        agent_color (Optional[str]): The color from agent config (if any).
        background_color (Optional[str]): The background color.
        border_char (str): The character to use for the border.
        console (Optional[Console]): Console instance to use for rendering.
    """
    color = get_agent_color(agent_name, agent_color)
    
    # Use provided console or create new one
    if console is None:
        # Create a custom theme to override the h1 style and define the code style.
        custom_theme = Theme(
            {
                "markdown.h1": Style(bold=True, underline=True),
                "markdown.code": Style(bold=True, color="cyan"),
            }
        )
        console = Console(theme=custom_theme)
    
    # Display agent name as title
    console.print(Text(agent_name, style="bold"))
    console.print(Text("─" * len(agent_name), style=color))
    
    # Manually process heading to avoid the default box
    lines = markdown_text.strip().split("\n")
    heading = None
    if lines and lines[0].startswith("# "):
        heading_text = lines[0][2:]
        heading = Text(heading_text, style="bold underline")
        lines = lines[1:]
        markdown_text = "\n".join(lines)
    
    md = Markdown(markdown_text)
    renderable = Group(heading, md) if heading else md
    
    bordered_md = BorderedMarkdown(
        renderable,
        border_char=border_char,
        border_style=color,
        background_color=background_color,
    )
    console.print(bordered_md)


def render_agent_permission_request(
    request_text: str,
    agent_name: str,
    agent_color: Optional[str] = None,
    console: Optional[Console] = None,
    additional_content = None,
) -> None:
    """
    Renders agent permission request with a left border and agent name.
    
    Args:
        request_text (str): The permission request text.
        agent_name (str): The name of the agent.
        agent_color (Optional[str]): The color from agent config (if any).
        console (Optional[Console]): Console instance to use for rendering.
        additional_content: Additional Rich renderable content to display.
    """
    color = get_agent_color(agent_name, agent_color)
    
    if console is None:
        console = Console()
    
    # Format the main permission request
    formatted_text = f"Permission Request from {agent_name}\n\n{request_text}"
    
    # Create the main markdown content
    main_content = Markdown(formatted_text)
    
    # If there's additional content, create a group with both
    if additional_content is not None:
        from rich.console import Group
        content_to_render = Group(main_content, "", additional_content)  # Empty string adds spacing
    else:
        content_to_render = main_content
    
    bordered_md = BorderedMarkdown(
        content_to_render,
        border_char="▊",
        border_style=color,
        background_color="#050505",
    )
    console.print(bordered_md)


if __name__ == "__main__":
    md_content = """
# This is a heading

This is some **bold** and *italic* text.

- list item 1
- list item 2

`some code`
"""
    print("--- Without background color ---")
    render_markdown_with_left_border(md_content, "blue")
    print("\n--- With background color ---")
    render_markdown_with_left_border(md_content, "blue", background_color="grey23")
    print("\n--- With custom border character ---")
    render_markdown_with_left_border(md_content, "red", border_char="|")
    print("\n--- With a title ---")
    render_markdown_with_left_border(md_content, "green", title="This is a Title")
    print("\n--- Agent response example ---")
    render_agent_markdown(md_content, "code_reviewer", "#0087ff")
    print("\n--- Permission request example ---")
    render_agent_permission_request("I need permission to write to the file config.py", "devops_automation")
    print("\n--- Permission request with additional content ---")
    from rich.syntax import Syntax
    code_content = Syntax("print('Hello, World!')", "python", theme="monokai")
    render_agent_permission_request("Create file\n\npath: `/tmp/hello.py`", "Qx", "#ff5f00", additional_content=code_content)
