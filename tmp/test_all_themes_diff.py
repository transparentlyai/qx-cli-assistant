from rich.console import Console
from rich.syntax import Syntax
from pygments.styles import get_all_styles

console = Console()

sample_diff_text = """
--- a/file.txt
+++ b/file.txt
@@ -1,3 +1,3 @@
-Hello World
+Hello Rich World
 This is a sample file.
 Another line.
"""

available_themes = list(get_all_styles())

console.print(f"[bold yellow]Found {len(available_themes)} available themes. Testing diff rendering for each...[/bold yellow]\n")

for theme_name in available_themes:
    console.rule(f"[bold green]Theme: '{theme_name}'[/]")
    try:
        syntax_themed_diff = Syntax(sample_diff_text, "diff", theme=theme_name, line_numbers=False, background_color="default")
        console.print(syntax_themed_diff)
        console.print("\n") # Add some spacing
    except Exception as e:
        console.print(f"[red]Could not render theme '{theme_name}': {e}[/red]\n")

console.print("[bold yellow]Finished testing all themes.[/bold yellow]")
