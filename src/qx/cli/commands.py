import logging
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from openai.types.chat import ChatCompletionMessageParam, ChatCompletionSystemMessageParam, ChatCompletionUserMessageParam
from rich.text import Text

import qx.core.user_prompts
from qx.cli.theme import themed_console
from qx.core.agent_manager import get_agent_manager
from qx.core.config_manager import ConfigManager
from qx.core.constants import QX_VERSION
from qx.core.models import MODELS
from qx.core.llm import QXLLMAgent, initialize_llm_agent, query_llm
from qx.core.session_manager import reset_session, save_session_async, get_or_create_session_filename
from qx.core.paths import QX_SESSIONS_DIR

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


async def _handle_save_session_command(
    session_name: str,
    config_manager: ConfigManager,
    current_message_history: Optional[List[ChatCompletionMessageParam]] = None
):
    """
    Handle /save-session command to save the current session with a custom name.
    """
    if not session_name:
        themed_console.print("Usage: /save-session <session-name>", style="error")
        return
    
    # Sanitize the session name
    session_name = session_name.strip()
    # Replace spaces with underscores and remove invalid filename characters
    safe_session_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in session_name)
    
    # Check if .Q directory exists
    if not QX_SESSIONS_DIR.parent.is_dir():
        themed_console.print("'.Q' directory not found. Cannot save session.", style="error")
        return
    
    # Create sessions directory if it doesn't exist
    QX_SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Get current agent manager
    agent_manager = get_agent_manager()
    current_agent_name = await agent_manager.get_current_agent_name()
    
    # Get all agent histories
    all_agent_histories = agent_manager.get_all_agent_histories()
    
    # Make sure current agent's history is up to date
    if current_agent_name and current_message_history:
        all_agent_histories[current_agent_name] = current_message_history
    
    if not all_agent_histories:
        themed_console.print("No conversation history to save.", style="warning")
        return
    
    # Create filename with timestamp and custom name
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_filename = QX_SESSIONS_DIR / f"qx_session_{timestamp}_{safe_session_name}.json"
    
    try:
        # Prepare session data
        import json
        session_data = {
            "format_version": "2.0",
            "current_agent": current_agent_name,
            "session_name": session_name,
            "saved_at": datetime.now().isoformat(),
            "agents": {}
        }
        
        for agent_name, history in all_agent_histories.items():
            # Exclude system messages and serialize
            agent_history = [
                msg for msg in history if (
                    (hasattr(msg, "role") and msg.role != "system") or
                    (isinstance(msg, dict) and msg.get("role") != "system")
                )
            ]
            serializable_history = []
            for msg in agent_history:
                if hasattr(msg, "model_dump") and callable(getattr(msg, "model_dump")):
                    serializable_history.append(msg.model_dump())
                elif hasattr(msg, "__dict__"):
                    serializable_history.append(msg.__dict__)
                elif hasattr(msg, "items"):
                    serializable_history.append(dict(msg))
                else:
                    serializable_history.append(msg)
            session_data["agents"][agent_name] = serializable_history
        
        # Write the session file
        session_filename.write_text(
            json.dumps(session_data, indent=2), encoding="utf-8"
        )
        
        themed_console.print(
            f"✓ Session saved as '{session_name}' to:\n  {session_filename}",
            style="success"
        )
        
    except Exception as e:
        logger.error(f"Failed to save session: {e}", exc_info=True)
        themed_console.print(f"Failed to save session: {e}", style="error")


async def _handle_agents_command(command_args: str, config_manager: ConfigManager,
                                current_message_history: Optional[List[ChatCompletionMessageParam]] = None) -> Optional[List[ChatCompletionMessageParam]]:
    """
    Handle agent management commands.
    Returns updated message history if it was modified, None otherwise.
    """
    parts = command_args.strip().split() if command_args else []
    subcommand = parts[0] if parts else "list"

    agent_manager = get_agent_manager()

    if subcommand == "list":
        # Use current working directory for project-specific agent discovery
        agents_info = await agent_manager.list_user_agents(cwd=os.getcwd())
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
                description = agent.get("description", "No description available")
                # Truncate long descriptions for clean display
                if len(description) > 80:
                    description = description[:77] + "..."
                mode = agent.get("execution_mode", "unknown")
                status = " [CURRENT]" if agent.get("is_current") else ""

                text = Text()
                text.append(f"  📁 {name}: ", style="blue")
                text.append(f"{description}", style="white")
                text.append(f" ({mode}{status})", style="dim white")
                themed_console.print(text)

        # Show built-in agents
        if development_agents:
            themed_console.print("\n🛠️  Built-in Agents:", style="bold green")
            for agent in development_agents:
                name = agent["name"]
                description = agent.get("description", "No description available")
                # Truncate long descriptions for clean display
                if len(description) > 80:
                    description = description[:77] + "..."
                mode = agent.get("execution_mode", "unknown")
                status = " [CURRENT]" if agent.get("is_current") else ""

                text = Text()
                text.append(f"  - {name}: ", style="primary")
                text.append(f"{description}", style="white")
                text.append(f" ({mode}{status})", style="dim white")
                themed_console.print(text)

        # Show user agents
        if user_agents:
            themed_console.print(
                "\n👤 User Agents (~/.config/qx/agents/):", style="bold yellow"
            )
            for agent in user_agents:
                name = agent["name"]
                description = agent.get("description", "No description available")
                # Truncate long descriptions for clean display
                if len(description) > 80:
                    description = description[:77] + "..."
                mode = agent.get("execution_mode", "unknown")
                status = " [CURRENT]" if agent.get("is_current") else ""

                text = Text()
                text.append(f"  - {name}: ", style="primary")
                text.append(f"{description}", style="white")
                text.append(f" ({mode}{status})", style="dim white")
                themed_console.print(text)

        # Show system agents
        if system_agents:
            themed_console.print(
                "\n🌐 System Agents (/etc/qx/agents/):", style="bold white"
            )
            for agent in system_agents:
                name = agent["name"]
                description = agent.get("description", "No description available")
                # Truncate long descriptions for clean display
                if len(description) > 80:
                    description = description[:77] + "..."
                mode = agent.get("execution_mode", "unknown")
                status = " [CURRENT]" if agent.get("is_current") else ""

                text = Text()
                text.append(f"  - {name}: ", style="primary")
                text.append(f"{description}", style="white")
                text.append(f" ({mode}{status})", style="dim white")
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
            # Check if agent is a system agent (not available to users)
            agent_info = agent_manager.get_agent_info(agent_name, cwd=os.getcwd())
            if agent_info and agent_info.get("type") == "system":
                themed_console.print(
                    f"Cannot switch to system agent '{agent_name}'. System agents are not available to users.",
                    style="error"
                )
                return
            
            # Save current agent's message history before switching
            current_agent_name = await agent_manager.get_current_agent_name()
            if current_agent_name and current_message_history:
                agent_manager.save_agent_message_history(current_agent_name, current_message_history)
                logger.debug(f"Saved {len(current_message_history)} messages for agent '{current_agent_name}'")

            # Attempt to switch the LLM agent
            success = await agent_manager.switch_llm_agent(
                agent_name, config_manager.mcp_manager
            )

            if success:
                # Show simple agent switch message
                current_agent = await agent_manager.get_current_agent()
                if current_agent:
                    agent_display_name = current_agent.name or agent_name
                    themed_console.print(
                        f"You are now talking to {agent_display_name}",
                        style="text.muted",
                    )
                    
                    # Get this agent's existing message history (if any)
                    existing_history = agent_manager.get_current_message_history()
                    if existing_history:
                        logger.info(f"Agent '{agent_name}' resumed with {len(existing_history)} previous messages")
                    
                    # Process initial_query if defined in agent config
                    if hasattr(current_agent, 'initial_query') and current_agent.initial_query:
                        logger.debug(f"Processing initial_query for agent '{agent_name}': {current_agent.initial_query}")
                        
                        # Get the active LLM agent instance
                        active_llm_agent = agent_manager.get_active_llm_agent()
                        if active_llm_agent:
                            try:
                                # Import the system prompt loading function
                                from qx.core.llm_components.prompts import load_and_format_system_prompt
                                
                                # Get this agent's existing conversation history
                                existing_history = agent_manager.get_current_message_history()
                                system_prompt = load_and_format_system_prompt(current_agent)
                                
                                # Create message history for this agent
                                if existing_history and len(existing_history) > 0:
                                    # This agent has existing history - append the initial query
                                    initial_message_history = list(existing_history)
                                    
                                    # Add initial query at the end
                                    initial_message_history.append(
                                        ChatCompletionUserMessageParam(
                                            role="user", content=current_agent.initial_query
                                        )
                                    )
                                else:
                                    # No existing history, create fresh
                                    initial_message_history = [
                                        ChatCompletionSystemMessageParam(
                                            role="system", content=system_prompt
                                        ),
                                        ChatCompletionUserMessageParam(
                                            role="user", content=current_agent.initial_query
                                        ),
                                    ]
                                
                                # Send the initial query to the LLM (this will display the response)
                                result = await query_llm(
                                    active_llm_agent,
                                    current_agent.initial_query,
                                    message_history=initial_message_history,
                                    console=themed_console,
                                    add_user_message_to_history=False,  # Already added above
                                    config_manager=config_manager,
                                )
                                
                                # Update agent manager with the new message history that includes the agent switch interaction
                                if result and hasattr(result, 'message_history'):
                                    agent_manager.set_current_message_history(result.message_history)
                                elif existing_history:
                                    # If no new history returned, at least preserve the conversation context
                                    agent_manager.set_current_message_history(initial_message_history)
                                
                            except Exception as e:
                                logger.error(f"Error processing initial_query for agent '{agent_name}': {e}")
                                themed_console.print(
                                    f"Warning: Failed to process initial query for agent '{agent_name}': {e}",
                                    style="warning"
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
            agent_info = agent_manager.get_agent_info(
                current_agent_name, cwd=os.getcwd()
            )
            if agent_info and "path" in agent_info:
                agent_path = Path(agent_info["path"])
                if ".Q/agents" in str(agent_path):
                    themed_console.print(
                        f"Source: {agent_path} (Project Agent)", style="dim blue"
                    )
                elif "src/qx/agents" in str(agent_path):
                    themed_console.print(
                        f"Source: {agent_path} (Development Agent)", style="dim green"
                    )
                elif ".config/qx/agents" in str(agent_path):
                    themed_console.print(
                        f"Source: {agent_path} (User Agent)", style="dim yellow"
                    )
                else:
                    themed_console.print(f"Source: {agent_path}", style="dim white")
        else:
            themed_console.print("No current agent loaded", style="warning")

    elif subcommand == "reload":
        if len(parts) > 1:
            # Reload specific agent
            reload_agent_name = parts[1]
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
        else:
            # Reload all agents
            results = await agent_manager.reload_all_agents(cwd=os.getcwd())
            success_count = sum(1 for success in results.values() if success)
            failed_agents = [name for name, success in results.items() if not success]
            
            if failed_agents:
                themed_console.print(
                    f"Reloaded {success_count}/{len(results)} agents successfully. "
                    f"Failed agents: {', '.join(failed_agents)}",
                    style="warning"
                )
            else:
                themed_console.print(
                    f"Successfully reloaded all {success_count} agents from disk",
                    style="info"
                )

    elif subcommand == "refresh":
        # Refresh agent discovery to pick up new project agents
        agent_names = agent_manager.refresh_agent_discovery(cwd=os.getcwd())
        themed_console.print(
            f"Refreshed agent discovery. Found {len(agent_names)} agents.", style="info"
        )

        # Show any new project agents
        project_agent_names = []
        for name in agent_names:
            agent_info = agent_manager.get_agent_info(name, cwd=os.getcwd())
            if agent_info and ".Q/agents" in agent_info.get("path", ""):
                project_agent_names.append(name)

        if project_agent_names:
            themed_console.print(
                f"Project agents: {', '.join(project_agent_names)}", style="blue"
            )
        else:
            themed_console.print(
                "No project agents found in .Q/agents/", style="dim white"
            )

    elif subcommand == "load":
        if len(parts) < 2:
            themed_console.print("Usage: /agents load <agent_name>", style="error")
            return

        agent_name = parts[1]
        
        # Check if agent exists and is not a system agent
        agent_info = agent_manager.get_agent_info(agent_name, cwd=os.getcwd())
        if not agent_info:
            themed_console.print(f"Agent '{agent_name}' not found", style="error")
            return
            
        if agent_info.get("type") == "system":
            themed_console.print(
                f"Cannot load system agent '{agent_name}'. System agents are not available to users.",
                style="error"
            )
            return
            
        # Check if it's a built-in agent
        if agent_manager._agent_loader.is_builtin_agent(agent_name, cwd=os.getcwd()):
            themed_console.print(
                f"Agent '{agent_name}' is a built-in agent and is already available.",
                style="warning"
            )
            return
        
        # Get the current agent's message history
        current_agent_name = await agent_manager.get_current_agent_name()
        if not current_agent_name:
            themed_console.print("No active agent to load project agent for", style="error")
            return
            
        current_history = agent_manager.get_current_message_history()
        if current_history is None:
            current_history = []
        
        # Create the system message
        agent_description = agent_info.get("description", "A project-specific agent")
        system_message = {
            "role": "system",
            "content": f"The '{agent_name}' agent is now available: {agent_description}"
        }
        
        # Check if already loaded
        if any(msg.get("content") == system_message["content"] for msg in current_history if isinstance(msg, dict)):
            themed_console.print(f"Agent '{agent_name}' is already loaded", style="warning")
            return
        
        # Inject the system message
        current_history.append(system_message)
        agent_manager.set_current_message_history(current_history)
        
        themed_console.print(
            f"Loaded project agent '{agent_name}' - now available to the current agent",
            style="success"
        )
        
        # Return the updated message history
        return current_history
        
    elif subcommand == "unload":
        if len(parts) < 2:
            themed_console.print("Usage: /agents unload <agent_name>", style="error")
            return

        agent_name = parts[1]
        
        # Check if it's a built-in agent
        if agent_manager._agent_loader.is_builtin_agent(agent_name, cwd=os.getcwd()):
            themed_console.print(
                f"Cannot unload built-in agent '{agent_name}'.",
                style="error"
            )
            return
        
        # Get the current agent's message history
        current_agent_name = await agent_manager.get_current_agent_name()
        if not current_agent_name:
            themed_console.print("No active agent to unload project agent from", style="error")
            return
            
        current_history = agent_manager.get_current_message_history()
        if not current_history:
            themed_console.print(f"Agent '{agent_name}' is not loaded", style="warning")
            return
        
        # Remove the system message for this agent
        original_length = len(current_history)
        current_history = [
            msg for msg in current_history 
            if not (isinstance(msg, dict) and 
                    msg.get("role") == "system" and 
                    f"The '{agent_name}' agent is now available:" in msg.get("content", ""))
        ]
        
        if len(current_history) == original_length:
            themed_console.print(f"Agent '{agent_name}' is not loaded", style="warning")
            return
        
        # Update the message history
        agent_manager.set_current_message_history(current_history)
        
        themed_console.print(
            f"Unloaded project agent '{agent_name}' - no longer available to the current agent",
            style="success"
        )
        
        # Return the updated message history
        return current_history

    else:
        themed_console.print(f"Unknown agents subcommand: {subcommand}", style="error")
        themed_console.print(
            "Available subcommands: list, switch, info, reload, refresh, load, unload",
            style="text.muted",
        )
    
    # Return None to indicate no changes to message history
    return None


def _show_header(llm_agent: QXLLMAgent):
    """Displays the header with version, model, and cwd."""
    themed_console.print(
        f"\n[dim]Qx ver:[info]{QX_VERSION}[/] | [dim]model:[/][info]{os.path.basename(llm_agent.model_name)}[/] | [dim]cwd:[/][info]{os.getcwd()}[/]"
    )


def _handle_clear_command(llm_agent: QXLLMAgent):
    """Clears the console and displays the header."""
    themed_console.clear()
    _show_header(llm_agent)


async def _handle_inline_command(
    command_input: str, llm_agent: QXLLMAgent, config_manager: ConfigManager,
    current_message_history: Optional[List[ChatCompletionMessageParam]] = None
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
        updated_history = await _handle_agents_command(command_args, config_manager, current_message_history)
        if updated_history is not None:
            return updated_history
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
    elif command_name == "/save-session":
        await _handle_save_session_command(command_args, config_manager, current_message_history)
    elif command_name == "/help":
        themed_console.print("QX - Multi-Agent AI Assistant", style="app.header")
        
        # Core Commands
        themed_console.print("\nCore Commands:", style="app.header")
        themed_console.print(
            "  /model [<name>]  - Show or update LLM model configuration",
            style="primary",
        )
        themed_console.print(
            "  /agents [cmd]    - Manage agents (list|switch|info|reload|refresh)",
            style="primary",
        )
        themed_console.print(
            "  /tools           - List active tools with descriptions",
            style="primary",
        )
        themed_console.print(
            "  /reset           - Reset session and clear message history", 
            style="primary"
        )
        themed_console.print(
            "  /approve-all     - Activate 'approve all' mode for tool confirmations",
            style="primary",
        )
        themed_console.print(
            "  /print <text>    - Print text to the console", 
            style="primary"
        )
        themed_console.print(
            "  /save-session <name> - Save current session with a custom name",
            style="primary"
        )
        
        
        # Help
        themed_console.print("\nHelp:", style="app.header")
        themed_console.print("  /help                    - Show this help message", style="primary")
        
        # Agent Management Details
        themed_console.print("\nAgent Management Commands:", style="app.header")
        themed_console.print("  /agents list             - List all available agents", style="primary")
        themed_console.print("  /agents switch <name>    - Switch to a different agent", style="primary")
        themed_console.print("  /agents info             - Show current agent details", style="primary")
        themed_console.print("  /agents load <name>      - Make project agent available to AI", style="primary")
        themed_console.print("  /agents unload <name>    - Remove project agent from AI knowledge", style="primary")
        themed_console.print("  /agents reload           - Reload ALL agents from disk", style="primary")
        themed_console.print("  /agents reload <name>    - Reload specific agent from disk", style="primary")
        themed_console.print("  /agents refresh          - Refresh agent discovery", style="primary")
        
        themed_console.print("\n  Agent Configuration Features:", style="dim white")
        themed_console.print("    • initial_query: Automatic greeting when switching agents", style="dim cyan")
        themed_console.print("    • Cache invalidation: /agents reload picks up YAML changes", style="dim cyan")
        themed_console.print("    • Project-specific: Place agents in .Q/agents/ directory", style="dim cyan")

        themed_console.print("\nKey Bindings:", style="app.header")
        themed_console.print(
            "  Ctrl+A / F5 - Toggle 'Approve All' mode", style="primary"
        )
        themed_console.print("  Ctrl+C      - Abort current operation", style="primary")
        themed_console.print("  Ctrl+D      - Exit QX", style="primary")
        themed_console.print(
            "  Ctrl+E      - Edit input in external editor (vi/vim/nvim/nano/emacs/code)",
            style="primary",
        )
        themed_console.print(
            "  F1          - Toggle between PLANNING and IMPLEMENTING modes",
            style="primary",
        )
        themed_console.print(
            "  F2          - Toggle between MULTI and SINGLE agent modes", style="primary"
        )
        themed_console.print("  F3          - Toggle 'Details' mode", style="primary")
        themed_console.print(
            "  F4          - Toggle stdout and stderr visibility", style="primary"
        )
        themed_console.print(
            "  Ctrl+R      - Fuzzy history search (fzf)", style="primary"
        )
        themed_console.print("  F12         - Emergency cancel", style="primary")
        themed_console.print(
            "  Esc+Enter   - Toggle multiline mode (Alt+Enter)", style="primary"
        )

        themed_console.print("\nAgent Operation Modes:", style="app.header")
        themed_console.print("  • MULTI Mode (default):", style="warning")
        themed_console.print(
            "    - Agents can delegate tasks to other specialized agents", style="info"
        )
        themed_console.print("    - Enable complex multi-agent workflows", style="info")
        themed_console.print("    - Blue 'MULTI' indicator in footer toolbar", style="info")
        themed_console.print("  • SINGLE Mode:", style="warning")
        themed_console.print(
            "    - Only the current agent operates, no delegation", style="info"
        )
        themed_console.print("    - Simpler, focused single-agent operation", style="info")
        themed_console.print("    - Blue 'SINGLE' indicator in footer toolbar", style="info")
        themed_console.print("    - Toggle with F2", style="info")

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
        themed_console.print("    - Toggle with F1", style="info")

        themed_console.print("\nInput Modes:", style="app.header")
        themed_console.print(
            "  • Single-line mode (default): Qx⏵ prompt (color matches active agent)",
            style="warning",
        )
        themed_console.print("    - Enter: Submit input", style="info")
        themed_console.print("    - Esc+Enter: Switch to multiline mode", style="info")
        themed_console.print("  • Multiline mode: Qxm⏵ prompt (blue)", style="warning")
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
            "  • Agent Mode: Shows MULTI or SINGLE agent operation mode", style="info"
        )
        themed_console.print(
            "  • StdOE: Shows if command output is visible (ON/OFF)", style="info"
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
            "  • Create custom agents with YAML files in ~/.config/qx/agents/ or <project-path>/.Q/agents/",
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

        themed_console.print("\nDirectives System:", style="app.header")
        themed_console.print(
            "  Use @directive syntax to inject reusable prompts into your messages.",
            style="warning",
        )
        themed_console.print(
            "  • Usage: Type @<directive-name> in your message (e.g., @reviewer, @planner)",
            style="info",
        )
        themed_console.print(
            "  • Built-in directives: @worklogger, @reviewer, @planner",
            style="info",
        )
        themed_console.print(
            "  • Create custom directives: Place .md files in .Q/directives/ in your project",
            style="info",
        )
        themed_console.print(
            "  • Tab completion: Type @ and press Tab to see available directives",
            style="info",
        )
        themed_console.print(
            "  • Project directives override built-in ones with the same name",
            style="info",
        )
        themed_console.print(
            "  • Full documentation: docs/DIRECTIVES.md",
            style="info",
        )


    else:
        themed_console.print(f"Unknown command: {command_name}", style="error")
        themed_console.print(
            "Available commands: /model, /tools, /agents, /reset, /approve-all, /print, /save-session, /help",
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
            "Available commands: /model, /tools, /reset, /print",
            style="text.muted",
        )
    return current_message_history
