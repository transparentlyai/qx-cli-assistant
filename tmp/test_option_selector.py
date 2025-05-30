# Add project root to sys.path to allow importing from src
import sys
import os

# Calculate the path to the project's root directory
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# Path to the main CSS file
MAIN_CSS_PATH = os.path.join(project_root, "src", "qx", "css", "main.css")

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Label

# Now we can import the custom widget
from src.qx.custom_widgets.option_selector import OptionSelector

class TestOptionSelectorApp(App):
    # Set the CSS path for the application. Textual will load this stylesheet.
    CSS_PATH = MAIN_CSS_PATH 
    BINDINGS = [("q", "quit", "Quit")]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        options = [
            ("Yes", "Y"),
            ("No", "N"),
            ("Cancel", "C"),
            ("All", "A"),
            ("Yes, but", "B"),
            ("Maybe Later", "M"),
            ("Another Option With A Very Long Name To Test Scrolling", "O"),
            ("Final Choice", "F"),
        ]
        # The css_path parameter in OptionSelector is for its own awareness or future use;
        # actual styling comes from App.CSS_PATH loading main.css.
        yield OptionSelector(
            options, 
            id="option_selector", 
            border_title="Make a choice:", 
            css_path=MAIN_CSS_PATH 
        )
        yield Label("Selected: None", id="result_label")

    async def on_option_selector_option_selected(self, event: OptionSelector.OptionSelected) -> None:
        result_label = self.query_one("#result_label", Label)
        result_label.update(f"Selected: {event.value} (Key: {event.key}, Index: {event.index})")

if __name__ == "__main__":
    app = TestOptionSelectorApp()
    app.run()
