import asyncio
import os
import shlex # Not used in reference for fzf part, but kept for now
import shutil
import subprocess # subprocess is not directly used by pyfzf, but good to keep if other shell ops needed
from pathlib import Path
from datetime import datetime
from typing import List, Tuple, Optional

from prompt_toolkit import PromptSession
from prompt_toolkit.document import Document # Corrected import
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.styles import Style # Import for styling

from rich.console import Console as RichConsole
from pyfzf.pyfzf import FzfPrompt # Import FzfPrompt

from qx.core.paths import Q_HISTORY_FILE

# Define the prompt style using the user-provided colors
prompt_style = Style.from_dict(
    {
        "": "#ff0066",  # Default text (user input)
        "prompt": "#FF4500",  # Style for the prompt marker "Q⏵ "
        "prompt.multiline": "#0066CC",  # Style for multiline continuation
        "hint": "#888888",  # Style for hints (e.g., auto-suggestion)
    }
)

async def get_user_input(console: RichConsole) -> str:
    """
    Asynchronously gets user input from the QX prompt using prompt_toolkit,
    with fzf-based history search on Ctrl-R, replicating reference logic.
    """
    try:
        Q_HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        console.print(f"[warning]Warning: Could not create history directory {Q_HISTORY_FILE.parent}: {e}[/warning]")

    q_history = FileHistory(str(Q_HISTORY_FILE))
    # Pass the defined style to the PromptSession
    session = PromptSession(history=q_history, style=prompt_style)
    kb = KeyBindings()

    def _parse_history_entry_for_fzf(timestamp_line: str, command_line: str) -> Optional[Tuple[str, str]]:
        """
        Parses a timestamp and command line pair from history for FZF.
        Args:
            timestamp_line: The line starting with '# '.
            command_line: The line starting with '+'.
        Returns:
            A tuple (formatted_display_string, original_command) or None if parsing fails.
        """
        if not timestamp_line.startswith("# ") or not command_line.startswith("+"):
            return None
        try:
            ts_str = timestamp_line[2:].strip()
            try:
                dt_obj = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S.%f")
            except ValueError:
                dt_obj = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
            
            formatted_ts = dt_obj.strftime("[%d %b %H:%M]") # e.g., [15 May 18:08]
            original_command = command_line[1:].strip()
            display_string = f"{formatted_ts}  {original_command}" # Two spaces after date
            return display_string, original_command
        except (ValueError, IndexError):
            return None

    @kb.add('c-r')
    def _show_history_fzf_event(event):
        """Handle Ctrl+R: Show command history using FZF with formatted entries."""
        if not shutil.which('fzf'):
            console.print("[warning]fzf not found. Ctrl-R history search disabled.[/warning]")
            return

        history_data_for_fzf: List[Tuple[str, str]] = [] # List of (display_string, original_command)
        
        if not Q_HISTORY_FILE.exists() or Q_HISTORY_FILE.stat().st_size == 0:
            return
            
        try:
            with open(Q_HISTORY_FILE, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except IOError as e:
            console.print(f"[error]Error reading history file: {e}[/error]")
            return

        if not lines:
            return

        timestamp_line_buffer: Optional[str] = None
        for line_with_nl in lines:
            stripped_line = line_with_nl.strip()
            if not stripped_line: 
                continue
            if stripped_line.startswith("# "):
                timestamp_line_buffer = stripped_line
            elif stripped_line.startswith("+") and timestamp_line_buffer is not None:
                parsed_entry = _parse_history_entry_for_fzf(timestamp_line_buffer, stripped_line)
                if parsed_entry:
                    history_data_for_fzf.append(parsed_entry)
                timestamp_line_buffer = None 
            else: 
                if not stripped_line.startswith("# "): 
                    date_placeholder = ' ' * 15 
                    display_string = f"{date_placeholder}  {stripped_line}"
                    history_data_for_fzf.append((display_string, stripped_line))
                timestamp_line_buffer = None 

        if not history_data_for_fzf:
            return

        history_data_for_fzf.reverse() 

        display_options = [item[0] for item in history_data_for_fzf]
        
        fzf = FzfPrompt()
        try:
            selected_display_list = fzf.prompt(
                display_options, # Corrected: display_options is the first positional argument
                fzf_options="--height 40% --header='[QX History Search]' --prompt='Search> ' --select-1 --exit-0 --no-sort"
            )

            if selected_display_list:
                selected_display = selected_display_list[0]
                original_command_to_insert = ""
                for disp_str, orig_cmd in history_data_for_fzf:
                    if disp_str == selected_display:
                        original_command_to_insert = orig_cmd
                        break
                
                if original_command_to_insert:
                    event.app.current_buffer.document = Document( 
                        text=original_command_to_insert, cursor_position=len(original_command_to_insert)
                    )
        except Exception as e: 
            console.print(f"[error]Error running fzf: {e}[/error]")
            console.print("[info]Ensure 'fzf' executable is installed and in your PATH.[/info]")

    # Use a list of (style_class, text) tuples for the prompt message
    # This allows "class:prompt" to be styled by `prompt_style`
    prompt_message = [("class:prompt", "Q⏵ ")]
    
    user_input = await asyncio.to_thread(
        session.prompt,
        prompt_message, # Pass the new prompt_message
        key_bindings=kb 
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
                ts_now = datetime.now()
                # Import timedelta here as it's only used in test
                from datetime import timedelta 
                ts1_dt = ts_now - timedelta(hours=1)
                ts2_dt = ts_now - timedelta(hours=2)
                
                f.write(f"# {ts1_dt.strftime('%Y-%m-%d %H:%M:%S.%f')}\\n")
                f.write("+ls -la\\n\\n") 
                f.write(f"# {ts2_dt.strftime('%Y-%m-%d %H:%M:%S.%f')}\\n")
                f.write('+echo "hello world"\\n\\n')
                f.write("git status # No timestamp for this one\\n\\n") 
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