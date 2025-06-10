import os
import logging
from pathlib import Path
from typing import List, Optional

from openai.types.chat import ChatCompletionMessageParam
from rich.text import Text

from qx.cli.theme import themed_console
from qx.core.llm import QXLLMAgent, initialize_llm_agent
from qx.core.session_manager import reset_session
from qx.core.config_manager import ConfigManager
import qx.core.user_prompts
from qx.core.constants import MODELS
from qx.core.agent_manager import get_agent_manager

logger = logging.getLogger("qx")


def _handle_model_command(
    agent: QXLLMAgent,
    config_manager: ConfigManager,
    new_model_name: Optional[str] = None,
):
    """
    Displays or updates the current LLM model configuration.
    """
    if new_model_name:
        model_to_save = None
        for model in MODELS:
            if model["name"] == new_model_name:
                model_to_save = model["model"]
                break

        if model_to_save:
            config_manager.set_config_value("QX_MODEL_NAME", model_to_save)
            themed_console.print(f"Model updated to: {model_to_save}", style="info")
            themed_console.print(
                "Please restart QX for the change to take full effect.", style="warning"
            )
        else:
            themed_console.print(f"Model '{new_model_name}' not found.", style="error")

    else:
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


SIMPLE_TOOL_DESCRIPTIONS = {
    "get_current_time_tool": "Provides the current date and time.",
    "execute_shell_tool": "Runs a specified command in the shell.",
    "read_file_tool": "Reads the contents of a file at a given path.",
    "todo_manager_tool": "Helps manage tasks and to-do lists.",
    "web_fetch_tool": "Retrieves content from a URL.",
    "write_file_tool": "Creates or updates a file with the provided content.",
    "worktree_manager_tool": "Manages Git worktrees for branch management.",
    # MCP tools (dynamically loaded)
    "brave_web_search": "Searches the web using Brave Search API (MCP).",
    "brave_local_search": "Searches for local businesses and places (MCP).",
    "fetch_html": "Fetches website content as HTML (MCP).",
    "fetch_markdown": "Fetches website content as Markdown (MCP).",
    "fetch_txt": "Fetches website content as plain text (MCP).",
    "fetch_json": "Fetches JSON data from URLs (MCP).",
}


def _handle_tools_command(agent: QXLLMAgent):
    """
    Displays the list of active tools.
    """
    themed_console.print("Active Tools:", style="app.header")
    if not agent._openai_tools_schema:
        themed_console.print("  No tools available.", style="warning")
        return

    for tool in agent._openai_tools_schema:
        tool_name = tool.get("function", {}).get("name", "N/A")
        description = SIMPLE_TOOL_DESCRIPTIONS.get(
            tool_name, "No description available."
        )
        text = Text()
        text.append(f"  - {tool_name}: ", style="primary")
        text.append(description, style="dim white")
        themed_console.print(text)


async def _handle_agents_command(command_args: str, config_manager: ConfigManager):
    """
    Handle agent management commands.
    """
    parts = command_args.strip().split() if command_args else []
    subcommand = parts[0] if parts else "list"

    agent_manager = get_agent_manager()

    if subcommand == "list":
        # Use current working directory for project-specific agent discovery
        agents_info = await agent_manager.list_agents(cwd=os.getcwd())
        current_agent_name = await agent_manager.get_current_agent_name()

        # Categorize agents by their source
        project_agents = []
        development_agents = []
        user_agents = []
        system_agents = []
        
        for agent in agents_info:
            agent_path = agent.get("path", "")
            if ".Q/agents" in agent_path:
                project_agents.append(agent)
            elif "src/qx/agents" in agent_path:
                development_agents.append(agent)
            elif ".config/qx/agents" in agent_path:
                user_agents.append(agent)
            else:
                system_agents.append(agent)

        themed_console.print("Available Agents:", style="app.header")
        
        # Show project agents first (most relevant)
        if project_agents:
            themed_console.print("\n📁 Project Agents (.Q/agents/):", style="bold blue")
            for agent in project_agents:
                name = agent["name"]
                mode = agent.get("execution_mode", "unknown")
                status = " [CURRENT]" if agent.get("is_current") else ""
                
                text = Text()
                text.append(f"  📁 {name}: ", style="blue")
                text.append(f"{mode}{status}", style="dim white")
                themed_console.print(text)

        # Show built-in agents
        if development_agents:
            themed_console.print("\n🛠️  Built-in Agents:", style="bold green")
            for agent in development_agents:
                name = agent["name"]
                mode = agent.get("execution_mode", "unknown")
                status = " [CURRENT]" if agent.get("is_current") else ""
                
                text = Text()
                text.append(f"  - {name}: ", style="primary")
                text.append(f"{mode}{status}", style="dim white")
                themed_console.print(text)

        # Show user agents
        if user_agents:
            themed_console.print("\n👤 User Agents (~/.config/qx/agents/):", style="bold yellow")
            for agent in user_agents:
                name = agent["name"]
                mode = agent.get("execution_mode", "unknown")
                status = " [CURRENT]" if agent.get("is_current") else ""
                
                text = Text()
                text.append(f"  - {name}: ", style="primary")
                text.append(f"{mode}{status}", style="dim white")
                themed_console.print(text)

        # Show system agents
        if system_agents:
            themed_console.print("\n🌐 System Agents (/etc/qx/agents/):", style="bold white")
            for agent in system_agents:
                name = agent["name"]
                mode = agent.get("execution_mode", "unknown")
                status = " [CURRENT]" if agent.get("is_current") else ""
                
                text = Text()
                text.append(f"  - {name}: ", style="primary")
                text.append(f"{mode}{status}", style="dim white")
                themed_console.print(text)
        
        # If no agents found
        if not (project_agents or development_agents or user_agents or system_agents):
            themed_console.print("No agents found.", style="warning")

    elif subcommand == "switch":
        if len(parts) < 2:
            themed_console.print("Usage: /agents switch <agent_name>", style="error")
            return

        agent_name = parts[1]

        try:
            # Attempt to switch the LLM agent
            success = await agent_manager.switch_llm_agent(
                agent_name, config_manager.mcp_manager
            )

            if success:
                themed_console.print(
                    f"Successfully switched to agent '{agent_name}'", style="info"
                )

                # Show the new agent info
                current_agent = await agent_manager.get_current_agent()
                if current_agent:
                    role_preview = (
                        current_agent.role[:100] + "..."
                        if len(current_agent.role) > 100
                        else current_agent.role
                    )
                    themed_console.print(f"Role: {role_preview}", style="dim white")
                    themed_console.print(
                        "Agent is now active and will respond to your queries.",
                        style="info",
                    )
            else:
                themed_console.print(
                    f"Failed to switch to agent '{agent_name}'", style="error"
                )
        except Exception as e:
            themed_console.print(
                f"Error switching to agent '{agent_name}': {e}", style="error"
            )

    elif subcommand == "info":
        current_agent_name = await agent_manager.get_current_agent_name()
        current_agent = await agent_manager.get_current_agent()

        if current_agent_name and current_agent:
            themed_console.print(f"Current Agent: {current_agent_name}", style="info")

            # Show role preview
            role_preview = (
                current_agent.role[:150] + "..."
                if len(current_agent.role) > 150
                else current_agent.role
            )
            themed_console.print(f"Role: {role_preview}", style="dim white")

            # Show execution mode
            mode = (
                current_agent.execution.mode
                if current_agent.execution
                else "interactive"
            )
            themed_console.print(f"Mode: {mode}", style="dim white")

            # Show model info
            if current_agent.model:
                model_name = current_agent.model.name
                themed_console.print(f"Model: {model_name}", style="dim white")
                
            # Show agent source location
            agent_info = agent_manager.get_agent_info(current_agent_name, cwd=os.getcwd())
            if agent_info and "path" in agent_info:
                agent_path = Path(agent_info["path"])
                if ".Q/agents" in str(agent_path):
                    themed_console.print(f"Source: {agent_path} (Project Agent)", style="dim blue")
                elif "src/qx/agents" in str(agent_path):
                    themed_console.print(f"Source: {agent_path} (Development Agent)", style="dim green")
                elif ".config/qx/agents" in str(agent_path):
                    themed_console.print(f"Source: {agent_path} (User Agent)", style="dim yellow")
                else:
                    themed_console.print(f"Source: {agent_path}", style="dim white")
        else:
            themed_console.print("No current agent loaded", style="warning")

    elif subcommand == "reload":
        reload_agent_name: Optional[str] = (
            parts[1] if len(parts) > 1 else await agent_manager.get_current_agent_name()
        )
        if not reload_agent_name:
            themed_console.print(
                "No agent specified and no current agent to reload", style="error"
            )
            return

        result = await agent_manager.reload_agent(reload_agent_name)
        if result.success:
            themed_console.print(
                f"Reloaded agent '{reload_agent_name}' from {result.source_path}",
                style="info",
            )
        else:
            themed_console.print(
                f"Failed to reload agent '{reload_agent_name}': {result.error}",
                style="error",
            )
    
    elif subcommand == "refresh":
        # Refresh agent discovery to pick up new project agents
        agent_names = agent_manager.refresh_agent_discovery(cwd=os.getcwd())
        themed_console.print(f"Refreshed agent discovery. Found {len(agent_names)} agents.", style="info")
        
        # Show any new project agents
        project_agents = []
        for name in agent_names:
            agent_info = agent_manager.get_agent_info(name, cwd=os.getcwd())
            if agent_info and ".Q/agents" in agent_info.get("path", ""):
                project_agents.append(name)
        
        if project_agents:
            themed_console.print(f"Project agents: {', '.join(project_agents)}", style="blue")
        else:
            themed_console.print("No project agents found in .Q/agents/", style="dim white")

    else:
        themed_console.print(f"Unknown agents subcommand: {subcommand}", style="error")
        themed_console.print(
            "Available subcommands: list, switch, info, reload, refresh", style="text.muted"
        )


async def _handle_inline_command(
    command_input: str, llm_agent: QXLLMAgent, config_manager: ConfigManager
):
    """Handle slash commands in inline mode."""
    parts = command_input.strip().split(maxsplit=1)
    command_name = parts[0].lower()
    command_args = parts[1] if len(parts) > 1 else ""

    if command_name == "/model":
        _handle_model_command(llm_agent, config_manager, command_args)
    elif command_name == "/tools":
        _handle_tools_command(llm_agent)
    elif command_name == "/agents":
        await _handle_agents_command(command_args, config_manager)
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
            "  /model [<model-name>] - Show or update LLM model configuration",
            style="primary",
        )
        themed_console.print(
            "  /tools      - List active tools with simple descriptions",
            style="primary",
        )
        themed_console.print(
            "  /agents [list|switch|info|reload] - Manage agents",
            style="primary",
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

        themed_console.print("\nKey Bindings:", style="app.header")
        themed_console.print(
            "  Ctrl+A      - Toggle 'Approve All' mode", style="primary"
        )
        themed_console.print("  Ctrl+C      - Abort current operation", style="primary")
        themed_console.print("  Ctrl+D      - Exit QX", style="primary")
        themed_console.print(
            "  Ctrl+E      - Edit input in external editor (vi/vim/nvim/nano/emacs/code)",
            style="primary",
        )
        themed_console.print(
            "  Ctrl+O      - Toggle stdout visibility", style="primary"
        )
        themed_console.print(
            "  Ctrl+P      - Toggle between PLANNING and IMPLEMENTING modes",
            style="primary",
        )
        themed_console.print(
            "  Ctrl+R      - Fuzzy history search (fzf)", style="primary"
        )
        themed_console.print("  Ctrl+T      - Toggle 'Details' mode", style="primary")
        themed_console.print("  F12         - Emergency cancel", style="primary")
        themed_console.print(
            "  Esc+Enter   - Toggle multiline mode (Alt+Enter)", style="primary"
        )

        themed_console.print("\nInteraction Modes:", style="app.header")
        themed_console.print("  • IMPLEMENTING Mode (default):", style="warning")
        themed_console.print(
            "    - Focus on execution, coding, and implementation tasks", style="info"
        )
        themed_console.print("    - Green indicator in footer toolbar", style="info")
        themed_console.print("  • PLANNING Mode:", style="warning")
        themed_console.print(
            "    - Focus on analysis, planning, and strategic thinking", style="info"
        )
        themed_console.print("    - Blue indicator in footer toolbar", style="info")
        themed_console.print("    - Toggle with Ctrl+P", style="info")

        themed_console.print("\nInput Modes:", style="app.header")
        themed_console.print(
            "  • Single-line mode (default): Qx⏵ prompt", style="warning"
        )
        themed_console.print("    - Enter: Submit input", style="info")
        themed_console.print("    - Esc+Enter: Switch to multiline mode", style="info")
        themed_console.print("  • Multiline mode: Qm⏵ prompt", style="warning")
        themed_console.print(
            "    - Enter: Add newline (continue editing)", style="info"
        )
        themed_console.print(
            "    - Alt+Enter: Submit input and return to single-line", style="info"
        )

        themed_console.print("\nFooter Toolbar Status:", style="app.header")
        themed_console.print(
            "  • Mode: Shows current interaction mode (PLANNING/IMPLEMENTING)",
            style="info",
        )
        themed_console.print(
            "  • Details: Shows if AI reasoning is visible (ON/OFF)", style="info"
        )
        themed_console.print(
            "  • Stdout: Shows if command output is visible (ON/OFF)", style="info"
        )
        themed_console.print(
            "  • Approve All: Shows automatic approval status (ON/OFF)", style="info"
        )

        themed_console.print("\nEditor Configuration:", style="app.header")
        themed_console.print(
            "  • Set QX_DEFAULT_EDITOR environment variable to choose editor",
            style="warning",
        )
        themed_console.print("    - Default: nano", style="info")
        themed_console.print(
            "    - Supported: vi, vim, nvim, nano, emacs, code/vscode", style="info"
        )
        themed_console.print(
            "    - Example: export QX_DEFAULT_EDITOR=emacs", style="info"
        )
        themed_console.print(
            "    - Can also be set in qx.conf files (system, user, or project level)",
            style="info",
        )

        themed_console.print("\nAgent Management:", style="app.header")
        themed_console.print(
            "  QX supports modular agents - specialized AI assistants for different tasks.",
            style="warning",
        )
        themed_console.print(
            "  • Use /agents to manage agents (list, switch, info, reload)",
            style="info",
        )
        themed_console.print(
            "  • Built-in agents: qx (default), code_reviewer, devops_automation, documentation_writer, data_processor",
            style="info",
        )
        themed_console.print(
            "  • Create custom agents with YAML files in ./src/qx/agents/ or ~/.config/qx/agents/",
            style="info",
        )
        themed_console.print(
            "  • Set QX_DEFAULT_AGENT environment variable to start with a specific agent",
            style="info",
        )
        themed_console.print(
            "  • Tab completion available for all agent commands and names",
            style="info",
        )
        themed_console.print(
            "  • Full documentation: docs/AGENTS.md",
            style="info",
        )

    else:
        themed_console.print(f"Unknown command: {command_name}", style="error")
        themed_console.print(
            "Available commands: /model, /tools, /agents, /reset, /approve-all, /print, /help",
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
        _handle_model_command(llm_agent, config_manager, command_args)
    elif command_name == "/tools":
        _handle_tools_command(llm_agent)
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
    elif command_name == "/print":  # Added to handle_command as well for consistency
        if command_args:
            themed_console.print(command_args)
        else:
            themed_console.print("Usage: /print <text to print>", style="error")
    else:
        themed_console.print(f"Unknown command: {command_name}", style="error")
        themed_console.print(
            "Available commands: /model, /tools, /reset, /print", style="text.muted"
        )
    return current_message_history
