import asyncio
import shutil
import subprocess  # subprocess is not directly used by pyfzf, but good to keep if other shell ops needed
from datetime import datetime, timedelta
from typing import Any, List, Optional, Tuple

from prompt_toolkit import PromptSession
from prompt_toolkit.document import Document
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.styles import Style
from pyfzf.pyfzf import FzfPrompt
from rich.console import Console as RichConsole

from qx.core.approvals import ApprovalManager  # Import ApprovalManager
from qx.core.paths import Q_HISTORY_FILE

# Define the prompt style using the user-provided colors
prompt_style = Style.from_dict(
    {
        "": "#ff0066",  # Default text (user input)
        "prompt": "#FF4500",  # Style for the prompt marker "Q⏵ " or "QA⏵ "
        "prompt.multiline": "#0066CC",  # Style for multiline continuation
        "hint": "#888888",  # Style for hints (e.g., auto-suggestion, multiline hint)
    }
)

# Define the fixed prompt strings and formats
QX_FIXED_PROMPT_TEXT = "Q⏵ "
QX_AUTO_APPROVE_PROMPT_TEXT = "QA⏵ "
QX_MULTILINE_PROMPT_TEXT = "M⏵ "
QX_MULTILINE_HINT_TEXT = "[Alt+Enter to submit] "

QX_FIXED_PROMPT_FORMATTED = FormattedText([("class:prompt", QX_FIXED_PROMPT_TEXT)])
QX_AUTO_APPROVE_PROMPT_FORMATTED = FormattedText(
    [("class:prompt", QX_AUTO_APPROVE_PROMPT_TEXT)]
)
QX_MULTILINE_PROMPT_FORMATTED = FormattedText(
    [
        ("class:prompt.multiline", QX_MULTILINE_PROMPT_TEXT),
        ("class:hint", QX_MULTILINE_HINT_TEXT),
        ("", "\n"),  # Newline after hint for user input
    ]
)


async def get_user_input(
    console: RichConsole, approval_manager: ApprovalManager
) -> str:
    """
    Asynchronously gets user input from the QX prompt using prompt_toolkit,
    with fzf-based history search on Ctrl-R and multiline input support.
    - Enter: Submits the current line (unless in multiline mode).
    - Alt+Enter: Toggles multiline mode. Submits when toggled off.
    - Ctrl+R: Triggers FZF fuzzy history search.
    - Ctrl+C: Exits the prompt.
    The prompt changes to 'QA⏵ ' if 'approve all' mode is active.
    The multiline prompt is 'M⏵ ' with a hint.
    """
    try:
        Q_HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        console.print(
            f"[warning]Warning: Could not create history directory {Q_HISTORY_FILE.parent}: {e}[/warning]"
        )

    q_history = FileHistory(str(Q_HISTORY_FILE))
    session = PromptSession(history=q_history, style=prompt_style)
    kb = KeyBindings()

    is_multiline = [False]  # Use a list to allow modification in closures

    # current_prompt_formatted holds the FormattedText object for the prompt
    current_prompt_formatted: List[Any] = [
        QX_AUTO_APPROVE_PROMPT_FORMATTED
        if approval_manager.is_globally_approved()
        else QX_FIXED_PROMPT_FORMATTED
    ]

    @kb.add("c-r")
    def _show_history_fzf_event(event):
        """Handle Ctrl+R: Show command history using FZF with formatted entries."""
        if not shutil.which("fzf"):
            console.print(
                "[warning]fzf not found. Ctrl-R history search disabled.[/warning]"
            )
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

        processed_history_entries: List[
            Tuple[str, str]
        ] = []  # (display_string, original_command)
        current_command_parts: List[str] = []
        current_timestamp_str: Optional[str] = (
            None  # Stores the raw timestamp line content (e.g., "# 1629390000.123456")
        )

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
            else:  # Treat as a single line command without timestamp or '+'
                if (
                    current_command_parts
                ):  # Should not happen if format is strict, but handle defensively
                    original_command_pending = "\n".join(current_command_parts)
                    fzf_display_command_pending = original_command_pending.replace(
                        "\n", " ↵ "
                    )
                    ts_placeholder_pending = " " * 15  # Placeholder as no timestamp
                    display_string_pending = (
                        f"{ts_placeholder_pending}  {fzf_display_command_pending}"
                    )
                    processed_history_entries.append(
                        (display_string_pending, original_command_pending)
                    )
                    current_command_parts = []  # Reset

                original_command = stripped_line  # The line itself is the command
                fzf_display_command = original_command.replace("\n", " ↵ ")
                formatted_ts_display = " " * 15  # Placeholder as no timestamp
                display_string = f"{formatted_ts_display}  {fzf_display_command}"
                processed_history_entries.append((display_string, original_command))
                idx += 1
                current_timestamp_str = None  # Reset timestamp

        if current_command_parts:  # Process any remaining command parts at EOF
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
            return

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
            console.print(
                "[info]Ensure 'fzf' executable is installed and in your PATH.[/info]"
            )

    @kb.add("c-m")  # Enter
    def _handle_enter(event):
        if is_multiline[0]:
            event.app.current_buffer.insert_text("\n")
        else:
            event.app.current_buffer.validate_and_handle()

    @kb.add("escape", "c-m")  # Alt+Enter
    def _handle_alt_enter(event):
        if is_multiline[0]:
            is_multiline[0] = False
            if approval_manager.is_globally_approved():
                current_prompt_formatted[0] = QX_AUTO_APPROVE_PROMPT_FORMATTED
            else:
                current_prompt_formatted[0] = QX_FIXED_PROMPT_FORMATTED
            event.app.current_buffer.validate_and_handle()  # Submit
        else:
            is_multiline[0] = True
            current_prompt_formatted[0] = QX_MULTILINE_PROMPT_FORMATTED
            # Optionally, insert a newline to start multiline input on a new line in the buffer
            # This matches the reference behavior.
            event.app.current_buffer.insert_text("\n")

    @kb.add("c-c")
    def _handle_ctrl_c(event):
        event.app.exit(exception=KeyboardInterrupt())

    # Reset multiline state for this specific prompt call
    is_multiline[0] = False
    # Set initial prompt based on approval status
    if approval_manager.is_globally_approved():
        current_prompt_formatted[0] = QX_AUTO_APPROVE_PROMPT_FORMATTED
    else:
        current_prompt_formatted[0] = QX_FIXED_PROMPT_FORMATTED

    try:
        user_input = await asyncio.to_thread(
            session.prompt,
            lambda: current_prompt_formatted[0],  # Use lambda for dynamic prompt
            key_bindings=kb,
        )
        return user_input
    except KeyboardInterrupt:
        # This message is now more of a fallback, as Ctrl+C should exit cleanly.
        # However, it's good to keep for other potential KeyboardInterrupt sources.
        console.print("\n[#666666]Prompt aborted. Use 'exit' or 'quit' to exit QX.[/]")
        return ""  # Return empty string to signify aborted input
    except EOFError:  # Ctrl+D
        return "exit"  # Signal to exit the application


if __name__ == "__main__":

    async def main_test():
        console_for_test = RichConsole()
        approval_manager_test = ApprovalManager(console=console_for_test)

        print("Testing qprompt. Type Ctrl-R for fzf history (if fzf is installed).")
        print("Press Enter to submit.")
        print(
            f"Press Alt+Enter to toggle multiline input (prompt changes to '{QX_MULTILINE_PROMPT_TEXT.strip()}' + hint)."
        )
        print("While in multiline, Enter adds a newline.")
        print("Press Alt+Enter again to submit the multiline input.")
        print(
            "Type 'approve all' (simulated) to test QA❯ prompt, then 'reset approve' (simulated)."
        )
        print(f"History file will be: {Q_HISTORY_FILE}")
        Q_HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)

        if not Q_HISTORY_FILE.exists() or Q_HISTORY_FILE.stat().st_size == 0:
            with open(Q_HISTORY_FILE, "w", encoding="utf-8") as f:
                ts_now = datetime.now()
                ts1_dt = ts_now - timedelta(hours=1)
                ts2_dt = ts_now - timedelta(hours=2)
                ts3_dt = ts_now - timedelta(minutes=30)

                f.write(f"# {ts1_dt.strftime('%Y-%m-%d %H:%M:%S.%f')}\n")
                f.write("+ls -la\n\n")
                f.write(f"# {ts2_dt.strftime('%Y-%m-%d %H:%M:%S.%f')}\n")
                f.write(
                    '+echo "hello\nworld"\n\n'
                )  # Example of multiline command in history
                f.write("git status # No specific timestamp line for this one\n\n")
                f.write("python script.py --arg value\n")
                f.write(f"# {ts3_dt.timestamp()}\n")  # Example of float timestamp
                f.write("+multi line\n")
                f.write("+command example\n")
                f.write("+  with indentation\n")

        while True:
            try:
                inp = await get_user_input(console_for_test, approval_manager_test)

                if (
                    inp == "" and not is_multiline[0]
                ):  # Check if input was aborted by Ctrl+C
                    # The KeyboardInterrupt handler in get_user_input now returns ""
                    # We might want to decide if this should also break the loop or just ask for new input.
                    # For now, let's assume it means "clear current input line and retry".
                    # If "exit" is returned (from Ctrl+D), the loop will break.
                    continue

                if inp.strip().lower() == "approve all":
                    approval_manager_test._approve_all_until = (
                        datetime.now() + timedelta(minutes=15)
                    )
                    console_for_test.print(
                        "[info]Simulated 'approve all' for 15 minutes.[/info]"
                    )
                    continue
                elif inp.strip().lower() == "reset approve":
                    approval_manager_test._approve_all_until = None
                    console_for_test.print(
                        "[info]Simulated reset of 'approve all'.[/info]"
                    )
                    continue

                if inp.lower() == "exit":  # Handles Ctrl+D or typed "exit"
                    console_for_test.print("\nExiting test.")
                    break

                if inp:  # Only print if there's actual input
                    console_for_test.print(f"You entered:\n---\n[b]{inp}[/b]\n---")

            except KeyboardInterrupt:  # This catches Ctrl+C if it happens outside get_user_input, or if get_user_input re-raises it.
                console_for_test.print("\nExiting test (Ctrl-C).")
                break
            # EOFError should be handled by get_user_input returning "exit"

    asyncio.run(main_test())
