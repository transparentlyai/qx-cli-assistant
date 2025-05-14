TITLE: Basic Prompt with prompt-toolkit (Python)
DESCRIPTION: This Python snippet demonstrates the simplest usage of `prompt_toolkit` to get input from the user. It calls the `prompt` function with a string message and then prints the returned user input. This mimics the behavior of Python's built-in `input` or `raw_input`. Requires the `prompt_toolkit` library installed.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/getting_started.rst#_snippet_2

LANGUAGE: python
CODE:
```
from prompt_toolkit import prompt

text = prompt("Give me some input: ")
print(f"You said: {text}")
```

----------------------------------------

TITLE: Implementing SQLite REPL Main Loop - Python
DESCRIPTION: Contains the core logic for the SQLite REPL application. It establishes a connection to the specified database, initializes a `PromptSession` with configured syntax highlighting (SqlLexer), autocompletion (sql_completer), and styling. The code then enters a loop to repeatedly prompt the user for SQL input, execute the command via the database connection, and print results or any exceptions encountered. It includes basic handling for keyboard interrupts (Ctrl-C) and end-of-file (Ctrl-D) signals.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/tutorials/repl.rst#_snippet_9

LANGUAGE: python
CODE:
```
def main(database):
        connection = sqlite3.connect(database)
        session = PromptSession(
            lexer=PygmentsLexer(SqlLexer), completer=sql_completer, style=style)

        while True:
            try:
                text = session.prompt('> ')
            except KeyboardInterrupt:
                continue  # Control-C pressed. Try again.
            except EOFError:
                break  # Control-D pressed.

            with connection:
                try:
                    messages = connection.execute(text)
                except Exception as e:
                    print(repr(e))
                else:
                    for message in messages:
                        print(message)

        print('GoodBye!')
```

----------------------------------------

TITLE: Simple Input Prompt with prompt_toolkit in Python
DESCRIPTION: Demonstrates the basic usage of the `prompt` function from `prompt_toolkit.shortcuts` to ask the user for text input. It functions similarly to Python's built-in `input` or `raw_input` but provides basic Emacs key bindings. The returned text is then printed to the console.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/asking_for_input.rst#_snippet_0

LANGUAGE: python
CODE:
```
from prompt_toolkit import prompt

text = prompt("Give me some input: ")
print(f"You said: {text}")
```

----------------------------------------

TITLE: Getting User Input using Prompt Toolkit - Python
DESCRIPTION: Demonstrates the simplest use of the prompt_toolkit library. It imports the `prompt` function to ask the user for input and then prints the received input. This snippet shows the basic interaction pattern.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/README.rst#_snippet_2

LANGUAGE: Python
CODE:
```
from prompt_toolkit import prompt

if __name__ == '__main__':
    answer = prompt('Give me some input: ')
    print('You said: %s' % answer)
```

----------------------------------------

TITLE: Read User Input using prompt_toolkit
DESCRIPTION: This Python snippet demonstrates the most basic use of prompt_toolkit's `prompt()` function to read a single line of input from the user and print it back. It is wrapped in a standard `main` function and guarded by `if __name__ == '__main__':`.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/tutorials/repl.rst#_snippet_1

LANGUAGE: python
CODE:
```
from prompt_toolkit import prompt

def main():
    text = prompt('> ')
    print('You entered:', text)

if __name__ == '__main__':
    main()
```

----------------------------------------

TITLE: Running Simple Full Screen prompt_toolkit Application Python
DESCRIPTION: Creates and runs a minimal full-screen prompt_toolkit application instance. This example shows the basic structure, initializing the `Application` object with `full_screen=True` to use the alternate screen buffer and calling `run()` to start the event loop. It results in a default application message because no layout is specified.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/full_screen_apps.rst#_snippet_0

LANGUAGE: python
CODE:
```
from prompt_toolkit import Application

app = Application(full_screen=True)
app.run()
```

----------------------------------------

TITLE: Displaying an Input Dialog in Prompt Toolkit
DESCRIPTION: Use the input_dialog function to prompt the user for text input. It displays a title, a text label, and an input field. The .run() method displays the dialog and returns the string entered by the user when they submit the form (usually by pressing Enter). An optional password=True argument can turn this into a password input field.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/dialogs.rst#_snippet_1

LANGUAGE: python
CODE:
```
from prompt_toolkit.shortcuts import input_dialog

text = input_dialog(
    title='Input dialog example',
    text='Please type your name:').run()
```

----------------------------------------

TITLE: Defining Basic Key Bindings in prompt_toolkit Python
DESCRIPTION: This snippet demonstrates how to create a KeyBindings instance and define simple key bindings using the `@bindings.add` decorator. It shows examples for binding a single character ('a') and a control key combination ('c-t'), executing a function when the key is pressed.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/advanced_topics/key_bindings.rst#_snippet_0

LANGUAGE: python
CODE:
```
from prompt_toolkit.key_binding import KeyBindings

bindings = KeyBindings()

@bindings.add('a')
def _(event):
    " Do something if 'a' has been pressed. "
    ...


@bindings.add('c-t')
def _(event):
    " Do something if Control-T has been pressed. "
    ...
```

----------------------------------------

TITLE: Creating Password Input Prompt (Python)
DESCRIPTION: Shows how to create a password input field using prompt-toolkit where the typed characters are replaced by asterisks (`*`). This is achieved by setting the `is_password=True` flag when calling the `prompt` function, preventing sensitive input from being displayed directly. Requires `prompt_toolkit`.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/asking_for_input.rst#_snippet_35

LANGUAGE: python
CODE:
```
from prompt_toolkit import prompt

prompt("Enter password: ", is_password=True)
```

----------------------------------------

TITLE: Using PromptSession with Default History - Python
DESCRIPTION: Demonstrates the standard way to use `prompt_toolkit.shortcuts.PromptSession`. By default, `PromptSession` includes an in-memory history, allowing users to recall previous inputs using arrow keys within the same session.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/asking_for_input.rst#_snippet_19

LANGUAGE: python
CODE:
```
from prompt_toolkit import PromptSession

session = PromptSession()

while True:
    session.prompt()
```

----------------------------------------

TITLE: Running prompt_toolkit Application in asyncio Python
DESCRIPTION: This snippet demonstrates how to run a prompt_toolkit Application within an existing asyncio event loop. It defines an async main function that creates an Application instance (placeholder ...) and uses the awaitable application.run_async() method to execute it, then runs the main coroutine using asyncio.get_event_loop().run_until_complete(). This is the recommended approach when embedding prompt_toolkit in an asyncio application.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/advanced_topics/asyncio.rst#_snippet_0

LANGUAGE: python
CODE:
```
from prompt_toolkit.application import Application
import asyncio

async def main():
    # Define application.
    application = Application(
        ...
    )

    result = await application.run_async()
    print(result)

asyncio.get_event_loop().run_until_complete(main())
```

----------------------------------------

TITLE: Using Asyncio Coroutine as prompt_toolkit Key Binding Handler Python
DESCRIPTION: This snippet shows how to define a key binding ('x') that executes an asyncio coroutine as its handler. The coroutine performs background tasks, printing 'hello' repeatedly above the prompt using `in_terminal` and pausing with `asyncio.sleep`, allowing the user to continue typing while the task runs.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/advanced_topics/key_bindings.rst#_snippet_9

LANGUAGE: Python
CODE:
```
from prompt_toolkit.application import in_terminal

@bindings.add('x')
async def print_hello(event):
    """
    Pressing 'x' will print 5 times "hello" in the background above the
    prompt.
    """
    for i in range(5):
        # Print hello above the current prompt.
        async with in_terminal():
            print('hello')

        # Sleep, but allow further input editing in the meantime.
        await asyncio.sleep(1)
```

----------------------------------------

TITLE: PromptSession Asynchronous Call (v3) - Python
DESCRIPTION: This snippet demonstrates the updated method for performing asynchronous prompt calls in prompt_toolkit version 3.0. The dedicated `prompt_async()` method replaces the `prompt()` method with the `async_=True` parameter used in version 2.0.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/upgrading/3.0.rst#_snippet_4

LANGUAGE: python
CODE:
```
# For 3.0
result = await PromptSession().prompt_async('Say something: ')
```

----------------------------------------

TITLE: Adding Simple Word Autocompletion with prompt_toolkit in Python
DESCRIPTION: Illustrates how to add basic autocompletion to a prompt using the `WordCompleter`. An instance of `WordCompleter` is created with a list of potential completion words and passed to the `completer` parameter of the `prompt` function. The completer suggests completions for the word immediately preceding the cursor.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/asking_for_input.rst#_snippet_9

LANGUAGE: python
CODE:
```
from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter

html_completer = WordCompleter(["<html>", "<body>", "<head>", "<title>"])
text = prompt("Enter HTML: ", completer=html_completer)
print(f"You said: {text}")
```

----------------------------------------

TITLE: Adding Custom Key Bindings to Prompt (Python)
DESCRIPTION: This example demonstrates defining custom key bindings using `KeyBindings` and adding them to the prompt. It includes bindings for printing text using `run_in_terminal` and exiting the application, showing how to handle actions that affect the terminal output or application state.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/asking_for_input.rst#_snippet_26

LANGUAGE: python
CODE:
```
from prompt_toolkit import prompt
from prompt_toolkit.application import run_in_terminal
from prompt_toolkit.key_binding import KeyBindings

bindings = KeyBindings()

@bindings.add("c-t")
def _(event):
    " Say \"hello\" when `c-t` is pressed. "
    def print_hello():
        print("hello world")
    run_in_terminal(print_hello)

@bindings.add("c-x")
def _(event):
    " Exit when `c-x` is pressed. "
    event.app.exit()

text = prompt("> ", key_bindings=bindings)
print(f"You said: {text}")
```

----------------------------------------

TITLE: Creating a Prompt Session with prompt_toolkit in Python
DESCRIPTION: Shows how to use the `PromptSession` class to create an input session instance. Calling the `prompt` method on this instance allows for multiple input requests while maintaining state, such as input history, between calls. Configuration options can be passed to the session instance or overridden per prompt call.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/asking_for_input.rst#_snippet_1

LANGUAGE: python
CODE:
```
from prompt_toolkit import PromptSession

# Create prompt object.
session = PromptSession()

# Do multiple input calls.
text1 = session.prompt()
text2 = session.prompt()
```

----------------------------------------

TITLE: Create a REPL Loop with PromptSession
DESCRIPTION: This Python snippet introduces `PromptSession` to create a continuous loop for the REPL. It handles `KeyboardInterrupt` (Ctrl+C) to continue the loop and `EOFError` (Ctrl+D) to break the loop and exit, providing a basic interactive session experience with history.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/tutorials/repl.rst#_snippet_2

LANGUAGE: python
CODE:
```
from prompt_toolkit import PromptSession

def main():
    session = PromptSession()

    while True:
        try:
            text = session.prompt('> ')
        except KeyboardInterrupt:
            continue
        except EOFError:
            break
        else:
            print('You entered:', text)
    print('GoodBye!')

if __name__ == '__main__':
    main()
```

----------------------------------------

TITLE: Creating Custom Validator Class - Python
DESCRIPTION: Demonstrates creating a custom input validator by inheriting from `Validator` and implementing the `validate` method. It checks if the input text is purely numeric and raises a `ValidationError` with a custom message and cursor position if not.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/asking_for_input.rst#_snippet_16

LANGUAGE: python
CODE:
```
from prompt_toolkit.validation import Validator, ValidationError
from prompt_toolkit import prompt

class NumberValidator(Validator):
    def validate(self, document):
        text = document.text

        if text and not text.isdigit():
            i = 0

            # Get index of first non numeric character.
            # We want to move the cursor here.
            for i, c in enumerate(text):
                if not c.isdigit():
                    break

            raise ValidationError(
                message="This input contains non-numeric characters",
                cursor_position=i
            )

number = int(prompt("Give a number: ", validator=NumberValidator()))
print(f"You said: {number}")
```

----------------------------------------

TITLE: Creating Basic Custom Completer Class - Python
DESCRIPTION: Demonstrates the minimum implementation for a custom completer by inheriting from `Completer` and overriding the `get_completions` generator method. It yields a simple completion with a start position.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/asking_for_input.rst#_snippet_11

LANGUAGE: python
CODE:
```
from prompt_toolkit import prompt
from prompt_toolkit.completion import Completer, Completion

class MyCustomCompleter(Completer):
    def get_completions(self, document, complete_event):
        yield Completion("completion", start_position=0)

text = prompt("> ", completer=MyCustomCompleter())
```

----------------------------------------

TITLE: Defining SQL Keywords for Completion - Python
DESCRIPTION: Defines a comprehensive list of SQL keywords using `WordCompleter` from `prompt_toolkit.completion`. This list serves as the source for autocompletion suggestions provided to the user as they type SQL commands in the REPL, enhancing usability. The completer is configured to ignore case.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/tutorials/repl.rst#_snippet_7

LANGUAGE: python
CODE:
```
'drop', 'each', 'else', 'end', 'escape', 'except', 'exclusive',
        'exists', 'explain', 'fail', 'for', 'foreign', 'from', 'full', 'glob',
        'group', 'having', 'if', 'ignore', 'immediate', 'in', 'index',
        'indexed', 'initially', 'inner', 'insert', 'instead', 'intersect',
        'into', 'is', 'isnull', 'join', 'key', 'left', 'like', 'limit',
        'match', 'natural', 'no', 'not', 'notnull', 'null', 'of', 'offset',
        'on', 'or', 'order', 'outer', 'plan', 'pragma', 'primary', 'query',
        'raise', 'recursive', 'references', 'regexp', 'reindex', 'release',
        'rename', 'replace', 'restrict', 'right', 'rollback', 'row',
        'savepoint', 'select', 'set', 'table', 'temp', 'temporary', 'then',
        'to', 'transaction', 'trigger', 'union', 'unique', 'update', 'using',
        'vacuum', 'values', 'view', 'virtual', 'when', 'where', 'with',
        'without'], ignore_case=True)
```

----------------------------------------

TITLE: Displaying a Yes/No Confirmation Dialog in Prompt Toolkit
DESCRIPTION: Use the yes_no_dialog function to present a simple confirmation prompt to the user. It displays a title, a text label, and 'Yes'/'No' buttons. The .run() method displays the dialog and returns a boolean value (True for Yes, False for No) based on the user's selection.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/dialogs.rst#_snippet_2

LANGUAGE: python
CODE:
```
from prompt_toolkit.shortcuts import yes_no_dialog

result = yes_no_dialog(
    title='Yes/No dialog example',
    text='Do you want to confirm?').run()
```

----------------------------------------

TITLE: Combining Filters with Operators - prompt_toolkit Python
DESCRIPTION: Demonstrates combining `prompt_toolkit` filters using the negation (`~`) and logical OR (`|`) operators (`&` for AND is also supported) to create more complex conditional filters. The examples show how these compound filters are applied in key bindings to activate based on combined criteria, such as 'not searching' or 'searching OR has selection'.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/advanced_topics/filters.rst#_snippet_4

LANGUAGE: python
CODE:
```
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.filters import has_selection, has_search

kb = KeyBindings()

@kb.add('c-t', filter=~is_searching)
def _(event):
    " Do something, but not while searching. "
    pass

@kb.add('c-t', filter=has_search | has_selection)
def _(event):
    " Do something, but only when searching or when there is a selection. "
    pass
```

----------------------------------------

TITLE: Add Syntax Highlighting to REPL Input
DESCRIPTION: This Python snippet integrates Pygments SQL lexer to add syntax highlighting to the user input within the REPL loop. It uses `PygmentsLexer` to wrap the `SqlLexer` and passes it to the `PromptSession` constructor.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/tutorials/repl.rst#_snippet_3

LANGUAGE: python
CODE:
```
from prompt_toolkit import PromptSession
from prompt_toolkit.lexers import PygmentsLexer
from pygments.lexers.sql import SqlLexer

def main():
    session = PromptSession(lexer=PygmentsLexer(SqlLexer))

    while True:
        try:
            text = session.prompt('> ')
        except KeyboardInterrupt:
            continue
        except EOFError:
            break
        else:
            print('You entered:', text)
    print('GoodBye!')

if __name__ == '__main__':
    main()
```

----------------------------------------

TITLE: Adding Conditional Key Bindings to Prompt (Python)
DESCRIPTION: This snippet shows how to make a custom key binding active only when a specific condition is met. It uses the `@Condition` decorator and passes the condition filter to the `@bindings.add` method.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/asking_for_input.rst#_snippet_27

LANGUAGE: python
CODE:
```
from prompt_toolkit import prompt
from prompt_toolkit.filters import Condition
from prompt_toolkit.key_binding import KeyBindings
import datetime

bindings = KeyBindings()

@Condition
def is_active():
    " Only activate key binding on the second half of each minute. "
    return datetime.datetime.now().second > 30

@bindings.add("c-t", filter=is_active)
def _(event):
    # ...
    pass

prompt("> ", key_bindings=bindings)
```

----------------------------------------

TITLE: Initializing NestedCompleter with Dictionary - Python
DESCRIPTION: Shows how to create a hierarchical completer from a nested dictionary where `None` indicates no further nesting. It then uses this completer with the `prompt` function to get user input.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/asking_for_input.rst#_snippet_10

LANGUAGE: python
CODE:
```
from prompt_toolkit import prompt
from prompt_toolkit.completion import NestedCompleter

completer = NestedCompleter.from_nested_dict({
    "show": {
        "version": None,
        "clock": None,
        "ip": {
            "interface": {"brief"}
        }
    },
    "exit": None,
})

text = prompt("# ", completer=completer)
print(f"You said: {text}")
```

----------------------------------------

TITLE: Using Filter in Key Binding - prompt_toolkit Python
DESCRIPTION: Explains how to use a `prompt_toolkit` filter, such as `is_searching`, within the `filter` parameter of the `@kb.add` decorator on a `KeyBindings` instance. This ensures that the associated key binding (`c-t`) only triggers the decorated function when the filter evaluates to `True`, enabling conditional key press handling.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/advanced_topics/filters.rst#_snippet_2

LANGUAGE: python
CODE:
```
from prompt_toolkit.key_binding import KeyBindings

kb = KeyBindings()

@kb.add('c-t', filter=is_searching)
def _(event):
    # Do, something, but only when searching.
    pass
```

----------------------------------------

TITLE: Displaying a Checkbox List Dialog in Prompt Toolkit
DESCRIPTION: Use the checkboxlist_dialog function to display a dialog with a list of choices where the user can select multiple options, presented as checkboxes. Choices are provided as a list of tuples (return value, display text). The .run() method displays the dialog and returns a list of values corresponding to the selected checkbox options.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/dialogs.rst#_snippet_5

LANGUAGE: python
CODE:
```
from prompt_toolkit.shortcuts import checkboxlist_dialog

results_array = checkboxlist_dialog( 
    title="CheckboxList dialog", 
    text="What would you like in your breakfast ?",
    values=[ 
        ("eggs", "Eggs"),
        ("bacon", "Bacon"),
        ("croissants", "20 Croissants"),
        ("daily", "The breakfast of the day")
    ] 
).run()
```

----------------------------------------

TITLE: Attaching a Filter to a Key Binding in prompt_toolkit Python
DESCRIPTION: This snippet demonstrates how to make a key binding conditional by attaching a Filter, specifically a Condition instance. The key binding ('c-t') will only be active and trigger its associated function if the `is_active` condition function returns `True` when evaluated.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/advanced_topics/key_bindings.rst#_snippet_5

LANGUAGE: python
CODE:
```
from prompt_toolkit.filters import Condition
import datetime

@Condition
def is_active():
    " Only activate key binding on the second half of each minute. "
    return datetime.datetime.now().second > 30

@bindings.add('c-t', filter=is_active)
def _(event):
    # ...
    pass
```

----------------------------------------

TITLE: Displaying a Radio List Dialog in Prompt Toolkit
DESCRIPTION: Use the radiolist_dialog function to display a dialog with a list of mutually exclusive choices, presented as radio buttons. Choices are provided as a list of tuples, where each tuple contains the return value (first element) and the text to display (second element). The .run() method displays the dialog and returns the value associated with the selected radio option.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/dialogs.rst#_snippet_4

LANGUAGE: python
CODE:
```
from prompt_toolkit.shortcuts import radiolist_dialog

result = radiolist_dialog( 
    title="RadioList dialog", 
    text="Which breakfast would you like ?", 
    values=[ 
        ("breakfast1", "Eggs and beacon"), 
        ("breakfast2", "French breakfast"), 
        ("breakfast3", "Equestrian breakfast") 
    ] 
).run()
```

----------------------------------------

TITLE: Displaying a Button Dialog in Prompt Toolkit
DESCRIPTION: Use the button_dialog function to offer the user choices represented by buttons. Buttons are defined as a list of tuples, where each tuple contains the button's label (string) and the value to be returned if that button is clicked. The .run() method displays the dialog and returns the value associated with the selected button.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/dialogs.rst#_snippet_3

LANGUAGE: python
CODE:
```
from prompt_toolkit.shortcuts import button_dialog

result = button_dialog(
    title='Button dialog example',
    text='Do you want to confirm?',
    buttons=[
        ('Yes', True),
        ('No', False),
        ('Maybe...', None)
    ],
).run()
```

----------------------------------------

TITLE: Conditionally Enabling/Disabling Key Binding Sets in prompt_toolkit Python
DESCRIPTION: This snippet shows how to wrap an entire set of KeyBindings (`my_bindings`) within a ConditionalKeyBindings object. The wrapped bindings will only be active if the provided filter (`is_active` condition) evaluates to `True`.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/advanced_topics/key_bindings.rst#_snippet_6

LANGUAGE: python
CODE:
```
from prompt_toolkit.key_binding import ConditionalKeyBindings
import datetime

@Condition
def is_active():
    " Only activate key binding on the second half of each minute. "
    return datetime.datetime.now().second > 30

bindings = ConditionalKeyBindings(
    key_bindings=my_bindings,
    filter=is_active)

```

----------------------------------------

TITLE: Displaying a Message Dialog in Prompt Toolkit
DESCRIPTION: Use the message_dialog function to display a simple message box with a title and text. The .run() method is called to display the dialog and block until the user dismisses it (usually by pressing Enter). This dialog does not return a value.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/dialogs.rst#_snippet_0

LANGUAGE: python
CODE:
```
from prompt_toolkit.shortcuts import message_dialog

message_dialog(
    title='Example dialog window',
    text='Do you want to continue?\nPress ENTER to quit.').run()
```

----------------------------------------

TITLE: Adding Pygments Syntax Highlighting to prompt_toolkit in Python
DESCRIPTION: Illustrates how to enable syntax highlighting by providing a `lexer` parameter to the `prompt` function. This example uses an `HtmlLexer` from Pygments, wrapped in `PygmentsLexer`, to apply highlighting based on HTML syntax rules. The default prompt_toolkit style includes the default Pygments colorscheme.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/asking_for_input.rst#_snippet_2

LANGUAGE: python
CODE:
```
from pygments.lexers.html import HtmlLexer
from prompt_toolkit.shortcuts import prompt
from prompt_toolkit.lexers import PygmentsLexer

text = prompt("Enter HTML: ", lexer=PygmentsLexer(HtmlLexer))
print(f"You said: {text}")
```

----------------------------------------

TITLE: Enabling Mouse Support in Prompt (Python)
DESCRIPTION: Shows how to enable limited mouse support for a prompt-toolkit input field. This includes functionality for positioning the cursor, scrolling in multiline inputs, and clicking in the autocompletion menu. Mouse support is activated by passing the `mouse_support=True` option to the `prompt` function. Requires `prompt_toolkit`.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/asking_for_input.rst#_snippet_33

LANGUAGE: python
CODE:
```
from prompt_toolkit import prompt

prompt("What is your name: ", mouse_support=True)
```

----------------------------------------

TITLE: Using PromptSession with Auto-suggestion from History (Python)
DESCRIPTION: This snippet demonstrates how to use `PromptSession` with `AutoSuggestFromHistory` to provide suggestions to the user based on previous inputs stored in an `InMemoryHistory`. A loop continuously prompts the user, retrieves input, and prints it back.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/asking_for_input.rst#_snippet_21

LANGUAGE: python
CODE:
```
from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory

session = PromptSession()

while True:
    text = session.prompt("> ", auto_suggest=AutoSuggestFromHistory())
    print(f"You said: {text}")
```

----------------------------------------

TITLE: Displaying Progress for Generator with Total in prompt_toolkit Python
DESCRIPTION: Explains how to provide the total number of items explicitly using the `total` parameter when the iterable itself cannot determine its length (e.g., a generator). This allows the progress bar to display completion percentage and estimated time. Requires `prompt_toolkit` and `time`.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/progress_bars.rst#_snippet_1

LANGUAGE: python
CODE:
```
def some_iterable():
    yield ...

with ProgressBar() as pb:
    for i in pb(some_iterable(), total=1000):
        time.sleep(.01)
```

----------------------------------------

TITLE: Printing HTML fg/bg Attributes with prompt_toolkit
DESCRIPTION: Demonstrates setting both foreground (`fg`) and background (`bg`) colors for text within an HTML tag using attributes, supporting both ANSI and named colors.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/printing_text.rst#_snippet_4

LANGUAGE: python
CODE:
```
# Colors from the ANSI palette.
print_formatted_text(HTML('<aaa fg="ansiwhite" bg="ansigreen">White on green</aaa>'))
```

----------------------------------------

TITLE: Printing HTML Color Tags with prompt_toolkit
DESCRIPTION: Shows how to use the `HTML` class to specify foreground colors using tag names, including ANSI palette colors (e.g., `<ansired>`) and named colors (e.g., `<skyblue>`).
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/printing_text.rst#_snippet_3

LANGUAGE: python
CODE:
```
# Colors from the ANSI palette.
print_formatted_text(HTML('<ansired>This is red</ansired>'))
print_formatted_text(HTML('<ansigreen>This is green</ansigreen>'))

# Named colors (256 color palette, or true color, depending on the output).
print_formatted_text(HTML('<skyblue>This is sky blue</skyblue>'))
print_formatted_text(HTML('<seagreen>This is sea green</seagreen>'))
print_formatted_text(HTML('<violet>This is violet</violet>'))
```

----------------------------------------

TITLE: Initializing Prompt with Default Value (Python)
DESCRIPTION: Demonstrates a basic interactive prompt using prompt-toolkit. It sets a default value for the input field by retrieving the current user's name using `getpass.getuser()` from the standard library's `getpass` module. Requires `prompt_toolkit` and `getpass`.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/asking_for_input.rst#_snippet_32

LANGUAGE: python
CODE:
```
from prompt_toolkit import prompt
import getpass

prompt("What is your name: ", default=f"{getpass.getuser()}")
```

----------------------------------------

TITLE: Style the Completion Menu Appearance
DESCRIPTION: This Python snippet demonstrates how to customize the appearance of the auto-completion menu. It creates a `prompt_toolkit.styles.Style` instance with specific rules for 'completion-menu' and 'scrollbar' elements and passes the style to the `PromptSession` constructor.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/tutorials/repl.rst#_snippet_5

LANGUAGE: python
CODE:
```
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.lexers import PygmentsLexer
from prompt_toolkit.styles import Style
from pygments.lexers.sql import SqlLexer

sql_completer = WordCompleter([
    'abort', 'action', 'add', 'after', 'all', 'alter', 'analyze', 'and',
    'as', 'asc', 'attach', 'autoincrement', 'before', 'begin', 'between',
    'by', 'cascade', 'case', 'cast', 'check', 'collate', 'column',
    'commit', 'conflict', 'constraint', 'create', 'cross', 'current_date',
    'current_time', 'current_timestamp', 'database', 'default',
    'deferrable', 'deferred', 'delete', 'desc', 'detach', 'distinct',
    'drop', 'each', 'else', 'end', 'escape', 'except', 'exclusive',
    'exists', 'explain', 'fail', 'for', 'foreign', 'from', 'full', 'glob',
    'group', 'having', 'if', 'ignore', 'immediate', 'in', 'index',
    'indexed', 'initially', 'inner', 'insert', 'instead', 'intersect',
    'into', 'is', 'isnull', 'join', 'key', 'left', 'like', 'limit',
    'match', 'natural', 'no', 'not', 'notnull', 'null', 'of', 'offset',
    'on', 'or', 'order', 'outer', 'plan', 'pragma', 'primary', 'query',
    'raise', 'recursive', 'references', 'regexp', 'reindex', 'release',
    'rename', 'replace', 'restrict', 'right', 'rollback', 'row',
    'savepoint', 'select', 'set', 'table', 'temp', 'temporary', 'then',
    'to', 'transaction', 'trigger', 'union', 'unique', 'update', 'using',
    'vacuum', 'values', 'view', 'virtual', 'when', 'where', 'with',
    'without'], ignore_case=True)

style = Style.from_dict({
    'completion-menu.completion': 'bg:#008888 #ffffff',
    'completion-menu.completion.current': 'bg:#00aaaa #000000',
    'scrollbar.background': 'bg:#88aaaa',
    'scrollbar.button': 'bg:#222222',
})

def main():
   session = PromptSession(
       lexer=PygmentsLexer(SqlLexer), completer=sql_completer, style=style)

   while True:
       try:
           text = session.prompt('> ')
       except KeyboardInterrupt:
           continue
       except EOFError:
           break
       else:
           print('You entered:', text)
   print('GoodBye!')

if __name__ == '__main__':
    main()
```

----------------------------------------

TITLE: Adding Global Key Binding to Exit Application - Python
DESCRIPTION: Illustrates how to register a global key binding (Ctrl-Q) to exit the prompt_toolkit application. It uses the `@kb.add('c-q')` decorator on a function that receives an event object. The handler function calls `event.app.exit()` to terminate the application's main loop, optionally returning a value.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/full_screen_apps.rst#_snippet_4

LANGUAGE: python
CODE:
```
from prompt_toolkit import Application
from prompt_toolkit.key_binding import KeyBindings

kb = KeyBindings()

@kb.add('c-q')
def exit_(event):
    """
    Pressing Ctrl-Q will exit the user interface.

    Setting a return value means: quit the event loop that drives the user
    interface and return this value from the `Application.run()` call. 
    """
    event.app.exit()

app = Application(key_bindings=kb, full_screen=True)
app.run()
```

----------------------------------------

TITLE: Merging Key Binding Sets in prompt_toolkit Python
DESCRIPTION: This snippet demonstrates how to combine multiple KeyBindings instances into a single set using the `merge_key_bindings` function. This is useful for organizing key bindings from different parts of an application.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/advanced_topics/key_bindings.rst#_snippet_7

LANGUAGE: python
CODE:
```
from prompt_toolkit.key_binding import merge_key_bindings

bindings = merge_key_bindings([
    bindings1,
    bindings2,
])
```

----------------------------------------

TITLE: Merging Multiple prompt_toolkit Styles in Python
DESCRIPTION: This snippet illustrates how to combine multiple existing prompt_toolkit.styles.Style objects into a single, merged style. It demonstrates using the prompt_toolkit.styles.merge_styles function to combine several individual Style objects (style1, style2, style3) into a single, new Style object. This is useful for layering or combining different style definitions from various sources or components within an application.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/advanced_topics/styling.rst#_snippet_8

LANGUAGE: python
CODE:
```
from prompt_toolkit.styles import merge_styles

style = merge_styles([
    style1,
    style2,
    style3
])
```

----------------------------------------

TITLE: Adding Key Bindings and Toolbar to prompt_toolkit Progress Bar Python
DESCRIPTION: Demonstrates how to pass a `KeyBindings` object to the `ProgressBar` to add custom keyboard shortcuts and how to display information using the `bottom_toolbar` parameter. It also shows using `patch_stdout` to ensure `print` statements appear correctly above the progress bar and how to use key bindings to control the progress (e.g., stopping it). Requires `prompt_toolkit`, its key bindings, HTML, stdout patching, `os`, `time`, and `signal`.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/progress_bars.rst#_snippet_6

LANGUAGE: python
CODE:
```
from prompt_toolkit import HTML
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.shortcuts import ProgressBar

import os
import time
import signal

bottom_toolbar = HTML(' <b>[f]<\/b> Print "f" <b>[x]<\/b> Abort.')

# Create custom key bindings first.
kb = KeyBindings()
cancel = [False]

@kb.add('f')
def _(event):
        print('You pressed `f`.')

@kb.add('x')
def _(event):
        " Send Abort (control-c) signal. "
        cancel[0] = True
        os.kill(os.getpid(), signal.SIGINT)

# Use `patch_stdout`, to make sure that prints go above the
# application.
with patch_stdout():
        with ProgressBar(key_bindings=kb, bottom_toolbar=bottom_toolbar) as pb:
            for i in pb(range(800)):
                time.sleep(.01)

                # Stop when the cancel flag has been set.
                if cancel[0]:
                    break
```

----------------------------------------

TITLE: Add Auto-completion for SQL Keywords
DESCRIPTION: This Python snippet adds auto-completion functionality to the REPL using `prompt_toolkit.completion.WordCompleter`. It defines a list of SQLite keywords and passes the resulting `WordCompleter` instance to the `PromptSession` constructor.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/tutorials/repl.rst#_snippet_4

LANGUAGE: python
CODE:
```
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.lexers import PygmentsLexer
from pygments.lexers.sql import SqlLexer

sql_completer = WordCompleter([
    'abort', 'action', 'add', 'after', 'all', 'alter', 'analyze', 'and',
    'as', 'asc', 'attach', 'autoincrement', 'before', 'begin', 'between',
    'by', 'cascade', 'case', 'cast', 'check', 'collate', 'column',
    'commit', 'conflict', 'constraint', 'create', 'cross', 'current_date',
    'current_time', 'current_timestamp', 'database', 'default',
    'deferrable', 'deferred', 'delete', 'desc', 'detach', 'distinct',
    'drop', 'each', 'else', 'end', 'escape', 'except', 'exclusive',
    'exists', 'explain', 'fail', 'for', 'foreign', 'from', 'full', 'glob',
    'group', 'having', 'if', 'ignore', 'immediate', 'in', 'index',
    'indexed', 'initially', 'inner', 'insert', 'instead', 'intersect',
    'into', 'is', 'isnull', 'join', 'key', 'left', 'like', 'limit',
    'match', 'natural', 'no', 'not', 'notnull', 'null', 'of', 'offset',
    'on', 'or', 'order', 'outer', 'plan', 'pragma', 'primary', 'query',
    'raise', 'recursive', 'references', 'regexp', 'reindex', 'release',
    'rename', 'replace', 'restrict', 'right', 'rollback', 'row',
    'savepoint', 'select', 'set', 'table', 'temp', 'temporary', 'then',
    'to', 'transaction', 'trigger', 'union', 'unique', 'update', 'using',
    'vacuum', 'values', 'view', 'virtual', 'when', 'where', 'with',
    'without'], ignore_case=True)

def main():
    session = PromptSession(
        lexer=PygmentsLexer(SqlLexer), completer=sql_completer)

    while True:
        try:
            text = session.prompt('> ')
        except KeyboardInterrupt:
            continue
        except EOFError:
            break
        else:
            print('You entered:', text)
    print('GoodBye!')

if __name__ == '__main__':
    main()
```

----------------------------------------

TITLE: Printing HTML Basic Tags with prompt_toolkit
DESCRIPTION: Illustrates how to use the `prompt_toolkit.formatted_text.HTML` class to print text formatted using basic HTML-like tags such as `<b>`, `<i>`, and `<u>` for bold, italic, and underline.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/printing_text.rst#_snippet_2

LANGUAGE: python
CODE:
```
from prompt_toolkit import print_formatted_text, HTML

print_formatted_text(HTML('<b>This is bold</b>'))
print_formatted_text(HTML('<i>This is italic</i>'))
print_formatted_text(HTML('<u>This is underlined</u>'))
```

----------------------------------------

TITLE: Testing PromptSession with Pipe Input and Dummy Output - Python
DESCRIPTION: This snippet demonstrates how to test a `PromptSession` by programmatically sending input via `create_pipe_input` and suppressing output using `DummyOutput`. It verifies that the session returns the expected result based on the provided input, including the necessary newline character to accept the prompt.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/advanced_topics/unit_testing.rst#_snippet_0

LANGUAGE: python
CODE:
```
from prompt_toolkit.shortcuts import PromptSession
from prompt_toolkit.input import create_pipe_input
from prompt_toolkit.output import DummyOutput

def test_prompt_session():
    with create_pipe_input() as inp:
        inp.send_text("hello\n")
        session = PromptSession(
            input=inp,
            output=DummyOutput(),
        )

        result = session.prompt()

    assert result == "hello"
```

----------------------------------------

TITLE: Defining Sequential Key Bindings in prompt_toolkit Python
DESCRIPTION: This snippet shows how to define a key binding that triggers only after a specific sequence of keys is pressed. The `@bindings.add` decorator is used with multiple arguments representing the sequence ('a' followed by 'b'). The binding function is executed only after the entire sequence is completed.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/advanced_topics/key_bindings.rst#_snippet_2

LANGUAGE: python
CODE:
```
@bindings.add('a', 'b')
def _(event):
    " Do something if 'a' is pressed and then 'b' is pressed. "
    ...
```

----------------------------------------

TITLE: Using Wildcards in Key Bindings in prompt_toolkit Python
DESCRIPTION: This snippet illustrates the use of the '<any>' wildcard in a key binding sequence. It allows a binding to match any key pressed immediately after a preceding key ('a'). The actual key pressed after 'a' can be inspected via the 'event' object.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/advanced_topics/key_bindings.rst#_snippet_4

LANGUAGE: python
CODE:
```
@bindings.add('a', '<any>')
def _(event):
    ...
```

----------------------------------------

TITLE: Using AppSession for Global Dummy Output - Python
DESCRIPTION: This example shows how to use `create_app_session` as a context manager to establish a global `DummyOutput` for a block of code. This is useful when you cannot easily pass input/output objects down the call stack and want all prompt_toolkit operations within the block to use the specified output device.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/advanced_topics/unit_testing.rst#_snippet_1

LANGUAGE: python
CODE:
```
from prompt_toolkit.application import create_app_session
from prompt_toolkit.shortcuts import print_formatted_text
from prompt_toolkit.output import DummyOutput

def test_something():
    with create_app_session(output=DummyOutput()):
        ...
        print_formatted_text('Hello world')
        ...
```

----------------------------------------

TITLE: Replacing Built-in Print with prompt_toolkit
DESCRIPTION: Shows how to import and alias `print_formatted_text` to replace the standard built-in `print` function, allowing formatted text support by default.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/printing_text.rst#_snippet_1

LANGUAGE: python
CODE:
```
from prompt_toolkit import print_formatted_text as print

print('Hello world')
```

----------------------------------------

TITLE: Creating Styles from a Dictionary in prompt_toolkit Python
DESCRIPTION: This snippet illustrates creating a prompt_toolkit Style object using a Python dictionary, which is suitable for Python 3.6+ where dictionary order is preserved. It shows how to initialize a prompt_toolkit Style object using the from_dict class method, passing a Python dictionary where keys are class name combinations (like 'header body left.text') and values are style strings.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/advanced_topics/styling.rst#_snippet_6

LANGUAGE: python
CODE:
```
from prompt_toolkit.styles import Style

style = Style.from_dict({
     'header body left.text': 'underline',
})
```

----------------------------------------

TITLE: Building Custom Layout with VSplit and Windows prompt_toolkit Python
DESCRIPTION: Demonstrates creating a custom prompt_toolkit layout using `VSplit` to divide the screen vertically. It combines a `Window` containing an editable `BufferControl`, a fixed-width `Window` displaying a vertical line, and another `Window` with a static `FormattedTextControl` showing text. The built layout is then used to instantiate and run a full-screen `Application`.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/full_screen_apps.rst#_snippet_1

LANGUAGE: python
CODE:
```
from prompt_toolkit import Application
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.layout.containers import VSplit, Window
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
from prompt_toolkit.layout.layout import Layout

buffer1 = Buffer()  # Editable buffer.

root_container = VSplit([
    # One window that holds the BufferControl with the default buffer on
    # the left.
    Window(content=BufferControl(buffer=buffer1)),

    # A vertical line in the middle. We explicitly specify the width, to
    # make sure that the layout engine will not try to divide the whole
    # width by three for all these windows. The window will simply fill its
    # content by repeating this character.
    Window(width=1, char='|'),

    # Display the text 'Hello world' on the right.
    Window(content=FormattedTextControl(text='Hello world')),
])

layout = Layout(root_container)

app = Application(layout=layout, full_screen=True)
app.run() # You won't be able to Exit this app
```

----------------------------------------

TITLE: Printing HTML with Custom Styles in prompt_toolkit
DESCRIPTION: Explains how to define a custom `prompt_toolkit.styles.Style` object to map HTML tag names (like `<aaa>`, `<bbb>`) to specific styles (colors, italics) and apply this style when printing `HTML` text.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/printing_text.rst#_snippet_5

LANGUAGE: python
CODE:
```
from prompt_toolkit import print_formatted_text, HTML
from prompt_toolkit.styles import Style

style = Style.from_dict({
    'aaa': '#ff0066',
    'bbb': '#44ff00 italic',
})

print_formatted_text(HTML('<aaa>Hello</aaa> <bbb>world</bbb>!'), style=style)
```

----------------------------------------

TITLE: Understanding Default Formatting for prompt_toolkit Progress Bar Python
DESCRIPTION: Displays the list of `Formatter` objects that constitute the default appearance of a `prompt_toolkit` progress bar. This serves as an example for customizing the appearance by creating a similar list and passing it to the `ProgressBar`. Requires importing formatters like `Label`, `Text`, `Percentage`, `Bar`, `Progress`, and `TimeLeft`.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/progress_bars.rst#_snippet_4

LANGUAGE: python
CODE:
```
from prompt_toolkit.shortcuts.progress_bar.formatters import *

default_formatting = [
        Label(),
        Text(' '),
        Percentage(),
        Text(' '),
        Bar(),
        Text(' '),
        Progress(),
        Text(' '),
        Text('eta [', style='class:time-left'),
        TimeLeft(),
        Text(']', style='class:time-left'),
        Text(' '),
    ]
```

----------------------------------------

TITLE: Defining Alt/Meta Key Bindings in prompt_toolkit Python
DESCRIPTION: This snippet explains how Alt/Meta key combinations are often translated by terminals into an Escape key followed by the desired character. It demonstrates defining a binding for 'alt-f' by creating a sequential binding for 'escape' followed by 'f'.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/advanced_topics/key_bindings.rst#_snippet_3

LANGUAGE: python
CODE:
```
@bindings.add('escape', 'f')
def _(event):
    " Do something if alt-f or meta-f have been pressed. "
```

----------------------------------------

TITLE: Customizing Formatting and Style of prompt_toolkit Progress Bar Python
DESCRIPTION: Shows how to create a custom list of `Formatter` objects and define a custom `Style` using `prompt_toolkit.styles.Style.from_dict` to change the visual appearance of the progress bar, mimicking an apt-get style. These custom objects are passed to the `ProgressBar` constructor. Requires `prompt_toolkit`, its formatters and styles, and `time`.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/progress_bars.rst#_snippet_5

LANGUAGE: python
CODE:
```
from prompt_toolkit.shortcuts import ProgressBar
from prompt_toolkit.styles import Style
from prompt_toolkit.shortcuts.progress_bar import formatters
import time

style = Style.from_dict({
        'label': 'bg:#ffff00 #000000',
        'percentage': 'bg:#ffff00 #000000',
        'current': '#448844',
        'bar': '',
    })


custom_formatters = [
        formatters.Label(),
        formatters.Text(': [', style='class:percentage'),
        formatters.Percentage(),
        formatters.Text(']', style='class:percentage'),
        formatters.Text(' '),
        formatters.Bar(sym_a='#', sym_b='#', sym_c='.'),
        formatters.Text('  '),
    ]

with ProgressBar(style=style, formatters=custom_formatters) as pb:
        for i in pb(range(1600), label='Installing'):
            time.sleep(.01)
```

----------------------------------------

TITLE: Displaying Progress for Multiple Parallel Tasks in prompt_toolkit Python
DESCRIPTION: Shows how to manage and display progress for multiple tasks executed in separate threads using one `ProgressBar`. Each thread iterates over a range, wrapped by the progress bar, and the main thread waits for them to complete using `join` with a timeout. Requires `prompt_toolkit`, `time`, and `threading`.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/progress_bars.rst#_snippet_2

LANGUAGE: python
CODE:
```
from prompt_toolkit.shortcuts import ProgressBar
import time
import threading


with ProgressBar() as pb:
        # Two parallel tasks.
        def task_1():
            for i in pb(range(100)):
                time.sleep(.05)

        def task_2():
            for i in pb(range(150)):
                time.sleep(.08)

        # Start threads.
        t1 = threading.Thread(target=task_1)
        t2 = threading.Thread(target=task_2)
        t1.daemon = True
        t2.daemon = True
        t1.start()
        t2.start()

        # Wait for the threads to finish. We use a timeout for the join() call,
        # because on Windows, join cannot be interrupted by Control-C or any other
        # signal.
        for t in [t1, t2]:
            while t.is_alive():
                t.join(timeout=.5)
```

----------------------------------------

TITLE: Printing Pygments Lexer Output with prompt_toolkit
DESCRIPTION: Demonstrates how to use a Pygments lexer (e.g., `PythonLexer`) to tokenize a code string and then print the resulting list of `(Token, text)` tuples using `PygmentsTokens`.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/printing_text.rst#_snippet_10

LANGUAGE: python
CODE:
```
import pygments
from pygments.token import Token
from pygments.lexers.python import PythonLexer

from prompt_toolkit.formatted_text import PygmentsTokens
from prompt_toolkit import print_formatted_text

# Printing the output of a pygments lexer.
tokens = list(pygments.lex('print("Hello")', lexer=PythonLexer()))
print_formatted_text(PygmentsTokens(tokens))
```

----------------------------------------

TITLE: Applying Styles to the Prompt Message with prompt_toolkit Python
DESCRIPTION: Demonstrates how to color the prompt string itself using a formatted message and a style dictionary. The message is a list of `(style_class, text)` tuples, and the style dictionary maps these class names to specific style definitions. This allows for creating complex, colored prompt prefixes.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/asking_for_input.rst#_snippet_7

LANGUAGE: python
CODE:
```
from prompt_toolkit.shortcuts import prompt
from prompt_toolkit.styles import Style

style = Style.from_dict({
    # User input (default text).
    "":          "#ff0066",

    # Prompt.
    "username": "#884444",
    "at":       "#00aa00",
    "colon":    "#0000aa",
    "pound":    "#00aa00",
    "host":     "#00ffff bg:#444400",
    "path":     "ansicyan underline",
})

message = [
    ("class:username", "john"),
    ("class:at",       "@"),
    ("class:host",     "localhost"),
    ("class:colon",    ":"),
    ("class:path",     "/user/john"),
    ("class:pound",    "# "),
]

text = prompt(message, style=style)
```

----------------------------------------

TITLE: Defining Layout Styles with Class Names in prompt_toolkit Python
DESCRIPTION: This snippet shows how to define a layout using VSplit and Window objects, assigning style class names (e.g., 'class:left', 'class:top', 'class:bottom') to individual controls. It then creates a Style object using a list of tuples, where each tuple associates a class name with a Pygments-like style string, allowing centralized control of styling based on logical roles.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/advanced_topics/styling.rst#_snippet_0

LANGUAGE: python
CODE:
```
from prompt_toolkit.layout import VSplit, Window
from prompt_toolkit.styles import Style

layout = VSplit([
    Window(BufferControl(...), style='class:left'),
    HSplit([
        Window(BufferControl(...), style='class:top'),
        Window(BufferControl(...), style='class:bottom'),
    ], style='class:right')
])

style = Style([
     ('left', 'bg:ansired'),
     ('top', 'fg:#00aaaa'),
     ('bottom', 'underline bold'),
 ])
```

----------------------------------------

TITLE: Assigning Multiple Style Classes in prompt_toolkit Python
DESCRIPTION: This snippet illustrates alternative syntaxes for assigning multiple class names to a prompt_toolkit UI element's style property. It shows using a comma-separated list ('class:left,bottom') and repeating the 'class:' prefix ('class:left class:bottom'), both achieving the same effect of applying styles associated with both specified classes.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/advanced_topics/styling.rst#_snippet_1

LANGUAGE: python
CODE:
```
Window(BufferControl(...), style='class:left,bottom'),
Window(BufferControl(...), style='class:left class:bottom'),
```

----------------------------------------

TITLE: Setting Different Cursor Shapes (Python)
DESCRIPTION: Demonstrates how to control the visual appearance of the cursor during input using the `cursor` parameter of the `prompt` function. It shows examples for various cursor shapes like BLOCK, UNDERLINE, BEAM, blinking variations, and using a `ModalCursorShapeConfig` for mode-dependent shapes in Vi mode. Requires `prompt_toolkit` and `prompt_toolkit.cursor_shapes`.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/asking_for_input.rst#_snippet_36

LANGUAGE: python
CODE:
```
from prompt_toolkit import prompt
from prompt_toolkit.cursor_shapes import CursorShape, ModalCursorShapeConfig

# Several possible values for the `cursor_shape_config` parameter:
prompt(">", cursor=CursorShape.BLOCK)
prompt(">", cursor=CursorShape.UNDERLINE)
prompt(">", cursor=CursorShape.BEAM)
prompt(">", cursor=CursorShape.BLINKING_BLOCK)
prompt(">", cursor=CursorShape.BLINKING_UNDERLINE)
prompt(">", cursor=CursorShape.BLINKING_BEAM)
prompt(">", cursor=ModalCursorShapeConfig())
```

----------------------------------------

TITLE: Connect and Execute SQL via sqlite3
DESCRIPTION: This Python snippet integrates the `sqlite3` library to connect to an SQLite database. It attempts to execute the user's input as an SQL command within the REPL loop using `connection.execute()` and prints fetched results or handles errors.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/tutorials/repl.rst#_snippet_6

LANGUAGE: python
CODE:
```
#!/usr/bin/env python
import sys
import sqlite3

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.lexers import PygmentsLexer
from prompt_toolkit.styles import Style
from pygments.lexers.sql import SqlLexer

sql_completer = WordCompleter([
    'abort', 'action', 'add', 'after', 'all', 'alter', 'analyze', 'and',
    'as', 'asc', 'attach', 'autoincrement', 'before', 'begin', 'between',
    'by', 'cascade', 'case', 'cast', 'check', 'collate', 'column',
    'commit', 'conflict', 'constraint', 'create', 'cross', 'current_date',
    'current_time', 'current_timestamp', 'database', 'default',
    'deferrable', 'deferred', 'delete', 'desc', 'detach', 'distinct',
```

----------------------------------------

TITLE: Enabling Complete While Typing Option - Python
DESCRIPTION: Configures the `prompt` function to automatically suggest completions as the user types, without requiring the tab key. It highlights that this option is incompatible with `enable_history_search`.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/asking_for_input.rst#_snippet_14

LANGUAGE: python
CODE:
```
text = prompt(
    "Enter HTML: ",
    completer=my_completer,
    complete_while_typing=True
)
```

----------------------------------------

TITLE: Loading Pygments Styles into prompt_toolkit Python
DESCRIPTION: This snippet demonstrates how to load a predefined style from the Pygments library and convert it for use with prompt_toolkit. It uses pygments.styles.get_style_by_name to fetch a Pygments style class (e.g., 'monokai') and then prompt_toolkit.styles.pygments.style_from_pygments_cls to convert it into a prompt_toolkit.styles.Style object that can be passed to the Application.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/advanced_topics/styling.rst#_snippet_7

LANGUAGE: python
CODE:
```
from prompt_toolkit.styles.pygments import style_from_pygments_cls
from pygments.styles import get_style_by_name

style = style_from_pygments_cls(get_style_by_name('monokai'))
```

----------------------------------------

TITLE: Disabling Validate While Typing Option - Python
DESCRIPTION: Configures the `prompt` function to perform validation only after the user presses the Enter key, instead of validating in real-time as the user types.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/asking_for_input.rst#_snippet_17

LANGUAGE: python
CODE:
```
prompt(
    "Give a number: ",
    validator=NumberValidator(),
    validate_while_typing=False
)
```

----------------------------------------

TITLE: Using Async Prompt in Asyncio (Python)
DESCRIPTION: Provides an example of how to integrate prompt-toolkit into an `asyncio` application using the awaitable `prompt_async` method of `PromptSession`. This prevents blocking the asyncio event loop. The example also shows using `patch_stdout` as a recommended context manager to protect the prompt from output by other coroutines. Requires `prompt_toolkit` and `prompt_toolkit.patch_stdout`.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/asking_for_input.rst#_snippet_37

LANGUAGE: python
CODE:
```
from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout

async def my_coroutine():
    session = PromptSession()
    while True:
        with patch_stdout():
            result = await session.prompt_async("Say something: ")
        print(f"You said: {result}")
```

----------------------------------------

TITLE: Instantiating Buffer and Window in prompt_toolkit Python
DESCRIPTION: This snippet demonstrates the fundamental setup for displaying text in `prompt_toolkit`. It imports necessary classes like `Buffer`, `BufferControl`, and `Window`, creates a `Buffer` to hold text, and then wraps a `BufferControl` (configured to display the buffer) within a `Window`. This structure is the starting point for the rendering process described in the text.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/advanced_topics/rendering_flow.rst#_snippet_0

LANGUAGE: python
CODE:
```
from prompt_toolkit.enums import DEFAULT_BUFFER
from prompt_toolkit.layout.containers import Window
from prompt_toolkit.layout.controls import BufferControl
from prompt_toolkit.buffer import Buffer

b = Buffer(name=DEFAULT_BUFFER)
Window(content=BufferControl(buffer=b))
```

----------------------------------------

TITLE: Defining Custom Input Styles with prompt_toolkit in Python
DESCRIPTION: Explains how to create a custom style using `Style.from_dict` by providing a dictionary mapping token types (like 'pygments.comment' or 'pygments.keyword') to style strings. This custom style is then passed to the `style` parameter of the `prompt` function. The dictionary format is similar to Pygments styles but with prompt_toolkit specific additions.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/asking_for_input.rst#_snippet_4

LANGUAGE: python
CODE:
```
from pygments.lexers.html import HtmlLexer
from prompt_toolkit.shortcuts import prompt
from prompt_toolkit.styles import Style
from prompt_toolkit.lexers import PygmentsLexer

our_style = Style.from_dict({
    "pygments.comment": "#888888 bold",
    "pygments.keyword": "#ff88ff bold",
})

text = prompt(
    "Enter HTML: ",
    lexer=PygmentsLexer(HtmlLexer),
    style=our_style
)
```

----------------------------------------

TITLE: Running SQLite REPL and Argument Handling - Python
DESCRIPTION: This block serves as the application's entry point when the script is executed directly. It checks the command-line arguments (`sys.argv`) to determine the database file path. If no arguments are provided (beyond the script name), it defaults to using an in-memory SQLite database (':memory:'). Finally, it calls the `main` function with the selected database path to initiate the REPL.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/tutorials/repl.rst#_snippet_10

LANGUAGE: python
CODE:
```
if __name__ == '__main__':
        if len(sys.argv) < 2:
            db = ':memory:'
        else:
            db = sys.argv[1]

        main(db)
```

----------------------------------------

TITLE: Pytest Fixture for Mocked Input/Output - Python
DESCRIPTION: This pytest fixture provides a reusable setup for testing prompt_toolkit applications. It uses `create_pipe_input` for simulated input, `DummyOutput` for suppressed output, and wraps the test execution within an `AppSession` that uses these mock devices. The fixture yields the pipe input object, allowing tests to send arbitrary text.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/advanced_topics/unit_testing.rst#_snippet_2

LANGUAGE: python
CODE:
```
import pytest
from prompt_toolkit.application import create_app_session
from prompt_toolkit.input import create_pipe_input
from prompt_toolkit.output import DummyOutput

@pytest.fixture(autouse=True, scope="function")
def mock_input():
    with create_pipe_input() as pipe_input:
        with create_app_session(input=pipe_input, output=DummyOutput()):
            yield pipe_input
```

----------------------------------------

TITLE: Initialize Prompt Toolkit Application with Brightness Transformation - Python
DESCRIPTION: This snippet shows how to apply an `AdjustBrightnessStyleTransformation` to a `prompt_toolkit.Application` instance. It configures the transformation to increase the minimum brightness level, which is useful for improving visibility on dark terminal backgrounds.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/advanced_topics/styling.rst#_snippet_11

LANGUAGE: python
CODE:
```
from prompt_toolkit.styles import AdjustBrightnessStyleTransformation

app = Application(
    style_transformation=AdjustBrightnessStyleTransformation(
        min_brightness=0.5,  # Increase the minimum brightness.
        max_brightness=1.0,
    )
    # ...
)
```

----------------------------------------

TITLE: Using to_filter Utility - prompt_toolkit Python
DESCRIPTION: Illustrates the use of `prompt_toolkit`'s `to_filter` utility function, which takes either a boolean value (True/False) or an actual `Filter` instance and consistently returns a `Filter` instance. This is useful for designing APIs that need to accept both static boolean states and dynamic filter objects interchangeably.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/advanced_topics/filters.rst#_snippet_5

LANGUAGE: python
CODE:
```
from prompt_toolkit.filters.utils import to_filter
from prompt_toolkit.filters import Condition, has_search, has_selection

# In each of the following three examples, 'f' will be a `Filter`
# instance.
f = to_filter(True)
f = to_filter(False)
f = to_filter(Condition(lambda: True))
f = to_filter(has_search | has_selection)
```

----------------------------------------

TITLE: Using a Pygments Style Class with prompt_toolkit in Python
DESCRIPTION: Demonstrates how to use a Pygments style class directly, like `TangoStyle`, by wrapping it with `style_from_pygments_cls`. The resulting style object is then passed to the `style` parameter of the `prompt` function. This allows applying a complete Pygments color scheme to the input text when combined with a lexer.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/asking_for_input.rst#_snippet_5

LANGUAGE: python
CODE:
```
from prompt_toolkit.shortcuts import prompt
from prompt_toolkit.styles import style_from_pygments_cls
from prompt_toolkit.lexers import PygmentsLexer
from pygments.styles.tango import TangoStyle
from pygments.lexers.html import HtmlLexer

tango_style = style_from_pygments_cls(TangoStyle)

text = prompt(
    "Enter HTML: ", 
    lexer=PygmentsLexer(HtmlLexer),
    style=tango_style
)
```

----------------------------------------

TITLE: Applying a Specific Pygments Style in prompt_toolkit Python Prompt
DESCRIPTION: Shows how to use a specific Pygments style, like 'monokai', for syntax highlighting in a prompt. The Pygments style is wrapped using `style_from_pygments_cls` and passed to the `style` parameter. Setting `include_default_pygments_style=False` prevents merging with the built-in default style.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/asking_for_input.rst#_snippet_3

LANGUAGE: python
CODE:
```
from pygments.lexers.html import HtmlLexer
from pygments.styles import get_style_by_name
from prompt_toolkit.shortcuts import prompt
from prompt_toolkit.lexers import PygmentsLexer
from prompt_toolkit.styles.pygments import style_from_pygments_cls

style = style_from_pygments_cls(get_style_by_name("monokai"))
text = prompt(
    "Enter HTML: ",
    lexer=PygmentsLexer(HtmlLexer),
    style=style,
    include_default_pygments_style=False
)
print(f"You said: {text}")
```

----------------------------------------

TITLE: Merging Pygments and Custom Styles in prompt_toolkit Python
DESCRIPTION: Shows how to combine multiple styles using `merge_styles`. This example merges a full Pygments style (Tango) with a custom style defined via `Style.from_dict`. The merged style is then applied to the prompt, allowing for a base theme overridden or extended by specific custom rules.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/asking_for_input.rst#_snippet_6

LANGUAGE: python
CODE:
```
from prompt_toolkit.shortcuts import prompt
from prompt_toolkit.styles import Style, style_from_pygments_cls, merge_styles
from prompt_toolkit.lexers import PygmentsLexer

from pygments.styles.tango import TangoStyle
from pygments.lexers.html import HtmlLexer

our_style = merge_styles([
    style_from_pygments_cls(TangoStyle),
    Style.from_dict({
        "pygments.comment": "#888888 bold",
        "pygments.keyword": "#ff88ff bold",
    })
])

text = prompt(
    "Enter HTML: ",
    lexer=PygmentsLexer(HtmlLexer),
    style=our_style
)
```

----------------------------------------

TITLE: Styling Individual Completions in prompt_toolkit - Python
DESCRIPTION: Illustrates how to customize the appearance of individual completion suggestions in the prompt_toolkit menu. It shows examples using ANSI color codes, simple style names, and style class names for lookup in a stylesheet.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/asking_for_input.rst#_snippet_12

LANGUAGE: python
CODE:
```
from prompt_toolkit.completion import Completer, Completion

class MyCustomCompleter(Completer):
    def get_completions(self, document, complete_event):
        # Display this completion, black on yellow.
        yield Completion(
            "completion1",
            start_position=0,
            style="bg:ansiyellow fg:ansiblack"
        )

        # Underline completion.
        yield Completion(
            "completion2",
            start_position=0,
            style="underline"
        )

        # Specify class name, which will be looked up in the style sheet.
        yield Completion(
            "completion3",
            start_position=0,
            style="class:special-completion"
        )
```

----------------------------------------

TITLE: Converting to Formatted Text with prompt_toolkit
DESCRIPTION: Introduces the `prompt_toolkit.formatted_text.to_formatted_text` function, which converts various inputs (like `HTML` objects) into a standard formatted text representation, allowing an additional style to be applied during conversion.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/printing_text.rst#_snippet_12

LANGUAGE: python
CODE:
```
from prompt_toolkit.formatted_text import to_formatted_text, HTML
from prompt_toolkit import print_formatted_text

html = HTML('<aaa>Hello</aaa> <bbb>world</bbb>!')
text = to_formatted_text(html, style='class:my_html bg:#00ff00 italic')

print_formatted_text(text)
```

----------------------------------------

TITLE: Styling Pygments Tokens with prompt_toolkit
DESCRIPTION: Explains how Pygments tokens are mapped to prompt_toolkit class names and shows how to define a `Style` object to customize the appearance of specific Pygments token types.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/printing_text.rst#_snippet_11

LANGUAGE: python
CODE:
```
from prompt_toolkit.styles import Style

style = Style.from_dict({
    'pygments.keyword': 'underline',
    'pygments.literal.string': 'bg:#00ff00 #ffffff',
})
print_formatted_text(PygmentsTokens(tokens), style=style)
```

----------------------------------------

TITLE: Defining Eager Key Bindings in prompt_toolkit Python
DESCRIPTION: This snippet demonstrates how to define multiple key bindings, including one marked with `eager=True`. An eager binding triggers immediately upon its key match, preventing the system from waiting for longer potential matches, which is useful for overriding default behaviors or creating immediate actions.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/advanced_topics/key_bindings.rst#_snippet_8

LANGUAGE: Python
CODE:
```
@bindings.add('a', 'b')
def binding_1(event):
    ...

@bindings.add('a', eager=True)
def binding_2(event):
    ...
```

----------------------------------------

TITLE: Defining prompt-toolkit Styles - Python
DESCRIPTION: Sets up the visual appearance for various components of the `prompt_toolkit` user interface using `Style.from_dict`. It specifies background and foreground colors for the completion menu items (normal and current selection) and scrollbar elements, customizing the look and feel of the REPL.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/tutorials/repl.rst#_snippet_8

LANGUAGE: python
CODE:
```
style = Style.from_dict({
        'completion-menu.completion': 'bg:#008888 #ffffff',
        'completion-menu.completion.current': 'bg:#00aaaa #000000',
        'scrollbar.background': 'bg:#88aaaa',
        'scrollbar.button': 'bg:#222222',
    })
```

----------------------------------------

TITLE: Adding Title and Label to prompt_toolkit Progress Bar in Python
DESCRIPTION: Explains how to customize the progress bar by setting a `title` for the overall display and a `label` for individual tasks using `prompt_toolkit.formatted_text.HTML` for rich formatting. The example shows colored text in the title and label. Requires `prompt_toolkit`, `HTML`, and `time`.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/progress_bars.rst#_snippet_3

LANGUAGE: python
CODE:
```
from prompt_toolkit.shortcuts import ProgressBar
from prompt_toolkit.formatted_text import HTML
import time

title = HTML('Downloading <style bg="yellow" fg="black">4 files...<\/style>')
label = HTML('<ansired>some file<\/ansired>: ')

with ProgressBar(title=title) as pb:
        for i in pb(range(800), label=label):
            time.sleep(.01)
```

----------------------------------------

TITLE: Creating Validator from Callable Function - Python
DESCRIPTION: Provides an alternative, simpler way to create a validator using a standard function that returns a boolean (`True` for valid, `False` for invalid). It uses `Validator.from_callable`, allowing specification of a default error message and cursor behavior.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/asking_for_input.rst#_snippet_18

LANGUAGE: python
CODE:
```
from prompt_toolkit.validation import Validator
from prompt_toolkit import prompt

def is_number(text):
    return text.isdigit()

validator = Validator.from_callable(
    is_number,
    error_message="This input contains non-numeric characters",
    move_cursor_to_end=True
)

number = int(prompt("Give a number: ", validator=validator))
print(f"You said: {number}")
```

----------------------------------------

TITLE: Adding Dynamic Bottom Toolbar with Styled Text (Python)
DESCRIPTION: This snippet demonstrates creating a dynamic bottom toolbar using a callable that returns a list of `(style, text)` tuples. It also shows how to define custom styles for elements like the toolbar using `prompt_toolkit.styles.Style`.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/asking_for_input.rst#_snippet_23

LANGUAGE: python
CODE:
```
from prompt_toolkit import prompt
from prompt_toolkit.styles import Style

def bottom_toolbar():
    return [("class:bottom-toolbar", " This is a toolbar. ")]

style = Style.from_dict({
    "bottom-toolbar": "#ffffff bg:#333333",
})

text = prompt("> ", bottom_toolbar=bottom_toolbar, style=style)
print(f"You said: {text}")
```

----------------------------------------

TITLE: Enabling 24bit True Color in prompt_toolkit Python Prompt
DESCRIPTION: Shows how to activate 24-bit true color output for the prompt. This is achieved by passing the `color_depth` parameter with the value `ColorDepth.TRUE_COLOR` to the `prompt` function. This provides access to a wider range of colors beyond the standard 256-color palette if the terminal supports it.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/asking_for_input.rst#_snippet_8

LANGUAGE: python
CODE:
```
from prompt_toolkit.output import ColorDepth

text = prompt(message, style=style, color_depth=ColorDepth.TRUE_COLOR)
```

----------------------------------------

TITLE: Styling Dialogs with Prompt Toolkit Styles and HTML
DESCRIPTION: Demonstrates how to apply custom styling to a dialog using a Style object created with Style.from_dict and how to use HTML objects for styled text within the dialog title. The style argument is passed to the dialog function.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/dialogs.rst#_snippet_6

LANGUAGE: python
CODE:
```
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.shortcuts import message_dialog
from prompt_toolkit.styles import Style

example_style = Style.from_dict({
    'dialog':             'bg:#88ff88',
    'dialog frame.label': 'bg:#ffffff #000000',
    'dialog.body':        'bg:#000000 #00ff00',
    'dialog shadow':      'bg:#00aa00',
})

message_dialog(
    title=HTML('<style bg="blue" fg="white">Styled</style> '
               '<style fg="ansired">dialog</style> window'),
    text='Do you want to continue?\nPress ENTER to quit.',
    style=example_style).run()
```

----------------------------------------

TITLE: Initializing prompt_toolkit Application with KeyBindings - Python
DESCRIPTION: Shows the basic setup for a prompt_toolkit application that uses key bindings. It creates a `KeyBindings` object, initializes the `Application` with this object, and then starts the application's event loop using `app.run()`. This is the fundamental structure for adding interactive key commands.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/full_screen_apps.rst#_snippet_3

LANGUAGE: python
CODE:
```
from prompt_toolkit import Application
from prompt_toolkit.key_binding import KeyBindings

kb = KeyBindings()
app = Application(key_bindings=kb)
app.run()
```

----------------------------------------

TITLE: Customizing Multiline Prompt Continuation (Python)
DESCRIPTION: This snippet demonstrates how to provide a custom continuation prompt for multiline input using a callable function. The function receives the required width, line number, and soft wrap status and should return formatted text.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/asking_for_input.rst#_snippet_31

LANGUAGE: python
CODE:
```
from prompt_toolkit import prompt

def prompt_continuation(width, line_number, is_soft_wrap):
    return "." * width
    # Or: return [("", "." * width)]

prompt(
    "multiline input> ",
    multiline=True,
    prompt_continuation=prompt_continuation
)
```

----------------------------------------

TITLE: Handling SIGINT Signal with prompt_toolkit Key Binding Python
DESCRIPTION: This snippet demonstrates how to define a key binding specifically for the `<sigint>` signal. This allows the application to execute custom code when a SIGINT signal is received from an external source, distinct from handling the 'c-c' key press which is handled separately in raw terminal mode.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/advanced_topics/key_bindings.rst#_snippet_11

LANGUAGE: Python
CODE:
```
@bindings.add('<sigint>')
def _(event):
    # ...
    pass
```

----------------------------------------

TITLE: Adding Dynamic Right Prompt (RPROMPT) with Styling (Python)
DESCRIPTION: This example illustrates how to add a dynamic right prompt (RPROMPT), similar to ZSH, to the prompt. It uses a callable function to generate the prompt content and applies a custom style definition.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/asking_for_input.rst#_snippet_24

LANGUAGE: python
CODE:
```
from prompt_toolkit import prompt
from prompt_toolkit.styles import Style

example_style = Style.from_dict({
    "rprompt": "bg:#ff0066 #ffffff",
})

def get_rprompt():
    return "<rprompt>"

answer = prompt("> ", rprompt=get_rprompt, style=example_style)
```

----------------------------------------

TITLE: Conditionally Importing Event Loop - Python
DESCRIPTION: This code demonstrates how to conditionally import the appropriate get_event_loop function based on the prompt_toolkit version. Version 3.0 uses the standard asyncio event loop, while version 2.0 used a prompt_toolkit specific implementation. Using the PTK3 flag ensures the correct import is used.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/upgrading/3.0.rst#_snippet_1

LANGUAGE: python
CODE:
```
if PTK3:
    from asyncio import get_event_loop
else:
    from prompt_toolkit.eventloop import get_event_loop
```

----------------------------------------

TITLE: Printing (classname, text) Tuples with Styles in prompt_toolkit
DESCRIPTION: Illustrates using a list of `(classname, text)` tuples with `FormattedText` and applying styles defined in a separate `Style` object to map class names to specific visual styles.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/printing_text.rst#_snippet_8

LANGUAGE: python
CODE:
```
from prompt_toolkit import print_formatted_text
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.styles import Style

# The text.
text = FormattedText([
    ('class:aaa', 'Hello'),
    ('', ' '),
    ('class:bbb', 'World'),
])

# The style sheet.
style = Style.from_dict({
    'aaa': '#ff0066',
    'bbb': '#44ff00 italic',
})

print_formatted_text(text, style=style)
```

----------------------------------------

TITLE: Setting prompt_toolkit Application Color Depth Manually in Python
DESCRIPTION: This snippet demonstrates explicitly setting the color depth for a prompt_toolkit Application instance. It imports ColorDepth from prompt_toolkit.output.color_depth and passes a specific depth value (e.g., ColorDepth.ANSI_COLORS_ONLY) to the color_depth parameter when instantiating the Application class, overriding any environment variable setting for this instance.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/advanced_topics/styling.rst#_snippet_10

LANGUAGE: python
CODE:
```
from prompt_toolkit.output.color_depth import ColorDepth

app = Application(
    color_depth=ColorDepth.ANSI_COLORS_ONLY,
    # ...
)
```

----------------------------------------

TITLE: Disabling Line Wrapping in Prompt (Python)
DESCRIPTION: Illustrates how to disable the default line wrapping behavior in a prompt-toolkit input. When line wrapping is disabled using `wrap_lines=False`, the input string will scroll horizontally instead of wrapping to the next line, similar to older command-line interfaces. Requires `prompt_toolkit`.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/asking_for_input.rst#_snippet_34

LANGUAGE: python
CODE:
```
from prompt_toolkit import prompt

prompt("What is your name: ", wrap_lines=False)
```

----------------------------------------

TITLE: Using HTML for Completion Display Text - Python
DESCRIPTION: Demonstrates the use of `prompt_toolkit.formatted_text.HTML` to create rich, styled display text for a completion item. It shows how the `display` attribute can be combined with the standard `style` attribute for more complex visual presentations.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/asking_for_input.rst#_snippet_13

LANGUAGE: python
CODE:
```
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.formatted_text import HTML

class MyCustomCompleter(Completer):
    def get_completions(self, document, complete_event):
        yield Completion(
            "completion1",
            start_position=0,
            display=HTML("<b>completion</b><ansired>1</ansired>"),
            style="bg:ansiyellow"
        )
```

----------------------------------------

TITLE: Synchronous Dialog Execution (v3/v2) - Python
DESCRIPTION: This code demonstrates how to handle synchronous dialog execution conditionally for prompt_toolkit versions 2.0 and 3.0. In version 3, the dialog function returns an Application object, and `.run()` must be called to display it; in version 2, the function directly returns the result.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/upgrading/3.0.rst#_snippet_6

LANGUAGE: python
CODE:
```
if PTK3:
    result = input_dialog(title='...', text='...').run()
else:
    result = input_dialog(title='...', text='...')
```

----------------------------------------

TITLE: Using PromptSession with FileHistory - Python
DESCRIPTION: Shows how to configure `PromptSession` to use a persistent history that is saved to a file. By passing a `FileHistory` instance with a specified file path, previously entered commands will be loaded on startup and saved on exit.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/asking_for_input.rst#_snippet_20

LANGUAGE: python
CODE:
```
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory

session = PromptSession(history=FileHistory("~/.myhistory"))

while True:
    session.prompt()
```

----------------------------------------

TITLE: Excluding Key Binding from Macro Recording in prompt_toolkit Python
DESCRIPTION: This snippet illustrates how to define a key binding ('c-t') that is excluded from macro recording by setting the `record_in_macro` parameter to `False`. This means the action will execute, but the key press will not be added to the macro sequence being recorded.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/advanced_topics/key_bindings.rst#_snippet_10

LANGUAGE: Python
CODE:
```
@bindings.add('c-t', record_in_macro=False)
def _(event):
    # ...
    pass
```

----------------------------------------

TITLE: PromptSession Asynchronous Call (v2) - Python
DESCRIPTION: This snippet shows the syntax used in prompt_toolkit version 2.0 for making asynchronous prompt calls within an asyncio application. The `async_=True` parameter was used to enable asynchronous behavior, which has been removed in version 3.0.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/upgrading/3.0.rst#_snippet_3

LANGUAGE: python
CODE:
```
# For 2.0
result = await PromptSession().prompt('Say something: ', async_=True)
```

----------------------------------------

TITLE: Creating Condition Filter with Lambda - prompt_toolkit Python
DESCRIPTION: Shows how to instantiate a `prompt_toolkit` `Condition` filter by passing a lambda function that evaluates a dynamic boolean value from the application state. This filter dynamically checks if the application is currently in a searching state by calling `get_app().is_searching`.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/advanced_topics/filters.rst#_snippet_0

LANGUAGE: python
CODE:
```
from prompt_toolkit.application.current import get_app
from prompt_toolkit.filters import Condition

is_searching = Condition(lambda: get_app().is_searching)
```

----------------------------------------

TITLE: Printing ANSI Escape Sequences with prompt_toolkit
DESCRIPTION: Shows how to use the `prompt_toolkit.formatted_text.ANSI` class to parse and print text containing VT100 ANSI escape sequences, making them work correctly even on terminals that don't natively support them.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/printing_text.rst#_snippet_6

LANGUAGE: python
CODE:
```
from prompt_toolkit import print_formatted_text, ANSI

print_formatted_text(ANSI('\x1b[31mhello \x1b[32mworld'))
```

----------------------------------------

TITLE: Removing Explicit Asyncio Integration (v2) - Python
DESCRIPTION: In prompt_toolkit version 2.0, it was necessary to explicitly tell the library to use the asyncio event loop using these lines. Since version 3.0 uses asyncio natively by default, these lines should be removed when upgrading.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/upgrading/3.0.rst#_snippet_2

LANGUAGE: python
CODE:
```
from prompt_toolkit.eventloop.defaults import use_asyncio_event_loop
use_asyncio_event_loop()
```

----------------------------------------

TITLE: Evaluating Filter State - prompt_toolkit Python
DESCRIPTION: Demonstrates how to retrieve the current boolean value of a `prompt_toolkit` filter instance, like `is_searching`, by simply calling it directly as if it were a function. Executing the filter in this way evaluates its underlying expression or function and returns the current boolean result.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/advanced_topics/filters.rst#_snippet_3

LANGUAGE: python
CODE:
```
print(is_searching())
```

----------------------------------------

TITLE: Displaying Simple Progress Bar with prompt_toolkit Python
DESCRIPTION: Shows how to wrap a simple iterable like `range` with the `ProgressBar` context manager to display progress. It pauses briefly in each iteration using `time.sleep(0.01)`. Requires `prompt_toolkit` and the `time` module.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/progress_bars.rst#_snippet_0

LANGUAGE: python
CODE:
```
from prompt_toolkit.shortcuts import ProgressBar
import time


with ProgressBar() as pb:
    for i in pb(range(800)):
        time.sleep(.01)
```

----------------------------------------

TITLE: Printing Pygments Tokens Manually with prompt_toolkit
DESCRIPTION: Shows how to manually create a list of `(pygments.Token, text)` tuples representing formatted code and print it using `prompt_toolkit.formatted_text.PygmentsTokens`.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/printing_text.rst#_snippet_9

LANGUAGE: python
CODE:
```
from pygments.token import Token
from prompt_toolkit import print_formatted_text
from prompt_toolkit.formatted_text import PygmentsTokens

text = [
    (Token.Keyword, 'print'),
    (Token.Punctuation, '('),
    (Token.Literal.String.Double, '"'),
    (Token.Literal.String.Double, 'hello'),
    (Token.Literal.String.Double, '"'),
    (Token.Punctuation, ')'),
    (Token.Text, '\n'),
]

print_formatted_text(PygmentsTokens(text))
```

----------------------------------------

TITLE: Printing (style, text) Tuples with prompt_toolkit
DESCRIPTION: Demonstrates creating formatted text directly as a list of `(style, text)` tuples and printing it using `prompt_toolkit.formatted_text.FormattedText`, allowing precise control over styling segments.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/printing_text.rst#_snippet_7

LANGUAGE: python
CODE:
```
from prompt_toolkit import print_formatted_text
from prompt_toolkit.formatted_text import FormattedText

text = FormattedText([
    ('#ff0066', 'Hello'),
    ('', ' '),
    ('#44ff00 italic', 'World'),
])

print_formatted_text(text)
```

----------------------------------------

TITLE: Adding Dynamic Bottom Toolbar with HTML (Python)
DESCRIPTION: This example shows how to add a dynamic bottom toolbar to the prompt using a callable function that returns an `HTML` object. The function is called each time the prompt is rendered, allowing the toolbar content to change dynamically.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/asking_for_input.rst#_snippet_22

LANGUAGE: python
CODE:
```
from prompt_toolkit import prompt
from prompt_toolkit.formatted_text import HTML

def bottom_toolbar():
    return HTML("This is a <b><style bg=\"ansired\">Toolbar<\/style><\/b>!")

text = prompt("> ", bottom_toolbar=bottom_toolbar)
print(f"You said: {text}")
```

----------------------------------------

TITLE: Running Completion in Background Thread - Python
DESCRIPTION: Enables asynchronous completion by executing the completer's `get_completions` method in a separate thread. This prevents blocking the event loop when completion generation is time-consuming.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/asking_for_input.rst#_snippet_15

LANGUAGE: python
CODE:
```
text = prompt("> ", completer=MyCustomCompleter(), complete_in_thread=True)
```

----------------------------------------

TITLE: Setting Prompt Input Mode to Vi (Python)
DESCRIPTION: This simple snippet shows how to configure the `prompt_toolkit` prompt to use Vi key bindings instead of the default Emacs bindings by passing the `vi_mode=True` argument.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/asking_for_input.rst#_snippet_25

LANGUAGE: python
CODE:
```
from prompt_toolkit import prompt

prompt("> ", vi_mode=True)
```

----------------------------------------

TITLE: Enabling Multiline Input in Prompt (Python)
DESCRIPTION: This simple example shows how to enable multiline input for the prompt by setting the `multiline=True` parameter. Note that enabling multiline input changes the default behavior of the Enter key.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/asking_for_input.rst#_snippet_30

LANGUAGE: python
CODE:
```
from prompt_toolkit import prompt

prompt("> ", multiline=True)
```

----------------------------------------

TITLE: Focusing a prompt_toolkit Window - Python
DESCRIPTION: Demonstrates how to programmatically change the focus to a specific Window object within the prompt_toolkit application's layout. It retrieves the current application instance using `get_app()` and then calls the layout's `focus()` method, passing the target window.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/full_screen_apps.rst#_snippet_2

LANGUAGE: python
CODE:
```
from prompt_toolkit.application import get_app

# This window was created earlier.
w = Window()

# ...

# Now focus it.
get_app().layout.focus(w)
```

----------------------------------------

TITLE: Defining Style Rules for Dotted Class Names in prompt_toolkit Python
DESCRIPTION: This snippet illustrates how to define a style rule in a Style object that targets a specific class name using dot notation. It demonstrates creating a style rule within a prompt_toolkit Style object where the rule's key is a dotted class name ('a.b.c'). This rule's style ('underline') will be applied to any UI element that has been assigned the exact class name 'a.b.c', respecting the dot notation hierarchy as explained in the text.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/advanced_topics/styling.rst#_snippet_4

LANGUAGE: python
CODE:
```
style = Style([
     ('a.b.c', 'underline'),
 ])
```

----------------------------------------

TITLE: Installing Prompt Toolkit using Pip - Shell
DESCRIPTION: Provides the standard command to install the prompt_toolkit library using the Python package manager, pip. This is the most common method for installing Python libraries.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/README.rst#_snippet_0

LANGUAGE: Shell
CODE:
```
pip install prompt_toolkit
```

----------------------------------------

TITLE: Installing Prompt Toolkit using Conda - Shell
DESCRIPTION: Provides the command to install the prompt_toolkit library using the Conda package manager. This command specifies the 'conda-forge' channel.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/README.rst#_snippet_1

LANGUAGE: Shell
CODE:
```
conda install -c https://conda.anaconda.org/conda-forge prompt_toolkit
```

----------------------------------------

TITLE: Basic Printing with prompt_toolkit
DESCRIPTION: Demonstrates the basic usage of the `prompt_toolkit.print_formatted_text` function to print a simple string without any special formatting.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/printing_text.rst#_snippet_0

LANGUAGE: python
CODE:
```
from prompt_toolkit import print_formatted_text

print_formatted_text('Hello world')
```

----------------------------------------

TITLE: Install prompt_toolkit using pip
DESCRIPTION: This command installs the prompt_toolkit library using pip, which is required to run the code examples in this tutorial.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/tutorials/repl.rst#_snippet_0

LANGUAGE: bash
CODE:
```
pip install prompt_toolkit
```

----------------------------------------

TITLE: Setting up prompt_toolkit Input Hook (Python)
DESCRIPTION: This snippet demonstrates the basic structure for defining and setting an input hook in prompt_toolkit. It shows importing the necessary function, defining a placeholder `inputhook` function that would contain the logic for running the external loop, and then activating the hook using `set_eventloop_with_inputhook`. The `inputhook_context` provides information like a file descriptor to monitor for readiness.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/advanced_topics/input_hooks.rst#_snippet_0

LANGUAGE: python
CODE:
```
from prompt_toolkit.eventloop.inputhook import set_eventloop_with_inputhook

def inputhook(inputhook_context):
    # At this point, we run the other loop. This loop is supposed to run
    # until either `inputhook_context.fileno` becomes ready for reading or
    # `inputhook_context.input_is_ready()` returns True.

    # A good way is to register this file descriptor in this other event
    # loop with a callback that stops this loop when this FD becomes ready.
    # There is no need to actually read anything from the FD.

    while True:
        ...

set_eventloop_with_inputhook(inputhook)

# Any asyncio code at this point will now use this new loop, with input
# hook installed.
```

----------------------------------------

TITLE: Dynamically Toggling Emacs/Vi Mode and Displaying State (Python)
DESCRIPTION: This example demonstrates creating a key binding that toggles the prompt's editing mode between Emacs and Vi. It also uses a dynamic bottom toolbar to display the current active editing mode.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/asking_for_input.rst#_snippet_28

LANGUAGE: python
CODE:
```
from prompt_toolkit import prompt
from prompt_toolkit.application.current import get_app
from prompt_toolkit.enums import EditingMode
from prompt_toolkit.key_binding import KeyBindings

def run():
    # Create a set of key bindings.
    bindings = KeyBindings()

    # Add an additional key binding for toggling this flag.
    @bindings.add("f4")
    def _(event):
        " Toggle between Emacs and Vi mode. "
        app = event.app

        if app.editing_mode == EditingMode.VI:
            app.editing_mode = EditingMode.EMACS
        else:
            app.editing_mode = EditingMode.VI

    # Add a toolbar at the bottom to display the current input mode.
    def bottom_toolbar():
        " Display the current input mode. "
        text = "Vi" if get_app().editing_mode == EditingMode.VI else "Emacs"
        return [
            ("class:toolbar", " [F4] %s " % text)
        ]

    prompt("> ", key_bindings=bindings, bottom_toolbar=bottom_toolbar)

run()
```

----------------------------------------

TITLE: Reading Raw Keys from Stdin (Python)
DESCRIPTION: Demonstrates how to use prompt-toolkit to read individual key presses directly from standard input without rendering a visible prompt. It utilizes `create_input`, `raw_mode`, and `attach` to process `KeyPress` objects asynchronously. The example shows how to listen for key events and handle specific keys like Ctrl+C. Requires `asyncio`, `prompt_toolkit.input`, and `prompt_toolkit.keys`.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/asking_for_input.rst#_snippet_38

LANGUAGE: python
CODE:
```
import asyncio

from prompt_toolkit.input import create_input
from prompt_toolkit.keys import Keys


async def main() -> None:
    done = asyncio.Event()
    input = create_input()

    def keys_ready():
        for key_press in input.read_keys():
            print(key_press)

            if key_press.key == Keys.ControlC:
                done.set()

    with input.raw_mode():
        with input.attach(keys_ready):
            await done.wait()


if __name__ == "__main__":
    asyncio.run(main())
```

----------------------------------------

TITLE: Creating Condition Filter with Decorator - prompt_toolkit Python
DESCRIPTION: Illustrates using the `@Condition` decorator to turn a function into a `prompt_toolkit` filter. The decorated function `is_searching` checks the application state to determine if searching is active, and the decorator automatically wraps it into a `Condition` instance, providing an alternative syntax to the lambda approach.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/advanced_topics/filters.rst#_snippet_1

LANGUAGE: python
CODE:
```
from prompt_toolkit.application.current import get_app
from prompt_toolkit.filters import Condition

@Condition
def is_searching():
    return get_app().is_searching
```

----------------------------------------

TITLE: Setting Default Color Depth via Shell Environment Variable
DESCRIPTION: This snippet provides examples of setting the PROMPT_TOOLKIT_COLOR_DEPTH environment variable in a shell script (like .bashrc) to configure the default color depth for prompt_toolkit applications. Setting this variable configures the default color depth (e.g., 4-bit, 8-bit) for any prompt_toolkit application launched from that shell environment, overriding the default behavior.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/advanced_topics/styling.rst#_snippet_9

LANGUAGE: shell
CODE:
```
# export PROMPT_TOOLKIT_COLOR_DEPTH=DEPTH_1_BIT
export PROMPT_TOOLKIT_COLOR_DEPTH=DEPTH_4_BIT
# export PROMPT_TOOLKIT_COLOR_DEPTH=DEPTH_8_BIT
# export PROMPT_TOOLKIT_COLOR_DEPTH=DEPTH_24_BIT
```

----------------------------------------

TITLE: Binding Control-Space for Prompt Completion (Python)
DESCRIPTION: This snippet provides a key binding definition to use 'c-space' instead of 'tab' for triggering autocompletion. It checks if completion is already active and either selects the next completion or starts a new completion.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/asking_for_input.rst#_snippet_29

LANGUAGE: python
CODE:
```
kb = KeyBindings()

@kb.add("c-space")
def _(event):
    " Initialize autocompletion, or select the next completion. "
    buff = event.app.current_buffer
    if buff.complete_state:
        buff.complete_next()
    else:
        buff.start_completion(select_first=False)
```

----------------------------------------

TITLE: Installing prompt-toolkit with pip (Command Line)
DESCRIPTION: This command installs the `prompt_toolkit` library using the pip package manager. It is the standard way to install the library in a Python environment. Requires pip installed and a functional Python environment.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/getting_started.rst#_snippet_0

LANGUAGE: command line
CODE:
```
pip install prompt_toolkit
```

----------------------------------------

TITLE: Installing prompt-toolkit with Conda (Command Line)
DESCRIPTION: This command installs the `prompt_toolkit` library using the Conda package manager, specifically pulling the package from the conda-forge channel. This method is used for installing the library within a Conda environment. Requires Conda installed and the conda-forge channel configured.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/getting_started.rst#_snippet_1

LANGUAGE: command line
CODE:
```
conda install -c https://conda.anaconda.org/conda-forge prompt_toolkit
```

----------------------------------------

TITLE: Combining Style Class Names and Inline Styles in prompt_toolkit Python
DESCRIPTION: This snippet shows how to combine a style class name with inline style attributes on a prompt_toolkit control. It illustrates applying both a style class name ('class:header') and an inline style attribute ('bg:red') to the style property of a prompt_toolkit Window. The order specifies priority, meaning the inline style ('bg:red') will override any conflicting background color defined in the 'header' class style.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/advanced_topics/styling.rst#_snippet_2

LANGUAGE: python
CODE:
```
Window(BufferControl(...), style='class:header bg:red'),
```

----------------------------------------

TITLE: Defining Style Rules for Multiple Combined Classes in prompt_toolkit Python
DESCRIPTION: This snippet demonstrates defining a style rule in a Style object that applies only when an element possesses *both* specified class names. It shows how to create a style rule within a prompt_toolkit Style object using a tuple key that contains multiple class names separated by spaces ('header left'). This rule's style ('underline') will only be applied to a UI element if it has *both* the 'header' class and the 'left' class assigned to its style.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/advanced_topics/styling.rst#_snippet_3

LANGUAGE: python
CODE:
```
style = Style([
     ('header left', 'underline'),
 ])
```

----------------------------------------

TITLE: Defining Style Rules for Combined Simple and Dotted Classes in prompt_toolkit Python
DESCRIPTION: This snippet shows how to define a complex style rule in a Style object that combines simple and dotted class names. It demonstrates creating a style rule in a prompt_toolkit Style object using a key that is a space-separated combination of simple and dotted class names ('header body left.text'). This rule's style ('underline') will be applied to a UI element only if it simultaneously possesses all the specified classes: 'header', 'body', and 'left.text'.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/advanced_topics/styling.rst#_snippet_5

LANGUAGE: python
CODE:
```
style = Style([
     ('header body left.text', 'underline'),
 ])
```

----------------------------------------

TITLE: Applying Custom Styles to CheckboxList Dialog Components
DESCRIPTION: Provides an example of styling a specific dialog type (CheckboxList) by defining a custom Style using Style.from_dict and targeting various internal components like 'dialog', 'button', 'checkbox', 'dialog.body', 'dialog shadow', 'frame.label', and 'dialog.body label'. The style is passed to the dialog function.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/dialogs.rst#_snippet_7

LANGUAGE: python
CODE:
```
from prompt_toolkit.shortcuts import checkboxlist_dialog
from prompt_toolkit.styles import Style

results = checkboxlist_dialog(
    title="CheckboxList dialog",
    text="What would you like in your breakfast ?",
    values=[
        ("eggs", "Eggs"),
        ("bacon", "Bacon"),
        ("croissants", "20 Croissants"),
        ("daily", "The breakfast of the day")
    ],
    style=Style.from_dict({
        'dialog': 'bg:#cdbbb3',
        'button': 'bg:#bf99a4',
        'checkbox': '#e8612c',
        'dialog.body': 'bg:#a9cfd0',
        'dialog shadow': 'bg:#c98982',
        'frame.label': '#fcaca3',
        'dialog.body label': '#fd8bb6',
    })
).run()
```

----------------------------------------

TITLE: Asynchronous Dialog Execution (v3/v2) - Python
DESCRIPTION: This snippet shows how to conditionally execute dialogs asynchronously for prompt_toolkit versions 2.0 and 3.0. Version 3 requires calling `.run_async()` on the returned Application object, while version 2 used the `async_=True` parameter on the original function call.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/upgrading/3.0.rst#_snippet_7

LANGUAGE: python
CODE:
```
if PTK3:
    result = await input_dialog(title='...', text='...').run_async()
else:
    result = await input_dialog(title='...', text='...', async_=True)
```

----------------------------------------

TITLE: Detecting Prompt Toolkit Version - Python
DESCRIPTION: This snippet shows how to import the prompt_toolkit version string and use it to create a boolean flag (PTK3) that indicates whether version 3.x is currently being used. This flag can be used for conditional logic during the upgrade process to support both versions.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/upgrading/3.0.rst#_snippet_0

LANGUAGE: python
CODE:
```
from prompt_toolkit import __version__ as ptk_version

PTK3 = ptk_version.startswith('3.')
```

----------------------------------------

TITLE: Defining a Custom Filter Python
DESCRIPTION: Demonstrates how to define a custom filter in prompt_toolkit 2.0 using the @Condition decorator. Filters are now functions, and this decorator simplifies creating new ones. Requires prompt_toolkit.filters.Condition.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/upgrading/2.0.rst#_snippet_0

LANGUAGE: python
CODE:
```
from prompt_toolkit.filters import Condition

@Condition
def my_filter();
    return True  # Or False
```

----------------------------------------

TITLE: Input Dialog Call (v2) - Python
DESCRIPTION: This snippet shows the typical way of calling dialog functions like `input_dialog` in prompt_toolkit version 2.0. The function call itself would block and directly return the dialog's result upon completion.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/upgrading/3.0.rst#_snippet_5

LANGUAGE: python
CODE:
```
from prompt_toolkit.shortcuts import input_dialog

result = input_dialog(title='...', text='...')
```

----------------------------------------

TITLE: Pytest Fixture for AppSession Setup - Python
DESCRIPTION: This pytest fixture ensures that a fresh `AppSession` is created for each test function. Running prompt_toolkit code within this session context ensures that library functions use the current session's settings, which is particularly useful for compatibility with pytest features like `capsys` that may modify `sys.stdout`.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/advanced_topics/unit_testing.rst#_snippet_3

LANGUAGE: python
CODE:
```
from prompt_toolkit.application import create_app_session

@fixture(autouse=True, scope="function")
def _pt_app_session():
    with create_app_session():
        yield
```

----------------------------------------

TITLE: Disabling Terminal Flow Control with stty
DESCRIPTION: This shell command is provided as a solution to prevent the terminal from capturing C-q and C-s keys, which are traditionally used for software flow control (ixon). Running this command allows these keys to be bound within applications like prompt_toolkit.
SOURCE: https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/docs/pages/advanced_topics/key_bindings.rst#_snippet_1

LANGUAGE: shell
CODE:
```
stty -ixon
```
