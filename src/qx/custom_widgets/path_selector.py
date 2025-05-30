from textual.app import ComposeResult
from textual.containers import Vertical
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Input, Label
import os

class PathSelector(Widget):
    """
    A widget for selecting file system paths with autocompletion.
    """

    DEFAULT_CSS = """
    PathSelector {
        width: auto;
        height: auto;
        padding: 1;
        border: round $primary;
        border-title-align: center;
    }
    PathSelector > Vertical {
        width: auto;
        height: auto;
    }
    Input {
        width: 100%;
        margin-bottom: 1;
    }
    Label {
        width: 100%;
        padding: 0 1;
    }
    Label.selected {
        background: $secondary;
        color: $text;
    }
    """

    path_input: reactive[str] = reactive("")
    selected_path: reactive[str | None] = reactive(None)

    def __init__(
        self,
        initial_path: str = "",
        *args,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
        border_title: str | None = "Select Path",
    ) -> None:
        super().__init__(name=name, id=id, classes=classes, disabled=disabled)
        self.path_input = initial_path
        self.border_title = border_title
        self._options: list[tuple[str, str]] = []
        self._option_labels: list[Label] = []
        self._selected_index: int = 0

    def compose(self) -> ComposeResult:
        yield Input(value=self.path_input, placeholder="Enter path...", id="path_input")
        with Vertical(id="options_container"):
            pass # Options will be dynamically added here

    def on_mount(self) -> None:
        self.query_one("#path_input", Input).focus()
        self._update_options()

    def on_input_changed(self, event: Input.Changed) -> None:
        self.path_input = event.value
        self._update_options()

    def _update_options(self) -> None:
        # This method will be implemented to list files/directories
        # For now, a placeholder
        self._options = []
        current_dir = os.path.dirname(self.path_input) if self.path_input else "."
        if not current_dir:
            current_dir = "."
        
        try:
            items = os.listdir(current_dir)
            matching_items = []
            input_basename = os.path.basename(self.path_input)

            for item in items:
                full_path = os.path.join(current_dir, item)
                if item.lower().startswith(input_basename.lower()):
                    display_text = item
                    if os.path.isdir(full_path):
                        display_text += "/"
                    matching_items.append((display_text, full_path))
            
            self._options = sorted(matching_items, key=lambda x: (not os.path.isdir(x[1]), x[0].lower()))

        except OSError:
            self._options = [] # Handle cases where path is invalid or not accessible

        self._recompose_options()
        self._update_selection_display()

    def _recompose_options(self) -> None:
        options_container = self.query_one("#options_container", Vertical)
        options_container.remove_children()
        self._option_labels = []
        for text, key in self._options:
            label = Label(text)
            self._option_labels.append(label)
            options_container.mount(label)
        self._selected_index = 0 if self._options else -1

    def _update_selection_display(self) -> None:
        for i, label in enumerate(self._option_labels):
            label.remove_class("selected")
            if i == self._selected_index:
                label.add_class("selected")
                # Ensure the selected item is visible
                options_container = self.query_one("#options_container", Vertical)
                if options_container:
                    options_container.scroll_to_widget(label, animate=False)

    def on_key(self, event) -> None:
        if not hasattr(event, 'key'):
            return

        key_char = event.key.lower()

        if key_char == "up":
            if self._options:
                self._selected_index = (self._selected_index - 1 + len(self._options)) % len(self._options)
                self._update_selection_display()
            event.stop()
        elif key_char == "down":
            if self._options:
                self._selected_index = (self._selected_index + 1) % len(self._options)
                self._update_selection_display()
            event.stop()
        elif key_char == "enter":
            if self._selected_index != -1 and self._options:
                selected_display_text, selected_full_path = self._options[self._selected_index]
                self.query_one("#path_input", Input).value = selected_full_path
                self.path_input = selected_full_path
                self.selected_path = selected_full_path
                self._update_options() # Re-filter based on the selected full path
            event.stop()
        elif key_char == "tab":
            if self._selected_index != -1 and self._options:
                selected_display_text, selected_full_path = self._options[self._selected_index]
                self.query_one("#path_input", Input).value = selected_full_path
                self.path_input = selected_full_path
                self._update_options() # Re-filter based on the selected full path
            event.stop()
