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
        width: 100%;
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
    selected_index = reactive(0) # Default to 0
    
    def __init__(self, items: List[Tuple[str, str]], owner: Optional[Widget] = None, **kwargs):
        super().__init__(**kwargs)
        self.items = items
        self.owner = owner
        self.can_focus = True
        
    def _apply_selection_styles_and_scroll(self) -> None:
        """Helper to apply styles and scroll, ensuring widget is mounted and items exist."""
        if not self.is_mounted or not self.items:
            # If no items, still call _update_item_styles to clear any previous selection visuals
            if self.is_mounted:
                self._update_item_styles()
            return
        self._update_item_styles()
        self._scroll_selected_to_view()

    def on_mount(self) -> None:
        self.focus()
        # Defer the initial styling and scrolling until after the next refresh
        # This ensures that the DOM is fully updated and styles can be applied correctly.
        if self.items: # Only schedule if there are items to potentially select
            self.app.call_after_refresh(self._apply_selection_styles_and_scroll)
        else:
            # If no items on mount, ensure any residual styling is cleared
            self.app.call_after_refresh(self._update_item_styles)
        
    def watch_selected_index(self, old_index: int, new_index: int) -> None:
        # Called when selected_index changes. Apply styles directly.
        self._apply_selection_styles_and_scroll()
    
    def watch_items(self, old_items: list, new_items: list) -> None:
        """Called when items list changes."""
        # When items change (e.g., populated after mount or cleared),
        # reset selected_index to 0 if there are new items, and update styles.
        if new_items:
            if self.selected_index != 0:
                self.selected_index = 0 # This will trigger watch_selected_index
            else:
                # If selected_index is already 0, watch_selected_index won't fire, so call directly
                self._apply_selection_styles_and_scroll()
        else:
            # No items, clear selection visuals
            self.selected_index = -1 # Or some other indicator for no selection if 0 is valid for empty
            self._apply_selection_styles_and_scroll()

    def _scroll_selected_to_view(self) -> None:
        if not self.items or not self.is_mounted or self.selected_index < 0 or self.selected_index >= len(self.children):
            return
        try:
            if self.selected_index < len(self.children):
                 selected_widget = self.children[self.selected_index]
                 if isinstance(selected_widget, Static) and selected_widget.has_class("item"):
                    self.scroll_to_widget(selected_widget, animate=False, top=False)
        except Exception as e:
            self.log(f"Error scrolling to widget: {e}")

    def _update_item_styles(self) -> None:
        if not self.is_mounted: 
            return
        for i, child in enumerate(self.children):
            if isinstance(child, Static) and child.has_class(f"item-{i}"):
                if self.items and i == self.selected_index:
                    child.add_class("selected")
                else:
                    child.remove_class("selected")

    def compose(self) -> ComposeResult:
        for i, (name, type_) in enumerate(self.items):
            item_classes = f"item item-{i}" 
            yield Static(f"{name} [dim]{type_}[/dim]", classes=item_classes)
                
    def on_key(self, event: Key) -> None:
        self.log(f"CompletionMenu on_key received: {event.key}")

    def action_move_up(self):
        if self.items:
            self.selected_index = (self.selected_index - 1 + len(self.items)) % len(self.items)

    def action_move_down(self):
        if self.items:
            self.selected_index = (self.selected_index + 1) % len(self.items)

    def action_select_item(self):
        if self.items and 0 <= self.selected_index < len(self.items):
            message = self.ItemSelected(self.selected_index, self.items[self.selected_index][0], owner_widget=self.owner)
            if self.owner: 
                self.owner.post_message(message)
            else: 
                self.post_message(message)

    def action_cancel_selection(self):
        message = self.Cancelled(owner_widget=self.owner)
        if self.owner: 
            self.owner.post_message(message)
        else: 
            self.post_message(message)
