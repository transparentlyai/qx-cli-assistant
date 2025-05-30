from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static
from textual.containers import Container
from qx.custom_widgets.simple_selector import SimpleSelector

class SimpleSelectorExampleApp(App):
    """A simple Textual app to demonstrate the SimpleSelector widget."""

    BINDINGS = [
        ("d", "toggle_dark", "Toggle dark mode"),
    ]

    def compose(self) -> ComposeResult:
        items = [
            ("Apple", "A round fruit"),
            ("Banana", "A long yellow fruit"),
            ("Cherry", "A small red fruit"),
            ("Date", "A sweet, edible fruit"),
            ("Elderberry", "A dark purple berry"),
        ]
        yield Header()
        with Container():
            yield Static("Select an item:", classes="title")
            yield SimpleSelector(items, id="my_selector")
            yield Static("Selected: ", id="selected_output")
        yield Footer()

    def on_simple_selector_selected(self, message: SimpleSelector.Selected) -> None:
        """Handle SimpleSelector.Selected message."""
        self.query_one("#selected_output", Static).update(
            f"Selected: {message.item} - {message.description} (Index: {message.index})"
        )

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.dark = not self.dark

if __name__ == "__main__":
    app = SimpleSelectorExampleApp()
    app.run()
