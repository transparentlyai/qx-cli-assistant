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
from qx.core.approvals import ApprovalManager # Import ApprovalManager

# Define the prompt style using the user-provided colors
prompt_style = Style.from_dict(
    {
        "": "#ff0066",  # Default text (user input)
        "prompt": "#FF4500",  # Style for the prompt marker "Q❯ " or "QA❯ "
        "prompt.multiline": "#0066CC",  # Style for multiline continuation
        "hint": "#888888",  # Style for hints (e.g., auto-suggestion)
    }
)

async def get_user_input(console: RichConsole, approval_manager: ApprovalManager) -> str: # Add approval_manager parameter
    """
    Asynchronously gets user input from the QX prompt using prompt_toolkit,
    with fzf-based history search on Ctrl-R.
    The prompt changes to 'QA❯ ' if 'approve all' mode is active.
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
                if current_command_parts:
                    original_command = "\n".join(current_command_parts)
                    fzf_display_command = original_command.replace("\n", " ↵ ")
                    formatted_ts_display = " " * 15
                    display_string = f"{formatted_ts_display}  {fzf_display_command}"
                    processed_history_entries.append((display_string, original_command))
                    current_command_parts = []
                
                current_timestamp_str = stripped_line
                idx += 1
            elif stripped_line.startswith("+"):
                command_part = stripped_line[1:]
                current_command_parts.append(command_part)
                idx += 1
                while idx < len(lines) and lines[idx].strip().startswith("+"):
                    current_command_parts.append(lines[idx].strip()[1:])
                    idx += 1
                
                original_command = "\n".join(current_command_parts)
                fzf_display_command = original_command.replace("\n", " ↵ ")

                formatted_ts_display = " " * 15
                if current_timestamp_str:
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
                
                current_command_parts = []
                current_timestamp_str = None
            else:
                if current_command_parts:
                    original_command_pending = "\n".join(current_command_parts)
                    fzf_display_command_pending = original_command_pending.replace("\n", " ↵ ")
                    ts_placeholder_pending = " " * 15
                    display_string_pending = f"{ts_placeholder_pending}  {fzf_display_command_pending}"
                    processed_history_entries.append((display_string_pending, original_command_pending))
                    current_command_parts = []
                    current_timestamp_str = None

                original_command = stripped_line
                fzf_display_command = original_command.replace("\n", " ↵ ")
                formatted_ts_display = " " * 15
                display_string = f"{formatted_ts_display}  {fzf_display_command}"
                processed_history_entries.append((display_string, original_command))
                idx += 1
                current_timestamp_str = None

        if current_command_parts:
            original_command = "\n".join(current_command_parts)
            fzf_display_command = original_command.replace("\n", " ↵ ")
            formatted_ts_display = " " * 15
            if current_timestamp_str:
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

    # Determine prompt string based on approval_manager state
    if approval_manager.is_globally_approved():
        prompt_text = "QA❯ "
    else:
        prompt_text = "Q❯ "
    
    prompt_message = [("class:prompt", prompt_text)]
    
    user_input = await asyncio.to_thread(
        session.prompt,
        prompt_message,
        key_bindings=kb 
    )
    return user_input

if __name__ == '__main__':
    async def main_test():
        console_for_test = RichConsole()
        # For testing, create an ApprovalManager instance
        # In a real app, this would be passed from the main application logic
        approval_manager_test = ApprovalManager(console=console_for_test)

        print("Testing qprompt. Type Ctrl-R for fzf history (if fzf is installed).")
        print("Type 'approve all' (simulated) to test QA❯ prompt, then 'reset approve' (simulated).")
        print(f"History file will be: {Q_HISTORY_FILE}")
        Q_HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        if not Q_HISTORY_FILE.exists() or Q_HISTORY_FILE.stat().st_size == 0:
             with open(Q_HISTORY_FILE, "w", encoding="utf-8") as f:
                from datetime import timedelta
                ts_now = datetime.now()
                ts1_dt = ts_now - timedelta(hours=1)
                ts2_dt = ts_now - timedelta(hours=2)
                ts3_dt = ts_now - timedelta(minutes=30)

                f.write(f"# {ts1_dt.strftime('%Y-%m-%d %H:%M:%S.%f')}\n")
                f.write("+ls -la\n\n") 
                f.write(f"# {ts2_dt.strftime('%Y-%m-%d %H:%M:%S.%f')}\n")
                f.write("+echo \"hello\nworld\"\n\n")
                f.write("git status # No specific timestamp line for this one\n\n") 
                f.write("python script.py --arg value\n")
                f.write(f"# {ts3_dt.timestamp()}\n")
                f.write("+multi line\n")
                f.write("+command example\n")
                f.write("+  with indentation\n")

        while True:
            try:
                # Pass the test approval_manager to get_user_input
                inp = await get_user_input(console_for_test, approval_manager_test)
                
                # Simulate 'approve all' and 'reset approve' for testing the prompt change
                if inp.strip().lower() == "approve all":
                    approval_manager_test._approve_all_until = datetime.now() + timedelta(minutes=15)
                    console_for_test.print("[info]Simulated 'approve all' for 15 minutes.[/info]")
                    continue
                elif inp.strip().lower() == "reset approve":
                    approval_manager_test._approve_all_until = None
                    console_for_test.print("[info]Simulated reset of 'approve all'.[/info]")
                    continue
                
                if inp.lower() == 'exit':
                    break
                console_for_test.print(f"You entered: [b]{inp}[/b]")

            except KeyboardInterrupt:
                console_for_test.print("\nExiting test (Ctrl-C).")
                break
            except EOFError:
                console_for_test.print("\nExiting test (EOF).")
                break
 
    asyncio.run(main_test())