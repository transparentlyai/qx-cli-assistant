from textual.app import App, ComposeResult
from textual.widgets import RichLog

class MinimalRichLogApp(App):
    def compose(self) -> ComposeResult:
        yield RichLog(id="test-log", markup=True)

if __name__ == "__main__":
    app = MinimalRichLogApp()
    app.run()
