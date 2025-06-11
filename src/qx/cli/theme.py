from rich.console import Console
from rich.theme import Theme

# Define the application's Rich theme
# This can be expanded with more styles as needed.
# Example styles:
# "info": "dim cyan",
# "warning": "magenta",
# "danger": "bold red"

custom_theme = Theme(
    {
        "primary": "blue",
        "secondary": "dim green",
        "highlight": "yellow on black",
        "info": "cyan",
        "warning": "yellow",
        "error": "red",
        "debug": "dim white",
        "success": "green",
        "attention": "yellow",
        "critical": "bright_red",
        # UI elements
        "app.title": "bold white on blue",
        "app.header": "bold yellow",
        "app.footer": "dim white",
        # Text styles
        "text.default": "white",
        "text.muted": "dim white",
        "text.important": "bold yellow",
        # Log levels
        "log.debug": "dim blue",
        "log.info": "blue",
        "log.warning": "yellow",
        "log.error": "bold red",
        "log.critical": "bold white on red",
        # Table styles
        "table.header": "bold magenta",
        "table.footer": "dim magenta",
        "table.cell": "white",
        "table.odd_row": "on grey11",
        "table.even_row": "none",
        # Prompt toolkit styles (if you integrate with prompt_toolkit and Rich)
        # These are just examples and might need adjustment based on usage
        "prompt.default": "bold green",
        "prompt.text": "white",
        "prompt.arg": "cyan",
        "prompt.value": "yellow",
        # Markdown specific styles (if rendering markdown)
        "markdown.h1": "bold blue",
        "markdown.h2": "bold green",
        "markdown.code": "dim cyan",
        "markdown.link": "underline blue",
        # Other common elements
        "spinner": "bold blue",
        "progress.bar": "blue",
        "progress.percentage": "blue",
        "rule.line": "dim blue",
        "repr.str": "green",
        "repr.number": "cyan",
        "repr.bool_true": "bold green",
        "repr.bool_false": "bold red",
        "repr.none": "magenta",
        "numbers": "blue",  # Added new style for numbers
    }
)

# To use this theme in your Rich Console:
# from rich.console import Console
# from qx.cli.theme import custom_theme
# console = Console(theme=custom_theme)
# console.print("This is a [primary]primary[/] message.")
# console.print("This is an [error]error[/] message.")
# console.print("This is a [success]success[/] message.")

# Markdown-specific themes for BorderedMarkdown
default_markdown_theme = Theme(
    {
        "markdown.h1": "bold underline bright_white",
        "markdown.h2": "bold underline white",
        "markdown.h3": "bold underline dim white",
        "markdown.h4": "bold underline white",
        "markdown.h5": "bold underline dim white",
        "markdown.h6": "bold underline dim white",
        "markdown.text": "white",
        "markdown.paragraph": "#e4e4e4",
        "markdown.emphasis": "italic",
        "markdown.strong": "bold #ffd787",
        "markdown.code": "#5f87d7",
        "markdown.code_block": "cyan on grey11",
        "markdown.link": "underline blue",
        "markdown.link_url": "dim blue",
        "markdown.list": "white",
        "markdown.list_item": "white",
        "markdown.quote": "italic dim white",
        "markdown.hr": " #ff8700",
        "markdown.item.bullet": "bold yellow",
        "markdown.item.number": "bold yellow",
        "code": "#5f87d7",
    }
)

dimmed_grey_markdown_theme = Theme(
    {
        "markdown.h1": "bold grey42",
        "markdown.h2": "bold grey39",
        "markdown.h3": "bold grey35",
        "markdown.h4": "grey30",
        "markdown.h5": "grey27",
        "markdown.h6": "grey23",
        "markdown.text": "grey39",
        "markdown.paragraph": "grey39",
        "markdown.emphasis": "italic grey35",
        "markdown.strong": "bold grey42",
        "markdown.code": "bold grey46",
        "markdown.code_block": "grey42 on grey11",
        "markdown.link": "underline grey35",
        "markdown.link_url": "grey27",
        "markdown.list": "grey39",
        "markdown.list_item": "grey39",
        "markdown.quote": "italic grey27",
        "markdown.hr": "grey23",
        "markdown.item.bullet": "bold grey35",
        "markdown.item.number": "bold grey35",
        "code": "bold grey46",
    }
)

# Global themed console instance
themed_console = Console(theme=custom_theme)


if __name__ == "__main__":
    console = Console(theme=custom_theme)

    console.print("Demonstrating QX CLI Theme Styles", style="app.title")
    console.print("-" * 40, style="rule.line")

    console.print("Primary text style", style="primary")
    console.print("Secondary text style", style="secondary")
    console.print("[highlight]Highlighted text[/highlight]")
    console.print("Info message", style="info")
    console.print("Warning message", style="warning")
    console.print("Error message", style="error")
    console.print("Debug message", style="debug")
    console.print("Success message!", style="success")

    console.print("\nApp UI Styles:", style="app.header")
    console.print("This is a footer style", style="app.footer")

    console.print("\nText Styles:", style="app.header")
    console.print("Default text.", style="text.default")
    console.print("Muted text.", style="text.muted")
    console.print("Important text.", style="text.important")

    console.print("\nLog Level Styles:", style="app.header")
    console.print("This is a debug log.", style="log.debug")
    console.print("This is an info log.", style="log.info")
    console.print("This is a warning log.", style="log.warning")
    console.print("This is an error log.", style="log.error")
    console.print("This is a critical log.", style="log.critical")

    console.print("\nMarkdown Styles (example):", style="app.header")
    console.print("# Markdown H1", style="markdown.h1")
    console.print("## Markdown H2", style="markdown.h2")
    console.print("`some_code_snippet()`", style="markdown.code")
    console.print("A [markdown.link]link to somewhere[/markdown.link]")

    console.print("\nOther Elements:", style="app.header")
    console.print("Spinner style (conceptual)", style="spinner")
    console.print("Progress bar style (conceptual)", style="progress.bar")
    console.print("Rule line below:", style="text.default")
    console.rule()

    console.print("\nRepresentations:", style="app.header")
    console.print("String representation", style="repr.str")
    console.print(12345, style="repr.number")
    console.print(True, style="repr.bool_true")
    console.print(False, style="repr.bool_false")
    console.print(None, style="repr.none")
    console.print(
        "This is a [numbers]12345[/] number.", style="numbers"
    )  # Added example for new style

    console.print("-" * 40, style="rule.line")
    console.print("Theme demonstration complete.", style="app.title")
