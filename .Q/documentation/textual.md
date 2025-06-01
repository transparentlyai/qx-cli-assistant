TITLE: Centering Multiple Widgets Individually with `Center` Container in Textual Python
DESCRIPTION: This example shows how to correctly center multiple widgets, such as `Button`s, in a Textual application. Instead of relying solely on the parent's `align` property, each widget is wrapped within a `textual.containers.Center` container, ensuring each widget is individually centered on its own line, preventing left-alignment within the overall centered block.
SOURCE: https://github.com/textualize/textual/blob/main/questions/align-center-middle.question.md#_snippet_1

LANGUAGE: Python
CODE:
```
from textual.app import App, ComposeResult
from textual.containers import Center
from textual.widgets import Button

class ButtonApp(App):

    CSS = """
    Screen {
        align: center middle;
    }
    """

    def compose(self) -> ComposeResult:
        yield Center(Button("PUSH ME!"))
        yield Center(Button("AND ME!"))
        yield Center(Button("ALSO PLEASE PUSH ME!"))
        yield Center(Button("HEY ME ALSO!!"))

if __name__ == "__main__":
    ButtonApp().run()
```

----------------------------------------

TITLE: Implementing a Non-Blocking Background Task in Textual (Correct)
DESCRIPTION: This snippet shows the corrected approach for running a long-running operation asynchronously in a Textual application. By replacing `time.sleep` with `await asyncio.sleep`, the operation becomes non-blocking, allowing the Textual UI to remain responsive. It illustrates how to properly use `await` within a coroutine to yield control back to the event loop, enabling concurrent execution of other tasks while the long operation is in progress.
SOURCE: https://github.com/textualize/textual/blob/main/docs/blog/posts/responsive-app-background-task.md#_snippet_2

LANGUAGE: Python
CODE:
```
import asyncio
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Button, Label
from textual.containers import Container

class NonBlockingApp(App):
    BINDINGS = [
        ("c", "change_color", "Change Color"),
        ("l", "load", "Load Data")
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        with Container():
            yield Button("Change Color", id="change_color")
            yield Button("Load Data", id="load_data")
            yield Label("Ready", id="status_label")

    def action_change_color(self) -> None:
        self.query_one("#status_label").update("Color changed!")
        self.screen.styles.background = "blue" if self.screen.styles.background == "red" else "red"

    async def _do_long_operation(self) -> None:
        # 1. We create a label that tells the user that we are starting our time-consuming operation.
        self.query_one("#status_label").update("Starting long operation...")
        # 2. We `await` the time-consuming operation so that the application remains responsive.
        await asyncio.sleep(5) # This is the non-blocking change
        # 3. We create a label that tells the user that the time-consuming operation has been concluded.
        self.query_one("#status_label").update("Long operation finished.")

    def action_load(self) -> None:
        self.query_one("#status_label").update("Loading data...")
        asyncio.create_task(self._do_long_operation())

if __name__ == "__main__":
    app = NonBlockingApp()
    app.run()
```

----------------------------------------

TITLE: Handling Button Events and Toggling CSS Classes (Python)
DESCRIPTION: Implements an `on_button_pressed` event handler in Textual to respond to button clicks. It demonstrates how to add or remove the "started" CSS class on a widget using `add_class()` and `remove_class()` methods to dynamically change its appearance based on user interaction.
SOURCE: https://github.com/textualize/textual/blob/main/docs/tutorial.md#_snippet_9

LANGUAGE: python
CODE:
```
# stopwatch04.py

from textual.app import App, ComposeResult
from textual.containers import Container
from textual.widgets import Button, Header, Footer, Static

class Stopwatch(Static):
    """A stopwatch widget."""

    def compose(self) -> ComposeResult:
        """Create child widgets for the stopwatch."""
        yield Static("00:00:00.00", id="time")
        with Container(id="buttons"):
            yield Button("Start", id="start", variant="success")
            yield Button("Stop", id="stop", variant="error")
            yield Button("Reset", id="reset")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Called when a button is pressed."""
        button_id = event.button.id
        if button_id == "start":
            self.add_class("started")
        elif button_id == "stop":
            self.remove_class("started")


class StopwatchApp(App):
    """Textual app for the Stopwatch."""

    CSS_PATH = "stopwatch04.tcss"

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield Footer()
        yield Container(
            Stopwatch(),
            Stopwatch(),
            Stopwatch(),
            id="stopwatches",
        )


if __name__ == "__main__":
    app = StopwatchApp()
    app.run()

```

----------------------------------------

TITLE: Creating a Real-time Clock Application with Textual Python
DESCRIPTION: This Textual application displays the current time using the `Digits` widget. It updates the time every second by querying the widget and formatting the `datetime.now().time()` output. The CSS aligns the display to the center.
SOURCE: https://github.com/textualize/textual/blob/main/README.md#_snippet_0

LANGUAGE: Python
CODE:
```
"""
An App to show the current time.
"""

from datetime import datetime

from textual.app import App, ComposeResult
from textual.widgets import Digits


class ClockApp(App):
    CSS = """
    Screen { align: center middle; }
    Digits { width: auto; }
    """

    def compose(self) -> ComposeResult:
        yield Digits("")

    def on_ready(self) -> None:
        self.update_clock()
        self.set_interval(1, self.update_clock)

    def update_clock(self) -> None:
        clock = datetime.now().time()
        self.query_one(Digits).update(f"{clock:%T}")


if __name__ == "__main__":
    app = ClockApp()
    app.run()
```

----------------------------------------

TITLE: Running a Textual Application (Python)
DESCRIPTION: This standard Python entry point creates an instance of the `MotherApp` and starts the Textual application. It's the main execution block for launching the TUI.
SOURCE: https://github.com/textualize/textual/blob/main/docs/blog/posts/anatomy-of-a-textual-user-interface.md#_snippet_8

LANGUAGE: Python
CODE:
```
if __name__ == "__main__":
    app = MotherApp()
    app.run()
```

----------------------------------------

TITLE: Mounting and Modifying a Widget Asynchronously in Textual Python
DESCRIPTION: This example illustrates how to explicitly `await` the `mount` method. Awaiting ensures that the widget is fully initialized and mounted before any subsequent operations, such as querying the widget and modifying its styles, are performed. This pattern is necessary when immediate post-mount actions are required.
SOURCE: https://github.com/textualize/textual/blob/main/docs/blog/posts/await-me-maybe.md#_snippet_2

LANGUAGE: Python
CODE:
```
async def on_key(self):
    # Add MyWidget to the screen
    await self.mount(MyWidget("Hello, World!"))
    # add a border
    self.query_one(MyWidget).styles.border = ("heavy", "red")
```

----------------------------------------

TITLE: Textual `on` Decorator Handler with Event Object (Python)
DESCRIPTION: Similar to the naming convention, this handler uses the `@on` decorator and accepts the event object as a positional argument. It accesses `message.color` to animate the background, showcasing event data access with the decorator approach.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/events.md#_snippet_5

LANGUAGE: python
CODE:
```
    @on(ColorButton.Selected)
    def animate_background_color(self, message: ColorButton.Selected) -> None:
        self.screen.styles.animate("background", message.color, duration=0.5)
```

----------------------------------------

TITLE: Creating a Basic Textual App Class in Python
DESCRIPTION: This snippet demonstrates the simplest way to define a Textual application by subclassing `textual.app.App`. It serves as the foundational structure for any Textual application, providing the necessary inheritance for app functionality.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/app.md#_snippet_0

LANGUAGE: python
CODE:
```
from textual.app import App

class MyApp(App):
    pass
```

----------------------------------------

TITLE: Dispatching Button Press Events with the @on Decorator in Textual Python
DESCRIPTION: This snippet showcases the new `@on` decorator introduced in Textual 0.23.0 for more granular event dispatching. It allows specific methods to handle `Button.Pressed` events based on CSS selectors (e.g., `#id` for ID, `.class` for class names), eliminating the need for large `if` statements within a single handler. This approach enhances code readability and maintainability. It requires the `textual` library and the `@on` decorator.
SOURCE: https://github.com/textualize/textual/blob/main/docs/blog/posts/release0-23-0.md#_snippet_1

LANGUAGE: Python
CODE:
```
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Button, Label
from textual.containers import Container
from textual.on import on

class MyButtonApp(App):
    BINDINGS = [
        ("d", "toggle_dark", "Toggle dark mode"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        with Container():
            yield Button("Bell", id="bell")
            yield Button("Toggle Dark", classes="toggle dark")
            yield Button("Quit", id="quit")
            yield Label("Press a button!")

    @on(Button.Pressed, "#bell")
    def handle_bell_button(self) -> None:
        """Handles the bell button pressed event."""
        self.query_one(Label).update("Bell button pressed!")

    @on(Button.Pressed, ".toggle.dark")
    def handle_toggle_dark_button(self) -> None:
        """Handles the toggle dark button pressed event."""
        self.query_one(Label).update("Toggle Dark button pressed!")

    @on(Button.Pressed, "#quit")
    def handle_quit_button(self) -> None:
        """Handles the quit button pressed event."""
        self.query_one(Label).update("Quit button pressed!")
        self.exit()

if __name__ == "__main__":
    app = MyButtonApp()
    app.run()
```

----------------------------------------

TITLE: Implementing Accurate Asyncio Sleep for Windows
DESCRIPTION: This Python function provides a more accurate asynchronous sleep mechanism for Windows, addressing the 15ms granularity limitation of `asyncio.sleep`. It achieves better precision by offloading the blocking `time.sleep` call to a thread pool executor, making it suitable for animations and time-sensitive operations in Textual applications. It takes `sleep_for` (float) as input, representing the duration in seconds to sleep.
SOURCE: https://github.com/textualize/textual/blob/main/docs/blog/posts/better-sleep-on-windows.md#_snippet_0

LANGUAGE: Python
CODE:
```
from time import sleep as time_sleep
from asyncio import get_running_loop

async def sleep(sleep_for: float) -> None:
    """An asyncio sleep.

    On Windows this achieves a better granularity than asyncio.sleep

    Args:
        sleep_for (float): Seconds to sleep for.
    """    
    await get_running_loop().run_in_executor(None, time_sleep, sleep_for)
```

----------------------------------------

TITLE: Handling User Input Submission in Textual Python
DESCRIPTION: This asynchronous event handler is triggered when a user submits text in the `Input` widget. It clears the input, adds the user's prompt to the chat view, mounts a new `Response` widget for the LLM's reply, anchors it to the bottom, and then calls `send_prompt` to process the input.
SOURCE: https://github.com/textualize/textual/blob/main/docs/blog/posts/anatomy-of-a-textual-user-interface.md#_snippet_6

LANGUAGE: Python
CODE:
```
    @on(Input.Submitted)
    async def on_input(self, event: Input.Submitted) -> None:
        chat_view = self.query_one("#chat-view")
        event.input.clear()
        await chat_view.mount(Prompt(event.value))
        await chat_view.mount(response := Response())
        response.anchor()
        self.send_prompt(event.value, response)
```

----------------------------------------

TITLE: Installing Textual via PyPI
DESCRIPTION: Installs the core Textual library using pip, the Python package installer. This is the standard method for getting Textual.
SOURCE: https://github.com/textualize/textual/blob/main/docs/getting_started.md#_snippet_0

LANGUAGE: Bash
CODE:
```
pip install textual
```

----------------------------------------

TITLE: Retrieving a Single Widget by ID (Python)
DESCRIPTION: This snippet demonstrates how to use the `query_one` method to retrieve a single widget instance by its CSS ID selector. It searches the DOM for the first widget with the ID "send". If no match is found, a `NoMatches` exception is raised.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/queries.md#_snippet_0

LANGUAGE: Python
CODE:
```
send_button = self.query_one("#send")
```

----------------------------------------

TITLE: Calculator Example in Textual
DESCRIPTION: This example demonstrates a calculator application built with Textual, showcasing its ability to create interactive terminal applications. It includes both the Python code for the application logic and the CSS for styling.
SOURCE: https://github.com/textualize/textual/blob/main/docs/index.md#_snippet_1

LANGUAGE: Python
CODE:
```
--8<-- "examples/calculator.py"
```

----------------------------------------

TITLE: Testing Textual App Interactions with Pytest and Pilot (Python)
DESCRIPTION: This module contains two asynchronous tests for the `RGBApp` using `pytest` and Textual's `Pilot` object. The `test_keys` function simulates key presses (r, g, b) to verify background color changes, while `test_buttons` simulates button clicks for the same purpose. Both tests use `run_test()` to run the app in headless mode and assert the application's state.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/testing.md#_snippet_1

LANGUAGE: Python
CODE:
```
import pytest
from textual.app import App, ComposeResult
from textual.pilot import Pilot
from textual.widgets import Header, Footer, Button
from textual.containers import Container

# Re-defining RGBApp for self-containment in the example
class RGBApp(App):
    CSS = """
    Screen {
        align-items: center;
        justify-content: center;
    }
    Container {
        width: 100%;
        height: 100%;
        display: grid;
        grid-template-columns: 1fr 1fr 1fr;
        grid-gap: 1;
        align-items: center;
        justify-items: center;
    }
    Button {
        width: 80%;
        height: 80%;
        font-size: 2;
    }
    """

    BINDINGS = [
        ("r", "set_color('red')", "Red"),
        ("g", "set_color('green')", "Green"),
        ("b", "set_color('blue')", "Blue"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        with Container():
            yield Button("Red", id="red", variant="error")
            yield Button("Green", id="green", variant="success")
            yield Button("Blue", id="blue", variant="primary")
        yield Footer()

    def action_set_color(self, color: str) -> None:
        self.screen.styles.background = color

@pytest.mark.asyncio
async def test_keys():
    """Test that pressing keys changes the background color."""
    app = RGBApp()
    async with app.run_test() as pilot:
        # Default background color for Textual is black (rgb(0,0,0))
        assert pilot.app.screen.styles.background == "rgb(0,0,0)"
        await pilot.press("r")
        assert pilot.app.screen.styles.background == "red"
        await pilot.press("g")
        assert pilot.app.screen.styles.background == "green"
        await pilot.press("b")
        assert pilot.app.screen.styles.background == "blue"

@pytest.mark.asyncio
async def test_buttons():
    """Test that clicking buttons changes the background color."""
    app = RGBApp()
    async with app.run_test() as pilot:
        # Default background color for Textual is black (rgb(0,0,0))
        assert pilot.app.screen.styles.background == "rgb(0,0,0)"
        await pilot.click("#red")
        assert pilot.app.screen.styles.background == "red"
        await pilot.click("#green")
        assert pilot.app.screen.styles.background == "green"
        await pilot.click("#blue")
        assert pilot.app.screen.styles.background == "blue"
```

----------------------------------------

TITLE: Running a Textual App Instance in Python
DESCRIPTION: This code shows how to instantiate and run a Textual application. Calling `app.run()` puts the terminal into application mode, allowing Textual to manage user input and screen updates. It's the standard entry point for launching a Textual UI.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/app.md#_snippet_1

LANGUAGE: python
CODE:
```
from textual.app import App

class MyApp(App):
    pass

if __name__ == "__main__":
    app = MyApp()
    app.run()
```

----------------------------------------

TITLE: Declaring an Async Worker in Textual (Python)
DESCRIPTION: This snippet shows how to declare a non-threaded, asynchronous worker function in Textual. By making the function `async` and omitting `thread=True` from the `@work` decorator, the worker will run asynchronously on the main event loop, which is the default and recommended behavior for non-threaded operations.
SOURCE: https://github.com/textualize/textual/blob/main/questions/worker-thread-error.question.md#_snippet_1

LANGUAGE: python
CODE:
```
@work()
async def run_in_background():
    ...
```

----------------------------------------

TITLE: World Clock App with Data Binding - Python
DESCRIPTION: This Python code demonstrates data binding in a Textual application. It binds the app's `time` reactive attribute to the `time` attribute of the `WorldClock` widgets, eliminating the need for a separate watcher to update the clocks.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/reactivity.md#_snippet_24

LANGUAGE: python
CODE:
```
from __future__ import annotations

import asyncio
import time
from datetime import datetime, timezone

import pytz
from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Static


class TimeDisplay(Static):
    
```

----------------------------------------

TITLE: Handling Button Presses with Textual (Python)
DESCRIPTION: This method serves as the event handler for button press events in the Textual application. It determines which button was pressed based on its ID, retrieves the associated `TimeDisplay` widget, and invokes the corresponding action (`start`, `stop`, or `reset`). It also manages a CSS class ('started') on the parent widget to visually indicate the stopwatch's state.
SOURCE: https://github.com/textualize/textual/blob/main/docs/tutorial.md#_snippet_11

LANGUAGE: Python
CODE:
```
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Event handler called when a button is pressed."""
        button_id = event.button.id
        time_display = self.query_one(TimeDisplay)
        if button_id == "start":
            time_display.start()
            self.add_class("started")
        elif button_id == "stop":
            time_display.stop()
            self.remove_class("started")
        elif button_id == "reset":
            time_display.reset()
```

----------------------------------------

TITLE: Textual App with Reactive Bug
DESCRIPTION: This example demonstrates a Textual app that cycles through greetings but contains a bug where a watcher attempts to update a label before it is mounted, resulting in a NoMatches error. The reactive attribute is set in the constructor, which invokes a watcher before the widget is fully mounted.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/reactivity.md#_snippet_19

LANGUAGE: python
CODE:
```
from textual.app import App, ComposeResult
from textual.widgets import Label
from textual.reactive import reactive

class Greeter(Label):

    DEFAULT_CSS = """
    Greeter {
        width: auto;
        height: auto;
        padding: 1 2;
        border: tall $primary;
    }
    """

    greeting: reactive[str] = reactive("Hello, World!")

    def watch_greeting(self, greeting: str) -> None:
        self.update(greeting)

    def on_mount(self) -> None:
        self.greeting = "Goodbye, World!"

class ReactiveBugApp(App):

    CSS = """
    Screen {
        layout: vertical;
        align: center middle;
    }
    """

    def compose(self) -> ComposeResult:
        yield Greeter()

if __name__ == "__main__":
    app = ReactiveBugApp()
    app.run()
```

----------------------------------------

TITLE: Defining Custom Markdown Widgets for UI
DESCRIPTION: These Python classes define custom Textual widgets, Prompt and Response, by extending the built-in Markdown widget. They are used to display user input and AI responses, leveraging Markdown formatting for rich text. Response specifically sets a border title.
SOURCE: https://github.com/textualize/textual/blob/main/docs/blog/posts/anatomy-of-a-textual-user-interface.md#_snippet_1

LANGUAGE: Python
CODE:
```
class Prompt(Markdown):
    pass


class Response(Markdown):
    BORDER_TITLE = "Mother"
```

----------------------------------------

TITLE: Docking Header and Footer Widgets in Textual
DESCRIPTION: This code demonstrates how to dock header and footer widgets to the top and bottom edges of the screen in a Textual application using CSS. It shows how to use the `dock` style rule to fix the position of widgets and automatically adjust the available area for other widgets.
SOURCE: https://github.com/textualize/textual/blob/main/docs/how-to/design-a-layout.md#_snippet_1

LANGUAGE: python
CODE:
```
from textual.app import App, ComposeResult
from textual.widgets import Placeholder
from textual.containers import Screen
from textual import css


class Header(Placeholder):
    
```

----------------------------------------

TITLE: Loading External CSS in Textual App (Python)
DESCRIPTION: This Python snippet demonstrates how to link an external CSS file (.tcss) to a Textual application using the CSS_PATH class variable. The path is relative to the app's definition, allowing the app to load and apply styles from the specified CSS file.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/app.md#_snippet_7

LANGUAGE: python
CODE:
```
--8<-- "docs/examples/app/question02.py"
```

----------------------------------------

TITLE: Initializing Textual Application Screens in Python
DESCRIPTION: This Python class defines the core `GridInfo` Textual application, demonstrating how to structure a non-trivial Textual app by declaring its CSS file, title, and a collection of distinct screens. The `on_mount` method is used to push the initial 'main' screen, ensuring that the primary application logic resides within dedicated screen classes rather than the main `App` class itself.
SOURCE: https://github.com/textualize/textual/blob/main/docs/blog/posts/on-dog-food-the-original-metaverse-and-not-being-bored.md#_snippet_0

LANGUAGE: Python
CODE:
```
class GridInfo( App[ None ] ):
    """TUI app for showing information about the Second Life grid."""

    CSS_PATH = "gridinfo.css"
    """The name of the CSS file for the app."""

    TITLE = "Grid Information"
    """str: The title of the application."""

    SCREENS = {
        "main": Main,
        "region": RegionInfo
    }
    """The collection of application screens."""

    def on_mount( self ) -> None:
        """Set up the application on startup."""
        self.push_screen( "main" )
```

----------------------------------------

TITLE: Running a Blocking Background Task in Textual (Incorrect)
DESCRIPTION: This snippet demonstrates an attempt to run a long-running operation in the background using `asyncio.create_task`. Although `_do_long_operation` is an `async` function (coroutine), it still uses `time.sleep`, which is a blocking call. This causes the Textual application's event loop to freeze and the UI to become unresponsive during the operation, highlighting the importance of using `await` with asynchronous I/O operations.
SOURCE: https://github.com/textualize/textual/blob/main/docs/blog/posts/responsive-app-background-task.md#_snippet_1

LANGUAGE: Python
CODE:
```
import time
import asyncio
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Button, Label
from textual.containers import Container

class BlockingApp(App):
    BINDINGS = [
        ("c", "change_color", "Change Color"),
        ("l", "load", "Load Data")
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        with Container():
            yield Button("Change Color", id="change_color")
            yield Button("Load Data", id="load_data")
            yield Label("Ready", id="status_label")

    def action_change_color(self) -> None:
        self.query_one("#status_label").update("Color changed!")
        self.screen.styles.background = "blue" if self.screen.styles.background == "red" else "red"

    async def _do_long_operation(self) -> None:
        # This is the blocking part, using time.sleep
        self.query_one("#status_label").update("Starting long operation...")
        time.sleep(5) # This blocks the event loop
        self.query_one("#status_label").update("Long operation finished.")

    def action_load(self) -> None:
        self.query_one("#status_label").update("Loading data...")
        # Create a task to run the long operation concurrently
        asyncio.create_task(self._do_long_operation())

if __name__ == "__main__":
    app = BlockingApp()
    app.run()
```

----------------------------------------

TITLE: Defining a Widget with Scoped CSS in Textual (Python)
DESCRIPTION: This Python snippet defines a `MyWidget` class inheriting from `Widget` and demonstrates the use of `DEFAULT_CSS` to apply styles. Prior to Textual 0.38.0, the `Label` rule would style all `Label` widgets globally. With 0.38.0, the CSS is automatically scoped to only affect `Label` instances within `MyWidget`, preventing unintended global style impacts. The `compose` method yields two `Label` instances.
SOURCE: https://github.com/textualize/textual/blob/main/docs/blog/posts/release0-38-0.md#_snippet_0

LANGUAGE: python
CODE:
```
class MyWidget(Widget):
    DEFAULT_CSS = """
    MyWidget {
        height: auto;
        border: magenta;
    }
    Label {
        border: solid green;
    }
    """

    def compose(self) -> ComposeResult:
        yield Label("foo")
        yield Label("bar")
```

----------------------------------------

TITLE: Setting Box-sizing in CSS
DESCRIPTION: This CSS snippet demonstrates how to explicitly set the `box-sizing` property. It shows examples for both `border-box`, which is the default behavior, and `content-box`, which alters how padding and border contribute to the element's total size.
SOURCE: https://github.com/textualize/textual/blob/main/docs/styles/box_sizing.md#_snippet_1

LANGUAGE: css
CODE:
```
/* Set box sizing to border-box (default) */
box-sizing: border-box;

/* Set box sizing to content-box */
box-sizing: content-box;
```

----------------------------------------

TITLE: Initializing LLM Model on Textual App Mount (Python)
DESCRIPTION: This event handler is called when the Textual application receives a `Mount` event, typically used for initial setup. It initializes the LLM model (e.g., "gpt-4o") using the `llm` library, making it available for later use in the application.
SOURCE: https://github.com/textualize/textual/blob/main/docs/blog/posts/anatomy-of-a-textual-user-interface.md#_snippet_5

LANGUAGE: Python
CODE:
```
    def on_mount(self) -> None:
        self.model = llm.get_model("gpt-4o")
```

----------------------------------------

TITLE: Custom Widget with Render Method in Textual (Python)
DESCRIPTION: This code defines a custom widget class named `Hello` that extends the base `Widget` class. It overrides the `render` method to return a Textual `Text` object containing a formatted greeting string. The greeting string uses Textual's markup to style the word 'World' in bold.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/widgets.md#_snippet_0

LANGUAGE: Python
CODE:
```
class Hello(Widget):
    
```

----------------------------------------

TITLE: Binding Textual Actions to Keys (Python)
DESCRIPTION: This example demonstrates how to bind Textual actions to specific keyboard keys using the `BINDINGS` class attribute. Pressing 'r', 'g', or 'b' will trigger the `set_background` action with the corresponding color, providing an alternative input method to links for executing actions.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/actions.md#_snippet_3

LANGUAGE: python
CODE:
```
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static

class ActionsApp(App):
    BINDINGS = [
        ("r", "set_background('red')", "Set Red Background"),
        ("g", "set_background('green')", "Set Green Background"),
        ("b", "set_background('blue')", "Set Blue Background"),
    ]

    def action_set_background(self, color: str) -> None:
        self.screen.styles.background = color

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        yield Static("Press 'r', 'g', or 'b' to change background.")

if __name__ == "__main__":
    ActionsApp().run()
```

----------------------------------------

TITLE: Combining Multiple Input Validators - Python
DESCRIPTION: This snippet demonstrates how to integrate multiple built-in and custom validators with the `Input` widget. It also shows how to handle `Input.Changed` and `Input.Submitted` events to update the UI based on the `validation_result` and how to implement a custom `Validator` class.
SOURCE: https://github.com/textualize/textual/blob/main/docs/widgets/input.md#_snippet_3

LANGUAGE: Python
CODE:
```
--8<-- "docs/examples/widgets/input_validation.py"
```

----------------------------------------

TITLE: Awaiting Widget Mounting for Immediate Interaction in Textual Python
DESCRIPTION: This snippet provides the solution to the asynchronous mounting problem. By making the event handler `async` and `await`ing `self.mount(Welcome())`, it ensures that the `Welcome` widget and its children (like the Button) are fully mounted and available in the DOM before attempting to query and modify them, preventing `NoMatches` exceptions.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/app.md#_snippet_4

LANGUAGE: python
CODE:
```
from textual.app import App
from textual.widgets import Button, Welcome


class WelcomeApp(App):
    async def on_key(self) -> None:
        await self.mount(Welcome())
        self.query_one(Button).label = "YES!"


if __name__ == "__main__":
    app = WelcomeApp()
    app.run()
```

----------------------------------------

TITLE: Styling a Specific Widget in Textual (Python)
DESCRIPTION: This example shows how to apply styles to an individual `Static` widget within a Textual application. It defines a widget in `compose` and then applies a 'darkblue' background and a 'heavy' white border to it in the `on_mount` handler.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/styles.md#_snippet_1

LANGUAGE: python
CODE:
```
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static
from textual.containers import Container

class MyApp(App):
    def compose(self) -> ComposeResult:
        self.my_widget = Static("Hello, Textual!")
        yield Container(self.my_widget)
        yield Header()
        yield Footer()

    def on_mount(self) -> None:
        self.my_widget.styles.background = "darkblue"
        self.my_widget.styles.border = ("heavy", "white")

if __name__ == "__main__":
    app = MyApp()
    app.run()
```

----------------------------------------

TITLE: Iterating Over All Widgets (Python)
DESCRIPTION: This code demonstrates how to use the `query` method without any arguments to retrieve a `DOMQuery` object containing all widgets, including children and their descendants, from the calling widget's scope. The loop then iterates and prints each discovered widget.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/queries.md#_snippet_4

LANGUAGE: Python
CODE:
```
for widget in self.query():
    print(widget)
```

----------------------------------------

TITLE: Compute Method Example - Python
DESCRIPTION: This example demonstrates how to use a compute method (`compute_color`) to combine red, green, and blue color components into a `Color` object. The `watch_color` method is then called when the result of `compute_color` changes, updating the background color of a widget.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/reactivity.md#_snippet_17

LANGUAGE: Python
CODE:
```
class ComputedApp(App):

    CSS_PATH = "computed01.tcss"

    red = reactive(128)
    green = reactive(128)
    blue = reactive(128)

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield Input(value=str(self.red), id="red", title="Red")
            yield Input(value=str(self.green), id="green", title="Green")
            yield Input(value=str(self.blue), id="blue", title="Blue")
        yield Static("Color!", id="color")

    def compute_color(self) -> Color:
        
```

----------------------------------------

TITLE: Posting Messages (Textual 0.14.0+) - Python
DESCRIPTION: This snippet shows the simplified message posting in Textual 0.14.0 and later. The `await` keyword is no longer required for `post_message`, and the `sender` argument is automatically handled by the framework, reducing boilerplate.
SOURCE: https://github.com/textualize/textual/blob/main/docs/blog/posts/release0-14-0.md#_snippet_1

LANGUAGE: Python
CODE:
```
self.post_message(self.Change(item=self.item))
```

----------------------------------------

TITLE: Performing Batch Updates - Textual Python
DESCRIPTION: This snippet demonstrates the use of the `self.app.batch_update()` context manager to prevent screen updates until the block exits. This is crucial for operations like removing and mounting multiple widgets (e.g., `MarkdownBlock` content) to avoid visual flicker and ensure a smooth, instant update experience.
SOURCE: https://github.com/textualize/textual/blob/main/docs/blog/posts/release0-12-0.md#_snippet_2

LANGUAGE: python
CODE:
```
with self.app.batch_update():
    await self.query("MarkdownBlock").remove()
    await self.mount_all(output)
```

----------------------------------------

TITLE: Defining Equivalent Textual Message Handlers (Python)
DESCRIPTION: This snippet illustrates the equivalence between defining a Textual message handler using the `@on` decorator and using the `on_` naming convention. Both methods achieve the same result of handling a `Button.Pressed` event.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/events.md#_snippet_2

LANGUAGE: python
CODE:
```
@on(Button.Pressed)
def handle_button_pressed(self):
    ...

def on_button_pressed(self):
    ...
```

----------------------------------------

TITLE: Installing Textual and Development Tools via pip
DESCRIPTION: This command installs the Textual framework and its development tools (`textual-dev`) using pip, the Python package installer. `textual-dev` provides additional utilities for debugging and development.
SOURCE: https://github.com/textualize/textual/blob/main/README.md#_snippet_1

LANGUAGE: Bash
CODE:
```
pip install textual textual-dev
```

----------------------------------------

TITLE: Conditional Variant Rendering (Anti-Pattern) in Python
DESCRIPTION: This snippet illustrates a less preferred approach for handling variant-dependent rendering using a series of `if/elif` statements. While functional, this pattern can become unwieldy and difficult to maintain as the number of variants grows, leading to less modular code.
SOURCE: https://github.com/textualize/textual/blob/main/docs/blog/posts/placeholder-pr.md#_snippet_4

LANGUAGE: Python
CODE:
```
if variant == "default":
    # render the default placeholder
elif variant == "size":
    # render the placeholder with its size
elif variant == "state":
    # render the state of the placeholder
elif variant == "css":
    # render the placeholder with its CSS rules
elif variant == "text":
    # render the placeholder with some text inside
```

----------------------------------------

TITLE: Running Textual App for Console Debugging
DESCRIPTION: Executes a Textual application with the `--dev` switch, directing its `print` output and Textual log messages to a separate `textual console` window. This setup is crucial for effective debugging without overwriting application content.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/devtools.md#_snippet_12

LANGUAGE: bash
CODE:
```
textual run --dev my_app.py
```

----------------------------------------

TITLE: Initializing Header and Footer Widgets in Textual
DESCRIPTION: This code defines a Textual app with a screen and placeholder widgets for the header and footer. It demonstrates the basic structure for setting up the initial layout of a Textual application, focusing on defining the app, screen, and placeholder widgets for header and footer.
SOURCE: https://github.com/textualize/textual/blob/main/docs/how-to/design-a-layout.md#_snippet_0

LANGUAGE: python
CODE:
```
from textual.app import App, ComposeResult
from textual.widgets import Placeholder
from textual.containers import Screen


class Header(Placeholder):
    
```

----------------------------------------

TITLE: Creating Reactive Attributes in Textual
DESCRIPTION: This code demonstrates how to create reactive attributes in a Textual widget using the `reactive` function. It shows examples of creating string, integer, and boolean reactive attributes with default values.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/reactivity.md#_snippet_0

LANGUAGE: Python
CODE:
```
from textual.reactive import reactive
from textual.widget import Widget

class Reactive(Widget):

    name = reactive("Paul")  # (1)!
    count = reactive(0) # (2)!
    is_cool = reactive(True)  # (3)!
```

----------------------------------------

TITLE: Displaying Desktop-Style Notifications in Textual (Python)
DESCRIPTION: This snippet demonstrates how to display a desktop-style notification, often referred to as a 'toast', within a Textual application. It utilizes the `notify()` method, passing a message string and an optional title, to present a temporary informational pop-up to the user. This method is typically invoked from an event handler, such as `on_mount`, when the application component is ready.
SOURCE: https://github.com/textualize/textual/blob/main/docs/blog/posts/release0-30-0.md#_snippet_0

LANGUAGE: Python
CODE:
```
def on_mount(self) -> None:
    self.notify("Hello, from Textual!", title="Welcome")
```

----------------------------------------

TITLE: Smart Refresh Example with Reactive Attributes
DESCRIPTION: This example demonstrates how modifying a reactive attribute triggers an automatic refresh of the widget. The `Name` widget has a reactive `who` attribute, and changes to this attribute cause the widget to re-render.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/reactivity.md#_snippet_3

LANGUAGE: Python
CODE:
```
from textual.app import App, ComposeResult
from textual.reactive import reactive
from textual.widgets import Header, Footer, Input, Static

class Name(Static):

    who = reactive("World")

    def render(self) -> str:
        return f"Hello, {self.who}!"

class RefreshApp(App):

    CSS_PATH = "refresh01.tcss"
    BINDINGS = [("d", "toggle_dark", "Toggle dark mode")]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        yield Name()
        yield Input(placeholder="Enter your name")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        name = self.query_one(Name)
        name.who = event.value or "World"
```

----------------------------------------

TITLE: Running Textual App in Development Mode
DESCRIPTION: Runs a Textual application with the `--dev` switch, enabling development mode features such as live editing of CSS files. Changes to CSS are reflected in the terminal almost immediately upon saving.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/devtools.md#_snippet_10

LANGUAGE: bash
CODE:
```
textual run --dev my_app.py
```

----------------------------------------

TITLE: Centering a Single Widget in Textual Screen (Python)
DESCRIPTION: This Textual Python application demonstrates how to center a single `Button` widget within a `Screen`. It achieves this by applying `align: center middle;` to the `Screen`'s CSS, which centers its child widgets both horizontally and vertically.
SOURCE: https://github.com/textualize/textual/blob/main/docs/FAQ.md#_snippet_1

LANGUAGE: Python
CODE:
```
from textual.app import App, ComposeResult
from textual.widgets import Button

class ButtonApp(App):

    CSS = """
    Screen {
        align: center middle;
    }
    """

    def compose(self) -> ComposeResult:
        yield Button("PUSH ME!")

if __name__ == "__main__":
    ButtonApp().run()
```

----------------------------------------

TITLE: Python Code for Buttons
DESCRIPTION: This Python code creates a Textual app with a container and two buttons (Yes and No) styled with CSS. It demonstrates how to structure a simple Textual application with basic layout and styling.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/CSS.md#_snippet_28

LANGUAGE: python
CODE:
```
from textual.app import App, ComposeResult
from textual.widgets import Static
from textual.containers import Horizontal

class NestingExample(App):
    CSS_PATH = "nesting02.tcss"

    def compose(self) -> ComposeResult:
        yield Horizontal(
            Static("Yes", classes="button affirmative"),
            Static("No", classes="button negative"),
            id="questions",
        )
```

----------------------------------------

TITLE: Adding Columns and Tweets with VerticalScroll
DESCRIPTION: Defines a Column widget by subclassing VerticalScroll to create columns with vertical scrollbars. Adds multiple Tweet placeholder widgets to each column to visualize the layout.
SOURCE: https://github.com/textualize/textual/blob/main/docs/how-to/design-a-layout.md#_snippet_4

LANGUAGE: python
CODE:
```
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, HorizontalScroll, Placeholder, VerticalScroll


class Column(VerticalScroll):
    pass


class Tweet(Placeholder):
    pass


class ColumnsApp(App):
    CSS_PATH = "columns.tcss"
    BINDINGS = [("d", "toggle_dark", "Toggle dark mode")]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        with HorizontalScroll():
            with Column():
                for n in range(4):
                    yield Tweet(f"Tweet {n+1}")
            with Column():
                for n in range(2):
                    yield Tweet(f"Tweet {n+1}")
            with Column():
                for n in range(5):
                    yield Tweet(f"Tweet {n+1}")
            with Column():
                for n in range(3):
                    yield Tweet(f"Tweet {n+1}")


if __name__ == "__main__":
    app = ColumnsApp()
    app.run()
```

----------------------------------------

TITLE: Implementing TimeDisplay Widget in Textual (Python)
DESCRIPTION: This snippet defines the `TimeDisplay` widget, a `Static` subclass in Textual, used to display elapsed time. It leverages Textual's reactive attributes and `set_interval` to automatically update the displayed time, with `on_mount` setting up a timer, `update_time` calculating the current time, and `watch_time` rendering the time string when the `time` attribute changes.
SOURCE: https://github.com/textualize/textual/blob/main/docs/blog/posts/spinners-and-pbs-in-textual.md#_snippet_2

LANGUAGE: Python
CODE:
```
from time import monotonic

from textual.reactive import reactive
from textual.widgets import Static


class TimeDisplay(Static):
    """A widget to display elapsed time."""

    start_time = reactive(monotonic)
    time = reactive(0.0)
    total = reactive(0.0)

    def on_mount(self) -> None:
        """Event handler called when widget is added to the app."""
        self.update_timer = self.set_interval(1 / 60, self.update_time, pause=True)

    def update_time(self) -> None:
        """Method to update time to current."""
        self.time = self.total + (monotonic() - self.start_time)

    def watch_time(self, time: float) -> None:
        """Called when the time attribute changes."""
        minutes, seconds = divmod(time, 60)
        hours, minutes = divmod(minutes, 60)
        self.update(f"{hours:02,.0f}:{minutes:02.0f}:{seconds:05.2f}")
```

----------------------------------------

TITLE: Defining a Custom Command Provider in Textual (Python)
DESCRIPTION: This Python class, `ColorCommands`, extends Textual's `Provider` to add custom commands to the command palette. The `search` method implements fuzzy matching for color names, yielding `Hit` objects that, when selected, post a `SwitchColor` message to the app. It enables users to quickly select colors via the command palette.
SOURCE: https://github.com/textualize/textual/blob/main/docs/blog/posts/release0.37.0.md#_snippet_0

LANGUAGE: python
CODE:
```
class ColorCommands(Provider):
    """A command provider to select colors."""

    async def search(self, query: str) -> Hits:
        """Called for each key."""
        matcher = self.matcher(query)
        for color in COLOR_NAME_TO_RGB.keys():
            score = matcher.match(color)
            if score > 0:
                yield Hit(
                    score,
                    matcher.highlight(color),
                    partial(self.app.post_message, SwitchColor(color)),
                )
```

----------------------------------------

TITLE: Handling Button Variants in Textual (Python)
DESCRIPTION: This Python snippet from the Textual `Button` widget demonstrates how CSS classes are dynamically managed when a button's `variant` attribute changes. The `watch_variant` method removes the old variant's CSS class (prefixed with a hyphen) and adds the new variant's class, ensuring the button's appearance updates correctly based on its state. This pattern is crucial for widgets with different visual styles or states.
SOURCE: https://github.com/textualize/textual/blob/main/docs/blog/posts/placeholder-pr.md#_snippet_0

LANGUAGE: Python
CODE:
```
class Button(Static, can_focus=True):
    # ...

    def watch_variant(self, old_variant: str, variant: str):
        self.remove_class(f"-{old_variant}")
        self.add_class(f"-{variant}")
```

----------------------------------------

TITLE: Setting Widget Visibility via Python `visible` Property
DESCRIPTION: This Python snippet illustrates a convenient boolean shortcut for toggling a Textual widget's visibility. By setting the `widget.visible` property to `False`, the widget becomes invisible, and setting it to `True` makes it visible again.
SOURCE: https://github.com/textualize/textual/blob/main/docs/styles/visibility.md#_snippet_5

LANGUAGE: python
CODE:
```
# Make a widget invisible
widget.visible = False

# Make the widget visible again
widget.visible = True
```

----------------------------------------

TITLE: Validating Reactive Attribute Values in Textual (Python)
DESCRIPTION: This example demonstrates how to use validation methods (methods starting with `validate_`) to check and potentially modify the value assigned to a reactive attribute.  It restricts a count to a range between 0 and 10.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/reactivity.md#_snippet_8

LANGUAGE: python
CODE:
```
--8<-- "docs/examples/guide/reactivity/validate01.py"
```

----------------------------------------

TITLE: Declaring a Threaded Worker in Textual (Python)
DESCRIPTION: This snippet demonstrates how to declare a threaded worker function in Textual version 0.31.0 and later. By setting `thread=True` on the `@work` decorator, the function `run_in_background` will execute in a separate thread, which is required for threaded workers to prevent `WorkerDeclarationError`.
SOURCE: https://github.com/textualize/textual/blob/main/questions/worker-thread-error.question.md#_snippet_0

LANGUAGE: python
CODE:
```
@work(thread=True)
def run_in_background():
    ...
```

----------------------------------------

TITLE: Defining Priority Key Binding in Textual App (Python)
DESCRIPTION: This snippet defines a priority key binding for a Textual application. It binds 'ctrl+q' to the 'quit' action, allowing users to exit the app. The `show=False` parameter prevents it from appearing in the footer, and `priority=True` ensures it's checked before other bindings, making it a global hotkey.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/input.md#_snippet_0

LANGUAGE: Python
CODE:
```
    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit", show=False, priority=True)
    ]
```

----------------------------------------

TITLE: Handling Custom Messages in Textual Main Screen Python
DESCRIPTION: This Python snippet illustrates how the Main screen listens for and reacts to the Activity.Moved message emitted by an Activity widget. Upon receiving the message, it calls save_activity_list(), demonstrating a decoupled way to trigger screen-level actions based on child widget events.
SOURCE: https://github.com/textualize/textual/blob/main/docs/blog/posts/on-dog-food-the-original-metaverse-and-not-being-bored.md#_snippet_3

LANGUAGE: Python
CODE:
```
    def on_activity_moved( self, _: Activity.Moved ) -> None:
        """React to an activity being moved."""
        self.save_activity_list()
```

----------------------------------------

TITLE: Retrieving a Single Widget by ID and Type (Python)
DESCRIPTION: This code uses `query_one` to find a widget with the ID "send" and additionally verifies that the retrieved widget is an instance of the `Button` class. If the matched widget is not a `Button`, a `WrongType` exception is raised, providing type safety and aiding type-checkers like MyPy.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/queries.md#_snippet_1

LANGUAGE: Python
CODE:
```
send_button = self.query_one("#send", Button)
```

----------------------------------------

TITLE: Setting Widget Layout at Runtime (Python)
DESCRIPTION: This Python snippet demonstrates how to dynamically change a Textual widget's layout property at runtime by directly modifying its `styles.layout` attribute. This allows for interactive layout adjustments based on application logic or user input, providing flexibility beyond static CSS declarations.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/layout.md#_snippet_0

LANGUAGE: python
CODE:
```
widget.styles.layout = "vertical"
```

----------------------------------------

TITLE: Adding a Command Provider to a Textual App (Python)
DESCRIPTION: This Python snippet demonstrates how to integrate a custom command provider, `ColorCommands`, into a Textual application. By extending the `App.COMMANDS` set, the `ColorCommands` provider becomes available in the app's command palette, allowing users to access its defined commands.
SOURCE: https://github.com/textualize/textual/blob/main/docs/blog/posts/release0.37.0.md#_snippet_1

LANGUAGE: python
CODE:
```
class ColorApp(App):
    """Experiment with the command palette."""

    COMMANDS = App.COMMANDS | {ColorCommands}
```

----------------------------------------

TITLE: Running Existing Textual Snapshot Tests
DESCRIPTION: This `make` command executes existing snapshot tests to check their current output against historical snapshots. It's typically used after making changes to ensure no regressions have been introduced, allowing for visual inspection of the test results before deciding to update the history.
SOURCE: https://github.com/textualize/textual/blob/main/CONTRIBUTING.md#_snippet_3

LANGUAGE: Shell
CODE:
```
make test-snapshot
```

----------------------------------------

TITLE: Applying Absolute Position and Offset in CSS
DESCRIPTION: This CSS snippet demonstrates how to set a `Label` widget's position to `absolute` and apply an `offset` of `10` units horizontally and `5` units vertically. When `position` is `absolute`, the `offset` is calculated from the top-left corner of the widget's container.
SOURCE: https://github.com/textualize/textual/blob/main/docs/css_types/position.md#_snippet_0

LANGUAGE: css
CODE:
```
Label {
    position: absolute;
    offset: 10 5;
}
```

----------------------------------------

TITLE: Defining a Textual App with Custom Arguments in Python
DESCRIPTION: This snippet illustrates how to define a Textual `App` class (`Greetings`) that accepts custom arguments (`greeting` and `to_greet`) by overriding the `__init__` method. These arguments are stored as instance attributes and then used within the `compose` method to dynamically generate the UI content.
SOURCE: https://github.com/textualize/textual/blob/main/questions/pass-args-to-app.question.md#_snippet_0

LANGUAGE: python
CODE:
```
from textual.app import App, ComposeResult
from textual.widgets import Static

class Greetings(App[None]):

    def __init__(self, greeting: str="Hello", to_greet: str="World") -> None:
        self.greeting = greeting
        self.to_greet = to_greet
        super().__init__()

    def compose(self) -> ComposeResult:
        yield Static(f"{self.greeting}, {self.to_greet}")
```

----------------------------------------

TITLE: Setting Widget Visibility with CSS
DESCRIPTION: These CSS snippets provide direct examples for controlling a widget's display state. They show how to make a widget invisible using `visibility: hidden` and how to ensure it is displayed using `visibility: visible`.
SOURCE: https://github.com/textualize/textual/blob/main/docs/styles/visibility.md#_snippet_3

LANGUAGE: css
CODE:
```
/* Widget is invisible */
visibility: hidden;

/* Widget is visible */
visibility: visible;
```

----------------------------------------

TITLE: Declaring Threaded Workers in Textual Python
DESCRIPTION: This snippet demonstrates how to define a threaded worker function in Textual applications by applying the @work(thread=True) decorator. This ensures the decorated function executes in a separate thread, preventing the main UI thread from blocking during long-running operations. It is required for Textual versions 0.31.0 and later to explicitly declare threaded workers.
SOURCE: https://github.com/textualize/textual/blob/main/docs/FAQ.md#_snippet_3

LANGUAGE: Python
CODE:
```
@work(thread=True)
def run_in_background():
    ...
```

----------------------------------------

TITLE: Watching Reactive Attribute Changes in Textual (Python)
DESCRIPTION: This example demonstrates how to use watch methods (methods starting with `watch_`) to react to changes in reactive attributes. The `watch_color` method is called whenever the `color` attribute changes, updating the background color of the widget.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/reactivity.md#_snippet_10

LANGUAGE: python
CODE:
```
--8<-- "docs/examples/guide/reactivity/watch01.py"
```

----------------------------------------

TITLE: Composing Textual Widgets with Context Managers in Python
DESCRIPTION: This Python snippet refactors the utility containers example to use Textual's context manager syntax (`with` statement) for composing widgets. This approach simplifies the code for adding child widgets to containers like `Horizontal` and `Vertical`, making it generally easier to write and edit compared to positional arguments.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/layout.md#_snippet_3

LANGUAGE: python
CODE:
```
--8<-- "docs/examples/guide/layout/utility_containers_using_with.py"
```

----------------------------------------

TITLE: Writing a Basic Snapshot Test with snap_compare in Python
DESCRIPTION: This snippet demonstrates how to write a basic snapshot test in Textual by injecting the `snap_compare` fixture into a test function. It asserts the comparison of a Textual app's output, specified by its file path, against a saved snapshot. The `snap_compare` fixture supports additional arguments, such as `press`, for simulating user interactions.
SOURCE: https://github.com/textualize/textual/blob/main/notes/snapshot_testing.md#_snippet_0

LANGUAGE: Python
CODE:
```
def test_grid_layout_basic_overflow(snap_compare):
    assert snap_compare("docs/examples/guide/layout/grid_layout2.py")
```

----------------------------------------

TITLE: Running Textual App in Development Mode
DESCRIPTION: This command runs a Textual application in development mode, enabling live editing of CSS styles. Any changes made to the CSS file will be instantly updated in the terminal without restarting the application.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/CSS.md#_snippet_3

LANGUAGE: bash
CODE:
```
textual run my_app.py --dev
```

----------------------------------------

TITLE: Manipulating Colors with Textual's Color Class in Python
DESCRIPTION: This snippet demonstrates the `Color` class from Textual, which provides robust functionality for parsing, manipulating, and converting color formats (e.g., HTML, CSS). It supports various operations like darkening, blending, and converting to different color models (RGB, HSL, Hex), offering a natural and performant way to handle color data without external C dependencies.
SOURCE: https://github.com/textualize/textual/blob/main/docs/blog/posts/steal-this-code.md#_snippet_2

LANGUAGE: Python
CODE:
```
>>> from textual.color import Color
>>> color = Color.parse("lime")
>>> color
Color(0, 255, 0, a=1.0)
>>> color.darken(0.8)
Color(0, 45, 0, a=1.0)
>>> color + Color.parse("red").with_alpha(0.1)
Color(25, 229, 0, a=1.0)
>>> color = Color.parse("#12a30a")
>>> color
Color(18, 163, 10, a=1.0)
>>> color.css
'rgb(18,163,10)'
>>> color.hex
'#12A30A'
>>> color.monochrome
Color(121, 121, 121, a=1.0)
>>> color.monochrome.hex
'#797979'
>>> color.hsl
HSL(h=0.3246187363834423, s=0.8843930635838151, l=0.33921568627450976)
>>>
```

----------------------------------------

TITLE: Using Theme Variables in Textual CSS (CSS)
DESCRIPTION: This CSS snippet demonstrates how to utilize theme-defined variables, such as `$primary` and `$foreground`, within Textual's CSS. These variables automatically update when the application's theme changes, ensuring consistent styling.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/design.md#_snippet_3

LANGUAGE: css
CODE:
```
MyWidget {
    background: $primary;
    color: $foreground;
}
```

----------------------------------------

TITLE: Composing UI Layout in Textual Python
DESCRIPTION: This method defines the initial layout of the Textual TUI application. It adds a `Header`, a `VerticalScroll` container for chat messages (pre-populated with a welcome `Response`), an `Input` widget for user text, and a `Footer`. It uses Textual's declarative layout system.
SOURCE: https://github.com/textualize/textual/blob/main/docs/blog/posts/anatomy-of-a-textual-user-interface.md#_snippet_4

LANGUAGE: Python
CODE:
```
    def compose(self) -> ComposeResult:
        yield Header()
        with VerticalScroll(id="chat-view"):
            yield Response("INTERFACE 2037 READY FOR INQUIRY")
        yield Input(placeholder="How can I help you?")
        yield Footer()
```

----------------------------------------

TITLE: Querying All Widgets of a Specific Type (Python)
DESCRIPTION: This snippet shows how to use the `query` method with a CSS selector to find all widgets of a specific type. In this case, it finds all `Button` widgets within the scope of the calling widget and iterates through them, printing each one.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/queries.md#_snippet_5

LANGUAGE: Python
CODE:
```
for button in self.query("Button"):
    print(button)
```

----------------------------------------

TITLE: Compound Widget Example in Python
DESCRIPTION: This code shows how to create a compound widget by combining an Input and a Label. The `compose` method is used to yield child widgets, creating a reusable widget with a right-aligned label next to an input control.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/widgets.md#_snippet_25

LANGUAGE: python
CODE:
```
    --8<-- "docs/examples/guide/compound/compound01.py"

```

----------------------------------------

TITLE: Setting Custom Return Code on Textual App Exit
DESCRIPTION: This snippet demonstrates how to explicitly set a custom integer return code and an exit message when exiting a Textual application due to a critical error condition. This allows differentiating specific error types from unhandled exceptions.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/app.md#_snippet_5

LANGUAGE: Python
CODE:
```
if critical_error:
    self.exit(return_code=4, message="Critical error occurred")
```

----------------------------------------

TITLE: Updating Layout on Reactive Attribute Change in Textual (Python)
DESCRIPTION: This example demonstrates how to set `layout=True` on a reactive attribute to ensure that the CSS layout updates when the attribute changes. This is crucial for widgets whose size depends on the attribute's value.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/reactivity.md#_snippet_6

LANGUAGE: python
CODE:
```
--8<-- "docs/examples/guide/reactivity/refresh02.py"
```

----------------------------------------

TITLE: Changing Simulated App Screen Size for Testing (Python)
DESCRIPTION: This snippet illustrates how to change the simulated terminal size for a Textual application during testing. By setting the `size` parameter in `app.run_test`, you can test how your app behaves under different screen dimensions.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/testing.md#_snippet_8

LANGUAGE: python
CODE:
```
async with app.run_test(size=(100, 50)) as pilot:
    ...
```

----------------------------------------

TITLE: Using Textual Log Function for Output (Python)
DESCRIPTION: This example demonstrates how to use the `textual.log` function within an `on_mount` event handler to output different types of data. It shows logging simple strings, local variables, key-value pairs, and Rich renderables like `self.tree` to the devtools console.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/devtools.md#_snippet_18

LANGUAGE: python
CODE:
```
def on_mount(self) -> None:
    log("Hello, World")  # simple string
    log(locals())  # Log local variables
    log(children=self.children, pi=3.141592)  # key/values
    log(self.tree)  # Rich renderables
```

----------------------------------------

TITLE: Masked Input Example
DESCRIPTION: This example demonstrates how to use the MaskedInput widget to create a credit card input field with validation and styling. It defines a template mask for a credit card number, which requires 16 digits in groups of 4. The example also shows how to apply custom styling for valid and invalid states.
SOURCE: https://github.com/textualize/textual/blob/main/docs/widgets/masked_input.md#_snippet_0

LANGUAGE: Python
CODE:
```
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, MaskedInput
from textual.containers import Vertical
from textual.css.query import DOMQuery


class MaskedInputApp(App):
    CSS_PATH = "masked_input.tcss"

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="body"):
            yield MaskedInput(
                template="9999-9999-9999-9999",
                placeholder="Credit card number",
                id="credit-card",
            )
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#credit-card").focus()


if __name__ == "__main__":
    app = MaskedInputApp()
    app.run()
```

----------------------------------------

TITLE: Handling Button Presses for Animation Control in Textual (Python)
DESCRIPTION: This Python snippet demonstrates how to handle button press events in a Textual application. It dynamically calls methods on widgets based on button IDs to pause or resume animations and updates the disabled state of the buttons to reflect the current interaction, ensuring only one button is active at a time. It relies on Textual's `query` method and attribute introspection.
SOURCE: https://github.com/textualize/textual/blob/main/docs/blog/posts/spinners-and-pbs-in-textual.md#_snippet_9

LANGUAGE: python
CODE:
```
                getattr(widget, pressed_id)()  # (5)!

            for button in self.query(Button):  # (6)!
                if button.id == pressed_id:
                    button.disabled = True
                else:
                    button.disabled = False


    LiveDisplayApp().run()
```

----------------------------------------

TITLE: Handling Mount and Key Events in Textual App (Python)
DESCRIPTION: This example illustrates how to define event handlers in a Textual application using `on_mount` and `on_key` methods. The `on_mount` handler sets the background color upon app startup, while `on_key` dynamically changes the background based on numeric key presses, demonstrating basic interactivity.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/app.md#_snippet_2

LANGUAGE: python
CODE:
```
from textual.app import App
from textual.events import Key

class MyApp(App):
    def on_mount(self) -> None:
        self.screen.styles.background = "darkblue"

    def on_key(self, event: Key) -> None:
        if event.key.isdigit():
            color_map = {
                "0": "red", "1": "green", "2": "blue",
                "3": "yellow", "4": "purple", "5": "orange",
                "6": "cyan", "7": "magenta", "8": "lime",
                "9": "pink"
            }
            self.screen.styles.background = color_map.get(event.key, "darkblue")

if __name__ == "__main__":
    app = MyApp()
    app.run()
```

----------------------------------------

TITLE: Sending Prompt to LLM with Threaded Worker in Textual (Python)
DESCRIPTION: This method, decorated as a threaded Textual worker, sends the user's prompt to the LLM. It processes the LLM's response in chunks, incrementally updating the `Response` widget's content to create a streaming text effect, ensuring the UI remains responsive.
SOURCE: https://github.com/textualize/textual/blob/main/docs/blog/posts/anatomy-of-a-textual-user-interface.md#_snippet_7

LANGUAGE: Python
CODE:
```
    @work(thread=True)
    def send_prompt(self, prompt: str, response: Response) -> None:
        response_content = ""
        llm_response = self.model.prompt(prompt, system=SYSTEM)
        for chunk in llm_response:
            response_content += chunk
            self.call_from_thread(response.update, response_content)
```

----------------------------------------

TITLE: Textual Message Handler with Event Object (Python)
DESCRIPTION: This handler, defined using the naming convention, accepts a positional argument `message` which is the event object. It uses the `message.color` property to animate the screen's background, demonstrating how to access event-specific data.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/events.md#_snippet_4

LANGUAGE: python
CODE:
```
    def on_color_button_selected(self, message: ColorButton.Selected) -> None:
        self.screen.styles.animate("background", message.color, duration=0.5)
```

----------------------------------------

TITLE: Defining Python Script Dependencies and Initial Setup
DESCRIPTION: This snippet demonstrates how to define Python script dependencies using PEP 0723 comments, allowing automatic environment setup. It also includes essential imports for Textual UI and LLM interaction, and defines a system prompt for the AI agent.
SOURCE: https://github.com/textualize/textual/blob/main/docs/blog/posts/anatomy-of-a-textual-user-interface.md#_snippet_0

LANGUAGE: Python
CODE:
```
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "llm",
#     "textual",
# ]
# ///
from textual import on, work
from textual.app import App, ComposeResult
from textual.widgets import Header, Input, Footer, Markdown
from textual.containers import VerticalScroll
import llm

SYSTEM = """Formulate all responses as if you where the sentient AI named Mother from the Aliens movies."""
```

----------------------------------------

TITLE: Installing Project in Editable Mode with pip
DESCRIPTION: This bash command installs the project in editable mode using pip. The `-e` flag ensures that changes to the source code are immediately reflected without needing to reinstall the package. The `.` specifies that the project is located in the current directory.
SOURCE: https://github.com/textualize/textual/blob/main/docs/how-to/package-with-hatch.md#_snippet_14

LANGUAGE: bash
CODE:
```
pip install -e .
```

----------------------------------------

TITLE: Running a Textual App with Positional and Keyword Arguments in Python
DESCRIPTION: This code demonstrates how to instantiate and run the `Greetings` Textual app, showcasing different ways to pass arguments. It includes examples of running the app with default arguments, using a keyword argument, and providing both positional arguments, highlighting the flexibility of argument passing.
SOURCE: https://github.com/textualize/textual/blob/main/questions/pass-args-to-app.question.md#_snippet_1

LANGUAGE: python
CODE:
```
# Running with default arguments.
Greetings().run()

# Running with a keyword argument.
Greetings(to_greet="davep").run()

# Running with both positional arguments.
Greetings("Well hello", "there").run()
```

----------------------------------------

TITLE: Applying Column Span in Textual Grid Layout (Python/CSS)
DESCRIPTION: This snippet demonstrates how to make a grid cell span multiple columns using Textual's CSS. It assigns an ID to a widget in Python's `compose` method and then applies `column-span: 2;` and `tint: magenta 40%;` in the TUI CSS to expand the widget horizontally and highlight it.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/layout.md#_snippet_10

LANGUAGE: python
CODE:
```
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static
from textual.containers import Container

class GridApp(App):
    CSS_PATH = "grid_layout5_col_span.tcss"

    def compose(self) -> ComposeResult:
        yield Header()
        with Container():
            yield Static("One")
            yield Static("Two", id="two")
            yield Static("Three")
            yield Static("Four")
            yield Static("Five")
            yield Static("Six")
        yield Footer()

if __name__ == "__main__":
    app = GridApp()
    app.run()
```

LANGUAGE: css
CODE:
```
Screen {
    layout: grid;
    grid-size: 3 2;
}

#two {
    column-span: 2;
    tint: magenta 40%;
}
```

----------------------------------------

TITLE: Handling Button Presses with @on Decorator - Python
DESCRIPTION: This Python snippet demonstrates the use of the `@on` decorator in Textual to dispatch messages from multiple buttons to a single method. It shows how to capture button presses for arithmetic operations and update the application state accordingly.
SOURCE: https://github.com/textualize/textual/blob/main/docs/blog/posts/release0-24-0.md#_snippet_0

LANGUAGE: python
CODE:
```
    @on(Button.Pressed, "#plus,#minus,#divide,#multiply")
    def pressed_op(self, event: Button.Pressed) -> None:
        """Pressed one of the arithmetic operations."""
        self.right = Decimal(self.value or "0")
        self._do_math()
        assert event.button.id is not None
        self.operator = event.button.id
```

----------------------------------------

TITLE: Static Widget with Content Update in Textual (Python)
DESCRIPTION: This code defines a custom widget named `Hello` that extends the `Static` widget class. It cycles through greetings in different languages when clicked. The `update` method is used to change the content of the widget, and a click handler is used to trigger the update.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/widgets.md#_snippet_3

LANGUAGE: Python
CODE:
```
class Hello(Static):
    
```

----------------------------------------

TITLE: Filtering Textual Query Objects
DESCRIPTION: This snippet illustrates the `filter()` method, which refines an existing Textual DOMQuery object. It first queries for all 'Button' widgets and then applies a filter using '.disabled' to create a new query object containing only those buttons that also possess the specified CSS class. This allows for building more specific queries from broader ones.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/queries.md#_snippet_10

LANGUAGE: python
CODE:
```
# Get all the Buttons
buttons_query = self.query("Button")
# Buttons with 'disabled' CSS class
disabled_buttons = buttons_query.filter(".disabled")
```

----------------------------------------

TITLE: Excluding Widgets from Textual Query Objects
DESCRIPTION: This example demonstrates the `exclude()` method, which removes widgets matching a specified selector from an existing Textual DOMQuery object. It first queries for all 'Button' widgets and then excludes any that possess the '.disabled' CSS class. This effectively yields a query object containing only 'enabled' buttons.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/queries.md#_snippet_11

LANGUAGE: python
CODE:
```
# Get all the Buttons
buttons_query = self.query("Button")
# Remove all the Buttons with the 'disabled' CSS class
enabled_buttons = buttons_query.exclude(".disabled")
```

----------------------------------------

TITLE: Handling Worker State Change Events in Textual (Python)
DESCRIPTION: This snippet demonstrates how to handle Worker.StateChanged events in a Textual application. By defining an on_worker_state_changed method, the application can react to changes in a worker's lifecycle, such as logging its current state (PENDING, RUNNING, SUCCESS, ERROR, CANCELLED). This is crucial for monitoring long-running operations and providing user feedback.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/workers.md#_snippet_0

LANGUAGE: python
CODE:
```
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Button, Label
from textual.worker import WorkerState, work
import httpx
import asyncio

class WeatherApp(App):
    BINDINGS = [("q", "quit", "Quit")]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        yield Button("Get Weather", id="get_weather")
        yield Label("Weather: N/A", id="weather_label")

    @work(exclusive=True)
    async def get_weather_data(self) -> str:
        async with httpx.AsyncClient() as client:
            response = await client.get("https://api.weather.gov/points/39.7456,-97.0892")
            response.raise_for_status()
            data = response.json()
            return data["properties"]["relativeLocation"]["properties"]["city"]

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "get_weather":
            self.run_worker(self.get_weather_data(), exit_on_error=False)

    def on_worker_state_changed(self, event: WorkerState.StateChanged) -> None:
        """Handle worker state changes."""
        self.log(f"Worker {event.worker.name} changed state to {event.state.name}")
        if event.state == WorkerState.SUCCESS:
            self.query_one("#weather_label", Label).update(f"Weather: {event.worker.result}")
        elif event.state == WorkerState.ERROR:
            self.query_one("#weather_label", Label).update(f"Error: {event.worker.error}")
        elif event.state == WorkerState.CANCELLED:
            self.query_one("#weather_label", Label).update("Weather: Cancelled")

if __name__ == "__main__":
    app = WeatherApp()
    app.run()
```

----------------------------------------

TITLE: Changing Theme Programmatically in Textual App (Python)
DESCRIPTION: This snippet demonstrates how to programmatically change the active theme of a Textual application by setting the `App.theme` attribute within the `on_mount` method. This allows for dynamic theme updates at runtime.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/design.md#_snippet_0

LANGUAGE: python
CODE:
```
class MyApp(App):
    def on_mount(self) -> None:
        self.theme = "nord"
```

----------------------------------------

TITLE: Creating an Inline Code Editor with Textual Python
DESCRIPTION: This Textual application demonstrates how to create an inline code editor using the TextArea widget. It configures the TextArea to automatically adjust its height up to 50% of the viewport height. The run(inline=True) method is crucial for making the application appear directly under the terminal prompt rather than occupying the full screen, showcasing Textual's inline app capability.
SOURCE: https://github.com/textualize/textual/blob/main/docs/blog/posts/inline-mode.md#_snippet_0

LANGUAGE: python
CODE:
```
from textual.app import App, ComposeResult
from textual.widgets import TextArea


class InlineApp(App):
    CSS = """
    TextArea {
        height: auto;
        max-height: 50vh;
    }
    """

    def compose(self) -> ComposeResult:
        yield TextArea(language="python")


if __name__ == "__main__":
    InlineApp().run(inline=True)
```

----------------------------------------

TITLE: Searching Entire Screen for a Widget (Python)
DESCRIPTION: This example illustrates how to perform a `query_one` operation on the `self.screen` instance to search the entire DOM of the current screen. This ensures that the query covers all widgets within the screen, rather than just descendants of a specific widget.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/queries.md#_snippet_3

LANGUAGE: Python
CODE:
```
self.screen.query_one("#send-email")
```

----------------------------------------

TITLE: Posting a Message from a Widget in Textual
DESCRIPTION: This Python code shows how to post a message from a widget in a Textual application. The on_click method posts a custom message (MyWidget.Change) to the parent widget when the widget is clicked, indicating that the widget's active state has changed to True.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/widgets.md#_snippet_28

LANGUAGE: python
CODE:
```
def on_click(self):
    self.post_message(MyWidget.Change(active=True))
```

----------------------------------------

TITLE: Customizing Textual App Initialization in Python
DESCRIPTION: This code defines a Textual App subclass, Greetings, demonstrating how to customize its initialization by overriding the __init__ method to accept custom greeting and to_greet arguments. These arguments are then used within the compose method to dynamically generate the application's initial content. It requires textual.app.App, ComposeResult, and textual.widgets.Static.
SOURCE: https://github.com/textualize/textual/blob/main/docs/FAQ.md#_snippet_5

LANGUAGE: Python
CODE:
```
from textual.app import App, ComposeResult
from textual.widgets import Static

class Greetings(App[None]):

    def __init__(self, greeting: str="Hello", to_greet: str="World") -> None:
        self.greeting = greeting
        self.to_greet = to_greet
        super().__init__()

    def compose(self) -> ComposeResult:
        yield Static(f"{self.greeting}, {self.to_greet}")
```

----------------------------------------

TITLE: Pride Example in Textual
DESCRIPTION: This example demonstrates the 'pride.py' application built with the Textual framework. It showcases how to create visually appealing terminal applications using Textual's Python API.
SOURCE: https://github.com/textualize/textual/blob/main/docs/index.md#_snippet_0

LANGUAGE: Python
CODE:
```
--8<-- "examples/pride.py"
```

----------------------------------------

TITLE: Dynamically Updating App Title and Subtitle in Textual (Python)
DESCRIPTION: This Python example shows how to programmatically change a Textual application's title and subtitle during runtime. It illustrates updating the title and sub_title attributes within an event handler (e.g., a key press), demonstrating Textual's reactivity for dynamic UI updates.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/app.md#_snippet_11

LANGUAGE: python
CODE:
```
--8<-- "docs/examples/app/question_title02.py"
```

----------------------------------------

TITLE: Targeting Child Widgets by State (Textual CSS)
DESCRIPTION: Illustrates how to combine a CSS class selector (`.started`) with an ID selector (`#start`) to target a specific child widget (the start button) only when its parent has the specified class. This rule hides the start button when the stopwatch is in the 'started' state.
SOURCE: https://github.com/textualize/textual/blob/main/docs/tutorial.md#_snippet_8

LANGUAGE: css
CODE:
```
.started #start {
    display: none
}
```

----------------------------------------

TITLE: Example pyproject.toml [project] Section
DESCRIPTION: Shows the basic structure of the `[project]` section in `pyproject.toml`, including metadata like name, version, description, and dependencies.
SOURCE: https://github.com/textualize/textual/blob/main/docs/how-to/package-with-hatch.md#_snippet_5

LANGUAGE: TOML
CODE:
```
[project]
name = "textual-calculator"
dynamic = ["version"]
description = 'A example app'
readme = "README.md"
requires-python = ">=3.8"
license = "MIT"
keywords = []
authors = [
  { name = "Will McGugan", email = "redacted@textualize.io" },
]
classifiers = [
  "Development Status :: 4 - Beta",
  "Programming Language :: Python",
  "Programming Language :: Python :: 3.8",
  "Programming Language :: Python :: 3.9",
  "Programming Language :: Python :: 3.10",
  "Programming Language :: Python :: 3.11",
  "Programming Language :: Python :: 3.12",
  "Programming Language :: Python :: Implementation :: CPython",
  "Programming Language :: Python :: Implementation :: PyPy",
]
dependencies = []
```

----------------------------------------

TITLE: Exiting Textual App with System Return Code
DESCRIPTION: This example shows how to correctly exit a Textual application process with a system return code. It retrieves the app's internal `return_code` (or defaults to 0 for success) and passes it to `sys.exit()` to terminate the process with the desired status.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/app.md#_snippet_6

LANGUAGE: Python
CODE:
```
if __name__ == "__main__"
    app = MyApp()
    app.run()
    import sys
    sys.exit(app.return_code or 0)
```

----------------------------------------

TITLE: Styling Textual UI Components with Sass/CSS
DESCRIPTION: This Sass/CSS snippet defines the visual layout and styling for various Textual UI components, including `Screen`, `Horizontal` containers, `Button` elements, `Grid` layouts, and `IntervalUpdater` widgets. It uses properties like `align`, `height`, `margin`, `grid-size`, and `border` to control positioning, spacing, and appearance within the Textual application.
SOURCE: https://github.com/textualize/textual/blob/main/docs/blog/posts/spinners-and-pbs-in-textual.md#_snippet_10

LANGUAGE: css
CODE:
```
    Screen {
        align: center middle;
    }

    Horizontal {
        height: 1fr;
        align-horizontal: center;
    }

    Button {
        margin: 0 3 0 3;
    }

    Grid {
        height: 4fr;
        align: center middle;
        grid-size: 3 2;
        grid-columns: 8;
        grid-rows: 1;
        grid-gutter: 1;
        border: gray double;
    }

    IntervalUpdater {
        content-align: center middle;
    }
```

----------------------------------------

TITLE: Mounting Widgets with `before` and `after` Parameters in Textual Python
DESCRIPTION: This snippet demonstrates the updated `mount` method in Textual, showcasing how to precisely position new widgets using the `before` and `after` parameters. It illustrates mounting a `Button` at the beginning, a `Static` widget after a CSS selector, and another `Static` widget after a specific existing widget object. This provides more intuitive control over widget placement compared to previous versions.
SOURCE: https://github.com/textualize/textual/blob/main/docs/blog/posts/release0-4-0.md#_snippet_0

LANGUAGE: Python
CODE:
```
# Mount at the start
self.mount(Button(id="Buy Coffee"), before=0)

# Mount after a selector
self.mount(Static("Password is incorrect"), after="Dialog Input.-error")

# Mount after a specific widget
tweet = self.query_one("Tweet")
self.mount(Static("Consider switching to Mastodon"), after=tweet)
```

----------------------------------------

TITLE: Applying Bold Style with Textual Markup
DESCRIPTION: This example shows how to apply bold formatting to a specific part of a string using Textual content markup. The text enclosed between `[bold]` and `[/bold]` tags will appear bold, while the rest of the string remains unstyled.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/content.md#_snippet_4

LANGUAGE: Textual Markup
CODE:
```
[bold]Hello[/bold], World!
```

----------------------------------------

TITLE: Removing Row Below Cursor in Textual DataTable (Python)
DESCRIPTION: This snippet demonstrates how to remove a specific row from a Textual DataTable based on the current cursor position. It uses `coordinate_to_cell_key` to obtain the `row_key` from the `cursor_coordinate` and then passes this key to the `remove_row` method. This operation requires an instance of a `DataTable` widget.
SOURCE: https://github.com/textualize/textual/blob/main/docs/widgets/data_table.md#_snippet_0

LANGUAGE: python
CODE:
```
# Get the keys for the row and column under the cursor.
row_key, _ = table.coordinate_to_cell_key(table.cursor_coordinate)
# Supply the row key to `remove_row` to delete the row.
table.remove_row(row_key)
```

----------------------------------------

TITLE: Querying Widgets with Complex CSS Selector (Python)
DESCRIPTION: This example demonstrates using a more complex CSS selector with the `query` method to find specific widgets. It targets all `Button` widgets that have the CSS class `disabled` and are descendants of a `Dialog` widget, then iterates and prints them.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/queries.md#_snippet_6

LANGUAGE: Python
CODE:
```
for button in self.query("Dialog Button.disabled"):
    print(button)
```

----------------------------------------

TITLE: Defining a Fixed-Size Grid Layout in Textual Python
DESCRIPTION: This Python snippet demonstrates how to create a fixed-size grid layout in Textual using the `grid` layout. It shows how to define a 3x2 grid and populate its cells with six widgets, which are inserted from left-to-right and top-to-bottom.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/layout.md#_snippet_6

LANGUAGE: python
CODE:
```
--8<-- "docs/examples/guide/layout/grid_layout1.py"
```

----------------------------------------

TITLE: Composing Widgets (New Syntax) - Textual Python
DESCRIPTION: This snippet illustrates the new, preferred way to compose widgets in Textual using context managers. It allows for a more readable and editable structure, where child widgets are simply indented within their parent's `with` block, reducing lines of code and presenting attributes on the same line as containers.
SOURCE: https://github.com/textualize/textual/blob/main/docs/blog/posts/release0-12-0.md#_snippet_1

LANGUAGE: python
CODE:
```
for color_name in ColorSystem.COLOR_NAMES:
    with ColorGroup(id=f"group-{color_name}"):
        yield Label(f'"{color_name}"')
        for level in LEVELS:
            color = f"{color_name}-{level}" if level else color_name
            with ColorItem(classes=color):
                yield ColorBar(f"${color}", classes="text label")
                yield ColorBar("$text-muted", classes="muted")
                yield ColorBar("$text-disabled", classes="disabled")
```

----------------------------------------

TITLE: Implementing Reactive Attributes in Textual Python
DESCRIPTION: This snippet demonstrates adding reactive attributes (`start_time`, `time`) to a Textual widget (`TimeDisplay`). It shows how to initialize them, use `set_interval` in `on_mount` to periodically update a reactive attribute (`time`), and implement a `watch_time` method that automatically updates the widget's display whenever the `time` attribute changes.
SOURCE: https://github.com/textualize/textual/blob/main/docs/tutorial.md#_snippet_10

LANGUAGE: python
CODE:
```
from textual.reactive import reactive
from textual.widget import Widget
from time import monotonic

class TimeDisplay(Widget):
    """A widget to display elapsed time."""

    start_time = reactive(monotonic)
    time = reactive(0.0)

    def on_mount(self) -> None:
        """Called when the widget is added to the app."""
        self.set_interval(1 / 60, self.update_time)

    def update_time(self) -> None:
        """Method to update the time attribute."""
        self.time = monotonic() - self.start_time

    def watch_time(self, time: float) -> None:
        """Called when the time attribute changes."""
        minutes, seconds = divmod(time, 60)
        hours, minutes = divmod(minutes, 60)
        self.update(f"{hours:02.0f}:{minutes:02.0f}:{seconds:05.2f}")

# Example usage (simplified, assumes a Textual App context)
# app = App()
# app.mount(TimeDisplay())
# app.run()
```

----------------------------------------

TITLE: Dynamically Watching Reactive Attributes in Textual (Python)
DESCRIPTION: This example demonstrates how to dynamically add watchers to reactive attributes using the `watch` method.  This allows reacting to changes in reactive attributes for which you can't edit the watch methods directly. The app watches the `counter` attribute of a `Counter` widget and updates a progress bar accordingly.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/reactivity.md#_snippet_12

LANGUAGE: python
CODE:
```
--8<-- "docs/examples/guide/reactivity/dynamic_watch.py"
```

----------------------------------------

TITLE: Abstracting Animated Widgets with IntervalUpdater - Python
DESCRIPTION: This Python snippet introduces the `IntervalUpdater` class, designed to abstract common animation logic for Textual widgets. It manages the regular updating of a `_renderable_object` via `set_interval`, allowing subclasses like `IndeterminateProgressBar` and `SpinnerWidget` to define their specific Rich renderables for animation. This promotes code reuse for regularly updating UI components.
SOURCE: https://github.com/textualize/textual/blob/main/docs/blog/posts/spinners-and-pbs-in-textual.md#_snippet_7

LANGUAGE: Python
CODE:
```
from rich.progress import Progress, BarColumn
from rich.spinner import Spinner

from textual.app import RenderableType
from textual.widgets import Button, Static


class IntervalUpdater(Static):
    _renderable_object: RenderableType  # (1)!

    def update_rendering(self) -> None:  # (2)!
        self.update(self._renderable_object)

    def on_mount(self) -> None:  # (3)!
        self.interval_update = self.set_interval(1 / 60, self.update_rendering)


class IndeterminateProgressBar(IntervalUpdater):
    """Basic indeterminate progress bar widget based on rich.progress.Progress."""
    def __init__(self) -> None:
        super().__init__("")
        self._renderable_object = Progress(BarColumn())  # (4)!
        self._renderable_object.add_task("", total=None)


class SpinnerWidget(IntervalUpdater):
    """Basic spinner widget based on rich.spinner.Spinner."""
    def __init__(self, style: str) -> None:
        super().__init__("")
        self._renderable_object = Spinner(style)  # (5)!
```

----------------------------------------

TITLE: Using mutate_reactive with Reactive List
DESCRIPTION: This example demonstrates how to use `mutate_reactive` to notify Textual of changes to a mutable reactive object (in this case, a list).  Without `mutate_reactive`, Textual won't detect changes made to the list's contents, and the display won't update. The example creates a reactive list of strings and appends a new name to it, triggering an update via `mutate_reactive`.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/reactivity.md#_snippet_21

LANGUAGE: python
CODE:
```
from textual.app import App, ComposeResult
from textual.widgets import Input
from textual.reactive import reactive

class InputApp(App):

    names: reactive[list[str]] = reactive(["Will"])

    def compose(self) -> ComposeResult:
        yield Input(placeholder="Enter your name")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        name = event.value
        self.names.append(name)
        self.mutate_reactive("names")

        event.control.value = ""

if __name__ == "__main__":
    app = InputApp()
    app.run()
```

----------------------------------------

TITLE: Adding Pause/Resume Functionality to Animated Widgets - Python
DESCRIPTION: This Python snippet extends the `IntervalUpdater` class with `pause()` and `resume()` methods, enabling control over the widget's animation interval. It demonstrates their usage within a `LiveDisplayApp` that composes multiple animated widgets and provides interactive 'Pause' and 'Resume' buttons to control their animations, showcasing dynamic UI control in Textual applications.
SOURCE: https://github.com/textualize/textual/blob/main/docs/blog/posts/spinners-and-pbs-in-textual.md#_snippet_8

LANGUAGE: Python
CODE:
```
from rich.progress import Progress, BarColumn
from rich.spinner import Spinner

from textual.app import App, ComposeResult, RenderableType
from textual.containers import Grid, Horizontal, Vertical
from textual.widgets import Button, Static


class IntervalUpdater(Static):
    _renderable_object: RenderableType

    def update_rendering(self) -> None:
        self.update(self._renderable_object)

    def on_mount(self) -> None:
        self.interval_update = self.set_interval(1 / 60, self.update_rendering)

    def pause(self) -> None:  # (1)!
        self.interval_update.pause()

    def resume(self) -> None:  # (2)!
        self.interval_update.resume()


class IndeterminateProgressBar(IntervalUpdater):
    """Basic indeterminate progress bar widget based on rich.progress.Progress."""
    def __init__(self) -> None:
        super().__init__("")
        self._renderable_object = Progress(BarColumn())
        self._renderable_object.add_task("", total=None)


class SpinnerWidget(IntervalUpdater):
    """Basic spinner widget based on rich.spinner.Spinner."""
    def __init__(self, style: str) -> None:
        super().__init__("")
        self._renderable_object = Spinner(style)


class LiveDisplayApp(App[None]):
    """App showcasing some widgets that update regularly."""
    CSS_PATH = "myapp.css"

    def compose(self) -> ComposeResult:
        yield Vertical(
                Grid(
                    SpinnerWidget("moon"),
                    IndeterminateProgressBar(),
                    SpinnerWidget("aesthetic"),
                    SpinnerWidget("bouncingBar"),
                    SpinnerWidget("earth"),
                    SpinnerWidget("dots8Bit"),
                ),
                Horizontal(
                    Button("Pause", id="pause"),  # (3)!
                    Button("Resume", id="resume", disabled=True),
                ),
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:  # (4)!
        pressed_id = event.button.id
        assert pressed_id is not None
        for widget in self.query(IntervalUpdater):
```

----------------------------------------

TITLE: Custom Widget with CSS Styling in Textual (Python)
DESCRIPTION: This code defines a Textual app that includes a custom widget (`Hello`) and applies CSS styling to it. The CSS targets the `Hello` widget and sets its background color to green.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/widgets.md#_snippet_1

LANGUAGE: Python
CODE:
```
class Hello(Widget):
    
```

----------------------------------------

TITLE: Implementing Placeholder Variant Cycling in Textual (Python)
DESCRIPTION: This snippet defines the `Placeholder` class, a Textual `Static` widget. It demonstrates how to initialize the widget with a specific display variant and set up an `itertools.cycle` to manage variant transitions. The `on_click` method triggers `cycle_variant`, which updates the placeholder's variant to the next one in the predefined cycle, ensuring the correct starting point for the cycle upon instantiation.
SOURCE: https://github.com/textualize/textual/blob/main/docs/blog/posts/placeholder-pr.md#_snippet_1

LANGUAGE: python
CODE:
```
class Placeholder(Static):
    def __init__(
        self,
        variant: PlaceholderVariant = "default",
        *,
        label: str | None = None,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        # ...

        self.variant = self.validate_variant(variant)
        # Set a cycle through the variants with the correct starting point.
        self._variants_cycle = cycle(_VALID_PLACEHOLDER_VARIANTS_ORDERED)
        while next(self._variants_cycle) != self.variant:
            pass

    def on_click(self) -> None:
        """Click handler to cycle through the placeholder variants."""
        self.cycle_variant()

    def cycle_variant(self) -> None:
        """Get the next variant in the cycle."""
        self.variant = next(self._variants_cycle)
```

----------------------------------------

TITLE: Defining Margin Syntax in CSS
DESCRIPTION: This snippet outlines the syntax for the `margin` property in CSS, showing how it can accept one, two, or four integer values to define spacing for all edges, top/bottom and left/right, or top, right, bottom, and left edges respectively. It also includes the syntax for individual margin properties like `margin-top`, `margin-right`, `margin-bottom`, and `margin-left`.
SOURCE: https://github.com/textualize/textual/blob/main/docs/styles/margin.md#_snippet_0

LANGUAGE: CSS
CODE:
```
margin: <integer>
      # one value for all edges
      | <integer> <integer>
      # top/bot   left/right
      | <integer> <integer> <integer> <integer>;
      # top       right     bot       left

margin-top: <integer>;
margin-right: <integer>;
margin-bottom: <integer>;
margin-left: <integer>;
```

----------------------------------------

TITLE: Setting Widget Styles in Python
DESCRIPTION: This snippet demonstrates the programmatic approach to setting style properties on a widget in Python. It shows how to assign various types of values, including tuples for complex syntax, to 'property_name' and 'property_name_variant' attributes of a widget's 'styles' object. This serves as a template for documenting how to set specific styles programmatically.
SOURCE: https://github.com/textualize/textual/blob/main/docs/styles/_template.md#_snippet_1

LANGUAGE: python
CODE:
```
widget.styles.property_name = value1
widget.styles.property_name = value2
widget.styles.property_name = (different_syntax_value, shown_here)

widget.styles.property_name_variant = value3
widget.styles.property_name_variant = value4
```

----------------------------------------

TITLE: Loading Indicator Example
DESCRIPTION: This example demonstrates how to use the loading reactive property to display a LoadingIndicator widget while data is being fetched. It simulates a network request with a sleep and toggles the loading property to show and hide the indicator.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/widgets.md#_snippet_18

LANGUAGE: python
CODE:
```
import asyncio
import random

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, DataTable


class LoadingApp(App):
    
```

----------------------------------------

TITLE: Creating a Basic Textual Snapshot Test in Python
DESCRIPTION: This snippet demonstrates how to create a basic snapshot test for a Textual application using the `snap_compare` pytest fixture. It asserts that the current visual output of the specified Textual app matches a previously saved snapshot, or generates a new one on the first run. The `path/to/calculator.py` parameter specifies the relative path to the Textual application file.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/testing.md#_snippet_10

LANGUAGE: python
CODE:
```
def test_calculator(snap_compare):
    assert snap_compare("path/to/calculator.py")
```

----------------------------------------

TITLE: Running Textual App from Python Module
DESCRIPTION: Runs a Textual application by importing it from a Python module. This command assumes a Textual app instance named `app` exists within the specified module (e.g., `music.play`).
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/devtools.md#_snippet_3

LANGUAGE: bash
CODE:
```
textual run music.play
```

----------------------------------------

TITLE: CSS Selector Example
DESCRIPTION: This CSS selector targets the Textual widget defined by the Python class `Header`. Styles within this rule set will be applied to all Header widgets in the application.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/CSS.md#_snippet_1

LANGUAGE: css
CODE:
```
Header {
  dock: top;
  height: 3;
  content-align: center middle;
  background: blue;
  color: white;
}
```

----------------------------------------

TITLE: CSS Pseudo-class Hover Example
DESCRIPTION: This CSS rule uses the `:hover` pseudo-class to change the background color of a Button to green when the mouse cursor is over it.  Pseudo-classes allow styling widgets based on their state.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/CSS.md#_snippet_15

LANGUAGE: css
CODE:
```
Button:hover {
  background: green;
}
```

----------------------------------------

TITLE: Registering and Applying a Custom Theme in Textual App (Python)
DESCRIPTION: This snippet illustrates how to register a custom theme using `App.register_theme` and then apply it to the application by setting `self.theme`. Registration makes the theme available, and setting `self.theme` immediately updates the app's appearance.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/design.md#_snippet_2

LANGUAGE: python
CODE:
```
from textual.app import App

class MyApp(App):
    def on_mount(self) -> None:
        # Register the theme
        self.register_theme(arctic_theme)  # (1)!

        # Set the app's theme
        self.theme = "arctic"  # (2)!
```

----------------------------------------

TITLE: Assigning IDs to TabPane for Programmatic Switching - Python
DESCRIPTION: This snippet illustrates how to assign unique `id` attributes to TabPane widgets. Providing an ID is crucial for programmatically switching between tabs, as it allows direct referencing of specific tabs. If IDs are not provided, Textual assigns default sequential IDs like 'tab-1', 'tab-2', etc.
SOURCE: https://github.com/textualize/textual/blob/main/docs/widgets/tabbed_content.md#_snippet_2

LANGUAGE: python
CODE:
```
def compose(self) -> ComposeResult:
    with TabbedContent():
        with TabPane("Leto", id="leto"):
            yield Markdown(LETO)
        with TabPane("Jessica", id="jessica"):
            yield Markdown(JESSICA)
        with TabPane("Paul", id="paul"):
            yield Markdown(PAUL)
```

----------------------------------------

TITLE: Direct CSS Background Style Examples
DESCRIPTION: Provides various examples of setting the `background` style directly in CSS, including named colors, colors with opacity percentages, and RGB/HSL color formats. These snippets illustrate the flexibility of the `background` property for different visual effects.
SOURCE: https://github.com/textualize/textual/blob/main/docs/styles/background.md#_snippet_5

LANGUAGE: css
CODE:
```
/* Blue background */
background: blue;

/* 20% red background */
background: red 20%;

/* RGB color */
background: rgb(100, 120, 200);

/* HSL color */
background: hsl(290, 70%, 80%);
```

----------------------------------------

TITLE: Configuring Entry Point in pyproject.toml
DESCRIPTION: This TOML configuration specifies the entry point for the calculator application. It maps the `calculator` command to the `calculator` function within the `textual_calculator.entry_points` module, enabling the application to be run from the command line using the `calculator` command.
SOURCE: https://github.com/textualize/textual/blob/main/docs/how-to/package-with-hatch.md#_snippet_12

LANGUAGE: toml
CODE:
```
[project.scripts]
calculator = "textual_calculator.entry_points:calculator"
```

----------------------------------------

TITLE: Using Fraction Unit for Proportional Sizing in Textualize CSS
DESCRIPTION: This example illustrates the use of the 'fr' unit to define proportional sizes. Widgets with 'fr' values will distribute available space proportionally, where a higher 'fr' value indicates a larger share of the space.
SOURCE: https://github.com/textualize/textual/blob/main/docs/css_types/scalar.md#_snippet_1

LANGUAGE: CSS
CODE:
```
width: 1fr
```

LANGUAGE: CSS
CODE:
```
width: 3fr
```

----------------------------------------

TITLE: Using FR Units for Flexible Layout in Textual
DESCRIPTION: This code demonstrates how to use FR units to create a flexible layout in a Textual application, ensuring that the central area resizes with the terminal window. It shows how to set the width and height of a widget to `1fr` to divide the remaining space equally among the widgets.
SOURCE: https://github.com/textualize/textual/blob/main/docs/how-to/design-a-layout.md#_snippet_2

LANGUAGE: python
CODE:
```
from textual.app import App, ComposeResult
from textual.widgets import Placeholder
from textual.containers import Screen
from textual import css


class Header(Placeholder):
    
```

----------------------------------------

TITLE: Defining a Simple Textual Action Method (Python)
DESCRIPTION: This snippet demonstrates how to define a basic action method in a Textual application. The `action_set_background` method changes the screen's background color. It also shows a key handler that directly calls this action method when the 'r' key is pressed, illustrating that action methods are regular callable functions.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/actions.md#_snippet_0

LANGUAGE: python
CODE:
```
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static

class ActionsApp(App):
    def action_set_background(self, color: str) -> None:
        self.screen.styles.background = color

    async def on_key(self, event) -> None:
        if event.key == "r":
            self.action_set_background("red")

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        yield Static("Press 'r' to set background to red.")

if __name__ == "__main__":
    ActionsApp().run()
```

----------------------------------------

TITLE: Styling for Dark Mode in Textual 0.38.0 with Pseudo Selector (CSS)
DESCRIPTION: This CSS snippet shows the improved, more concise syntax for applying styles when the Textual application is in dark mode, introduced in version 0.38.0. It uses the new `:dark` pseudo selector directly on `MyWidget` to target `Label` elements, making theme-dependent styling more readable and straightforward.
SOURCE: https://github.com/textualize/textual/blob/main/docs/blog/posts/release0-38-0.md#_snippet_2

LANGUAGE: css
CODE:
```
MyWidget:dark Label {
    ...
}
```

----------------------------------------

TITLE: Applying Colors in Textual CSS
DESCRIPTION: This CSS snippet illustrates various ways to apply colors to Textual elements using CSS rules. It shows examples of using named colors, Textual variables (e.g., `$accent`), and HSL descriptions for properties like `background`, `color`, and `tint` to style different components.
SOURCE: https://github.com/textualize/textual/blob/main/docs/css_types/color.md#_snippet_1

LANGUAGE: css
CODE:
```
Header {
    background: red;           /* Color name */
}

.accent {
    color: $accent;            /* Textual variable */
}

#footer {
    tint: hsl(300, 20%, 70%);  /* HSL description */
}
```

----------------------------------------

TITLE: Getting Last Widget with Type Check in Textual
DESCRIPTION: This example shows how to use `last()` with an `expect_type` argument to retrieve the last widget matching a selector while also verifying its class. It queries for elements with the '.disabled' CSS class and ensures the last match is specifically a `Button` instance, raising a `WrongType` exception if the type does not match.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/queries.md#_snippet_9

LANGUAGE: python
CODE:
```
disabled_button = self.query(".disabled").last(Button)
```

----------------------------------------

TITLE: Common Docking Styles in Textual CSS
DESCRIPTION: This snippet provides practical examples of how to apply the `dock` property in Textual CSS. It demonstrates fixing a widget to the bottom, left, right, or top edge of its parent container, along with inline comments explaining each option.
SOURCE: https://github.com/textualize/textual/blob/main/docs/styles/dock.md#_snippet_1

LANGUAGE: css
CODE:
```
dock: bottom;  /* Docks on the bottom edge of the parent container. */
dock: left;    /* Docks on the   left edge of the parent container. */
dock: right;   /* Docks on the  right edge of the parent container. */
dock: top;     /* Docks on the    top edge of the parent container. */
```

----------------------------------------

TITLE: FizzBuzz Table Widget with Rich
DESCRIPTION: This example demonstrates how to create a Textual widget that displays a FizzBuzz table using Rich renderables. It showcases the use of a Rich table as widget content to visualize the FizzBuzz sequence.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/widgets.md#_snippet_13

LANGUAGE: python
CODE:
```
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer
from textual.widget import Widget
from rich.table import Table


class FizzBuzz(Widget):
    
```

----------------------------------------

TITLE: Importing Textual Log Function (Python)
DESCRIPTION: This line imports the `log` function directly from the `textual` library. The `log` function is designed for pretty-printing various data structures and any content that Rich can display to the Textual devtools console.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/devtools.md#_snippet_17

LANGUAGE: python
CODE:
```
from textual import log
```

----------------------------------------

TITLE: Handling Asynchronous Widget Mounting Issues in Textual Python
DESCRIPTION: This snippet demonstrates a common issue when dynamically mounting widgets in Textual. It attempts to query and modify a child widget (Button) immediately after calling `self.mount(Welcome())` without awaiting, which often leads to a `NoMatches` exception because the widget has not yet been fully mounted and rendered.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/app.md#_snippet_3

LANGUAGE: python
CODE:
```
from textual.app import App
from textual.widgets import Button, Welcome


class WelcomeApp(App):
    def on_key(self) -> None:
        self.mount(Welcome())
        self.query_one(Button).label = "YES!" # (1)!


if __name__ == "__main__":
    app = WelcomeApp()
    app.run()
```

----------------------------------------

TITLE: Defining Input.Changed Message Class in Textual Python
DESCRIPTION: This snippet shows the definition of the `Changed` message class nested within the `Input` widget class in Textual. This structure establishes a namespace for the message, leading to handler names like `on_input_changed`.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/events.md#_snippet_0

LANGUAGE: Python
CODE:
```
class Input(Widget):
    ...
    class Changed(Message):
        """Posted when the value changes."""
        ...
```

----------------------------------------

TITLE: Setting Textual Widget Styles Programmatically in Python
DESCRIPTION: This Python snippet shows how to programmatically set multiple style properties for a Textual widget using its 'styles' attribute. Each line assigns a 'type_value' to a specific 'rule' property of the widget's styles.
SOURCE: https://github.com/textualize/textual/blob/main/docs/css_types/_template.md#_snippet_1

LANGUAGE: python
CODE:
```
widget.styles.rule = type_value_1
widget.styles.rule = type_value_2
widget.styles.rule = type_value_3
```

----------------------------------------

TITLE: Action to Set Switch Value in Textual
DESCRIPTION: This Python code demonstrates an action within a Textual application that sets the value of a Switch widget to true (1). It uses query_one to select the Switch widget and then updates its value attribute.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/widgets.md#_snippet_27

LANGUAGE: python
CODE:
```
def action_set_true(self):
    self.query_one(Switch).value = 1
```

----------------------------------------

TITLE: Running Named Textual App from Python Module
DESCRIPTION: Executes a Textual application by importing it from a Python module, explicitly specifying the name of the app instance or class if it's not the default `app`. This allows running multiple apps within a single module.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/devtools.md#_snippet_4

LANGUAGE: bash
CODE:
```
textual run music.play:MusicPlayerApp
```

----------------------------------------

TITLE: Installing Textual Calculator with pip
DESCRIPTION: This command demonstrates how to install the packaged Textual calculator application using pip, the Python package installer.
SOURCE: https://github.com/textualize/textual/blob/main/docs/how-to/package-with-hatch.md#_snippet_0

LANGUAGE: bash
CODE:
```
pip install textual-calculator
```

----------------------------------------

TITLE: Applying CSS Overflow Properties
DESCRIPTION: This CSS snippet demonstrates how to apply different `overflow` values to control scrollbar visibility. It shows examples for automatic scrollbars on both axes (default), hiding the vertical scrollbar, and always showing the horizontal scrollbar.
SOURCE: https://github.com/textualize/textual/blob/main/docs/styles/overflow.md#_snippet_1

LANGUAGE: css
CODE:
```
/* Automatic scrollbars on both axes (the default) */
overflow: auto auto;

/* Hide the vertical scrollbar */
overflow-y: hidden;

/* Always show the horizontal scrollbar */
overflow-x: scroll;
```

----------------------------------------

TITLE: CSS Examples for Grid-columns
DESCRIPTION: These CSS examples demonstrate how to apply the `grid-columns` style. The first rule sets all columns to 50% width, while the second uses fractional units (`fr`) to make every other column twice as wide as the first, illustrating flexible column sizing.
SOURCE: https://github.com/textualize/textual/blob/main/docs/styles/grid/grid_columns.md#_snippet_1

LANGUAGE: CSS
CODE:
```
/* Set all columns to have 50% width */
grid-columns: 50%;

/* Every other column is twice as wide as the first one */
grid-columns: 1fr 2fr;
```

----------------------------------------

TITLE: Adding Keybindings to a Textual Widget
DESCRIPTION: This snippet demonstrates how to add keybindings to a Textual widget. The `BINDINGS` class variable associates key presses with actions, allowing the widget to respond to keyboard input.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/widgets.md#_snippet_12

LANGUAGE: python
CODE:
```
from textual.app import App, ComposeResult
from textual.widgets import Static
from textual.reactive import reactive

class Counter(Static):
    
```

----------------------------------------

TITLE: Combining Actions with Styles (Textual Markup)
DESCRIPTION: Shows how to combine a click action with other styles in Textual markup. Here, the text is styled with a success background color and transparency, in addition to triggering the `app.bell` action on click.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/content.md#_snippet_20

LANGUAGE: Textual Markup
CODE:
```
Play the [on $success 30% @click=app.bell]bell[/]
```

----------------------------------------

TITLE: Simplified Textual Widget Initialization and Refresh (Python)
DESCRIPTION: This Python snippet presents a simplified `IntervalUpdater` widget. It initializes the `Static` base class directly with a `RenderableType` object, eliminating the need for explicit `update` calls. The `on_mount` method sets up a 60 FPS refresh interval, leveraging the widget's inherent ability to re-render its initialized content.
SOURCE: https://github.com/textualize/textual/blob/main/docs/blog/posts/spinners-and-pbs-in-textual.md#_snippet_12

LANGUAGE: Python
CODE:
```
class IntervalUpdater(Static):
    _renderable_object: RenderableType

    def __init__(self, renderable_object: RenderableType) -> None:  # (1)!
        super().__init__(renderable_object)  # (2)!

    def on_mount(self) -> None:
        self.interval_update = self.set_interval(1 / 60, self.refresh)  # (3)!
```

----------------------------------------

TITLE: Setting Text Color with CSS
DESCRIPTION: Demonstrates various ways to set the `color` style in CSS, including named colors, colors with opacity percentages, RGB values, and the `auto` keyword for automatic contrast selection.
SOURCE: https://github.com/textualize/textual/blob/main/docs/styles/color.md#_snippet_0

LANGUAGE: css
CODE:
```
/* Blue text */
color: blue;

/* 20% red text */
color: red 20%;

/* RGB color */
color: rgb(100, 120, 200);

/* Automatically choose color with suitable contrast for readability */
color: auto;
```

----------------------------------------

TITLE: Defining Context-Aware Key Bindings in Textual Python
DESCRIPTION: This snippet demonstrates how to define BINDINGS within different Textual widgets (Activity, Filters, Main screen) to provide context-specific behavior for the escape key. This approach improves elegance and allows for dynamic Footer descriptions, replacing a single, overloaded top-level binding.
SOURCE: https://github.com/textualize/textual/blob/main/docs/blog/posts/on-dog-food-the-original-metaverse-and-not-being-bored.md#_snippet_1

LANGUAGE: Python
CODE:
```
...

class Activity( Widget ):
    """A widget that holds and displays a suggested activity."""

    BINDINGS = [
        ...
        Binding( "escape", "deselect", "Switch to Types" )
    ]

...

class Filters( Vertical ):
    """Filtering sidebar."""

    BINDINGS = [
        Binding( "escape", "close", "Close Filters" )
    ]

...

class Main( Screen ):
    """The main application screen."""

    BINDINGS = [
        Binding( "escape", "quit", "Close" )
    ]
    """The bindings for the main screen."""
```

----------------------------------------

TITLE: World Clock App with Data Binding and Renamed Attribute - Python
DESCRIPTION: This Python code extends the data binding example by demonstrating how to bind reactive attributes when the attribute names differ between the parent app and the child widget. It uses keyword arguments in the `data_bind` call to map the app's `time` attribute to the widget's `clock_time` attribute.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/reactivity.md#_snippet_25

LANGUAGE: python
CODE:
```
from __future__ import annotations

import asyncio
import time
from datetime import datetime, timezone

import pytz
from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Static


class TimeDisplay(Static):
    
```

----------------------------------------

TITLE: Launching Textual Debug Console
DESCRIPTION: Starts the Textual debug console in a dedicated terminal window. This console captures `print` statements and Textual log messages from applications running in development mode, aiding in debugging.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/devtools.md#_snippet_11

LANGUAGE: bash
CODE:
```
textual console
```

----------------------------------------

TITLE: Comparing Textual Width Units (CSS)
DESCRIPTION: This CSS demonstrates various width units for Textual widgets, including fixed columns, percentages, terminal-relative units (tw, th), viewport-relative units (vw, vh), automatic sizing, and fractional units (fr). Each rule targets a specific widget ID to illustrate the different sizing behaviors.
SOURCE: https://github.com/textualize/textual/blob/main/docs/styles/width.md#_snippet_4

LANGUAGE: css
CODE:
```
#columns {
    width: 9;
}

#percentage {
    width: 12.5%;
}

#tw {
    width: 10tw;
}

#th {
    width: 25th;
}

#vw {
    width: 15vw;
}

#vh {
    width: 25vh;
}

#auto {
    width: auto;
}

#fr1 {
    width: 1fr;
}

#fr3 {
    width: 3fr;
}

Horizontal {
    height: 100%;
}
Placeholder {
    border: solid 1px white;
    margin: 1;
    background: #333;
}
```

----------------------------------------

TITLE: Implementing Multi-Mode Navigation in Textual App (Python)
DESCRIPTION: This Python snippet demonstrates how to implement multi-mode navigation in a Textual application using the `MODES` class variable, `DEFAULT_MODE`, and `switch_mode` action. It defines three distinct screens (Dashboard, Settings, Help) and associates them with named modes, allowing users to switch between these independent screen stacks via key bindings or button presses. The `on_mount` method ensures the app starts in the default 'dashboard' mode.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/screens.md#_snippet_0

LANGUAGE: Python
CODE:
```
from textual.app import App, Screen, ComposeResult
from textual.widgets import Header, Footer, Button, Label
from textual.containers import Container
from textual.actions import Action

class DashboardScreen(Screen):
    BINDINGS = [
        ("s", "switch_mode('settings')", "Settings"),
        ("h", "switch_mode('help')", "Help"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Label("Welcome to the Dashboard!"),
            Button("Go to Settings", id="settings_button"),
            Button("Go to Help", id="help_button"),
        )
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "settings_button":
            self.app.switch_mode("settings")
        elif event.button.id == "help_button":
            self.app.switch_mode("help")

class SettingsScreen(Screen):
    BINDINGS = [
        ("d", "switch_mode('dashboard')", "Dashboard"),
        ("h", "switch_mode('help')", "Help"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Label("Settings Screen"),
            Button("Go to Dashboard", id="dashboard_button"),
            Button("Go to Help", id="help_button"),
        )
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "dashboard_button":
            self.app.switch_mode("dashboard")
        elif event.button.id == "help_button":
            self.app.switch_mode("help")

class HelpScreen(Screen):
    BINDINGS = [
        ("d", "switch_mode('dashboard')", "Dashboard"),
        ("s", "switch_mode('settings')", "Settings"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Label("Help Screen"),
            Button("Go to Dashboard", id="dashboard_button"),
            Button("Go to Settings", id="settings_button"),
        )
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "dashboard_button":
            self.app.switch_mode("dashboard")
        elif event.button.id == "settings_button":
            self.app.switch_mode("settings")

class ModesApp(App):
    MODES = {
        "dashboard": DashboardScreen,
        "settings": SettingsScreen,
        "help": HelpScreen,
    }
    DEFAULT_MODE = "dashboard"

    BINDINGS = [
        ("d", "switch_mode('dashboard')", "Dashboard"),
        ("s", "switch_mode('settings')", "Settings"),
        ("h", "switch_mode('help')", "Help"),
    ]

    def on_mount(self) -> None:
        self.switch_mode(self.DEFAULT_MODE)

if __name__ == "__main__":
    app = ModesApp()
    app.run()
```

----------------------------------------

TITLE: Creating a Simple Textual RGB App (Python)
DESCRIPTION: This Textual application displays three buttons: 'Red', 'Green', and 'Blue'. Clicking a button or pressing its corresponding key (r, g, b) changes the application's background color. It serves as a demonstration app for testing user interface interactions.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/testing.md#_snippet_0

LANGUAGE: Python
CODE:
```
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Button
from textual.containers import Container

class RGBApp(App):
    CSS = """
    Screen {
        align-items: center;
        justify-content: center;
    }
    Container {
        width: 100%;
        height: 100%;
        display: grid;
        grid-template-columns: 1fr 1fr 1fr;
        grid-gap: 1;
        align-items: center;
        justify-items: center;
    }
    Button {
        width: 80%;
        height: 80%;
        font-size: 2;
    }
    """

    BINDINGS = [
        ("r", "set_color('red')", "Red"),
        ("g", "set_color('green')", "Green"),
        ("b", "set_color('blue')", "Blue"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        with Container():
            yield Button("Red", id="red", variant="error")
            yield Button("Green", id="green", variant="success")
            yield Button("Blue", id="blue", variant="primary")
        yield Footer()

    def action_set_color(self, color: str) -> None:
        self.screen.styles.background = color

if __name__ == "__main__":
    app = RGBApp()
    app.run()
```

----------------------------------------

TITLE: Safe Markup Variable Substitution with Content.from_markup - Textual Python
DESCRIPTION: This snippet demonstrates the recommended and secure way to insert variables into Textual markup using the Content.from_markup method. By passing variables as keyword arguments, Textual intelligently handles the substitution, ensuring that any square brackets within the variable's value are treated as literal text rather than markup, thereby preventing styling conflicts and maintaining display integrity.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/content.md#_snippet_29

LANGUAGE: python
CODE:
```
return Content.from_markup("hello [bold]$name[/bold]!", name=name)
```

----------------------------------------

TITLE: Checkerboard Widget with Mouse Highlight in Python
DESCRIPTION: This code demonstrates how to update a checkerboard widget to highlight the square under the mouse pointer using the Line API. It includes a reactive variable to track the cursor position and refresh only the necessary regions of the widget.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/widgets.md#_snippet_24

LANGUAGE: python
CODE:
```
    --8<-- "docs/examples/guide/widgets/checker04.py"

```

----------------------------------------

TITLE: Creating a Focusable Widget in Textual
DESCRIPTION: This snippet demonstrates how to create a focusable widget in Textual by setting the `can_focus` attribute to `True`. This allows the widget to receive keyboard input.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/widgets.md#_snippet_10

LANGUAGE: python
CODE:
```
from textual.app import App, ComposeResult
from textual.widgets import Static

class Counter(Static):
    
```

----------------------------------------

TITLE: Defining a Widget Class
DESCRIPTION: This Python code defines a custom widget class named `Alert` that inherits from `Static`. This widget can then be styled using CSS selectors.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/CSS.md#_snippet_4

LANGUAGE: python
CODE:
```
from textual.widgets import Static

class Alert(Static):
    pass
```

----------------------------------------

TITLE: CSS Border Property Syntax
DESCRIPTION: Defines the syntax for applying borders in Textual CSS. It shows how to set a border for all edges or individual edges (top, right, bottom, left) using a border style, color, and an optional percentage for blending.
SOURCE: https://github.com/textualize/textual/blob/main/docs/styles/border.md#_snippet_0

LANGUAGE: css
CODE:
```
border: [<a href="../../css_types/border">&lt;border&gt;</a>] [<a href="../../css_types/color">&lt;color&gt;</a>] [<a href="../../css_types/percentage">&lt;percentage&gt;</a>];

border-top: [<a href="../../css_types/border">&lt;border&gt;</a>] [<a href="../../css_types/color">&lt;color&gt;</a>] [<a href="../../css_types/percentage">&lt;percentage&gt;</a>];
border-right: [<a href="../../css_types/border">&lt;border&gt;</a>] [<a href="../../css_types/color">&lt;color&gt;</a> [<a href="../../css_types/percentage">&lt;percentage&gt;</a>]];
border-bottom: [<a href="../../css_types/border">&lt;border&gt;</a>] [<a href="../../css_types/color">&lt;color&gt;</a> [<a href="../../css_types/percentage">&lt;percentage&gt;</a>]];
border-left: [<a href="../../css_types/border">&lt;border&gt;</a>] [<a href="../../css_types/color">&lt;color&gt;</a> [<a href="../../css_types/percentage">&lt;percentage&gt;</a>]];
```

----------------------------------------

TITLE: Integrating Plotext Scatter Plot into a Textual Application
DESCRIPTION: This Python snippet shows how to embed a Plotext scatter plot within a Textual application using the `textual-plotext` library. It defines a Textual `App` that composes a `PlotextPlot` widget. In the `on_mount` method, it accesses the `plt` property of the widget to generate a sinusoidal signal, plot it, and set a title, demonstrating the seamless integration of Plotext's API within Textual.
SOURCE: https://github.com/textualize/textual/blob/main/docs/blog/posts/textual-plotext.md#_snippet_1

LANGUAGE: Python
CODE:
```
from textual.app import App, ComposeResult

from textual_plotext import PlotextPlot

class ScatterApp(App[None]):

    def compose(self) -> ComposeResult:
        yield PlotextPlot()

    def on_mount(self) -> None:
        plt = self.query_one(PlotextPlot).plt
        y = plt.sin() # sinusoidal test signal
        plt.scatter(y)
        plt.title("Scatter Plot") # to apply a title

if __name__ == "__main__":
    ScatterApp().run()
```

----------------------------------------

TITLE: Styling Widgets with Textual CSS
DESCRIPTION: Defines styles for the `Stopwatch`, `TimeDisplay`, and `Button` widgets using Textual CSS. It covers properties like background, height, margin, padding, text alignment, color, width, docking, and display visibility, and shows how to target widgets by their ID using `#`.
SOURCE: https://github.com/textualize/textual/blob/main/docs/tutorial.md#_snippet_6

LANGUAGE: CSS
CODE:
```
Stopwatch {
    background: $boost;
    height: 5;
    margin: 1;
    min-width: 50;
    padding: 1;
}

TimeDisplay { 
    text-align: center;
    color: $foreground-muted;
    height: 3;
}

Button {
    width: 16;
}

#start {
    dock: left;
}

#stop {
    dock: left;
    display: none;
}

#reset {
    dock: right;
}
```

----------------------------------------

TITLE: Aligning Children with `align` - CSS
DESCRIPTION: Demonstrates how to use the `align` CSS property to position child widgets within a container. It shows examples for centering children and aligning them to the top-right.
SOURCE: https://github.com/textualize/textual/blob/main/docs/styles/align.md#_snippet_1

LANGUAGE: css
CODE:
```
/* Align child widgets to the center. */
align: center middle;
/* Align child widget to the top right */
align: right top;
```

----------------------------------------

TITLE: Configuring Input Validation Trigger - Python
DESCRIPTION: This snippet shows how to configure an `Input` widget to perform validation only when the input value is explicitly submitted, by setting the `validate_on` parameter.
SOURCE: https://github.com/textualize/textual/blob/main/docs/widgets/input.md#_snippet_2

LANGUAGE: Python
CODE:
```
input = Input(validate_on=["submitted"])
```

----------------------------------------

TITLE: Defining CSS Style Rules
DESCRIPTION: This snippet illustrates the general syntax for defining CSS style rules. It shows how to assign single values, multiple values, and different syntax variations to a 'rule-name', as well as defining 'rule-name-variant' properties. This serves as a template for documenting specific CSS properties.
SOURCE: https://github.com/textualize/textual/blob/main/docs/styles/_template.md#_snippet_0

LANGUAGE: css
CODE:
```
rule-name: value1
rule-name: value2
rule-name: different-syntax-value shown-here

rule-name-variant: value3
rule-name-variant: value4
```

----------------------------------------

TITLE: Overriding Textual Theme Variables (Python)
DESCRIPTION: This Python snippet demonstrates how to customize Textual theme variables by passing a `variables` dictionary to the `Theme` constructor. It specifically shows overriding `block-cursor-foreground` and `input-selection-background` to achieve a custom look for the Gruvbox theme, allowing fine-grained control over UI element appearance.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/design.md#_snippet_4

LANGUAGE: Python
CODE:
```
Theme(
    name="gruvbox",
    primary="#85A598",
    secondary="#A89A85",
    warning="#fabd2f",
    error="#fb4934",
    success="#b8bb26",
    accent="#fabd2f",
    foreground="#fbf1c7",
    background="#282828",
    surface="#3c3836",
    panel="#504945",
    dark=True,
    variables={
        "block-cursor-foreground": "#fbf1c7",
        "input-selection-background": "#689d6a40"
    }
)
```

----------------------------------------

TITLE: Applying Padding with CSS
DESCRIPTION: This snippet demonstrates various ways to apply padding using CSS in Textual. It shows how to set uniform padding for all edges, different padding for vertical and horizontal axes, and distinct padding for each of the four edges (top, right, bottom, left). It also illustrates setting padding for individual edges using `padding-top`, `padding-right`, `padding-bottom`, and `padding-left` properties.
SOURCE: https://github.com/textualize/textual/blob/main/docs/styles/padding.md#_snippet_0

LANGUAGE: CSS
CODE:
```
/* Set padding of 1 around all edges */
padding: 1;
/* Set padding of 2 on the top and bottom edges, and 4 on the left and right */
padding: 2 4;
/* Set padding of 1 on the top, 2 on the right,
                 3 on the bottom, and 4 on the left */
padding: 1 2 3 4;

padding-top: 1;
padding-right: 2;
padding-bottom: 3;
padding-left: 4;
```

----------------------------------------

TITLE: Writing Text to a Textual Log Widget
DESCRIPTION: This example demonstrates how to create a Textual application that uses the `Log` widget. It shows how to append single lines using `Log.write_line` and multiple lines using `Log.write_lines` via button presses, and how to clear the log using an action.
SOURCE: https://github.com/textualize/textual/blob/main/docs/widgets/log.md#_snippet_0

LANGUAGE: Python
CODE:
```
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Log, Button
from textual.containers import Vertical

class LogApp(App):
    BINDINGS = [("c", "clear_log", "Clear Log")]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        with Vertical():
            yield Button("Write Line", id="write_line_button")
            yield Button("Write Multiple Lines", id="write_multiple_lines_button")
            yield Log(id="my_log")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        log_widget = self.query_one("#my_log", Log)
        if event.button.id == "write_line_button":
            log_widget.write_line(f"Line {log_widget.line_count + 1} written at {self.app.get_time()}")
        elif event.button.id == "write_multiple_lines_button":
            log_widget.write_lines([
                f"Multi-line 1 at {self.app.get_time()}",
                f"Multi-line 2 at {self.app.get_time()}"
            ])

    def action_clear_log(self) -> None:
        self.query_one("#my_log", Log).clear()

if __name__ == "__main__":
    app = LogApp()
    app.run()
```

----------------------------------------

TITLE: Configuring Textual App with Auto-Focus and TCSS
DESCRIPTION: This Python snippet defines the main MotherApp class, the top-level object for the Textual application. It sets AUTO_FOCUS to direct initial input focus to the Input widget and includes TCSS (Textual Cascading Style Sheets) to style the Prompt and Response widgets, defining their background, color, margins, and borders for a distinct visual appearance.
SOURCE: https://github.com/textualize/textual/blob/main/docs/blog/posts/anatomy-of-a-textual-user-interface.md#_snippet_2

LANGUAGE: Python
CODE:
```
class MotherApp(App):
    AUTO_FOCUS = "Input"

    CSS = """
    Prompt {
        background: $primary 10%;
        color: $text;
        margin: 1;        
        margin-right: 8;
        padding: 1 2 0 2;
    }

    Response {
        border: wide $success;
        background: $success 10%;   
        color: $text;             
        margin: 1;      
        margin-left: 8; 
        padding: 1 2 0 2;
    }
    """
```

----------------------------------------

TITLE: Retrieving a Single Widget by Type (Python)
DESCRIPTION: This snippet shows how to use `query_one` to retrieve a single widget instance solely by its type. It will return the first `Button` instance found in the DOM below the calling widget. This is useful when you expect only one instance of a particular widget type.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/queries.md#_snippet_2

LANGUAGE: Python
CODE:
```
my_button = self.query_one(Button)
```

----------------------------------------

TITLE: Setting Text Color in Python
DESCRIPTION: Illustrates how to set the `color` style for a widget in Python, either by assigning a CSS-like string or by using a `Color` object from `textual.color` for more programmatic control.
SOURCE: https://github.com/textualize/textual/blob/main/docs/styles/color.md#_snippet_1

LANGUAGE: python
CODE:
```
# Set blue text
widget.styles.color = "blue"

from textual.color import Color
# Set with a color object
widget.styles.color = Color.parse("pink")
```

----------------------------------------

TITLE: Composing TabbedContent with Positional Arguments - Python
DESCRIPTION: This snippet demonstrates how to compose a TabbedContent widget by passing tab titles directly as positional arguments to its constructor. Each argument corresponds to a tab, and the subsequent yielded Markdown widgets become the content for those tabs in order. This method is concise for simple tab setups.
SOURCE: https://github.com/textualize/textual/blob/main/docs/widgets/tabbed_content.md#_snippet_0

LANGUAGE: python
CODE:
```
def compose(self) -> ComposeResult:
    with TabbedContent("Leto", "Jessica", "Paul"):
        yield Markdown(LETO)
        yield Markdown(JESSICA)
        yield Markdown(PAUL)
```

----------------------------------------

TITLE: Enabling Syntax Highlighting in Textual TextArea (Python)
DESCRIPTION: This code illustrates how to enable syntax highlighting for a specific programming language within a Textual `TextArea`. By passing the `language` argument (e.g., `language="python"`) during instantiation, the `TextArea` will automatically highlight the text according to the specified language's syntax rules.
SOURCE: https://github.com/textualize/textual/blob/main/docs/blog/posts/text-area-learnings.md#_snippet_1

LANGUAGE: python
CODE:
```
yield TextArea(language="python")
```

----------------------------------------

TITLE: Applying Translucent Background to Textual Screen with SASS
DESCRIPTION: This SASS snippet demonstrates how to apply a translucent background to a Textual `DialogScreen`. By setting the `background` property to a color (e.g., `$primary`) followed by a percentage (e.g., `30%`), the screen becomes partially transparent, allowing the content of the screen below to be visible. This effect is useful for creating modal dialogs that visually indicate the underlying screen's presence.
SOURCE: https://github.com/textualize/textual/blob/main/docs/blog/posts/release0-17-0.md#_snippet_0

LANGUAGE: SASS
CODE:
```
DialogScreen {
    align: center middle;
    background: $primary 30%;
}
```

----------------------------------------

TITLE: Programmatically Setting Grid Size in Python
DESCRIPTION: Illustrates how to programmatically adjust the grid dimensions (rows and columns) for a widget using Textual's Python API. It shows separate properties for setting the number of rows and columns on a widget's styles.
SOURCE: https://github.com/textualize/textual/blob/main/docs/styles/grid/grid_size.md#_snippet_1

LANGUAGE: python
CODE:
```
widget.styles.grid_size_rows = 3
widget.styles.grid_size_columns = 6
```

----------------------------------------

TITLE: Defining Calculator App Entry Point in Python
DESCRIPTION: This Python code defines a function `calculator` that initializes and runs the `CalculatorApp` from the `textual_calculator.calculator` module. This function serves as the entry point for the application, allowing it to be launched from the command line.
SOURCE: https://github.com/textualize/textual/blob/main/docs/how-to/package-with-hatch.md#_snippet_11

LANGUAGE: python
CODE:
```
from textual_calculator.calculator import CalculatorApp


def calculator():
    app = CalculatorApp()
    app.run()
```

----------------------------------------

TITLE: Rendering Markup String Directly (Python)
DESCRIPTION: Shows a Textual `Widget`'s `render` method returning a string containing markup. Textual automatically converts this string into a `Content` instance, applying the bold style to 'Hello, World!' as specified by the markup.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/content.md#_snippet_23

LANGUAGE: Python
CODE:
```
class WelcomeWidget(Widget):
    def render(self) -> RenderResult:
        return "[b]Hello, World![/b]"
```

----------------------------------------

TITLE: Basic Indeterminate Progress Bar with Rich (Python)
DESCRIPTION: This code demonstrates a simple indeterminate progress bar using Rich's `Progress` context manager. It adds a task with `total=None` to signify indeterminacy and then enters an infinite loop with a small `time.sleep` to keep the program running, allowing the progress bar to animate without explicit updates.
SOURCE: https://github.com/textualize/textual/blob/main/docs/blog/posts/spinners-and-pbs-in-textual.md#_snippet_3

LANGUAGE: Python
CODE:
```
with Progress() as progress:
    _ = progress.add_task("Loading...", total=None)  # (1)!
    while True:
        time.sleep(0.01)
```

----------------------------------------

TITLE: CSS with Nesting
DESCRIPTION: This CSS defines the same styles as the previous example, but uses nesting to group rules related to the `#questions` container and its buttons. The nesting selector (&) is used to combine selectors for specific button types.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/CSS.md#_snippet_27

LANGUAGE: css
CODE:
```
#questions {
    layout: horizontal;
    height: 3;
    padding: 1;
    align: center middle;

    .button {
        width: 10;
        height: 1fr;
        border: tall $primary 60%;
        color: $text;
        dock: left;
        margin: 1;
        content-align: center middle;

        &.affirmative {
            background: $success;
            color: $text-light;
        }

        &.negative {
            background: $error;
            color: $text-light;
        }
    }
}
```

----------------------------------------

TITLE: Running Textual Actions from Action Strings (Python)
DESCRIPTION: This example demonstrates how to invoke a Textual action using an action string and the `run_action()` method. Instead of directly calling the action method, `run_action()` parses a string like `'set_background(\'red\')'` and dispatches it. Note that `run_action()` is a coroutine, requiring the `on_key` method to be `async`.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/actions.md#_snippet_1

LANGUAGE: python
CODE:
```
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static

class ActionsApp(App):
    def action_set_background(self, color: str) -> None:
        self.screen.styles.background = color

    async def on_key(self, event) -> None:
        if event.key == "r":
            await self.run_action("set_background('red')")

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        yield Static("Press 'r' to set background to red via action string.")

if __name__ == "__main__":
    ActionsApp().run()
```

----------------------------------------

TITLE: Implementing 'Await Me Maybe' Pattern in Python
DESCRIPTION: This snippet demonstrates the 'Await me maybe' pattern, allowing a function to execute a callback that can be either a regular synchronous function or an asynchronous coroutine. It uses `inspect.isawaitable` to conditionally `await` the result, enabling flexible callback handling in an async context without forcing all callers to be `async`.
SOURCE: https://github.com/textualize/textual/blob/main/docs/blog/posts/await-me-maybe.md#_snippet_0

LANGUAGE: Python
CODE:
```
import asyncio
import inspect


def plain_old_function():
    return "Plain old function"

async def async_function():
    return "Async function"


async def await_me_maybe(callback):
    result = callback()
    if inspect.isawaitable(result):
        return await result
    return result


async def run_framework():
    print(
        await await_me_maybe(plain_old_function)
    )
    print(
        await await_me_maybe(async_function)
    )


if __name__ == "__main__":
    asyncio.run(run_framework())
```

----------------------------------------

TITLE: Box-sizing CSS Syntax
DESCRIPTION: This snippet illustrates the valid syntax for the `box-sizing` CSS property, specifying the two accepted values: `border-box` and `content-box`. It defines the fundamental structure for applying this style.
SOURCE: https://github.com/textualize/textual/blob/main/docs/styles/box_sizing.md#_snippet_0

LANGUAGE: css
CODE:
```
box-sizing: border-box | content-box;
```

----------------------------------------

TITLE: Styling Buttons within a Dialog
DESCRIPTION: This CSS rule makes the text of buttons within a widget with the ID 'dialog' bold. It uses the descendant combinator to target buttons that are descendants of the dialog widget.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/CSS.md#_snippet_16

LANGUAGE: css
CODE:
```
#dialog Button {
  text-style: bold;
}
```

----------------------------------------

TITLE: Basic Label Widget Usage (Python)
DESCRIPTION: This Python snippet demonstrates how to create and use a `Label` widget within a Textual application to display static text. It shows the minimal setup required to run a Textual app with a single label.
SOURCE: https://github.com/textualize/textual/blob/main/docs/widgets/label.md#_snippet_0

LANGUAGE: Python
CODE:
```
from textual.app import App, ComposeResult
from textual.widgets import Label

class MyLabelApp(App):
    def compose(self) -> ComposeResult:
        yield Label("This is a simple Label.")

if __name__ == "__main__":
    MyLabelApp().run()
```

----------------------------------------

TITLE: Serving Textual App from Python File
DESCRIPTION: Launches a Textual application and serves it as a web application in a browser. This command takes a Python file path and makes the terminal app accessible via a web interface.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/devtools.md#_snippet_6

LANGUAGE: bash
CODE:
```
textual serve my_app.py
```

----------------------------------------

TITLE: Getting the Last Matching Widget with Textual
DESCRIPTION: This snippet demonstrates using the `last()` method on a Textual DOMQuery object to retrieve the final widget matching a CSS selector. It queries for all 'Button' widgets and then selects the last one found. If no buttons are present, a `NoMatches` exception is raised.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/queries.md#_snippet_8

LANGUAGE: python
CODE:
```
last_button = self.query("Button").last()
```

----------------------------------------

TITLE: Implementing an LRU Cache in Python
DESCRIPTION: This example showcases Textual's `LRUCache` class, a container-based Least Recently Used (LRU) cache implementation. Unlike `functools.lru_cache`, it provides more control over cache lifetime and behaves like a dictionary, automatically evicting the least recently used items when `maxsize` is reached. It's ideal for caching frequently accessed data to improve performance and manage memory.
SOURCE: https://github.com/textualize/textual/blob/main/docs/blog/posts/steal-this-code.md#_snippet_1

LANGUAGE: Python
CODE:
```
>>> from textual._cache import LRUCache
>>> cache = LRUCache(maxsize=3)
>>> cache["foo"] = 1
>>> cache["bar"] = 2
>>> cache["baz"] = 3
>>> dict(cache)
{'foo': 1, 'bar': 2, 'baz': 3}
>>> cache["egg"] = 4
>>> dict(cache)
{'bar': 2, 'baz': 3, 'egg': 4}
```

----------------------------------------

TITLE: Increasing Textual Console Verbosity
DESCRIPTION: Launches the Textual debug console with the `-v` switch, which increases the verbosity of log messages. This includes "verbose" events that are typically excluded, providing more detailed debugging information.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/devtools.md#_snippet_13

LANGUAGE: bash
CODE:
```
textual console -v
```

----------------------------------------

TITLE: Recomposing a Widget on Reactive Attribute Change - Python
DESCRIPTION: This example demonstrates how to use `recompose=True` to refresh a widget by removing all child widgets and calling `compose()` again when the `who` reactive attribute changes. This approach creates a new set of child widgets instead of updating existing ones.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/reactivity.md#_snippet_13

LANGUAGE: Python
CODE:
```
class RefreshApp(App):

    BINDINGS = [("p", "toggle_name", "Toggle Name")]

    who = reactive("World", recompose=True)

    def compose(self) -> ComposeResult:
        yield Label(f"Hello, {self.who}!", id="greeting")

    def action_toggle_name(self) -> None:
        self.who = "Textual" if self.who == "World" else "World"
```

----------------------------------------

TITLE: Setting Screen Styles in Textual (Python)
DESCRIPTION: This snippet demonstrates how to apply styles directly to the Textual screen. It sets the screen's background color to 'darkblue' and adds a 'heavy' white border, updating the terminal display accordingly.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/styles.md#_snippet_0

LANGUAGE: python
CODE:
```
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer

class MyApp(App):
    def compose(self) -> ComposeResult:
        self.screen.styles.background = "darkblue"
        self.screen.styles.border = ("heavy", "white")
        yield Header()
        yield Footer()

if __name__ == "__main__":
    app = MyApp()
    app.run()
```

----------------------------------------

TITLE: Applying Class to All Matched Widgets in Textual (Loop-Free)
DESCRIPTION: This snippet showcases a loop-free operation on a Textual DOMQuery object using `add_class()`. It efficiently adds the 'disabled' CSS class to all widgets matching the 'Button' selector without requiring an explicit Python `for` loop. This method provides a concise and optimized way to perform bulk updates on matched widgets.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/queries.md#_snippet_12

LANGUAGE: python
CODE:
```
self.query("Button").add_class("disabled")
```

----------------------------------------

TITLE: Applying Styles Programmatically in Textual
DESCRIPTION: This Python snippet illustrates an alternative method for applying styles to Textual widgets directly within the code. It demonstrates setting the color property to "red" and the margin property to 8, showcasing how styles can be manipulated programmatically instead of using TCSS.
SOURCE: https://github.com/textualize/textual/blob/main/docs/blog/posts/anatomy-of-a-textual-user-interface.md#_snippet_3

LANGUAGE: Python
CODE:
```
self.styles.color = "red"
self.styles.margin = 8
```

----------------------------------------

TITLE: Initializing `itertools.cycle` for Placeholder Variants (Python)
DESCRIPTION: This snippet highlights the crucial initialization logic within the `Placeholder` class's `__init__` method. It shows how `itertools.cycle` is used to create an iterable for placeholder variants and how a `while` loop ensures that the cycle starts from the currently assigned variant, preventing incorrect initial states when cycling through options.
SOURCE: https://github.com/textualize/textual/blob/main/docs/blog/posts/placeholder-pr.md#_snippet_2

LANGUAGE: python
CODE:
```
from itertools import cycle
# ...
class Placeholder(Static):
    # ...
    def __init__(...):
        # ...
        self._variants_cycle = cycle(_VALID_PLACEHOLDER_VARIANTS_ORDERED)
        while next(self._variants_cycle) != self.variant:
            pass
```

----------------------------------------

TITLE: Defining Dock Style Syntax in Textual CSS
DESCRIPTION: This snippet illustrates the valid syntax for the `dock` property in Textual CSS, specifying the four possible values (`bottom`, `left`, `right`, `top`) that determine which edge of the container a widget will be fixed to.
SOURCE: https://github.com/textualize/textual/blob/main/docs/styles/dock.md#_snippet_0

LANGUAGE: css
CODE:
```
dock: bottom | left | right | top;
```

----------------------------------------

TITLE: Composing Collapsible Widget with Context Manager - Python
DESCRIPTION: Illustrates the preferred way to add content to a Textual Collapsible widget using a Python `with` statement (context manager). This allows for more structured and readable content composition.
SOURCE: https://github.com/textualize/textual/blob/main/docs/widgets/collapsible.md#_snippet_1

LANGUAGE: python
CODE:
```
def compose(self) -> ComposeResult:
    with Collapsible():
        yield Label("Hello, world.")
```

----------------------------------------

TITLE: Setting Static App Title and Subtitle in Textual (Python)
DESCRIPTION: This Python snippet demonstrates how to define static application titles and subtitles in a Textual app. By setting the TITLE and SUB_TITLE class variables, the default header widget will display these values, providing consistent branding or context for the application.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/app.md#_snippet_10

LANGUAGE: python
CODE:
```
--8<-- "docs/examples/app/question_title01.py"
```

----------------------------------------

TITLE: Styling Buttons within a Dialog and Horizontal Widget
DESCRIPTION: This CSS rule makes the text of buttons bold if they are descendants of both a 'Horizontal' widget and a widget with the ID 'dialog'. It combines multiple selectors with the descendant combinator.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/CSS.md#_snippet_17

LANGUAGE: css
CODE:
```
#dialog Horizontal Button {
  text-style: bold;
}
```

----------------------------------------

TITLE: Simulating Multiple Key Presses with Textual Pilot (Python)
DESCRIPTION: This snippet demonstrates how to use the `pilot.press` method to simulate a sequence of individual key presses, effectively mimicking a user typing. It supports both printable characters and special keys like 'enter' or 'ctrl+' modifiers.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/testing.md#_snippet_2

LANGUAGE: python
CODE:
```
await pilot.press("h", "e", "l", "l", "o")
```

----------------------------------------

TITLE: Logging with App/Widget Instance Methods (Python)
DESCRIPTION: This snippet illustrates the convenient `self.log` method available on `App` and `Widget` objects for direct logging. It demonstrates its use within `on_load` and `on_mount` event handlers, providing a concise way to log information from instance methods.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/devtools.md#_snippet_19

LANGUAGE: python
CODE:
```
from textual.app import App

class LogApp(App):

    def on_load(self):
        self.log("In the log handler!", pi=3.141529)

    def on_mount(self):
        self.log(self.tree)

if __name__ == "__main__":
    LogApp().run()
```

----------------------------------------

TITLE: Styling a Focused Widget in Textual
DESCRIPTION: This CSS snippet styles a widget when it has focus, changing the background and foreground colors to indicate focus.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/widgets.md#_snippet_11

LANGUAGE: css
CODE:
```
Counter:focus {
    background: $panel;
    color: $text;
}

Counter {
    height: 5;
    width: 10;
    border: tall $primary;
    content-align: center middle;
}
```

----------------------------------------

TITLE: Declaring Asynchronous Workers in Textual Python
DESCRIPTION: This example illustrates how to define an asynchronous worker function in Textual using the @work() decorator without the thread=True parameter. The function must be declared async. This approach is suitable when a separate thread is not needed, preventing accidental creation of threaded workers and potential unexpected results.
SOURCE: https://github.com/textualize/textual/blob/main/docs/FAQ.md#_snippet_4

LANGUAGE: Python
CODE:
```
@work()
async def run_in_background():
    ...
```

----------------------------------------

TITLE: Self-Inspecting Rich Inspect Function (Python)
DESCRIPTION: This snippet demonstrates a meta-use case of `rich.inspect` by inspecting the `inspect` function itself. This reveals all available arguments and options for `inspect`, allowing users to discover its full capabilities.
SOURCE: https://github.com/textualize/textual/blob/main/docs/blog/posts/rich-inspect.md#_snippet_3

LANGUAGE: Python
CODE:
```
>>> inspect(inspect)
```

----------------------------------------

TITLE: Creating Clickable Links (Textual Markup)
DESCRIPTION: Shows how to create a clickable link in Textual markup. The `link=` attribute specifies the URL, making the enclosed text a hyperlink that launches the web browser when clicked, if supported by the terminal.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/content.md#_snippet_17

LANGUAGE: Textual Markup
CODE:
```
[link="https://www.willmcgugan.com"]Visit my blog![/link]
```

----------------------------------------

TITLE: Updating Textual Snapshots with Pytest
DESCRIPTION: This command updates the saved snapshot for the Textual application. It should only be run after visually confirming that the current output (left side of the snapshot report) is correct. This action establishes the current visual state as the new 'ground truth' for future comparisons, overwriting any previous snapshots.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/testing.md#_snippet_12

LANGUAGE: shell
CODE:
```
pytest --snapshot-update
```

----------------------------------------

TITLE: Styling a Fixed-Size Grid Layout in Textual CSS
DESCRIPTION: This CSS snippet configures the `grid-size` property for a Textual grid layout, specifically setting it to 3x2. It defines the dimensions of the grid, ensuring widgets are placed within the specified number of columns and rows.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/layout.md#_snippet_7

LANGUAGE: css
CODE:
```
--8<-- "docs/examples/guide/layout/grid_layout1.tcss"
```

----------------------------------------

TITLE: Creating a Simple Form with Input Widgets - Python
DESCRIPTION: This snippet demonstrates the basic creation of a form using two `Input` widgets in Textual, showcasing their fundamental integration within a Textual application.
SOURCE: https://github.com/textualize/textual/blob/main/docs/widgets/input.md#_snippet_0

LANGUAGE: Python
CODE:
```
--8<-- "docs/examples/widgets/input.py"
```

----------------------------------------

TITLE: Serving Textual App from Python Module Command
DESCRIPTION: Serves a Textual application by executing it as a Python module command. This requires specifying the full command, including `python -m`, to correctly launch the app for serving.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/devtools.md#_snippet_8

LANGUAGE: bash
CODE:
```
textual serve "python -m textual"
```

----------------------------------------

TITLE: Inspecting Object Methods with Rich Inspect (Python)
DESCRIPTION: This snippet shows how to use `rich.inspect` with the `methods=True` argument to include all public API methods in the inspection report. This provides a more comprehensive view of an object's capabilities.
SOURCE: https://github.com/textualize/textual/blob/main/docs/blog/posts/rich-inspect.md#_snippet_1

LANGUAGE: Python
CODE:
```
>>> inspect(text_file, methods=True)
```

----------------------------------------

TITLE: Getting a Built-in TextArea Theme in Python
DESCRIPTION: This code snippet shows how to retrieve a reference to an existing built-in TextAreaTheme, such as 'monokai', using the TextAreaTheme.get_builtin_theme class method. This allows developers to extend or modify existing themes rather than creating them from scratch.
SOURCE: https://github.com/textualize/textual/blob/main/docs/widgets/text_area.md#_snippet_10

LANGUAGE: python
CODE:
```
from textual.widgets.text_area import TextAreaTheme

monokai = TextAreaTheme.get_builtin_theme("monokai")
```

----------------------------------------

TITLE: Using Viewport Width Unit for Viewport-Relative Length in Textualize CSS
DESCRIPTION: This example shows the 'vw' unit, which sets a widget's length as a percentage relative to the *viewport width*. This unit provides a way to size elements relative to the overall terminal window, independent of parent containers.
SOURCE: https://github.com/textualize/textual/blob/main/docs/css_types/scalar.md#_snippet_5

LANGUAGE: CSS
CODE:
```
width: 25vw
```

----------------------------------------

TITLE: Setting Widget Width in Python
DESCRIPTION: Illustrates how to programmatically control a widget's width in Textual using its `styles` attribute. Examples include setting a fixed width (integer), a percentage width (string), and an automatic width (string).
SOURCE: https://github.com/textualize/textual/blob/main/docs/styles/width.md#_snippet_6

LANGUAGE: python
CODE:
```
widget.styles.width = 10
widget.styles.width = "50%"
widget.styles.width = "auto"
```

----------------------------------------

TITLE: Setting Content Alignment in Textual Python
DESCRIPTION: This snippet illustrates how to programmatically set content alignment for a Textual widget using its `styles` attribute. It demonstrates assigning a tuple for combined horizontal and vertical alignment via `content_align`, and individual string values for `content_align_horizontal` and `content_align_vertical`.
SOURCE: https://github.com/textualize/textual/blob/main/docs/styles/content_align.md#_snippet_1

LANGUAGE: python
CODE:
```
# Align content in the very center of a widget
widget.styles.content_align = ("center", "middle")
# Align content at the top right of a widget
widget.styles.content_align = ("right", "top")

# Change the horizontal alignment of the content of a widget
widget.styles.content_align_horizontal = "right"
# Change the vertical alignment of the content of a widget
widget.styles.content_align_vertical = "middle"
```

----------------------------------------

TITLE: Composing TabbedContent with Markdown Documents - Python
DESCRIPTION: This Python snippet demonstrates how to use the TabbedContent widget to display multiple Markdown documents, showcasing its expressive interface for composing UI elements. It takes tab titles as arguments and yields Markdown widgets for each tab's content, simplifying the creation of tabbed UIs.
SOURCE: https://github.com/textualize/textual/blob/main/docs/blog/posts/release0-16-0.md#_snippet_0

LANGUAGE: python
CODE:
```
def compose(self) -> ComposeResult:
    with TabbedContent("Leto", "Jessica", "Paul"):
        yield Markdown(LETO)
        yield Markdown(JESSICA)
        yield Markdown(PAUL)
```

----------------------------------------

TITLE: Decreasing Textual Console Verbosity by Excluding Groups
DESCRIPTION: Starts the Textual debug console while excluding specific message groups using the `-x` flag. This allows filtering logs to focus on particular types of messages, such as warnings, errors, and `print` statements, by excluding others.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/devtools.md#_snippet_14

LANGUAGE: bash
CODE:
```
textual console -x SYSTEM -x EVENT -x DEBUG -x INFO
```

----------------------------------------

TITLE: Integrating Python's Logging with TextualHandler (Python)
DESCRIPTION: This example shows how to configure Python's standard `logging` module to direct its output to Textual's devtools console using `TextualHandler`. This is particularly useful for viewing logs from third-party libraries that utilize the built-in logging module within a Textual application.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/devtools.md#_snippet_20

LANGUAGE: python
CODE:
```
import logging
from textual.app import App
from textual.logging import TextualHandler

logging.basicConfig(
    level="NOTSET",
    handlers=[TextualHandler()],
)


class LogApp(App):
    """Using logging with Textual."""

    def on_mount(self) -> None:
        logging.debug("Logged via TextualHandler")


if __name__ == "__main__":
    LogApp().run()
```

----------------------------------------

TITLE: Applying Display Styles in CSS
DESCRIPTION: Demonstrates how to explicitly set the `display` property in CSS to either show (`block`) or hide (`none`) a widget, controlling its rendering and space reservation.
SOURCE: https://github.com/textualize/textual/blob/main/docs/styles/display.md#_snippet_1

LANGUAGE: css
CODE:
```
/* Widget is shown */
display: block;

/* Widget is not shown */
display: none;
```

----------------------------------------

TITLE: Dynamically Calling Variant Update Methods with Getattr in Python
DESCRIPTION: This method dynamically dispatches to a specific update method based on the current `variant` attribute. It uses `getattr` to construct the method name (e.g., `_update_size_variant`) and then calls it, providing a flexible and extensible way to handle variant-specific rendering without large conditional blocks.
SOURCE: https://github.com/textualize/textual/blob/main/docs/blog/posts/placeholder-pr.md#_snippet_5

LANGUAGE: Python
CODE:
```
class Placeholder(Static):
    # ...
    def call_variant_update(self) -> None:
        """Calls the appropriate method to update the render of the placeholder."""
        update_variant_method = getattr(self, f"_update_{self.variant}_variant")
        update_variant_method()
```

----------------------------------------

TITLE: CSS Rule for Error and Disabled Classes
DESCRIPTION: This CSS rule targets widgets that have both the 'error' and 'disabled' classes applied. It sets their background to dark red.  Class selectors are chained together with a full stop (`.`) to match widgets with all specified classes.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/CSS.md#_snippet_12

LANGUAGE: css
CODE:
```
.error.disabled {
  background: darkred;
}
```

----------------------------------------

TITLE: Applying Borders in Textual CSS
DESCRIPTION: Demonstrates various ways to apply borders to widgets using Textual CSS. Examples include setting a universal border, a border on a specific edge, and a border with color blending for opacity.
SOURCE: https://github.com/textualize/textual/blob/main/docs/styles/border.md#_snippet_2

LANGUAGE: css
CODE:
```
/* Set a heavy white border */
border: heavy white;

/* Set a red border on the left */
border-left: outer red;

/* Set a rounded orange border, 50% opacity. */
border: round orange 50%;
```

----------------------------------------

TITLE: Applying Margin Styles in CSS
DESCRIPTION: This snippet demonstrates various ways to apply margin to a widget using CSS. It shows shorthand notations for setting uniform margin, vertical/horizontal margins, and individual margins for all four sides (top, right, bottom, left). It also includes examples for setting margin on each side independently using `margin-top`, `margin-right`, `margin-bottom`, and `margin-left`.
SOURCE: https://github.com/textualize/textual/blob/main/docs/styles/margin.md#_snippet_1

LANGUAGE: CSS
CODE:
```
/* Set margin of 1 around all edges */
margin: 1;
/* Set margin of 2 on the top and bottom edges, and 4 on the left and right */
margin: 2 4;
/* Set margin of 1 on the top, 2 on the right,
                 3 on the bottom, and 4 on the left */
margin: 1 2 3 4;

margin-top: 1;
margin-right: 2;
margin-bottom: 3;
margin-left: 4;
```

----------------------------------------

TITLE: Composing TabbedContent with TabPane Widgets - Python
DESCRIPTION: This snippet shows an alternative way to compose TabbedContent by wrapping each content pane within a TabPane widget. The TabPane constructor takes the tab title as its first parameter. This approach provides more explicit control over each tab's content and is useful when more complex configurations or IDs are needed.
SOURCE: https://github.com/textualize/textual/blob/main/docs/widgets/tabbed_content.md#_snippet_1

LANGUAGE: python
CODE:
```
def compose(self) -> ComposeResult:
    with TabbedContent():
        with TabPane("Leto"):
            yield Markdown(LETO)
        with TabPane("Jessica"):
            yield Markdown(JESSICA)
        with TabPane("Paul"):
            yield Markdown(PAUL)
```

----------------------------------------

TITLE: CSS without Nesting
DESCRIPTION: This CSS defines styles for a container, buttons, and specific button types (affirmative and negative) without using nesting. It demonstrates a straightforward approach where each selector is fully specified.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/CSS.md#_snippet_25

LANGUAGE: css
CODE:
```
#questions {
    layout: horizontal;
    height: 3;
    padding: 1;
    align: center middle;
}

#questions .button {
    width: 10;
    height: 1fr;
    border: tall $primary 60%;
    color: $text;
    dock: left;
    margin: 1;
    content-align: center middle;
}

#questions .button.affirmative {
    background: $success;
    color: $text-light;
}

#questions .button.negative {
    background: $error;
    color: $text-light;
}
```

----------------------------------------

TITLE: Setting Height in Python (Basic Examples)
DESCRIPTION: Demonstrates how to programmatically set a widget's height using Textual's Python API, covering explicit integer values, percentage strings, and automatic sizing.
SOURCE: https://github.com/textualize/textual/blob/main/docs/styles/height.md#_snippet_2

LANGUAGE: Python
CODE:
```
self.styles.height = 10  # Explicit cell height can be an int
self.styles.height = "50%"
self.styles.height = "auto"
```

----------------------------------------

TITLE: Defining a CSS Variable
DESCRIPTION: This CSS defines a variable named `$border` and assigns it the value 'wide green'. Variables in Textual CSS are prefixed with `$` and can be used to store reusable styling values.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/CSS.md#_snippet_20

LANGUAGE: css
CODE:
```
$border: wide green;
```

----------------------------------------

TITLE: Running Setup Code Before Textual Snapshot Capture (Python)
DESCRIPTION: This snippet illustrates how to execute arbitrary asynchronous code before a snapshot is captured using the `run_before` parameter. The `run_before` parameter takes an `async` function that receives a `pilot` object, allowing for interactions like hovering over a specific widget (e.g., `#number-5`) before the snapshot is taken. This is useful for setting up specific UI states.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/testing.md#_snippet_15

LANGUAGE: python
CODE:
```
def test_calculator_hover_number(snap_compare):
    async def run_before(pilot) -> None:
        await pilot.hover("#number-5")

    assert snap_compare("path/to/calculator.py", run_before=run_before)
```

----------------------------------------

TITLE: Typing a Select Widget for Integer Values (Python)
DESCRIPTION: This snippet demonstrates how to explicitly type a Textual Select widget to handle integer values. It initializes a list of options, where each option is a tuple containing a display string and an integer value, and then creates a Select widget instance with the specified integer type. This ensures type safety for the selected value.
SOURCE: https://github.com/textualize/textual/blob/main/docs/widgets/select.md#_snippet_0

LANGUAGE: python
CODE:
```
options = [("First", 1), ("Second", 2)]
my_select: Select[int] = Select(options)
```

----------------------------------------

TITLE: Setting Vertical Overflow to Hidden in CSS
DESCRIPTION: This CSS snippet demonstrates how to set the `overflow-y` property to `hidden` for an element with the ID `container`. This prevents content from overflowing vertically, effectively clipping any content that extends beyond the element's height. It's useful for controlling layout and preventing scrollbars.
SOURCE: https://github.com/textualize/textual/blob/main/docs/css_types/overflow.md#_snippet_0

LANGUAGE: css
CODE:
```
#container {
    overflow-y: hidden;  /* Don't overflow */
}
```

----------------------------------------

TITLE: Defining States with CSS Classes (Textual CSS)
DESCRIPTION: Defines CSS rules for a Textual stopwatch widget, including a `.started` class to apply specific styles (like background color and hiding/showing buttons) when the widget is in a started state.
SOURCE: https://github.com/textualize/textual/blob/main/docs/tutorial.md#_snippet_7

LANGUAGE: css
CODE:
```
/* stopwatch04.tcss */

Screen {
    align: center middle;
}

#stopwatch {
    width: 50%;
    height: 50%;
    background: $surface;
    border: heavy $surface;
    align: center middle;
}

#time {
    width: 100%;
    height: 50%;
    text-align: center;
    background: $panel;
    content-align: center middle;
    color: $text;
}

#buttons {
    width: 100%;
    height: 50%;
    layout: horizontal;
    align: center middle;
}

Button {
    width: 1fr;
    margin: 1;
}

/* New rules for the started state */
.started {
    background: $success;
}

.started #time {
    background: $success-darken-2;
}

.started #start {
    display: none;
}

.started #reset {
    display: none;
}

.started #stop {
    display: block;
}

/* Default state rules */
:not(.started) #stop {
    display: none;
}
```

----------------------------------------

TITLE: Static Widget with Default CSS in Textual (Python)
DESCRIPTION: This code defines a custom widget named `Hello` that extends the `Static` widget class and includes embedded default CSS. The CSS is defined as a `DEFAULT_CSS` class variable and styles the widget's appearance.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/widgets.md#_snippet_5

LANGUAGE: Python
CODE:
```
class Hello(Static):
    
```

----------------------------------------

TITLE: Clock with Recompose - Python
DESCRIPTION: This example demonstrates a clock implemented using recompose. The `Digits` widget is replaced with a new instance every time the `time` attribute changes, simplifying the code by removing the need for a separate `watch_time` method.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/reactivity.md#_snippet_16

LANGUAGE: Python
CODE:
```
class Digits(Widget):
    
```

----------------------------------------

TITLE: Defining a Custom Textual Theme (Python)
DESCRIPTION: This snippet shows how to define a custom theme in Textual using the `Theme` class. It maps variable names to specific color values and can include additional CSS variables. This theme must be registered before use.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/design.md#_snippet_1

LANGUAGE: python
CODE:
```
from textual.theme import Theme

arctic_theme = Theme(
    name="arctic",
    primary="#88C0D0",
    secondary="#81A1C1",
    accent="#B48EAD",
    foreground="#D8DEE9",
    background="#2E3440",
    success="#A3BE8C",
    warning="#EBCB8B",
    error="#BF616A",
    surface="#3B4252",
    panel="#434C5E",
    dark=True,
    variables={
        "block-cursor-text-style": "none",
        "footer-key-foreground": "#88C0D0",
        "input-selection-background": "#81a1c1 35%",
    },
)
```

----------------------------------------

TITLE: Creating a 2x2 Grid with Nested Utility Containers in Python
DESCRIPTION: This snippet demonstrates how to construct a simple 2x2 grid layout in Textual by nesting `Horizontal` and `Vertical` container widgets. It shows the traditional method of adding children using positional arguments to achieve a single row with two columns.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/layout.md#_snippet_1

LANGUAGE: python
CODE:
```
--8<-- "docs/examples/guide/layout/utility_containers.py"
```

----------------------------------------

TITLE: Implementing Thread Workers with urllib.request in Textual (Python)
DESCRIPTION: This example illustrates the use of thread workers in Textual for non-asynchronous operations, specifically fetching weather data using urllib.request. It shows how to use the @work(thread=True) decorator and how to check for cancellation manually within a thread worker using get_current_worker to ensure graceful exit, as direct cancellation like coroutines is not possible.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/workers.md#_snippet_1

LANGUAGE: python
CODE:
```
import urllib.request
import json
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Button, Label
from textual.worker import work, get_current_worker, WorkerState

class WeatherAppThread(App):
    BINDINGS = [("q", "quit", "Quit")]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        yield Button("Get Weather (Thread)", id="get_weather_thread")
        yield Label("Weather: N/A", id="weather_label_thread")

    @work(thread=True, exclusive=True)
    def get_weather_data_thread(self) -> str:
        worker = get_current_worker()
        try:
            with urllib.request.urlopen("https://api.weather.gov/points/39.7456,-97.0892") as url:
                if worker.is_cancelled: # Manual cancellation check
                    return "Cancelled"
                data = json.loads(url.read().decode())
                if worker.is_cancelled: # Manual cancellation check
                    return "Cancelled"
                city = data["properties"]["relativeLocation"]["properties"]["city"]
                # Simulate some work
                for _ in range(2):
                    if worker.is_cancelled:
                        return "Cancelled"
                    self.call_from_thread(lambda: self.log("Working...")) # Call UI from thread
                    import time
                    time.sleep(0.1)
                return city
        except Exception as e:
            self.call_from_thread(lambda: self.log(f"Thread worker error: {e}"))
            raise

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "get_weather_thread":
            self.run_worker(self.get_weather_data_thread(), exit_on_error=False)

    def on_worker_state_changed(self, event: WorkerState.StateChanged) -> None:
        self.log(f"Thread Worker {event.worker.name} changed state to {event.state.name}")
        if event.state == WorkerState.SUCCESS:
            self.query_one("#weather_label_thread", Label).update(f"Weather: {event.worker.result}")
        elif event.state == WorkerState.ERROR:
            self.query_one("#weather_label_thread", Label).update(f"Error: {event.worker.error}")
        elif event.state == WorkerState.CANCELLED:
            self.query_one("#weather_label_thread", Label).update("Weather: Cancelled")

if __name__ == "__main__":
    app = WeatherAppThread()
    app.run()
```

----------------------------------------

TITLE: Styling a Widget with an ID Selector
DESCRIPTION: This CSS code styles the widget with the ID "next" by drawing a red outline around it. The ID selector starts with a hash (`#`).
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/CSS.md#_snippet_8

LANGUAGE: css
CODE:
```
#next {
  outline: red;
}
```

----------------------------------------

TITLE: Creating a Widget with an ID
DESCRIPTION: This Python code creates a `Button` widget and assigns it the ID "next". The ID can be used to target the widget with a CSS selector.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/CSS.md#_snippet_7

LANGUAGE: python
CODE:
```
yield Button(id="next")
```

----------------------------------------

TITLE: Updating Rich Progress Bar in Textual App (Python)
DESCRIPTION: This snippet demonstrates how a Textual widget updates a Rich progress bar using `self.update()` with the `Progress` object. It also shows the basic structure of a Textual `App` that composes and runs an `IndeterminateProgress` widget, which is expected to contain the progress bar logic.
SOURCE: https://github.com/textualize/textual/blob/main/docs/blog/posts/spinners-and-pbs-in-textual.md#_snippet_5

LANGUAGE: Python
CODE:
```
        self.update(self._bar)  # (4)!


class MyApp(App):
    def compose(self) -> ComposeResult:
        yield IndeterminateProgress()


if __name__ == "__main__":
    app = MyApp()
    app.run()
```

----------------------------------------

TITLE: Button with CSS Class in Textual
DESCRIPTION: This code demonstrates how to create a Textual Button widget and assign a CSS class named 'success' to it. This allows the button to be styled using CSS rules that target the '.success' class.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/CSS.md#_snippet_9

LANGUAGE: python
CODE:
```
yield Button(classes="success")
```

----------------------------------------

TITLE: Setting Grid Row Heights in CSS
DESCRIPTION: Demonstrates how to set grid row heights using the `grid-rows` CSS property in Textual. It shows examples for setting all rows to a uniform height and for defining alternating row heights using `fr` units.
SOURCE: https://github.com/textualize/textual/blob/main/docs/styles/grid/grid_rows.md#_snippet_0

LANGUAGE: css
CODE:
```
/* Set all rows to have 50% height */
grid-rows: 50%;

/* Every other row is twice as tall as the first one */
grid-rows: 1fr 2fr;
```

----------------------------------------

TITLE: Displaying Rich Spinner in Textual App (Python)
DESCRIPTION: This snippet illustrates how to integrate and display a Rich spinner within a Textual application. It defines a `SpinnerWidget` that initializes a `rich.spinner.Spinner` instance and updates it frequently using `set_interval` and `self.update()`, similar to how a progress bar is updated. The `MyApp` then composes and runs this custom spinner widget.
SOURCE: https://github.com/textualize/textual/blob/main/docs/blog/posts/spinners-and-pbs-in-textual.md#_snippet_6

LANGUAGE: Python
CODE:
```
from rich.spinner import Spinner

from textual.app import App, ComposeResult
from textual.widgets import Static


class SpinnerWidget(Static):
    def __init__(self):
        super().__init__("")
        self._spinner = Spinner("moon")  # (1)!

    def on_mount(self) -> None:
        self.update_render = self.set_interval(1 / 60, self.update_spinner)

    def update_spinner(self) -> None:
        self.update(self._spinner)


class MyApp(App[None]):
    def compose(self) -> ComposeResult:
        yield SpinnerWidget()


MyApp().run()
```

----------------------------------------

TITLE: Applying Various Color Styles to Widgets (Python)
DESCRIPTION: This example illustrates applying various color-related styles to multiple `Static` widgets. It sets text color, background color, and border color for different widgets using named color constants.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/styles.md#_snippet_3

LANGUAGE: python
CODE:
```
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static
from textual.containers import Container

class ColorApp(App):
    def compose(self) -> ComposeResult:
        yield Container(
            Static("Red Text", id="red-text"),
            Static("Green Background", id="green-bg"),
            Static("Blue Border", id="blue-border"),
        )
        yield Header()
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#red-text").styles.color = "crimson"
        self.query_one("#green-bg").styles.background = "lime"
        self.query_one("#blue-border").styles.border = ("solid", "darkblue")
        self.query_one("#blue-border").styles.color = "white"

if __name__ == "__main__":
    app = ColorApp()
    app.run()
```

----------------------------------------

TITLE: Defining Custom Messages (Textual 0.14.0+) - Python
DESCRIPTION: This code defines a custom `Changed` message class for `MyWidget` in Textual 0.14.0 and later. The `sender` argument is no longer required in the `__init__` method, simplifying message class definitions as the framework handles it automatically.
SOURCE: https://github.com/textualize/textual/blob/main/docs/blog/posts/release0-14-0.md#_snippet_3

LANGUAGE: Python
CODE:
```
class MyWidget(Widget):

    class Changed(Message):
        """My widget change event."""
        def __init__(self, item_index:int) -> None:
            self.item_index = item_index
            super().__init__()
```

----------------------------------------

TITLE: Simulating Click with Absolute Offset with Textual Pilot (Python)
DESCRIPTION: This snippet illustrates how to simulate a mouse click at specific screen coordinates by providing an `offset` tuple to the `pilot.click` method. The offset is relative to the screen's top-left corner.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/testing.md#_snippet_4

LANGUAGE: python
CODE:
```
await pilot.click(offset=(10, 5))
```

----------------------------------------

TITLE: Setting Absolute Position and Offset in Python Styles
DESCRIPTION: This Python snippet shows how to programmatically set a widget's position to `absolute` and its `offset` using the `styles` attribute. The `offset` is provided as a tuple `(10, 5)`, corresponding to horizontal and vertical displacement from the container's origin when the position is absolute.
SOURCE: https://github.com/textualize/textual/blob/main/docs/css_types/position.md#_snippet_1

LANGUAGE: python
CODE:
```
widget.styles.position = "absolute"
widget.styles.offset = (10, 5)
```

----------------------------------------

TITLE: Applying Fixed and Fractional Dimensions in Textual CSS
DESCRIPTION: This CSS snippet demonstrates how to define the `width` in fixed cell units and `height` using a fractional unit (`1fr`) for a `Horizontal` widget. The `1fr` unit ensures the widget takes up a proportional size relative to its container's available space.
SOURCE: https://github.com/textualize/textual/blob/main/docs/css_types/scalar.md#_snippet_7

LANGUAGE: css
CODE:
```
Horizontal {
    width: 60;     /* 60 cells */
    height: 1fr;   /* proportional size of 1 */
}
```

----------------------------------------

TITLE: Applying Inline CSS in Textual App (Python)
DESCRIPTION: This Python example illustrates how to embed CSS directly within a Textual application's Python code. By setting the CSS class variable to a multi-line string containing CSS rules, developers can define styles without external files, suitable for smaller or self-contained styling needs.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/app.md#_snippet_9

LANGUAGE: python
CODE:
```
--8<-- "docs/examples/app/question03.py"
```

----------------------------------------

TITLE: Setting Widget Visibility via Python Styles
DESCRIPTION: This Python code demonstrates how to programmatically adjust a Textual widget's visibility by directly assigning string values ('hidden' or 'visible') to its `styles.visibility` property, offering fine-grained control from the application logic.
SOURCE: https://github.com/textualize/textual/blob/main/docs/styles/visibility.md#_snippet_4

LANGUAGE: python
CODE:
```
# Widget is invisible
self.styles.visibility = "hidden"

# Widget is visible
self.styles.visibility = "visible"
```

----------------------------------------

TITLE: Disabling Markup in Notify Method (Python)
DESCRIPTION: Illustrates how to disable markup processing when using Textual's `notify()` method. Setting `markup=False` ensures that the input string, such as a Python `repr` of a list, is displayed literally without being interpreted as markup.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/content.md#_snippet_22

LANGUAGE: Python
CODE:
```
# debug code: what is my_list at this point?
self.notify(repr(my_list), markup=False)
```

----------------------------------------

TITLE: Setting Terminal Size for Textual Snapshot Tests (Python)
DESCRIPTION: This snippet demonstrates how to capture a snapshot with a specific terminal size using the `terminal_size` parameter. The parameter accepts a tuple `(width, height)` to define the dimensions of the simulated terminal. In this example, the snapshot is taken with a terminal size of 50 columns by 100 rows.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/testing.md#_snippet_14

LANGUAGE: python
CODE:
```
def test_calculator(snap_compare):
    assert snap_compare("path/to/calculator.py", terminal_size=(50, 100))
```

----------------------------------------

TITLE: Running Textual App with Varied Arguments in Python
DESCRIPTION: This snippet provides examples of how to instantiate and run the Greetings Textual App using different argument passing methods: default, keyword, and positional. It showcases the flexibility in launching Textual applications with specific initial configurations, demonstrating how the __init__ method's parameters can be populated at runtime.
SOURCE: https://github.com/textualize/textual/blob/main/docs/FAQ.md#_snippet_6

LANGUAGE: Python
CODE:
```
# Running with default arguments.
Greetings().run()

# Running with a keyword argument.
Greetings(to_greet="davep").run()

# Running with both positional arguments.
Greetings("Well hello", "there").run()
```

----------------------------------------

TITLE: Running the Textual Built-in Demo Application
DESCRIPTION: This command executes the built-in Textual demo application directly from the installed package. It provides a quick way to see Textual's capabilities without writing any code.
SOURCE: https://github.com/textualize/textual/blob/main/README.md#_snippet_2

LANGUAGE: Bash
CODE:
```
python -m textual
```

----------------------------------------

TITLE: Accessing Textual CLI Help
DESCRIPTION: Displays a list of available sub-commands and their usage for the Textual command-line interface. This command is available after installing the Textual developer tools.
SOURCE: https://github.com/textualize/textual/blob/main/docs/getting_started.md#_snippet_5

LANGUAGE: Bash
CODE:
```
textual --help
```

----------------------------------------

TITLE: Typing SelectionList with Integer Values in Python
DESCRIPTION: This snippet demonstrates how to explicitly type a `SelectionList` widget in Textual to handle integer values for its selections. It initializes a list of tuples, where each tuple contains a prompt and an integer value, and then creates a `SelectionList` instance, specifying `int` as the generic type for its values. This ensures type safety for the selection values.
SOURCE: https://github.com/textualize/textual/blob/main/docs/widgets/selection_list.md#_snippet_0

LANGUAGE: python
CODE:
```
selections = [("First", 1), ("Second", 2)]
my_selection_list: SelectionList[int] =  SelectionList(*selections)
```

----------------------------------------

TITLE: Setting min-height in Python (Textual Styles)
DESCRIPTION: Illustrates how to programmatically set the `min_height` style for a widget in Textual using Python. It shows examples of assigning both an integer value for rows and a string representing a viewport-relative unit.
SOURCE: https://github.com/textualize/textual/blob/main/docs/styles/min_height.md#_snippet_2

LANGUAGE: python
CODE:
```
# Set the minimum height to 10 rows
widget.styles.min_height = 10

# Set the minimum height to 25% of the viewport height
widget.styles.min_height = "25vh"
```

----------------------------------------

TITLE: Running Textual CLI Example (Shell)
DESCRIPTION: This command demonstrates how to execute a Textual application script using the Textual command-line interface. It runs the 'text_style.py' file, which is likely an example used for generating documentation screenshots.
SOURCE: https://github.com/textualize/textual/blob/main/docs/examples/styles/README.md#_snippet_0

LANGUAGE: Shell
CODE:
```
textual run text_style.py
```

----------------------------------------

TITLE: Aligning Container Horizontally in CSS
DESCRIPTION: This CSS snippet demonstrates how to align an element to the right along the horizontal axis using the `align-horizontal` property. This property is applied to a container to control the horizontal positioning of its content.
SOURCE: https://github.com/textualize/textual/blob/main/docs/css_types/horizontal.md#_snippet_0

LANGUAGE: css
CODE:
```
.container {
    align-horizontal: right;
}
```

----------------------------------------

TITLE: Setting Vertical Alignment in CSS
DESCRIPTION: This CSS snippet demonstrates how to set the vertical alignment of an element within a container using the `align-vertical` property. It aligns the element to the top of its vertical axis, typically used in frameworks like Textual that extend CSS-like styling.
SOURCE: https://github.com/textualize/textual/blob/main/docs/css_types/vertical.md#_snippet_0

LANGUAGE: css
CODE:
```
.container {
    align-vertical: top;
}
```

----------------------------------------

TITLE: Launching Textual Application via uv (Shell)
DESCRIPTION: This shell command uses `uv` to run the `mother.py` Textual application. It's the command-line instruction to start the TUI.
SOURCE: https://github.com/textualize/textual/blob/main/docs/blog/posts/anatomy-of-a-textual-user-interface.md#_snippet_10

LANGUAGE: Shell
CODE:
```
uv run mother.py
```

----------------------------------------

TITLE: Running Textual Example Application (Shell)
DESCRIPTION: This snippet provides shell commands to navigate to the Textual examples directory and execute a specific Python example application, 'pride.py'. It demonstrates the standard way to run Textual examples from the command line.
SOURCE: https://github.com/textualize/textual/blob/main/examples/README.md#_snippet_0

LANGUAGE: Shell
CODE:
```
cd textual/examples
python pride.py
```

----------------------------------------

TITLE: Setting Widget Width to 50% (Python)
DESCRIPTION: This Python example demonstrates a basic Textual application that applies a 50% width to a widget using an external CSS file. The application composes a header, a container widget, and a footer.
SOURCE: https://github.com/textualize/textual/blob/main/docs/styles/width.md#_snippet_1

LANGUAGE: python
CODE:
```
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Container

class WidthApp(App):
    CSS_PATH = "width.tcss"

    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(id="my-widget")
        yield Footer()

if __name__ == "__main__":
    app = WidthApp()
    app.run()
```

----------------------------------------

TITLE: Centering a Single Widget with `align` in Textual Python
DESCRIPTION: This snippet demonstrates how to center a single `Button` widget within a Textual `Screen` using the `align: center middle;` CSS property applied to the `Screen`. This method centers the *content* of the screen, which works effectively for a single child.
SOURCE: https://github.com/textualize/textual/blob/main/questions/align-center-middle.question.md#_snippet_0

LANGUAGE: Python
CODE:
```
from textual.app import App, ComposeResult
from textual.widgets import Button

class ButtonApp(App):

    CSS = """
    Screen {
        align: center middle;
    }
    """

    def compose(self) -> ComposeResult:
        yield Button("PUSH ME!")

if __name__ == "__main__":
    ButtonApp().run()
```

----------------------------------------

TITLE: Setting Max-width in CSS
DESCRIPTION: This snippet demonstrates how to apply the `max-width` style directly in CSS. It shows examples of setting a fixed maximum width in rows and a relative maximum width as a percentage of the viewport width.
SOURCE: https://github.com/textualize/textual/blob/main/docs/styles/max_width.md#_snippet_0

LANGUAGE: css
CODE:
```
/* Set the maximum width to 10 rows */
max-width: 10;

/* Set the maximum width to 25% of the viewport width */
max-width: 25vw;
```

----------------------------------------

TITLE: Syntax for Display Property in CSS
DESCRIPTION: Defines the valid syntax for the `display` CSS property, allowing widgets to be shown (`block`) or hidden (`none`). The default value is `block`.
SOURCE: https://github.com/textualize/textual/blob/main/docs/styles/display.md#_snippet_0

LANGUAGE: css
CODE:
```
display: block | none;
```

----------------------------------------

TITLE: Applying Content Alignment in Textual CSS
DESCRIPTION: This snippet demonstrates how to apply content alignment styles in Textual CSS. It shows examples of setting both horizontal and vertical alignment simultaneously using `content-align`, and individually using `content-align-horizontal` and `content-align-vertical`.
SOURCE: https://github.com/textualize/textual/blob/main/docs/styles/content_align.md#_snippet_0

LANGUAGE: css
CODE:
```
/* Align content in the very center of a widget */
content-align: center middle;
/* Align content at the top right of a widget */
content-align: right top;

/* Change the horizontal alignment of the content of a widget */
content-align-horizontal: right;
/* Change the vertical alignment of the content of a widget */
content-align-vertical: middle;
```

----------------------------------------

TITLE: Using Auto Value for Optimal Sizing in Textualize CSS
DESCRIPTION: This snippet demonstrates the 'auto' value, which instructs Textualize to automatically compute the optimal size for a widget. This typically means the widget will size itself to fit its content without causing scrolling.
SOURCE: https://github.com/textualize/textual/blob/main/docs/css_types/scalar.md#_snippet_6

LANGUAGE: CSS
CODE:
```
width: auto
```

----------------------------------------

TITLE: Setting Widget Padding in Python
DESCRIPTION: This snippet illustrates how to programmatically set padding for a Textual widget using its `styles.padding` attribute in Python. It demonstrates setting uniform padding with a single integer, vertical and horizontal padding with a 2-integer tuple, and distinct padding for all four edges (top, right, bottom, left) with a 4-integer tuple. Note that individual padding properties like `padding-top` are not directly settable via the Python API.
SOURCE: https://github.com/textualize/textual/blob/main/docs/styles/padding.md#_snippet_1

LANGUAGE: Python
CODE:
```
# Set padding of 1 around all edges
widget.styles.padding = 1
# Set padding of 2 on the top and bottom edges, and 4 on the left and right
widget.styles.padding = (2, 4)
# Set padding of 1 on top, 2 on the right, 3 on the bottom, and 4 on the left
widget.styles.padding = (1, 2, 3, 4)
```

----------------------------------------

TITLE: Moving Cursor and Selecting Text in TextArea (Python)
DESCRIPTION: This code moves the `TextArea` cursor to a specific location (row 4, column 8) and simultaneously selects all text between the original cursor position and the new target location. The `select=True` parameter enables text selection during the movement.
SOURCE: https://github.com/textualize/textual/blob/main/docs/widgets/text_area.md#_snippet_5

LANGUAGE: python
CODE:
```
# Move the cursor from its current location to row index 4,
# column index 8, while selecting all the text between.
text_area.move_cursor((4, 8), select=True)
```

----------------------------------------

TITLE: Custom Indeterminate Progress Widget in Textual (Python)
DESCRIPTION: This snippet defines `IndeterminateProgress`, a custom Textual `Static` widget intended to display an indeterminate progress bar. It initializes a `rich.progress.Progress` object with a `BarColumn` and adds an indeterminate task. The `on_mount` method sets up an interval timer to call `update_progress_bar` 60 times per second, aiming to update the widget's display.
SOURCE: https://github.com/textualize/textual/blob/main/docs/blog/posts/spinners-and-pbs-in-textual.md#_snippet_4

LANGUAGE: Python
CODE:
```
from rich.progress import Progress, BarColumn

from textual.app import App, ComposeResult
from textual.widgets import Static


class IndeterminateProgress(Static):
    def __init__(self):
        super().__init__("")
        self._bar = Progress(BarColumn())  # (1)!
        self._bar.add_task("", total=None)  # (2)!

    def on_mount(self) -> None:
        # When the widget is mounted start updating the display regularly.
        self.update_render = self.set_interval(
            1 / 60, self.update_progress_bar
        )  # (3)!

    def update_progress_bar(self) -> None:
```

----------------------------------------

TITLE: Textual Grid Layout Example (Python)
DESCRIPTION: Illustrates the application of Textual grid styles in a Python application. This snippet is a reference to an external Python file that sets up a Textual app demonstrating grid layout properties like `grid-size`, `column-span`, `row-span`, and `grid-gutter`.
SOURCE: https://github.com/textualize/textual/blob/main/docs/styles/grid/index.md#_snippet_1

LANGUAGE: Python
CODE:
```
--8<-- "docs/examples/styles/grid.py"
```

----------------------------------------

TITLE: Example External CSS for Textual App (CSS)
DESCRIPTION: This CSS snippet provides styling rules for a Textual application. It defines how elements, specifically a Label with a certain id, should appear, demonstrating the content of an external .tcss file referenced by a Textual app.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/app.md#_snippet_8

LANGUAGE: css
CODE:
```
--8<-- "docs/examples/app/question02.tcss"
```

----------------------------------------

TITLE: Defining Input Widget Types - Python
DESCRIPTION: This snippet illustrates how to utilize the `type` parameter of the `Input` widget to enforce specific data types like 'integer' or 'number', thereby preventing users from entering invalid characters.
SOURCE: https://github.com/textualize/textual/blob/main/docs/widgets/input.md#_snippet_1

LANGUAGE: Python
CODE:
```
--8<-- "docs/examples/widgets/input_types.py"
```

----------------------------------------

TITLE: Simulating Key Presses in Textual Snapshot Tests (Python)
DESCRIPTION: This snippet shows how to simulate key presses before a snapshot is captured using the `press` parameter. The `press` parameter takes a list of strings, where each string represents a key or a sequence of keys to be pressed. In this example, '1', '2', and '3' are pressed sequentially on the calculator app before the snapshot is taken.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/testing.md#_snippet_13

LANGUAGE: python
CODE:
```
def test_calculator_pressing_numbers(snap_compare):
    assert snap_compare("path/to/calculator.py", press=["1", "2", "3"])
```

----------------------------------------

TITLE: Clone Textual Repository (SSH)
DESCRIPTION: Command to clone the Textual repository from GitHub using the SSH protocol.
SOURCE: https://github.com/textualize/textual/blob/main/docs/tutorial.md#_snippet_1

LANGUAGE: bash
CODE:
```
git clone git@github.com:Textualize/textual.git
```

----------------------------------------

TITLE: Setting Text Alignment in CSS
DESCRIPTION: Illustrates how to set the `text-align` property to `right` for a widget using standard CSS. This snippet can be applied directly in a Textual CSS file.
SOURCE: https://github.com/textualize/textual/blob/main/docs/styles/text_align.md#_snippet_2

LANGUAGE: css
CODE:
```
/* Set text in the widget to be right aligned */
text-align: right;
```

----------------------------------------

TITLE: Displaying Full Help Documentation with Rich Inspect (Python)
DESCRIPTION: This snippet illustrates how to use `rich.inspect` with both `methods=True` and `help=True` to display the full, unabbreviated documentation for an object's attributes and methods. This is useful for in-depth understanding.
SOURCE: https://github.com/textualize/textual/blob/main/docs/blog/posts/rich-inspect.md#_snippet_2

LANGUAGE: Python
CODE:
```
>>> inspect(text_file, methods=True, help=True)
```

----------------------------------------

TITLE: Displaying Italic Text in Textual Markup
DESCRIPTION: This snippet demonstrates basic content markup by displaying the word 'Hello!' in italic style within a Textual widget. The `[i]` tag applies italic formatting, which is then rendered by Textual's markup engine.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/content.md#_snippet_1

LANGUAGE: Textual Markup
CODE:
```
[i]Hello!
```

----------------------------------------

TITLE: Comparing Textual Width Units (Python)
DESCRIPTION: This Python application composes multiple `Placeholder` widgets within a `Horizontal` container, each with a unique ID. These IDs are used by the accompanying CSS file to apply different width units, allowing for a visual comparison of their effects.
SOURCE: https://github.com/textualize/textual/blob/main/docs/styles/width.md#_snippet_3

LANGUAGE: python
CODE:
```
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Placeholder, Horizontal

class WidthComparisonApp(App):
    CSS_PATH = "width_comparison.tcss"

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            yield Placeholder(id="columns")
            yield Placeholder(id="percentage")
            yield Placeholder(id="tw")
            yield Placeholder(id="th")
            yield Placeholder(id="vw")
            yield Placeholder(id="vh")
            yield Placeholder(id="auto", content="#auto")
            yield Placeholder(id="fr1")
            yield Placeholder(id="fr3")
        yield Footer()

if __name__ == "__main__" :
    app = WidthComparisonApp()
    app.run()
```

----------------------------------------

TITLE: Typing Reactive Attributes
DESCRIPTION: This code shows how to add explicit type hints to reactive attributes, especially when the attribute type is a superset of the default type, such as making an attribute optional.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/reactivity.md#_snippet_2

LANGUAGE: Python
CODE:
```
name: reactive[str | None] = reactive("Paul")
```

----------------------------------------

TITLE: Setting Widget Width to 50% (CSS)
DESCRIPTION: This CSS snippet sets the width of a `Container` widget to 50% of its parent's available space. This is a common way to make widgets responsive to screen size.
SOURCE: https://github.com/textualize/textual/blob/main/docs/styles/width.md#_snippet_2

LANGUAGE: css
CODE:
```
/* width.tcss */
Container {
    width: 50%;
    background: darkblue;
}
```

----------------------------------------

TITLE: Matching Textual Messages by Arbitrary Attributes (Python)
DESCRIPTION: This example demonstrates how to use the `on` decorator with keyword arguments to match messages based on specific attributes, provided those attributes are in `Message.ALLOW_SELECTOR_MATCH`. Here, it matches `TabbedContent.TabActivated` only when the tab with the ID 'home' is activated.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/events.md#_snippet_3

LANGUAGE: python
CODE:
```
@on(TabbedContent.TabActivated, pane="#home")
def home_tab(self) -> None:
    self.log("Switched back to home tab.")
    ...
```

----------------------------------------

TITLE: Setting Grid Row Heights in Python
DESCRIPTION: Illustrates how to programmatically set the `grid-rows` style for a Textual grid widget using Python. It provides examples for applying uniform row heights and alternating row heights directly via the widget's style attribute.
SOURCE: https://github.com/textualize/textual/blob/main/docs/styles/grid/grid_rows.md#_snippet_1

LANGUAGE: python
CODE:
```
grid.styles.grid_rows = "50%"
grid.styles.grid_rows = "1fr 2fr"
```

----------------------------------------

TITLE: Adding Clickable Text Links in Textual
DESCRIPTION: This snippet demonstrates how to add clickable text links to a Textual widget. When the link is clicked, it triggers the specified action (app.bell in this case).
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/widgets.md#_snippet_6

LANGUAGE: python
CODE:
```
from textual.app import App, ComposeResult
from textual.widgets import Static

TEXT = """Click [@click=app.bell]Me[/] to make a bell sound.
Click [@click=update_text]here[/] to change this text.
"""

class HelloLinksApp(App):

    CSS_PATH = "hello05.tcss"

    def compose(self) -> ComposeResult:
        yield Static(TEXT)

    def action_bell(self) -> None:
        
```

----------------------------------------

TITLE: Setting Height in CSS (Basic Examples)
DESCRIPTION: Illustrates common ways to set the `height` property in Textual CSS, including explicit cell height, percentage-based height, and automatic height adjustment.
SOURCE: https://github.com/textualize/textual/blob/main/docs/styles/height.md#_snippet_1

LANGUAGE: CSS
CODE:
```
/* Explicit cell height */
height: 10;

/* Percentage height */
height: 50%;

/* Automatic height */
height: auto
```

----------------------------------------

TITLE: Running Pytest for Snapshot Testing
DESCRIPTION: This command executes pytest to run the snapshot tests. On the first run, it generates an SVG screenshot and fails, prompting the user to validate the initial snapshot. Subsequent runs compare the current output against the saved snapshot, passing if they match or failing if a visual regression is detected.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/testing.md#_snippet_11

LANGUAGE: shell
CODE:
```
pytest
```

----------------------------------------

TITLE: Using Widget Display Shortcut in Python
DESCRIPTION: Shows the simplified way to hide or show a Textual widget by directly setting its `display` property to `False` (hide) or `True` (show), providing a convenient shortcut for visibility control.
SOURCE: https://github.com/textualize/textual/blob/main/docs/styles/display.md#_snippet_3

LANGUAGE: python
CODE:
```
# Hide the widget
widget.display = False

# Show the widget
widget.display = True
```

----------------------------------------

TITLE: Using Percent Unit for Container-Relative Length in Textualize CSS
DESCRIPTION: This snippet shows how the '%' unit sets a widget's length as a percentage relative to the space provided by its immediate container. It can be applied to both width and height properties.
SOURCE: https://github.com/textualize/textual/blob/main/docs/css_types/scalar.md#_snippet_2

LANGUAGE: CSS
CODE:
```
width: 50%
```

LANGUAGE: CSS
CODE:
```
height: 50%
```

----------------------------------------

TITLE: CSS Rule for Success Class
DESCRIPTION: This CSS rule targets widgets with the class 'success' and sets their background to green and text color to white.  The dot (`.`) prefix indicates a class selector.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/CSS.md#_snippet_11

LANGUAGE: css
CODE:
```
.success {
  background: green;
  color: white;
}
```

----------------------------------------

TITLE: Rendering Markup via Content.from_markup (Python)
DESCRIPTION: Demonstrates explicitly returning a `Content` object created from markup using `Content.from_markup()`. This is functionally equivalent to returning a markup string directly but offers more control and flexibility for complex content generation.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/content.md#_snippet_24

LANGUAGE: Python
CODE:
```
class WelcomeWidget(Widget):
    def render(self) -> RenderResult:
        return Content.from_markup("[b]Hello, World![/b]")
```

----------------------------------------

TITLE: Applying Warning Style with CSS Variables (Textual Markup)
DESCRIPTION: Illustrates applying a warning style to text, setting both the foreground and background colors using CSS variables. `$warning` sets the text color, and `$warning-muted` sets the background color for emphasis.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/content.md#_snippet_16

LANGUAGE: Textual Markup
CODE:
```
[$warning on $warning-muted]This is a warning![/]
```

----------------------------------------

TITLE: Setting Reactive Attribute with set_reactive
DESCRIPTION: This example demonstrates how to use `set_reactive` to set a reactive attribute without immediately invoking the watcher. This is useful during initialization or when you want to avoid triggering updates prematurely. The `set_reactive` method accepts the reactive attribute (as a class variable) and the new value.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/reactivity.md#_snippet_20

LANGUAGE: python
CODE:
```
from textual.app import App, ComposeResult
from textual.widgets import Label
from textual.reactive import reactive

class Greeter(Label):

    DEFAULT_CSS = """
    Greeter {
        width: auto;
        height: auto;
        padding: 1 2;
        border: tall $primary;
    }
    """

    greeting: reactive[str] = reactive("Hello, World!")

    def watch_greeting(self, greeting: str) -> None:
        self.update(greeting)

    def on_mount(self) -> None:
        greeting = "Goodbye, World!"
        self.set_reactive(Greeter.greeting, greeting)

class ReactiveBugApp(App):

    CSS = """
    Screen {
        layout: vertical;
        align: center middle;
    }
    """

    def compose(self) -> ComposeResult:
        yield Greeter()

if __name__ == "__main__":
    app = ReactiveBugApp()
    app.run()
```

----------------------------------------

TITLE: Setting Text Alignment in Python
DESCRIPTION: This Python snippet shows how to programmatically set the `text_align` style property of any Textual widget to `justify` using its `styles` attribute. This achieves the same justified text effect as the CSS example but is applied directly in Python code.
SOURCE: https://github.com/textualize/textual/blob/main/docs/css_types/text_align.md#_snippet_1

LANGUAGE: python
CODE:
```
widget.styles.text_align = "justify"
```

----------------------------------------

TITLE: Applying Tint Style in Python with Textual
DESCRIPTION: These Python examples show how to programmatically set the `tint` style on a Textual widget. The first uses `textual.color.Color.with_alpha` for precise alpha control, and the second directly assigns an `rgba` string.
SOURCE: https://github.com/textualize/textual/blob/main/docs/styles/tint.md#_snippet_2

LANGUAGE: Python
CODE:
```
# A red tint
from textual.color import Color
widget.styles.tint = Color.parse("red").with_alpha(0.2);

# A green tint
widget.styles.tint = "rgba(0, 200, 0, 0.3)"
```

----------------------------------------

TITLE: Moving TextArea Cursor Location (Python)
DESCRIPTION: Shows how to programmatically update the cursor's position within a `TextArea` widget by assigning a new `(row_index, column_index)` tuple to the `cursor_location` property. The example demonstrates moving the cursor from the initial (0, 0) to (0, 4).
SOURCE: https://github.com/textualize/textual/blob/main/docs/widgets/text_area.md#_snippet_3

LANGUAGE: Python
CODE:
```
>>> text_area = TextArea()
>>> text_area.cursor_location
(0, 0)
>>> text_area.cursor_location = (0, 4)
>>> text_area.cursor_location
(0, 4)
```

----------------------------------------

TITLE: Applying Docking Styles in Textual Python
DESCRIPTION: This snippet shows how to programmatically set the `dock` style for a widget in Textual using Python. It illustrates assigning "bottom", "left", "right", or "top" to `widget.styles.dock` to dynamically fix the widget's position relative to its parent container.
SOURCE: https://github.com/textualize/textual/blob/main/docs/styles/dock.md#_snippet_2

LANGUAGE: python
CODE:
```
widget.styles.dock = "bottom"  # Dock bottom.
widget.styles.dock = "left"    # Dock   left.
widget.styles.dock = "right"   # Dock  right.
widget.styles.dock = "top"     # Dock    top.
```

----------------------------------------

TITLE: Setting Minimum Width in CSS
DESCRIPTION: This snippet demonstrates how to apply the `min-width` style in CSS. It shows examples of setting a fixed minimum width (e.g., 10 rows) and a percentage-based minimum width relative to the viewport (e.g., 25vw).
SOURCE: https://github.com/textualize/textual/blob/main/docs/styles/min_width.md#_snippet_0

LANGUAGE: CSS
CODE:
```
/* Set the minimum width to 10 rows */
min-width: 10;

/* Set the minimum width to 25% of the viewport width */
min-width: 25vw;
```

----------------------------------------

TITLE: CSS Rules Example
DESCRIPTION: This example demonstrates CSS rules within a rule set. Each rule consists of a name and a value, separated by a colon and ending with a semicolon. These rules define the style properties of the selected widget.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/CSS.md#_snippet_2

LANGUAGE: css
CODE:
```
Header {
  dock: top;
  height: 3;
  content-align: center middle;
  background: blue;
  color: white;
}
```

----------------------------------------

TITLE: Styling Content Programmatically (Python)
DESCRIPTION: Demonstrates how to programmatically apply styles to a `Content` object using the `stylize()` method. This example creates content and then applies a 'bold' style to the substring from index 7 to 12 ('World'), returning a new immutable Content instance.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/content.md#_snippet_27

LANGUAGE: Python
CODE:
```
content = Content("Hello, World!")
content = content.stylize(7, 12, "bold")
```

----------------------------------------

TITLE: Applying Backgrounds with Opacity in Textual CSS
DESCRIPTION: Demonstrates setting background colors with varying opacity levels for widgets using Textual's CSS. This example creates multiple widgets to visually illustrate the effect of different percentage-based opacity settings applied via CSS rules.
SOURCE: https://github.com/textualize/textual/blob/main/docs/styles/background.md#_snippet_4

LANGUAGE: css
CODE:
```
--8<-- "docs/examples/styles/background_transparency.tcss"
```

----------------------------------------

TITLE: Launching Textual Calculator from the command line
DESCRIPTION: This command shows how to launch the Textual calculator application from the command line after it has been installed.
SOURCE: https://github.com/textualize/textual/blob/main/docs/how-to/package-with-hatch.md#_snippet_1

LANGUAGE: bash
CODE:
```
calculator
```

----------------------------------------

TITLE: Setting Widget Opacity to 50% in CSS
DESCRIPTION: Demonstrates how to set the `opacity` of a widget to 50% using a CSS rule. This makes the widget appear semi-transparent by blending it with its parent's background color.
SOURCE: https://github.com/textualize/textual/blob/main/docs/styles/opacity.md#_snippet_1

LANGUAGE: css
CODE:
```
/* Fade the widget to 50% against its parent's background */
opacity: 50%;
```

----------------------------------------

TITLE: Setting Screen Background Color to Lime (Python)
DESCRIPTION: This line of code demonstrates setting the background style of the current screen to the pre-defined color 'lime'. This is a direct assignment to the `styles.background` attribute.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/styles.md#_snippet_2

LANGUAGE: python
CODE:
```
self.screen.styles.background = "lime"
```

----------------------------------------

TITLE: Example of an Opening Markup Tag
DESCRIPTION: This snippet illustrates the syntax of an opening content markup tag in Textual. An opening tag, like `[bold]`, initiates a style change that applies to the subsequent text until a corresponding closing tag is encountered.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/content.md#_snippet_2

LANGUAGE: Textual Markup
CODE:
```
[bold]
```

----------------------------------------

TITLE: Mounting a Widget Synchronously in Textual Python
DESCRIPTION: This snippet demonstrates calling Textual's `mount` method without explicitly awaiting its result. This approach is suitable when the immediate completion of the mounting operation is not critical, as Textual ensures the widget is mounted before the next message handler executes. It adds an instance of `MyWidget` to the screen.
SOURCE: https://github.com/textualize/textual/blob/main/docs/blog/posts/await-me-maybe.md#_snippet_1

LANGUAGE: Python
CODE:
```
def on_key(self):
    # Add MyWidget to the screen
    self.mount(MyWidget("Hello, World!"))
```

----------------------------------------

TITLE: Setting Initial State of Collapsible Widget - Python
DESCRIPTION: Demonstrates how to control the initial expanded or collapsed state of a Textual Collapsible widget using the `collapsed` boolean parameter. `collapsed=False` makes it expanded initially, while `collapsed=True` (the default) keeps it collapsed.
SOURCE: https://github.com/textualize/textual/blob/main/docs/widgets/collapsible.md#_snippet_3

LANGUAGE: python
CODE:
```
def compose(self) -> ComposeResult:
    with Collapsible(title="Contents 1", collapsed=False):
        yield Label("Hello, world.")

    with Collapsible(title="Contents 2", collapsed=True):  # Default.
        yield Label("Hello, world.")
```

----------------------------------------

TITLE: Overriding Container Visibility in Textual (Python & CSS)
DESCRIPTION: This comprehensive example showcases the interaction of the `visibility` style with parent-child relationships in Textual. It illustrates how child widgets can explicitly override an invisible parent container's `visibility` setting to remain visible.
SOURCE: https://github.com/textualize/textual/blob/main/docs/styles/visibility.md#_snippet_2

LANGUAGE: python
CODE:
```
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Placeholder
from textual.containers import Horizontal

class VisibilityContainersApp(App[None]):
    CSS_PATH = "visibility_containers.tcss"

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="top-container"):
            yield Placeholder("Top 1")
            yield Placeholder("Top 2")
            yield Placeholder("Top 3")

        with Horizontal(id="middle-container"):
            yield Placeholder("Middle 1")
            yield Placeholder("Middle 2")
            yield Placeholder("Middle 3")

        with Horizontal(id="bottom-container"):
            yield Placeholder("Bottom 1", id="bottom-child-1")
            yield Placeholder("Bottom 2", id="bottom-child-2")
            yield Placeholder("Bottom 3", id="bottom-child-3")
        yield Footer()

if __name__ == "__main__":
    app = VisibilityContainersApp()
    app.run()
```

LANGUAGE: css
CODE:
```
Horizontal {
    border: solid white;
    padding: 1;
    height: auto;
    margin-bottom: 1;
}
#middle-container {
    visibility: hidden;
}
#bottom-container {
    visibility: hidden;
}
#bottom-child-1, #bottom-child-2, #bottom-child-3 {
    visibility: visible;
}
Placeholder {
    width: 1fr;
    height: 5;
    border: solid blue;
    text-align: center;
    vertical-align: middle;
}
```

----------------------------------------

TITLE: Applying Text Styles in CSS
DESCRIPTION: This snippet demonstrates how to apply text styles using CSS. It shows examples of applying a single style like 'strike' and combining multiple styles such as 'strike', 'bold', 'italic', and 'reverse' to elements identified by their IDs.
SOURCE: https://github.com/textualize/textual/blob/main/docs/css_types/text_style.md#_snippet_0

LANGUAGE: css
CODE:
```
#label1 {
    /* You can specify any value by itself. */
    rule: strike;
}

#label2 {
    /* You can also combine multiple values. */
    rule: strike bold italic reverse;
}
```

----------------------------------------

TITLE: Simulating Click with Widget-Relative Offset with Textual Pilot (Python)
DESCRIPTION: This example demonstrates how to simulate a click relative to a specific widget by combining a CSS selector (or widget class like `Button`) with an `offset`. The offset is added to the widget's coordinates, allowing clicks outside its direct bounds.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/testing.md#_snippet_5

LANGUAGE: python
CODE:
```
await pilot.click(Button, offset=(0, -1))
```

----------------------------------------

TITLE: Setting Outline Styles Programmatically in Textual (Python)
DESCRIPTION: This Python code shows how to programmatically control the outline properties of a Textual widget. It sets a heavy white outline for the entire widget and then specifically applies an outer red outline to its left side.
SOURCE: https://github.com/textualize/textual/blob/main/docs/styles/outline.md#_snippet_2

LANGUAGE: Python
CODE:
```
# Set a heavy white outline
widget.outline = ("heavy", "white")

# Set a red outline on the left
widget.outline_left = ("outer", "red")
```

----------------------------------------

TITLE: Installing Textual Core and Dev Tools (Shell)
DESCRIPTION: This command demonstrates how to install both the core Textual library and its dedicated developer tools package. This new approach separates the `textual` core from `textual-dev` to optimize dependencies and avoid installation issues.
SOURCE: https://github.com/textualize/textual/blob/main/docs/blog/posts/release0-29-0.md#_snippet_0

LANGUAGE: Shell
CODE:
```
pip install textual textual-dev
```

----------------------------------------

TITLE: Applying link-color in Textual Python Application
DESCRIPTION: This Python example demonstrates how `link-color` affects Textual action links while showing that it does not apply to standard hyperlinks. It sets up a Textual app with various labels, some with action links and others with regular hyperlinks, to illustrate the styling difference.
SOURCE: https://github.com/textualize/textual/blob/main/docs/styles/links/link_color.md#_snippet_1

LANGUAGE: python
CODE:
```
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Label
from textual.containers import Container

class LinkColorApp(App):
    CSS_PATH = "link_color.tcss"

    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Label("This label has a [link=https://textual.textualize.io]regular hyperlink[/]."),
            Label("This label has an [b link=app.action_one]action link one[/]."),
            Label("This label has an [b link=app.action_two]action link two[/]."),
            Label("This label has an [b link=app.action_three]action link three[/]."),
        )
        yield Footer()

    def action_one(self) -> None:
        self.notify("Action one triggered!")

    def action_two(self) -> None:
        self.notify("Action two triggered!")

    def action_three(self) -> None:
        self.notify("Action three triggered!")

if __name__ == "__main__":
    app = LinkColorApp()
    app.run()
```

----------------------------------------

TITLE: Setting `align` Style - Python
DESCRIPTION: Shows how to programmatically set the `align` style for a widget's children in Python, using tuples to specify horizontal and vertical alignment values.
SOURCE: https://github.com/textualize/textual/blob/main/docs/styles/align.md#_snippet_3

LANGUAGE: python
CODE:
```
# Align child widgets to the center
widget.styles.align = ("center", "middle")
# Align child widgets to the top right
widget.styles.align = ("right", "top")
```

----------------------------------------

TITLE: Triggering Actions on Click (Textual Markup)
DESCRIPTION: Demonstrates how to associate an action with clickable text in Textual. The `@click=` attribute specifies the action (`app.bell`) to be executed when the marked text is clicked, in this case, playing the terminal bell sound.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/content.md#_snippet_18

LANGUAGE: Textual Markup
CODE:
```
Play the [@click=app.bell]bell[/]
```

----------------------------------------

TITLE: Using Height Unit for Container Height-Relative Length in Textualize CSS
DESCRIPTION: This snippet illustrates the 'h' unit, which sets a widget's length as a percentage relative to the container's *height*, irrespective of whether the property is 'width' or 'height'. This ensures scaling based on the container's vertical dimension.
SOURCE: https://github.com/textualize/textual/blob/main/docs/css_types/scalar.md#_snippet_4

LANGUAGE: CSS
CODE:
```
height: 75h
```

LANGUAGE: CSS
CODE:
```
width: 75h
```

----------------------------------------

TITLE: Styling Header Widget with CSS
DESCRIPTION: This CSS rule set styles a Textual Header widget. It docks the header to the top of the screen, sets its height to 3, aligns content to the center, and applies a blue background with white text.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/CSS.md#_snippet_0

LANGUAGE: css
CODE:
```
Header {
  dock: top;
  height: 3;
  content-align: center middle;
  background: blue;
  color: white;
}
```

----------------------------------------

TITLE: Using HorizontalScroll Container in Textual
DESCRIPTION: Replaces a custom ColumnsContainer with the built-in HorizontalScroll container to manage columns with a horizontal scrollbar. This simplifies the layout and avoids the need for custom CSS styling.
SOURCE: https://github.com/textualize/textual/blob/main/docs/how-to/design-a-layout.md#_snippet_3

LANGUAGE: python
CODE:
```
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, HorizontalScroll, Placeholder


class ColumnsContainer(HorizontalScroll):
    pass


class ColumnsApp(App):
    CSS_PATH = "columns.tcss"
    BINDINGS = [("d", "toggle_dark", "Toggle dark mode")]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        yield ColumnsContainer(Placeholder(), Placeholder(), Placeholder())


if __name__ == "__main__":
    app = ColumnsApp()
    app.run()
```

----------------------------------------

TITLE: Setting max-height Programmatically in Textual Python
DESCRIPTION: Illustrates how to programmatically set the `max_height` style for a Textual widget using its `styles` attribute in Python. This allows dynamic control over a widget's maximum height, accepting both integer row counts and viewport-relative string values.
SOURCE: https://github.com/textualize/textual/blob/main/docs/styles/max_height.md#_snippet_2

LANGUAGE: python
CODE:
```
# Set the maximum height to 10 rows
widget.styles.max_height = 10

# Set the maximum height to 25% of the viewport height
widget.styles.max_height = "25vh"
```

----------------------------------------

TITLE: Textual Message Handler Without Event Object (Python)
DESCRIPTION: This handler demonstrates that the event object parameter can be omitted from the method signature if the handler's logic does not require access to the event's data. This simplifies the method signature when only a side effect, like playing a bell sound, is needed.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/events.md#_snippet_6

LANGUAGE: python
CODE:
```
    def on_color_button_selected(self) -> None:
        self.app.bell()
```

----------------------------------------

TITLE: Setting min-height in CSS
DESCRIPTION: Demonstrates how to set the `min-height` CSS property using both absolute row units (e.g., `10`) and relative viewport height units (e.g., `25vh`). This directly applies the minimum height constraint in a Textual CSS (TCSS) file.
SOURCE: https://github.com/textualize/textual/blob/main/docs/styles/min_height.md#_snippet_1

LANGUAGE: css
CODE:
```
/* Set the minimum height to 10 rows */
min-height: 10;

/* Set the minimum height to 25% of the viewport height */
min-height: 25vh;
```

----------------------------------------

TITLE: Serving a Textual Demo App Locally (Shell)
DESCRIPTION: This command demonstrates how to serve the default Textual demo application locally. It uses the `textual serve` command to execute a Python module, making the Textual app accessible through a web browser on the local machine.
SOURCE: https://github.com/textualize/textual/blob/main/README.md#_snippet_4

LANGUAGE: Shell
CODE:
```
textual serve "python -m textual"
```

----------------------------------------

TITLE: Applying Basic Visibility in Textual (Python & CSS)
DESCRIPTION: This example demonstrates how to hide a specific widget within a Textual application using the `visibility: hidden` CSS property. It highlights that even when hidden, the widget still occupies its allocated space in the layout.
SOURCE: https://github.com/textualize/textual/blob/main/docs/styles/visibility.md#_snippet_1

LANGUAGE: python
CODE:
```
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Placeholder
from textual.containers import Container

class VisibilityApp(App[None]):
    CSS_PATH = "visibility.tcss"

    def compose(self) -> ComposeResult:
        yield Header()
        with Container():
            yield Placeholder("Visible Widget 1")
            yield Placeholder("Hidden Widget 2", id="hidden-widget")
            yield Placeholder("Visible Widget 3")
        yield Footer()

if __name__ == "__main__":
    app = VisibilityApp()
    app.run()
```

LANGUAGE: css
CODE:
```
Container {
    layout: horizontal;
    border: solid green;
    height: auto;
    padding: 1;
    margin: 1;
}
Placeholder {
    width: 1fr;
    height: 5;
    border: solid blue;
    text-align: center;
    vertical-align: middle;
}
#hidden-widget {
    visibility: hidden;
}
```

----------------------------------------

TITLE: Setting Position in Textual CSS
DESCRIPTION: Demonstrates how to set the `position` style property in Textual CSS using both `relative` and `absolute` values. These values dictate whether the widget's offset is applied from its normal flow position or from the container's top-left origin.
SOURCE: https://github.com/textualize/textual/blob/main/docs/styles/position.md#_snippet_1

LANGUAGE: css
CODE:
```
position: relative;
position: absolute;
```

----------------------------------------

TITLE: Installing Textual App with Pipx
DESCRIPTION: This command installs a Textual application using Pipx, which creates an isolated virtual environment to prevent dependency conflicts with other Python packages. It installs the specified application and its dependencies within this environment.
SOURCE: https://github.com/textualize/textual/blob/main/docs/how-to/package-with-hatch.md#_snippet_19

LANGUAGE: bash
CODE:
```
pipx install textual_calculator
```

----------------------------------------

TITLE: Creating a Dynamic Row Grid Layout in Textual Python
DESCRIPTION: This Python snippet illustrates how to create a Textual grid layout that dynamically adds new rows as needed. By omitting the number of rows from `grid-size`, the grid will expand vertically to accommodate additional widgets beyond the initial column count.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/layout.md#_snippet_8

LANGUAGE: python
CODE:
```
--8<-- "docs/examples/guide/layout/grid_layout2.py"
```

----------------------------------------

TITLE: Embedding Textual Actions in Markup Links (Python)
DESCRIPTION: This snippet illustrates how to embed Textual actions directly within markup using the `@click` tag. Clicking on the generated links will execute the specified `set_background` action with different color parameters, demonstrating how actions can be triggered from UI elements.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/actions.md#_snippet_2

LANGUAGE: python
CODE:
```
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static

class ActionsApp(App):
    def action_set_background(self, color: str) -> None:
        self.screen.styles.background = color

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        yield Static(
            """
            Click a link to change background:
            @click=set_background('red')Red@/click
            @click=set_background('green')Green@/click
            @click=set_background('blue')Blue@/click
            """
        )

if __name__ == "__main__":
    ActionsApp().run()
```

----------------------------------------

TITLE: Installing Textual with Syntax Highlighting via PyPI
DESCRIPTION: Installs Textual along with optional dependencies for syntax highlighting in the TextArea widget. This is achieved by specifying the 'syntax' extras during pip installation.
SOURCE: https://github.com/textualize/textual/blob/main/docs/getting_started.md#_snippet_2

LANGUAGE: Bash
CODE:
```
pip install "textual[syntax]"
```

----------------------------------------

TITLE: Simulating Screen Click at Origin with Textual Pilot (Python)
DESCRIPTION: This example shows how to simulate a mouse click at the screen's top-left corner (0,0) using the `pilot.click()` method without any arguments. This is useful for testing general screen interactions.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/testing.md#_snippet_3

LANGUAGE: python
CODE:
```
await pilot.click()
```

----------------------------------------

TITLE: Composing Collapsible Widget with Constructor - Python
DESCRIPTION: Demonstrates how to add content to a Textual Collapsible widget by passing child widgets directly to its constructor. This method is suitable for simple content additions.
SOURCE: https://github.com/textualize/textual/blob/main/docs/widgets/collapsible.md#_snippet_0

LANGUAGE: python
CODE:
```
def compose(self) -> ComposeResult:
    yield Collapsible(Label("Hello, world."))
```

----------------------------------------

TITLE: Simulating Click with Modifier Keys with Textual Pilot (Python)
DESCRIPTION: This example demonstrates how to simulate a mouse click while holding down modifier keys (Shift, Meta, or Control) by setting the respective boolean parameters (`shift`, `meta`, `control`) in the `pilot.click` method. This allows testing complex key-mouse combinations.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/testing.md#_snippet_7

LANGUAGE: python
CODE:
```
await pilot.click("#slider", control=True)
```

----------------------------------------

TITLE: Obtaining Java Language Object with py-tree-sitter-languages (Python)
DESCRIPTION: This snippet demonstrates how to obtain a `Language` object for Java using the `get_language` function from the `tree_sitter_languages` package. This object is a prerequisite for enabling syntax highlighting and other language-specific features within Textual's `TextArea` widget. The `get_language` function takes the language name as a string argument.
SOURCE: https://github.com/textualize/textual/blob/main/docs/widgets/text_area.md#_snippet_17

LANGUAGE: python
CODE:
```
from tree_sitter_languages import get_language
java_language = get_language("java")
```

----------------------------------------

TITLE: Applying Offset Styles in CSS
DESCRIPTION: Demonstrates how to apply `offset`, `offset-x`, and `offset-y` CSS properties to move a widget. `offset: 8 2;` moves the widget 8 units horizontally and 2 units vertically. `offset-x: 4;` moves it 4 units horizontally, and `offset-y: -3;` moves it 3 units negatively along the y-axis.
SOURCE: https://github.com/textualize/textual/blob/main/docs/styles/offset.md#_snippet_1

LANGUAGE: CSS
CODE:
```
/* Move the widget 8 cells in the x direction and 2 in the y direction */
offset: 8 2;

/* Move the widget 4 cells in the x direction
offset-x: 4;
/* Move the widget -3 cells in the y direction
offset-y: -3;
```

----------------------------------------

TITLE: Creating Non-Refreshing Reactive Attributes
DESCRIPTION: This code illustrates how to create non-refreshing reactive attributes using `var`. Changing the value of `self.count` will not cause a refresh or layout.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/reactivity.md#_snippet_5

LANGUAGE: Python
CODE:
```
from textual.reactive import var
from textual.widget import Widget

class MyWidget(Widget):
    count = var(0)  # (1)!
```

----------------------------------------

TITLE: Controlling Widget Display via Styles in Python
DESCRIPTION: Illustrates how to programmatically control a Textual widget's display status using its `styles.display` attribute, setting it to 'none' to hide or 'block' to show, affecting its rendering and layout space.
SOURCE: https://github.com/textualize/textual/blob/main/docs/styles/display.md#_snippet_2

LANGUAGE: python
CODE:
```
# Hide the widget
self.styles.display = "none"

# Show the widget again
self.styles.display = "block"
```

----------------------------------------

TITLE: Setting Widget Dimensions Programmatically in Textual Python
DESCRIPTION: This Python snippet illustrates how to set a widget's `width` to a fixed cell unit (an integer) and its `height` to a proportional fractional unit (`'1fr'`) directly via its `styles` attribute. This allows for dynamic control over widget sizing.
SOURCE: https://github.com/textualize/textual/blob/main/docs/css_types/scalar.md#_snippet_8

LANGUAGE: python
CODE:
```
widget.styles.width = 16       # Cell unit can be specified with an int/float
widget.styles.height = "1fr"   # proportional size of 1
```

----------------------------------------

TITLE: Styling Toast Widget Padding (SCSS)
DESCRIPTION: This snippet demonstrates how to customize the padding of the `Toast` widget using a CSS type selector. It sets a uniform padding of 3 units around the toast notification.
SOURCE: https://github.com/textualize/textual/blob/main/docs/widgets/toast.md#_snippet_0

LANGUAGE: scss
CODE:
```
Toast {
    padding: 3;
}
```

----------------------------------------

TITLE: Textual Application Demonstrating link-style-hover (Python)
DESCRIPTION: A Textual Python application that creates various labels, some with regular hyperlinks and others with Textual action links, to demonstrate how `link-style-hover` only affects action links. It highlights the creation of different link types and includes placeholder actions for the Textual links.
SOURCE: https://github.com/textualize/textual/blob/main/docs/styles/links/link_style_hover.md#_snippet_1

LANGUAGE: Python
CODE:
```
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Label
from textual.containers import Vertical

class LinkStyleHoverApp(App[None]):
    CSS_PATH = "link_style_hover.tcss"

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical():
            # 1. This label has a hyperlink so it won't be affected by the `link-style-hover` rule.
            yield Label("Visit [link=https://textual.textualize.io]Textualize[/link]")
            # 2. This label has an "action link" that can be styled with `link-style-hover`.
            yield Label("Click [link=app://action_one]Action One[/link]")
            # 3. This label has an "action link" that can be styled with `link-style-hover`.
            yield Label("Click [link=app://action_two]Action Two[/link]")
            # 4. This label has an "action link" that can be styled with `link-style-hover`.
            yield Label("Click [link=app://action_three]Action Three[/link]")
        yield Footer()

    def action_action_one(self) -> None:
        self.bell()

    def action_action_two(self) -> None:
        self.bell()

    def action_action_three(self) -> None:
        self.bell()

if __name__ == "__main__":
    app = LinkStyleHoverApp()
    app.run()
```

----------------------------------------

TITLE: Textual Python Application Demonstrating Link Hover Color
DESCRIPTION: This Python snippet illustrates how `link-color-hover` affects Textual action links, but not standard hyperlinks. It sets up multiple labels with different link types to showcase the style's selective application, defining actions for the Textual links.
SOURCE: https://github.com/textualize/textual/blob/main/docs/styles/links/link_color_hover.md#_snippet_1

LANGUAGE: python
CODE:
```
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Label
from textual.color import Color

class LinkColorHoverApp(App):
    CSS_PATH = "link_color_hover.tcss"

    def compose(self) -> ComposeResult:
        yield Header()
        yield Label("This is a [link=https://textual.textualize.io]regular hyperlink[/link].")
        yield Label("This is an [b link=app.action_one]action link one[/b].")
        yield Label("This is an [b link=app.action_two]action link two[/b].")
        yield Label("This is an [b link=app.action_three]action link three[/b].")
        yield Footer()

    def action_one(self) -> None:
        self.notify("Action one triggered!")

    def action_two(self) -> None:
        self.notify("Action two triggered!")

    def action_three(self) -> None:
        self.notify("Action three triggered!")

if __name__ == "__main__":
    app = LinkColorHoverApp()
    app.run()
```

----------------------------------------

TITLE: Styling Utility Containers in Textual CSS
DESCRIPTION: This CSS snippet provides styling for the utility containers example, specifically highlighting line 2. It defines the visual appearance of the `Horizontal` and `Vertical` containers used for layout.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/layout.md#_snippet_2

LANGUAGE: css
CODE:
```
--8<-- "docs/examples/guide/layout/utility_containers.tcss"
```

----------------------------------------

TITLE: Applying Backgrounds with Opacity in Textual Python
DESCRIPTION: Shows how to set background colors with varying opacity levels for widgets using Textual's Python API. This example creates multiple widgets to visually demonstrate the effect of different percentage-based opacity settings.
SOURCE: https://github.com/textualize/textual/blob/main/docs/styles/background.md#_snippet_3

LANGUAGE: python
CODE:
```
--8<-- "docs/examples/styles/background_transparency.py"
```

----------------------------------------

TITLE: Setting Text Alignment in Textual Python
DESCRIPTION: Shows how to programmatically set the `text-align` style of a Textual widget to `right` using its `styles` attribute. This method allows dynamic style changes from Python code.
SOURCE: https://github.com/textualize/textual/blob/main/docs/styles/text_align.md#_snippet_3

LANGUAGE: python
CODE:
```
# Set text in the widget to be right aligned
widget.styles.text_align = "right"
```

----------------------------------------

TITLE: Creating an Indeterminate Progress Bar with Rich's `Progress` class (Python)
DESCRIPTION: This snippet illustrates how to create an indeterminate progress bar using Rich's `Progress` class. By setting `total=None` when adding a task, the progress bar displays an ongoing animation without a defined end, suitable for tasks with unknown durations. The `while True` loop keeps the progress bar active indefinitely.
SOURCE: https://github.com/textualize/textual/blob/main/docs/blog/posts/spinners-and-pbs-in-textual.md#_snippet_1

LANGUAGE: Python
CODE:
```
import time
from rich.progress import Progress

with Progress() as progress:
    _ = progress.add_task("Loading...", total=None)  # (1)!
    while True:
        time.sleep(0.01)
```

----------------------------------------

TITLE: Changing TextArea Theme Dynamically (Python)
DESCRIPTION: This snippet demonstrates how to dynamically change the theme of an existing `TextArea` instance. By assigning a new theme name (e.g., 'vscode_dark') to the `theme` attribute, the `TextArea` immediately updates its appearance to reflect the new theme.
SOURCE: https://github.com/textualize/textual/blob/main/docs/widgets/text_area.md#_snippet_8

LANGUAGE: python
CODE:
```
text_area.theme = "vscode_dark"
```

----------------------------------------

TITLE: Styling Buttons in a Sidebar
DESCRIPTION: This CSS rule underlines the text of buttons that are direct children of a widget with the ID 'sidebar'. It uses the child combinator (>) to target immediate children.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/CSS.md#_snippet_18

LANGUAGE: css
CODE:
```
#sidebar > Button {
  text-style: underline;
}
```

----------------------------------------

TITLE: Applying Multiple Rules to a CSS Class
DESCRIPTION: This CSS snippet demonstrates how to define multiple style rules within a single class selector. Each 'rule' is assigned a specific 'type-value', illustrating the basic syntax for applying styles to elements matching '.some-class'.
SOURCE: https://github.com/textualize/textual/blob/main/docs/css_types/_template.md#_snippet_0

LANGUAGE: css
CODE:
```
.some-class {
    rule: type-value-1;
    rule: type-value-2;
    rule: type-value-3;
}
```

----------------------------------------

TITLE: Applying max-height in Textual CSS
DESCRIPTION: Demonstrates how to set the `max-height` property in Textual CSS using both absolute row counts and viewport-relative units. This allows controlling a widget's maximum vertical size based on fixed values or a percentage of the terminal's height.
SOURCE: https://github.com/textualize/textual/blob/main/docs/styles/max_height.md#_snippet_1

LANGUAGE: css
CODE:
```
/* Set the maximum height to 10 rows */
max-height: 10;

/* Set the maximum height to 25% of the viewport height */
max-height: 25vh;
```

----------------------------------------

TITLE: Align Style Syntax - CSS
DESCRIPTION: Defines the syntax for the `align`, `align-horizontal`, and `align-vertical` CSS properties, specifying the types of values they accept for horizontal and vertical alignment.
SOURCE: https://github.com/textualize/textual/blob/main/docs/styles/align.md#_snippet_0

LANGUAGE: css
CODE:
```
align: <a href="../../css_types/horizontal">&lt;horizontal&gt;</a> <a href="../../css_types/vertical">&lt;vertical&gt;</a>;

align-horizontal: <a href="../../css_types/horizontal">&lt;horizontal&gt;</a>;
align-vertical: <a href="../../css_types/vertical">&lt;vertical&gt;</a>;
```

----------------------------------------

TITLE: Defining Grid Gutter Syntax in Textual CSS
DESCRIPTION: This snippet illustrates the syntax for the `grid-gutter` CSS property in Textual. It accepts one or two integer values, where a single value sets both vertical and horizontal gutters, and two values set vertical and horizontal gutters respectively.
SOURCE: https://github.com/textualize/textual/blob/main/docs/styles/grid/grid_gutter.md#_snippet_0

LANGUAGE: CSS
CODE:
```
grid-gutter: <integer> [<integer>];
```

----------------------------------------

TITLE: Setting Button Background to Green
DESCRIPTION: This CSS rule sets the background color of all Button widgets to green. It applies to all buttons in the application unless overridden by more specific rules.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/CSS.md#_snippet_23

LANGUAGE: css
CODE:
```
Button {
  background: green;
}
```

----------------------------------------

TITLE: Running Textual App from Python File
DESCRIPTION: Executes a Textual application by providing the path to its Python source file. This command is equivalent to `python my_app.py` but allows for additional Textual-specific switches like `--dev` for debugging.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/devtools.md#_snippet_1

LANGUAGE: bash
CODE:
```
textual run my_app.py
```

----------------------------------------

TITLE: CSS Overflow Property Syntax
DESCRIPTION: This snippet illustrates the syntax for the `overflow` CSS property, which can accept one or two values for horizontal and vertical scrollbar control, respectively. It also shows the syntax for `overflow-x` and `overflow-y` for individual axis control.
SOURCE: https://github.com/textualize/textual/blob/main/docs/styles/overflow.md#_snippet_0

LANGUAGE: css
CODE:
```
overflow: <a href="../../css_types/overflow">&lt;overflow&gt;</a> <a href="../../css_types/overflow">&lt;overflow&gt;</a>;

overflow-x: <a href="../../css_types/overflow">&lt;overflow&gt;</a>;
overflow-y: <a href="../../css_types/overflow">&lt;overflow&gt;</a>;
```

----------------------------------------

TITLE: Setting Grid Gutter in Textual Python Styles
DESCRIPTION: This Python snippet shows how to programmatically set the vertical and horizontal grid gutters for a Textual widget's styles. Unlike the CSS shorthand, these properties must be set individually for each axis using `grid_gutter_vertical` and `grid_gutter_horizontal`.
SOURCE: https://github.com/textualize/textual/blob/main/docs/styles/grid/grid_gutter.md#_snippet_2

LANGUAGE: Python
CODE:
```
widget.styles.grid_gutter_vertical = "1"
widget.styles.grid_gutter_horizontal = "2"
```

----------------------------------------

TITLE: Problematic Markup Variable Substitution with F-strings - Textual Python
DESCRIPTION: This snippet illustrates a common but flawed method of embedding dynamic content into Textual markup using Python's f-strings. While seemingly straightforward, this approach is prone to errors if the variable's value contains square brackets, which Textual might incorrectly interpret as markup tags, leading to unintended styling or display issues. It is generally advised against for robust applications.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/content.md#_snippet_28

LANGUAGE: python
CODE:
```
class WelcomeWidget(Widget):
    def render(self) -> RenderResult:
        name = "Will"
        return f"Hello [bold]{name}[/bold]!"
```

----------------------------------------

TITLE: Styling a Widget's Base Class
DESCRIPTION: This CSS code styles all `Static` widgets with a blue background and a round green border. Because `Alert` extends `Static`, this style will also apply to `Alert` widgets unless overridden by a more specific selector.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/CSS.md#_snippet_6

LANGUAGE: css
CODE:
```
Static {
  background: blue;
  border: round green;
}
```

----------------------------------------

TITLE: Defining Textual Layout Syntax
DESCRIPTION: This snippet illustrates the general syntax for defining the `layout` style in Textual's CSS-like styling. It shows the accepted values: `grid`, `horizontal`, or `vertical`, which determine how child widgets are arranged within their parent.
SOURCE: https://github.com/textualize/textual/blob/main/docs/styles/layout.md#_snippet_0

LANGUAGE: Textual CSS
CODE:
```
layout: grid | horizontal | vertical;
```

----------------------------------------

TITLE: Programmatically Setting Overflow in Python
DESCRIPTION: This Python snippet illustrates how to programmatically set the `overflow-x` and `overflow-y` properties for a widget's styles. It demonstrates hiding the vertical scrollbar and always showing the horizontal scrollbar using direct attribute assignment.
SOURCE: https://github.com/textualize/textual/blob/main/docs/styles/overflow.md#_snippet_2

LANGUAGE: python
CODE:
```
# Hide the vertical scrollbar
widget.styles.overflow_y = "hidden"

# Always show the horizontal scrollbar
widget.styles.overflow_x = "scroll"
```

----------------------------------------

TITLE: Adding Basic TextArea to Textual App (Python)
DESCRIPTION: This snippet demonstrates the simplest way to integrate a `TextArea` widget into a Textual application. By yielding `TextArea()` within the `compose` method, developers can add a basic multi-line text editing component to their terminal UI.
SOURCE: https://github.com/textualize/textual/blob/main/docs/blog/posts/text-area-learnings.md#_snippet_0

LANGUAGE: python
CODE:
```
yield TextArea()
```

----------------------------------------

TITLE: Setting Ellipsis Text-overflow in Textual Python
DESCRIPTION: This Python snippet, specifically for the Textual framework, shows how to programmatically set the `text-overflow` style for a `widget` instance to `ellipsis`. This provides a dynamic way to control text overflow behavior directly within Python code, mirroring the CSS functionality.
SOURCE: https://github.com/textualize/textual/blob/main/docs/styles/text_overflow.md#_snippet_2

LANGUAGE: Python
CODE:
```
widget.styles.text_overflow = "ellipsis"
```

----------------------------------------

TITLE: Styling Hovered Buttons with !important
DESCRIPTION: This CSS rule sets the background color of buttons to blue when hovered over, using the `!important` flag to override any other conflicting styles. The `!important` flag ensures that this rule always takes precedence.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/CSS.md#_snippet_19

LANGUAGE: css
CODE:
```
Button:hover {
  background: blue !important;
}
```

----------------------------------------

TITLE: Installing Textual Developer Tools via Conda-Forge
DESCRIPTION: Installs Textual developer tools using micromamba from the conda-forge channel. This complements the core Textual installation for development purposes within a conda environment.
SOURCE: https://github.com/textualize/textual/blob/main/docs/getting_started.md#_snippet_4

LANGUAGE: Bash
CODE:
```
micromamba install -c conda-forge textual-dev
```

----------------------------------------

TITLE: Button with Tooltip
DESCRIPTION: This example demonstrates how to add a tooltip to a button widget. The tooltip is set using the widget's tooltip property, which can accept text or any Rich renderable.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/widgets.md#_snippet_16

LANGUAGE: python
CODE:
```
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Button


class TooltipApp(App):
    
```

----------------------------------------

TITLE: Changing Command Palette Key Binding in Textual App (Python)
DESCRIPTION: This example illustrates how to customize the key binding used to open the command palette in a Textual application. By assigning a new key combination string to the `COMMAND_PALETTE_BINDING` class variable on your `App` class, you can override the default binding.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/command_palette.md#_snippet_1

LANGUAGE: Python
CODE:
```
class NewPaletteBindingApp(App):
    COMMAND_PALETTE_BINDING = "ctrl+backslash"
```

----------------------------------------

TITLE: Selecting Text in TextArea (Python)
DESCRIPTION: This snippet demonstrates how to programmatically select a range of text within a `TextArea` widget. It sets the `selection` attribute to a `Selection` object, specifying the start and end coordinates (row, column) to select the first two lines of text.
SOURCE: https://github.com/textualize/textual/blob/main/docs/widgets/text_area.md#_snippet_4

LANGUAGE: python
CODE:
```
text_area.selection = Selection(start=(0, 0), end=(2, 0))
```

----------------------------------------

TITLE: Setting Minimum Width in Python Styles
DESCRIPTION: This snippet illustrates how to programmatically set the `min-width` style for a widget using Textual's Python API. It provides examples for setting a fixed minimum width and a viewport-relative percentage minimum width.
SOURCE: https://github.com/textualize/textual/blob/main/docs/styles/min_width.md#_snippet_1

LANGUAGE: Python
CODE:
```
# Set the minimum width to 10 rows
widget.styles.min_width = 10

# Set the minimum width to 25% of the viewport width
widget.styles.min_width = "25vw"
```

----------------------------------------

TITLE: Removing Column Below Cursor in Textual DataTable (Python)
DESCRIPTION: This snippet illustrates how to remove a specific column from a Textual DataTable based on the current cursor position. It utilizes `coordinate_to_cell_key` to extract the `column_key` from the `cursor_coordinate` and then supplies this key to the `remove_column` method. This operation requires an instance of a `DataTable` widget.
SOURCE: https://github.com/textualize/textual/blob/main/docs/widgets/data_table.md#_snippet_1

LANGUAGE: python
CODE:
```
# Get the keys for the row and column under the cursor.
_, column_key = table.coordinate_to_cell_key(table.cursor_coordinate)
# Supply the column key to `column_row` to delete the column.
table.remove_column(column_key)
```

----------------------------------------

TITLE: Combining Bold and Italic Styles in Textual Markup
DESCRIPTION: This snippet demonstrates how to nest and combine multiple styles using Textual content markup. The outer `[bold]` tags apply bold formatting, and the inner `[italic]` tags further apply italic formatting to the enclosed text, resulting in 'Bold and italic' being both bold and italic.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/content.md#_snippet_5

LANGUAGE: Textual Markup
CODE:
```
[bold]Bold [italic]Bold and italic[/italic][/bold]
```

----------------------------------------

TITLE: Handling Resize Events for 'Size' Variant in Textual Python
DESCRIPTION: This Textual event handler is triggered whenever the widget is resized. If the current `variant` of the placeholder is 'size', it calls `_update_size_variant` to refresh the displayed size information, ensuring the placeholder's content remains accurate during layout changes.
SOURCE: https://github.com/textualize/textual/blob/main/docs/blog/posts/placeholder-pr.md#_snippet_7

LANGUAGE: Python
CODE:
```
class Placeholder(Static):
    # ...
    def on_resize(self, event: events.Resize) -> None:
        """Update the placeholder "size" variant with the new placeholder size."""
        if self.variant == "size":
            self._update_size_variant()
```

----------------------------------------

TITLE: Setting Text Alignment in CSS
DESCRIPTION: This CSS snippet demonstrates how to set the `text-align` property for a `Label` widget to `justify`, causing its text content to be justified within the widget's bounds. This is applied directly within a Textual CSS file.
SOURCE: https://github.com/textualize/textual/blob/main/docs/css_types/text_align.md#_snippet_0

LANGUAGE: css
CODE:
```
Label {
    text-align: justify;
}
```

----------------------------------------

TITLE: Applying Borders in Textual Python
DESCRIPTION: Illustrates how to programmatically set borders on Textual widgets using Python. It shows how to apply a border to all edges and to a specific edge using a tuple of style and color.
SOURCE: https://github.com/textualize/textual/blob/main/docs/styles/border.md#_snippet_3

LANGUAGE: python
CODE:
```
# Set a heavy white border
widget.styles.border = ("heavy", "white")

# Set a red border on the left
widget.styles.border_left = ("outer", "red")
```

----------------------------------------

TITLE: Setting Initial Active Tab in TabbedContent - Python
DESCRIPTION: This snippet shows how to specify the initial active tab when a TabbedContent widget is created. By default, the first child tab is active. The `initial` argument in the TabbedContent constructor can be set to the `id` of a specific TabPane to make it the initially displayed tab upon widget creation.
SOURCE: https://github.com/textualize/textual/blob/main/docs/widgets/tabbed_content.md#_snippet_4

LANGUAGE: python
CODE:
```
def compose(self) -> ComposeResult:
    with TabbedContent(initial="jessica"):
        with TabPane("Leto", id="leto"):
            yield Markdown(LETO)
        with TabPane("Jessica", id="jessica"):
            yield Markdown(JESSICA)
        with TabPane("Paul", id="paul"):
            yield Markdown(PAUL)
```

----------------------------------------

TITLE: Common CSS Width Declarations
DESCRIPTION: Provides concise examples of how to set the `width` property in Textual CSS using different value types: an explicit number of columns, a percentage of the parent's width, and `auto` for content-based sizing.
SOURCE: https://github.com/textualize/textual/blob/main/docs/styles/width.md#_snippet_5

LANGUAGE: css
CODE:
```
/* Explicit cell width */
width: 10;

/* Percentage width */
width: 50%;

/* Automatic width */
width: auto;
```

----------------------------------------

TITLE: Scanning Line Breaks with Memory Mapping - Python
DESCRIPTION: This Python method efficiently scans a large file for newline characters (\n) using the `mmap` module, which memory-maps the file for fast, OS-level access without loading the entire file into RAM. It uses `rfind` for reverse searching and yields line break offsets in batches to prevent UI blocking, making it suitable for processing very large log files.
SOURCE: https://github.com/textualize/textual/blob/main/docs/blog/posts/toolong-retrospective.md#_snippet_1

LANGUAGE: Python
CODE:
```
    def scan_line_breaks(
        self, batch_time: float = 0.25
    ) -> Iterable[tuple[int, list[int]]]:
        """Scan the file for line breaks.

        Args:
            batch_time: Time to group the batches.

        Returns:
            An iterable of tuples, containing the scan position and a list of offsets of new lines.
        """
        fileno = self.fileno
        size = self.size
        if not size:
            return
        log_mmap = mmap.mmap(fileno, size, prot=mmap.PROT_READ)
        rfind = log_mmap.rfind
        position = size
        batch: list[int] = []
        append = batch.append
        get_length = batch.__len__
        monotonic = time.monotonic
        break_time = monotonic()

        while (position := rfind(b"\n", 0, position)) != -1:
            append(position)
            if get_length() % 1000 == 0 and monotonic() - break_time > batch_time:
                break_time = monotonic()
                yield (position, batch)
                batch = []
                append = batch.append
        yield (0, batch)
        log_mmap.close()
```

----------------------------------------

TITLE: Resetting Button Background to Initial Value
DESCRIPTION: This CSS rule resets the background color of buttons within a widget with the class 'dialog' to their initial (default) value. It uses the `initial` keyword to revert to the default styling.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/CSS.md#_snippet_24

LANGUAGE: css
CODE:
```
.dialog Button {
  background: initial;
}
```

----------------------------------------

TITLE: Creating TextArea with a Built-in Theme (Python)
DESCRIPTION: This snippet demonstrates how to initialize a `TextArea` widget as a code editor with a specific built-in theme. It uses `TextArea.code_editor` to create the instance, setting the initial content, language for syntax highlighting, and applying the 'dracula' theme.
SOURCE: https://github.com/textualize/textual/blob/main/docs/widgets/text_area.md#_snippet_6

LANGUAGE: python
CODE:
```
# Create a TextArea with the 'dracula' theme.
yield TextArea.code_editor("print(123)", language="python", theme="dracula")
```

----------------------------------------

TITLE: Building Project with Hatch
DESCRIPTION: These bash commands navigate to the project directory and build the project using Hatch. The `hatch build` command creates a `dist` folder containing the project archive files.
SOURCE: https://github.com/textualize/textual/blob/main/docs/how-to/package-with-hatch.md#_snippet_16

LANGUAGE: bash
CODE:
```
cd textual-calculator
hatch build
```

----------------------------------------

TITLE: Programmatically Setting Widget Offset in Python
DESCRIPTION: Illustrates how to programmatically set the `offset` style for a Textual widget using Python. The `widget.styles.offset` property is assigned a tuple `(x, y)` to define the horizontal and vertical displacement simultaneously, as single-axis offsets cannot be set independently via Python.
SOURCE: https://github.com/textualize/textual/blob/main/docs/styles/offset.md#_snippet_2

LANGUAGE: Python
CODE:
```
# Move the widget 2 cells in the x direction, and 4 in the y direction.
widget.styles.offset = (2, 4)
```

----------------------------------------

TITLE: Setting link-style via Textual Python Styles
DESCRIPTION: These Python snippets show how to programmatically set the `link-style` for a Textual widget. The first line sets the link text to bold, and the second applies bold, italic, and reversed styling, directly manipulating the widget's style properties.
SOURCE: https://github.com/textualize/textual/blob/main/docs/styles/links/link_style.md#_snippet_1

LANGUAGE: python
CODE:
```
widget.styles.link_style = "bold"
widget.styles.link_style = "bold italic reverse"
```

----------------------------------------

TITLE: Applying Percentage Values in CSS
DESCRIPTION: This CSS snippet demonstrates how to use percentage values for properties like 'color' and 'offset'. It shows examples of an integer percentage for color and negative/decimal percentages for offset, highlighting the flexibility of the <percentage> type.
SOURCE: https://github.com/textualize/textual/blob/main/docs/css_types/percentage.md#_snippet_0

LANGUAGE: css
CODE:
```
#footer {
    /* Integer followed by % */
    color: red 70%;

    /* The number can be negative/decimal, although that may not make sense */
    offset: -30% 12.5%;
}
```

----------------------------------------

TITLE: Styling a Dynamic Row Grid Layout in Textual CSS
DESCRIPTION: This CSS snippet configures a Textual grid layout to have a fixed number of columns (3) while allowing rows to be created on demand. This is achieved by setting `grid-size` to only specify the column count, enabling the grid to expand vertically as more widgets are added.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/layout.md#_snippet_9

LANGUAGE: css
CODE:
```
--8<-- "docs/examples/guide/layout/grid_layout2.tcss"
```

----------------------------------------

TITLE: Setting Horizontal Layout in Textual CSS
DESCRIPTION: This CSS snippet demonstrates how to apply a horizontal layout to a widget using Textual's styling. When applied, it arranges child widgets along the horizontal axis, from left to right, within the parent container.
SOURCE: https://github.com/textualize/textual/blob/main/docs/styles/layout.md#_snippet_1

LANGUAGE: CSS
CODE:
```
layout: horizontal;
```

----------------------------------------

TITLE: Setting Horizontal Layout in Textual Python
DESCRIPTION: This Python snippet shows how to programmatically set a widget's layout to 'horizontal' using Textual's `styles` attribute. This dynamically arranges the widget's children from left to right, offering runtime control over widget arrangement.
SOURCE: https://github.com/textualize/textual/blob/main/docs/styles/layout.md#_snippet_2

LANGUAGE: Python
CODE:
```
widget.styles.layout = "horizontal"
```

----------------------------------------

TITLE: Emitting Custom Messages for Widget State Changes in Textual Python
DESCRIPTION: This Python snippet shows how an Activity widget defines and emits a custom Moved message when its position changes. This decouples the Activity from the Main screen, allowing the screen to react to the change without the child widget knowing about the screen's saving capabilities. It uses emit_no_wait (with a warning about its deprecation).
SOURCE: https://github.com/textualize/textual/blob/main/docs/blog/posts/on-dog-food-the-original-metaverse-and-not-being-bored.md#_snippet_2

LANGUAGE: Python
CODE:
```
    class Moved( Message ):
        """A message to indicate that an activity has moved."""

    def action_move_up( self ) -> None:
        """Move this activity up one place in the list."""
        if self.parent is not None and not self.is_first:
            parent = cast( Widget, self.parent )
            parent.move_child(
                self, before=parent.children.index( self ) - 1
            )
            self.emit_no_wait( self.Moved( self ) )
            self.scroll_visible( top=True )
```

----------------------------------------

TITLE: Checkerboard Widget with Line API in Textual
DESCRIPTION: This code implements a Textual widget that renders a checkerboard pattern using the line API. The render_line method calculates a Strip for each row, containing alternating black and white space characters. It demonstrates the use of Segment and Style objects to customize the appearance of the checkerboard squares.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/widgets.md#_snippet_19

LANGUAGE: Python
CODE:
```
from textual.app import App, ComposeResult
from textual.widget import Widget
from textual.reactive import reactive
from textual.strip import Strip
from rich.style import Style
from rich.segment import Segment

class Checkerboard(Widget):

    DEFAULT_CSS = """
    Checkerboard {
        width: auto;
        height: auto;
    }
    """

    size = reactive(10)

    def render_line(self, y: int) -> Strip:
        
```

----------------------------------------

TITLE: Applying Accent Color with CSS Variable (Textual Markup)
DESCRIPTION: Demonstrates how to apply a theme's accent color to text using a CSS variable in Textual markup. The `$accent` variable references the predefined accent color, making the enclosed text appear in that color.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/content.md#_snippet_15

LANGUAGE: Textual Markup
CODE:
```
[$accent]Accent color[/]
```

----------------------------------------

TITLE: Filtering Query Results by Type (Python)
DESCRIPTION: This code snippet illustrates using the `results` method on a `DOMQuery` object to filter the returned widgets by a specific type. It first queries for all widgets with the CSS class `disabled` and then uses `.results(Button)` to yield only `Button` instances from that set, which is beneficial for type-checkers.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/queries.md#_snippet_7

LANGUAGE: Python
CODE:
```
for button in self.query(".disabled").results(Button):
    print(button)
```

----------------------------------------

TITLE: Configuring Textual Border Titles and Subtitles (Python)
DESCRIPTION: This Python snippet demonstrates how to configure border titles and subtitles for Textual widgets, showcasing various alignment options, markup usage, and truncation behavior. It highlights that (sub)titles can contain nested Rich markup and links, are truncated when long, and are not displayed if empty or if the widget lacks a border. An auxiliary function is also mentioned for creating labels with specific border properties.
SOURCE: https://github.com/textualize/textual/blob/main/docs/snippets/border_sub_title_align_all_example.md#_snippet_0

LANGUAGE: Python
CODE:
```
--8<-- "docs/examples/styles/border_sub_title_align_all.py"
```

----------------------------------------

TITLE: Installing Pytest Textual Snapshot Plugin (Shell)
DESCRIPTION: This command demonstrates how to install the `pytest-textual-snapshot` plugin using `pip`. This plugin is essential for performing visual snapshot testing of Textual applications, helping to catch unintended UI changes.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/testing.md#_snippet_9

LANGUAGE: shell
CODE:
```
pip install pytest-textual-snapshot
```

----------------------------------------

TITLE: Setting Horizontal Alignment for Widget in Python
DESCRIPTION: This Python snippet shows how to programmatically set the horizontal alignment of a widget to 'right' using its `styles.align_horizontal` attribute. This is typically used in UI frameworks to control widget positioning dynamically.
SOURCE: https://github.com/textualize/textual/blob/main/docs/css_types/horizontal.md#_snippet_1

LANGUAGE: python
CODE:
```
widget.styles.align_horizontal = "right"
```

----------------------------------------

TITLE: Setting Borders Programmatically in Textual Python
DESCRIPTION: This Python snippet illustrates how to programmatically set border styles and colors for Textual widgets using their `styles` attribute. It applies a `heavy` red border to a widget and a `solid` blue bottom border.
SOURCE: https://github.com/textualize/textual/blob/main/docs/css_types/border.md#_snippet_2

LANGUAGE: Python
CODE:
```
widget.styles.border = ("heavy", "red")
widget.styles.border_bottom = ("solid", "blue")
```

----------------------------------------

TITLE: CSS for Static Widget in Textual
DESCRIPTION: This CSS styles the `Hello` widget, setting its width, height, padding, border, background color, text color, and content alignment.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/widgets.md#_snippet_4

LANGUAGE: CSS
CODE:
```
Hello {
    width: auto;
    height: auto;
    padding: 1 2;
    border: tall $primary;
    background: $panel;
    color: $text;
    content-align: center middle;
}
```

----------------------------------------

TITLE: Applying Colors with Hex and RGB in Textual Markup
DESCRIPTION: Illustrates how to apply colors to text using standard HTML hex color codes (`[#RRGGBB]`) and RGB function notation (`[rgba(R,G,B)]`) within Textual markup. The `[/]` tag closes the color application.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/content.md#_snippet_8

LANGUAGE: Textual Markup
CODE:
```
[#ff0000]HTML hex style[/]
[rgba(0,255,0)]HTML RGB style[/]
```

----------------------------------------

TITLE: Setting Link Hover Color in Textual Python Styles
DESCRIPTION: These Python examples show how to programmatically set the `link-color-hover` style on a widget using string values for color and opacity, or directly with a `Color` object. This allows dynamic styling of link hover effects.
SOURCE: https://github.com/textualize/textual/blob/main/docs/styles/links/link_color_hover.md#_snippet_4

LANGUAGE: python
CODE:
```
widget.styles.link_color_hover = "red 70%"
widget.styles.link_color_hover = "black"

# You can also use a `Color` object directly:
widget.styles.link_color_hover = Color(100, 30, 173)
```

----------------------------------------

TITLE: Setting Border Titles and Subtitles on Textual Widgets
DESCRIPTION: This snippet demonstrates how to set the border title and subtitle of a Textual widget. The title is set as a class variable, while the subtitle is set as an instance attribute.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/widgets.md#_snippet_8

LANGUAGE: python
CODE:
```
from textual.app import App, ComposeResult
from textual.widgets import Static

class HelloBorderApp(App):

    CSS_PATH = "hello06.tcss"

    class Hello(Static):
        
```

----------------------------------------

TITLE: Applying 'below' Layer in Textual CSS
DESCRIPTION: This CSS snippet demonstrates how to assign a widget to the 'below' layer using the `layer` style. Widgets on higher layers are drawn on top of widgets on lower layers, affecting visual stacking.
SOURCE: https://github.com/textualize/textual/blob/main/docs/styles/layer.md#_snippet_1

LANGUAGE: CSS
CODE:
```
/* Draw the widget on the layer called 'below' */
layer: below;
```

----------------------------------------

TITLE: Styling Toast Severity Levels (SCSS)
DESCRIPTION: These snippets illustrate how to apply specific styles to `Toast` widgets based on their severity levels (`-information`, `-warning`, `-error`) using CSS class selectors. This allows for distinct visual cues for different types of notifications.
SOURCE: https://github.com/textualize/textual/blob/main/docs/widgets/toast.md#_snippet_2

LANGUAGE: scss
CODE:
```
Toast.-information {
    /* Styling here. */
}

Toast.-warning {
    /* Styling here. */
}

Toast.-error {
    /* Styling here. */
}
```

----------------------------------------

TITLE: Applying Integer Offset in CSS
DESCRIPTION: This CSS snippet demonstrates how to use integer values for the `offset` property within a CSS rule. It shows two integer values, `10` and `-20`, applied to define an offset for an element with the class `classname`.
SOURCE: https://github.com/textualize/textual/blob/main/docs/css_types/integer.md#_snippet_0

LANGUAGE: css
CODE:
```
.classname {
    offset: 10 -20
}
```

----------------------------------------

TITLE: Creating a Determinate Progress Bar with Rich's `track` function (Python)
DESCRIPTION: This snippet demonstrates how to create a determinate progress bar using Rich's `track` function. It simulates a task with a known number of steps (20 in this case) and updates the progress bar as each step is completed. The `time.sleep` call simulates work being done.
SOURCE: https://github.com/textualize/textual/blob/main/docs/blog/posts/spinners-and-pbs-in-textual.md#_snippet_0

LANGUAGE: Python
CODE:
```
import time
from rich.progress import track

for _ in track(range(20), description="Processing..."):
    time.sleep(0.5)  # Simulate work being done
```

----------------------------------------

TITLE: Applying Percentage Values to Widget Styles in Python
DESCRIPTION: This Python snippet illustrates how percentage values, similar to CSS, can be applied to widget styles. It shows setting 'color' with an integer percentage and 'offset' with negative and decimal percentages, demonstrating the programmatic application of these values.
SOURCE: https://github.com/textualize/textual/blob/main/docs/css_types/percentage.md#_snippet_1

LANGUAGE: python
CODE:
```
# Integer followed by %
widget.styles.color = "red 70%"

# The number can be negative/decimal, although that may not make sense
widget.styles.offset = ("-30%", "12.5%")
```

----------------------------------------

TITLE: Running Textual App as CLI Command
DESCRIPTION: Runs a Textual application that is installed as a command-line script using the `-c` switch. This is useful for executing Textual apps that are part of a larger CLI tool, such as `textual colors`.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/devtools.md#_snippet_5

LANGUAGE: bash
CODE:
```
textual run -c textual colors
```

----------------------------------------

TITLE: Setting Box-sizing in Python (Textual)
DESCRIPTION: This Python snippet illustrates how to programmatically control the `box_sizing` attribute of a widget within the Textual framework. It provides examples for setting the widget's box model to both `border-box` (default) and `content-box` via Python code.
SOURCE: https://github.com/textualize/textual/blob/main/docs/styles/box_sizing.md#_snippet_2

LANGUAGE: python
CODE:
```
# Set box sizing to border-box (default)
widget.box_sizing = "border-box"

# Set box sizing to content-box
widget.box_sizing = "content-box"
```

----------------------------------------

TITLE: Using Cell Unit for Absolute Length in Textualize CSS
DESCRIPTION: This snippet demonstrates how to use an integer or float (truncated) to specify an absolute length in cells. When applied horizontally, it corresponds to columns; vertically, it corresponds to lines, setting a fixed dimension for the widget.
SOURCE: https://github.com/textualize/textual/blob/main/docs/css_types/scalar.md#_snippet_0

LANGUAGE: CSS
CODE:
```
width: 15
```

LANGUAGE: CSS
CODE:
```
height: 10
```

----------------------------------------

TITLE: Implementing Scrolling in a Textual Widget (checker03.py)
DESCRIPTION: This example demonstrates how to add scrolling functionality to a Textual widget by extending the ScrollView class. It configures the virtual size of the scrollable content and updates the render_line method to account for scroll offsets.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/widgets.md#_snippet_23

LANGUAGE: python
CODE:
```
class Checkerboard(ScrollView):

    def __init__(self, board_size: int = 100) -> None:
        self.board_size = board_size
        super().__init__()

    def compose(self) -> ComposeResult:
        yield Static(f"{self.board_size=}", id="board_size")

    def on_mount(self) -> None:
        self.virtual_size = Size(self.board_size, self.board_size)

    def render_line(self, y: int) -> Strip:
        width = self.size.width
        board_size = self.board_size
        scroll_x, scroll_y = self.scroll_offset
        white = Style(bgcolor=Color.parse("white"))
        black = Style(bgcolor=Color.parse("black"))
        line = []
        for x in range(width):
            if (x + y + scroll_x + scroll_y) % 2 == 0:
                line.append((white, " "))
            else:
                line.append((black, " "))
        strip = Strip(line)
        return strip.crop(scroll_x, scroll_x + self.size.width)


class CheckerboardApp(App):
    CSS_PATH = "checker03.tcss"

    def compose(self) -> ComposeResult:
        yield Checkerboard(board_size=100)
```

----------------------------------------

TITLE: Initializing Hatch Project
DESCRIPTION: Initializes a Hatch project in the current directory for existing code. Replace `<YOUR PROJECT NAME>` with the actual project name.
SOURCE: https://github.com/textualize/textual/blob/main/docs/how-to/package-with-hatch.md#_snippet_4

LANGUAGE: Bash
CODE:
```
hatch new --init <YOUR PROJECT NAME>
```

----------------------------------------

TITLE: Simple Tree Control Example - Python
DESCRIPTION: This snippet demonstrates a basic implementation of Textual's new scalable Tree control, showcasing its simplified API for managing hierarchical data. It references an external Python file containing the actual example code.
SOURCE: https://github.com/textualize/textual/blob/main/docs/blog/posts/release0-6-0.md#_snippet_0

LANGUAGE: python
CODE:
```
--8<-- "docs/examples/widgets/tree.py"
```

----------------------------------------

TITLE: Setting link-color in Textual Python Styles
DESCRIPTION: Demonstrates how to programmatically set the `link-color` style for a Textual widget using Python. It shows setting the color with a string (including opacity and CSS variables) and directly with a `Color` object.
SOURCE: https://github.com/textualize/textual/blob/main/docs/styles/links/link_color.md#_snippet_4

LANGUAGE: python
CODE:
```
widget.styles.link_color = "red 70%"
widget.styles.link_color = "$accent"

# You can also use a `Color` object directly:
widget.styles.link_color = Color(100, 30, 173)
```

----------------------------------------

TITLE: Setting Outline Styles in Textual CSS
DESCRIPTION: These CSS rules demonstrate how to apply outlines to Textual widgets. The first rule sets a heavy white outline globally, while the second specifically applies an outer red outline to the left edge of a widget.
SOURCE: https://github.com/textualize/textual/blob/main/docs/styles/outline.md#_snippet_1

LANGUAGE: CSS
CODE:
```
/* Set a heavy white outline */
outline:heavy white;

/* set a red outline on the left */
outline-left:outer red;
```

----------------------------------------

TITLE: Styling Text Links in Textual
DESCRIPTION: This CSS snippet styles the appearance of text links within a Textual widget, specifically targeting the 'underline' pseudo-class to remove the default underline.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/widgets.md#_snippet_7

LANGUAGE: css
CODE:
```
Static a:link {
  text-style: none;
}

Static a:visited {
  text-style: none;
}

Static a:hover {
  text-style: none;
}

Static a:active {
  text-style: none;
}

Static a:focus {
  outline: none;
  text-style: none;
}

Static a:link:underline {
  text-style: underline;
}

Static a:visited:underline {
  text-style: underline;
}

Static a:hover:underline {
  text-style: underline;
}

Static a:active:underline {
  text-style: underline;
}

Static a:focus:underline {
  text-style: underline;
}
```

----------------------------------------

TITLE: Setting Scrollbar Background Color in Textual Python
DESCRIPTION: This Python snippet shows how to programmatically set the `scrollbar-background` style for a Textual widget. It accesses the `styles` attribute of a `widget` object and assigns the string 'blue' to its `scrollbar_background` property, effectively changing the scrollbar's background color dynamically.
SOURCE: https://github.com/textualize/textual/blob/main/docs/styles/scrollbar_colors/scrollbar_background.md#_snippet_1

LANGUAGE: Python
CODE:
```
widget.styles.scrollbar_background = "blue"
```

----------------------------------------

TITLE: Setting Vertical Alignment in Python (Textual)
DESCRIPTION: This Python snippet shows how to programmatically set the vertical alignment of a widget's style using Textual's `styles` attribute. It sets the `align_vertical` property to 'top', mirroring the CSS functionality for dynamic styling within Textual applications.
SOURCE: https://github.com/textualize/textual/blob/main/docs/css_types/vertical.md#_snippet_1

LANGUAGE: python
CODE:
```
widget.styles.align_vertical = "top"
```

----------------------------------------

TITLE: Initializing Tabs with String Labels (Python)
DESCRIPTION: This snippet demonstrates how to construct a `Tabs` widget by providing string or `Text` objects as positional arguments. This method automatically creates `Tab` widgets with auto-incrementing IDs. It's suitable for simple tab setups where explicit ID control is not required.
SOURCE: https://github.com/textualize/textual/blob/main/docs/widgets/tabs.md#_snippet_0

LANGUAGE: python
CODE:
```
def compose(self) -> ComposeResult:
    yield Tabs("First tab", "Second tab", Text.from_markup("[u]Third[/u] tab"))
```

----------------------------------------

TITLE: Watching Reactive Variant Changes in Textual Python
DESCRIPTION: This method is a Textual watcher for the `variant` reactive attribute. It's automatically called when the `variant` changes, validating the new variant, updating CSS classes, and then delegating the actual content update to `call_variant_update`.
SOURCE: https://github.com/textualize/textual/blob/main/docs/blog/posts/placeholder-pr.md#_snippet_3

LANGUAGE: Python
CODE:
```
class Placeholder(Static):
    # ...
    variant = reactive("default")
    # ...
    def watch_variant(
        self, old_variant: PlaceholderVariant, variant: PlaceholderVariant
    ) -> None:
        self.validate_variant(variant)
        self.remove_class(f"-{old_variant}")
        self.add_class(f"-{variant}")
        self.call_variant_update()  # <-- let this method do the heavy lifting!
```

----------------------------------------

TITLE: Setting link-background Style Programmatically in Python
DESCRIPTION: This snippet illustrates how to programmatically set the `link-background` style for a Textual widget using Python. It provides examples of assigning a color string with opacity, using a CSS variable string, and directly assigning a `Color` object to control the background of action links.
SOURCE: https://github.com/textualize/textual/blob/main/docs/styles/links/link_background.md#_snippet_1

LANGUAGE: python
CODE:
```
widget.styles.link_background = "red 70%"
widget.styles.link_background = "$accent"

# You can also use a `Color` object directly:
widget.styles.link_background = Color(100, 30, 173)
```

----------------------------------------

TITLE: Applying link-style in Textual CSS
DESCRIPTION: These CSS examples demonstrate how to apply different text styles using the `link-style` property. The first line sets the link text to bold, while the second applies bold, italic, and reversed styling, affecting only Textual action links.
SOURCE: https://github.com/textualize/textual/blob/main/docs/styles/links/link_style.md#_snippet_0

LANGUAGE: css
CODE:
```
link-style: bold;
link-style: bold italic reverse;
```

----------------------------------------

TITLE: Setting Italic Text Style in Python (Textual)
DESCRIPTION: This Python snippet shows how to programmatically set the text style of a Textual widget to italic. By accessing the `styles` attribute of a widget and assigning a string value to `text_style`, developers can dynamically control the text's appearance. This method is useful for applying styles at runtime or based on application logic.
SOURCE: https://github.com/textualize/textual/blob/main/docs/styles/text_style.md#_snippet_1

LANGUAGE: python
CODE:
```
widget.styles.text_style = "italic"
```

----------------------------------------

TITLE: BitSwitch: Sending Custom Messages on Switch Change (byte02.py)
DESCRIPTION: This code snippet demonstrates how to extend the `ByteEditor` widget so that clicking any of the 8 `BitSwitch` widgets updates the decimal value. It adds a custom message to `BitSwitch` that is caught in the `ByteEditor`. The `BitSwitch` widget now has an `on_switch_changed` method which will handle a `Switch.Changed` message, sent when the user clicks a switch. This is used to store the new value of the bit, and sent a new custom message, `BitSwitch.BitChanged`.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/widgets.md#_snippet_29

LANGUAGE: python
CODE:
```
class BitSwitch(Widget):
    
```

----------------------------------------

TITLE: Applying Background Tint on Focus (CSS)
DESCRIPTION: Demonstrates how to apply a subtle white tint to a widget's background when it gains focus, using a 10% blend. This is typically used for visual emphasis, making the focused element slightly lighter.
SOURCE: https://github.com/textualize/textual/blob/main/docs/styles/background_tint.md#_snippet_0

LANGUAGE: css
CODE:
```
MyWidget:focus {
    background-tint: white 10%
}
```

----------------------------------------

TITLE: Setting Fixed Column Width and Tweet Height
DESCRIPTION: Sets a fixed width for the columns and a fixed height for the tweet placeholders. This demonstrates how to control the size of elements within the layout for a more structured appearance.
SOURCE: https://github.com/textualize/textual/blob/main/docs/how-to/design-a-layout.md#_snippet_5

LANGUAGE: python
CODE:
```
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, HorizontalScroll, Placeholder, VerticalScroll


class Column(VerticalScroll):
    DEFAULT_CSS = """Column {width: 32;}"""


class Tweet(Placeholder):
    DEFAULT_CSS = """Tweet {height: 5;}"""


class ColumnsApp(App):
    CSS_PATH = "columns.tcss"
    BINDINGS = [("d", "toggle_dark", "Toggle dark mode")]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        with HorizontalScroll():
            with Column():
                for n in range(4):
                    yield Tweet(f"Tweet {n+1}")
            with Column():
                for n in range(2):
                    yield Tweet(f"Tweet {n+1}")
            with Column():
                for n in range(5):
                    yield Tweet(f"Tweet {n+1}")
            with Column():
                for n in range(3):
                    yield Tweet(f"Tweet {n+1}")


if __name__ == "__main__":
    app = ColumnsApp()
    app.run()
```

----------------------------------------

TITLE: Defining Component Classes for Styling in Textual (checker02.py)
DESCRIPTION: This example demonstrates how to define component classes within a Textual widget to enable styling via CSS. It defines a checkerboard widget with white and black squares, assigning component classes to each for customizable styling.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/widgets.md#_snippet_22

LANGUAGE: python
CODE:
```
class Checkerboard(Widget):

    COMPONENT_CLASSES = {
        "checkerboard--white-square",
        "checkerboard--black-square",
    }

    DEFAULT_CSS = """
    Checkerboard {
        height: 100%;
        width: 100%;
    }
    .checkerboard--white-square {
        background: white;
    }

    .checkerboard--black-square {
        background: black;
    }
    """

    def render_line(self, y: int) -> Strip:
        width = self.size.width
        white = self.get_component_rich_style("checkerboard--white-square")
        black = self.get_component_rich_style("checkerboard--black-square")
        line = []
        for x in range(width):
            if (x + y) % 2 == 0:
                line.append((white, " "))
            else:
                line.append((black, " "))
        return Strip(line)


class CheckerboardApp(App):
    def compose(self) -> ComposeResult:
        yield Checkerboard()
```

----------------------------------------

TITLE: Constructing Content With Markup Processing (Python)
DESCRIPTION: Shows how to create a `Content` object that processes markup using the `Content.from_markup()` alternative constructor. This allows applying styles like bold to parts of the string, similar to direct markup strings.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/content.md#_snippet_26

LANGUAGE: Python
CODE:
```
Content.from_markup("hello, [bold]World[/bold]!")
```

----------------------------------------

TITLE: Tint Style Syntax in CSS
DESCRIPTION: This snippet defines the CSS syntax for the `tint` property. It accepts a `<color>` value and an optional `<percentage>` to control the alpha component, which is crucial for blending without obscuring content.
SOURCE: https://github.com/textualize/textual/blob/main/docs/styles/tint.md#_snippet_0

LANGUAGE: CSS
CODE:
```
tint: <color> [<percentage>];
```

----------------------------------------

TITLE: Applying Hatch Styles with CSS
DESCRIPTION: Demonstrates various `hatch` CSS properties to apply textured backgrounds to Textual widgets. It shows how to use predefined hatch types like 'cross' and 'right', as well as custom characters, along with color and optional opacity.
SOURCE: https://github.com/textualize/textual/blob/main/docs/styles/hatch.md#_snippet_0

LANGUAGE: css
CODE:
```
/* Red cross hatch */
hatch: cross red;
/* Right diagonals, 50% transparent green. */
hatch: right green 50%;
/* T custom character in 80% blue. **/
hatch: "T" blue 80%;
```

----------------------------------------

TITLE: Applying a Registered TextArea Theme in Python
DESCRIPTION: This snippet shows how to apply a registered theme to a TextArea instance by setting its theme attribute to the desired theme's name. This action immediately updates the visual appearance of the TextArea.
SOURCE: https://github.com/textualize/textual/blob/main/docs/widgets/text_area.md#_snippet_13

LANGUAGE: python
CODE:
```
text_area.theme = "my_cool_theme"
```

----------------------------------------

TITLE: Direct Python Background Style Examples
DESCRIPTION: Illustrates different ways to set the `background` style in Textual using Python, including string-based color names, HSL strings, and direct `Color` object manipulation. It shows how to parse colors from strings or instantiate them directly for finer control.
SOURCE: https://github.com/textualize/textual/blob/main/docs/styles/background.md#_snippet_6

LANGUAGE: python
CODE:
```
# Set blue background
widget.styles.background = "blue"
# Set through HSL model
widget.styles.background = "hsl(351,32%,89%)"

from textual.color import Color
# Set with a color object by parsing a string
widget.styles.background = Color.parse("pink")
widget.styles.background = Color.parse("#FF00FF")
# Set with a color object instantiated directly
widget.styles.background = Color(120, 60, 100)
```

----------------------------------------

TITLE: Setting `align-horizontal` and `align-vertical` Styles - Python
DESCRIPTION: Demonstrates how to individually control the horizontal and vertical alignment of a widget's children in Python using `styles.align_horizontal` and `styles.align_vertical`.
SOURCE: https://github.com/textualize/textual/blob/main/docs/styles/align.md#_snippet_4

LANGUAGE: python
CODE:
```
# Change the horizontal alignment of the children of a widget
widget.styles.align_horizontal = "right"
# Change the vertical alignment of the children of a widget
widget.styles.align_vertical = "middle"
```

----------------------------------------

TITLE: Applying Row and Column Span in Textual Grid Layout (Python/CSS)
DESCRIPTION: This example extends the cell spanning concept by demonstrating how to make a grid cell span both multiple rows and columns. It targets the same widget with ID `#two` and applies `row-span: 2;` in addition to `column-span: 2;` in the TUI CSS, causing the widget to occupy four grid cells.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/layout.md#_snippet_11

LANGUAGE: python
CODE:
```
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static
from textual.containers import Container

class GridApp(App):
    CSS_PATH = "grid_layout6_row_span.tcss"

    def compose(self) -> ComposeResult:
        yield Header()
        with Container():
            yield Static("One")
            yield Static("Two", id="two")
            yield Static("Three")
            yield Static("Four")
            yield Static("Five")
            yield Static("Six")
        yield Footer()

if __name__ == "__main__":
    app = GridApp()
    app.run()
```

LANGUAGE: css
CODE:
```
Screen {
    layout: grid;
    grid-size: 3 2;
}

#two {
    column-span: 2;
    row-span: 2;
    tint: magenta 40%;
}
```

----------------------------------------

TITLE: Example Text Alignment in Textual Python
DESCRIPTION: Demonstrates various text alignment options (`left`, `center`, `right`, `justify`) within a Textual application using Python. This code defines a simple Textual app that displays four static widgets, each with a different text alignment applied via CSS classes.
SOURCE: https://github.com/textualize/textual/blob/main/docs/styles/text_align.md#_snippet_0

LANGUAGE: python
CODE:
```
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static
from textual.containers import Container

class TextAlignApp(App):
    CSS_PATH = "text_align.tcss"

    def compose(self) -> ComposeResult:
        yield Header()
        with Container():
            yield Static("Left aligned text", classes="left")
            yield Static("Center aligned text", classes="center")
            yield Static("Right aligned text", classes="right")
            yield Static("Justified text", classes="justify")
        yield Footer()

if __name__ == "__main__":
    app = TextAlignApp()
    app.run()
```

----------------------------------------

TITLE: Running Textual Application with Custom Port (Bash)
DESCRIPTION: This command runs a Textual application (`my_app.py`) in development mode, explicitly specifying the same custom port (7342) that the console is configured to use. This ensures proper communication between the application and the devtools console.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/devtools.md#_snippet_16

LANGUAGE: bash
CODE:
```
textual run --dev --port 7342 my_app.py
```

----------------------------------------

TITLE: Using Auto Colors for Contrast in Textual Markup
DESCRIPTION: Explains the 'auto' color value, which instructs Textual to automatically select either white or black text color to ensure optimal contrast against a specified background color (e.g., `[auto on sienna]`).
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/content.md#_snippet_11

LANGUAGE: Textual Markup
CODE:
```
[auto on sienna]This should be fairly readable.
```

----------------------------------------

TITLE: Clock without Recompose - Python
DESCRIPTION: This example shows a clock implemented without recompose. It updates the time every second by refreshing the Digits widget and formatting the time in both the `compose()` method and the `watch_time()` method.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/reactivity.md#_snippet_15

LANGUAGE: Python
CODE:
```
class Digits(Widget):
    
```

----------------------------------------

TITLE: Creating Hatch Environment
DESCRIPTION: Creates a new virtual environment for the project using Hatch. This command only needs to be run once.
SOURCE: https://github.com/textualize/textual/blob/main/docs/how-to/package-with-hatch.md#_snippet_7

LANGUAGE: Bash
CODE:
```
hatch env create
```

----------------------------------------

TITLE: Setting Widget Opacity to 50% in Python
DESCRIPTION: Illustrates how to programmatically set the `opacity` of a Textual widget to 50% using its `styles` attribute in Python. This achieves the same visual blending effect as the CSS `opacity` property.
SOURCE: https://github.com/textualize/textual/blob/main/docs/styles/opacity.md#_snippet_2

LANGUAGE: python
CODE:
```
# Fade the widget to 50% against its parent's background
widget.styles.opacity = "50%"
```

----------------------------------------

TITLE: Using Python Integers and Floats for CSS Number Types
DESCRIPTION: This Python snippet illustrates how `int` and `float` types are used to set CSS-like properties that expect a <number> type. It demonstrates assigning an integer tuple for `grid_size` and a float for `opacity` to a widget's style.
SOURCE: https://github.com/textualize/textual/blob/main/docs/css_types/number.md#_snippet_1

LANGUAGE: python
CODE:
```
widget.styles.grid_size = (3, 6)  # Integers are numbers
widget.styles.opacity = 0.5       # Numbers can have a decimal part
```

----------------------------------------

TITLE: Applying Italic Text Style in CSS
DESCRIPTION: This CSS snippet demonstrates how to apply an italic text style to a Textual widget using the `text-style` property. This property directly sets the visual style of text within the widget. It is typically used within a Textual CSS (TCSS) file to define styles for specific selectors.
SOURCE: https://github.com/textualize/textual/blob/main/docs/styles/text_style.md#_snippet_0

LANGUAGE: css
CODE:
```
text-style: italic;
```

----------------------------------------

TITLE: Applying Backgrounds in Textual Python (Basic Example)
DESCRIPTION: Demonstrates how to apply different background colors to widgets using Textual's Python API. This snippet is part of a basic usage example, showing how to set distinct backgrounds for multiple UI elements.
SOURCE: https://github.com/textualize/textual/blob/main/docs/styles/background.md#_snippet_1

LANGUAGE: python
CODE:
```
--8<-- "docs/examples/styles/background.py"
```

----------------------------------------

TITLE: Setting Grid Gutter in Textual CSS Examples
DESCRIPTION: These CSS examples demonstrate how to set the `grid-gutter` property. The first example sets uniform vertical and horizontal gutters to '5', while the second example sets them independently to '1' (vertical) and '2' (horizontal) using two integer values.
SOURCE: https://github.com/textualize/textual/blob/main/docs/styles/grid/grid_gutter.md#_snippet_1

LANGUAGE: CSS
CODE:
```
/* Set vertical and horizontal gutters to be the same */
grid-gutter: 5;

/* Set vertical and horizontal gutters separately */
grid-gutter: 1 2;
```

----------------------------------------

TITLE: Textual Link CSS Property Syntax Definition
DESCRIPTION: This snippet provides the HTML-formatted syntax definitions for various CSS properties used to style Textual action links. It details properties like link-background, link-color, and link-style, along with their hover counterparts, specifying the expected value types for each.
SOURCE: https://github.com/textualize/textual/blob/main/docs/styles/links/index.md#_snippet_0

LANGUAGE: HTML
CODE:
```
<a href="./link_background">link-background</a>: <a href="../../../css_types/color">&lt;color&gt;</a> [<a href="../../../css_types/percentage">&lt;percentage&gt;</a>];

<a href="./link_color">link-color</a>: <a href="../../../css_types/color">&lt;color&gt;</a> [<a href="../../../css_types/percentage">&lt;percentage&gt;</a>];

<a href="./link_style">link-style</a>: <a href="../../../css_types/text_style">&lt;text-style&gt;</a>;

<a href="./link_background_hover">link-background-hover</a>: <a href="../../../css_types/color">&lt;color&gt;</a> [<a href="../../../css_types/percentage">&lt;percentage&gt;</a>];

<a href="./link_color_hover">link-color-hover</a>: <a href="../../../css_types/color">&lt;color&gt;</a> [<a href="../../../css_types/percentage">&lt;percentage&gt;</a>];

<a href="./link_style_hover">link-style-hover</a>: <a href="../../../css_types/text_style">&lt;text-style&gt;</a>;
```

----------------------------------------

TITLE: Setting Text Styles in Python
DESCRIPTION: This snippet illustrates how to programmatically set text styles for a widget in Python. It provides examples for applying a single style like 'strike' and combining multiple styles such as 'strike bold italic reverse' to the 'text_style' attribute of a widget's styles.
SOURCE: https://github.com/textualize/textual/blob/main/docs/css_types/text_style.md#_snippet_1

LANGUAGE: python
CODE:
```
# You can specify any value by itself
widget.styles.text_style = "strike"

# You can also combine multiple values
widget.styles.text_style = "strike bold italic reverse
```

----------------------------------------

TITLE: Applying Tint Style in CSS
DESCRIPTION: These CSS examples demonstrate how to apply the `tint` style. The first example uses a named color ('red') with a 20% alpha, while the second uses an `rgba` function to specify a green color with 30% opacity.
SOURCE: https://github.com/textualize/textual/blob/main/docs/styles/tint.md#_snippet_1

LANGUAGE: CSS
CODE:
```
/* A red tint (could indicate an error) */
tint: red 20%;

/* A green tint */
tint: rgba(0, 200, 0, 0.3);
```

----------------------------------------

TITLE: Applying Thin Green Keyline in CSS
DESCRIPTION: This CSS snippet demonstrates how to apply a 'thin' green keyline to a 'Vertical' element using the 'keyline' property. It sets both the line style and color for visual separation or emphasis.
SOURCE: https://github.com/textualize/textual/blob/main/docs/css_types/keyline.md#_snippet_0

LANGUAGE: css
CODE:
```
Vertical {
    keyline: thin green;
}
```

----------------------------------------

TITLE: Basic Object Inspection with Rich Inspect (Python)
DESCRIPTION: This snippet demonstrates the basic usage of `rich.inspect` to get a data-oriented summary of a Python object. It shows how to import `inspect`, create a file object, and then use `inspect` to display its attributes.
SOURCE: https://github.com/textualize/textual/blob/main/docs/blog/posts/rich-inspect.md#_snippet_0

LANGUAGE: Python
CODE:
```
>>> from rich import inspect
>>> text_file = open("foo.txt", "w")
>>> inspect(text_file)
```

----------------------------------------

TITLE: Setting Text-wrap Style in Python (Textual)
DESCRIPTION: These Python snippets show how to programmatically set the `text-wrap` style for a Textual widget. The first line enables word-wrapping, and the second disables it, directly controlling the text flow behavior of the widget.
SOURCE: https://github.com/textualize/textual/blob/main/docs/styles/text_wrap.md#_snippet_2

LANGUAGE: Python
CODE:
```
widget.styles.text_wrap = "wrap"
widget.styles.text_wrap = "nowrap"
```

----------------------------------------

TITLE: Styling a Widget with a Type Selector
DESCRIPTION: This CSS code styles all `Alert` widgets with a solid red border. The type selector matches the name of the Python class.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/CSS.md#_snippet_5

LANGUAGE: css
CODE:
```
Alert {
  border: solid red;
}
```

----------------------------------------

TITLE: Simulating Double and Triple Clicks with Textual Pilot (Python)
DESCRIPTION: This snippet shows how to simulate multiple clicks (e.g., double or triple clicks) on a widget by setting the `times` parameter in the `pilot.click` method. This is useful for testing interactions that require rapid consecutive clicks.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/testing.md#_snippet_6

LANGUAGE: python
CODE:
```
await pilot.click(Button, times=2) # Double click
await pilot.click(Button, times=3) # Triple click
```

----------------------------------------

TITLE: Defining Visibility Style Syntax (CSS)
DESCRIPTION: This snippet illustrates the basic syntax for the `visibility` CSS property, specifying its two possible values: `hidden` to make an element invisible while retaining its layout space, and `visible` to display it normally.
SOURCE: https://github.com/textualize/textual/blob/main/docs/styles/visibility.md#_snippet_0

LANGUAGE: css
CODE:
```
visibility: hidden | visible;
```

----------------------------------------

TITLE: Benchmarking Standard Tuple Creation Performance with Hyperfine
DESCRIPTION: This snippet uses `hyperfine` to benchmark the creation time of 10,000 standard `tuple` instances in Python. It demonstrates the performance improvement achieved by switching from `NamedTuple` to `tuple` for high-frequency instantiations, leading to significant responsiveness gains.
SOURCE: https://github.com/textualize/textual/blob/main/docs/blog/posts/text-area-learnings.md#_snippet_3

LANGUAGE: Shell
CODE:
```
hyperfine -w 2 'python sandbox/darren/make_tuples.py'
```

----------------------------------------

TITLE: Constructing Content Without Markup Processing (Python)
DESCRIPTION: Illustrates creating a `Content` object directly from a string using its constructor. Note that this method does not process markup; any square brackets in the string will be displayed literally rather than being interpreted as tags.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/content.md#_snippet_25

LANGUAGE: Python
CODE:
```
Content("hello, World!")
```

----------------------------------------

TITLE: Adjusting Color Opacity with Percentage in Textual Markup
DESCRIPTION: Shows how to modify the opacity of a color using a percentage value appended to the color name (e.g., `[red 50%]`). This creates a faded effect by blending the color with the background.
SOURCE: https://github.com/textualize/textual/blob/main/docs/guide/content.md#_snippet_12

LANGUAGE: Textual Markup
CODE:
```
[red 50%]This is in faded red[/]
```

----------------------------------------

TITLE: Textual CSS Styling for Link Hover Color Example
DESCRIPTION: This TCSS snippet demonstrates applying `link-color-hover` to specific Textual action links. It highlights how the style selectively targets action links, leaving regular hyperlinks unaffected, by using CSS selectors like `nth-child`.
SOURCE: https://github.com/textualize/textual/blob/main/docs/styles/links/link_color_hover.md#_snippet_2

LANGUAGE: css
CODE:
```
Screen {
    background: #222;
}

Label:nth-child(3) { /* Targets the first action link */
    link-color-hover: red;
}

Label:nth-child(4) { /* Targets the second action link */
    link-color-hover: blue 50%;
}

Label:nth-child(5) { /* Targets the third action link */
    link-color-hover: green;
}
```

----------------------------------------

TITLE: Defining Layers in CSS
DESCRIPTION: This CSS snippet demonstrates how to define `layers` within a `Screen` block. It assigns a space-separated string of valid name patterns, showcasing names composed of only letters, letters and hyphens, leading underscores, and alphanumeric characters, adhering to the specified `<name>` syntax.
SOURCE: https://github.com/textualize/textual/blob/main/docs/css_types/name.md#_snippet_0

LANGUAGE: css
CODE:
```
Screen {
    layers: onlyLetters Letters-and-hiphens _lead-under letters-1-digit;
}
```

----------------------------------------

TITLE: Setting Max-width in Python
DESCRIPTION: This snippet illustrates how to programmatically set the `max_width` style for a Textual widget using Python. It includes examples for setting a fixed maximum width and a relative maximum width using string representation for viewport percentage.
SOURCE: https://github.com/textualize/textual/blob/main/docs/styles/max_width.md#_snippet_1

LANGUAGE: python
CODE:
```
# Set the maximum width to 10 rows
widget.styles.max_width = 10

# Set the maximum width to 25% of the viewport width
widget.styles.max_width = "25vw"
```
