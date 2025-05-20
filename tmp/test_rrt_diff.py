from rich.console import Console
from rich.syntax import Syntax

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

console.rule("[bold green]Testing 'rrt' theme with 'diff' lexer[/]")
syntax_rrt_diff = Syntax(sample_diff_text, "diff", theme="rrt", line_numbers=False)
console.print(syntax_rrt_diff)

console.rule("[bold green]Testing 'monokai' theme with 'diff' lexer (for comparison)[/]")
syntax_monokai_diff = Syntax(sample_diff_text, "diff", theme="monokai", line_numbers=False)
console.print(syntax_monokai_diff)

console.rule("[bold green]Testing 'rrt' theme with 'python' lexer (known good from previous test)[/]")
python_code = "def foo():\n  return 'bar'"
syntax_rrt_python = Syntax(python_code, "python", theme="rrt", line_numbers=True)
console.print(syntax_rrt_python)
