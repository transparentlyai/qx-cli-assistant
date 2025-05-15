import asyncio
import os
import shlex
import shutil
import subprocess
from pathlib import Path
from datetime import datetime # New import

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

    history = FileHistory(str(Q_HISTORY_FILE))
    kb = KeyBindings()

    @kb.add('c-r')
    def _(event):
        """
        Handle Ctrl-R: Open fzf with command history, formatted with dates.
        """
        if not shutil.which('fzf'):
            console.print("[warning]fzf not found. Ctrl-R history search disabled.[/warning]")
            return

        if not Q_HISTORY_FILE.exists() or Q_HISTORY_FILE.stat().st_size == 0:
            return

        try:
            fzf_cmd = ['fzf', '--height', '40%', '--reverse', '--tac']
            
            raw_history_lines = Q_HISTORY_FILE.read_text(encoding='utf-8').splitlines()
            processed_history_for_fzf = []
            
            # Date format: [DD Mon HH:MM] (e.g., [15 May 18:08]) - length 15
            date_format_str = "[%d %b %H:%M]"
            date_placeholder_len = 15 # len("[DD Mon HH:MM]")
            prefix_strip_len = date_placeholder_len + 2 # 15 for date/placeholder + 2 spaces

            i = 0
            while i < len(raw_history_lines):
                line = raw_history_lines[i]
                if line.startswith('+') and line[1:].isdigit():
                    try:
                        timestamp = int(line[1:])
                        dt_object = datetime.fromtimestamp(timestamp)
                        date_str = dt_object.strftime(date_format_str)
                        if i + 1 < len(raw_history_lines):
                            command = raw_history_lines[i+1]
                            processed_history_for_fzf.append(f"{date_str}  {command}")
                            i += 1 # Skip the command line as it's processed
                        else: 
                            processed_history_for_fzf.append(f"{date_str}  ")
                    except ValueError: 
                        date_placeholder = ' ' * date_placeholder_len
                        processed_history_for_fzf.append(f"{date_placeholder}  {line}")
                else:
                    date_placeholder = ' ' * date_placeholder_len
                    processed_history_for_fzf.append(f"{date_placeholder}  {line}")
                i += 1
            
            fzf_input = "\\n".join(processed_history_for_fzf)
            if not fzf_input.strip(): 
                return

            process = subprocess.run(
                fzf_cmd,
                input=fzf_input,
                capture_output=True,
                text=True,
                check=False
            )

            if process.returncode == 0 and process.stdout:
                selected_line_from_fzf = process.stdout.strip()
                if len(selected_line_from_fzf) > prefix_strip_len:
                    actual_command = selected_line_from_fzf[prefix_strip_len:]
                else: 
                    actual_command = selected_line_from_fzf 
                event.app.current_buffer.text = actual_command
                event.app.current_buffer.cursor_position = len(actual_command)
            elif process.returncode not in [0, 1, 130]:
                console.print(f"[error]fzf error (code {process.returncode}): {process.stderr.strip()}[/error]")

        except FileNotFoundError:
            console.print("[warning]fzf command not found during execution. Ctrl-R history search disabled.[/warning]")
        except Exception as e:
            console.print(f"[error]Error during fzf history search: {e}[/error]")

    prompt_message_html = HTML('<style fg="ansicyan" bold="true">Q⏵ </style>')
    
    session = PromptSession(
        history=history,
        key_bindings=kb,
    )

    user_input = await asyncio.to_thread(
        session.prompt,
        prompt_message_html,
    )
    return user_input

if __name__ == '__main__':
    async def main_test():
        console_for_test = RichConsole()
        print("Testing qprompt. Type Ctrl-R for fzf history (if fzf is installed).")
        print(f"History file will be: {Q_HISTORY_FILE}")
        Q_HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        if not Q_HISTORY_FILE.exists() or Q_HISTORY_FILE.stat().st_size == 0:
             with open(Q_HISTORY_FILE, "w", encoding="utf-8") as f:
                ts1 = int(datetime.now().timestamp()) - 3600 
                ts2 = int(datetime.now().timestamp()) - 7200 
                f.write(f"+{ts1}\\n")
                f.write("ls -la\\n")
                f.write(f"+{ts2}\\n")
                f.write('echo "hello world"\\n')
                f.write("git status # No timestamp for this one\\n") 
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