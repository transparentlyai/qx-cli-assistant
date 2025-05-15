import asyncio
import os
import shlex
import shutil
import subprocess
from pathlib import Path

from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.formatted_text import HTML
from rich.console import Console as RichConsole

from qx.core.paths import Q_HISTORY_FILE # Import the history file path

async def get_user_input(console: RichConsole) -> str:
    """
    Asynchronously gets user input from the QX prompt using prompt_toolkit,
    with fzf-based history search on Ctrl-R.

    Args:
        console: The Rich Console object for printing messages (e.g., fzf not found).

    Returns:
        The string entered by the user.
    """
    
    # Ensure the directory for the history file exists
    try:
        Q_HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        console.print(f"[warning]Warning: Could not create history directory {Q_HISTORY_FILE.parent}: {e}[/warning]")
        # History will likely fail or be in-memory only if this occurs.

    history = FileHistory(str(Q_HISTORY_FILE))
    kb = KeyBindings()

    @kb.add('c-r')
    def _(event):
        """
        Handle Ctrl-R: Open fzf with command history.
        """
        if not shutil.which('fzf'):
            console.print("[warning]fzf not found. Ctrl-R history search disabled.[/warning]")
            # Optionally, could provide a small line to the prompt buffer indicating this.
            # event.app.current_buffer.insert_text(" # fzf not found")
            return

        if not Q_HISTORY_FILE.exists() or Q_HISTORY_FILE.stat().st_size == 0:
            # console.print("[info]History file is empty or does not exist.[/info]")
            # No history to search
            return

        try:
            fzf_cmd = ['fzf', '--height', '40%', '--reverse', '--tac']
            
            # Pass history file content to fzf's stdin
            history_content = Q_HISTORY_FILE.read_text(encoding='utf-8')
            
            process = subprocess.run(
                fzf_cmd,
                input=history_content,
                capture_output=True,
                text=True,
                check=False  # Don't raise for non-zero exit if user cancels fzf
            )

            if process.returncode == 0 and process.stdout: # 0 is success for fzf
                selected_command = process.stdout.strip()
                event.app.current_buffer.text = selected_command
                event.app.current_buffer.cursor_position = len(selected_command)
            # elif process.returncode == 1: # No match
                # Do nothing, buffer remains as is
            # elif process.returncode == 130: # User cancelled fzf (Ctrl-C, Esc)
                # Do nothing, buffer remains as is
            elif process.returncode not in [0, 1, 130]: # Other errors
                console.print(f"[error]fzf error (code {process.returncode}): {process.stderr.strip()}[/error]")

        except FileNotFoundError: # Should be caught by shutil.which, but as a fallback
            console.print("[warning]fzf command not found during execution. Ctrl-R history search disabled.[/warning]")
        except Exception as e:
            console.print(f"[error]Error during fzf history search: {e}[/error]")

    prompt_message_html = HTML('<style fg="ansicyan" bold="true">Q⏵ </style>')
    
    # Use PromptSession for history and key bindings
    session = PromptSession(
        history=history,
        key_bindings=kb,
        # enable_history_search=True, # Standard Ctrl-R, conflicts if we define our own
    )

    # prompt_toolkit's prompt is synchronous, run in a thread.
    user_input = await asyncio.to_thread(
        session.prompt,
        prompt_message_html,
    )
    return user_input

if __name__ == '__main__':
    # Example of how to test this module directly
    async def main_test():
        console_for_test = RichConsole()
        print("Testing qprompt. Type Ctrl-R for fzf history (if fzf is installed).")
        print(f"History file will be: {Q_HISTORY_FILE}")
        # Ensure history dir exists for test
        Q_HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        # Add some dummy history for testing fzf
        if not Q_HISTORY_FILE.exists() or Q_HISTORY_FILE.stat().st_size == 0:
             with open(Q_HISTORY_FILE, "w", encoding="utf-8") as f:
                f.write("ls -la\\n")
                f.write("echo \\"hello world\\"\\n")
                f.write("git status\\n")
                f.write("python script.py --arg value\\n")
        
        while True:
            try:
                inp = await get_user_input(console_for_test)
                if inp.lower() == 'exit':
                    break
                print(f"You entered: {inp}")
            except KeyboardInterrupt:
                print("Exiting test.")
                break
            except EOFError:
                print("Exiting test (EOF).")
                break

    asyncio.run(main_test())