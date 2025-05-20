from rich.console import Console
from rich.syntax import Syntax

console = Console()

python_code = """
def example_function(name: str) -> str:
    # This is a comment
    greeting = f"Hello, {name}!"
    print(greeting)
    return greeting

class MyClass:
    def __init__(self, value: int):
        self.value = value

# Calling the function
example_function("World")
"""

console.rule("[bold green]Testing 'rrt' theme (should have dark background & highlights)[/]")
syntax_rrt = Syntax(python_code, "python", theme="rrt", line_numbers=True)
console.print(syntax_rrt)

console.rule("[bold green]Testing 'monokai' theme (should have dark background & highlights)[/]")
syntax_monokai = Syntax(python_code, "python", theme="monokai", line_numbers=True)
console.print(syntax_monokai)

console.rule("[bold green]Testing 'rrt' theme with background_color='default' (original problematic case)[/]")
syntax_rrt_default_bg = Syntax(python_code, "python", theme="rrt", line_numbers=True, background_color="default")
console.print(syntax_rrt_default_bg)
