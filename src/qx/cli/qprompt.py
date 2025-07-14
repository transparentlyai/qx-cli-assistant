import asyncio
import logging
import os
import signal
import subprocess
from typing import Any, List, Optional

from openai.types.chat import ChatCompletionMessageParam, ChatCompletionUserMessageParam
from prompt_toolkit import PromptSession
from prompt_toolkit.application import run_in_terminal
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.filters import Condition
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.shortcuts.prompt import CompleteStyle
from prompt_toolkit.styles import Style
from prompt_toolkit.validation import ValidationError, Validator

from qx.cli.commands import _handle_clear_command, _handle_inline_command
from qx.cli.completer import QXCompleter
from qx.cli.history import QXHistory
from qx.cli.theme import themed_console
from qx.core.config_manager import ConfigManager
from qx.core.history_utils import parse_history_for_fzf
from qx.core.llm import QXLLMAgent, query_llm
from qx.core.output_control import output_control_manager
from qx.core.paths import QX_HISTORY_FILE
from qx.core.session_manager import clean_old_sessions, save_session
from qx.core.state_manager import details_manager
from qx.core.user_prompts import _approve_all_lock

logger = logging.getLogger("qx")

is_multiline_mode = [False]
pending_text = [""]
_details_active_for_toolbar = [True]
_stdout_active_for_toolbar = [True]
_planning_mode_active = [False]
_thinking_budget = ["low"]  # Always starts at LOW
_thinking_budget_levels = ["low", "medium", "high"]
_current_agent_for_toolbar: List[Optional[Any]] = [
    None
]  # Store current agent reference


def _model_supports_thinking(model_name: str) -> bool:
    """Check if the model supports thinking budget parameter."""
    from qx.core.models import MODELS

    for model_config in MODELS:
        if model_config["model"] == model_name:
            return "thinking" in model_config.get("accepts", ())
    return False


class SingleLineNonEmptyValidator(Validator):
    def validate(self, document):
        if not is_multiline_mode[0]:
            text = document.text.strip()
            if not text:
                raise ValidationError(message="")


def get_bottom_toolbar():
    import qx.core.user_prompts as user_prompts
    from qx.core.agent_mode_manager import get_agent_mode_manager

    agent_mode_manager = get_agent_mode_manager()
    agent_mode_text = agent_mode_manager.get_display_text()
    agent_mode_status = f'<style bg="#3b82f6" fg="black">{agent_mode_text}</style>'

    approve_all_status = (
        '<style bg="#22c55e" fg="black">ON</style>'
        if user_prompts._approve_all_active
        else '<style bg="#ef4444" fg="black">OFF</style>'
    )
    details_status = (
        '<style bg="#22c55e" fg="black">ON</style>'
        if _details_active_for_toolbar[0]
        else '<style bg="#ef4444" fg="black">OFF</style>'
    )
    stdout_status = (
        '<style bg="#22c55e" fg="black">ON</style>'
        if _stdout_active_for_toolbar[0]
        else '<style bg="#ef4444" fg="black">OFF</style>'
    )

    mode_status = (
        '<style bg="#0097ff" fg="black">PLANNING</style>'
        if _planning_mode_active[0]
        else '<style bg="#22c55e" fg="black">IMPLEMENTING</style>'
    )

    # Add thinking budget status
    current_agent = _current_agent_for_toolbar[0]

    if current_agent and _model_supports_thinking(current_agent.model_name):
        thinking_level = _thinking_budget[0].upper()
        thinking_status = f'<style bg="#3b82f6" fg="black">{thinking_level}</style>'
    else:
        thinking_status = '<style fg="#6b7280">DISABLED</style>'

    toolbar_html = f'<style fg="black" bg="white"> <style fg="black" bg="#6b7280">F1</style> {mode_status} | <style fg="black" bg="#6b7280">F2</style> {agent_mode_status} | <style fg="black" bg="#6b7280">F3</style> Details: {details_status} | <style fg="black" bg="#6b7280">F4</style> StdOE: {stdout_status} | <style fg="black" bg="#6b7280">F5</style> Approve All: {approve_all_status} | <style fg="black" bg="#6b7280">F6</style> Think: {thinking_status}</style>'
    return HTML(toolbar_html)


async def _handle_llm_interaction(
    agent: QXLLMAgent,
    user_input: str,
    current_message_history: Optional[List[ChatCompletionMessageParam]],
    code_theme_to_use: str,
    plain_text_output: bool = False,
    add_user_message_to_history: bool = True,
    config_manager: Optional[Any] = None,
) -> Optional[List[ChatCompletionMessageParam]]:
    run_result: Optional[Any] = None
    try:
        # Update agent's reasoning effort if model supports thinking
        if _model_supports_thinking(agent.model_name):
            agent.reasoning_effort = _thinking_budget[0]

        run_result = await query_llm(
            agent,
            user_input,
            message_history=current_message_history,
            console=themed_console,
            add_user_message_to_history=add_user_message_to_history,
            config_manager=config_manager,
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
            # Use BorderedMarkdown for consistent #050505 background color
            from rich.markdown import Markdown

            from qx.cli.quote_bar_component import BorderedMarkdown

            bordered_md = BorderedMarkdown(
                Markdown(output_content, code_theme="rrt"),
                border_style="dim blue",
                background_color="#050505",
            )
            themed_console.print(bordered_md, markup=True)
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
    config_manager: ConfigManager,
):
    qx_history = QXHistory(QX_HISTORY_FILE)
    qx_completer = QXCompleter()
    _details_active_for_toolbar[0] = await details_manager.is_active()
    _stdout_active_for_toolbar[0] = await output_control_manager.should_show_stdout()

    # Get the agent manager and check if we need to restore agent's history
    from qx.core.agent_manager import get_agent_manager

    agent_manager = get_agent_manager()
    current_agent_name = await agent_manager.get_current_agent_name()

    if current_agent_name and current_message_history is None:
        # Try to restore this agent's previous message history
        restored_history = agent_manager.get_current_message_history()
        if restored_history:
            current_message_history = restored_history
            logger.debug(
                f"Restored {len(current_message_history)} messages for agent '{current_agent_name}'"
            )

    # Load planning mode from configuration
    planning_mode_config = config_manager.get_config_value("QX_PLANNING_MODE", "false")
    _planning_mode_active[0] = planning_mode_config.lower() == "true"

    # Load agent mode from configuration
    from qx.core.agent_mode_manager import get_agent_mode_manager, AgentMode

    agent_mode_manager = get_agent_mode_manager()
    agent_mode_config = config_manager.get_config_value("QX_AGENT_MODE", "multi")
    if agent_mode_config.lower() == "single":
        agent_mode_manager.set_mode(AgentMode.SINGLE)
    else:
        agent_mode_manager.set_mode(AgentMode.MULTI)

    # Track the current agent to detect switches
    current_active_agent = llm_agent
    _current_agent_for_toolbar[0] = llm_agent

    # Initialize global hotkey system but don't start it yet
    # We'll use suspend/resume pattern around prompt_toolkit usage
    try:
        from qx.core.hotkey_manager import (
            get_hotkey_manager,
            register_default_handlers,
            register_global_hotkey,
        )

        global_hotkey_manager = get_hotkey_manager()
        # Register handlers but don't start yet - we'll control start/stop around prompts
        register_default_handlers()
        # Register global hotkeys for all the same functions as prompt_toolkit
        register_global_hotkey("ctrl+c", "cancel")  # Same as prompt_toolkit
        register_global_hotkey("ctrl+d", "exit")  # Same as prompt_toolkit
        register_global_hotkey("ctrl+r", "history")  # Same as prompt_toolkit
        register_global_hotkey("ctrl+a", "approve_all")  # Same as prompt_toolkit
        register_global_hotkey("f5", "approve_all")  # Alternative to Ctrl+A
        register_global_hotkey(
            "f1", "toggle_planning_mode"
        )  # Toggle planning/implementing
        register_global_hotkey("f2", "toggle_agent_mode")  # Toggle multi/single agent
        register_global_hotkey("f3", "toggle_details")  # Same as prompt_toolkit
        register_global_hotkey("f4", "toggle_stdout")  # Re-enabled with fix
        register_global_hotkey("f12", "cancel")  # Additional emergency key
        logger.debug("Global hotkey handlers registered (matching prompt_toolkit)")
    except Exception as e:
        logger.debug(f"Exception during global hotkey setup: {e}")
        global_hotkey_manager = None

    input_style = Style.from_dict(
        {
            "": "fg:#ff005f",
            "selected": "fg:#ff005f bg:#050505 reverse",
            "bottom-toolbar": "fg:black bg:black",
            "bottom-toolbar.text": "fg:black bg:black",
            "bottom-toolbar.key": "fg:black bg:black",
            "toolbar": "fg:black bg:black",
            "status": "fg:black bg:black",
            # --- Custom styles for completion menu ---
            "completion-menu": "bg:#080808 #dddddd",
            "completion-menu.completion": "fg:#dddddd bg:#080808",
            "completion-menu.completion.current": "bg:#ffffff #007bff",
            "completion-menu.meta": "fg:#aaaaaa bg:#080808",
            "completion-menu.meta.current": "fg:#007bff bg:#080808 italic",
        }
    )

    # Restore all hotkeys in prompt_toolkit - this works better than global capture during input
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
            style = "warning"
            run_in_terminal(
                lambda: themed_console.print(
                    f"✓ [dim green]Approve All mode[/] {status}.", style=style
                )
            )
        event.app.invalidate()

    @bindings.add("f5")
    async def _(event):
        import qx.core.user_prompts as user_prompts

        async with _approve_all_lock:
            user_prompts._approve_all_active = not user_prompts._approve_all_active
            status = "activated" if user_prompts._approve_all_active else "deactivated"
            style = "warning"
            run_in_terminal(
                lambda: themed_console.print(
                    f"✓ [dim green]Approve All mode[/] {status}.", style=style
                )
            )
        event.app.invalidate()

    @bindings.add("f3")
    async def _(event):
        new_status = not await details_manager.is_active()
        await details_manager.set_status(new_status)
        _details_active_for_toolbar[0] = new_status

        config_manager.set_config_value("QX_SHOW_DETAILS", str(new_status).lower())

        status_text = "enabled" if new_status else "disabled"
        style = "warning"
        run_in_terminal(
            lambda: themed_console.print(
                f"✓ [dim green]Details:[/] {status_text}.", style=style
            )
        )
        event.app.invalidate()

    @bindings.add("f4")
    async def _(event):
        # Get current status and toggle it
        current_status = await output_control_manager.should_show_stdout()
        new_status = not current_status
        await output_control_manager.set_stdout_visibility(new_status)
        _stdout_active_for_toolbar[0] = new_status

        status_text = "enabled" if new_status else "disabled"
        style = "warning"
        run_in_terminal(
            lambda: themed_console.print(
                f"✓ [dim green]StdOE:[/] {status_text}.", style=style
            )
        )
        event.app.invalidate()

    @bindings.add("f1")
    def _(event):
        _planning_mode_active[0] = not _planning_mode_active[0]
        mode_text = "Planning" if _planning_mode_active[0] else "Implementing"

        # Save the planning mode state to configuration
        config_manager.set_config_value(
            "QX_PLANNING_MODE", str(_planning_mode_active[0]).lower()
        )

        style = "warning"
        run_in_terminal(
            lambda: themed_console.print(
                f"✓ [dim green]Mode:[/] {mode_text}.", style=style
            )
        )
        event.app.invalidate()

    @bindings.add("f2")
    def _(event):
        from qx.core.agent_mode_manager import get_agent_mode_manager

        agent_mode_manager = get_agent_mode_manager()
        agent_mode_manager.toggle()
        mode_text = agent_mode_manager.get_display_text()

        # Save the agent mode state to configuration
        config_manager.set_config_value("QX_AGENT_MODE", mode_text.lower())

        style = "warning"
        run_in_terminal(
            lambda: themed_console.print(
                f"✓ [dim green]Agent Mode:[/] {mode_text}.", style=style
            )
        )
        event.app.invalidate()

    @bindings.add("f6")
    def _(event):
        current_agent = _current_agent_for_toolbar[0]

        # Check if current model supports thinking
        if current_agent and _model_supports_thinking(current_agent.model_name):
            # Cycle through thinking budget levels
            current_index = _thinking_budget_levels.index(_thinking_budget[0])
            next_index = (current_index + 1) % len(_thinking_budget_levels)
            _thinking_budget[0] = _thinking_budget_levels[next_index]

            thinking_text = _thinking_budget[0].upper()
            style = "warning"
            run_in_terminal(
                lambda: themed_console.print(
                    f"✓ [dim green]Thinking Budget:[/] {thinking_text}.", style=style
                )
            )
        else:
            # Model doesn't support thinking
            style = "error"
            run_in_terminal(
                lambda: themed_console.print(
                    "✗ [red]Thinking Budget:[/] Not supported by current model.",
                    style=style,
                )
            )

        event.app.invalidate()

    @bindings.add("c-e")
    def _(event):
        import tempfile

        current_text = event.current_buffer.text
        editor = os.getenv("QX_DEFAULT_EDITOR", "nano")
        temp_file_path = None

        try:
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".txt", delete=False
            ) as temp_file:
                temp_file.write(current_text)
                temp_file_path = temp_file.name

            print("\r\033[K", end="", flush=True)

            editor_cmd = []
            if editor in ["code", "vscode"]:
                editor_cmd = [editor, "--wait", temp_file_path]
            elif editor in ["nano", "vi", "vim", "nvim"]:
                editor_cmd = [editor, temp_file_path]
            else:
                editor_cmd = [editor, temp_file_path]

            subprocess.run(editor_cmd, check=False)

            event.app.invalidate()
            event.app.renderer.reset()

            try:
                with open(temp_file_path, "r") as f:
                    edited_content = f.read()
                event.current_buffer.text = edited_content
                event.current_buffer.cursor_position = len(edited_content)
            except Exception as read_error:
                run_in_terminal(
                    lambda err=read_error: themed_console.print(
                        f"✗ [red]Error reading edited file:[/] {err}", style="error"
                    )
                )

        except Exception as edit_error:
            run_in_terminal(
                lambda err=edit_error: themed_console.print(
                    f"✗ [red]Failed to open editor:[/] {err}", style="error"
                )
            )
        finally:
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.unlink(temp_file_path)
                except Exception:
                    pass

    session: PromptSession[str] = PromptSession(
        history=qx_history,
        auto_suggest=AutoSuggestFromHistory(),
        enable_history_search=False,
        completer=qx_completer,
        complete_style=CompleteStyle.COLUMN,
        key_bindings=bindings,
        mouse_support=False,
        wrap_lines=True,
        multiline=Condition(lambda: is_multiline_mode[0]),
        validator=SingleLineNonEmptyValidator(),
        validate_while_typing=False,
        style=input_style,
        bottom_toolbar=get_bottom_toolbar,
    )

    # Handle terminal resize for proper redrawing
    def handle_resize(signum, frame):
        if hasattr(session, "app") and session.app:
            session.app.invalidate()
            session.app.renderer.reset()

    # Register signal handler for terminal resize
    signal.signal(signal.SIGWINCH, handle_resize)

    try:
        # Team mode workflow removed - will be reimplemented later

        while True:
            if not is_multiline_mode[0]:
                is_multiline_mode[0] = False

            # Get current agent color for prompt (text always remains "Qx")
            from qx.core.agent_manager import get_agent_manager

            agent_manager = get_agent_manager()
            current_agent_config = await agent_manager.get_current_agent()

            if current_agent_config:
                agent_color = getattr(current_agent_config, "color", None)

                # Use agent color if available, otherwise fallback to random color
                if agent_color:
                    prompt_color = agent_color
                else:
                    # Import color selection function and use agent name for consistent color
                    from qx.cli.quote_bar_component import get_agent_color

                    agent_name = current_agent_config.name or "Qx"
                    prompt_color = get_agent_color(agent_name, None)
            else:
                # Fallback when no agent is loaded
                prompt_color = "#ff5f00"

            current_prompt = (
                HTML('<style fg="#0087ff">Qxm⏵</style> ')
                if is_multiline_mode[0]
                else HTML(f'<style fg="{prompt_color}">Qx⏵</style> ')
            )

            # Stop global hotkeys before prompt_toolkit takes control
            if global_hotkey_manager and global_hotkey_manager.running:
                global_hotkey_manager.stop()
                logger.debug("Stopped global hotkeys for prompt input")

            try:
                result = await session.prompt_async(
                    current_prompt, wrap_lines=True, default=pending_text[0] or ""
                )
            finally:
                # Always restart global hotkeys after prompt_toolkit releases control
                if global_hotkey_manager:
                    global_hotkey_manager.start()
                    logger.debug("Restarted global hotkeys after prompt input")

            if result not in ["__TOGGLE_MULTILINE__", "__AGENT_SWITCHED__"]:
                pending_text[0] = ""

            if result == "__TOGGLE_MULTILINE__":
                try:
                    print("\033[1A\r\033[K", end="", flush=True)
                except Exception:
                    pass
                continue

            if result == "__AGENT_SWITCHED__":
                # Agent was switched, clear the prompt line and continue with new colors
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

            if user_input.lower() == "clear":
                _handle_clear_command(llm_agent)
                continue

            if is_multiline_mode[0]:
                try:
                    print("\033[1A\r\033[K", end="", flush=True)
                except Exception:
                    pass
                is_multiline_mode[0] = False

            if user_input.startswith("/"):
                # Get current active agent for command handling
                from qx.core.agent_manager import get_agent_manager

                agent_manager = get_agent_manager()
                active_llm_agent = agent_manager.get_active_llm_agent() or llm_agent

                # Pass current message history to command handler
                result = await _handle_inline_command(
                    user_input,
                    active_llm_agent,
                    config_manager,
                    current_message_history,
                )

                # Check if command returned an updated message history
                if result is not None:
                    current_message_history = result
                    logger.debug(
                        f"Updated message history from command: {len(current_message_history)} messages"
                    )
                # Special handling for agent switch to restore agent's history
                elif user_input.startswith("/agents switch"):
                    # Get the new agent's message history
                    new_agent_name = await agent_manager.get_current_agent_name()
                    if new_agent_name:
                        new_history = agent_manager.get_current_message_history()
                        if new_history is not None:
                            current_message_history = new_history
                            logger.debug(
                                f"Restored {len(current_message_history)} messages for agent '{new_agent_name}'"
                            )
                continue

            # Save user message immediately
            if current_message_history is None:
                current_message_history = []

            # Process directives if input contains @
            processed_input = user_input
            if "@" in user_input:
                from qx.core.directive_manager import get_directive_manager

                directive_manager = get_directive_manager()

                # Find all @directive references in the input
                import re

                directive_pattern = r"@(\w+)"
                matches = re.findall(directive_pattern, user_input)

                for directive_name in matches:
                    directive = directive_manager.get_directive(directive_name)
                    if directive:
                        # Replace @directive with the directive content
                        processed_input = processed_input.replace(
                            f"@{directive_name}", f"\n\n{directive.content}\n\n"
                        )
                        themed_console.print(
                            f"[dim cyan]Loaded directive: @{directive_name}[/dim cyan]"
                        )
                    else:
                        themed_console.print(
                            f"[yellow]Warning: Unknown directive @{directive_name}[/yellow]"
                        )

            # Inject mode indicator if active
            final_user_input = processed_input
            if _planning_mode_active[0]:
                final_user_input = processed_input + "\n\n---\nPLANNING mode activated"
            else:
                final_user_input = (
                    processed_input + "\n\n---\nIMPLEMENTING mode activated"
                )

            current_message_history.append(
                ChatCompletionUserMessageParam(role="user", content=final_user_input)
            )

            # Save with all agent histories
            current_agent_name = await agent_manager.get_current_agent_name() or "qx"
            agent_manager.save_agent_message_history(
                current_agent_name, current_message_history
            )
            save_session(current_agent_name, agent_manager._agent_message_histories)

            # Get the currently active LLM agent (may have been switched)
            from qx.core.agent_manager import get_agent_manager

            agent_manager = get_agent_manager()
            active_llm_agent = agent_manager.get_active_llm_agent()

            # If no active agent in manager, something is wrong - keep using original
            if active_llm_agent is None:
                logger.warning(
                    "No active LLM agent found in agent manager, using original agent"
                )
                active_llm_agent = llm_agent

            # Update current agent tracker for display purposes
            if active_llm_agent != current_active_agent:
                current_active_agent = active_llm_agent
                _current_agent_for_toolbar[0] = active_llm_agent
                logger.info(
                    f"🔄 Agent switched, now using: {getattr(active_llm_agent, 'agent_name', 'unknown')}"
                )
                # Conversation history is managed per agent

            llm_task = asyncio.create_task(
                _handle_llm_interaction(
                    active_llm_agent,
                    final_user_input,
                    current_message_history,
                    "rrt",
                    add_user_message_to_history=False,
                    config_manager=config_manager,
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
                # Save current agent's history first
                current_agent_name = (
                    await agent_manager.get_current_agent_name() or "qx"
                )
                agent_manager.save_agent_message_history(
                    current_agent_name, current_message_history
                )

                # Save session with all agent histories
                save_session(current_agent_name, agent_manager._agent_message_histories)
                clean_old_sessions(keep_sessions)

    except (KeyboardInterrupt, EOFError):
        pass
    finally:
        # Save all agent histories before exiting
        try:
            current_agent_name = await agent_manager.get_current_agent_name() or "qx"
            if current_message_history:
                agent_manager.save_agent_message_history(
                    current_agent_name, current_message_history
                )
                save_session(current_agent_name, agent_manager._agent_message_histories)
                logger.debug(
                    f"Saved session with {len(agent_manager._agent_message_histories)} agent(s) on exit"
                )
        except Exception as e:
            logger.error(f"Error saving session on exit: {e}")

        qx_history.flush_history()
        # Stop global hotkey system
        try:
            if global_hotkey_manager and global_hotkey_manager.running:
                global_hotkey_manager.stop()
                logger.debug("Global hotkey system stopped")
        except Exception as e:
            logger.error(f"Error stopping global hotkey system: {e}")
