from textual.widgets import Static
from textual.widget import Widget # Corrected import for Widget
from textual.containers import Vertical
from textual.reactive import reactive
from textual.app import ComposeResult
from textual.message import Message
from textual.binding import Binding
from textual.events import Key
from typing import Optional, List, Tuple


class CompletionMenu(Static):
    """A simple completion menu for displaying path options."""
    
    DEFAULT_CSS = """
    CompletionMenu {
        height: auto;
        max-height: 10;
        width: auto;
        background: #1e1e1e;
        border: round #0087ff;
        padding: 0;
    }
    
    CompletionMenu:focus {
        border: round #00ff00;
    }
    
    CompletionMenu .item {
        padding: 0 1;
        width: 100%;
    }
    
    CompletionMenu .item.selected {
        background: #0087ff;
        color: white;
    }
    
    CompletionMenu .type {
        color: #666666;
    }
    
    CompletionMenu .item.selected .type {
        color: #cccccc;
    }
    """
    
    BINDINGS = [
        Binding("up", "move_up", "Up"),
        Binding("down", "move_down", "Down"),
        Binding("tab", "move_down", "Tab"), 
        Binding("enter", "select_item", "Select"),
        Binding("escape", "cancel_selection", "Cancel"),
    ]
    
    class ItemSelected(Message):
        def __init__(self, index: int, item: str):
            super().__init__()
            self.index = index
            self.item = item
    
    class Cancelled(Message):
        pass
    
    items = reactive([])
    selected_index = reactive(0, recompose=True)
    
    def __init__(self, items: List[Tuple[str, str]], owner: Optional[Widget] = None, **kwargs):
        super().__init__(**kwargs)
        self.items = items
        self.owner = owner # Store the owner widget
        self.can_focus = True
        
    def on_mount(self):
        self.focus()
        
    def watch_selected_index(self):
        self.refresh()
        
    def compose(self) -> ComposeResult:
        with Vertical():
            for i, (name, type_) in enumerate(self.items):
                classes = "item selected" if i == self.selected_index else "item"
                yield Static(f"{name} [dim]{type_}[/dim]", classes=classes)
                
    def on_key(self, event: Key) -> None:
        self.log(f"CompletionMenu on_key received: {event.key}")

    def action_move_up(self):
        self.log("CompletionMenu Action: move_up")
        if self.items:
            self.selected_index = (self.selected_index - 1) % len(self.items)

    def action_move_down(self):
        self.log("CompletionMenu Action: move_down")
        if self.items:
            self.selected_index = (self.selected_index + 1) % len(self.items)

    def action_select_item(self):
        self.log("CompletionMenu Action: select_item")
        if self.items and 0 <= self.selected_index < len(self.items):
            message = self.ItemSelected(self.selected_index, self.items[self.selected_index][0])
            if self.owner:
                self.owner.post_message(message)
            else:
                self.post_message(message)

    def action_cancel_selection(self):
        self.log("CompletionMenu Action: cancel_selection")
        message = self.Cancelled()
        if self.owner:
            self.owner.post_message(message)
        else:
            self.post_message(message)
