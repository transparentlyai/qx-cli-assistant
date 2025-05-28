import asyncio
import shutil
import subprocess
import os
from datetime import datetime, timedelta
from typing import Any, List, Optional, Tuple, Iterator, Callable
from pathlib import Path

from pyfzf.pyfzf import FzfPrompt

from qx.core.paths import QX_HISTORY_FILE
from qx.core.user_prompts import is_approve_all_active 

class TextualPromptInput:
    """
    Textual-based prompt input handler.
    This replaces the prompt_toolkit functionality.
    """
    
    def __init__(self, console, mcp_manager):
        self.console = console
        self.mcp_manager = mcp_manager
        self._input_future: Optional[asyncio.Future] = None
        
    def set_input_future(self, future: asyncio.Future):
        """Set the future that will be resolved when input is received."""
        self._input_future = future
        
    def handle_input(self, input_text: str):
        """Handle input received from the Textual app."""
        if self._input_future and not self._input_future.done():
            self._input_future.set_result(input_text)
            
    async def get_input(self) -> str:
        """Get input asynchronously."""
        if self._input_future:
            return await self._input_future
        return ""


async def get_user_input(
    console: Any, mcp_manager: Any
) -> str:
    """
    Get user input through the Textual interface.
    This function now works with the Textual app to get input.
    """
    try:
        QX_HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        console.print(
            f"[warning]Warning: Could not create history directory {QX_HISTORY_FILE.parent}: {e}[/warning]"
        )

    # Create a prompt input handler
    prompt_handler = TextualPromptInput(console, mcp_manager)
    
    # Create a future for the input
    input_future = asyncio.Future()
    prompt_handler.set_input_future(input_future)
    
    # Store the handler in the console for the app to use
    if hasattr(console, '_app') and console._app:
        console._app.prompt_handler = prompt_handler
    
    try:
        # Wait for input from the Textual app
        user_input = await input_future
        return user_input
    except KeyboardInterrupt:
        console.print("\n[#666666]Prompt aborted. Use 'exit' or 'quit' to exit QX.[/]")
        return ""
    except Exception as e:
        console.print(f"[red]Error getting input: {e}[/red]")
        return ""


def handle_history_search(console, history_file_path: Path) -> Optional[str]:
    """
    Handle history search using fzf.
    Returns the selected command or None if cancelled.
    """
    if not shutil.which("fzf"):
        console.print("[warning]fzf not found. History search disabled.[/warning]")
        return None
        
    if not history_file_path.exists() or history_file_path.stat().st_size == 0:
        return None
        
    try:
        with open(history_file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except IOError as e:
        console.print(f"[red]Error reading history file: {e}[/red]")
        return None
        
    if not lines:
        return None
        
    processed_history_entries: List[Tuple[str, str]] = []
    current_command_parts: List[str] = []
    current_timestamp_str: Optional[str] = None
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
                try: 
                    dt_obj = datetime.strptime(ts_content, "%Y-%m-%d %H:%M:%S.%f")
                except ValueError:
                    try: 
                        dt_obj = datetime.strptime(ts_content, "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        try: 
                            dt_obj = datetime.fromtimestamp(float(ts_content))
                        except ValueError: 
                            pass
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
            try: 
                dt_obj = datetime.strptime(ts_content, "%Y-%m-%d %H:%M:%S.%f")
            except ValueError:
                try: 
                    dt_obj = datetime.strptime(ts_content, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    try: 
                        dt_obj = datetime.fromtimestamp(float(ts_content))
                    except ValueError: 
                        pass
            if dt_obj: 
                formatted_ts_display = dt_obj.strftime("[%d %b %H:%M]")
        display_string = f"{formatted_ts_display}  {fzf_display_command}"
        processed_history_entries.append((display_string, original_command))
        
    if not processed_history_entries:
        return None
        
    processed_history_entries.reverse()
    history_data_for_fzf = processed_history_entries
    display_options = [item[0] for item in history_data_for_fzf]
    fzf = FzfPrompt()
    
    try:
        selected_display_list = fzf.prompt(
            display_options,
            fzf_options="--height 40% --header='[QX History Search]' --prompt='Search> ' --select-1 --exit-0 --no-sort",
        )
        if selected_display_list:
            selected_display_entry = selected_display_list[0]
            original_command_to_insert = ""
            for disp_str, orig_cmd in history_data_for_fzf:
                if disp_str == selected_display_entry:
                    original_command_to_insert = orig_cmd
                    break
            return original_command_to_insert
    except Exception as e:
        console.print(f"[red]Error running fzf: {e}[/red]")
        console.print("[info]Ensure 'fzf' executable is installed and in your PATH.[/info]")
        
    return None


if __name__ == "__main__":
    from qx.core.user_prompts import _approve_all_until
    from qx.core.mcp_manager import MCPManager

    async def main_test():
        from qx.cli.console import qx_console
        mcp_manager_for_test = MCPManager(qx_console)
        mcp_manager_for_test.load_mcp_configs()

        print("Testing qprompt with Textual interface.")
        print("Type 'exit' to quit.")
        
        QX_HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)

        if not QX_HISTORY_FILE.exists() or QX_HISTORY_FILE.stat().st_size == 0:
            with open(QX_HISTORY_FILE, "w", encoding="utf-8") as f:
                ts_now = datetime.now()
                f.write(f"# {(ts_now - timedelta(hours=1)).strftime('%Y-%m-%d %H:%M:%S.%f')}\n+ls -la src/\n\n")
                f.write(f"# {(ts_now - timedelta(minutes=30)).strftime('%Y-%m-%d %H:%M:%S.%f')}\n+/help\n\n")
                f.write(f"# {ts_now.timestamp()}\n+echo \"Hello QX\"\n")

        while True:
            try:
                inp = await get_user_input(qx_console, mcp_manager_for_test) 
                if inp == "": 
                    continue
                if inp.lower() == "exit":
                    print("\nExiting test.")
                    break
                if inp:
                    print(f"You entered:\n---\n{inp}\n---")
            except KeyboardInterrupt: 
                print("\nExiting test (Ctrl-C).")
                break
                
    asyncio.run(main_test())