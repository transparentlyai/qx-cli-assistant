"""Messages for LLM streaming and rendering."""
from typing import Optional
from textual.message import Message


class RenderStreamContent(Message):
    """Posted when LLM streaming content needs to be rendered."""
    
    def __init__(self, content: str, is_markdown: bool = True, end: str = ""):
        self.content = content
        self.is_markdown = is_markdown
        self.end = end
        super().__init__()


class StreamingComplete(Message):
    """Posted when LLM streaming is complete."""
    
    def __init__(self, add_newline: bool = True):
        self.add_newline = add_newline
        super().__init__()