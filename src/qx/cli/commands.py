import os
import logging
from typing import List, Optional

from rich.console import Console
from openai.types.chat import ChatCompletionMessageParam

from qx.core.llm import QXLLMAgent, initialize_llm_agent
from qx.core.session_manager import reset_session
from qx.core.config_manager import ConfigManager
import qx.core.user_prompts

logger = logging.getLogger("qx")


def _handle_model_command(agent: QXLLMAgent):
    """
    Displays information about the current LLM model configuration.
    """
    rich_console = Console()

    model_info_content = "[bold]Current LLM Model Configuration:[/bold]\n"
    model_info_content += f"  Model Name: [green]{agent.model_name}[/green]\n"
    model_info_content += (
        "  Provider: [green]OpenRouter (https://openrouter.ai/api/v1)[/green]\n"
    )

    temperature_val = agent.temperature
    max_tokens_val = agent.max_output_tokens
    reasoning_effort_val = agent.reasoning_effort

    model_info_content += f"  Temperature: [green]{temperature_val}[/green]\n"
    model_info_content += f"  Max Output Tokens: [green]{max_tokens_val}[/green]\n"
    model_info_content += f"  Reasoning Effort: [green]{reasoning_effort_val if reasoning_effort_val else 'None'}[/green]\n"

    rich_console.print(model_info_content)


async def _handle_inline_command(command_input: str, llm_agent: QXLLMAgent):
    """Handle slash commands in inline mode."""
    rich_console = Console()

    parts = command_input.strip().split(maxsplit=1)
    command_name = parts[0].lower()

    if command_name == "/model":
        _handle_model_command(llm_agent)
    elif command_name == "/reset":
        # Just reset message history in inline mode
        reset_session()
        rich_console.print("[info]Session reset, system prompt reloaded.[/info]")
    elif command_name == "/approve-all":
        async with qx.core.user_prompts._approve_all_lock:
            qx.core.user_prompts._approve_all_active = True
        rich_console.print(
            "[orange]✓ 'Approve All' mode activated for this session.[/orange]"
        )
    elif command_name == "/help":
        rich_console.print("[bold]Available Commands:[/bold]")
        rich_console.print(
            "  [green]/model[/green]      - Show current LLM model configuration"
        )
        rich_console.print(
            "  [green]/reset[/green]      - Reset session and clear message history"
        )
        rich_console.print(
            "  [green]/approve-all[/green] - Activate 'approve all' mode for tool confirmations"
        )
        rich_console.print("  [green]/help[/green]       - Show this help message")
        rich_console.print("\n[bold]Input Modes:[/bold]")
        rich_console.print(
            "  • [yellow]Single-line mode[/yellow] (default): [#ff5f00]QX⏵[/#ff5f00] prompt"
        )
        rich_console.print("    - [cyan]Enter[/cyan]: Submit input")
        rich_console.print("    - [cyan]Alt+Enter[/cyan]: Switch to multiline mode")
        rich_console.print(
            "  • [yellow]Multiline mode[/yellow]: [#0087ff]MULTILINE⏵[/#0087ff] prompt"
        )
        rich_console.print("    - [cyan]Enter[/cyan]: Add newline (continue editing)")
        rich_console.print(
            "    - [cyan]Alt+Enter[/cyan]: Submit input and return to single-line"
        )
        rich_console.print("\n[bold]Features:[/bold]")
        rich_console.print("  • [cyan]Tab completion[/cyan] for commands and paths")
        rich_console.print(
            "  • [cyan]Fuzzy history search[/cyan] with Ctrl+R (using fzf)"
        )
        rich_console.print("  • [cyan]Auto-suggestions[/cyan] from history")
        rich_console.print(
            "  • [cyan]Shift+Tab[/cyan]: Toggle 'Approve All' mode"
        )  # Added Shift+Tab feature
        rich_console.print("  • [cyan]Ctrl+C or Ctrl+D[/cyan] to exit")
    else:
        rich_console.print(f"[red]Unknown command: {command_name}[/red]")
        rich_console.print("Available commands: /model, /reset, /approve-all, /help")


async def handle_command(
    command_input: str,
    llm_agent: QXLLMAgent,
    config_manager: ConfigManager,
    current_message_history: Optional[List[ChatCompletionMessageParam]],
) -> Optional[List[ChatCompletionMessageParam]]:
    """Handle slash commands."""
    parts = command_input.strip().split(maxsplit=1)
    command_name = parts[0].lower()

    if command_name == "/model":
        _handle_model_command(llm_agent)
    elif command_name == "/reset":
        # No console to clear in inline mode
        reset_session()
        # Re-initialize agent after reset, as system prompt might change
        from qx.core.constants import DEFAULT_MODEL

        model_name_from_env = os.environ.get("QX_MODEL_NAME", DEFAULT_MODEL)
        new_agent = initialize_llm_agent(
            model_name_str=model_name_from_env,
            console=None,
            mcp_manager=config_manager.mcp_manager,
            enable_streaming=os.environ.get("QX_ENABLE_STREAMING", "true").lower()
            == "true",
        )
        if new_agent is None:
            Console().print("[red]Error:[/red] Failed to reinitialize agent after reset")
            return current_message_history
        # Note: We can't actually replace the agent reference here since it's passed by value
        Console().print("[info]Session reset, system prompt reloaded.[/info]")
        return None  # Clear history after reset
    else:
        Console().print(f"[red]Unknown command: {command_name}[/red]")
        Console().print("Available commands: /model, /reset")
    return current_message_history
