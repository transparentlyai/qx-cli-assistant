# ExtendedInput Widget

## Overview

`ExtendedInput` is a custom Textual widget that provides an enhanced text input experience, designed to be a flexible and powerful replacement for the standard `Input` or `TextArea` in specific CLI application scenarios. It supports features like command history, path/command completion, and dynamic switching between single-line and multi-line input modes.

The widget is designed to be largely self-contained in its core input and completion logic, communicating with its parent application (e.g., `QXApp`) through a system of Textual messages. This decoupled approach allows for cleaner integration and separation of concerns.

## Features

-   **Single and Multi-line Input**: Toggle between modes using `Alt+Enter`.
    -   In single-line mode, `Enter` submits the input.
    -   In multi-line mode, `Enter` adds a newline, and `Alt+Enter` submits the input.
-   **Command History**:
    -   Navigate through history using `Up` and `Down` arrow keys.
    -   Search history using `fzf` (if installed) with `Ctrl+R`.
    -   Configurable history file path and custom load/save functions.
-   **Path and Command Completion**:
    -   Trigger completion using the `Tab` key.
    -   Supports `bash` `compgen` for path completion.
    -   Supports a custom `command_completer` for application-specific command suggestions.
    -   Displays a `CompletionMenu` widget for multiple candidates.
-   **Decoupled Communication**: Uses Textual messages to interact with the parent application for logging, UI updates, and displaying/hiding the completion menu.
-   **Focus Management**: Manages its focus state and signals to the parent when it can or cannot be focused (e.g., when a completion menu is active).

## Messages

`ExtendedInput` uses the following messages for communication:

### Emitted Messages (Posted by `ExtendedInput`)

These messages are posted to the parent application:

-   `UserInputSubmitted(input_text: str)`:
    Posted when the user submits their input (e.g., by pressing `Enter` in single-line mode or `Alt+Enter`).
-   `LogEmitted(text: str, level: str = "info")`:
    Posted when the widget needs to log an internal event, warning, or error.
-   `MultilineModeToggled(is_multiline: bool)`:
    Posted when the input mode changes between single-line and multi-line. The parent can use this to update UI elements like the prompt.
-   `DisplayCompletionMenu(menu_widget: Widget, anchor_widget: Widget)`:
    Posted when `ExtendedInput` has created and configured a `CompletionMenu` instance that needs to be displayed. The `menu_widget` is the `CompletionMenu` itself, and `anchor_widget` is the `ExtendedInput` instance (for positioning context if needed by the parent).
-   `HideCompletionMenu(menu_widget: Widget)`:
    Posted when the `CompletionMenu` should be hidden (e.g., an item is selected, or completion is cancelled).

### Consumed Messages (Handled by `ExtendedInput`)

These messages are typically emitted by the `CompletionMenu` and handled by `ExtendedInput`:

-   `CompletionMenu.ItemSelected(item: Any, index: int, owner_widget: Widget)`:
    Handled when the user selects an item from the `CompletionMenu`. `ExtendedInput` will then insert the selected completion.
-   `CompletionMenu.Cancelled(owner_widget: Widget)`:
    Handled when the user cancels the `CompletionMenu` (e.g., by pressing `Escape` while the menu is active).

## Configuration

`ExtendedInput` can be configured upon instantiation:

-   `command_completer: Optional[CommandCompleterProtocol]`:
    An object that conforms to `CommandCompleterProtocol` (i.e., has a `get_completions(self, partial_input: str) -> List[str]` method). This is used to provide custom command completion suggestions.
-   `history_file_path: Optional[Path]`:
    A `pathlib.Path` object pointing to the file where command history should be stored. If provided without custom load/save functions, a default file-based history mechanism is used.
-   `history_load_fn: Optional[HistoryLoadFunction]`:
    A callable that takes a `Path` and returns a `List[str]` of history items.
    ```python
    class HistoryLoadFunction(Protocol):
        def __call__(self, path: Path) -> List[str]: ...
    ```
-   `history_save_fn: Optional[HistorySaveFunction]`:
    A callable that takes a `Path` and a command string (`str`) to save an item to history.
    ```python
    class HistorySaveFunction(Protocol):
        def __call__(self, path: Path, command: str) -> None: ...
    ```

## Integration Example

Here's a conceptual example of how a parent Textual `App` might integrate `ExtendedInput`:

```python
from pathlib import Path
from textual.app import App, ComposeResult
from textual.widgets import Static, RichLog
from textual import on

from qx.custom_widgets.extended_input import (
    ExtendedInput,
    UserInputSubmitted,
    LogEmitted,
    MultilineModeToggled,
    DisplayCompletionMenu,
    HideCompletionMenu
)
from qx.custom_widgets.completion_menu import CompletionMenu # For type hinting

# Assume QX_HISTORY_FILE is defined
QX_HISTORY_FILE = Path("~/.qx_history").expanduser()

class MyApp(App):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_input: Optional[ExtendedInput] = None
        self.output_log: Optional[RichLog] = None
        self.prompt_label: Optional[Static] = None
        self._active_completion_menu: Optional[CompletionMenu] = None
        self._original_prompt = "> "
        self._multiline_prompt = "... "

    def compose(self) -> ComposeResult:
        self.output_log = RichLog(id="output")
        self.prompt_label = Static(self._original_prompt, id="prompt")
        # Instantiate ExtendedInput with history path
        self.user_input = ExtendedInput(
            id="main-input",
            history_file_path=QX_HISTORY_FILE
            # command_completer can be set here or later via set_command_completer
        )
        yield self.output_log
        yield self.prompt_label
        yield self.user_input

    def on_mount(self) -> None:
        self.user_input.focus()
        # Example: Set a command completer
        # self.user_input.set_command_completer(MyCustomCompleter())

    @on(UserInputSubmitted)
    async def handle_user_input(self, message: UserInputSubmitted):
        self.output_log.write(f"User submitted: {message.input_text}")
        self.user_input.text = "" # Clear input after submission

    @on(LogEmitted)
    def handle_log_from_input(self, message: LogEmitted):
        self.output_log.write(f"[Input Log - {message.level}]: {message.text}")

    @on(MultilineModeToggled)
    def handle_multiline_toggle(self, message: MultilineModeToggled):
        if message.is_multiline:
            self.prompt_label.update(self._multiline_prompt)
        else:
            self.prompt_label.update(self._original_prompt)
        self.user_input.focus()

    @on(DisplayCompletionMenu)
    async def show_completion_menu(self, message: DisplayCompletionMenu):
        if self._active_completion_menu:
            await self._active_completion_menu.remove()
        self._active_completion_menu = message.menu_widget
        # ExtendedInput sets styles; parent mounts it.
        # Mount to screen for overlay.
        await self.screen.mount(self._active_completion_menu)
        self._active_completion_menu.focus()
        if self.user_input: self.user_input.can_focus = False


    @on(HideCompletionMenu)
    async def hide_completion_menu(self, message: HideCompletionMenu):
        if self._active_completion_menu and self._active_completion_menu is message.menu_widget:
            await self._active_completion_menu.remove()
            self._active_completion_menu = None
            if self.user_input:
                self.user_input.can_focus = True
                self.user_input.focus()

```

## Bindings

The following key bindings are active within the `ExtendedInput` widget:

-   `tab`: `complete_path_or_command` - Triggers path or command completion. If a `CompletionMenu` is active, cycles through its items.
-   `up`: `history_previous` - Loads the previous command from history.
-   `down`: `history_next` - Loads the next command from history or clears input if at the end of history.
-   `alt+enter`: `toggle_multiline_or_submit` - Toggles multi-line mode. If in multi-line mode, submits the current input.
-   `ctrl+r`: `search_history_fzf` - Searches command history using `fzf` (requires `fzf` to be installed and in PATH).
-   `escape`: `handle_escape` - If a `CompletionMenu` is active, cancels/hides it. Otherwise, standard Textual escape behavior (e.g., clearing input if configured, or handled by parent app).
-   `enter`: (Default Textual behavior, modified) - Submits input in single-line mode. In multi-line mode, inserts a newline. `ExtendedInput` posts `UserInputSubmitted` on actual submission.

Note: Some bindings have `show=False` as they are context-dependent or advanced features. `priority=True` is used for some bindings to ensure they are caught by `ExtendedInput` before potentially being handled by the parent application if similar global bindings exist.
