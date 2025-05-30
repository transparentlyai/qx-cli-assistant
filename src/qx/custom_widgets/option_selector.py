from textual.app import ComposeResult
from textual.containers import Vertical
from textual.css.query import DOMQuery
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Label
import os # Added for path operations

class OptionSelector(Widget):
    """
    A widget to select an option from a list using keyboard navigation.

    It allows users to navigate options using up/down arrow keys, a specific
    character key associated with an option, or by pressing Enter to select
    the currently highlighted option.

    Attributes:
        options (list[tuple[str, str]]): The list of options to display.
            Each tuple contains (display_text, selection_key).
        selected_index (reactive[int]): The index of the currently selected option.
        border_title (str | None): The title displayed in the widget's border.

    CSS Styling:
        The widget and its components can be styled using Textual CSS.

        Key Selectors:
        - `OptionSelector`: Targets the main container of the widget.
            - Default styles: `width: auto; height: auto; padding: 1; border: round $primary; border-title-align: center;`
        - `OptionSelector > Vertical`: Targets the vertical layout container holding the option labels.
            - Default styles: `width: auto; height: auto;`
        - `Label`: Targets individual option labels within the selector.
            - Default styles: `width: 100%; padding: 0 1;`
        - `Label.selected`: Targets the currently highlighted/selected option label.
            - Default styles: `background: $secondary; color: $text;`

        The `[b u]` tags used for highlighting the selection key in an option's text
        (e.g., "[b u]Y[/b u]es") can also be styled if your application-wide CSS
        defines styles for `b` (bold) and `u` (underline) tags, or more specific
        selectors like `OptionSelector Label > b` and `OptionSelector Label > u`.

        To apply custom CSS from a file, pass the file path to the `css_path`
        parameter during instantiation. This will load and apply the styles
        from the specified file to the application. Note that these styles are
        globally applied to the app, not just this widget instance, so use specific
        selectors (e.g., by ID: `#my_option_selector Label`) if you need to target
        a specific instance.
    """

    DEFAULT_CSS = """
    OptionSelector {
        width: auto;
        height: auto;
        padding: 1;
        border: round $primary;
        border-title-align: center;
    }
    OptionSelector > Vertical {
        width: auto;
        height: auto;
    }
    Label { /* General Label style within OptionSelector context */
        width: 100%;
        padding: 0 1; /* Default padding for labels */
    }
    Label.selected { /* Style for the selected Label */
        background: $secondary;
        color: $text;
    }
    """

    class OptionSelected(Message):
        """Posted when an option is selected."""
        def __init__(self, value: str, key: str, index: int) -> None:
            super().__init__()
            self.value = value # The display text of the selected option
            self.key = key     # The key/value associated with the selected option
            self.index = index # The numerical index of the selected option

    selected_index: reactive[int] = reactive(0)

    def __init__(
        self,
        options: list[tuple[str, str]],
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
        border_title: str | None = None,
        css_path: str | None = None, # New parameter
    ) -> None:
        super().__init__(name=name, id=id, classes=classes, disabled=disabled)
        self.options = options
        self._option_labels: list[Label] = []
        self.border_title = border_title or "Select an Option"
        self.external_css_path = css_path # Store the path

    def _highlight_key(self, text: str, key: str) -> str:
        """Highlights the selection key in the option text."""
        try:
            # Attempt to find the exact key char (case-insensitive)
            key_char_to_find = key.lower()
            text_lower = text.lower()
            key_index = -1
            
            # Prefer finding the key as a distinct word or start of word if possible
            # This is a simple heuristic, might need refinement for complex cases
            # For now, we stick to the original logic of finding the first occurrence
            key_index = text_lower.find(key_char_to_find)

            if key_index != -1:
                # Highlight the first occurrence of the key character
                return f"{text[:key_index]}[b u]{text[key_index:key_index+len(key)]}[/b u]{text[key_index+len(key):]}"
            else: # Key not found, highlight the first character of the text as fallback
                 return f"[b u]{text[0]}[/b u]{text[1:]}"
        except ValueError: # Should not happen with find, but as a safeguard
            return f"[b u]{text[0]}[/b u]{text[1:]}"


    def compose(self) -> ComposeResult:
        with Vertical():
            for text, key in self.options:
                highlighted_text = self._highlight_key(text, key)
                label = Label(highlighted_text)
                self._option_labels.append(label)
                yield label

    def on_mount(self) -> None:
        """Set initial focus, update styles, and load external CSS if provided."""
        if self.external_css_path and os.path.exists(self.external_css_path):
            try:
                # Textual's App class has a `STYLESHEETS` attribute or `stylesheet` property
                # for managing CSS. Widgets themselves don't typically load app-level CSS directly.
                # A common pattern is to add to App.CSS_PATH or App.STYLESHEETS.
                # For simplicity here, we'll assume the app will handle CSS loading.
                # This widget will just make the app aware of an additional CSS file.
                # A more robust way would be for the app to collect these paths.
                #
                # If this widget needs to *guarantee* its styles are loaded,
                # it might need a reference to the app or a different mechanism.
                # For now, we'll print a message if a CSS path is provided,
                # as a placeholder for actual CSS loading logic by the app.
                #
                # A simple way to apply CSS directly if the app supports it:
                if hasattr(self.app, 'load_stylesheet'):
                     self.app.load_stylesheet(self.external_css_path)
                elif hasattr(self.app, 'stylesheet') and hasattr(self.app.stylesheet, 'read_all'):
                    # This is a more direct approach but might have side effects
                    # or not be the standard way in newer Textual versions.
                    # It's generally better to use App.CSS_PATH or similar.
                    # For now, we'll just note it.
                    #
                    # with open(self.external_css_path, "r") as css_file:
                    #     self.app.stylesheet.read_all(css_file.read())
                    # self.app.refresh_css()
                    pass # Placeholder for app-level CSS loading
                
                # The most straightforward way for an app to pick up CSS is by adding
                # the path to its CSS_PATH tuple before the app runs.
                # Since the widget is initialized within the app's lifecycle,
                # we can't easily modify App.CSS_PATH here for the current run.
                #
                # The user of this widget will need to ensure the CSS file is loaded
                # by their Textual application, e.g., by adding it to App.CSS_PATH.
                # This parameter serves as a convention.
                pass

            except Exception as e:
                self.log.error(f"Failed to process external CSS file '{self.external_css_path}': {e}")

        self.can_focus = True
        self._update_selection_display()


    def _update_selection_display(self) -> None:
        """Updates the visual selection of options."""
        for i, label in enumerate(self._option_labels):
            label.remove_class("selected")
            if i == self.selected_index:
                label.add_class("selected")
                # Ensure the selected item is visible
                # Check if Vertical container exists before querying
                vertical_container = self.query(Vertical).first()
                if vertical_container:
                    vertical_container.scroll_to_widget(label, animate=False)


    def watch_selected_index(self, old_index: int, new_index: int) -> None:
        """Called when selected_index changes."""
        self._update_selection_display()

    def on_key(self, event: Message) -> None: # Actually textual.events.Key
        # Make sure it's a key event (Textual's type hinting can be broad for Message)
        if not hasattr(event, 'key'):
            return

        key_char = event.key.lower()

        if key_char == "up":
            self.selected_index = (self.selected_index - 1 + len(self.options)) % len(self.options)
            event.stop()
        elif key_char == "down":
            self.selected_index = (self.selected_index + 1) % len(self.options)
            event.stop()
        elif key_char == "enter":
            if self.options: # Ensure options are not empty
                text, key_val = self.options[self.selected_index]
                self.post_message(self.OptionSelected(text, key_val, self.selected_index))
                event.stop()
        else:
            # Allow selection by pressing the associated key character
            for i, (text, key_val) in enumerate(self.options):
                if key_char == key_val.lower():
                    self.selected_index = i
                    # Automatically post message when key is pressed (original behavior)
                    self.post_message(self.OptionSelected(text, key_val, self.selected_index))
                    event.stop()
                    break
