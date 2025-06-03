import os
import logging
from typing import List, Optional

from openai.types.chat import ChatCompletionMessageParam

from qx.cli.theme import themed_console
from qx.core.llm import QXLLMAgent, initialize_llm_agent
from qx.core.session_manager import reset_session
from qx.core.config_manager import ConfigManager
import qx.core.user_prompts

logger = logging.getLogger("qx")


def _handle_model_command(agent: QXLLMAgent):
    """
    Displays information about the current LLM model configuration.
    """
    model_info_content = "Current LLM Model Configuration:\n"
    model_info_content += f"  Model Name: {agent.model_name}\n"
    model_info_content += "  Provider: OpenRouter (https://openrouter.ai/api/v1)\n"

    temperature_val = agent.temperature
    max_tokens_val = agent.max_output_tokens
    reasoning_effort_val = agent.reasoning_effort

    model_info_content += f"  Temperature: {temperature_val}\n"
    model_info_content += f"  Max Output Tokens: {max_tokens_val}\n"
    model_info_content += f"  Reasoning Effort: {reasoning_effort_val if reasoning_effort_val else 'None'}\n"

    themed_console.print(model_info_content, style="app.header")


async def _handle_inline_command(command_input: str, llm_agent: QXLLMAgent):
    """Handle slash commands in inline mode."""
    parts = command_input.strip().split(maxsplit=1)
    command_name = parts[0].lower()
    command_args = parts[1] if len(parts) > 1 else ""

    if command_name == "/model":
        _handle_model_command(llm_agent)
    elif command_name == "/reset":
        # Just reset message history in inline mode
        reset_session()
        themed_console.print("Session reset, system prompt reloaded.", style="info")
    elif command_name == "/approve-all":
        async with qx.core.user_prompts._approve_all_lock:
            qx.core.user_prompts._approve_all_active = True
        themed_console.print(
            "✓ 'Approve All' mode activated for this session.", style="warning"
        )
    elif command_name == "/print":
        if command_args:
            themed_console.print(command_args)
        else:
            themed_console.print("Usage: /print <text to print>", style="error")
    elif command_name == "/help":
        themed_console.print("Available Commands:", style="app.header")
        themed_console.print(
            "  /model      - Show current LLM model configuration", style="primary"
        )
        themed_console.print(
            "  /reset      - Reset session and clear message history", style="primary"
        )
        themed_console.print(
            "  /approve-all - Activate 'approve all' mode for tool confirmations",
            style="primary",
        )
        themed_console.print(
            "  /print <text> - Print the specified text to the console", style="primary"
        )
        themed_console.print("  /help       - Show this help message", style="primary")
        themed_console.print("\nInput Modes:", style="app.header")
        themed_console.print(
            "  • Single-line mode (default): Qx⏵ prompt", style="warning"
        )
        themed_console.print("    - Enter: Submit input", style="info")
        themed_console.print("    - Alt+Enter: Switch to multiline mode", style="info")
        themed_console.print("  • Multiline mode: MULTILINE⏵ prompt", style="warning")
        themed_console.print(
            "    - Enter: Add newline (continue editing)", style="info"
        )
        themed_console.print(
            "    - Alt+Enter: Submit input and return to single-line", style="info"
        )
        themed_console.print("\nFeatures:", style="app.header")
        themed_console.print("  • Tab completion for commands and paths", style="info")
        themed_console.print(
            "  • Fuzzy history search with Ctrl+R (using fzf)", style="info"
        )
        themed_console.print("  • Auto-suggestions from history", style="info")
        themed_console.print("  • Shift+Tab: Toggle 'Approve All' mode", style="info")
        themed_console.print("\nEmergency Stop:", style="app.header")
        themed_console.print(
            "  • Ctrl+C: Emergency stop - interrupts current operation and returns to prompt",
            style="info",
        )
        themed_console.print(
            "    - Cancels streaming LLM responses immediately", style="text.muted"
        )
        themed_console.print(
            "    - Preserves partial responses when possible", style="text.muted"
        )
        themed_console.print("    - Does not exit the application", style="text.muted")
        themed_console.print("\nExit:", style="app.header")
        themed_console.print("  • Ctrl+D: Exit QX", style="info")
    else:
        themed_console.print(f"Unknown command: {command_name}", style="error")
        themed_console.print(
            "Available commands: /model, /reset, /approve-all, /print, /help",
            style="text.muted",
        )


async def handle_command(
    command_input: str,
    llm_agent: QXLLMAgent,
    config_manager: ConfigManager,
    current_message_history: Optional[List[ChatCompletionMessageParam]],
) -> Optional[List[ChatCompletionMessageParam]]:
    """Handle slash commands."""
    parts = command_input.strip().split(maxsplit=1)
    command_name = parts[0].lower()
    command_args = parts[1] if len(parts) > 1 else ""


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
            themed_console.print(
                "Error: Failed to reinitialize agent after reset", style="error"
            )
            return current_message_history
        # Note: We can't actually replace the agent reference here since it's passed by value
        themed_console.print("Session reset, system prompt reloaded.", style="info")
        return None  # Clear history after reset
    elif command_name == "/print": # Added to handle_command as well for consistency
        if command_args:
            themed_console.print(command_args)
        else:
            themed_console.print("Usage: /print <text to print>", style="error")
    else:
        themed_console.print(f"Unknown command: {command_name}", style="error")
        themed_console.print("Available commands: /model, /reset, /print", style="text.muted")
    return current_message_history
