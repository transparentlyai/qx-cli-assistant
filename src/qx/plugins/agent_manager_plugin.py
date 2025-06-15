# src/qx/plugins/agent_manager_plugin.py
"""
Agent Manager Plugin for QX.
Provides tools for managing, switching, and monitoring agents.
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from rich.console import Console as RichConsole
from rich.table import Table
from rich.panel import Panel

# Import only types at module level to avoid circular dependencies

logger = logging.getLogger(__name__)


def _managed_plugin_print(content, source_id: str = "AgentManager", **kwargs) -> None:
    """Thread-safe console output helper."""
    try:
        from qx.core.console_manager import get_console_manager
        from qx.cli.console import themed_console

        manager = get_console_manager()
        if manager and manager._running:
            style = kwargs.get("style")
            markup = kwargs.get("markup", True)
            end = kwargs.get("end", "\n")
            manager.print(
                content,
                style=style,
                markup=markup,
                end=end,
                console=themed_console,
                source_identifier=source_id,
            )
            return
    except Exception:
        pass

    # Fallback to direct themed_console usage
    from qx.cli.console import themed_console

    if source_id:
        content = f"[{source_id}] {content}"
    themed_console.print(content, **kwargs)


# Input/Output Models for Agent Management Tools


class ListAgentsInput(BaseModel):
    """Input parameters for listing available agents."""

    show_details: bool = Field(
        default=False,
        description="Whether to show detailed information about each agent",
    )
    filter_mode: Optional[str] = Field(
        default=None,
        description="Filter agents by execution mode: 'interactive', 'autonomous', or 'hybrid'",
    )


class ListAgentsOutput(BaseModel):
    """Output for listing available agents."""

    success: bool
    message: str
    agents: List[Dict[str, Any]] = Field(default_factory=list)
    current_agent: Optional[str] = None


class SwitchAgentInput(BaseModel):
    """Input parameters for switching to a different agent."""

    agent_name: str = Field(description="Name of the agent to switch to")
    reload: bool = Field(
        default=False, description="Whether to reload the agent configuration from disk"
    )


class SwitchAgentOutput(BaseModel):
    """Output for agent switching operation."""

    success: bool
    message: str
    previous_agent: Optional[str] = None
    current_agent: Optional[str] = None


class AgentStatusInput(BaseModel):
    """Input parameters for getting agent status."""

    agent_name: Optional[str] = Field(
        default=None,
        description="Name of specific agent to get status for (current agent if not specified)",
    )
    include_autonomous: bool = Field(
        default=True, description="Whether to include autonomous agent status"
    )


class AgentStatusOutput(BaseModel):
    """Output for agent status information."""

    success: bool
    message: str
    current_agent: Optional[Dict[str, Any]] = None
    autonomous_agents: List[Dict[str, Any]] = Field(default_factory=list)


class StartAutonomousAgentInput(BaseModel):
    """Input parameters for starting autonomous agent."""

    agent_name: str = Field(description="Name of the agent to start autonomously")
    context: Optional[Dict[str, str]] = Field(
        default=None, description="Template context for agent initialization"
    )


class StartAutonomousAgentOutput(BaseModel):
    """Output for autonomous agent start operation."""

    success: bool
    message: str
    agent_name: Optional[str] = None
    session_id: Optional[str] = None


class StopAutonomousAgentInput(BaseModel):
    """Input parameters for stopping autonomous agent."""

    agent_name: str = Field(description="Name of the autonomous agent to stop")


class StopAutonomousAgentOutput(BaseModel):
    """Output for autonomous agent stop operation."""

    success: bool
    message: str
    agent_name: Optional[str] = None


class ReloadAgentInput(BaseModel):
    """Input parameters for reloading agent configuration."""

    agent_name: Optional[str] = Field(
        default=None,
        description="Name of agent to reload (current agent if not specified)",
    )


class ReloadAgentOutput(BaseModel):
    """Output for agent reload operation."""

    success: bool
    message: str
    agent_name: Optional[str] = None
    reloaded_from: Optional[str] = None




# Tool Functions


async def list_agents_tool(
    console: RichConsole, args: ListAgentsInput
) -> ListAgentsOutput:
    """List all available agents with their information."""
    try:
        # Lazy import to avoid circular dependencies during plugin loading
        from qx.core.agent_manager import get_agent_manager

        agent_manager = get_agent_manager()
        agents_info = await agent_manager.list_agents()
        current_agent_name = await agent_manager.get_current_agent_name()

        # Filter by mode if specified
        if args.filter_mode:
            mode_filter = args.filter_mode.lower()
            agents_info = [
                agent
                for agent in agents_info
                if agent.get("execution_mode", "").lower() == mode_filter
            ]

        # Create display table
        table = Table(title="Available Agents")
        table.add_column("Name", style="cyan", no_wrap=True)
        table.add_column("Description", style="white")
        table.add_column("Mode", style="green")
        table.add_column("Status", style="yellow")

        if args.show_details:
            table.add_column("Tools", style="blue")
            table.add_column("Model", style="magenta")

        for agent in agents_info:
            name = agent["name"]
            description = agent.get("description", "No description")[:50]
            mode = agent.get("execution_mode", "unknown")

            # Status indicators
            status_parts = []
            if agent.get("is_current"):
                status_parts.append("CURRENT")
            if agent.get("is_autonomous"):
                status_parts.append("AUTONOMOUS")
            status = " | ".join(status_parts) if status_parts else "Available"

            row = [name, description, mode, status]

            if args.show_details:
                tools = ", ".join(agent.get("tools", [])[:3])  # Show first 3 tools
                if len(agent.get("tools", [])) > 3:
                    tools += "..."
                model = agent.get("model", {}).get("name", "Unknown")[:30]
                row.extend([tools, model])

            table.add_row(*row)

        _managed_plugin_print(table)

        return ListAgentsOutput(
            success=True,
            message=f"Found {len(agents_info)} agents",
            agents=agents_info,
            current_agent=current_agent_name,
        )

    except Exception as e:
        error_msg = f"Failed to list agents: {e}"
        logger.error(error_msg, exc_info=True)
        _managed_plugin_print(error_msg, style="red")

        return ListAgentsOutput(success=False, message=error_msg)


async def switch_agent_tool(
    console: RichConsole, args: SwitchAgentInput
) -> SwitchAgentOutput:
    """Switch to a different agent."""
    try:
        from qx.core.agent_manager import get_agent_manager

        agent_manager = get_agent_manager()
        previous_agent_name = await agent_manager.get_current_agent_name()

        # Reload agent if requested
        if args.reload:
            reload_result = await agent_manager.reload_agent(args.agent_name)
            if not reload_result.success:
                return SwitchAgentOutput(
                    success=False,
                    message=f"Failed to reload agent '{args.agent_name}': {reload_result.error}",
                    previous_agent=previous_agent_name,
                )

        # Switch to the agent
        result = await agent_manager.switch_agent(args.agent_name)

        if result.success:
            _managed_plugin_print(
                f"Successfully switched from '{previous_agent_name}' to '{args.agent_name}'",
                style="green",
            )

            return SwitchAgentOutput(
                success=True,
                message=f"Switched to agent '{args.agent_name}'",
                previous_agent=previous_agent_name,
                current_agent=args.agent_name,
            )
        else:
            _managed_plugin_print(
                f"Failed to switch to agent '{args.agent_name}': {result.error}",
                style="red",
            )

            return SwitchAgentOutput(
                success=False,
                message=result.error or "Failed to switch agent",
                previous_agent=previous_agent_name,
            )

    except Exception as e:
        error_msg = f"Failed to switch agent: {e}"
        logger.error(error_msg, exc_info=True)
        _managed_plugin_print(error_msg, style="red")

        return SwitchAgentOutput(success=False, message=error_msg)


async def agent_status_tool(
    console: RichConsole, args: AgentStatusInput
) -> AgentStatusOutput:
    """Get status information for agents."""
    try:
        from qx.core.agent_manager import get_agent_manager

        agent_manager = get_agent_manager()

        # Get current agent info
        current_agent_name = await agent_manager.get_current_agent_name()
        current_agent_info = None

        if current_agent_name:
            current_agent_info = {"name": current_agent_name, "status": "active"}

            # Get additional info if specific agent requested or current agent
            target_agent = args.agent_name or current_agent_name
            if target_agent == current_agent_name:
                agent_info = agent_manager.get_agent_info(target_agent)
                if agent_info:
                    current_agent_info.update(agent_info)

        # Get autonomous agents status
        autonomous_agents = []
        if args.include_autonomous:
            autonomous_agents = await agent_manager.get_autonomous_agents_status()

        # Create status display
        if current_agent_info:
            panel_content = (
                f"[bold cyan]Current Agent:[/bold cyan] {current_agent_info['name']}\n"
            )
            panel_content += (
                f"[bold]Status:[/bold] {current_agent_info.get('status', 'Unknown')}\n"
            )

            if "execution_mode" in current_agent_info:
                panel_content += (
                    f"[bold]Mode:[/bold] {current_agent_info['execution_mode']}\n"
                )

            if "model" in current_agent_info:
                model_info = current_agent_info["model"]
                if isinstance(model_info, dict):
                    model_name = model_info.get("name", "Unknown")
                else:
                    model_name = str(model_info)
                panel_content += f"[bold]Model:[/bold] {model_name}\n"

            _managed_plugin_print(Panel(panel_content, title="Agent Status"))

        if autonomous_agents:
            table = Table(title="Autonomous Agents")
            table.add_column("Name", style="cyan")
            table.add_column("Status", style="green")
            table.add_column("Created", style="yellow")
            table.add_column("Mode", style="blue")

            for agent in autonomous_agents:
                created_at = datetime.fromisoformat(agent["created_at"]).strftime(
                    "%H:%M:%S"
                )
                table.add_row(
                    agent["name"], agent["status"], created_at, agent["config"]["mode"]
                )

            _managed_plugin_print(table)

        return AgentStatusOutput(
            success=True,
            message="Agent status retrieved successfully",
            current_agent=current_agent_info,
            autonomous_agents=autonomous_agents,
        )

    except Exception as e:
        error_msg = f"Failed to get agent status: {e}"
        logger.error(error_msg, exc_info=True)
        _managed_plugin_print(error_msg, style="red")

        return AgentStatusOutput(success=False, message=error_msg)


async def start_autonomous_agent_tool(
    console: RichConsole, args: StartAutonomousAgentInput
) -> StartAutonomousAgentOutput:
    """Start an autonomous agent in the background."""
    try:
        from qx.core.agent_manager import get_agent_manager

        agent_manager = get_agent_manager()

        # Start the autonomous agent
        success = await agent_manager.start_autonomous_agent(
            agent_name=args.agent_name, context=args.context
        )

        if success:
            _managed_plugin_print(
                f"Started autonomous agent '{args.agent_name}'", style="green"
            )

            return StartAutonomousAgentOutput(
                success=True,
                message=f"Autonomous agent '{args.agent_name}' started successfully",
                agent_name=args.agent_name,
                session_id=f"autonomous_{args.agent_name}_{datetime.now().isoformat()}",
            )
        else:
            return StartAutonomousAgentOutput(
                success=False,
                message=f"Failed to start autonomous agent '{args.agent_name}'",
            )

    except Exception as e:
        error_msg = f"Failed to start autonomous agent: {e}"
        logger.error(error_msg, exc_info=True)
        _managed_plugin_print(error_msg, style="red")

        return StartAutonomousAgentOutput(success=False, message=error_msg)


async def stop_autonomous_agent_tool(
    console: RichConsole, args: StopAutonomousAgentInput
) -> StopAutonomousAgentOutput:
    """Stop a running autonomous agent."""
    try:
        from qx.core.agent_manager import get_agent_manager

        agent_manager = get_agent_manager()

        # Stop the autonomous agent
        success = await agent_manager.stop_autonomous_agent(args.agent_name)

        if success:
            _managed_plugin_print(
                f"Stopped autonomous agent '{args.agent_name}'", style="blue"
            )

            return StopAutonomousAgentOutput(
                success=True,
                message=f"Autonomous agent '{args.agent_name}' stopped successfully",
                agent_name=args.agent_name,
            )
        else:
            return StopAutonomousAgentOutput(
                success=False,
                message=f"Failed to stop autonomous agent '{args.agent_name}' (may not be running)",
            )

    except Exception as e:
        error_msg = f"Failed to stop autonomous agent: {e}"
        logger.error(error_msg, exc_info=True)
        _managed_plugin_print(error_msg, style="red")

        return StopAutonomousAgentOutput(success=False, message=error_msg)


async def reload_agent_tool(
    console: RichConsole, args: ReloadAgentInput
) -> ReloadAgentOutput:
    """Reload agent configuration from disk."""
    try:
        from qx.core.agent_manager import get_agent_manager

        agent_manager = get_agent_manager()

        # Get target agent name
        target_agent = args.agent_name
        if not target_agent:
            target_agent = await agent_manager.get_current_agent_name()
            if not target_agent:
                return ReloadAgentOutput(
                    success=False,
                    message="No current agent to reload and no agent name specified",
                )

        # Reload the agent
        result = await agent_manager.reload_agent(target_agent)

        if result.success:
            _managed_plugin_print(
                f"Reloaded agent '{target_agent}' from {result.source_path}",
                style="green",
            )

            return ReloadAgentOutput(
                success=True,
                message=f"Agent '{target_agent}' reloaded successfully",
                agent_name=target_agent,
                reloaded_from=str(result.source_path) if result.source_path else None,
            )
        else:
            _managed_plugin_print(
                f"Failed to reload agent '{target_agent}': {result.error}", style="red"
            )

            return ReloadAgentOutput(
                success=False,
                message=result.error or "Failed to reload agent",
                agent_name=target_agent,
            )

    except Exception as e:
        error_msg = f"Failed to reload agent: {e}"
        logger.error(error_msg, exc_info=True)
        _managed_plugin_print(error_msg, style="red")

        return ReloadAgentOutput(success=False, message=error_msg)


