TITLE: Rich Print Example
DESCRIPTION: This snippet demonstrates the use of the Rich print function with console markup for styling text and automatically formatting Python objects. It shows how to print colored and styled text, along with a formatted representation of local variables.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/introduction.rst#2025-04-16_snippet_3

LANGUAGE: python
CODE:
```
">>> print("[italic red]Hello[/italic red] World!", locals())"
```

----------------------------------------

TITLE: Importing Rich Print as rprint
DESCRIPTION: This snippet shows how to import the Rich print function as 'rprint' to avoid shadowing the built-in Python print function. It provides an alternative way to use Rich's printing capabilities without overriding the standard print.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/introduction.rst#2025-04-16_snippet_4

LANGUAGE: python
CODE:
```
"from rich import print as rprint"
```

----------------------------------------

TITLE: Using Rich Print Function with Markup
DESCRIPTION: Example of importing and using Rich's print function that extends Python's built-in print with markup support for styling text with colors and formatting.
SOURCE: https://github.com/Textualize/rich/blob/master/README.de.md#2025-04-16_snippet_2

LANGUAGE: python
CODE:
```
from rich import print

print("Hello, [bold magenta]World[/bold magenta]!", ":vampire:", locals())
```

----------------------------------------

TITLE: Printing with Rich Console in Python
DESCRIPTION: Demonstrates various ways to use the Console.print() method for outputting rich content to the terminal. This includes printing lists, styled text, and local variables.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/console.rst#2025-04-16_snippet_1

LANGUAGE: python
CODE:
```
console.print([1, 2, 3])
console.print("[blue underline]Looks like a link")
console.print(locals())
console.print("FOO", style="white on blue")
```

----------------------------------------

TITLE: Creating and Printing a Table using Rich in Python
DESCRIPTION: This snippet demonstrates how to create a table with the Rich library, add columns and rows, and print it to the terminal. The example creates a table for Star Wars movies, including release dates and box office figures.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/tables.rst#2025-04-16_snippet_0

LANGUAGE: Python
CODE:
```
from rich.console import Console
from rich.table import Table

table = Table(title="Star Wars Movies")

table.add_column("Released", justify="right", style="cyan", no_wrap=True)
table.add_column("Title", style="magenta")
table.add_column("Box Office", justify="right", style="green")

table.add_row("Dec 20, 2019", "Star Wars: The Rise of Skywalker", "$952,110,690")
table.add_row("May 25, 2018", "Solo: A Star Wars Story", "$393,151,347")
table.add_row("Dec 15, 2017", "Star Wars Ep. V111: The Last Jedi", "$1,332,539,889")
table.add_row("Dec 16, 2016", "Rogue One: A Star Wars Story", "$1,332,439,889")

console = Console()
console.print(table)
```

----------------------------------------

TITLE: Basic Rich Print Example
DESCRIPTION: Demonstrates importing and using Rich's enhanced print function with markup and emoji support. The function accepts the same arguments as Python's built-in print but adds formatting capabilities.
SOURCE: https://github.com/Textualize/rich/blob/master/README.md#2025-04-16_snippet_1

LANGUAGE: python
CODE:
```
from rich import print

print("Hello, [bold magenta]World[/bold magenta]!", ":vampire:", locals())
```

----------------------------------------

TITLE: Printing JSON with Rich Console in Python
DESCRIPTION: Illustrates how to pretty print JSON using the Console.print_json() method and how to log JSON using the JSON class. It also shows how to use the command-line interface for JSON printing.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/console.rst#2025-04-16_snippet_3

LANGUAGE: python
CODE:
```
console.print_json('[false, true, null, "foo"]')
```

LANGUAGE: python
CODE:
```
from rich.json import JSON
console.log(JSON('["foo", "bar"]'))
```

LANGUAGE: python
CODE:
```
from rich import print_json
```

----------------------------------------

TITLE: Logging with Rich Console
DESCRIPTION: This snippet demonstrates how to use the `Console` object from the `rich` library for logging data to the console. It highlights features like syntax highlighting, pretty printing of data structures, and displaying local variables. The `log_locals` parameter is used to display a table of local variables where the log function is called, useful for debugging.
SOURCE: https://github.com/Textualize/rich/blob/master/README.fa.md#2025-04-16_snippet_9

LANGUAGE: python
CODE:
```
from rich.console import Console
console = Console()

test_data = [
    {"jsonrpc": "2.0", "method": "sum", "params": [None, 1, 2, 4, False, True], "id": "1",},
    {"jsonrpc": "2.0", "method": "notify_hello", "params": [7]},
    {"jsonrpc": "2.0", "method": "subtract", "params": [42, 23], "id": "2"},
]

def test_log():
    enabled = False
    context = {
        "foo": "bar",
    }
    movies = ["Deadpool", "Rise of the Skywalker"]
    console.log("Hello from", console, "!")
    console.log(test_data, log_locals=True)


test_log()
```

----------------------------------------

TITLE: Basic Progress Tracking with Rich in Python
DESCRIPTION: Demonstrates how to use the track function from rich.progress to display progress for a simple loop. The function automatically handles progress updates and display.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/progress.rst#2025-04-16_snippet_0

LANGUAGE: python
CODE:
```
import time
from rich.progress import track

for i in track(range(20), description="Processing..."):
    time.sleep(1)  # Simulate work being done
```

----------------------------------------

TITLE: Installing Rich in Python REPL
DESCRIPTION: Code to integrate Rich into the Python REPL environment, enabling pretty printing and syntax highlighting for all data structures displayed in the interactive console.
SOURCE: https://github.com/Textualize/rich/blob/master/README.de.md#2025-04-16_snippet_3

LANGUAGE: python
CODE:
```
>>> from rich import pretty
>>> pretty.install()
```

----------------------------------------

TITLE: Using Rich's Markup Syntax
DESCRIPTION: Shows how to use Rich's markup syntax for fine-grained styling within text. The syntax is similar to BBCode with tags for bold, underline, italic, and other formatting options.
SOURCE: https://github.com/Textualize/rich/blob/master/README.md#2025-04-16_snippet_6

LANGUAGE: python
CODE:
```
console.print("Where there is a [bold cyan]Will[/bold cyan] there [u]is[/u] a [i]way[/i].")
```

----------------------------------------

TITLE: Creating Formatted Tables with Rich
DESCRIPTION: Demonstrates creation of formatted tables using Rich's Table class with custom styling, column alignment, and markup rendering.
SOURCE: https://github.com/Textualize/rich/blob/master/README.md#2025-04-16_snippet_10

LANGUAGE: python
CODE:
```
from rich.console import Console
from rich.table import Table

console = Console()

table = Table(show_header=True, header_style="bold magenta")
table.add_column("Date", style="dim", width=12)
table.add_column("Title")
table.add_column("Production Budget", justify="right")
table.add_column("Box Office", justify="right")
table.add_row(
    "Dec 20, 2019", "Star Wars: The Rise of Skywalker", "$275,000,000", "$375,126,118"
)
table.add_row(
    "May 25, 2018",
    "[red]Solo[/red]: A Star Wars Story",
    "$275,000,000",
    "$393,151,347",
)
table.add_row(
    "Dec 15, 2017",
    "Star Wars Ep. VIII: The Last Jedi",
    "$262,000,000",
    "[bold]$1,332,539,889[/bold]",
)

console.print(table)
```

----------------------------------------

TITLE: Implementing Rich Console Logging
DESCRIPTION: Demonstrates how to use Rich's console logging functionality to display formatted data including timestamps and file locations. Shows logging of Python structures with syntax highlighting and pretty printing of collections.
SOURCE: https://github.com/Textualize/rich/blob/master/README.md#2025-04-16_snippet_8

LANGUAGE: python
CODE:
```
from rich.console import Console
console = Console()

test_data = [
    {"jsonrpc": "2.0", "method": "sum", "params": [None, 1, 2, 4, False, True], "id": "1",},
    {"jsonrpc": "2.0", "method": "notify_hello", "params": [7]},
    {"jsonrpc": "2.0", "method": "subtract", "params": [42, 23], "id": "2"},
]

def test_log():
    enabled = False
    context = {
        "foo": "bar",
    }
    movies = ["Deadpool", "Rise of the Skywalker"]
    console.log("Hello from", console, "!")
    console.log(test_data, log_locals=True)


test_log()
```

----------------------------------------

TITLE: Advanced Progress Display with Multiple Tasks in Python
DESCRIPTION: Shows how to create a Progress object with multiple tasks, update them concurrently, and use a context manager for automatic start/stop of the display.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/progress.rst#2025-04-16_snippet_1

LANGUAGE: python
CODE:
```
import time

from rich.progress import Progress

with Progress() as progress:

    task1 = progress.add_task("[red]Downloading...", total=1000)
    task2 = progress.add_task("[green]Processing...", total=1000)
    task3 = progress.add_task("[cyan]Cooking...", total=1000)

    while not progress.finished:
        progress.update(task1, advance=0.5)
        progress.update(task2, advance=0.3)
        progress.update(task3, advance=0.9)
        time.sleep(0.02)
```

----------------------------------------

TITLE: Highlight Code with Rich Syntax in Python
DESCRIPTION: Demonstrates how to highlight syntax using the Rich library in Python. The snippet reads a file, detects the language, and prints it to the console. Dependencies include the Rich library, specifically the Console and Syntax classes.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/syntax.rst#2025-04-16_snippet_0

LANGUAGE: python
CODE:
```
from rich.console import Console
from rich.syntax import Syntax

console = Console()
with open("syntax.py", "rt") as code_file:
    syntax = Syntax(code_file.read(), "python")
console.print(syntax)
```

----------------------------------------

TITLE: Basic Rich Logging Handler Setup in Python
DESCRIPTION: Demonstrates how to set up a basic Rich logging handler with formatting configuration. This snippet shows the minimal setup required to get started with Rich logging.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/logging.rst#2025-04-16_snippet_0

LANGUAGE: python
CODE:
```
import logging
from rich.logging import RichHandler

FORMAT = "%(message)s"
logging.basicConfig(
    level="NOTSET", format=FORMAT, datefmt="[%X]", handlers=[RichHandler()]
)

log = logging.getLogger("rich")
log.info("Hello, World!")
```

----------------------------------------

TITLE: Colorful Input Prompt with Emoji
DESCRIPTION: This snippet showcases how to use the `input` method of the Rich Console to create a colorful prompt, including inline styles and emoji support. It prompts the user for their name with a styled and emoji-rich message.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/console.rst#2025-04-16_snippet_10

LANGUAGE: Python
CODE:
```
from rich.console import Console
console = Console()
console.input("What is [i]your[/i] [bold red]name[/]? :smiley: ")
```

----------------------------------------

TITLE: Progress Bar with Rich
DESCRIPTION: This code snippet shows how to use the `track` function from the Rich library to display a progress bar for a loop. The `track` function wraps an iterable and automatically updates the progress bar as the loop iterates.
SOURCE: https://github.com/Textualize/rich/blob/master/README.kr.md#2025-04-16_snippet_10

LANGUAGE: python
CODE:
```
from rich.progress import track

for step in track(range(100)):
    do_step(step)
```

----------------------------------------

TITLE: Initializing Rich Console in Python
DESCRIPTION: Creates a Console instance for use throughout a project. This snippet demonstrates how to create a console.py file with a global Console object that can be imported and used in other parts of the project.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/console.rst#2025-04-16_snippet_0

LANGUAGE: python
CODE:
```
from rich.console import Console
console = Console()
```

LANGUAGE: python
CODE:
```
from my_project.console import console
```

----------------------------------------

TITLE: Justifying Text with Rich Console in Python
DESCRIPTION: Illustrates how to use the justify parameter in Console.print() and Console.log() methods to align text within the terminal. It shows left, right, center, and full justification options.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/console.rst#2025-04-16_snippet_7

LANGUAGE: python
CODE:
```
from rich.console import Console

console = Console(width=20)

style = "bold white on blue"
console.print("Rich", style=style)
console.print("Rich", style=style, justify="left")
console.print("Rich", style=style, justify="center")
console.print("Rich", style=style, justify="right")
```

----------------------------------------

TITLE: Displaying Status with Rich
DESCRIPTION: This snippet demonstrates how to use the `status` method from the `Console` class to display a status message and a spinner while a task is being performed.  The `status` method displays a message with an animated spinner. The code simulates tasks being completed over time with `sleep` function.
SOURCE: https://github.com/Textualize/rich/blob/master/README.fa.md#2025-04-16_snippet_13

LANGUAGE: python
CODE:
```
from time import sleep
from rich.console import Console

console = Console()
tasks = [f"task {n}" for n in range(1, 11)]

with console.status("[bold green]Working on tasks...") as status:
    while tasks:
        task = tasks.pop(0)
        sleep(1)
        console.log(f"{task} complete")
```

----------------------------------------

TITLE: Printing/Logging Above Rich Progress Display
DESCRIPTION: This code demonstrates how to print or log messages above the Rich progress display using the internal Console object accessible via `progress.console`. It adds a task to the progress bar and prints messages for each job.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/progress.rst#2025-04-16_snippet_6

LANGUAGE: python
CODE:
```
with Progress() as progress:
    task = progress.add_task("twiddling thumbs", total=10)
    for job in range(10):
        progress.console.print(f"Working on job #{job}")
        # run_job(job) # Placeholder for job execution
        progress.advance(task)
```

----------------------------------------

TITLE: Using Live Display with Console Printing in Python
DESCRIPTION: Illustrates how to use the internal console of a Live object to print messages above the live display. This example combines updating a table with printing status messages.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/live.rst#2025-04-16_snippet_2

LANGUAGE: python
CODE:
```
import time

from rich.live import Live
from rich.table import Table

table = Table()
table.add_column("Row ID")
table.add_column("Description")
table.add_column("Level")

with Live(table, refresh_per_second=4) as live:  # update 4 times a second to feel fluid
    for row in range(12):
        live.console.print(f"Working on row #{row}")
        time.sleep(0.4)
        table.add_row(f"{row}", f"description {row}", "[red]ERROR")
```

----------------------------------------

TITLE: Rendering Markdown with Rich
DESCRIPTION: This code snippet demonstrates how to render Markdown content using the Rich library. It imports the `Console` and `Markdown` classes from the `rich` library. It reads the content of a `README.md` file and converts it to a `Markdown` object, which is then printed to the console using `console.print()` for formatted display.
SOURCE: https://github.com/Textualize/rich/blob/master/README.ja.md#2025-04-16_snippet_14

LANGUAGE: python
CODE:
```
from rich.console import Console
from rich.markdown import Markdown

console = Console()
with open("README.md") as readme:
    markdown = Markdown(readme.read())
console.print(markdown)
```

----------------------------------------

TITLE: Rendering Markdown with Rich
DESCRIPTION: This snippet demonstrates how to render Markdown content in the terminal using the `Markdown` class from the `rich` library. It reads Markdown content from a file, creates a `Markdown` object, and prints it to the console, rendering the Markdown formatting.
SOURCE: https://github.com/Textualize/rich/blob/master/README.fa.md#2025-04-16_snippet_17

LANGUAGE: python
CODE:
```
from rich.console import Console
from rich.markdown import Markdown

console = Console()
with open("README.md") as readme:
    markdown = Markdown(readme.read())
console.print(markdown)
```

----------------------------------------

TITLE: Creating a Table with Rich
DESCRIPTION: This snippet demonstrates how to create a styled table using the `Table` class from the `rich` library. It sets up column headers, styles, and adds rows with formatted data. The console.print(table) will render the table to the terminal.
SOURCE: https://github.com/Textualize/rich/blob/master/README.fa.md#2025-04-16_snippet_11

LANGUAGE: python
CODE:
```
from rich.console import Console
from rich.table import Table

console = Console()

table = Table(show_header=True, header_style="bold magenta")
table.add_column("Date", style="dim", width=12)
table.add_column("Title")
table.add_column("Production Budget", justify="right")
table.add_column("Box Office", justify="right")
table.add_row(
    "Dec 20, 2019", "Star Wars: The Rise of Skywalker", "$275,000,000", "$375,126,118"
)
table.add_row(
    "May 25, 2018",
    "[red]Solo[/red]: A Star Wars Story",
    "$275,000,000",
    "$393,151,347",
)
table.add_row(
    "Dec 15, 2017",
    "Star Wars Ep. VIII: The Last Jedi",
    "$262,000,000",
    "[bold]$1,332,539,889[/bold]",
)

console.print(table)
```

----------------------------------------

TITLE: Overlapping Markup Tags - Python
DESCRIPTION: Shows how markup tags can be combined and overlapped for complex styling.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/markup.rst#2025-04-16_snippet_3

LANGUAGE: python
CODE:
```
print("[bold]Bold[italic] bold and italic [/bold]italic[/italic]")
```

----------------------------------------

TITLE: Creating a Grid with Rich Table Class
DESCRIPTION: This snippet creates a grid layout using the Table class, suitable for positioning multiple contents within the terminal. It expands to fit the available size and aligns text to the left and right.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/tables.rst#2025-04-16_snippet_4

LANGUAGE: Python
CODE:
```
from rich import print
from rich.table import Table

grid = Table.grid(expand=True)
grid.add_column()
grid.add_column(justify="right")
grid.add_row("Raising shields", "[bold magenta]COMPLETED [green]:heavy_check_mark:")

print(grid)
```

----------------------------------------

TITLE: Using Rich's Print Function
DESCRIPTION: Example of using Rich's enhanced print function to format text with color, style, and display emoji and variables. This demonstrates the markup syntax with magenta bold text.
SOURCE: https://github.com/Textualize/rich/blob/master/README.pt-br.md#2025-04-16_snippet_2

LANGUAGE: python
CODE:
```
from rich import print

print("Hello, [bold magenta]World[/bold magenta]!", ":vampire:", locals())
```

----------------------------------------

TITLE: Displaying Directory Contents in Columns with Rich
DESCRIPTION: This snippet uses the Rich library to display the contents of a directory in columns. It imports necessary modules like `os`, `sys`, `print`, and `Columns` from the `rich` library. The `os.listdir()` function is used to retrieve the list of files and directories, which are then passed to the `Columns` class for formatted output using `print`.
SOURCE: https://github.com/Textualize/rich/blob/master/README.ja.md#2025-04-16_snippet_13

LANGUAGE: python
CODE:
```
import os
import sys

from rich import print
from rich.columns import Columns

directory = os.listdir(sys.argv[1])
print(Columns(directory))
```

----------------------------------------

TITLE: Implementing Syntax Highlighting
DESCRIPTION: Shows how to apply syntax highlighting to code using Rich's Syntax class with custom themes and line numbers.
SOURCE: https://github.com/Textualize/rich/blob/master/README.md#2025-04-16_snippet_15

LANGUAGE: python
CODE:
```
from rich.console import Console
from rich.syntax import Syntax

my_code = '''
def iter_first_last(values: Iterable[T]) -> Iterable[Tuple[bool, bool, T]]:
    """Iterate and generate a tuple with a flag for first and last value."""
    iter_values = iter(values)
    try:
        previous_value = next(iter_values)
    except StopIteration:
        return
    first = True
    for value in iter_values:
        yield first, False, previous_value
        first = False
        previous_value = value
    yield first, True, previous_value
'''
syntax = Syntax(my_code, "python", theme="monokai", line_numbers=True)
console = Console()
console.print(syntax)
```

----------------------------------------

TITLE: Implementing __rich_console__ Method for Advanced Custom Formatting in Python
DESCRIPTION: A more advanced example using a dataclass to implement __rich_console__ method that yields multiple renderable objects. This creates a complex custom representation with a table for a Student class.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/protocol.rst#2025-04-16_snippet_1

LANGUAGE: python
CODE:
```
from dataclasses import dataclass
from rich.console import Console, ConsoleOptions, RenderResult
from rich.table import Table

@dataclass
class Student:
    id: int
    name: str
    age: int
    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        yield f"[b]Student:[/b] #{self.id}"
        my_table = Table("Attribute", "Value")
        my_table.add_row("name", self.name)
        my_table.add_row("age", str(self.age))
        yield my_table
```

----------------------------------------

TITLE: Creating Tables with Rich
DESCRIPTION: This code snippet demonstrates how to create a table using the Rich library, with custom headers, styles, and data. It showcases the `Table` class and its methods for adding columns and rows. It requires the `rich` library.
SOURCE: https://github.com/Textualize/rich/blob/master/README.kr.md#2025-04-16_snippet_9

LANGUAGE: python
CODE:
```
from rich.console import Console
from rich.table import Table

console = Console()

table = Table(show_header=True, header_style="bold magenta")
table.add_column("Date", style="dim", width=12)
table.add_column("Title")
table.add_column("Production Budget", justify="right")
table.add_column("Box Office", justify="right")
table.add_row(
    "Dec 20, 2019", "Star Wars: The Rise of Skywalker", "$275,000,000", "$375,126,118"
)
table.add_row(
    "May 25, 2018",
    "[red]Solo[/red]: A Star Wars Story",
    "$275,000,000",
    "$393,151,347",
)
table.add_row(
    "Dec 15, 2017",
    "Star Wars Ep. VIII: The Last Jedi",
    "$262,000,000",
    "[bold]$1,332,539,889[/bold]",
)

console.print(table)
```

----------------------------------------

TITLE: Syntax Highlighting with Rich
DESCRIPTION: This code snippet demonstrates how to use Rich to perform syntax highlighting of code in the terminal. It uses the `Syntax` class to highlight Python code with a specified theme and line numbers.
SOURCE: https://github.com/Textualize/rich/blob/master/README.kr.md#2025-04-16_snippet_15

LANGUAGE: python
CODE:
```
from rich.console import Console
from rich.syntax import Syntax

my_code = '''
def iter_first_last(values: Iterable[T]) -> Iterable[Tuple[bool, bool, T]]:
    """Iterate and generate a tuple with a flag for first and last value."""
    iter_values = iter(values)
    try:
        previous_value = next(iter_values)
    except StopIteration:
        return
    first = True
    for value in iter_values:
        yield first, False, previous_value
        first = False
        previous_value = value
    yield first, True, previous_value
'''
syntax = Syntax(my_code, "python", theme="monokai", line_numbers=True)
console = Console()
console.print(syntax)
```

----------------------------------------

TITLE: Adding Branches to a Rich Tree (Python)
DESCRIPTION: This snippet shows how to add branches to an existing tree in Rich. After creating a tree, the add method is called to attach additional labels as branches. The updated tree now visually reflects the added branches connected to the main label.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/tree.rst#2025-04-16_snippet_1

LANGUAGE: python
CODE:
```
tree.add("foo")\ntree.add("bar")\nprint(tree)
```

----------------------------------------

TITLE: Rendering Markdown in Console using Rich
DESCRIPTION: This example demonstrates how to create a Markdown object with Rich and print it to the console. The code shows how to format an h1 heading, emphasized text, and a numbered list.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/markdown.rst#2025-04-16_snippet_0

LANGUAGE: python
CODE:
```
MARKDOWN = """
# This is an h1

Rich can do a pretty *decent* job of rendering markdown.

1. This is a list item
2. This is another list item
"""
from rich.console import Console
from rich.markdown import Markdown

console = Console()
md = Markdown(MARKDOWN)
console.print(md)
```

----------------------------------------

TITLE: Paging Console Output
DESCRIPTION: This code shows how to use a pager to display long output from the Rich Console. It uses a context manager `console.pager()` to send the output of `make_test_card()` to the system's pager.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/console.rst#2025-04-16_snippet_18

LANGUAGE: Python
CODE:
```
from rich.__main__ import make_test_card
from rich.console import Console

console = Console()
with console.pager():
    console.print(make_test_card())
```

----------------------------------------

TITLE: Columns Layout with Rich
DESCRIPTION: This code snippet shows how to display a directory listing in columns using the Rich library. It's a basic clone of the `ls` command found in MacOS/Linux. It utilizes the `Columns` class to format the output.
SOURCE: https://github.com/Textualize/rich/blob/master/README.kr.md#2025-04-16_snippet_13

LANGUAGE: python
CODE:
```
import os
import sys

from rich import print
from rich.columns import Columns

directory = os.listdir(sys.argv[1])
print(Columns(directory))
```

----------------------------------------

TITLE: Displaying Directory Contents in Columns
DESCRIPTION: Shows how to create a simple directory listing with content displayed in columns using Rich's Columns class.
SOURCE: https://github.com/Textualize/rich/blob/master/README.md#2025-04-16_snippet_13

LANGUAGE: python
CODE:
```
import os
import sys

from rich import print
from rich.columns import Columns

directory = os.listdir(sys.argv[1])
print(Columns(directory))
```

----------------------------------------

TITLE: Syntax Highlighting with Rich
DESCRIPTION: This snippet demonstrates how to use the `Syntax` class from the `rich` library to highlight Python code syntax in the terminal.  It creates a `Syntax` object with Python code, specifies the language, theme, and line numbers, and then prints it to the console, rendering the code with syntax highlighting.
SOURCE: https://github.com/Textualize/rich/blob/master/README.fa.md#2025-04-16_snippet_18

LANGUAGE: python
CODE:
```
from rich.console import Console
from rich.syntax import Syntax

my_code = '''
def iter_first_last(values: Iterable[T]) -> Iterable[Tuple[bool, bool, T]]:
    """Iterate and generate a tuple with a flag for first and last value."""
    iter_values = iter(values)
    try:
        previous_value = next(iter_values)
    except StopIteration:
        return
    first = True
    for value in iter_values:
        yield first, False, previous_value
        first = False
        previous_value = value
    yield first, True, previous_value
'''
syntax = Syntax(my_code, "python", theme="monokai", line_numbers=True)
console = Console()
console.print(syntax)
```

----------------------------------------

TITLE: Defining a Rich Repr for Custom Objects - Python
DESCRIPTION: This example defines a Bird class with a __rich_repr__ method to customize its representation for Rich. The class shows how Rich can improve readability for complex objects.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/pretty.rst#2025-04-16_snippet_4

LANGUAGE: Python
CODE:
```
class Bird:
    def __init__(self, name, eats=None, fly=True, extinct=False):
        self.name = name
        self.eats = list(eats) if eats else []
        self.fly = fly
        self.extinct = extinct

    def __rich_repr__(self):
        yield self.name
        yield "eats", self.eats
        yield "fly", self.fly, True
        yield "extinct", self.extinct, False

BIRDS = {
    "gull": Bird("gull", eats=["fish", "chips", "ice cream", "sausage rolls"]),
    "penguin": Bird("penguin", eats=["fish"], fly=False),
    "dodo": Bird("dodo", eats=["fruit"], fly=False, extinct=True)
}
print(BIRDS)
```

----------------------------------------

TITLE: Logging to Console - Python
DESCRIPTION: This snippet illustrates how to use the Console's log method to print messages along with metadata like time and calling file information.
SOURCE: https://github.com/Textualize/rich/blob/master/README.ja.md#2025-04-16_snippet_7

LANGUAGE: python
CODE:
```
from rich.console import Console
console = Console()

test_data = [
    {"jsonrpc": "2.0", "method": "sum", "params": [None, 1, 2, 4, False, True], "id": "1",},
    {"jsonrpc": "2.0", "method": "notify_hello", "params": [7]},
    {"jsonrpc": "2.0", "method": "subtract", "params": [42, 23], "id": "2"},
]

def test_log():
    enabled = False
    context = {
        "foo": "bar",
    }
    movies = ["Deadpool", "Rise of the Skywalker"]
    console.log("Hello from", console, "!")
    console.log(test_data, log_locals=True)

test_log()
```

----------------------------------------

TITLE: Implementing Progress Bars
DESCRIPTION: Shows how to create progress bars using Rich's track function for monitoring long-running tasks.
SOURCE: https://github.com/Textualize/rich/blob/master/README.md#2025-04-16_snippet_11

LANGUAGE: python
CODE:
```
from rich.progress import track

for step in track(range(100)):
    do_step(step)
```

----------------------------------------

TITLE: Using Alternate Screen
DESCRIPTION: This code demonstrates using the alternate screen mode in Rich. It displays a pretty printed dictionary on the alternate screen for 5 seconds before returning to the command prompt.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/console.rst#2025-04-16_snippet_19

LANGUAGE: Python
CODE:
```
from time import sleep
from rich.console import Console

console = Console()
with console.screen():
    console.print(locals())
    sleep(5)
```

----------------------------------------

TITLE: Creating Rich Tables with Custom Styling in Python
DESCRIPTION: Demonstrates creating a Rich Table with custom headers, styles, and justification for rendering structured data in the console
SOURCE: https://github.com/Textualize/rich/blob/master/README.cn.md#2025-04-16_snippet_6

LANGUAGE: python
CODE:
```
from rich.console import Console
from rich.table import Column, Table

console = Console()

table = Table(show_header=True, header_style="bold magenta")
table.add_column("Date", style="dim", width=12)
table.add_column("Title")
table.add_column("Production Budget", justify="right")
table.add_column("Box Office", justify="right")
table.add_row(
    "Dec 20, 2019", "Star Wars: The Rise of Skywalker", "$275,000,000", "$375,126,118"
)
table.add_row(
    "May 25, 2018",
    "[red]Solo[/red]: A Star Wars Story",
    "$275,000,000",
    "$393,151,347"
)
table.add_row(
    "Dec 15, 2017",
    "Star Wars Ep. VIII: The Last Jedi",
    "$262,000,000",
    "[bold]$1,332,539,889[/bold]"
)

console.print(table)
```

----------------------------------------

TITLE: Creating Error Console
DESCRIPTION: This code snippet demonstrates creating an error console using Rich, directing output to stderr. It initializes a Console object, specifying `stderr=True` to ensure error messages are written to the standard error stream.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/console.rst#2025-04-16_snippet_13

LANGUAGE: Python
CODE:
```
from rich.console import Console
error_console = Console(stderr=True)
```

----------------------------------------

TITLE: Creating a Fitted Panel in Python
DESCRIPTION: Demonstrates how to create a panel that fits the content rather than extending to the full width of the terminal. This can be done using the Panel.fit method or by setting expand=False.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/panel.rst#2025-04-16_snippet_1

LANGUAGE: python
CODE:
```
from rich import print
from rich.panel import Panel
print(Panel.fit("Hello, [red]World!"))
```

----------------------------------------

TITLE: Basic Console Print Usage
DESCRIPTION: Simple example of using the Console object's print method to output text to the terminal with automatic text wrapping to fit terminal width.
SOURCE: https://github.com/Textualize/rich/blob/master/README.de.md#2025-04-16_snippet_5

LANGUAGE: python
CODE:
```
console.print("Hello", "World!")
```

----------------------------------------

TITLE: Creating Status Spinners
DESCRIPTION: Demonstrates how to display animated status spinners with custom messages while executing tasks.
SOURCE: https://github.com/Textualize/rich/blob/master/README.md#2025-04-16_snippet_12

LANGUAGE: python
CODE:
```
from time import sleep
from rich.console import Console

console = Console()
tasks = [f"task {n}" for n in range(1, 11)]

with console.status("[bold green]Working on tasks...") as status:
    while tasks:
        task = tasks.pop(0)
        sleep(1)
        console.log(f"{task} complete")
```

----------------------------------------

TITLE: Suppressing Framework Frames in Traceback
DESCRIPTION: Excludes specific framework modules from Rich exception rendering
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/traceback.rst#2025-04-16_snippet_3

LANGUAGE: python
CODE:
```
import click
from rich.traceback import install
install(suppress=[click])
```

----------------------------------------

TITLE: Custom Column Progress Display in Python
DESCRIPTION: Demonstrates how to create a Progress object with custom columns, including default columns and additional ones like SpinnerColumn and TimeElapsedColumn.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/progress.rst#2025-04-16_snippet_4

LANGUAGE: python
CODE:
```
progress = Progress(
    SpinnerColumn(),
    *Progress.get_default_columns(),
    TimeElapsedColumn(),
)
```

----------------------------------------

TITLE: Handling Overflow in Rich Console for Python
DESCRIPTION: Demonstrates different methods for handling text overflow in Rich, including folding, cropping, and using ellipsis. This is useful when dealing with long text in limited space.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/console.rst#2025-04-16_snippet_8

LANGUAGE: python
CODE:
```
from typing import List
from rich.console import Console, OverflowMethod

console = Console(width=14)
supercali = "supercalifragilisticexpialidocious"

overflow_methods: List[OverflowMethod] = ["fold", "crop", "ellipsis"]
for overflow in overflow_methods:
    console.rule(overflow)
    console.print(supercali, overflow=overflow, style="bold blue")
    console.print()
```

----------------------------------------

TITLE: Displaying Status with Rich Console in Python
DESCRIPTION: Demonstrates how to use the Console.status() method to display a status message with a spinner animation that doesn't interfere with regular output.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/console.rst#2025-04-16_snippet_6

LANGUAGE: python
CODE:
```
with console.status("Working..."):
    do_work()
```

LANGUAGE: python
CODE:
```
with console.status("Monkeying around...", spinner="monkey"):
    do_work()
```

----------------------------------------

TITLE: Using the @group Decorator for Dynamic Renderables in Python
DESCRIPTION: This example shows how to use Rich's @group decorator to build a group from an iterator of renderables. This approach is more convenient when dealing with a larger or dynamic number of renderables.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/group.rst#2025-04-16_snippet_1

LANGUAGE: python
CODE:
```
from rich import print
from rich.console import group
from rich.panel import Panel

@group()
def get_panels():
    yield Panel("Hello", style="on blue")
    yield Panel("World", style="on red")

print(Panel(get_panels()))
```

----------------------------------------

TITLE: Printing Text in Color with Rich
DESCRIPTION: This snippet demonstrates how to print text in different colors using the Rich library. It includes examples of using a named color, a color number, and both hex and RGB color definitions. The color changes the foreground text color, and prefixes like 'on' or 'default' adjust the background color.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/style.rst#2025-04-16_snippet_0

LANGUAGE: Python
CODE:
```
console.print("Hello", style="magenta")
```

LANGUAGE: Python
CODE:
```
console.print("Hello", style="color(5)")
```

LANGUAGE: Python
CODE:
```
console.print("Hello", style="#af00ff")
console.print("Hello", style="rgb(175,0,255)")
```

LANGUAGE: Python
CODE:
```
console.print("DANGER!", style="red on white")
```

----------------------------------------

TITLE: Logging with Rich Console in Python
DESCRIPTION: Shows how to use the Console.log() method for debugging, which adds timestamps and file/line information to the output. It also demonstrates logging local variables.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/console.rst#2025-04-16_snippet_2

LANGUAGE: python
CODE:
```
>>> console.log("Hello, World!")
```

----------------------------------------

TITLE: Rich Exception Handling in Logging
DESCRIPTION: Shows how to configure Rich logging handler to use Rich's Traceback class for enhanced exception formatting. Includes try-except example with logging.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/logging.rst#2025-04-16_snippet_2

LANGUAGE: python
CODE:
```
import logging
from rich.logging import RichHandler

logging.basicConfig(
    level="NOTSET",
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)]
)

log = logging.getLogger("rich")
try:
    print(1 / 0)
except Exception:
    log.exception("unable print!")
```

----------------------------------------

TITLE: Initializing Rich Console Logging in Python
DESCRIPTION: Demonstrates creating a Rich Console object and logging data with syntax highlighting and local variable tracking
SOURCE: https://github.com/Textualize/rich/blob/master/README.cn.md#2025-04-16_snippet_5

LANGUAGE: python
CODE:
```
from rich.console import Console
console = Console()

test_data = [
    {"jsonrpc": "2.0", "method": "sum", "params": [None, 1, 2, 4, False, True], "id": "1"},
    {"jsonrpc": "2.0", "method": "notify_hello", "params": [7]},
    {"jsonrpc": "2.0", "method": "subtract", "params": [42, 23], "id": "2"},
]

def test_log():
    enabled = False
    context = {"foo": "bar"}
    movies = ["Deadpool", "Rise of the Skywalker"]
    console.log("Hello from", console, "!")
    console.log(test_data, log_locals=True)

test_log()
```

----------------------------------------

TITLE: Syntax Highlighting with Rich
DESCRIPTION: This snippet demonstrates syntax highlighting using the Rich library and the `Syntax` class. It imports `Console` and `Syntax` from `rich`. A multi-line string containing Python code is defined, and a `Syntax` object is created with specified language, theme and line numbers. Finally, the `Syntax` object is printed to the console for syntax-highlighted output.
SOURCE: https://github.com/Textualize/rich/blob/master/README.ja.md#2025-04-16_snippet_15

LANGUAGE: python
CODE:
```
from rich.console import Console
from rich.syntax import Syntax

my_code = '''
def iter_first_last(values: Iterable[T]) -> Iterable[Tuple[bool, bool, T]]:
    """Iterate and generate a tuple with a flag for first and last value."""
    iter_values = iter(values)
    try:
        previous_value = next(iter_values)
    except StopIteration:
        return
    first = True
    for value in iter_values:
        yield first, False, previous_value
        first = False
        previous_value = value
    yield first, True, previous_value
'''
syntax = Syntax(my_code, "python", theme="monokai", line_numbers=True)
console = Console()
console.print(syntax)
```

----------------------------------------

TITLE: Combining Style Attributes in Rich
DESCRIPTION: This example demonstrates combining various style attributes such as bold, blink, and underline with color in the Rich library. Attributes can be negated using '[not XYZ]' syntax for selective styling.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/style.rst#2025-04-16_snippet_1

LANGUAGE: Python
CODE:
```
console.print("Danger, Will Robinson!", style="blink bold red underline on white")
```

LANGUAGE: Python
CODE:
```
console.print("foo [not bold]bar[/not bold] baz", style="bold")
```

----------------------------------------

TITLE: Displaying Progress with Progress Bar - Python
DESCRIPTION: This snippet demonstrates how to use the Rich library to create a progress bar for tracking long-running tasks by wrapping a sequence with the track function.
SOURCE: https://github.com/Textualize/rich/blob/master/README.ja.md#2025-04-16_snippet_10

LANGUAGE: python
CODE:
```
from rich.progress import track

for step in track(range(100)):
    do_step(step)
```

----------------------------------------

TITLE: Using the Style Class
DESCRIPTION: This snippet illustrates creating a style by instantiating a Style class. Style objects are slightly faster as they avoid parsing overhead, and they can be combined using the '+' operator to add attributes.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/style.rst#2025-04-16_snippet_3

LANGUAGE: Python
CODE:
```
from rich.style import Style
danger_style = Style(color="red", blink=True, bold=True)
console.print("Danger, Will Robinson!", style=danger_style)
```

LANGUAGE: Python
CODE:
```
from rich.console import Console
from rich.style import Style
console = Console()

base_style = Style.parse("cyan")
console.print("Hello, World", style = base_style + Style(underline=True))
```

LANGUAGE: Python
CODE:
```
style = Style(color="magenta", bgcolor="yellow", italic=True)
style = Style.parse("italic magenta on yellow")
```

----------------------------------------

TITLE: Confirmation Prompt
DESCRIPTION: Shows how to use the Confirm class to ask a simple yes/no question from the user
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/prompt.rst#2025-04-16_snippet_3

LANGUAGE: python
CODE:
```
from rich.prompt import Confirm
is_rich_great = Confirm.ask("Do you like rich?")
assert is_rich_great
```

----------------------------------------

TITLE: Appending Styled Text using Rich
DESCRIPTION: This snippet illustrates how to append styled text to an existing Text instance, allowing for the creation of complex strings with different styles. It shows the use of the append method from the Text class.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/text.rst#2025-04-16_snippet_1

LANGUAGE: python
CODE:
```
text = Text()
text.append("Hello", style="bold magenta")
text.append(" World!")
console.print(text)
```

----------------------------------------

TITLE: Enabling Rich REPL Formatting
DESCRIPTION: Code to install Rich in the Python REPL environment. This enhances the default REPL by pretty-printing and syntax highlighting any data structures displayed.
SOURCE: https://github.com/Textualize/rich/blob/master/README.md#2025-04-16_snippet_2

LANGUAGE: python
CODE:
```
>>> from rich import pretty
>>> pretty.install()
```

----------------------------------------

TITLE: Automatic Rich Repr Generation - Python
DESCRIPTION: This code demonstrates the use of the @rich.repr.auto decorator for automatically generating a rich representation for a class based on its attributes, thus simplifying the implementation.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/pretty.rst#2025-04-16_snippet_5

LANGUAGE: Python
CODE:
```
import rich.repr

@rich.repr.auto
class Bird:
    def __init__(self, name, eats=None, fly=True, extinct=False):
        self.name = name
        self.eats = list(eats) if eats else []
        self.fly = fly
        self.extinct = extinct

BIRDS = {
    "gull": Bird("gull", eats=["fish", "chips", "ice cream", "sausage rolls"]),
    "penguin": Bird("penguin", eats=["fish"], fly=False),
    "dodo": Bird("dodo", eats=["fruit"], fly=False, extinct=True)
}
from rich import print
print(BIRDS)
```

----------------------------------------

TITLE: Markdown Rendering with Rich
DESCRIPTION: This code snippet shows how to render a Markdown file in the terminal using the Rich library. It reads the content of a Markdown file, creates a `Markdown` object, and prints it to the console.
SOURCE: https://github.com/Textualize/rich/blob/master/README.kr.md#2025-04-16_snippet_14

LANGUAGE: python
CODE:
```
from rich.console import Console
from rich.markdown import Markdown

console = Console()
with open("README.md") as readme:
    markdown = Markdown(readme.read())
console.print(markdown)
```

----------------------------------------

TITLE: Customizing Progress Display with Rich
DESCRIPTION: This code shows how to customize the Rich progress display by overriding the `get_renderables` method. It creates a custom `Progress` class that renders a `Panel` around the progress display.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/progress.rst#2025-04-16_snippet_8

LANGUAGE: python
CODE:
```
from rich.panel import Panel
from rich.progress import Progress

class MyProgress(Progress):
    def get_renderables(self):
        yield Panel(self.make_tasks_table(self.tasks))
```

----------------------------------------

TITLE: Creating a Rich Console Object
DESCRIPTION: Creates a Console object which provides more control over rich terminal content. The Console is the main interface for creating sophisticated formatted output.
SOURCE: https://github.com/Textualize/rich/blob/master/README.md#2025-04-16_snippet_3

LANGUAGE: python
CODE:
```
from rich.console import Console

console = Console()
```

----------------------------------------

TITLE: Reading Files with Progress Bar using Rich
DESCRIPTION: This example demonstrates how to generate a progress bar while reading a file using `rich.progress.open`. It opens a JSON file and displays a progress bar while loading the JSON data.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/progress.rst#2025-04-16_snippet_9

LANGUAGE: python
CODE:
```
import json
import rich.progress

with rich.progress.open("data.json", "rb") as file:
    data = json.load(file)
print(data)
```

----------------------------------------

TITLE: Basic Rich Markup Example - Python
DESCRIPTION: Demonstrates basic usage of Rich's markup syntax for styling text with bold and red colors.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/markup.rst#2025-04-16_snippet_0

LANGUAGE: python
CODE:
```
from rich import print
print("[bold red]alert![/bold red] Something happened")
```

----------------------------------------

TITLE: Using Rich's markup for inline styling
DESCRIPTION: Demonstration of Rich's bbcode-like markup syntax for inline text styling. This allows applying different styles to specific portions of text within a single print statement.
SOURCE: https://github.com/Textualize/rich/blob/master/README.hi.md#2025-04-16_snippet_7

LANGUAGE: python
CODE:
```
console.print("Where there is a [bold cyan]Will[/bold cyan] there [u]is[/u] a [i]way[/i].")
```

----------------------------------------

TITLE: Using Rich Markup for Advanced Formatting
DESCRIPTION: Example using Rich's markup syntax for inline styling similar to BBCode. This allows mixing multiple styles within a single string including bold, underline, and italic text.
SOURCE: https://github.com/Textualize/rich/blob/master/README.pt-br.md#2025-04-16_snippet_7

LANGUAGE: python
CODE:
```
console.print("Where there is a [bold cyan]Will[/bold cyan] there [u]is[/u] a [i]way[/i].")
```

----------------------------------------

TITLE: Using Rich Markup for Detailed Styling
DESCRIPTION: Example showing Rich's bbcode-like markup syntax for applying multiple styles to different parts of text within a single output string.
SOURCE: https://github.com/Textualize/rich/blob/master/README.de.md#2025-04-16_snippet_7

LANGUAGE: python
CODE:
```
console.print("Where there is a [bold cyan]Will[/bold cyan] there [u]is[/u] a [i]way[/i].")
```

----------------------------------------

TITLE: Using Rich markup for inline styling
DESCRIPTION: Demonstration of Rich's BBCode-like markup syntax for applying styles to specific portions of text within a console.print call.
SOURCE: https://github.com/Textualize/rich/blob/master/README.sv.md#2025-04-16_snippet_7

LANGUAGE: python
CODE:
```
console.print("Where there is a [bold cyan]Will[/bold cyan] there [u]is[/u] a [i]way[/i].")
```

----------------------------------------

TITLE: Logging with Rich Console
DESCRIPTION: This code snippet demonstrates how to use the `Console` object from the Rich library to log data with syntax highlighting and pretty formatting. It includes an example of logging a list of dictionaries and local variables.
SOURCE: https://github.com/Textualize/rich/blob/master/README.kr.md#2025-04-16_snippet_7

LANGUAGE: python
CODE:
```
from rich.console import Console
console = Console()

test_data = [
    {"jsonrpc": "2.0", "method": "sum", "params": [None, 1, 2, 4, False, True], "id": "1",},
    {"jsonrpc": "2.0", "method": "notify_hello", "params": [7]},
    {"jsonrpc": "2.0", "method": "subtract", "params": [42, 23], "id": "2"},
]

def test_log():
    enabled = False
    context = {
        "foo": "bar",
    }
    movies = ["Deadpool", "Rise of the Skywalker"]
    console.log("Hello from", console, "!")
    console.log(test_data, log_locals=True)


test_log()
```

----------------------------------------

TITLE: Applying Style to Text using Rich
DESCRIPTION: This snippet demonstrates how to create a styled text instance using the Rich library and apply a specific style to a segment of the text. It utilizes the Console and Text classes from the rich module.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/text.rst#2025-04-16_snippet_0

LANGUAGE: python
CODE:
```
from rich.console import Console
from rich.text import Text

console = Console()
text = Text("Hello, World!")
text.stylize("bold magenta", 0, 6)
console.print(text)
```

----------------------------------------

TITLE: Rich Logging with Markup and Highlighting
DESCRIPTION: Examples of how to use markup and custom highlighting in Rich logging messages using the extra parameter.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/logging.rst#2025-04-16_snippet_1

LANGUAGE: python
CODE:
```
log.error("[bold red blink]Server is shutting down![/]", extra={"markup": True})

log.error("123 will not be highlighted", extra={"highlighter": None})
```

----------------------------------------

TITLE: Creating a Simple Tree in Rich (Python)
DESCRIPTION: This code snippet demonstrates the creation of a simple tree structure with a single label using the Rich library. It imports the necessary classes from Rich and initializes a Tree instance with a text label. The output is a minimal representation of the tree.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/tree.rst#2025-04-16_snippet_0

LANGUAGE: python
CODE:
```
from rich.tree import Tree\nfrom rich import print\n\ntree = Tree("Rich Tree")\nprint(tree)
```

----------------------------------------

TITLE: Using Rich Inspect Function
DESCRIPTION: Demonstrates the Rich inspect function which produces a detailed report of any Python object. The example shows inspecting a list with methods=True to include method information.
SOURCE: https://github.com/Textualize/rich/blob/master/README.md#2025-04-16_snippet_7

LANGUAGE: python
CODE:
```
>>> my_list = ["foo", "bar"]
>>> from rich import inspect
>>> inspect(my_list, methods=True)
```

----------------------------------------

TITLE: Configuring sitecustomize.py Traceback Handler
DESCRIPTION: Automatically installs Rich traceback handler for virtual environment
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/traceback.rst#2025-04-16_snippet_2

LANGUAGE: python
CODE:
```
from rich.traceback import install
install(show_locals=True)
```

----------------------------------------

TITLE: Rich Markup Formatting
DESCRIPTION: Advanced example showing Rich's BBCode-style markup for text formatting
SOURCE: https://github.com/Textualize/rich/blob/master/README.tr.md#2025-04-16_snippet_6

LANGUAGE: python
CODE:
```
console.print("[bold red]Mustafa Kemal Atatürk[/bold red] [u](1881 - 10 Kasım 1938)[/u], [i]Türk asker ve devlet adamıdır[/i]. [bold cyan]Türk Kurtuluş Savaşı'nın başkomutanı ve Türkiye Cumhuriyeti'nin kurucusudur[/bold cyan].")
```

----------------------------------------

TITLE: Tracking Progress with Rich
DESCRIPTION: This snippet demonstrates how to use the `track` function from the `rich.progress` module to display a progress bar while iterating over a range of values.  It wraps a loop to visually indicate the progress of the loop's execution, enhancing the user experience during long-running processes.
SOURCE: https://github.com/Textualize/rich/blob/master/README.fa.md#2025-04-16_snippet_12

LANGUAGE: python
CODE:
```
from rich.progress import track

for step in track(range(100)):
    do_step(step)
```

----------------------------------------

TITLE: Highlight Code Using Syntax.from_path in Rich
DESCRIPTION: Shows the alternative constructor 'Syntax.from_path' for syntax highlighting. This method loads the code directly from the specified file path and auto-detects the file type, simplifying initialization.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/syntax.rst#2025-04-16_snippet_1

LANGUAGE: python
CODE:
```
from rich.console import Console
from rich.syntax import Syntax

console = Console()
syntax = Syntax.from_path("syntax.py")
console.print(syntax)
```

----------------------------------------

TITLE: Using Rich Inspect for Object Analysis in Python
DESCRIPTION: Example of using Rich's inspect function to generate a detailed report of a Python object.
SOURCE: https://github.com/Textualize/rich/blob/master/README.kr.md#2025-04-16_snippet_6

LANGUAGE: python
CODE:
```
>>> my_list = ["foo", "bar"]
>>> from rich import inspect
>>> inspect(my_list, methods=True)
```

----------------------------------------

TITLE: Creating a Tree Structure - Python
DESCRIPTION: This snippet demonstrates how to utilize the Rich library to display a tree structure, which can be useful for visualizing hierarchical data.
SOURCE: https://github.com/Textualize/rich/blob/master/README.ja.md#2025-04-16_snippet_12

LANGUAGE: sh
CODE:
```
python -m rich.tree
```

----------------------------------------

TITLE: Syntax Highlighting with Rich
DESCRIPTION: This snippet demonstrates how to use the Rich library to highlight Python code. It creates a `Syntax` object, specifying the code, language ("python"), and theme ("monokai"), and then prints it to the console.
SOURCE: https://github.com/Textualize/rich/blob/master/README.id.md#2025-04-16_snippet_8

LANGUAGE: python
CODE:
```
syntax = Syntax(my_code, "python", theme="monokai", line_numbers=True)
console = Console()
console.print(syntax)
```

----------------------------------------

TITLE: Splitting Layout Horizontally into Rows in Python
DESCRIPTION: Divides the "lower" sub-layout horizontally into two parts named "left" and "right" using the split_row method.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/layout.rst#2025-04-16_snippet_2

LANGUAGE: python
CODE:
```
layout["lower"].split_row(
    Layout(name="left"),
    Layout(name="right"),
)
print(layout)
```

----------------------------------------

TITLE: Printing to Console - Python
DESCRIPTION: This example shows how to use the Console object to print styled text to the terminal, demonstrating its similar interface to the built-in print function.
SOURCE: https://github.com/Textualize/rich/blob/master/README.ja.md#2025-04-16_snippet_5

LANGUAGE: python
CODE:
```
console.print("Hello", "World!")
```

----------------------------------------

TITLE: Applying Styles to Console Output
DESCRIPTION: Demonstration of adding color and style to terminal output using the style parameter with Rich's Console.print method.
SOURCE: https://github.com/Textualize/rich/blob/master/README.de.md#2025-04-16_snippet_6

LANGUAGE: python
CODE:
```
console.print("Hello", "World!", style="bold red")
```

----------------------------------------

TITLE: Console Print with Style Parameter
DESCRIPTION: Example of using the style parameter to apply bold red formatting to the entire output text.
SOURCE: https://github.com/Textualize/rich/blob/master/README.de-ch.md#2025-04-16_snippet_6

LANGUAGE: python
CODE:
```
console.print("Hello", "World!", style="bold red")
```

----------------------------------------

TITLE: Capturing Console Output with StringIO
DESCRIPTION: This example shows how to capture console output using a `StringIO` object. It redirects the console's output to a `StringIO` instance, allowing the printed text to be retrieved later with `getvalue()`.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/console.rst#2025-04-16_snippet_17

LANGUAGE: Python
CODE:
```
from io import StringIO
from rich.console import Console
console = Console(file=StringIO())
console.print("[bold red]Hello[/] World")
str_output = console.file.getvalue()
```

----------------------------------------

TITLE: Creating a Rainbow Highlighter Using Rich in Python
DESCRIPTION: This snippet showcases creating a RainbowHighlighter that highlights each character of a string with a random color using the Rich library. Highlighting is implemented by overriding the highlight method of the Highlighter class, applying a different color style to each character. Dependencies include random, rich.print, and rich.highlighter modules. Inputs are strings to be highlighted, and outputs are printed strings with each character styled with variable colors.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/highlighting.rst#2025-04-16_snippet_2

LANGUAGE: Python
CODE:
```
from random import randint

from rich import print
from rich.highlighter import Highlighter


class RainbowHighlighter(Highlighter):
    def highlight(self, text):
        for index in range(len(text)):
            text.stylize(f"color({randint(16, 255)})", index, index + 1)


rainbow = RainbowHighlighter()
print(rainbow("I must not fear. Fear is the mind-killer."))
```

----------------------------------------

TITLE: Implementing Directory Listing with Rich Columns in Python
DESCRIPTION: A basic implementation of a directory listing program using Rich's Columns class. The script takes a directory path as a command line argument and displays its contents in columns. It uses equal width columns that expand to fill the terminal width.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/columns.rst#2025-04-16_snippet_0

LANGUAGE: python
CODE:
```
import os
import sys

from rich import print
from rich.columns import Columns

if len(sys.argv) < 2:
    print("Usage: python columns.py DIRECTORY")
else:
    directory = os.listdir(sys.argv[1])
    columns = Columns(directory, equal=True, expand=True)
    print(columns)
```

----------------------------------------

TITLE: Basic Rich Print Usage with Formatting
DESCRIPTION: Example of using Rich's print function with formatting markup and emoji support, also demonstrating local variable inspection.
SOURCE: https://github.com/Textualize/rich/blob/master/README.de-ch.md#2025-04-16_snippet_2

LANGUAGE: python
CODE:
```
from rich import print

print("Hello, [bold magenta]World[/bold magenta]!", ":vampire:", locals())
```

----------------------------------------

TITLE: Status Indicator with Rich
DESCRIPTION: This code snippet demonstrates how to use the `status` method of the Rich `Console` class to display a spinner animation and a message while performing tasks. It simulates a background process with a spinner and log messages upon task completion.
SOURCE: https://github.com/Textualize/rich/blob/master/README.kr.md#2025-04-16_snippet_11

LANGUAGE: python
CODE:
```
from time import sleep
from rich.console import Console

console = Console()
tasks = [f"task {n}" for n in range(1, 11)]

with console.status("[bold green]Working on tasks...") as status:
    while tasks:
        task = tasks.pop(0)
        sleep(1)
        console.log(f"{task} complete")
```

----------------------------------------

TITLE: Using Rich inspect for object examination
DESCRIPTION: Example of using Rich's inspect function to produce a detailed report about a Python object, showing its attributes and methods with proper formatting.
SOURCE: https://github.com/Textualize/rich/blob/master/README.sv.md#2025-04-16_snippet_8

LANGUAGE: python
CODE:
```
>>> my_list = ["foo", "bar"]
>>> from rich import inspect
>>> inspect(my_list, methods=True)
```

----------------------------------------

TITLE: Emoji Printing with Rich
DESCRIPTION: This code snippet shows how to print emojis to the console using Rich by enclosing the emoji name between two colons. This requires the Rich library to be installed.
SOURCE: https://github.com/Textualize/rich/blob/master/README.kr.md#2025-04-16_snippet_8

LANGUAGE: python
CODE:
```
>>> console.print(":smiley: :vampire: :pile_of_poo: :thumbs_up: :raccoon:")
```

----------------------------------------

TITLE: Syntax Highlighting Code with Rich in Python
DESCRIPTION: Demonstrates creating a Syntax object to render code with syntax highlighting and line numbers
SOURCE: https://github.com/Textualize/rich/blob/master/README.cn.md#2025-04-16_snippet_8

LANGUAGE: python
CODE:
```
from rich.console import Console
from rich.syntax import Syntax

my_code = '''
def iter_first_last(values: Iterable[T]) -> Iterable[Tuple[bool, bool, T]]:
    """Iterate and generate a tuple with a flag for first and last value."""
    iter_values = iter(values)
    try:
        previous_value = next(iter_values)
    except StopIteration:
        return
    first = True
    for value in iter_values:
        yield first, False, previous_value
        first = False
        previous_value = value
    yield first, True, previous_value
'''
syntax = Syntax(my_code, "python", theme="monokai", line_numbers=True)
console = Console()
console.print(syntax)
```

----------------------------------------

TITLE: Building a Complex Tree Structure in Rich (Python)
DESCRIPTION: This code expands the tree structure by adding levels and branches using the Tree's add method. It illustrates how to create a more detailed and complex tree with multiple branches and sub-branches, demonstrating the flexibility of the Tree instance.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/tree.rst#2025-04-16_snippet_2

LANGUAGE: python
CODE:
```
baz_tree = tree.add("baz")\nbaz_tree.add("[red]Red").add("[green]Green").add("[blue]Blue")\nprint(tree)
```

----------------------------------------

TITLE: Testing Rich Installation
DESCRIPTION: Command to run a test of Rich after installation. This displays Rich's capabilities in the terminal.
SOURCE: https://github.com/Textualize/rich/blob/master/README.id.md#2025-04-16_snippet_1

LANGUAGE: sh
CODE:
```
python -m rich
```

----------------------------------------

TITLE: Using Rich Inspect for Object Examination
DESCRIPTION: Example demonstrating Rich's inspect function which generates a detailed report of any Python object, including its attributes and methods.
SOURCE: https://github.com/Textualize/rich/blob/master/README.de.md#2025-04-16_snippet_8

LANGUAGE: python
CODE:
```
>>> my_list = ["foo", "bar"]
>>> from rich import inspect
>>> inspect(my_list, methods=True)
```

----------------------------------------

TITLE: Creating a Panel with Title and Subtitle in Python
DESCRIPTION: Shows how to create a panel with both a title at the top and a subtitle at the bottom. This example creates a panel with 'Welcome' as the title and 'Thank you' as the subtitle.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/panel.rst#2025-04-16_snippet_2

LANGUAGE: python
CODE:
```
from rich import print
from rich.panel import Panel
print(Panel("Hello, [red]World!", title="Welcome", subtitle="Thank you"))
```

----------------------------------------

TITLE: Updating Live Display with Dynamic Table Generation in Python
DESCRIPTION: Shows how to update a live display by generating a new table in each iteration. This example demonstrates creating random data and updating the display using the update() method.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/live.rst#2025-04-16_snippet_1

LANGUAGE: python
CODE:
```
import random
import time

from rich.live import Live
from rich.table import Table


def generate_table() -> Table:
    """Make a new table."""
    table = Table()
    table.add_column("ID")
    table.add_column("Value")
    table.add_column("Status")

    for row in range(random.randint(2, 6)):
        value = random.random() * 100
        table.add_row(
            f"{row}", f"{value:3.2f}", "[red]ERROR" if value < 50 else "[green]SUCCESS"
        )
    return table


with Live(generate_table(), refresh_per_second=4) as live:
    for _ in range(40):
        time.sleep(0.4)
        live.update(generate_table())
```

----------------------------------------

TITLE: Using Rich Inspect Function in Python
DESCRIPTION: Example of using Rich's inspect function to generate a detailed report of a Python object.
SOURCE: https://github.com/Textualize/rich/blob/master/README.zh-tw.md#2025-04-16_snippet_5

LANGUAGE: Python
CODE:
```
>>> my_list = ["foo", "bar"]
>>> from rich import inspect
>>> inspect(my_list, methods=True)
```

----------------------------------------

TITLE: Using Rich Inspect to Examine Python Objects
DESCRIPTION: Example of using Rich's inspect function to produce a detailed report of a Python object, including its methods and properties.
SOURCE: https://github.com/Textualize/rich/blob/master/README.fr.md#2025-04-16_snippet_8

LANGUAGE: python
CODE:
```
>>> my_list = ["foo", "bar"]
>>> from rich import inspect
>>> inspect(my_list, methods=True)
```

----------------------------------------

TITLE: Using a Custom Console with Rich Progress
DESCRIPTION: This snippet demonstrates how to use a custom Console object with Rich Progress by passing it to the `Progress` constructor. It imports a custom console object and then prints a message using it before starting the progress.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/progress.rst#2025-04-16_snippet_7

LANGUAGE: python
CODE:
```
# from my_project import my_console # Placeholder for console import
from rich.console import Console

my_console = Console()

with Progress(console=my_console) as progress:
    my_console.print("[bold blue]Starting work!")
    # do_work(progress) # Placeholder for work execution
```

----------------------------------------

TITLE: Highlighting Words and Regular Expressions in Rich Text
DESCRIPTION: This snippet showcases methods for highlighting specific words or patterns in text using the highlight_words and highlight_regex methods in the Rich library's Text class.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/text.rst#2025-04-16_snippet_4

LANGUAGE: python
CODE:
```
# Here, include the relevant code to demonstrate highlighting methods.
```

----------------------------------------

TITLE: Using Rich markup for inline styling
DESCRIPTION: Demonstrates Rich's bbcode-like markup syntax for applying different styles to portions of text within a single string.
SOURCE: https://github.com/Textualize/rich/blob/master/README.fa.md#2025-04-16_snippet_7

LANGUAGE: python
CODE:
```
console.print("Where there is a [bold cyan]Will[/bold cyan] there [u]is[/u] a [i]way[/i].")
```

----------------------------------------

TITLE: Enable Line Numbers with Rich Syntax Highlighting
DESCRIPTION: Includes line numbers in the output by setting 'line_numbers=True' in the 'Syntax.from_path' method. This feature is useful for enhancing readability and reference purposes.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/syntax.rst#2025-04-16_snippet_2

LANGUAGE: python
CODE:
```
syntax = Syntax.from_path("syntax.py", line_numbers=True)
```

----------------------------------------

TITLE: Customizing Progress Bar Columns with Rich
DESCRIPTION: This code snippet demonstrates how to customize the columns of a Rich progress bar using the `Column` constructor and `table_column` argument. It creates a progress bar where the description takes one-third of the terminal width, and the bar takes up the remaining two-thirds.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/progress.rst#2025-04-16_snippet_5

LANGUAGE: python
CODE:
```
from time import sleep

from rich.table import Column
from rich.progress import Progress, BarColumn, TextColumn

text_column = TextColumn("{task.description}", table_column=Column(ratio=1))
bar_column = BarColumn(bar_width=None, table_column=Column(ratio=2))
progress = Progress(text_column, bar_column, expand=True)

with progress:
    for n in progress.track(range(100)):
        progress.print(n)
        sleep(0.1)
```

----------------------------------------

TITLE: Basic Console Printing
DESCRIPTION: Basic example of using the Console object's print method. This method automatically word-wraps text to fit the terminal width.
SOURCE: https://github.com/Textualize/rich/blob/master/README.md#2025-04-16_snippet_4

LANGUAGE: python
CODE:
```
console.print("Hello", "World!")
```

----------------------------------------

TITLE: Creating Rich Console Object
DESCRIPTION: Importing and instantiating a Rich Console object for advanced terminal control. This object provides methods for rich output.
SOURCE: https://github.com/Textualize/rich/blob/master/README.id.md#2025-04-16_snippet_4

LANGUAGE: python
CODE:
```
from rich.console import Console

console = Console()
```

----------------------------------------

TITLE: Creating and Using Rich Console Object
DESCRIPTION: These snippets show how to create a Rich Console object and use it to print styled text.
SOURCE: https://github.com/Textualize/rich/blob/master/README.es.md#2025-04-16_snippet_4

LANGUAGE: python
CODE:
```
from rich.console import Console

console = Console()
```

LANGUAGE: python
CODE:
```
console.print("Hello", "World!")
```

LANGUAGE: python
CODE:
```
console.print("Hello", "World!", style="bold red")
```

LANGUAGE: python
CODE:
```
console.print("Where there is a [bold cyan]Will[/bold cyan] there [u]is[/u] a [i]way[/i].")
```

----------------------------------------

TITLE: Using Console Status with Spinner - Python
DESCRIPTION: This code shows how to use the Rich library's status method to display a spinner animation alongside a message while executing tasks in the console.
SOURCE: https://github.com/Textualize/rich/blob/master/README.ja.md#2025-04-16_snippet_11

LANGUAGE: python
CODE:
```
from time import sleep
from rich.console import Console

console = Console()
tasks = [f"task {n}" for n in range(1, 11)]

with console.status("[bold green]Working on tasks...") as status:
    while tasks:
        task = tasks.pop(0)
        sleep(1)
        console.log(f"{task} complete")
```

----------------------------------------

TITLE: Adding Panels to Layout Sections in Python
DESCRIPTION: Divides the "right" layout into two Panel objects containing text. This demonstrates adding Rich renderables to layout sections.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/layout.rst#2025-04-16_snippet_3

LANGUAGE: python
CODE:
```
from rich.panel import Panel

layout["right"].split(
    Layout(Panel("Hello")),
    Layout(Panel("World!"))
)
```

----------------------------------------

TITLE: Styled Console Print
DESCRIPTION: Example of using Rich Console print with style argument for colored output
SOURCE: https://github.com/Textualize/rich/blob/master/README.tr.md#2025-04-16_snippet_5

LANGUAGE: python
CODE:
```
console.print("Merhaba", "Dünya!", style="bold red")
```

----------------------------------------

TITLE: Printing Text with Square Brackets in Rich
DESCRIPTION: Demonstrates methods to print strings containing square brackets without losing content in Rich library. Provides two primary approaches: disabling markup or escaping strings.
SOURCE: https://github.com/Textualize/rich/blob/master/questions/square_brackets.question.md#2025-04-16_snippet_0

LANGUAGE: python
CODE:
```
# Disable markup
console.print(text, markup=False)

# Escape square brackets
console.print(text.replace("[", "\\[").replace("]", "\\]"))
```

----------------------------------------

TITLE: Rich Renderable Example
DESCRIPTION: This snippet demonstrates using a Rich renderable (Panel) to display styled content in the terminal. It shows how to create a panel with bold yellow text and a red border.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/introduction.rst#2025-04-16_snippet_6

LANGUAGE: python
CODE:
```
">>> from rich.panel import Panel\n>>> Panel.fit("[bold yellow]Hi, I'm a Panel", border_style=\"red\")"
```

----------------------------------------

TITLE: Applying Styles to Console Output
DESCRIPTION: Demonstration of adding styles to console output using the style parameter. This applies bold red formatting to the entire output string.
SOURCE: https://github.com/Textualize/rich/blob/master/README.pt-br.md#2025-04-16_snippet_6

LANGUAGE: python
CODE:
```
console.print("Hello", "World!", style="bold red")
```

----------------------------------------

TITLE: Custom Email Syntax Highlighting with RegexHighlighter in Python
DESCRIPTION: This snippet demonstrates creating a custom regex highlighter to style email-like patterns with Rich. It defines an EmailHighlighter class that matches email patterns in text, highlighting them with a specified style. Dependencies include the rich.console, rich.highlighter, and rich.theme modules. Inputs are strings with potential email addresses, and outputs are strings printed with highlighted email addresses, styled using the defined theme.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/highlighting.rst#2025-04-16_snippet_0

LANGUAGE: Python
CODE:
```
from rich.console import Console
from rich.highlighter import RegexHighlighter
from rich.theme import Theme

class EmailHighlighter(RegexHighlighter):
    """Apply style to anything that looks like an email."""

    base_style = "example."
    highlights = [r"(?P<email>[\w-]+@([\w-]+\.)+[\w-]+)"]


theme = Theme({"example.email": "bold magenta"})
console = Console(highlighter=EmailHighlighter(), theme=theme)
console.print("Send funds to money@example.org")
```

----------------------------------------

TITLE: Styling Error Console
DESCRIPTION: This example shows how to create an error console and apply a specific style to the output. It sets both `stderr=True` and `style="bold red"` to make error messages visually distinct.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/console.rst#2025-04-16_snippet_14

LANGUAGE: Python
CODE:
```
error_console = Console(stderr=True, style="bold red")
```

----------------------------------------

TITLE: Directing Output to File
DESCRIPTION: This snippet demonstrates directing Rich Console output to a file. It opens a file in write text mode, creates a Console instance directing output to that file, and then prints a formatted rule to the file using the console.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/console.rst#2025-04-16_snippet_15

LANGUAGE: Python
CODE:
```
import sys
from rich.console import Console
from datetime import datetime

with open("report.txt", "wt") as report_file:
    console = Console(file=report_file)
    console.rule(f"Report Generated {datetime.now().ctime()}")
```

----------------------------------------

TITLE: Printing with Rich Console in Python
DESCRIPTION: Examples of using Rich Console to print formatted text with styles and markup.
SOURCE: https://github.com/Textualize/rich/blob/master/README.kr.md#2025-04-16_snippet_5

LANGUAGE: python
CODE:
```
console.print("Hello", "World!")

console.print("Hello", "World!", style="bold red")

console.print("Where there is a [bold cyan]Will[/bold cyan] there [u]is[/u] a [i]way[/i].")
```

----------------------------------------

TITLE: Creating a Rich Console Object
DESCRIPTION: Code to create a Console object from Rich for more control over terminal output formatting. The Console object provides advanced formatting capabilities beyond the basic print function.
SOURCE: https://github.com/Textualize/rich/blob/master/README.pt-br.md#2025-04-16_snippet_4

LANGUAGE: python
CODE:
```
from rich.console import Console

console = Console()
```

----------------------------------------

TITLE: Grouping Renderables with Group Class in Python
DESCRIPTION: This example demonstrates how to use Rich's Group class to combine multiple Panel objects into a single renderable, which can then be wrapped in another Panel. It shows the basic pattern for when you know the renderables in advance.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/group.rst#2025-04-16_snippet_0

LANGUAGE: python
CODE:
```
from rich import print
from rich.console import Group
from rich.panel import Panel

panel_group = Group(
    Panel("Hello", style="on blue"),
    Panel("World", style="on red"),
)
print(Panel(panel_group))
```

----------------------------------------

TITLE: Creating a Table with Positional Arguments in Rich
DESCRIPTION: This snippet shows how to create a table by providing column names directly in the constructor. This allows for a simpler initialization of the table without additional attributes.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/tables.rst#2025-04-16_snippet_2

LANGUAGE: Python
CODE:
```
table = Table("Released", "Title", "Box Office", title="Star Wars Movies")
```

----------------------------------------

TITLE: Embedding Pretty Printed Data in a Panel - Python
DESCRIPTION: This section illustrates how to use the Pretty class from rich.pretty to create a renderable with pretty printed data embedded within a panel using the rich.panel module.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/pretty.rst#2025-04-16_snippet_3

LANGUAGE: Python
CODE:
```
from rich import print
from rich.pretty import Pretty
from rich.panel import Panel

pretty = Pretty(locals())
panel = Panel(pretty)
print(panel)
```

----------------------------------------

TITLE: Prompt with Choices and Case Sensitivity
DESCRIPTION: Demonstrates configuring a prompt with a list of valid choices and controlling case sensitivity
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/prompt.rst#2025-04-16_snippet_2

LANGUAGE: python
CODE:
```
from rich.prompt import Prompt
name = Prompt.ask("Enter your name", choices=["Paul", "Jessica", "Duncan"], default="Paul", case_sensitive=False)
```

----------------------------------------

TITLE: Creating Hyperlinks in Styled Text
DESCRIPTION: This snippet shows how to create hyperlinks by including a 'link' attribute in the style definition, converting styled text into a clickable link if supported by the terminal.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/style.rst#2025-04-16_snippet_2

LANGUAGE: Python
CODE:
```
console.print("Google", style="link https://google.com")
```

----------------------------------------

TITLE: Using Rich Markup for Detailed Styling in Python
DESCRIPTION: Demonstrates Rich's markup syntax for applying detailed styling to specific parts of the output text.
SOURCE: https://github.com/Textualize/rich/blob/master/README.ru.md#2025-04-16_snippet_7

LANGUAGE: python
CODE:
```
console.print("Where there is a [bold cyan]Will[/bold cyan] there [u]is[/u] a [i]way[/i].")
```

----------------------------------------

TITLE: Rich Inspect Usage
DESCRIPTION: Example demonstrating Rich's inspect function for examining Python objects
SOURCE: https://github.com/Textualize/rich/blob/master/README.tr.md#2025-04-16_snippet_7

LANGUAGE: python
CODE:
```
>>> my_list = ["foo", "bar"]
>>> from rich import inspect
>>> inspect(my_list, methods=True)
```

----------------------------------------

TITLE: Printing Emoji with Rich Console
DESCRIPTION: Shows how to print emoji characters in console output using Rich by placing emoji names between colons.
SOURCE: https://github.com/Textualize/rich/blob/master/README.md#2025-04-16_snippet_9

LANGUAGE: python
CODE:
```
>>> console.print(":smiley: :vampire: :pile_of_poo: :thumbs_up: :raccoon:")
😃 🧛 💩 👍 🦝
```

----------------------------------------

TITLE: Using Rich Markup for Inline Styling
DESCRIPTION: Demonstration of Rich's markup syntax for adding inline styling to portions of text, similar to BBCode.
SOURCE: https://github.com/Textualize/rich/blob/master/README.fr.md#2025-04-16_snippet_7

LANGUAGE: python
CODE:
```
console.print("Where there is a [bold cyan]Will[/bold cyan] there [u]is[/u] a [i]way[/i].")
```

----------------------------------------

TITLE: Basic String Prompt Input in Rich
DESCRIPTION: Demonstrates how to use Rich's Prompt.ask() method to collect a user's name as a string input
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/prompt.rst#2025-04-16_snippet_0

LANGUAGE: python
CODE:
```
from rich.prompt import Prompt
name = Prompt.ask("Enter your name")
```

----------------------------------------

TITLE: Creating a Basic Panel in Python
DESCRIPTION: Shows how to create a basic panel with text content that includes rich formatting. This example creates a panel with the text 'Hello, World!' where 'World!' is colored red.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/panel.rst#2025-04-16_snippet_0

LANGUAGE: python
CODE:
```
from rich import print
from rich.panel import Panel
print(Panel("Hello, [red]World!"))
```

----------------------------------------

TITLE: Displaying Text in Rich Panel
DESCRIPTION: This snippet demonstrates how to utilize a Text instance as content in a Panel while configuring text alignment. The justify parameter controls the alignment of the text within the panel.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/text.rst#2025-04-16_snippet_5

LANGUAGE: python
CODE:
```
from rich import print
from rich.panel import Panel
from rich.text import Text
panel = Panel(Text("Hello", justify="right"))
print(panel)
```

----------------------------------------

TITLE: Manual Progress Display Management in Python
DESCRIPTION: Demonstrates how to manually start and stop a Progress display without using a context manager, ensuring proper cleanup with a try/finally block.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/progress.rst#2025-04-16_snippet_2

LANGUAGE: python
CODE:
```
import time

from rich.progress import Progress

progress = Progress()
progress.start()
try:
    task1 = progress.add_task("[red]Downloading...", total=1000)
    task2 = progress.add_task("[green]Processing...", total=1000)
    task3 = progress.add_task("[cyan]Cooking...", total=1000)

    while not progress.finished:
        progress.update(task1, advance=0.5)
        progress.update(task2, advance=0.3)
        progress.update(task3, advance=0.9)
        time.sleep(0.02)
finally:
    progress.stop()
```

----------------------------------------

TITLE: Creating and Using Style Themes
DESCRIPTION: The snippet shows how to create a theme using the Theme class and apply it to a Console object. The example demonstrates defining named styles within a theme and highlights the semantic advantage, making the code more understandable.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/style.rst#2025-04-16_snippet_4

LANGUAGE: Python
CODE:
```
from rich.console import Console
from rich.theme import Theme
custom_theme = Theme({
    "info": "dim cyan",
    "warning": "magenta",
    "danger": "bold red"
})
console = Console(theme=custom_theme)
console.print("This is information", style="info")
console.print("[warning]The pod bay doors are locked[/warning]")
console.print("Something terrible happened!", style="danger")
```

----------------------------------------

TITLE: Wrapping Existing File Objects with Rich Progress
DESCRIPTION: This code demonstrates how to wrap an existing file object with a progress bar using `rich.progress.wrap_file`. It reads a URL from the internet and displays a progress bar while reading the content.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/progress.rst#2025-04-16_snippet_10

LANGUAGE: python
CODE:
```
from time import sleep
from urllib.request import urlopen

from rich.progress import wrap_file

response = urlopen("https://www.textualize.io")
size = int(response.headers["Content-Length"])

with wrap_file(response, size) as file:
    for line in file:
        print(line.decode("utf-8"), end="")
        sleep(0.1)
```

----------------------------------------

TITLE: Using Emojis in Console Output - Python
DESCRIPTION: This snippet demonstrates how to include emojis in console output using Rich by specifying emoji names enclosed in colons.
SOURCE: https://github.com/Textualize/rich/blob/master/README.ja.md#2025-04-16_snippet_8

LANGUAGE: python
CODE:
```
>>> console.print(":smiley: :vampire: :pile_of_poo: :thumbs_up: :raccoon:")
```

----------------------------------------

TITLE: Low-Level Custom Rendering with Segments in Python
DESCRIPTION: An example showing how to create custom rendering at the segment level for complete control over appearance. It yields individual Segment objects with different styles for each part of the output.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/protocol.rst#2025-04-16_snippet_2

LANGUAGE: python
CODE:
```
class MyObject:
    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        yield Segment("My", Style(color="magenta"))
        yield Segment("Object", Style(color="green"))
        yield Segment("()", Style(color="cyan"))
```

----------------------------------------

TITLE: Rendering Markdown Content
DESCRIPTION: Demonstrates how to render markdown content in the terminal using Rich's Markdown class.
SOURCE: https://github.com/Textualize/rich/blob/master/README.md#2025-04-16_snippet_14

LANGUAGE: python
CODE:
```
from rich.console import Console
from rich.markdown import Markdown

console = Console()
with open("README.md") as readme:
    markdown = Markdown(readme.read())
console.print(markdown)
```

----------------------------------------

TITLE: Converting ANSI escape codes to Text instance in Rich
DESCRIPTION: This snippet demonstrates how to convert a string with ANSI escape sequences into a 'Text' instance using the Rich library's 'from_ansi' method. This conversion is crucial for maintaining correct output alignment in UI components like Panel and Table when such escape codes are present.
SOURCE: https://github.com/Textualize/rich/blob/master/questions/ansi_escapes.question.md#2025-04-16_snippet_0

LANGUAGE: python
CODE:
```
Text.from_ansi(\"your_string_with_escape_codes\")
```

----------------------------------------

TITLE: Transient Progress Display in Python
DESCRIPTION: Shows how to create a transient progress display that disappears after completion, useful for more minimal terminal output.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/progress.rst#2025-04-16_snippet_3

LANGUAGE: python
CODE:
```
with Progress(transient=True) as progress:
    task = progress.add_task("Working", total=100)
    do_work(task)
```

----------------------------------------

TITLE: Configuring Layout Ratio in Rich
DESCRIPTION: Demonstrates how to set layout ratio to control space allocation between different layout sections. By adjusting the ratio, you can define the proportional screen space occupied by each layout component.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/layout.rst#2025-04-16_snippet_6

LANGUAGE: python
CODE:
```
layout["upper"].size = None
layout["upper"].ratio = 2
print(layout)
```

----------------------------------------

TITLE: Truncating Pretty Printed Output - Python
DESCRIPTION: In this snippet, the max_length and max_string arguments are used to control how much of a data structure or string is shown in the output, effectively truncating long lists or strings for better readability.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/pretty.rst#2025-04-16_snippet_2

LANGUAGE: Python
CODE:
```
>>> pprint(locals(), max_length=2)
```

LANGUAGE: Python
CODE:
```
>>> pprint("Where there is a Will, there is a Way", max_string=21)
```

----------------------------------------

TITLE: Using Rich's inspect function
DESCRIPTION: Shows how to use Rich's inspect function to generate detailed reports about Python objects. This example displays information about a list, including its methods.
SOURCE: https://github.com/Textualize/rich/blob/master/README.fa.md#2025-04-16_snippet_8

LANGUAGE: python
CODE:
```
>>> my_list = ["foo", "bar"]
>>> from rich import inspect
>>> inspect(my_list, methods=True)
```

----------------------------------------

TITLE: Printing with Rich Console in Python
DESCRIPTION: Demonstrates using the Rich Console's print method to output text, which automatically handles word wrapping to fit the terminal width.
SOURCE: https://github.com/Textualize/rich/blob/master/README.ru.md#2025-04-16_snippet_5

LANGUAGE: python
CODE:
```
console.print("Hello", "World!")
```

----------------------------------------

TITLE: Toggling Layout Visibility in Rich
DESCRIPTION: Illustrates how to dynamically show or hide layout sections by setting the `visible` attribute, allowing for flexible UI configuration based on application state.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/layout.rst#2025-04-16_snippet_8

LANGUAGE: python
CODE:
```
layout["upper"].visible = False
print(layout)

layout["upper"].visible = True
print(layout)
```

----------------------------------------

TITLE: Creating a Table with Rich - Python
DESCRIPTION: This code creates a table using the Rich library, demonstrating how to format table headers, styles, and justify columns while displaying data.
SOURCE: https://github.com/Textualize/rich/blob/master/README.ja.md#2025-04-16_snippet_9

LANGUAGE: python
CODE:
```
from rich.console import Console
from rich.table import Table

console = Console()

table = Table(show_header=True, header_style="bold magenta")
table.add_column("Date", style="dim", width=12)
table.add_column("Title")
table.add_column("Production Budget", justify="right")
table.add_column("Box Office", justify="right")
table.add_row(
    "Dec 20, 2019", "Star Wars: The Rise of Skywalker", "$275,000,000", "$375,126,118"
)
table.add_row(
    "May 25, 2018",
    "[red]Solo[/red]: A Star Wars Story",
    "$275,000,000",
    "$393,151,347",
)
table.add_row(
    "Dec 15, 2017",
    "Star Wars Ep. VIII: The Last Jedi",
    "$262,000,000",
    "[bold]$1,332,539,889[/bold]",
)

console.print(table)
```

----------------------------------------

TITLE: Creating Rules with Rich Console in Python
DESCRIPTION: Shows how to use the Console.rule() method to create horizontal lines with optional titles for dividing terminal output into sections.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/console.rst#2025-04-16_snippet_5

LANGUAGE: python
CODE:
```
>>> console.rule("[bold red]Chapter 2")
```

----------------------------------------

TITLE: Creating Text from ANSI Codes using Rich
DESCRIPTION: This snippet illustrates how to convert an ANSI formatted string into a Text object using the from_ansi method. This facilitates the usage of pre-formatted strings within the Rich library.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/text.rst#2025-04-16_snippet_2

LANGUAGE: python
CODE:
```
text = Text.from_ansi("\033[1;35mHello\033[0m, World!")
console.print(text.spans)
```

----------------------------------------

TITLE: Basic Padding Example in Python
DESCRIPTION: Demonstrates how to create basic padding with a single value (1) applied to all sides of the text. This creates a blank line above and below, and a space on the left and right edges.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/padding.rst#2025-04-16_snippet_0

LANGUAGE: python
CODE:
```
from rich import print
from rich.padding import Padding
test = Padding("Hello", 1)
print(test)
```

----------------------------------------

TITLE: Basic Console Print Example
DESCRIPTION: Simple example showing how to use the console.print method which automatically wraps text to fit terminal width.
SOURCE: https://github.com/Textualize/rich/blob/master/README.de-ch.md#2025-04-16_snippet_5

LANGUAGE: python
CODE:
```
console.print("Hello", "World!")
```

----------------------------------------

TITLE: Using Rich Print for Formatted Output in Python
DESCRIPTION: Example of using Rich's print function to output formatted text with colors and emojis.
SOURCE: https://github.com/Textualize/rich/blob/master/README.kr.md#2025-04-16_snippet_2

LANGUAGE: python
CODE:
```
from rich import print

print("Hello, [bold magenta]World[/bold magenta]!", ":vampire:", locals())
```

----------------------------------------

TITLE: Basic Rich Print Usage
DESCRIPTION: Demonstrates the basic usage of Rich's print function with text formatting and emoji support
SOURCE: https://github.com/Textualize/rich/blob/master/README.cn.md#2025-04-16_snippet_1

LANGUAGE: python
CODE:
```
from rich import print

print("Hello, [bold magenta]World[/bold magenta]!", ":vampire:", locals())
```

----------------------------------------

TITLE: Hyperlink Markup - Python
DESCRIPTION: Shows how to create clickable hyperlinks in terminal output using Rich markup.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/markup.rst#2025-04-16_snippet_4

LANGUAGE: python
CODE:
```
print("Visit my [link=https://www.willmcgugan.com]blog[/link]!")
```

----------------------------------------

TITLE: Rich Inspect Function Usage
DESCRIPTION: Demonstrates using Rich's inspect function to examine Python objects
SOURCE: https://github.com/Textualize/rich/blob/master/README.cn.md#2025-04-16_snippet_4

LANGUAGE: python
CODE:
```
>>> my_list = ["foo", "bar"]
>>> from rich import inspect
>>> inspect(my_list, methods=True)
```

----------------------------------------

TITLE: Configuring Column Attributes in Rich Tables
DESCRIPTION: This example demonstrates how to create a table with specific column attributes using the Column class. It customizes the header and the justification of columns.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/tables.rst#2025-04-16_snippet_3

LANGUAGE: Python
CODE:
```
from rich.table import Column, Table
table = Table(
    "Released",
    "Title",
    Column(header="Box Office", justify="right"),
    title="Star Wars Movies"
)
```

----------------------------------------

TITLE: Assembling Text Instances using Rich
DESCRIPTION: This snippet shows how to use the assemble method to combine multiple strings and styles into a single Text instance. It reflects the simplicity provided by the Rich library for creating complex styled text.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/text.rst#2025-04-16_snippet_3

LANGUAGE: python
CODE:
```
text = Text.assemble(("Hello", "bold magenta"), ", World!")
console.print(text)
```

----------------------------------------

TITLE: Exporting SVG with Theme
DESCRIPTION: This example demonstrates how to export console output to an SVG file with a custom theme applied. It imports a predefined theme (MONOKAI) and passes it to the `save_svg` method.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/console.rst#2025-04-16_snippet_12

LANGUAGE: Python
CODE:
```
from rich.console import Console
from rich.terminal_theme import MONOKAI

console = Console(record=True)
console.save_svg("example.svg", theme=MONOKAI)
```

----------------------------------------

TITLE: Basic Console Printing
DESCRIPTION: Example of using the Console object's print method for basic output. Unlike the native print function, this will automatically wrap text to fit the terminal width.
SOURCE: https://github.com/Textualize/rich/blob/master/README.pt-br.md#2025-04-16_snippet_5

LANGUAGE: python
CODE:
```
console.print("Hello", "World!")
```

----------------------------------------

TITLE: Using Rich Markdown from Command Line to Display README
DESCRIPTION: This command-line example shows how to use Rich's Markdown module directly to render a README.md file in the terminal.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/markdown.rst#2025-04-16_snippet_1

LANGUAGE: bash
CODE:
```
python -m rich.markdown README.md
```

----------------------------------------

TITLE: Expanding Pretty Printed Output - Python
DESCRIPTION: This example demonstrates how to use the expand_all argument in the pprint method to fully expand lists when pretty printing, providing all elements in the output.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/pretty.rst#2025-04-16_snippet_1

LANGUAGE: Python
CODE:
```
>>> pprint(["eggs", "ham"], expand_all=True)
```

----------------------------------------

TITLE: Command Line Interface for Rich Syntax Highlighting
DESCRIPTION: Explains how to use the Syntax class via the command line to highlight a Python file. It allows users to quickly view syntax highlighting without writing additional code. Users can pass arguments for further customization.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/syntax.rst#2025-04-16_snippet_3

LANGUAGE: python
CODE:
```
python -m rich.syntax syntax.py
```

----------------------------------------

TITLE: Using Rich's inspect function for object inspection
DESCRIPTION: Example of using Rich's inspect function to generate a detailed report about a Python object. The inspect function shows properties, methods, and other details in a formatted display.
SOURCE: https://github.com/Textualize/rich/blob/master/README.hi.md#2025-04-16_snippet_8

LANGUAGE: python
CODE:
```
>>> my_list = ["foo", "bar"]
>>> from rich import inspect
>>> inspect(my_list, methods=True)
```

----------------------------------------

TITLE: Creating Basic Live Display with Table in Python
DESCRIPTION: Demonstrates how to create a basic live display using a Table renderable. The example shows updating the table within a Live context manager, adding rows with a delay to simulate dynamic content.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/live.rst#2025-04-16_snippet_0

LANGUAGE: python
CODE:
```
import time

from rich.live import Live
from rich.table import Table

table = Table()
table.add_column("Row ID")
table.add_column("Description")
table.add_column("Level")

with Live(table, refresh_per_second=4):  # update 4 times a second to feel fluid
    for row in range(12):
        time.sleep(0.4)  # arbitrary delay
        # update the renderable internally
        table.add_row(f"{row}", f"description {row}", "[red]ERROR")
```

----------------------------------------

TITLE: Safe Dynamic Markup - Python
DESCRIPTION: Shows how to safely handle dynamic text input by escaping potential markup in user-provided strings.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/markup.rst#2025-04-16_snippet_6

LANGUAGE: python
CODE:
```
from rich.markup import escape
def greet(name):
    console.print(f"Hello {escape(name)}!")
```

----------------------------------------

TITLE: Basic Console Printing
DESCRIPTION: Example of using the Console class's print method for basic output, which automatically wraps text to fit terminal width.
SOURCE: https://github.com/Textualize/rich/blob/master/README.fr.md#2025-04-16_snippet_5

LANGUAGE: python
CODE:
```
console.print("Hello", "World!")
```

----------------------------------------

TITLE: Single Line Rich Styling - Python
DESCRIPTION: Shows how to apply multiple styles to a single line of text without closing tags.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/markup.rst#2025-04-16_snippet_1

LANGUAGE: python
CODE:
```
print("[bold italic yellow on red blink]This text is impossible to read")
```

----------------------------------------

TITLE: Custom Padding with Tuple Values in Python
DESCRIPTION: Shows how to use a tuple of values to set different padding for vertical and horizontal sides. This example creates 2 blank lines above and below the text, with 4 spaces on the left and right sides.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/padding.rst#2025-04-16_snippet_1

LANGUAGE: python
CODE:
```
from rich import print
from rich.padding import Padding
test = Padding("Hello", (2, 4))
print(test)
```

----------------------------------------

TITLE: Using EmailHighlighter as a Callable in Rich Python
DESCRIPTION: This snippet illustrates how to use a previously defined EmailHighlighter as a callable to highlight emails in strings. After creating the EmailHighlighter object, it is used programmatically to highlight email addresses in text, showcasing the flexibility of applying custom highlighters at various levels of granularity. Dependencies include the rich.console and the custom EmailHighlighter definition. Inputs involve strings containing email addresses, and outputs are printed strings with highlighted emails according to the defined theme.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/highlighting.rst#2025-04-16_snippet_1

LANGUAGE: Python
CODE:
```
console = Console(theme=theme)
highlight_emails = EmailHighlighter()
console.print(highlight_emails("Send funds to money@example.org"))
```

----------------------------------------

TITLE: Updating Layout Content in Python
DESCRIPTION: Updates the content of the "left" layout section with a text string using the update method.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/layout.rst#2025-04-16_snippet_4

LANGUAGE: python
CODE:
```
layout["left"].update(
    "The mystery of life isn't a problem to solve, but a reality to experience."
)
print(layout)
```

----------------------------------------

TITLE: Rendering Markdown with Rich in Python
DESCRIPTION: Shows how to read a Markdown file and render it in the console using Rich's Markdown rendering capabilities
SOURCE: https://github.com/Textualize/rich/blob/master/README.cn.md#2025-04-16_snippet_7

LANGUAGE: python
CODE:
```
from rich.console import Console
from rich.markdown import Markdown

console = Console()
with open("README.md") as readme:
    markdown = Markdown(readme.read())
console.print(markdown)
```

----------------------------------------

TITLE: Splitting Layout Vertically into Columns in Python
DESCRIPTION: Divides the layout vertically into two sub-layouts named "upper" and "lower" using the split_column method.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/layout.rst#2025-04-16_snippet_1

LANGUAGE: python
CODE:
```
layout.split_column(
    Layout(name="upper"),
    Layout(name="lower")
)
print(layout)
```

----------------------------------------

TITLE: Implementing Rich Protocol Method Example
DESCRIPTION: Example of the Rich library's protocol method for custom object representation, allowing objects to define how they should be displayed.
SOURCE: https://github.com/Textualize/rich/blob/master/CHANGELOG.md#2025-04-16_snippet_3

LANGUAGE: python
CODE:
```
__rich_repr__
```

----------------------------------------

TITLE: Spinner Command with Rich
DESCRIPTION: This command displays available spinner animations from the `cli-spinners` library that can be used with Rich's status feature.
SOURCE: https://github.com/Textualize/rich/blob/master/README.kr.md#2025-04-16_snippet_16

LANGUAGE: python
CODE:
```
python -m rich.spinner
```

----------------------------------------

TITLE: Printing Layout Tree Structure in Rich
DESCRIPTION: Demonstrates how to use the `tree` attribute to visualize the hierarchical structure and configuration of complex layouts for debugging and understanding UI composition.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/layout.rst#2025-04-16_snippet_9

LANGUAGE: python
CODE:
```
print(layout.tree)
```

----------------------------------------

TITLE: Exporting Console Output
DESCRIPTION: This example shows how to enable recording of console output and then export it as text. It initializes a Console with `record=True`, allowing subsequent output to be captured for later export.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/console.rst#2025-04-16_snippet_11

LANGUAGE: Python
CODE:
```
from rich.console import Console
console = Console(record=True)
```

----------------------------------------

TITLE: Printing Exceptions with Rich Console
DESCRIPTION: Demonstrates printing exceptions with local variable context using Rich Console
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/traceback.rst#2025-04-16_snippet_0

LANGUAGE: python
CODE:
```
from rich.console import Console
console = Console()

try:
    do_something()
except Exception:
    console.print_exception(show_locals=True)
```

----------------------------------------

TITLE: Styled Padding with Custom Expansion in Python
DESCRIPTION: Demonstrates applying a style to padding and using the expand parameter to control width. This example sets blue background for the padding area and prevents it from expanding to the full terminal width.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/padding.rst#2025-04-16_snippet_2

LANGUAGE: python
CODE:
```
from rich import print
from rich.padding import Padding
test = Padding("Hello", (2, 4), style="on blue", expand=False)
print(test)
```

----------------------------------------

TITLE: Emoji Markup Usage - Python
DESCRIPTION: Demonstrates how to use emoji codes in Rich markup, including emoji variants.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/markup.rst#2025-04-16_snippet_7

LANGUAGE: python
CODE:
```
>>> from rich import print
>>> print(":warning:")
>>> print(":red_heart-emoji:")
>>> print(":red_heart-text:")
```

----------------------------------------

TITLE: Displaying Rich Markdown Command Line Help
DESCRIPTION: This command shows how to access the help information for Rich's Markdown command-line interface, which displays all available arguments and options.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/markdown.rst#2025-04-16_snippet_2

LANGUAGE: bash
CODE:
```
python -m rich.markdown -h
```

----------------------------------------

TITLE: Installing Rich with pip in Python
DESCRIPTION: Command to install the Rich library using pip, Python's package manager. This is the standard method to add Rich to your Python environment.
SOURCE: https://github.com/Textualize/rich/blob/master/README.de.md#2025-04-16_snippet_0

LANGUAGE: sh
CODE:
```
python -m pip install rich
```

----------------------------------------

TITLE: Installing Rich with pip
DESCRIPTION: Command to install Rich using pip package manager. After installation, you can test the library by running the rich module directly.
SOURCE: https://github.com/Textualize/rich/blob/master/README.md#2025-04-16_snippet_0

LANGUAGE: sh
CODE:
```
python -m pip install rich
```

LANGUAGE: sh
CODE:
```
python -m rich
```

----------------------------------------

TITLE: Installing Rich with pip
DESCRIPTION: Command to install Rich library using pip package manager
SOURCE: https://github.com/Textualize/rich/blob/master/README.pl.md#2025-04-16_snippet_0

LANGUAGE: sh
CODE:
```
python -m pip install rich
```

----------------------------------------

TITLE: Styling Output with Rich Console in Python
DESCRIPTION: Shows how to add color and style to console output using Rich's style argument in the print method.
SOURCE: https://github.com/Textualize/rich/blob/master/README.ru.md#2025-04-16_snippet_6

LANGUAGE: python
CODE:
```
console.print("Hello", "World!", style="bold red")
```

----------------------------------------

TITLE: Updating Alternate Screen
DESCRIPTION: This code snippet showcases how to update the alternate screen with a renderable object. It displays a countdown with blinking text centered on a panel in the alternate screen.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/console.rst#2025-04-16_snippet_20

LANGUAGE: Python
CODE:
```
from time import sleep

from rich.console import Console
from rich.align import Align
from rich.text import Text
from rich.panel import Panel

console = Console()

with console.screen(style="bold white on red") as screen:
    for count in range(5, 0, -1):
        text = Align.center(
            Text.from_markup(f"[blink]Don't Panic![/blink]\n{count}", justify="center"),
            vertical="middle",
        )
        screen.update(Panel(text))
        sleep(1)
```

----------------------------------------

TITLE: Customizing Default Styles in Rich
DESCRIPTION: This snippet shows how to customize default styles by overriding them in a custom Theme. Use "inherit=False" to prevent default styles from merging into the custom theme.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/style.rst#2025-04-16_snippet_5

LANGUAGE: Python
CODE:
```
from rich.console import Console
from rich.theme import Theme
console = Console(theme=Theme({"repr.number": "bold green blink"}))
console.print("The total is 128")
```

----------------------------------------

TITLE: Rich REPL Installation
DESCRIPTION: Code to install Rich in Python REPL for pretty printing of data types
SOURCE: https://github.com/Textualize/rich/blob/master/README.tr.md#2025-04-16_snippet_2

LANGUAGE: python
CODE:
```
>>> from rich import pretty
>>> pretty.install()
```

----------------------------------------

TITLE: Capturing Console Output with Context Manager
DESCRIPTION: This code demonstrates how to capture the output from a Rich Console using a context manager. It uses `console.capture()` to redirect the output, then retrieves the captured string with `capture.get()`.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/console.rst#2025-04-16_snippet_16

LANGUAGE: Python
CODE:
```
from rich.console import Console
console = Console()
with console.capture() as capture:
    console.print("[bold red]Hello[/] World")
str_output = capture.get()
```

----------------------------------------

TITLE: Using Rich Print for Formatted Output in Python
DESCRIPTION: Example of using Rich's print function to output formatted text with colors and emojis.
SOURCE: https://github.com/Textualize/rich/blob/master/README.zh-tw.md#2025-04-16_snippet_2

LANGUAGE: Python
CODE:
```
from rich import print

print("Hello, [bold magenta]World[/bold magenta]!", ":vampire:", locals())
```

----------------------------------------

TITLE: Installing Rich in Python REPL
DESCRIPTION: Code to integrate Rich into the Python REPL environment for pretty-printing and highlighting of data structures.
SOURCE: https://github.com/Textualize/rich/blob/master/README.de-ch.md#2025-04-16_snippet_3

LANGUAGE: python
CODE:
```
>>> from rich import pretty
>>> pretty.install()
```

----------------------------------------

TITLE: Installing Rich in Python REPL
DESCRIPTION: Code to configure Rich for use in Python's interactive console (REPL). This enhances the REPL by formatting and highlighting all output.
SOURCE: https://github.com/Textualize/rich/blob/master/README.fa.md#2025-04-16_snippet_3

LANGUAGE: python
CODE:
```
>>> from rich import pretty
>>> pretty.install()
```

----------------------------------------

TITLE: Installing Rich in Python REPL
DESCRIPTION: Code to install Rich in Python REPL for pretty-printing and syntax highlighting of data structures.
SOURCE: https://github.com/Textualize/rich/blob/master/README.zh-tw.md#2025-04-16_snippet_3

LANGUAGE: Python
CODE:
```
>>> from rich import pretty
>>> pretty.install()
```

----------------------------------------

TITLE: Installing Rich in Python REPL
DESCRIPTION: Code to install Rich's pretty printing in the Python REPL environment. This enhances the display of all data structures with proper formatting and syntax highlighting.
SOURCE: https://github.com/Textualize/rich/blob/master/README.pt-br.md#2025-04-16_snippet_3

LANGUAGE: python
CODE:
```
>>> from rich import pretty
>>> pretty.install()
```

----------------------------------------

TITLE: Installing Rich in Python REPL
DESCRIPTION: Code to install Rich in the Python REPL, which will format all output using Rich's styling capabilities.
SOURCE: https://github.com/Textualize/rich/blob/master/README.ru.md#2025-04-16_snippet_3

LANGUAGE: python
CODE:
```
>>> from rich import pretty
>>> pretty.install()
```

----------------------------------------

TITLE: Using Rich Inspector Function
DESCRIPTION: This example demonstrates the use of Rich's inspect function to display detailed information about a Python object.
SOURCE: https://github.com/Textualize/rich/blob/master/README.es.md#2025-04-16_snippet_5

LANGUAGE: python
CODE:
```
>>> my_list = ["foo", "bar"]
>>> from rich import inspect
>>> inspect(my_list, methods=True)
```

----------------------------------------

TITLE: Using Rich Console Markup
DESCRIPTION: Example of using Rich's markup syntax for inline styling. This demonstrates how to apply multiple styles within a single string.
SOURCE: https://github.com/Textualize/rich/blob/master/README.id.md#2025-04-16_snippet_6

LANGUAGE: python
CODE:
```
console.print("Where there is a [bold cyan]Will[/bold cyan] there [u]is[/u] a [i]way[/i].")
```

----------------------------------------

TITLE: Using Rich Print Function in Python
DESCRIPTION: This snippet demonstrates how to use Rich's print function to output styled text and emojis.
SOURCE: https://github.com/Textualize/rich/blob/master/README.es.md#2025-04-16_snippet_2

LANGUAGE: python
CODE:
```
from rich import print

print("Hello, [bold magenta]World[/bold magenta]!", ":vampire:", locals())
```

----------------------------------------

TITLE: Basic Console Print
DESCRIPTION: Simple example of using Rich Console print method
SOURCE: https://github.com/Textualize/rich/blob/master/README.tr.md#2025-04-16_snippet_4

LANGUAGE: python
CODE:
```
console.print("Merhaba", "Dünya!")
```

----------------------------------------

TITLE: Setting Minimum Layout Size in Rich
DESCRIPTION: Shows how to set a minimum size for a layout section to prevent it from shrinking below a specified number of rows, ensuring a minimum visibility threshold for UI components.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/layout.rst#2025-04-16_snippet_7

LANGUAGE: python
CODE:
```
layout["lower"].minimum_size = 10
```

----------------------------------------

TITLE: Using Rich Print Function in Python
DESCRIPTION: Example of using Rich's print function to output formatted text with colors and emojis, as well as displaying local variables.
SOURCE: https://github.com/Textualize/rich/blob/master/README.ru.md#2025-04-16_snippet_2

LANGUAGE: python
CODE:
```
from rich import print

print("Hello, [bold magenta]World[/bold magenta]!", ":vampire:", locals())
```

----------------------------------------

TITLE: Importing Rich Print Function
DESCRIPTION: This snippet demonstrates how to import the Rich print function, which replaces the built-in Python print function to enable rich text and formatting capabilities.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/introduction.rst#2025-04-16_snippet_2

LANGUAGE: python
CODE:
```
"from rich import print"
```

----------------------------------------

TITLE: Using Rich Inspect Function
DESCRIPTION: Example of using Rich's inspect function to display detailed information about a Python object. This demonstrates Rich's capability to provide rich, formatted output for debugging and exploration.
SOURCE: https://github.com/Textualize/rich/blob/master/README.id.md#2025-04-16_snippet_7

LANGUAGE: python
CODE:
```
>>> my_list = ["foo", "bar"]
>>> from rich import inspect
>>> inspect(my_list, methods=True)
```

----------------------------------------

TITLE: Styling text with Console print
DESCRIPTION: Shows how to apply styling to all text in a Console print call using the style parameter. This example applies bold red formatting to the output.
SOURCE: https://github.com/Textualize/rich/blob/master/README.fa.md#2025-04-16_snippet_6

LANGUAGE: python
CODE:
```
console.print("Hello", "World!", style="bold red")
```

----------------------------------------

TITLE: Styling Console Output
DESCRIPTION: Demonstrates adding styles to the entire Console output using the style parameter. This applies bold red formatting to all the text in the print statement.
SOURCE: https://github.com/Textualize/rich/blob/master/README.md#2025-04-16_snippet_5

LANGUAGE: python
CODE:
```
console.print("Hello", "World!", style="bold red")
```

----------------------------------------

TITLE: Installing Rich Library - Python
DESCRIPTION: The code snippet shows how to install the Rich library using pip, ensuring that the user can utilize its capabilities for enhancing terminal output.
SOURCE: https://github.com/Textualize/rich/blob/master/README.ja.md#2025-04-16_snippet_0

LANGUAGE: sh
CODE:
```
python -m pip install rich
```

----------------------------------------

TITLE: Displaying Columns with Rich
DESCRIPTION: This snippet shows how to display the contents of a directory in columns using the `rich.columns` module. The script takes a directory path as a command-line argument and displays the directory's contents in a formatted column layout using Rich's `Columns` class.
SOURCE: https://github.com/Textualize/rich/blob/master/README.fa.md#2025-04-16_snippet_16

LANGUAGE: python
CODE:
```
import os
import sys

from rich import print
from rich.columns import Columns

directory = os.listdir(sys.argv[1])
print(Columns(directory))
```

----------------------------------------

TITLE: Shorthand Style Closing - Python
DESCRIPTION: Demonstrates using the shorthand [/] syntax to close the last opened style.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/markup.rst#2025-04-16_snippet_2

LANGUAGE: python
CODE:
```
print("[bold red]Bold and red[/] not bold or red")
```

----------------------------------------

TITLE: Testing Rich Output in Python
DESCRIPTION: Command to test Rich output in the terminal after installation.
SOURCE: https://github.com/Textualize/rich/blob/master/README.kr.md#2025-04-16_snippet_1

LANGUAGE: sh
CODE:
```
python -m rich
```

----------------------------------------

TITLE: Testing Rich output in terminal
DESCRIPTION: Command to run a demonstration of Rich's capabilities directly in your terminal. This shows various formatting and styling features available in the library.
SOURCE: https://github.com/Textualize/rich/blob/master/README.hi.md#2025-04-16_snippet_1

LANGUAGE: shell
CODE:
```
python -m rich
```

----------------------------------------

TITLE: Console Print with Rich Markup
DESCRIPTION: Demonstration of Rich's bbcode-like markup for applying different styles to specific portions of text.
SOURCE: https://github.com/Textualize/rich/blob/master/README.de-ch.md#2025-04-16_snippet_7

LANGUAGE: python
CODE:
```
console.print("Where there is a [bold cyan]Will[/bold cyan] there [u]is[/u] a [i]way[/i].")
```

----------------------------------------

TITLE: Styled Console Output - Python
DESCRIPTION: This code showcases how to print styled text using the Console object, applying the 'bold red' style to the output.
SOURCE: https://github.com/Textualize/rich/blob/master/README.ja.md#2025-04-16_snippet_6

LANGUAGE: python
CODE:
```
console.print("Hello", "World!", style="bold red")
```

----------------------------------------

TITLE: Adding Style to Console Output
DESCRIPTION: Example showing how to apply styles to entire text output using the style keyword argument.
SOURCE: https://github.com/Textualize/rich/blob/master/README.fr.md#2025-04-16_snippet_6

LANGUAGE: python
CODE:
```
console.print("Hello", "World!", style="bold red")
```

----------------------------------------

TITLE: Installing Rich with pip
DESCRIPTION: Command to install the Rich library using pip package manager
SOURCE: https://github.com/Textualize/rich/blob/master/README.cn.md#2025-04-16_snippet_0

LANGUAGE: sh
CODE:
```
python -m pip install rich
```

----------------------------------------

TITLE: Testing Rich Output in Terminal
DESCRIPTION: Command to test Rich's formatting capabilities directly in your terminal. Running this will display a showcase of Rich's features.
SOURCE: https://github.com/Textualize/rich/blob/master/README.pt-br.md#2025-04-16_snippet_1

LANGUAGE: sh
CODE:
```
python -m rich
```

----------------------------------------

TITLE: Suppressing Framework Frames in Rich Logging
DESCRIPTION: Demonstrates how to configure Rich logging to suppress framework-specific frames in tracebacks, using Click framework as an example.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/logging.rst#2025-04-16_snippet_3

LANGUAGE: python
CODE:
```
import click
import logging
from rich.logging import RichHandler

logging.basicConfig(
    level="NOTSET",
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True, tracebacks_suppress=[click])]
)
```

----------------------------------------

TITLE: Defining Rich Traceback Omission in Python
DESCRIPTION: Python code blocks can opt out of being rendered in Rich tracebacks by setting a _rich_traceback_omit flag in their local scope.
SOURCE: https://github.com/Textualize/rich/blob/master/CHANGELOG.md#2025-04-16_snippet_0

LANGUAGE: python
CODE:
```
_rich_traceback_omit = True
```

----------------------------------------

TITLE: Using Rich's Inspect Function
DESCRIPTION: Example of using Rich's inspect function to generate a detailed report of a Python object. This shows an enhanced view of a list object including its methods.
SOURCE: https://github.com/Textualize/rich/blob/master/README.pt-br.md#2025-04-16_snippet_8

LANGUAGE: python
CODE:
```
>>> my_list = ["foo", "bar"]
>>> from rich import inspect
>>> inspect(my_list, methods=True)
```

----------------------------------------

TITLE: Creating a Console Instance - Python
DESCRIPTION: This code creates a Console object from the Rich library, allowing for enhanced control over terminal content output.
SOURCE: https://github.com/Textualize/rich/blob/master/README.ja.md#2025-04-16_snippet_4

LANGUAGE: python
CODE:
```
from rich.console import Console

console = Console()
```

----------------------------------------

TITLE: Initializing Console with Style
DESCRIPTION: This code snippet demonstrates how to initialize a Rich Console instance with a specific style applied to all printed output. It creates a console that prints text with a white font on a blue background.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/console.rst#2025-04-16_snippet_9

LANGUAGE: Python
CODE:
```
from rich.console import Console
blue_console = Console(style="white on blue")
blue_console.print("I'm blue. Da ba dee da ba di.")
```

----------------------------------------

TITLE: Installing Rich with pip
DESCRIPTION: This snippet shows how to install the Rich library using pip, the Python package installer. The -U flag is used to update Rich if it is already installed.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/introduction.rst#2025-04-16_snippet_0

LANGUAGE: shell
CODE:
```
"pip install rich"
```

----------------------------------------

TITLE: Installing Rich Python Library
DESCRIPTION: Command to install Rich using pip package manager. This installs the latest version of Rich from PyPI.
SOURCE: https://github.com/Textualize/rich/blob/master/README.id.md#2025-04-16_snippet_0

LANGUAGE: sh
CODE:
```
python -m pip install rich
```

----------------------------------------

TITLE: Rich Console Screen Control Methods
DESCRIPTION: Control methods for screen manipulation in Rich console, including cursor movement and screen clearing operations.
SOURCE: https://github.com/Textualize/rich/blob/master/CHANGELOG.md#2025-04-16_snippet_4

LANGUAGE: python
CODE:
```
Control.segment
Control.bell
Control.home
Control.move_to
Control.clear
Control.show_cursor
Control.alt_screen
```

----------------------------------------

TITLE: Creating and Using Rich Console Object in Python
DESCRIPTION: Example of creating a Rich Console object and using it to print formatted text.
SOURCE: https://github.com/Textualize/rich/blob/master/README.zh-tw.md#2025-04-16_snippet_4

LANGUAGE: Python
CODE:
```
from rich.console import Console

console = Console()
console.print("Hello", "World!")
console.print("Hello", "World!", style="bold red")
console.print("Where there is a [bold cyan]Will[/bold cyan] there [u]is[/u] a [i]way[/i].")
```

----------------------------------------

TITLE: Installing Pretty in Python REPL - Python
DESCRIPTION: This code installs the pretty print functionality of the Rich library in the Python REPL, enabling visually appealing data representations.
SOURCE: https://github.com/Textualize/rich/blob/master/README.ja.md#2025-04-16_snippet_2

LANGUAGE: python
CODE:
```
>>> from rich import pretty
>>> pretty.install()
```

----------------------------------------

TITLE: Viewing Available Box Styles
DESCRIPTION: Command to generate a table displaying all available box styles in Rich. Running this command will create a visual reference of the different box drawing options.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/appendix/box.rst#2025-04-16_snippet_1

LANGUAGE: python
CODE:
```
python -m rich.box
```

----------------------------------------

TITLE: Installing Rich with pip
DESCRIPTION: Command to install Rich Python library using pip package manager
SOURCE: https://github.com/Textualize/rich/blob/master/README.tr.md#2025-04-16_snippet_0

LANGUAGE: sh
CODE:
```
python -m pip install rich
```

----------------------------------------

TITLE: Creating a Rich Console Object in Python
DESCRIPTION: Importing and initializing a Rich Console object for advanced terminal output.
SOURCE: https://github.com/Textualize/rich/blob/master/README.kr.md#2025-04-16_snippet_4

LANGUAGE: python
CODE:
```
from rich.console import Console

console = Console()
```

----------------------------------------

TITLE: Recursive Error with Frame Limit
DESCRIPTION: Demonstrates handling recursive errors with frame limit configuration
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/traceback.rst#2025-04-16_snippet_4

LANGUAGE: python
CODE:
```
from rich.console import Console

def foo(n):
    return bar(n)

def bar(n):
    return foo(n)

console = Console()

try:
    foo(1)
except Exception:
    console.print_exception(max_frames=20)
```

----------------------------------------

TITLE: Sphinx Automodule Documentation Configuration
DESCRIPTION: ReStructuredText configuration for automatically generating documentation from the rich.console module, including all members.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/reference/console.rst#2025-04-16_snippet_0

LANGUAGE: rst
CODE:
```
.. automodule:: rich.console
    :members:
```

----------------------------------------

TITLE: Printing with Rich Console
DESCRIPTION: Examples of using the Rich Console object to print text. These demonstrate basic printing and adding styles to the output.
SOURCE: https://github.com/Textualize/rich/blob/master/README.id.md#2025-04-16_snippet_5

LANGUAGE: python
CODE:
```
console.print("Hello", "World!")

console.print("Hello", "World!", style="bold red")
```

----------------------------------------

TITLE: Using Rich Print Function for Enhanced Output
DESCRIPTION: Example of using Rich's print function to display colored and styled text along with emoji and variables in the terminal.
SOURCE: https://github.com/Textualize/rich/blob/master/README.fr.md#2025-04-16_snippet_2

LANGUAGE: python
CODE:
```
from rich import print

print("Hello, [bold magenta]World[/bold magenta]!", ":vampire:", locals())
```

----------------------------------------

TITLE: Handling Empty Tables in Rich
DESCRIPTION: This code snippet checks if the table has columns and decides whether to print the table or a message indicating no data. It is useful for scenarios where a table might be dynamically generated.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/tables.rst#2025-04-16_snippet_1

LANGUAGE: Python
CODE:
```
if table.columns:
    print(table)
else:
    print("[i]No data...[/i]")
```

----------------------------------------

TITLE: Testing Rich Output in Terminal
DESCRIPTION: Command to run a Rich demo that displays various formatting capabilities in the terminal.
SOURCE: https://github.com/Textualize/rich/blob/master/README.ru.md#2025-04-16_snippet_1

LANGUAGE: sh
CODE:
```
python -m rich
```

----------------------------------------

TITLE: Creating a Rich Console Object
DESCRIPTION: Example of importing and instantiating a Console object from Rich for more control over terminal output.
SOURCE: https://github.com/Textualize/rich/blob/master/README.de-ch.md#2025-04-16_snippet_4

LANGUAGE: python
CODE:
```
from rich.console import Console

console = Console()
```

----------------------------------------

TITLE: Installing Rich in Python REPL
DESCRIPTION: Code to install Rich in the Python REPL environment, which will automatically format and highlight all data structures in the interactive session.
SOURCE: https://github.com/Textualize/rich/blob/master/README.sv.md#2025-04-16_snippet_3

LANGUAGE: python
CODE:
```
>>> from rich import pretty
>>> pretty.install()
```

----------------------------------------

TITLE: Displaying Terminal Color Chart with HTML
DESCRIPTION: HTML code that renders a formatted table displaying standard terminal colors. The table shows color swatches, numbers, names, hex values, and RGB values for the standard 8-bit colors supported in terminals.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/appendix/colors.rst#2025-04-16_snippet_0

LANGUAGE: html
CODE:
```
<pre style="font-family:Menlo,'DejaVu Sans Mono',consolas,'Courier New',monospace">╔════════════╤════════╤═══════════════════════╤═════════╤══════════════════╗
    ║<span style="font-weight: bold"> Color      </span>│<span style="font-weight: bold"> Number </span>│<span style="font-weight: bold"> Name                  </span>│<span style="font-weight: bold"> Hex     </span>│<span style="font-weight: bold"> RGB              </span>║
    ╟────────────┼────────┼───────────────────────┼─────────┼──────────────────╢
    ║ <span style="background-color: #000000">          </span> │<span style="color: #808000">      0 </span>│<span style="color: #008000"> "black"               </span>│<span style="color: #000080">         </span>│<span style="color: #800080">                  </span>║
    ║ <span style="background-color: #800000">          </span> │<span style="color: #808000">      1 </span>│<span style="color: #008000"> "red"                 </span>│<span style="color: #000080">         </span>│<span style="color: #800080">                  </span>║
    ║ <span style="background-color: #008000">          </span> │<span style="color: #808000">      2 </span>│<span style="color: #008000"> "green"               </span>│<span style="color: #000080">         </span>│<span style="color: #800080">                  </span>║
    ║ <span style="background-color: #808000">          </span> │<span style="color: #808000">      3 </span>│<span style="color: #008000"> "yellow"              </span>│<span style="color: #000080">         </span>│<span style="color: #800080">                  </span>║
    ║ <span style="background-color: #000080">          </span> │<span style="color: #808000">      4 </span>│<span style="color: #008000"> "blue"                </span>│<span style="color: #000080">         </span>│<span style="color: #800080">                  </span>║
    ║ <span style="background-color: #800080">          </span> │<span style="color: #808000">      5 </span>│<span style="color: #008000"> "magenta"             </span>│<span style="color: #000080">         </span>│<span style="color: #800080">                  </span>║
    ║ <span style="background-color: #008080">          </span> │<span style="color: #808000">      6 </span>│<span style="color: #008000"> "cyan"                </span>│<span style="color: #000080">         </span>│<span style="color: #800080">                  </span>║
    ║ <span style="background-color: #c0c0c0">          </span> │<span style="color: #808000">      7 </span>│<span style="color: #008000"> "white"               </span>│<span style="color: #000080">         </span>│<span style="color: #800080">                  </span>║
    ║ <span style="background-color: #808080">          </span> │<span style="color: #808000">      8 </span>│<span style="color: #008000"> "bright_black"        </span>│<span style="color: #000080">         </span>│<span style="color: #800080">                  </span>║
    ║ <span style="background-color: #ff0000">          </span> │<span style="color: #808000">      9 </span>│<span style="color: #008000"> "bright_red"          </span>│<span style="color: #000080">         </span>│<span style="color: #800080">                  </span>║
    ║ <span style="background-color: #00ff00">          </span> │<span style="color: #808000">     10 </span>│<span style="color: #008000"> "bright_green"        </span>│<span style="color: #000080">         </span>│<span style="color: #800080">                  </span>║
    ║ <span style="background-color: #ffff00">          </span> │<span style="color: #808000">     11 </span>│<span style="color: #008000"> "bright_yellow"       </span>│<span style="color: #000080">         </span>│<span style="color: #800080">                  </span>║
    ║ <span style="background-color: #0000ff">          </span> │<span style="color: #808000">     12 </span>│<span style="color: #008000"> "bright_blue"         </span>│<span style="color: #000080">         </span>│<span style="color: #800080">                  </span>║
    ║ <span style="background-color: #ff00ff">          </span> │<span style="color: #808000">     13 </span>│<span style="color: #008000"> "bright_magenta"      </span>│<span style="color: #000080">         </span>│<span style="color: #800080">                  </span>║
    ║ <span style="background-color: #00ffff">          </span> │<span style="color: #808000">     14 </span>│<span style="color: #008000"> "bright_cyan"         </span>│<span style="color: #000080">         </span>│<span style="color: #800080">                  </span>║
    ║ <span style="background-color: #ffffff">          </span> │<span style="color: #808000">     15 </span>│<span style="color: #008000"> "bright_white"        </span>│<span style="color: #000080">         </span>│<span style="color: #800080">                  </span>║
    ║ <span style="background-color: #000000">          </span> │<span style="color: #808000">     16 </span>│<span style="color: #008000"> "grey0"               </span>│<span style="color: #000080"> #000000 </span>│<span style="color: #800080"> rgb(0,0,0)       </span>║
    ║ <span style="background-color: #00005f">          </span> │<span style="color: #808000">     17 </span>│<span style="color: #008000"> "navy_blue"           </span>│<span style="color: #000080"> #00005f </span>│<span style="color: #800080"> rgb(0,0,95)      </span>║
    ║ <span style="background-color: #000087">          </span> │<span style="color: #808000">     18 </span>│<span style="color: #008000"> "dark_blue"           </span>│<span style="color: #000080"> #000087 </span>│<span style="color: #800080"> rgb(0,0,135)     </span>║
    ║ <span style="background-color: #0000d7">          </span> │<span style="color: #808000">     20 </span>│<span style="color: #008000"> "blue3"               </span>│<span style="color: #000080"> #0000d7 </span>│<span style="color: #800080"> rgb(0,0,215)     </span>║
    ║ <span style="background-color: #0000ff">          </span> │<span style="color: #808000">     21 </span>│<span style="color: #008000"> "blue1"               </span>│<span style="color: #000080"> #0000ff </span>│<span style="color: #800080"> rgb(0,0,255)     </span>║
    ║ <span style="background-color: #005f00">          </span> │<span style="color: #808000">     22 </span>│<span style="color: #008000"> "dark_green"          </span>│<span style="color: #000080"> #005f00 </span>│<span style="color: #800080"> rgb(0,95,0)      </span>║
    ║ <span style="background-color: #005faf">          </span> │<span style="color: #808000">     25 </span>│<span style="color: #008000"> "deep_sky_blue4"      </span>│<span style="color: #000080"> #005faf </span>│<span style="color: #800080"> rgb(0,95,175)    </span>║
    ║ <span style="background-color: #005fd7">          </span> │<span style="color: #808000">     26 </span>│<span style="color: #008000"> "dodger_blue3"        </span>│<span style="color: #000080"> #005fd7 </span>│<span style="color: #800080"> rgb(0,95,215)    </span>║
    ║ <span style="background-color: #005fff">          </span> │<span style="color: #808000">     27 </span>│<span style="color: #008000"> "dodger_blue2"        </span>│<span style="color: #000080"> #005fff </span>│<span style="color: #800080"> rgb(0,95,255)    </span>║
    ║ <span style="background-color: #008700">          </span> │<span style="color: #808000">     28 </span>│<span style="color: #008000"> "green4"              </span>│<span style="color: #000080"> #008700 </span>│<span style="color: #800080"> rgb(0,135,0)     </span>║
    ║ <span style="background-color: #00875f">          </span> │<span style="color: #808000">     29 </span>│<span style="color: #008000"> "spring_green4"       </span>│<span style="color: #000080"> #00875f </span>│<span style="color: #800080"> rgb(0,135,95)    </span>║
    ║ <span style="background-color: #008787">          </span> │<span style="color: #808000">     30 </span>│<span style="color: #008000"> "turquoise4"          </span>│<span style="color: #000080"> #008787 </span>│<span style="color: #800080"> rgb(0,135,135)   </span>║
    ║ <span style="background-color: #0087d7">          </span> │<span style="color: #808000">     32 </span>│<span style="color: #008000"> "deep_sky_blue3"      </span>│<span style="color: #000080"> #0087d7 </span>│<span style="color: #800080"> rgb(0,135,215)   </span>║
    ║ <span style="background-color: #0087ff">          </span> │<span style="color: #808000">     33 </span>│<span style="color: #008000"> "dodger_blue1"        </span>│<span style="color: #000080"> #0087ff </span>│<span style="color: #800080"> rgb(0,135,255)   </span>║
    ║ <span style="background-color: #00af87">          </span> │<span style="color: #808000">     36 </span>│<span style="color: #008000"> "dark_cyan"           </span>│<span style="color: #000080"> #00af87 </span>│<span style="color: #800080"> rgb(0,175,135)   </span>║
    ║ <span style="background-color: #00afaf">          </span> │<span style="color: #808000">     37 </span>│<span style="color: #008000"> "light_sea_green"     </span>│<span style="color: #000080"> #00afaf </span>│<span style="color: #800080"> rgb(0,175,175)   </span>║
    ║ <span style="background-color: #00afd7">          </span> │<span style="color: #808000">     38 </span>│<span style="color: #008000"> "deep_sky_blue2"      </span>│<span style="color: #000080"> #00afd7 </span>│<span style="color: #800080"> rgb(0,175,215)   </span>║
```

----------------------------------------

TITLE: Rich Console Basic Usage
DESCRIPTION: Examples of using Rich's Console object for formatted terminal output
SOURCE: https://github.com/Textualize/rich/blob/master/README.pl.md#2025-04-16_snippet_4

LANGUAGE: python
CODE:
```
from rich.console import Console

console = Console()
```

LANGUAGE: python
CODE:
```
console.print("Hello", "World!")
```

LANGUAGE: python
CODE:
```
console.print("Hello", "World!", style="bold red")
```

LANGUAGE: python
CODE:
```
console.print("Where there is a [bold cyan]Will[/bold cyan] there [u]is[/u] a [i]way[/i].")
```

----------------------------------------

TITLE: Basic Rich print example
DESCRIPTION: Demonstrates how to use Rich's print function with markup for styling text. This example shows bold magenta formatting and includes an emoji and variable output.
SOURCE: https://github.com/Textualize/rich/blob/master/README.fa.md#2025-04-16_snippet_2

LANGUAGE: python
CODE:
```
from rich import print

print("Hello, [bold magenta]World[/bold magenta]!", ":vampire:", locals())
```

----------------------------------------

TITLE: Prompt with Default Value
DESCRIPTION: Shows how to set a default value that will be returned if the user presses enter without typing anything
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/prompt.rst#2025-04-16_snippet_1

LANGUAGE: python
CODE:
```
from rich.prompt import Prompt
name = Prompt.ask("Enter your name", default="Paul Atreides")
```

----------------------------------------

TITLE: Displaying Tree Structure with Rich
DESCRIPTION: This code snippet demonstrates how to display a tree structure using Rich. Running the command `python -m rich.tree` will output a tree representation in the console.
SOURCE: https://github.com/Textualize/rich/blob/master/README.kr.md#2025-04-16_snippet_12

LANGUAGE: python
CODE:
```
python -m rich.tree
```

----------------------------------------

TITLE: Initializing Rich Console in Python
DESCRIPTION: Example of importing and initializing the Rich Console class for more advanced terminal control and formatting.
SOURCE: https://github.com/Textualize/rich/blob/master/README.ru.md#2025-04-16_snippet_4

LANGUAGE: python
CODE:
```
from rich.console import Console

console = Console()
```

----------------------------------------

TITLE: Installing Rich in Python REPL
DESCRIPTION: Code to install Rich in Python REPL for pretty-printing data structures.
SOURCE: https://github.com/Textualize/rich/blob/master/README.kr.md#2025-04-16_snippet_3

LANGUAGE: python
CODE:
```
>>> from rich import pretty
>>> pretty.install()
```

----------------------------------------

TITLE: Previewing Benchmark Dashboard Locally
DESCRIPTION: Command to launch a local web server to preview the generated benchmark dashboard.
SOURCE: https://github.com/Textualize/rich/blob/master/benchmarks/README.md#2025-04-16_snippet_4

LANGUAGE: bash
CODE:
```
asv preview
```

----------------------------------------

TITLE: Using Rich print function with markup
DESCRIPTION: Example of importing and using Rich's print function to display formatted text with markup. The example shows bold magenta styling, emoji support, and variable inspection capabilities.
SOURCE: https://github.com/Textualize/rich/blob/master/README.hi.md#2025-04-16_snippet_2

LANGUAGE: python
CODE:
```
from rich import print

print("Hello, [bold magenta]World[/bold magenta]!", ":vampire:", locals())
```

----------------------------------------

TITLE: Using Rich Print Function - Python
DESCRIPTION: This snippet demonstrates how to import the Rich print function to produce styled text output in the terminal. It showcases bold magenta text output.
SOURCE: https://github.com/Textualize/rich/blob/master/README.ja.md#2025-04-16_snippet_1

LANGUAGE: python
CODE:
```
from rich import print

print("Hello, [bold magenta]World[/bold magenta]!", ":vampire:", locals())
```

----------------------------------------

TITLE: Installing Global Traceback Handler
DESCRIPTION: Configures Rich as the default traceback handler for uncaught exceptions
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/traceback.rst#2025-04-16_snippet_1

LANGUAGE: python
CODE:
```
from rich.traceback import install
install(show_locals=True)
```

----------------------------------------

TITLE: Rich Layout Methods
DESCRIPTION: Methods for managing layout splits and updates in Rich's layout system.
SOURCE: https://github.com/Textualize/rich/blob/master/CHANGELOG.md#2025-04-16_snippet_5

LANGUAGE: python
CODE:
```
Layout.add_split
Layout.split_column
Layout.split_row
layout.refresh
```

----------------------------------------

TITLE: Markup Escaping - Python
DESCRIPTION: Demonstrates how to escape markup tags using backslashes when you want to print literal brackets.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/markup.rst#2025-04-16_snippet_5

LANGUAGE: python
CODE:
```
>>> from rich import print
>>> print(r"foo\[bar]")
foo[bar]
```

----------------------------------------

TITLE: Rich REPL Installation
DESCRIPTION: Shows how to install Rich in Python REPL for pretty printing data structures
SOURCE: https://github.com/Textualize/rich/blob/master/README.pl.md#2025-04-16_snippet_3

LANGUAGE: python
CODE:
```
>>> from rich import pretty
>>> pretty.install()
```

----------------------------------------

TITLE: Rich Print Example
DESCRIPTION: Demonstrates using Rich's print function with markup formatting and emoji support
SOURCE: https://github.com/Textualize/rich/blob/master/README.pl.md#2025-04-16_snippet_2

LANGUAGE: python
CODE:
```
from rich import print

print("Hello, [bold magenta]World[/bold magenta]!", ":vampire:", locals())
```

----------------------------------------

TITLE: Displaying a Tree with Rich
DESCRIPTION: This snippet shows how to execute a Rich module to display a sample tree structure.  The command `python -m rich.tree` demonstrates the `rich.tree` module, showing how to create tree-like structures in the terminal with guides and labels.
SOURCE: https://github.com/Textualize/rich/blob/master/README.fa.md#2025-04-16_snippet_15

LANGUAGE: python
CODE:
```
python -m rich.tree
```

----------------------------------------

TITLE: Creating a Rich Console instance
DESCRIPTION: Example of importing and instantiating a Console object from Rich. The Console object provides more control over terminal formatting and output.
SOURCE: https://github.com/Textualize/rich/blob/master/README.hi.md#2025-04-16_snippet_4

LANGUAGE: python
CODE:
```
from rich.console import Console

console = Console()
```

----------------------------------------

TITLE: Running Basic Benchmark on Master Branch
DESCRIPTION: Command to run benchmarks against the master branch of Rich using Airspeed Velocity.
SOURCE: https://github.com/Textualize/rich/blob/master/benchmarks/README.md#2025-04-16_snippet_0

LANGUAGE: bash
CODE:
```
asv run
```

----------------------------------------

TITLE: Rich REPL Configuration
DESCRIPTION: Shows how to install Rich in Python's interactive REPL for pretty printing of data structures
SOURCE: https://github.com/Textualize/rich/blob/master/README.cn.md#2025-04-16_snippet_2

LANGUAGE: python
CODE:
```
>>> from rich import pretty
>>> pretty.install()
```

----------------------------------------

TITLE: Installing Rich in Python REPL for pretty printing
DESCRIPTION: Code to enable Rich pretty printing in Python's interactive REPL. This allows data structures to be automatically formatted and highlighted when displayed.
SOURCE: https://github.com/Textualize/rich/blob/master/README.hi.md#2025-04-16_snippet_3

LANGUAGE: python
CODE:
```
>>> from rich import pretty
>>> pretty.install()
```

----------------------------------------

TITLE: Creating a Rich Console object
DESCRIPTION: Code that imports and initializes a Console object from Rich, which provides more control over terminal output formatting than the basic print function.
SOURCE: https://github.com/Textualize/rich/blob/master/README.sv.md#2025-04-16_snippet_4

LANGUAGE: python
CODE:
```
from rich.console import Console

console = Console()
```

----------------------------------------

TITLE: Basic Console print example
DESCRIPTION: Demonstrates using the Console object's print method to display text in the terminal. This method handles word wrapping to fit the terminal width.
SOURCE: https://github.com/Textualize/rich/blob/master/README.fa.md#2025-04-16_snippet_5

LANGUAGE: python
CODE:
```
console.print("Hello", "World!")
```

----------------------------------------

TITLE: Basic Rich Print Usage
DESCRIPTION: Example showing how to import and use Rich's print function with markup formatting
SOURCE: https://github.com/Textualize/rich/blob/master/README.tr.md#2025-04-16_snippet_1

LANGUAGE: python
CODE:
```
from rich import print

print("Merhaba, [bold magenta]Dünya[/bold magenta]!", ":vampire:", locals())
```

----------------------------------------

TITLE: Generating Static Benchmark Website
DESCRIPTION: Command to generate a static website for browsing benchmark results, which will be saved in the benchmarks/html directory.
SOURCE: https://github.com/Textualize/rich/blob/master/benchmarks/README.md#2025-04-16_snippet_2

LANGUAGE: bash
CODE:
```
asv publish
```

----------------------------------------

TITLE: Inspect Function in Rich - Python
DESCRIPTION: This snippet utilizes the Rich inspect function to generate reports on Python objects, showcasing methods and attributes.
SOURCE: https://github.com/Textualize/rich/blob/master/README.ja.md#2025-04-16_snippet_3

LANGUAGE: python
CODE:
```
>>> from rich import inspect
>>> inspect(str, methods=True)
```

----------------------------------------

TITLE: Rich Console Object Usage
DESCRIPTION: Examples of using Rich's Console object for advanced terminal output formatting
SOURCE: https://github.com/Textualize/rich/blob/master/README.cn.md#2025-04-16_snippet_3

LANGUAGE: python
CODE:
```
from rich.console import Console

console = Console()
```

LANGUAGE: python
CODE:
```
console.print("Hello", "World!")
```

LANGUAGE: python
CODE:
```
console.print("Hello", "World!", style="bold red")
```

LANGUAGE: python
CODE:
```
console.print("Where there is a [bold cyan]Will[/bold cyan] there [u]is[/u] a [i]way[/i].")
```

----------------------------------------

TITLE: Using Low-Level Output in Rich Console for Python
DESCRIPTION: Demonstrates the use of the Console.out() method for lower-level output that bypasses some of Rich's automatic formatting features.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/console.rst#2025-04-16_snippet_4

LANGUAGE: python
CODE:
```
>>> console.out("Locals", locals())
```

----------------------------------------

TITLE: Basic Console printing
DESCRIPTION: Example of using the Console object's print method to output text to the terminal. Unlike the built-in print function, Rich will automatically wrap text to fit the terminal width.
SOURCE: https://github.com/Textualize/rich/blob/master/README.sv.md#2025-04-16_snippet_5

LANGUAGE: python
CODE:
```
console.print("Hello", "World!")
```

----------------------------------------

TITLE: Installing Rich in Python REPL
DESCRIPTION: This code installs Rich in the Python REPL for pretty-printing and syntax highlighting of data structures.
SOURCE: https://github.com/Textualize/rich/blob/master/README.es.md#2025-04-16_snippet_3

LANGUAGE: python
CODE:
```
>>> from rich import pretty
>>> pretty.install()
```

----------------------------------------

TITLE: Styling Console output with keywords
DESCRIPTION: Example of applying styles to Console output using the style keyword argument, which applies the specified style to the entire output line.
SOURCE: https://github.com/Textualize/rich/blob/master/README.sv.md#2025-04-16_snippet_6

LANGUAGE: python
CODE:
```
console.print("Hello", "World!", style="bold red")
```

----------------------------------------

TITLE: Setting Progress Total to None in Python
DESCRIPTION: Setting the total parameter to None on a Rich progress bar will display a pulsing animation instead of a percentage.
SOURCE: https://github.com/Textualize/rich/blob/master/CHANGELOG.md#2025-04-16_snippet_1

LANGUAGE: python
CODE:
```
total=None
```

----------------------------------------

TITLE: Printing Emojis to Console
DESCRIPTION: This snippet showcases how to print emojis in the terminal using the Rich library. Emojis are specified by enclosing their names within colons. The snippet prints a series of emojis including smiley, vampire, pile of poo, thumbs up, and raccoon.
SOURCE: https://github.com/Textualize/rich/blob/master/README.fa.md#2025-04-16_snippet_10

LANGUAGE: python
CODE:
```
>>> console.print(":smiley: :vampire: :pile_of_poo: :thumbs_up: :raccoon:")
```

----------------------------------------

TITLE: HTML Terminal Color Palette Display in Rich Library
DESCRIPTION: A formatted HTML table displaying terminal colors with swatches, indices, names, hex codes, and RGB values. Each row represents a different color in the Rich library's terminal color palette, showing both visual representation and technical color specifications.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/appendix/colors.rst#2025-04-16_snippet_1

LANGUAGE: html
CODE:
```
<span style="background-color: #8700af">          </span> │<span style="color: #808000">     91 </span>│<span style="color: #008000"> "dark_magenta"        </span>│<span style="color: #000080"> #8700af </span>│<span style="color: #800080"> rgb(135,0,175)   </span>
```

----------------------------------------

TITLE: Installing Rich with pip in Python
DESCRIPTION: Command to install Rich library using pip package manager.
SOURCE: https://github.com/Textualize/rich/blob/master/README.kr.md#2025-04-16_snippet_0

LANGUAGE: sh
CODE:
```
python -m pip install rich
```

----------------------------------------

TITLE: Rich Inspect Example
DESCRIPTION: Shows usage of Rich's inspect function for generating detailed object reports
SOURCE: https://github.com/Textualize/rich/blob/master/README.pl.md#2025-04-16_snippet_5

LANGUAGE: python
CODE:
```
>>> my_list = ["foo", "bar"]
>>> from rich import inspect
>>> inspect(my_list, methods=True)
```

----------------------------------------

TITLE: Creating a Rich Console Instance
DESCRIPTION: Code that shows how to import and create a Console instance for greater control over rich terminal output.
SOURCE: https://github.com/Textualize/rich/blob/master/README.fr.md#2025-04-16_snippet_4

LANGUAGE: python
CODE:
```
from rich.console import Console

console = Console()
```

----------------------------------------

TITLE: Installing Rich in REPL
DESCRIPTION: This snippet shows how to install Rich for automatic pretty printing and syntax highlighting of Python data structures in the REPL (Read-Eval-Print Loop) environment.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/introduction.rst#2025-04-16_snippet_5

LANGUAGE: python
CODE:
```
">>> from rich import pretty\n>>> pretty.install()\n>>> [\"Rich and pretty\", True]"
```

----------------------------------------

TITLE: Importing and Using Box Constants in Rich
DESCRIPTION: Shows how to import a box constant from rich.box and apply it to a Table. This allows customization of the box drawing characters used for tables and panels.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/appendix/box.rst#2025-04-16_snippet_0

LANGUAGE: python
CODE:
```
from rich import box
table = Table(box=box.SQUARE)
```

----------------------------------------

TITLE: Installing Rich with pip in Python
DESCRIPTION: Command to install Rich using pip package manager.
SOURCE: https://github.com/Textualize/rich/blob/master/README.zh-tw.md#2025-04-16_snippet_0

LANGUAGE: shell
CODE:
```
python -m pip install rich
```

----------------------------------------

TITLE: Displaying Spinner Options with Rich
DESCRIPTION: This snippet shows how to execute a Rich module to display available spinner animations. The command `python -m rich.spinner` will render a list of available spinners in the terminal, allowing users to select a spinner for use with Rich's `status` feature.
SOURCE: https://github.com/Textualize/rich/blob/master/README.fa.md#2025-04-16_snippet_14

LANGUAGE: python
CODE:
```
python -m rich.spinner
```

----------------------------------------

TITLE: Creating a Rich Console Object
DESCRIPTION: Example of importing and instantiating a Console object from Rich, which provides more control over terminal output formatting and styling.
SOURCE: https://github.com/Textualize/rich/blob/master/README.de.md#2025-04-16_snippet_4

LANGUAGE: python
CODE:
```
from rich.console import Console

console = Console()
```

----------------------------------------

TITLE: Styling console output with a keyword argument
DESCRIPTION: Example of applying styles to console output using the style keyword argument. This applies the specified style (bold red) to the entire printed text.
SOURCE: https://github.com/Textualize/rich/blob/master/README.hi.md#2025-04-16_snippet_6

LANGUAGE: python
CODE:
```
console.print("Hello", "World!", style="bold red")
```

----------------------------------------

TITLE: Using Rich Inspect Function
DESCRIPTION: Example of Rich's inspect function for creating detailed reports about Python objects, showing method inspection of a list.
SOURCE: https://github.com/Textualize/rich/blob/master/README.de-ch.md#2025-04-16_snippet_8

LANGUAGE: python
CODE:
```
>>> my_list = ["foo", "bar"]
>>> from rich import inspect
>>> inspect(my_list, methods=True)
```

----------------------------------------

TITLE: Installing Rich Package with pip
DESCRIPTION: This command installs the Rich package using pip, the Python package installer.
SOURCE: https://github.com/Textualize/rich/blob/master/README.es.md#2025-04-16_snippet_0

LANGUAGE: sh
CODE:
```
python -m pip install rich
```

----------------------------------------

TITLE: Implementing __rich_measure__ Method for Width Calculation in Python
DESCRIPTION: An example showing how to implement the __rich_measure__ method to inform Rich about the space requirements of a custom object. This helps with layout calculations in containers like Table.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/protocol.rst#2025-04-16_snippet_3

LANGUAGE: python
CODE:
```
class ChessBoard:
    def __rich_measure__(self, console: Console, options: ConsoleOptions) -> Measurement:
        return Measurement(8, options.max_width)
```

----------------------------------------

TITLE: Loading Rich IPython Extension
DESCRIPTION: This snippet shows how to load the Rich IPython extension, which provides pretty printing and traceback enhancements within an IPython environment.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/introduction.rst#2025-04-16_snippet_7

LANGUAGE: ipython
CODE:
```
"In [1]: %load_ext rich"
```

----------------------------------------

TITLE: Setting Fixed Layout Size in Python
DESCRIPTION: Sets the "upper" layout to have a fixed size of 10 rows, regardless of terminal dimensions.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/layout.rst#2025-04-16_snippet_5

LANGUAGE: python
CODE:
```
layout["upper"].size = 10
print(layout)
```

----------------------------------------

TITLE: Testing Rich Output in Python Terminal
DESCRIPTION: Command to test Rich's output capabilities in the terminal.
SOURCE: https://github.com/Textualize/rich/blob/master/README.zh-tw.md#2025-04-16_snippet_1

LANGUAGE: shell
CODE:
```
python -m rich
```

----------------------------------------

TITLE: Installing Rich in Python REPL
DESCRIPTION: Code to install Rich in the Python REPL for pretty-printing of data structures. This enhances the default REPL output.
SOURCE: https://github.com/Textualize/rich/blob/master/README.id.md#2025-04-16_snippet_3

LANGUAGE: python
CODE:
```
>>> from rich import pretty
>>> pretty.install()
```

----------------------------------------

TITLE: Installing Rich using pip
DESCRIPTION: Command to install the Rich library using pip package manager. This is the primary installation method for adding Rich to your Python environment.
SOURCE: https://github.com/Textualize/rich/blob/master/README.fa.md#2025-04-16_snippet_0

LANGUAGE: sh
CODE:
```
python -m pip install rich
```

----------------------------------------

TITLE: Installing Rich with Jupyter extras
DESCRIPTION: This snippet shows how to install Rich with additional dependencies needed for using it with Jupyter notebooks. It installs the 'jupyter' extra.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/introduction.rst#2025-04-16_snippet_1

LANGUAGE: shell
CODE:
```
"pip install \"rich[jupyter]\""
```

----------------------------------------

TITLE: Creating a Rich Console object
DESCRIPTION: Shows how to create a Console object, which is the main interface for Rich's advanced terminal output capabilities.
SOURCE: https://github.com/Textualize/rich/blob/master/README.fa.md#2025-04-16_snippet_4

LANGUAGE: python
CODE:
```
from rich.console import Console

console = Console()
```

----------------------------------------

TITLE: Rich Inspect Function Example
DESCRIPTION: This snippet demonstrates the use of Rich's inspect function to generate a detailed report on a Python object, including its attributes and methods. It showcases Rich's debugging capabilities.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/introduction.rst#2025-04-16_snippet_8

LANGUAGE: python
CODE:
```
">>> from rich import inspect\n>>> from rich.color import Color\n>>> color = Color.parse(\"red\")\n>>> inspect(color, methods=True)"
```

----------------------------------------

TITLE: Importing RichHandler from rich.logging in Python
DESCRIPTION: This code snippet demonstrates how to import the RichHandler class from the rich.logging module. RichHandler is used to enhance logging output with Rich's formatting capabilities.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/reference/logging.rst#2025-04-16_snippet_0

LANGUAGE: python
CODE:
```
from rich.logging import RichHandler
```

----------------------------------------

TITLE: Testing Rich Output in Terminal
DESCRIPTION: Command to run a demonstration of Rich's capabilities in your terminal by executing the Rich module directly.
SOURCE: https://github.com/Textualize/rich/blob/master/README.fr.md#2025-04-16_snippet_1

LANGUAGE: sh
CODE:
```
python -m rich
```

----------------------------------------

TITLE: Testing Rich output in terminal
DESCRIPTION: Command to run Rich's built-in demonstration that shows various formatting capabilities directly in your terminal.
SOURCE: https://github.com/Textualize/rich/blob/master/README.sv.md#2025-04-16_snippet_1

LANGUAGE: sh
CODE:
```
python -m rich
```

----------------------------------------

TITLE: Rich Console Object Creation
DESCRIPTION: Example showing how to import and create a Rich Console object for terminal output
SOURCE: https://github.com/Textualize/rich/blob/master/README.tr.md#2025-04-16_snippet_3

LANGUAGE: python
CODE:
```
from rich.console import Console

console = Console()
```

----------------------------------------

TITLE: Testing Rich Output in Terminal
DESCRIPTION: Command to run Rich's built-in demo to showcase its terminal output capabilities.
SOURCE: https://github.com/Textualize/rich/blob/master/README.de-ch.md#2025-04-16_snippet_1

LANGUAGE: sh
CODE:
```
python -m rich
```

----------------------------------------

TITLE: Generating Rich Markup Module Documentation with Sphinx
DESCRIPTION: RST directive for automating documentation generation of the rich.markup module. Uses Sphinx automodule to include all module members in the generated documentation.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/reference/markup.rst#2025-04-16_snippet_0

LANGUAGE: rst
CODE:
```
.. automodule:: rich.markup
    :members:
```

----------------------------------------

TITLE: Running Rich Demo
DESCRIPTION: Command to test Rich output capabilities in terminal
SOURCE: https://github.com/Textualize/rich/blob/master/README.pl.md#2025-04-16_snippet_1

LANGUAGE: sh
CODE:
```
python -m rich
```

----------------------------------------

TITLE: Testing Rich Output in Terminal
DESCRIPTION: This command runs a built-in Rich demo to showcase its capabilities in the terminal.
SOURCE: https://github.com/Textualize/rich/blob/master/README.es.md#2025-04-16_snippet_1

LANGUAGE: sh
CODE:
```
python -m rich
```

----------------------------------------

TITLE: Using Rich print function for formatted output
DESCRIPTION: Example of importing and using Rich's print function to output formatted text with markup, emojis, and Python objects. The function supports Rich's markup syntax for styling text.
SOURCE: https://github.com/Textualize/rich/blob/master/README.sv.md#2025-04-16_snippet_2

LANGUAGE: python
CODE:
```
from rich import print

print("Hello, [bold magenta]World[/bold magenta]!", ":vampire:", locals())
```

----------------------------------------

TITLE: Generating RST Documentation for rich.markdown Module
DESCRIPTION: RST directive to automatically generate documentation for the rich.markdown module including all its members. This is part of the Sphinx documentation system.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/reference/markdown.rst#2025-04-16_snippet_0

LANGUAGE: rst
CODE:
```
.. automodule:: rich.markdown
    :members:
```

----------------------------------------

TITLE: ReStructuredText Documentation for rich.emoji Module
DESCRIPTION: ReStructuredText directive for auto-generating documentation from the rich.emoji module, specifically documenting the Emoji class and its members.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/reference/emoji.rst#2025-04-16_snippet_0

LANGUAGE: rst
CODE:
```
.. automodule:: rich.emoji
    :members: Emoji
```

----------------------------------------

TITLE: Setting up Sphinx documentation structure for Rich library
DESCRIPTION: This ReStructuredText code establishes the table of contents structure using the toctree directive. It organizes the documentation into logical sections covering various Rich library features and capabilities.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/index.rst#2025-04-16_snippet_0

LANGUAGE: restructuredtext
CODE:
```
.. toctree::
   :maxdepth: 2
   :caption: Contents:

   introduction.rst
   console.rst
   style.rst
   markup.rst
   text.rst
   highlighting.rst
   pretty.rst
   logging.rst
   traceback.rst
   prompt.rst

   columns.rst
   group.rst   
   markdown.rst
   padding.rst
   panel.rst
   progress.rst
   syntax.rst
   tables.rst
   tree.rst
   live.rst
   layout.rst

   protocol.rst

   reference.rst
   appendix.rst
```

----------------------------------------

TITLE: Testing Rich Output in Terminal
DESCRIPTION: Command to run Rich's built-in demonstration module that showcases its formatting capabilities directly in your terminal.
SOURCE: https://github.com/Textualize/rich/blob/master/README.de.md#2025-04-16_snippet_1

LANGUAGE: sh
CODE:
```
python -m rich
```

----------------------------------------

TITLE: Using Rich Print Function
DESCRIPTION: Example of using Rich's print function to output styled text and emojis. This demonstrates basic text formatting and emoji support.
SOURCE: https://github.com/Textualize/rich/blob/master/README.id.md#2025-04-16_snippet_2

LANGUAGE: python
CODE:
```
from rich import print

print("Hello, [bold magenta]World[/bold magenta]!", ":vampire:", locals())
```

----------------------------------------

TITLE: Generating Documentation for rich.live Module using reStructuredText
DESCRIPTION: This snippet uses reStructuredText directives to automatically generate documentation for the rich.live module. It includes all members of the module in the documentation.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/reference/live.rst#2025-04-16_snippet_0

LANGUAGE: reStructuredText
CODE:
```
rich.live
=========

.. automodule:: rich.live
    :members:
```

----------------------------------------

TITLE: Displaying Terminal Color Table with HTML Formatting in Rich
DESCRIPTION: A formatted table displaying terminal color codes (230-255) with their names, hexadecimal values, and RGB equivalents. Each row shows a color swatch, index number, name, hex code, and RGB value in a structured format with styling applied using HTML spans.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/appendix/colors.rst#2025-04-16_snippet_4

LANGUAGE: html
CODE:
```
║ <span style="background-color: #ffffd7">          </span> │<span style="color: #808000">    230 </span>│<span style="color: #008000"> "cornsilk1"           </span>│<span style="color: #000080"> #ffffd7 </span>│<span style="color: #800080"> rgb(255,255,215) </span>║
    ║ <span style="background-color: #ffffff">          </span> │<span style="color: #808000">    231 </span>│<span style="color: #008000"> "grey100"             </span>│<span style="color: #000080"> #ffffff </span>│<span style="color: #800080"> rgb(255,255,255) </span>║
    ║ <span style="background-color: #080808">          </span> │<span style="color: #808000">    232 </span>│<span style="color: #008000"> "grey3"               </span>│<span style="color: #000080"> #080808 </span>│<span style="color: #800080"> rgb(8,8,8)       </span>║
    ║ <span style="background-color: #121212">          </span> │<span style="color: #808000">    233 </span>│<span style="color: #008000"> "grey7"               </span>│<span style="color: #000080"> #121212 </span>│<span style="color: #800080"> rgb(18,18,18)    </span>║
    ║ <span style="background-color: #1c1c1c">          </span> │<span style="color: #808000">    234 </span>│<span style="color: #008000"> "grey11"              </span>│<span style="color: #000080"> #1c1c1c </span>│<span style="color: #800080"> rgb(28,28,28)    </span>║
    ║ <span style="background-color: #262626">          </span> │<span style="color: #808000">    235 </span>│<span style="color: #008000"> "grey15"              </span>│<span style="color: #000080"> #262626 </span>│<span style="color: #800080"> rgb(38,38,38)    </span>║
    ║ <span style="background-color: #303030">          </span> │<span style="color: #808000">    236 </span>│<span style="color: #008000"> "grey19"              </span>│<span style="color: #000080"> #303030 </span>│<span style="color: #800080"> rgb(48,48,48)    </span>║
    ║ <span style="background-color: #3a3a3a">          </span> │<span style="color: #808000">    237 </span>│<span style="color: #008000"> "grey23"              </span>│<span style="color: #000080"> #3a3a3a </span>│<span style="color: #800080"> rgb(58,58,58)    </span>║
    ║ <span style="background-color: #444444">          </span> │<span style="color: #808000">    238 </span>│<span style="color: #008000"> "grey27"              </span>│<span style="color: #000080"> #444444 </span>│<span style="color: #800080"> rgb(68,68,68)    </span>║
    ║ <span style="background-color: #4e4e4e">          </span> │<span style="color: #808000">    239 </span>│<span style="color: #008000"> "grey30"              </span>│<span style="color: #000080"> #4e4e4e </span>│<span style="color: #800080"> rgb(78,78,78)    </span>║
    ║ <span style="background-color: #585858">          </span> │<span style="color: #808000">    240 </span>│<span style="color: #008000"> "grey35"              </span>│<span style="color: #000080"> #585858 </span>│<span style="color: #800080"> rgb(88,88,88)    </span>║
    ║ <span style="background-color: #626262">          </span> │<span style="color: #808000">    241 </span>│<span style="color: #008000"> "grey39"              </span>│<span style="color: #000080"> #626262 </span>│<span style="color: #800080"> rgb(98,98,98)    </span>║
    ║ <span style="background-color: #6c6c6c">          </span> │<span style="color: #808000">    242 </span>│<span style="color: #008000"> "grey42"              </span>│<span style="color: #000080"> #6c6c6c </span>│<span style="color: #800080"> rgb(108,108,108) </span>║
    ║ <span style="background-color: #767676">          </span> │<span style="color: #808000">    243 </span>│<span style="color: #008000"> "grey46"              </span>│<span style="color: #000080"> #767676 </span>│<span style="color: #800080"> rgb(118,118,118) </span>║
    ║ <span style="background-color: #808080">          </span> │<span style="color: #808000">    244 </span>│<span style="color: #008000"> "grey50"              </span>│<span style="color: #000080"> #808080 </span>│<span style="color: #800080"> rgb(128,128,128) </span>║
    ║ <span style="background-color: #8a8a8a">          </span> │<span style="color: #808000">    245 </span>│<span style="color: #008000"> "grey54"              </span>│<span style="color: #000080"> #8a8a8a </span>│<span style="color: #800080"> rgb(138,138,138) </span>║
    ║ <span style="background-color: #949494">          </span> │<span style="color: #808000">    246 </span>│<span style="color: #008000"> "grey58"              </span>│<span style="color: #000080"> #949494 </span>│<span style="color: #800080"> rgb(148,148,148) </span>║
    ║ <span style="background-color: #9e9e9e">          </span> │<span style="color: #808000">    247 </span>│<span style="color: #008000"> "grey62"              </span>│<span style="color: #000080"> #9e9e9e </span>│<span style="color: #800080"> rgb(158,158,158) </span>║
    ║ <span style="background-color: #a8a8a8">          </span> │<span style="color: #808000">    248 </span>│<span style="color: #008000"> "grey66"              </span>│<span style="color: #000080"> #a8a8a8 </span>│<span style="color: #800080"> rgb(168,168,168) </span>║
    ║ <span style="background-color: #b2b2b2">          </span> │<span style="color: #808000">    249 </span>│<span style="color: #008000"> "grey70"              </span>│<span style="color: #000080"> #b2b2b2 </span>│<span style="color: #800080"> rgb(178,178,178) </span>║
    ║ <span style="background-color: #bcbcbc">          </span> │<span style="color: #808000">    250 </span>│<span style="color: #008000"> "grey74"              </span>│<span style="color: #000080"> #bcbcbc </span>│<span style="color: #800080"> rgb(188,188,188) </span>║
    ║ <span style="background-color: #c6c6c6">          </span> │<span style="color: #808000">    251 </span>│<span style="color: #008000"> "grey78"              </span>│<span style="color: #000080"> #c6c6c6 </span>│<span style="color: #800080"> rgb(198,198,198) </span>║
    ║ <span style="background-color: #d0d0d0">          </span> │<span style="color: #808000">    252 </span>│<span style="color: #008000"> "grey82"              </span>│<span style="color: #000080"> #d0d0d0 </span>│<span style="color: #800080"> rgb(208,208,208) </span>║
    ║ <span style="background-color: #dadada">          </span> │<span style="color: #808000">    253 </span>│<span style="color: #008000"> "grey85"              </span>│<span style="color: #000080"> #dadada </span>│<span style="color: #800080"> rgb(218,218,218) </span>║
    ║ <span style="background-color: #e4e4e4">          </span> │<span style="color: #808000">    254 </span>│<span style="color: #008000"> "grey89"              </span>│<span style="color: #000080"> #e4e4e4 </span>│<span style="color: #800080"> rgb(228,228,228) </span>║
    ║ <span style="background-color: #eeeeee">          </span> │<span style="color: #808000">    255 </span>│<span style="color: #008000"> "grey93"              </span>│<span style="color: #000080"> #eeeeee </span>│<span style="color: #800080"> rgb(238,238,238) </span>║
    ╚════════════╧════════╧═══════════════════════╧═════════╧══════════════════╝
    </pre>
```

----------------------------------------

TITLE: Displaying Terminal Color Swatches with HTML Styling
DESCRIPTION: An HTML-based representation of a terminal color palette table showing color swatches, indices, names, hex codes, and RGB values. This snippet demonstrates how Rich displays color information in styled HTML output.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/appendix/colors.rst#2025-04-16_snippet_2

LANGUAGE: html
CODE:
```
║ <span style="background-color: #afafaf">          </span> │<span style="color: #808000">    145 </span>│<span style="color: #008000"> "grey69"              </span>│<span style="color: #000080"> #afafaf </span>│<span style="color: #800080"> rgb(175,175,175) </span>║
║ <span style="background-color: #afafd7">          </span> │<span style="color: #808000">    146 </span>│<span style="color: #008000"> "light_steel_blue3"   </span>│<span style="color: #000080"> #afafd7 </span>│<span style="color: #800080"> rgb(175,175,215) </span>║
║ <span style="background-color: #afafff">          </span> │<span style="color: #808000">    147 </span>│<span style="color: #008000"> "light_steel_blue"    </span>│<span style="color: #000080"> #afafff </span>│<span style="color: #800080"> rgb(175,175,255) </span>║
║ <span style="background-color: #afd75f">          </span> │<span style="color: #808000">    149 </span>│<span style="color: #008000"> "dark_olive_green3"   </span>│<span style="color: #000080"> #afd75f </span>│<span style="color: #800080"> rgb(175,215,95)  </span>║
║ <span style="background-color: #afd787">          </span> │<span style="color: #808000">    150 </span>│<span style="color: #008000"> "dark_sea_green3"     </span>│<span style="color: #000080"> #afd787 </span>│<span style="color: #800080"> rgb(175,215,135) </span>║
║ <span style="background-color: #afd7d7">          </span> │<span style="color: #808000">    152 </span>│<span style="color: #008000"> "light_cyan3"         </span>│<span style="color: #000080"> #afd7d7 </span>│<span style="color: #800080"> rgb(175,215,215) </span>║
║ <span style="background-color: #afd7ff">          </span> │<span style="color: #808000">    153 </span>│<span style="color: #008000"> "light_sky_blue1"     </span>│<span style="color: #000080"> #afd7ff </span>│<span style="color: #800080"> rgb(175,215,255) </span>║
║ <span style="background-color: #afff00">          </span> │<span style="color: #808000">    154 </span>│<span style="color: #008000"> "green_yellow"        </span>│<span style="color: #000080"> #afff00 </span>│<span style="color: #800080"> rgb(175,255,0)   </span>║
║ <span style="background-color: #afff5f">          </span> │<span style="color: #808000">    155 </span>│<span style="color: #008000"> "dark_olive_green2"   </span>│<span style="color: #000080"> #afff5f </span>│<span style="color: #800080"> rgb(175,255,95)  </span>║
║ <span style="background-color: #afff87">          </span> │<span style="color: #808000">    156 </span>│<span style="color: #008000"> "pale_green1"         </span>│<span style="color: #000080"> #afff87 </span>│<span style="color: #800080"> rgb(175,255,135) </span>║
║ <span style="background-color: #afffaf">          </span> │<span style="color: #808000">    157 </span>│<span style="color: #008000"> "dark_sea_green2"     </span>│<span style="color: #000080"> #afffaf </span>│<span style="color: #800080"> rgb(175,255,175) </span>║
║ <span style="background-color: #afffff">          </span> │<span style="color: #808000">    159 </span>│<span style="color: #008000"> "pale_turquoise1"     </span>│<span style="color: #000080"> #afffff </span>│<span style="color: #800080"> rgb(175,255,255) </span>║
║ <span style="background-color: #d70000">          </span> │<span style="color: #808000">    160 </span>│<span style="color: #008000"> "red3"                </span>│<span style="color: #000080"> #d70000 </span>│<span style="color: #800080"> rgb(215,0,0)     </span>║
║ <span style="background-color: #d70087">          </span> │<span style="color: #808000">    162 </span>│<span style="color: #008000"> "deep_pink3"          </span>│<span style="color: #000080"> #d70087 </span>│<span style="color: #800080"> rgb(215,0,135)   </span>║
║ <span style="background-color: #d700d7">          </span> │<span style="color: #808000">    164 </span>│<span style="color: #008000"> "magenta3"            </span>│<span style="color: #000080"> #d700d7 </span>│<span style="color: #800080"> rgb(215,0,215)   </span>║
║ <span style="background-color: #d75f00">          </span> │<span style="color: #808000">    166 </span>│<span style="color: #008000"> "dark_orange3"        </span>│<span style="color: #000080"> #d75f00 </span>│<span style="color: #800080"> rgb(215,95,0)    </span>║
║ <span style="background-color: #d75f5f">          </span> │<span style="color: #808000">    167 </span>│<span style="color: #008000"> "indian_red"          </span>│<span style="color: #000080"> #d75f5f </span>│<span style="color: #800080"> rgb(215,95,95)   </span>║
║ <span style="background-color: #d75f87">          </span> │<span style="color: #808000">    168 </span>│<span style="color: #008000"> "hot_pink3"           </span>│<span style="color: #000080"> #d75f87 </span>│<span style="color: #800080"> rgb(215,95,135)  </span>║
║ <span style="background-color: #d75faf">          </span> │<span style="color: #808000">    169 </span>│<span style="color: #008000"> "hot_pink2"           </span>│<span style="color: #000080"> #d75faf </span>│<span style="color: #800080"> rgb(215,95,175)  </span>║
║ <span style="background-color: #d75fd7">          </span> │<span style="color: #808000">    170 </span>│<span style="color: #008000"> "orchid"              </span>│<span style="color: #000080"> #d75fd7 </span>│<span style="color: #800080"> rgb(215,95,215)  </span>║
║ <span style="background-color: #d78700">          </span> │<span style="color: #808000">    172 </span>│<span style="color: #008000"> "orange3"             </span>│<span style="color: #000080"> #d78700 </span>│<span style="color: #800080"> rgb(215,135,0)   </span>║
║ <span style="background-color: #d7875f">          </span> │<span style="color: #808000">    173 </span>│<span style="color: #008000"> "light_salmon3"       </span>│<span style="color: #000080"> #d7875f </span>│<span style="color: #800080"> rgb(215,135,95)  </span>║
║ <span style="background-color: #d78787">          </span> │<span style="color: #808000">    174 </span>│<span style="color: #008000"> "light_pink3"         </span>│<span style="color: #000080"> #d78787 </span>│<span style="color: #800080"> rgb(215,135,135) </span>║
║ <span style="background-color: #d787af">          </span> │<span style="color: #808000">    175 </span>│<span style="color: #008000"> "pink3"               </span>│<span style="color: #000080"> #d787af </span>│<span style="color: #800080"> rgb(215,135,175) </span>║
║ <span style="background-color: #d787d7">          </span> │<span style="color: #808000">    176 </span>│<span style="color: #008000"> "plum3"               </span>│<span style="color: #000080"> #d787d7 </span>│<span style="color: #800080"> rgb(215,135,215) </span>║
║ <span style="background-color: #d787ff">          </span> │<span style="color: #808000">    177 </span>│<span style="color: #008000"> "violet"              </span>│<span style="color: #000080"> #d787ff </span>│<span style="color: #800080"> rgb(215,135,255) </span>║
║ <span style="background-color: #d7af00">          </span> │<span style="color: #808000">    178 </span>│<span style="color: #008000"> "gold3"               </span>│<span style="color: #000080"> #d7af00 </span>│<span style="color: #800080"> rgb(215,175,0)   </span>║
║ <span style="background-color: #d7af5f">          </span> │<span style="color: #808000">    179 </span>│<span style="color: #008000"> "light_goldenrod3"    </span>│<span style="color: #000080"> #d7af5f </span>│<span style="color: #800080"> rgb(215,175,95)  </span>║
║ <span style="background-color: #d7af87">          </span> │<span style="color: #808000">    180 </span>│<span style="color: #008000"> "tan"                 </span>│<span style="color: #000080"> #d7af87 </span>│<span style="color: #800080"> rgb(215,175,135) </span>║
║ <span style="background-color: #d7afaf">          </span> │<span style="color: #808000">    181 </span>│<span style="color: #008000"> "misty_rose3"         </span>│<span style="color: #000080"> #d7afaf </span>│<span style="color: #800080"> rgb(215,175,175) </span>║
║ <span style="background-color: #d7afd7">          </span> │<span style="color: #808000">    182 </span>│<span style="color: #008000"> "thistle3"            </span>│<span style="color: #000080"> #d7afd7 </span>│<span style="color: #800080"> rgb(215,175,215) </span>║
║ <span style="background-color: #d7afff">          </span> │<span style="color: #808000">    183 </span>│<span style="color: #008000"> "plum2"               </span>│<span style="color: #000080"> #d7afff </span>│<span style="color: #800080"> rgb(215,175,255) </span>║
║ <span style="background-color: #d7d700">          </span> │<span style="color: #808000">    184 </span>│<span style="color: #008000"> "yellow3"             </span>│<span style="color: #000080"> #d7d700 </span>│<span style="color: #800080"> rgb(215,215,0)   </span>║
║ <span style="background-color: #d7d75f">          </span> │<span style="color: #808000">    185 </span>│<span style="color: #008000"> "khaki3"              </span>│<span style="color: #000080"> #d7d75f </span>│<span style="color: #800080"> rgb(215,215,95)  </span>║
║ <span style="background-color: #d7d7af">          </span> │<span style="color: #808000">    187 </span>│<span style="color: #008000"> "light_yellow3"       </span>│<span style="color: #000080"> #d7d7af </span>│<span style="color: #800080"> rgb(215,215,175) </span>║
║ <span style="background-color: #d7d7d7">          </span> │<span style="color: #808000">    188 </span>│<span style="color: #008000"> "grey84"              </span>│<span style="color: #000080"> #d7d7d7 </span>│<span style="color: #800080"> rgb(215,215,215) </span>║
```

----------------------------------------

TITLE: Testing Rich in terminal
DESCRIPTION: Command to run a demonstration of Rich capabilities directly in your terminal. This shows various formatting features without writing any code.
SOURCE: https://github.com/Textualize/rich/blob/master/README.fa.md#2025-04-16_snippet_1

LANGUAGE: sh
CODE:
```
python -m rich
```

----------------------------------------

TITLE: Initializing a Basic Layout in Python
DESCRIPTION: Creates a basic Layout object and prints it to the terminal, which will display a box the size of the terminal with layout information.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/layout.rst#2025-04-16_snippet_0

LANGUAGE: python
CODE:
```
from rich import print
from rich.layout import Layout

layout = Layout()
print(layout)
```

----------------------------------------

TITLE: Testing Latest Commit on Current Branch
DESCRIPTION: Command to run benchmarks against the most recent commit on your current branch.
SOURCE: https://github.com/Textualize/rich/blob/master/benchmarks/README.md#2025-04-16_snippet_1

LANGUAGE: bash
CODE:
```
asv run HEAD^!
```

----------------------------------------

TITLE: Defining Appendix Table of Contents in reStructuredText
DESCRIPTION: A reStructuredText directive that creates a table of contents for the appendix section, with a maximum depth of 3 levels, linking to box and colors reference documentation.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/appendix.rst#2025-04-16_snippet_0

LANGUAGE: restructuredtext
CODE:
```
.. toctree::
   :maxdepth: 3

   appendix/box.rst
   appendix/colors.rst
```

----------------------------------------

TITLE: Specifying Python Package Dependencies for Rich Library
DESCRIPTION: This snippet lists the required Python packages and their versions for the Rich library project. It includes Sphinx for documentation generation, alabaster and sphinx-rtd-theme for theming, and sphinx-copybutton for enhanced functionality.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/requirements.txt#2025-04-16_snippet_0

LANGUAGE: Text
CODE:
```
alabaster==1.0.0
Sphinx==8.2.3
sphinx-rtd-theme==3.0.2
sphinx-copybutton==0.5.2
```

----------------------------------------

TITLE: Installing Rich with pip
DESCRIPTION: Command to install the Rich library using pip package manager. This installs the latest version of Rich from PyPI.
SOURCE: https://github.com/Textualize/rich/blob/master/README.sv.md#2025-04-16_snippet_0

LANGUAGE: sh
CODE:
```
python -m pip install rich
```

----------------------------------------

TITLE: Installing Rich in Python REPL for Pretty Printing
DESCRIPTION: Code to install Rich in the Python REPL environment to automatically format and highlight all data structures.
SOURCE: https://github.com/Textualize/rich/blob/master/README.fr.md#2025-04-16_snippet_3

LANGUAGE: python
CODE:
```
>>> from rich import pretty
>>> pretty.install()
```

----------------------------------------

TITLE: Installing Rich Python Library
DESCRIPTION: Command to install Rich using pip package manager. This installs the Rich library which provides terminal text formatting capabilities.
SOURCE: https://github.com/Textualize/rich/blob/master/README.pt-br.md#2025-04-16_snippet_0

LANGUAGE: sh
CODE:
```
python -m pip install rich
```

----------------------------------------

TITLE: Markdown Contributors List
DESCRIPTION: An alphabetically sorted list of contributors with links to their GitHub profiles or personal websites formatted in Markdown.
SOURCE: https://github.com/Textualize/rich/blob/master/CONTRIBUTORS.md#2025-04-16_snippet_0

LANGUAGE: markdown
CODE:
```
# Contributors

The following people have contributed to the development of Rich:

<!-- Add your name below, sort alphabetically by surname. Link to GitHub profile / your home page. -->

- [Patrick Arminio](https://github.com/patrick91)
- [Gregory Beauregard](https://github.com/GBeauregard/pyffstream)
- [Artur Borecki](https://github.com/pufereq)
- [Pedro Aaron](https://github.com/paaaron)
[...truncated for brevity...]
```

----------------------------------------

TITLE: RST Documentation Reference for Rich Align Module
DESCRIPTION: ReStructuredText directive for auto-generating documentation for the rich.align module and its members.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/reference/align.rst#2025-04-16_snippet_0

LANGUAGE: rst
CODE:
```
.. automodule:: rich.align
    :members:
```

----------------------------------------

TITLE: Installing Rich Python Library
DESCRIPTION: Command to install Rich using pip. This will install the latest version of Rich from PyPI.
SOURCE: https://github.com/Textualize/rich/blob/master/README.ru.md#2025-04-16_snippet_0

LANGUAGE: sh
CODE:
```
python -m pip install rich
```

----------------------------------------

TITLE: Importing Pretty Print Method - Python
DESCRIPTION: This code snippet shows how to import the pprint method from the rich.pretty module for pretty printing objects in Python. The pprint function can be customized with various arguments.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/pretty.rst#2025-04-16_snippet_0

LANGUAGE: Python
CODE:
```
>>> from rich.pretty import pprint
>>> pprint(locals())
```

----------------------------------------

TITLE: Using Rich Inspect Function in Python
DESCRIPTION: Example of using Rich's inspect function to display detailed information about a Python object, including its methods.
SOURCE: https://github.com/Textualize/rich/blob/master/README.ru.md#2025-04-16_snippet_8

LANGUAGE: python
CODE:
```
>>> my_list = ["foo", "bar"]
>>> from rich import inspect
>>> inspect(my_list, methods=True)
```

----------------------------------------

TITLE: Cat ASCII Art Design for Rich Text Library
DESCRIPTION: An ASCII art representation of a cat, using basic text characters to create a visual design. The cat drawing includes features like eyes, whiskers, and a box-like body structure.
SOURCE: https://github.com/Textualize/rich/blob/master/assets/logo.txt#2025-04-16_snippet_0

LANGUAGE: ascii-art
CODE:
```
 .-----------.\n/___/__|__\___\\n\     oo      /\n \_o8o888___ /\n /888888(. .)8.\n|\"\"\"\"\"[H]\\ /\"\"|\n|-- `. - |^| -|\n|__ _)\__|_| _|\n  _(________)_\n (____________)
```

----------------------------------------

TITLE: Configuring Sphinx automodule for Rich Columns Documentation
DESCRIPTION: ReStructuredText directive to automatically generate documentation for the rich.columns module, including all its members.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/reference/columns.rst#2025-04-16_snippet_0

LANGUAGE: restructuredtext
CODE:
```
.. automodule:: rich.columns
    :members:
```

----------------------------------------

TITLE: Documenting rich.tree module with automodule
DESCRIPTION: This snippet uses the Sphinx `automodule` directive to automatically generate documentation for the `rich.tree` module.  The `:members:` option ensures that all members of the module are included in the documentation.  This approach simplifies the documentation process by directly extracting information from the code.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/reference/tree.rst#2025-04-16_snippet_0

LANGUAGE: Sphinx
CODE:
```
.. automodule:: rich.tree
    :members: 
```

----------------------------------------

TITLE: Defining Rich Traceback Omission in Python
DESCRIPTION: Python code blocks can opt out of being rendered in Rich tracebacks by setting a _rich_traceback_omit flag in their local scope.
SOURCE: https://github.com/Textualize/rich/blob/master/CHANGELOG.md#2025-04-16_snippet_2

LANGUAGE: python
CODE:
```
_rich_traceback_omit = True
```

----------------------------------------

TITLE: Basic printing with Rich Console
DESCRIPTION: Basic example of using the Console object's print method to output text to the terminal. The console will automatically word-wrap text to fit the terminal width.
SOURCE: https://github.com/Textualize/rich/blob/master/README.hi.md#2025-04-16_snippet_5

LANGUAGE: python
CODE:
```
console.print("Hello", "World!")
```

----------------------------------------

TITLE: Sphinx AutoModule Documentation Configuration for Rich Color Module
DESCRIPTION: Sphinx configuration directive to automatically generate documentation for the rich.color module, including all members. This uses reStructuredText format to define documentation parameters.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/reference/color.rst#2025-04-16_snippet_0

LANGUAGE: rst
CODE:
```
.. automodule:: rich.color
    :members:
```

----------------------------------------

TITLE: Copying Generated HTML to Benchmark Repository
DESCRIPTION: Command to copy the generated benchmark HTML to the rich-benchmarks repository for publishing.
SOURCE: https://github.com/Textualize/rich/blob/master/benchmarks/README.md#2025-04-16_snippet_5

LANGUAGE: bash
CODE:
```
cp -r ../rich/benchmarks/html/* .
```

----------------------------------------

TITLE: Implementing __rich__ Method for Simple Custom Formatting in Python
DESCRIPTION: A basic example showing how to implement the __rich__ method in a custom class to return a string with console markup. This allows the object to be rendered with custom formatting when printed with Rich.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/protocol.rst#2025-04-16_snippet_0

LANGUAGE: python
CODE:
```
class MyObject:
    def __rich__(self) -> str:
        return "[bold cyan]MyObject()"
```

----------------------------------------

TITLE: Installing Rich using pip in Python
DESCRIPTION: Command to install the Rich library using pip package manager. This installs Rich from PyPI to enable rich text formatting in terminal applications.
SOURCE: https://github.com/Textualize/rich/blob/master/README.hi.md#2025-04-16_snippet_0

LANGUAGE: shell
CODE:
```
python -m pip install rich
```

----------------------------------------

TITLE: Running Benchmarks for Tagged Versions
DESCRIPTION: Command to run benchmarks for specific tagged versions listed in the asvhashfile.
SOURCE: https://github.com/Textualize/rich/blob/master/benchmarks/README.md#2025-04-16_snippet_3

LANGUAGE: bash
CODE:
```
asv run HASHFILE:asvhashfile
```

----------------------------------------

TITLE: Configuring Rich Module Documentation with reStructuredText
DESCRIPTION: Configuration directive for automatically generating module documentation using Sphinx automodule directive. Includes all members of the rich module in the generated documentation.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/reference/init.rst#2025-04-16_snippet_0

LANGUAGE: restructuredtext
CODE:
```
.. automodule:: rich
    :members:
```

----------------------------------------

TITLE: Configuring Sphinx AutoModule for rich.layout
DESCRIPTION: RST directive to automatically generate documentation from rich.layout module including all members.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/reference/layout.rst#2025-04-16_snippet_0

LANGUAGE: rst
CODE:
```
.. automodule:: rich.layout
    :members:
```

----------------------------------------

TITLE: HTML Color Sample Definitions
DESCRIPTION: HTML table rows showing color definitions with background color samples, color names, hex codes and RGB values. Each row contains styled spans for visual color representation and color code formatting.
SOURCE: https://github.com/Textualize/rich/blob/master/docs/source/appendix/colors.rst#2025-04-16_snippet_3

LANGUAGE: html
CODE:
```
<span style="background-color: #d7d7ff">          </span> │<span style="color: #808000">    189 </span>│<span style="color: #008000"> "light_steel_blue1"   </span>│<span style="color: #000080"> #d7d7ff </span>│<span style="color: #800080"> rgb(215,215,255) </span>
```

----------------------------------------

TITLE: Installing Rich with Python pip
DESCRIPTION: Command for installing the Rich Python package using pip package manager.
SOURCE: https://github.com/Textualize/rich/blob/master/README.fr.md#2025-04-16_snippet_0

LANGUAGE: sh
CODE:
```
python -m pip install rich
```

----------------------------------------

TITLE: Installing Rich with pip
DESCRIPTION: Command to install the Rich library using pip package manager.
SOURCE: https://github.com/Textualize/rich/blob/master/README.de-ch.md#2025-04-16_snippet_0

LANGUAGE: sh
CODE:
```
python -m pip install rich
```
