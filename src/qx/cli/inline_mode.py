import asyncio
import logging
import subprocess
from typing import Any, List, Optional

from openai.types.chat import ChatCompletionMessageParam
from prompt_toolkit import PromptSession
from prompt_toolkit.application import run_in_terminal
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.filters import Condition
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.shortcuts.prompt import CompleteStyle
from prompt_toolkit.styles import Style
from prompt_toolkit.validation import ValidationError, Validator
from rich.markdown import Markdown

from qx.cli.commands import _handle_inline_command
from qx.cli.completer import QXCompleter
from qx.cli.history import QXHistory
from qx.cli.theme import themed_console
from qx.core.config_manager import ConfigManager
from qx.core.history_utils import parse_history_for_fzf
from qx.core.llm import QXLLMAgent, query_llm
from qx.core.paths import QX_HISTORY_FILE
from qx.core.session_manager import clean_old_sessions, save_session
from qx.core.user_prompts import _approve_all_lock, _show_thinking_lock

logger = logging.getLogger("qx")

is_multiline_mode = [False]
pending_text = [""]


class SingleLineNonEmptyValidator(Validator):
    def validate(self, document):
        if not is_multiline_mode[0]:
            text = document.text.strip()
            if not text:
                raise ValidationError(message="")


def get_bottom_toolbar():
    import qx.core.user_prompts as user_prompts

    approve_all_status = (
        '<style fg="lime">ON</style>'
        if user_prompts._approve_all_active
        else '<style fg="red">OFF</style>'
    )
    thinking_status = (
        '<style fg="lime">ON</style>'
        if user_prompts._show_thinking_active
        else '<style fg="red">OFF</style>'
    )

    toolbar_html = (
        f"Show Thinking: {thinking_status} | Approve All: {approve_all_status}"
    )
    return HTML(toolbar_html)


async def _handle_llm_interaction(
    agent: QXLLMAgent,
    user_input: str,
    current_message_history: Optional[List[ChatCompletionMessageParam]],
    code_theme_to_use: str,
    plain_text_output: bool = False,
) -> Optional[List[ChatCompletionMessageParam]]:
    run_result: Optional[Any] = None
    try:
        run_result = await query_llm(
            agent,
            user_input,
            message_history=current_message_history,
            console=themed_console,
        )
    except asyncio.CancelledError:
        logger.info("LLM interaction cancelled by user")
        themed_console.print("\nOperation cancelled", style="warning")
        return current_message_history
    except Exception as e:
        logger.error(f"Error during LLM interaction: {e}", exc_info=True)
        themed_console.print(f"Error: {e}", style="error")
        return current_message_history

    if run_result and hasattr(run_result, "output"):
        output_content = str(run_result.output) if run_result.output is not None else ""
        if plain_text_output:
            print(output_content)
        elif not agent.enable_streaming and output_content.strip():
            themed_console.print()
            themed_console.print(
                Markdown(output_content, code_theme="rrt"), markup=True
            )
            themed_console.print()
        return (
            run_result.all_messages()
            if hasattr(run_result, "all_messages")
            else current_message_history
        )
    return current_message_history


async def _run_inline_mode(
    llm_agent: QXLLMAgent,
    current_message_history: Optional[List[ChatCompletionMessageParam]],
    keep_sessions: int,
):
    qx_history = QXHistory(QX_HISTORY_FILE)
    qx_completer = QXCompleter()
    config_manager = ConfigManager(themed_console, None)

    input_style = Style.from_dict(
        {
            "": "fg:#ff005f",
            "selected": "fg:#ff005f bg:#050505 reverse",
            "bottom-toolbar": "bg:#222222 fg:#888888",
            "bottom-toolbar.text": "bg:#222222 fg:#cccccc",
            "bottom-toolbar.key": "bg:#222222 fg:#ff5f00 bold",
        }
    )

    bindings = KeyBindings()

    @bindings.add("c-c")
    def _(event):
        if task := asyncio.current_task():
            task.cancel()
        event.current_buffer.reset()
        event.app.exit(exception=KeyboardInterrupt, style="class:aborting")

    @bindings.add("c-d")
    def _(event):
        event.app.exit(exception=EOFError, style="class:exiting")

    @bindings.add("c-r")
    def _(event):
        try:
            history_entries = parse_history_for_fzf(QX_HISTORY_FILE)
            if not history_entries:
                return

            fzf_input = "\n".join([display for display, _ in reversed(history_entries)])
            fzf_process = subprocess.run(
                ["fzf", "--ansi", "--reverse", "--height", "40%", "--no-clear"],
                input=fzf_input,
                capture_output=True,
                text=True,
            )

            event.app.invalidate()
            event.app.renderer.reset()

            if fzf_process.returncode == 0 and fzf_process.stdout.strip():
                selected_display = fzf_process.stdout.strip()
                for display, original in history_entries:
                    if display == selected_display:
                        event.current_buffer.text = original
                        event.current_buffer.cursor_position = len(original)
                        break
        except Exception:
            if event.app:
                event.app.invalidate()
                event.app.renderer.reset()

    @bindings.add("escape", "enter")
    def _(event):
        if is_multiline_mode[0]:
            event.current_buffer.validate_and_handle()
        else:
            is_multiline_mode[0] = True
            current_text = event.current_buffer.text
            if current_text.strip():
                current_text += "\n"
            pending_text[0] = current_text
            event.app.exit(result="__TOGGLE_MULTILINE__")

    @bindings.add("c-a")
    async def _(event):
        import qx.core.user_prompts as user_prompts

        async with _approve_all_lock:
            user_prompts._approve_all_active = not user_prompts._approve_all_active
            status = "activated" if user_prompts._approve_all_active else "deactivated"
            style = "success" if user_prompts._approve_all_active else "warning"
            run_in_terminal(
                lambda: themed_console.print(
                    f"✓ 'Approve All' mode {status}.", style=style
                )
            )
        event.app.invalidate()

    @bindings.add("c-t")
    async def _(event):
        import qx.core.user_prompts as user_prompts

        async with _show_thinking_lock:
            user_prompts._show_thinking_active = not user_prompts._show_thinking_active
            new_status_bool = user_prompts._show_thinking_active

            # Persist the change
            config_manager.set_config_value(
                "QX_SHOW_THINKING", str(new_status_bool).lower()
            )

            status_text = "enabled" if new_status_bool else "disabled"
            style = "warning"
            run_in_terminal(
                lambda: themed_console.print(
                    f"✓ [dim green]Show Thinking:[/] {status_text}.", style=style
                )
            )
        event.app.invalidate()

    session: PromptSession[str] = PromptSession(
        history=qx_history,
        auto_suggest=AutoSuggestFromHistory(),
        enable_history_search=False,
        completer=qx_completer,
        complete_style=CompleteStyle.MULTI_COLUMN,
        key_bindings=bindings,
        mouse_support=False,
        wrap_lines=True,
        multiline=Condition(lambda: is_multiline_mode[0]),
        validator=SingleLineNonEmptyValidator(),
        validate_while_typing=False,
        style=input_style,
        bottom_toolbar=get_bottom_toolbar,
    )

    try:
        while True:
            if not is_multiline_mode[0]:
                is_multiline_mode[0] = False

            current_prompt = (
                HTML('<style fg="#0087ff">Qm⏵</style> ')
                if is_multiline_mode[0]
                else HTML('<style fg="#ff5f00">Qx⏵</style> ')
            )

            result = await session.prompt_async(
                current_prompt, wrap_lines=True, default=pending_text[0] or ""
            )

            if result != "__TOGGLE_MULTILINE__":
                pending_text[0] = ""

            if result == "__TOGGLE_MULTILINE__":
                try:
                    print("\033[1A\r\033[K", end="", flush=True)
                except Exception:
                    pass
                continue

            user_input = result.strip()
            if not user_input:
                if is_multiline_mode[0]:
                    try:
                        print("\033[1A\r\033[K", end="", flush=True)
                    except Exception:
                        pass
                    is_multiline_mode[0] = False
                continue

            if user_input.lower() in ["exit", "quit"]:
                break

            if is_multiline_mode[0]:
                try:
                    print("\033[1A\r\033[K", end="", flush=True)
                except Exception:
                    pass
                is_multiline_mode[0] = False

            if user_input.startswith("/"):
                await _handle_inline_command(user_input, llm_agent)
                continue

            llm_task = asyncio.create_task(
                _handle_llm_interaction(
                    llm_agent, user_input, current_message_history, "rrt"
                )
            )

            try:
                current_message_history = await llm_task
            except asyncio.CancelledError:
                themed_console.print("\nOperation cancelled", style="warning")
                if not llm_task.done():
                    llm_task.cancel()
                    try:
                        await llm_task
                    except asyncio.CancelledError:
                        pass

            if current_message_history:
                save_session(current_message_history)
                clean_old_sessions(keep_sessions)

    except (KeyboardInterrupt, EOFError):
        pass
    finally:
        qx_history.flush_history()
