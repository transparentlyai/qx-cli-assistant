import asyncio
import os
import shutil
import subprocess # subprocess is not directly used by pyfzf, but good to keep if other shell ops needed
from pathlib import Path
from datetime import datetime
from typing import List, Tuple, Optional

from prompt_toolkit import PromptSession
from prompt_toolkit.document import Document
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.styles import Style

from rich.console import Console as RichConsole
from pyfzf.pyfzf import FzfPrompt

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
    with fzf-based history search on Ctrl-R.
    """
    try:
        Q_HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        console.print(f"[warning]Warning: Could not create history directory {Q_HISTORY_FILE.parent}: {e}[/warning]")

    q_history = FileHistory(str(Q_HISTORY_FILE))
    session = PromptSession(history=q_history, style=prompt_style)
    kb = KeyBindings()

    @kb.add('c-r')
    def _show_history_fzf_event(event):
        """Handle Ctrl+R: Show command history using FZF with formatted entries."""
        if not shutil.which('fzf'):
            console.print("[warning]fzf not found. Ctrl-R history search disabled.[/warning]")
            return

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

        processed_history_entries: List[Tuple[str, str]] = []  # (display_string, original_command)
        current_command_parts: List[str] = []
        current_timestamp_str: Optional[str] = None # Stores the raw timestamp line content (e.g., "# 1629390000.123456")

        idx = 0
        while idx < len(lines):
            line_with_nl = lines[idx]
            stripped_line = line_with_nl.strip()

            if not stripped_line:
                idx += 1
                continue

            if stripped_line.startswith("# "):
                # If there were pending command parts (e.g., non-timestamped command or '+' lines without prior '#'), process them.
                if current_command_parts:
                    original_command = "\n".join(current_command_parts)
                    fzf_display_command = original_command.replace("\n", " ↵ ")
                    # Use placeholder for timestamp as this command block didn't have one immediately preceding it
                    formatted_ts_display = " " * 15  # Matches "[DD Mon HH:MM]" length
                    display_string = f"{formatted_ts_display}  {fzf_display_command}"
                    processed_history_entries.append((display_string, original_command))
                    current_command_parts = []
                
                current_timestamp_str = stripped_line # Store this timestamp for the *next* command block
                idx += 1
            elif stripped_line.startswith("+"):
                command_part = stripped_line[1:]  # Remove '+'
                current_command_parts.append(command_part)
                idx += 1
                # Greedily consume all subsequent '+' lines for the current command
                while idx < len(lines) and lines[idx].strip().startswith("+"):
                    current_command_parts.append(lines[idx].strip()[1:])
                    idx += 1
                
                # Finalize the command accumulated
                original_command = "\n".join(current_command_parts)
                fzf_display_command = original_command.replace("\n", " ↵ ")

                formatted_ts_display = " " * 15  # Placeholder for "[DD Mon HH:MM]"
                if current_timestamp_str:
                    ts_content = current_timestamp_str[2:].strip() # Remove "# "
                    dt_obj = None
                    try: # Try our strftime format (YYYY-MM-DD HH:MM:SS.ffffff)
                        dt_obj = datetime.strptime(ts_content, "%Y-%m-%d %H:%M:%S.%f")
                    except ValueError:
                        try: # Try strftime format without microseconds
                            dt_obj = datetime.strptime(ts_content, "%Y-%m-%d %H:%M:%S")
                        except ValueError:
                            try: # Try prompt_toolkit's float timestamp
                                dt_obj = datetime.fromtimestamp(float(ts_content))
                            except ValueError:
                                pass # dt_obj remains None
                    if dt_obj:
                        formatted_ts_display = dt_obj.strftime("[%d %b %H:%M]")
                
                display_string = f"{formatted_ts_display}  {fzf_display_command}"
                processed_history_entries.append((display_string, original_command))
                
                current_command_parts = []
                current_timestamp_str = None # Timestamp has been used/associated
            else: # Line is not a timestamp and not a command part (e.g. manually edited history, or old format)
                # Finalize any pending '+' parts first, treating them as a command without a timestamp
                if current_command_parts:
                    original_command_pending = "\n".join(current_command_parts)
                    fzf_display_command_pending = original_command_pending.replace("\n", " ↵ ")
                    ts_placeholder_pending = " " * 15
                    display_string_pending = f"{ts_placeholder_pending}  {fzf_display_command_pending}"
                    processed_history_entries.append((display_string_pending, original_command_pending))
                    current_command_parts = []
                    current_timestamp_str = None # Ensure no previous timestamp carries over

                # Process the current line as a standalone command
                original_command = stripped_line
                fzf_display_command = original_command.replace("\n", " ↵ ") # Handle if it has newlines
                formatted_ts_display = " " * 15  # Placeholder for timestamp
                display_string = f"{formatted_ts_display}  {fzf_display_command}"
                processed_history_entries.append((display_string, original_command))
                idx += 1
                current_timestamp_str = None # Ensure no previous timestamp carries over

        # If file ends with '+' lines, process them
        if current_command_parts:
            original_command = "\n".join(current_command_parts)
            fzf_display_command = original_command.replace("\n", " ↵ ")
            formatted_ts_display = " " * 15 # Placeholder
            if current_timestamp_str: # This case implies '+' lines followed EOF, with a preceding timestamp
                ts_content = current_timestamp_str[2:].strip()
                dt_obj = None
                try: dt_obj = datetime.strptime(ts_content, "%Y-%m-%d %H:%M:%S.%f")
                except ValueError:
                    try: dt_obj = datetime.strptime(ts_content, "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        try: dt_obj = datetime.fromtimestamp(float(ts_content))
                        except ValueError: pass
                if dt_obj:
                    formatted_ts_display = dt_obj.strftime("[%d %b %H:%M]")
            
            display_string = f"{formatted_ts_display}  {fzf_display_command}"
            processed_history_entries.append((display_string, original_command))

        if not processed_history_entries:
            return

        # History file is typically oldest to newest. Reverse to show newest first in fzf.
        processed_history_entries.reverse()
        
        history_data_for_fzf = processed_history_entries
        display_options = [item[0] for item in history_data_for_fzf]
        
        fzf = FzfPrompt()
        try:
            selected_display_list = fzf.prompt(
                display_options,
                fzf_options="--height 40% --header='[QX History Search]' --prompt='Search> ' --select-1 --exit-0 --no-sort"
            )

            if selected_display_list:
                selected_display_entry = selected_display_list[0]
                # Find the original command corresponding to the selected display string
                original_command_to_insert = ""
                for disp_str, orig_cmd in history_data_for_fzf:
                    if disp_str == selected_display_entry:
                        original_command_to_insert = orig_cmd
                        break
                
                if original_command_to_insert:
                    event.app.current_buffer.document = Document(
                        text=original_command_to_insert, cursor_position=len(original_command_to_insert)
                    )
        except Exception as e: 
            console.print(f"[error]Error running fzf: {e}[/error]")
            console.print("[info]Ensure 'fzf' executable is installed and in your PATH.[/info]")

    prompt_message = [("class:prompt", "Q⏵ ")]
    
    user_input = await asyncio.to_thread(
        session.prompt,
        prompt_message,
        key_bindings=kb 
    )
    return user_input

if __name__ == '__main__':
    async def main_test():
        console_for_test = RichConsole()
        print("Testing qprompt. Type Ctrl-R for fzf history (if fzf is installed).")
        print(f"History file will be: {Q_HISTORY_FILE}")
        Q_HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        # Sample history for testing
        if not Q_HISTORY_FILE.exists() or Q_HISTORY_FILE.stat().st_size == 0:
             with open(Q_HISTORY_FILE, "w", encoding="utf-8") as f:
                from datetime import timedelta # Import timedelta here as it's only used in test
                ts_now = datetime.now()
                ts1_dt = ts_now - timedelta(hours=1)
                ts2_dt = ts_now - timedelta(hours=2)
                ts3_dt = ts_now - timedelta(minutes=30)

                # Entry 1: Simple command with timestamp
                f.write(f"# {ts1_dt.strftime('%Y-%m-%d %H:%M:%S.%f')}\n")
                f.write("+ls -la\n\n") 
                
                # Entry 2: Multiline command with timestamp
                f.write(f"# {ts2_dt.strftime('%Y-%m-%d %H:%M:%S.%f')}\n")
                f.write("+echo \"hello\nworld\"\n\n") # Command with actual newline

                # Entry 3: Command without timestamp (prompt-toolkit might add one later)
                f.write("git status # No specific timestamp line for this one\n\n") 
                
                # Entry 4: Another command, also no explicit timestamp line
                f.write("python script.py --arg value\n")

                # Entry 5: Multiline command using prompt-toolkit's float timestamp
                # (Simulating how prompt-toolkit might save it)
                f.write(f"# {ts3_dt.timestamp()}\n")
                f.write("+multi line\n")
                f.write("+command example\n")
                f.write("+  with indentation\n")

        while True:
            try:
                inp = await get_user_input(console_for_test)
                if inp.lower() == 'exit':
                    break
                console_for_test.print(f"You entered: [b]{inp}[/b]")
                if inp.strip(): # Add to history if not empty
                    # prompt_toolkit session handles writing to history automatically
                    pass
            except KeyboardInterrupt:
                console_for_test.print("\nExiting test (Ctrl-C).")
                break
            except EOFError:
                console_for_test.print("\nExiting test (EOF).")
                break
 
    asyncio.run(main_test())