from textual.app import ComposeResult
from textual.widgets import Static
from textual.containers import Vertical
from textual.reactive import reactive
from textual.message import Message

class SimpleSelector(Static):
    """A simple selection widget for a list of items with descriptions."""

    DEFAULT_CSS = """
    SimpleSelector {
        height: auto;
        width: auto;
        border: none; /* No borders as requested */
    }
    SimpleSelector:focus { /* Added focus style */
        border: round blue;
    }
    SimpleSelector .item {
        padding: 0 1;
        height: 1;
        width: 100%;
        text-align: left;
    }
    SimpleSelector .item.selected {
        background: #666666; /* Highlight selected item */
        color: white;
    }
    SimpleSelector .item.selected .description {
        color: #DDDDDD; /* Slightly different color for description when selected */
    }
    SimpleSelector .description {
        color: #AAAAAA; /* Default color for description */
        text-align: right;
        width: auto;
        padding-left: 2;
    }
    """

    CSS_PATH = "" # This will be set by the user if they want to load external CSS

    can_focus = True

    class Selected(Message):
        """Posted when a new item is selected."""
        def __init__(self, item: str, description: str, index: int) -> None:
            super().__init__()
            self.item = item
            self.description = description
            self.index = index

    items: reactive[list[tuple[str, str]]] = reactive([])
    selected_index: reactive[int] = reactive(0)

    def __init__(self, items: list[tuple[str, str]], css_path: str = "", id: str | None = None, classes: str | None = None) -> None:
        super().__init__(id=id, classes=classes)
        self.items = items
        if css_path:
            self.CSS_PATH = css_path
        if not self.items:
            self.selected_index = -1 # No selection if no items
        else:
            self.selected_index = 0

    def watch_items(self, old_items: list[tuple[str, str]], new_items: list[tuple[str, str]]) -> None:
        """Called when items changes."""
        self.refresh()
        if not new_items:
            self.selected_index = -1
        elif self.selected_index == -1:
            self.selected_index = 0
        elif self.selected_index >= len(new_items):
            self.selected_index = len(new_items) - 1

    def watch_selected_index(self, old_index: int, new_index: int) -> None:
        """Called when selected_index changes."""
        self.refresh()
        if 0 <= new_index < len(self.items):
            item, description = self.items[new_index]
            self.post_message(self.Selected(item, description, new_index))

    def compose(self) -> ComposeResult:
        """Create child widgets for the selector."""
        with Vertical():
            for i, (item, description) in enumerate(self.items):
                class_name = "item selected" if i == self.selected_index else "item"
                yield Static(f"{item} [dim]{description}[/dim]", classes=class_name)

    def on_key(self, event) -> None:
        """Handle key presses for navigation."""
        print(f"DEBUG: SimpleSelector on_key received event: {event}") # Added for debugging
        if not self.items:
            return

        if event.key == "up":
            self.selected_index = (self.selected_index - 1 + len(self.items)) % len(self.items)
            event.stop()
        elif event.key == "down":
            self.selected_index = (self.selected_index + 1) % len(self.items)
            event.stop()
        elif event.key == "tab":
            # Safely check for shift key, default to False if attribute doesn't exist
            is_shift_pressed = getattr(event, 'shift', False) or getattr(event, 'shift_key', False)
            if is_shift_pressed:
                self.selected_index = (self.selected_index - 1 + len(self.items)) % len(self.items)
            else:
                self.selected_index = (self.selected_index + 1) % len(self.items)
            event.stop()
