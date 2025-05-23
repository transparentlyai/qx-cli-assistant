import asyncio
import shutil
import subprocess
import os
from datetime import datetime, timedelta
from typing import Any, List, Optional, Tuple, Iterator

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import (
    Completer,
    Completion,
    PathCompleter,
    merge_completers,
)
from prompt_toolkit.document import Document
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.styles import Style
from prompt_toolkit.shortcuts import prompt_async # Corrected import path
from pyfzf.pyfzf import FzfPrompt
from rich.console import Console as RichConsole

from qx.core.paths import Q_HISTORY_FILE
from qx.cli.commands import CommandCompleter
# Import for "Approve All" status check
from qx.core.user_prompts import is_approve_all_active 

prompt_style = Style.from_dict(
    {
        "": "#ff0066",
        "prompt": "#FF4500",
        "prompt.multiline": "#0066CC",
        "hint": "#888888",
    }
)

QX_FIXED_PROMPT_TEXT = "Q⏵ "
QX_AUTO_APPROVE_PROMPT_TEXT = "QA⏵ " # Reinstated for "Approve All" mode
QX_MULTILINE_PROMPT_TEXT = "M⏵ "
QX_MULTILINE_HINT_TEXT = "[Alt+Enter to submit] "

QX_FIXED_PROMPT_FORMATTED = FormattedText([("class:prompt", QX_FIXED_PROMPT_TEXT)])
QX_AUTO_APPROVE_PROMPT_FORMATTED = FormattedText( # Reinstated
    [("class:prompt", QX_AUTO_APPROVE_PROMPT_TEXT)]
)
QX_MULTILINE_PROMPT_FORMATTED = FormattedText(
    [
        ("class:prompt.multiline", QX_MULTILINE_PROMPT_TEXT),
        ("class:hint", QX_MULTILINE_HINT_TEXT),
        ("", "\n"),
    ]
)

class CommandArgumentPathCompleter(Completer):
    def __init__(self):
        self.path_completer = PathCompleter(expanduser=True)

    def get_completions(
        self, document: Document, complete_event
    ) -> Iterator[Completion]:
        text_before_cursor = document.text_before_cursor
        if text_before_cursor.strip() == '/':
            return []
        words = text_before_cursor.split()
        if not words:
            return []
        current_word = words[-1]
        is_first_word_and_not_command_like = (len(words) == 1 and not current_word.startswith(("/", "~", ".", "\\")))
        looks_like_path = False
        if (
            current_word.startswith("/")
            or current_word.startswith("./")
            or current_word.startswith("../")
            or current_word.startswith("~")
        ):
            looks_like_path = True
        elif (len(words) > 1 or "/" in current_word or "\\" in current_word) and not is_first_word_and_not_command_like:
            looks_like_path = True
        if looks_like_path:
            last_slash_index = current_word.rfind("/")
            if os.name == 'nt':
                last_backslash_index = current_word.rfind("\\")
                last_slash_index = max(last_slash_index, last_backslash_index)
            if last_slash_index >= 0:
                path_prefix = current_word[: last_slash_index + 1]
                base_path = path_prefix
                partial_name = current_word[last_slash_index + 1 :]
            else:
                path_prefix = ""
                base_path = "./" if len(words) == 1 else ""
                partial_name = current_word
            expanded_base_path = os.path.expanduser(base_path if base_path else ".")
            try:
                if os.path.isdir(expanded_base_path):
                    dir_contents = os.listdir(expanded_base_path)
                    if not partial_name.startswith("."):
                        dir_contents = [item for item in dir_contents if not item.startswith(".")]
                    matches = [item for item in dir_contents if item.lower().startswith(partial_name.lower())]
                    for item in matches:
                        full_item_path = os.path.join(base_path, item)
                        display_text = item
                        completion_text = path_prefix + item
                        try:
                            is_dir = os.path.isdir(os.path.expanduser(full_item_path))
                        except OSError:
                            is_dir = False
                        if is_dir:
                            display_text = f"{item}/"
                            completion_text = f"{path_prefix}{item}/"
                        start_position = -len(current_word)
                        yield Completion(
                            completion_text,
                            start_position=start_position,
                            display=display_text,
                            display_meta="dir" if is_dir else "file",
                        )
                    return
            except (PermissionError, FileNotFoundError):
                pass
            dummy_document_for_path = Document(current_word, len(current_word))
            path_completions = self.path_completer.get_completions(dummy_document_for_path, complete_event)
            for comp in path_completions:
                adjusted_start_pos = comp.start_position - len(current_word)
                final_completion_text = path_prefix + comp.text
                yield Completion(
                    final_completion_text,
                    start_position=adjusted_start_pos,
                    display=comp.display,
                    display_meta=comp.display_meta,
                    style=comp.style,
                    selected_style=comp.selected_style,
                )

async def get_user_input(
    console: RichConsole,
) -> str:
    try:
        Q_HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        console.print(
            f"[warning]Warning: Could not create history directory {Q_HISTORY_FILE.parent}: {e}[/warning]"
        )

    q_history = FileHistory(str(Q_HISTORY_FILE))
    kb = KeyBindings()
    is_multiline = [False]
    
    # Determine prompt based on "Approve All" status
    if is_approve_all_active(console): # Pass console to is_approve_all_active
        current_prompt_formatted: List[Any] = [QX_AUTO_APPROVE_PROMPT_FORMATTED]
    else:
        current_prompt_formatted: List[Any] = [QX_FIXED_PROMPT_FORMATTED]

    @kb.add("c-r")
    def _show_history_fzf_event(event):
        if not shutil.which("fzf"):
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
        if not lines: return
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
                    try: dt_obj = datetime.strptime(ts_content, "%Y-%m-%d %H:%M:%S.%f")
                    except ValueError:
                        try: dt_obj = datetime.strptime(ts_content, "%Y-%m-%d %H:%M:%S")
                        except ValueError:
                            try: dt_obj = datetime.fromtimestamp(float(ts_content))
                            except ValueError: pass
                    if dt_obj: formatted_ts_display = dt_obj.strftime("[%d %b %H:%M]")
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
                try: dt_obj = datetime.strptime(ts_content, "%Y-%m-%d %H:%M:%S.%f")
                except ValueError:
                    try: dt_obj = datetime.strptime(ts_content, "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        try: dt_obj = datetime.fromtimestamp(float(ts_content))
                        except ValueError: pass
                if dt_obj: formatted_ts_display = dt_obj.strftime("[%d %b %H:%M]")
            display_string = f"{formatted_ts_display}  {fzf_display_command}"
            processed_history_entries.append((display_string, original_command))
        if not processed_history_entries: return
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
                if original_command_to_insert:
                    event.app.current_buffer.document = Document(
                        text=original_command_to_insert,
                        cursor_position=len(original_command_to_insert),
                    )
        except Exception as e:
            console.print(f"[error]Error running fzf: {e}[/error]")
            console.print("[info]Ensure 'fzf' executable is installed and in your PATH.[/info]")

    @kb.add("c-m")
    def _handle_enter(event):
        if is_multiline[0]:
            event.app.current_buffer.insert_text("\n")
        else:
            event.app.current_buffer.validate_and_handle()

    @kb.add("escape", "c-m")
    def _handle_alt_enter(event):
        if is_multiline[0]:
            is_multiline[0] = False
            # Update prompt based on "Approve All" status when exiting multiline
            if is_approve_all_active(console):
                current_prompt_formatted[0] = QX_AUTO_APPROVE_PROMPT_FORMATTED
            else:
                current_prompt_formatted[0] = QX_FIXED_PROMPT_FORMATTED
            event.app.current_buffer.validate_and_handle()
        else:
            is_multiline[0] = True
            current_prompt_formatted[0] = QX_MULTILINE_PROMPT_FORMATTED
            event.app.current_buffer.insert_text("\n")

    @kb.add("c-c")
    def _handle_ctrl_c(event):
        event.app.exit(exception=KeyboardInterrupt())

    # Set initial prompt state (already done above, but this ensures it if logic changes)
    is_multiline[0] = False 
    if is_approve_all_active(console):
        current_prompt_formatted[0] = QX_AUTO_APPROVE_PROMPT_FORMATTED
    else:
        current_prompt_formatted[0] = QX_FIXED_PROMPT_FORMATTED

    qx_command_completer = CommandCompleter()
    path_argument_completer = CommandArgumentPathCompleter()
    merged_completer = merge_completers([qx_command_completer, path_argument_completer])

    session = PromptSession(
        history=q_history, 
        style=prompt_style,
        completer=merged_completer, 
        complete_while_typing=True,
        key_bindings=kb
    )

    try:
        # The lambda for prompt needs to be re-evaluated each time to pick up changes
        # to current_prompt_formatted[0] if "Approve All" status changes between prompts.
        # This is implicitly handled if current_prompt_formatted is a list and its content is changed.
        # However, to be absolutely sure the LATEST state of is_approve_all_active is used:
        def get_current_prompt():
            if is_multiline[0]:
                return QX_MULTILINE_PROMPT_FORMATTED
            elif is_approve_all_active(console):
                return QX_AUTO_APPROVE_PROMPT_FORMATTED
            else:
                return QX_FIXED_PROMPT_FORMATTED

        user_input = await session.prompt_async(
            get_current_prompt, # Use a function to dynamically get the prompt
        )
        return user_input
    except KeyboardInterrupt:
        console.print("\n[#666666]Prompt aborted. Use 'exit' or 'quit' to exit QX.[/]")
        return ""
    except EOFError:
        return "exit"


if __name__ == "__main__":
    from qx.core.user_prompts import _approve_all_until # For testing __main__

    async def main_test():
        console_for_test = RichConsole()

        print("Testing qprompt. Type Ctrl-R for fzf history (if fzf is installed).")
        print("Tab for completion (commands like /help, then paths).")
        print("Press Enter to submit.")
        print(
            f"Press Alt+Enter to toggle multiline input (prompt changes to '{QX_MULTILINE_PROMPT_TEXT.strip()}' + hint)."
        )
        print("While in multiline, Enter adds a newline.")
        print("Press Alt+Enter again to submit the multiline input.")
        print(
            "Type 'activate approve all' to test QA⏵ prompt, then 'deactivate approve all'."
        )
        print(f"History file will be: {Q_HISTORY_FILE}")
        Q_HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)

        if not Q_HISTORY_FILE.exists() or Q_HISTORY_FILE.stat().st_size == 0:
            with open(Q_HISTORY_FILE, "w", encoding="utf-8") as f:
                ts_now = datetime.now()
                f.write(f"# {(ts_now - timedelta(hours=1)).strftime('%Y-%m-%d %H:%M:%S.%f')}\n+ls -la src/\n\n")
                f.write(f"# {(ts_now - timedelta(minutes=30)).strftime('%Y-%m-%d %H:%M:%S.%f')}\n+/help\n\n")
                f.write(f"# {ts_now.timestamp()}\n+echo \"Hello QX\"\n")

        while True:
            try:
                inp = await get_user_input(console_for_test) 
                if inp == "": 
                    continue
                if inp.strip().lower() == "activate approve all":
                    # Directly manipulate the state in user_prompts for testing
                    # This is a bit of a hack for testing; in real use, request_confirmation would set this.
                    from qx.core import user_prompts
                    user_prompts._approve_all_until = datetime.now() + timedelta(minutes=5)
                    console_for_test.print("[info]Simulated 'approve all' activation for 5 minutes.[/info]")
                    continue
                elif inp.strip().lower() == "deactivate approve all":
                    from qx.core import user_prompts
                    user_prompts._approve_all_until = None
                    console_for_test.print("[info]Simulated 'approve all' deactivation.[/info]")
                    continue
                if inp.lower() == "exit":
                    console_for_test.print("\nExiting test.")
                    break
                if inp:
                    console_for_test.print(f"You entered:\n---\n[b]{inp}[/b]\n---")
            except KeyboardInterrupt: 
                console_for_test.print("\nExiting test (Ctrl-C).")
                break
    asyncio.run(main_test())