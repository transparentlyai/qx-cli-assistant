from textual.widgets import Static
from textual.widget import Widget
from textual.containers import VerticalScroll
from textual.reactive import reactive
from textual.app import ComposeResult
from textual.message import Message
from textual.binding import Binding
from textual.events import Key
from typing import Optional, List, Tuple


class CompletionMenu(VerticalScroll):
    """A simple completion menu for displaying path options."""
    
    DEFAULT_CSS = """
    CompletionMenu {
        height: auto;
        max-height: 10;
        overflow-y: auto;
        width: 100%; /* Changed from auto to 100% */
        background: #1e1e1e;
        border: round #0087ff;
        padding: 0;
    }
    
    CompletionMenu:focus {
        border: round #00ff00;
    }
    
    CompletionMenu > .item {
        padding: 0 1;
        width: 100%;
        height: 1;
    }
    
    CompletionMenu > .item.selected {
        background: #0087ff;
        color: white;
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
        def __init__(self, index: int, item: str, owner_widget: Optional[Widget] = None):
            super().__init__()
            self.index = index
            self.item = item
            self.owner_widget = owner_widget
    
    class Cancelled(Message):
        def __init__(self, owner_widget: Optional[Widget] = None):
            super().__init__()
            self.owner_widget = owner_widget
    
    items = reactive([]) 
    selected_index = reactive(0)
    
    def __init__(self, items: List[Tuple[str, str]], owner: Optional[Widget] = None, **kwargs):
        super().__init__(**kwargs)
        self.items = items
        self.owner = owner # This is the ExtendedInput instance
        self.can_focus = True
        
    def on_mount(self) -> None:
        self.focus()
        self._update_item_styles() # Apply initial styling
        self._scroll_selected_to_view() # Scroll to initially selected item
        
    def watch_selected_index(self, old_index: int, new_index: int) -> None:
        if not self.is_mounted:
            return # Don't try to query or scroll if not mounted
        self._update_item_styles()
        self._scroll_selected_to_view()

    def _scroll_selected_to_view(self) -> None:
        """Scrolls the currently selected item into view."""
        if not self.items: # No items, nothing to scroll to
            return
        try:
            selected_widget = self.query(f".item-{self.selected_index}").first()
            if selected_widget:
                self.scroll_to_widget(selected_widget, animate=False, top=False) # top=False to center if possible
        except Exception as e:
            self.log(f"Error scrolling to widget: {e}")

    def _update_item_styles(self) -> None:
        """Updates the styles of items based on selection."""
        if not self.is_mounted: # Ensure children are available
            return
        for i, child in enumerate(self.children):
            # Check if child is a Static widget and has the item-i class
            if isinstance(child, Static) and child.has_class(f"item-{i}"):
                if i == self.selected_index:
                    child.add_class("selected")
                else:
                    child.remove_class("selected")

    def compose(self) -> ComposeResult:
        for i, (name, type_) in enumerate(self.items):
            item_classes = f"item item-{i}" # Assign item-i class here
            # Initial selection style is handled by _update_item_styles in on_mount
            yield Static(f"{name} [dim]{type_}[/dim]", classes=item_classes)
                
    def on_key(self, event: Key) -> None:
        self.log(f"CompletionMenu on_key received: {event.key}")

    def action_move_up(self):
        self.log("CompletionMenu Action: move_up")
        if self.items:
            self.selected_index = (self.selected_index - 1 + len(self.items)) % len(self.items)

    def action_move_down(self):
        self.log("CompletionMenu Action: move_down")
        if self.items:
            self.selected_index = (self.selected_index + 1) % len(self.items)

    def action_select_item(self):
        self.log("CompletionMenu Action: select_item")
        if self.items and 0 <= self.selected_index < len(self.items):
            message = self.ItemSelected(self.selected_index, self.items[self.selected_index][0], owner_widget=self.owner)
            if self.owner: # If owner (ExtendedInput) is set, post message via owner
                self.owner.post_message(message)
            else: # Fallback if no owner (should not happen in normal QXApp flow)
                self.post_message(message)

    def action_cancel_selection(self):
        self.log("CompletionMenu Action: cancel_selection")
        message = self.Cancelled(owner_widget=self.owner)
        if self.owner: # If owner (ExtendedInput) is set, post message via owner
            self.owner.post_message(message)
        else: # Fallback
            self.post_message(message)
