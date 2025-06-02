from rich.console import Console
from rich.syntax import Syntax
from pygments.styles import get_all_styles

console = Console()

sample_diff = """
--- a/old_file.txt
+++ b/new_file.txt
@@ -1,3 +1,3 @@
-This is line 1
+This is the new line 1
 This is line 2
-This is line 3
+This is the updated line 3
"""

console.print("[bold yellow]--- Pygments Diff Theme Previews ---\n[/bold yellow]")

for style_name in sorted(list(get_all_styles())):
    console.print(f"[bold blue]Theme: {style_name}[/bold blue]")
    try:
        syntax = Syntax(sample_diff, "diff", theme=style_name, line_numbers=False)
        console.print(syntax)
    except Exception as e:
        console.print(f"[red]Error rendering with theme {style_name}: {e}[/red]")
    console.print("\n")

console.print("[bold yellow]--- End of Previews ---\n[/bold yellow]")
