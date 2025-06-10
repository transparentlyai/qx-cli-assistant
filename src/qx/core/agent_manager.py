# src/qx/core/agent_manager.py
"""
Agent lifecycle management with session integration and console communication.
Manages agent loading, switching, and execution while preserving existing patterns.
"""

import asyncio
import logging
import os
import threading
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass

from qx.core.schemas import AgentConfig, AgentExecutionMode
from qx.core.agent_loader import AgentLoadResult, get_agent_loader
from qx.core.async_utils import TaskTracker
from qx.core.console_manager import get_console_manager
from qx.core.session_manager import get_or_create_session_filename

logger = logging.getLogger(__name__)


@dataclass
class AgentSession:
    """Represents an active agent session"""

    agent_name: str
    agent_config: AgentConfig
    session_id: str
    created_at: datetime
    status: str = "active"  # active, paused, stopped, error
    task: Optional[asyncio.Task] = None
    context: Optional[Dict[str, str]] = None


class AgentExecutionError(Exception):
    """Raised when agent execution encounters an error"""

    pass


class AgentManager:
    """
    Manages agent lifecycle, sessions, and execution.
    Integrates with existing session management and console systems.
    """

    def __init__(self):
        self._agent_loader = get_agent_loader()
        self._current_agent_session: Optional[AgentSession] = None
        self._autonomous_agents: Dict[str, AgentSession] = {}
        self._task_tracker = TaskTracker()
        self._lock = asyncio.Lock()
        self._console_manager = None  # Lazy initialization

        # Callbacks for agent lifecycle events
        self._on_agent_loaded: List[Callable[[AgentConfig], None]] = []
        self._on_agent_switched: List[
            Callable[[str, str], None]
        ] = []  # old_name, new_name
        self._on_agent_error: List[Callable[[str, Exception], None]] = []

    def _get_console_manager(self):
        """Lazy initialization of console manager to avoid circular imports"""
        if self._console_manager is None:
            try:
                self._console_manager = get_console_manager()
            except Exception as e:
                logger.warning(f"Console manager not available: {e}")
        return self._console_manager

    def _console_print(self, message: str, source_id: str = "AgentManager", **kwargs):
        """Safe console printing with fallback"""
        try:
            console_manager = self._get_console_manager()
            if (
                console_manager
                and hasattr(console_manager, "_running")
                and console_manager._running
            ):
                console_manager.print(message, source_identifier=source_id, **kwargs)
            else:
                # Fallback to logger (safer during initialization)
                logger.info(f"[{source_id}] {message}")
        except Exception as e:
            # Always fall back to logger on any error
            logger.error(f"Console print failed: {e}")
            logger.info(f"[{source_id}] {message}")

    async def load_agent(
        self,
        agent_name: str,
        context: Optional[Dict[str, str]] = None,
        cwd: Optional[str] = None,
    ) -> AgentLoadResult:
        """
        Load agent configuration by name.

        Args:
            agent_name: Name of the agent to load
            context: Template context for placeholder replacement
            cwd: Current working directory for path resolution

        Returns:
            AgentLoadResult with success/error information
        """
        async with self._lock:
            try:
                result = self._agent_loader.load_agent(
                    agent_name, context=context, cwd=cwd
                )

                if result.success:
                    # Fire loaded callbacks
                    for callback in self._on_agent_loaded:
                        try:
                            callback(result.agent)
                        except Exception as e:
                            logger.error(f"Error in agent loaded callback: {e}")

                    self._console_print(
                        f"Loaded agent '{agent_name}' from {result.source_path}",
                        style="green",
                    )
                else:
                    self._console_print(
                        f"Failed to load agent '{agent_name}': {result.error}",
                        style="red",
                    )

                return result

            except Exception as e:
                error_msg = f"Unexpected error loading agent '{agent_name}': {e}"
                logger.error(error_msg, exc_info=True)
                return AgentLoadResult(error=error_msg)

    async def switch_agent(
        self,
        agent_name: str,
        context: Optional[Dict[str, str]] = None,
        cwd: Optional[str] = None,
    ) -> AgentLoadResult:
        """
        Switch to a different agent, updating the current session.

        Args:
            agent_name: Name of the agent to switch to
            context: Template context for placeholder replacement
            cwd: Current working directory for path resolution

        Returns:
            AgentLoadResult with success/error information
        """
        async with self._lock:
            old_agent_name = (
                self._current_agent_session.agent_name
                if self._current_agent_session
                else "none"
            )

            # Load the new agent
            result = await self.load_agent(agent_name, context=context, cwd=cwd)

            if result.success and result.agent is not None:
                # Create new agent session
                try:
                    session_filename = await get_or_create_session_filename()
                    session_id = (
                        session_filename.stem
                        if session_filename
                        else f"session_{datetime.now().isoformat()}"
                    )
                except Exception:
                    session_id = f"session_{datetime.now().isoformat()}"

                self._current_agent_session = AgentSession(
                    agent_name=agent_name,
                    agent_config=result.agent,
                    session_id=session_id,
                    created_at=datetime.now(),
                    context=context,
                )

                # Fire switched callbacks
                for callback in self._on_agent_switched:
                    try:
                        callback(old_agent_name, agent_name)
                    except Exception as e:
                        logger.error(f"Error in agent switched callback: {e}")

                self._console_print(
                    f"Switched to agent '{agent_name}' (was '{old_agent_name}')",
                    style="blue",
                )

            return result

    async def get_current_agent(self) -> Optional[AgentConfig]:
        """Get the currently active agent configuration."""
        async with self._lock:
            return (
                self._current_agent_session.agent_config
                if self._current_agent_session
                else None
            )

    async def get_current_agent_name(self) -> Optional[str]:
        """Get the currently active agent name."""
        async with self._lock:
            return (
                self._current_agent_session.agent_name
                if self._current_agent_session
                else None
            )

    def _set_current_agent_session(
        self, agent_name: str, agent_config: Optional[AgentConfig]
    ):
        """Internal method to set current agent session without async overhead."""
        from datetime import datetime

        # Create agent session synchronously for startup
        if agent_config is None:
            logger.error(
                f"Cannot set agent session for {agent_name}: agent_config is None"
            )
            return

        session_id = f"session_{datetime.now().isoformat()}"
        self._current_agent_session = AgentSession(
            agent_name=agent_name,
            agent_config=agent_config,
            session_id=session_id,
            created_at=datetime.now(),
            context={},
        )

    def set_active_llm_agent(self, llm_agent):
        """Set the active LLM agent instance."""
        self._active_llm_agent = llm_agent

    def get_active_llm_agent(self):
        """Get the active LLM agent instance."""
        return getattr(self, "_active_llm_agent", None)

    async def switch_llm_agent(self, agent_name: str, mcp_manager) -> bool:
        """Switch the active LLM agent to a different agent configuration."""
        try:
            # Load the new agent
            result = await self.load_agent(
                agent_name,
                context={
                    "user_context": os.environ.get("QX_USER_CONTEXT", ""),
                    "project_context": os.environ.get("QX_PROJECT_CONTEXT", ""),
                    "project_files": os.environ.get("QX_PROJECT_FILES", ""),
                    "ignore_paths": "",
                },
                cwd=os.getcwd(),
            )

            if not result.success:
                return False

            # Create new LLM agent with the new configuration
            from qx.core.llm_utils import initialize_agent_with_mcp

            new_llm_agent = await initialize_agent_with_mcp(
                mcp_manager=mcp_manager, agent_config=result.agent
            )

            if new_llm_agent:
                # Update the agent session
                self._set_current_agent_session(agent_name, result.agent)

                # Replace the active LLM agent
                old_agent = self.get_active_llm_agent()
                self.set_active_llm_agent(new_llm_agent)

                # Clean up old agent if needed
                if old_agent:
                    try:
                        await old_agent.cleanup()
                    except Exception as e:
                        logger.error(f"Error cleaning up old LLM agent: {e}")

                return True

        except Exception as e:
            logger.error(f"Error switching LLM agent: {e}", exc_info=True)

        return False

    def discover_agents(self, cwd: Optional[str] = None) -> List[str]:
        """Discover all available agents with project context awareness."""
        # Always use current working directory if not provided for project agent discovery
        if cwd is None:
            cwd = os.getcwd()
        return self._agent_loader.discover_agents(cwd=cwd)

    def get_agent_info(
        self, agent_name: str, cwd: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Get information about an agent without loading it."""
        # Always use current working directory if not provided for project agent discovery
        if cwd is None:
            cwd = os.getcwd()
        return self._agent_loader.get_agent_info(agent_name, cwd=cwd)

    async def list_agents(self, cwd: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all available agents with their information."""
        # Always use current working directory if not provided for project agent discovery
        if cwd is None:
            cwd = os.getcwd()
        agent_names = self.discover_agents(cwd=cwd)
        agents_info = []

        for name in agent_names:
            info = self.get_agent_info(name, cwd=cwd)
            if info:
                # Add status information
                info["is_current"] = (
                    self._current_agent_session
                    and self._current_agent_session.agent_name == name
                )
                info["is_autonomous"] = name in self._autonomous_agents
                agents_info.append(info)

        return agents_info

    async def reload_agent(
        self,
        agent_name: Optional[str] = None,
        context: Optional[Dict[str, str]] = None,
        cwd: Optional[str] = None,
    ) -> AgentLoadResult:
        """
        Reload agent configuration from disk.
        If no agent_name provided, reloads the current agent.
        """
        async with self._lock:
            if not agent_name:
                if not self._current_agent_session:
                    return AgentLoadResult(error="No current agent to reload")
                agent_name = self._current_agent_session.agent_name
                context = context or self._current_agent_session.context

            # Clear cache and reload
            result = self._agent_loader.reload_agent(
                agent_name, context=context, cwd=cwd
            )

            if result.success:
                # Update current session if this is the active agent
                if (
                    self._current_agent_session
                    and self._current_agent_session.agent_name == agent_name
                ):
                    self._current_agent_session.agent_config = result.agent
                    self._current_agent_session.context = context

                # Update autonomous agents if applicable
                if agent_name in self._autonomous_agents:
                    self._autonomous_agents[agent_name].agent_config = result.agent
                    self._autonomous_agents[agent_name].context = context

                self._console_print(f"Reloaded agent '{agent_name}'", style="green")
            else:
                self._console_print(
                    f"Failed to reload agent '{agent_name}': {result.error}",
                    style="red",
                )

            return result

    async def start_autonomous_agent(
        self,
        agent_name: str,
        context: Optional[Dict[str, str]] = None,
        cwd: Optional[str] = None,
        task_handler: Optional[Callable] = None,
    ) -> bool:
        """
        Start an autonomous agent in the background.

        Args:
            agent_name: Name of the agent to start
            context: Template context for placeholder replacement
            cwd: Current working directory
            task_handler: Optional async function to handle agent tasks

        Returns:
            True if started successfully, False otherwise
        """
        try:
            # Load agent configuration
            result = await self.load_agent(agent_name, context=context, cwd=cwd)
            if not result.success or result.agent is None:
                self._console_print(
                    f"Cannot start autonomous agent '{agent_name}': {result.error or 'No agent config loaded'}",
                    style="red",
                )
                return False

            agent_config = result.agent

            # Check if agent supports autonomous mode
            if agent_config.execution.mode not in [
                AgentExecutionMode.AUTONOMOUS,
                AgentExecutionMode.HYBRID,
            ]:
                self._console_print(
                    f"Agent '{agent_name}' does not support autonomous mode (mode: {agent_config.execution.mode})",
                    style="yellow",
                )
                return False

            # Check if already running
            if agent_name in self._autonomous_agents:
                self._console_print(
                    f"Autonomous agent '{agent_name}' is already running",
                    style="yellow",
                )
                return False

            # Create agent session
            session_id = f"autonomous_{agent_name}_{datetime.now().isoformat()}"
            agent_session = AgentSession(
                agent_name=agent_name,
                agent_config=agent_config,
                session_id=session_id,
                created_at=datetime.now(),
                context=context,
            )

            # Start autonomous task
            async def autonomous_task():
                try:
                    self._console_print(
                        f"Starting autonomous agent '{agent_name}'",
                        source_id=agent_config.execution.console.source_identifier
                        or agent_name.upper(),
                    )

                    # Execute lifecycle hook
                    if agent_config.lifecycle.on_start:
                        self._console_print(
                            agent_config.lifecycle.on_start,
                            source_id=agent_config.execution.console.source_identifier
                            or agent_name.upper(),
                        )

                    # Run the task handler if provided
                    if task_handler:
                        await task_handler(agent_session)
                    else:
                        # Default autonomous behavior - just keep alive
                        while True:
                            await asyncio.sleep(
                                agent_config.execution.autonomous_config.poll_interval
                            )

                            # Check if still running
                            if agent_name not in self._autonomous_agents:
                                break

                except asyncio.CancelledError:
                    self._console_print(
                        f"Autonomous agent '{agent_name}' was cancelled",
                        source_id=agent_config.execution.console.source_identifier
                        or agent_name.upper(),
                    )
                    raise
                except Exception as e:
                    logger.error(
                        f"Error in autonomous agent '{agent_name}': {e}", exc_info=True
                    )

                    # Execute error lifecycle hook
                    if agent_config.lifecycle.on_error:
                        self._console_print(
                            agent_config.lifecycle.on_error,
                            source_id=agent_config.execution.console.source_identifier
                            or agent_name.upper(),
                        )

                    # Fire error callbacks
                    for callback in self._on_agent_error:
                        try:
                            callback(agent_name, e)
                        except Exception as callback_error:
                            logger.error(
                                f"Error in agent error callback: {callback_error}"
                            )

                    raise
                finally:
                    # Execute shutdown lifecycle hook
                    if agent_config.lifecycle.on_shutdown:
                        self._console_print(
                            agent_config.lifecycle.on_shutdown,
                            source_id=agent_config.execution.console.source_identifier
                            or agent_name.upper(),
                        )

                    # Clean up
                    if agent_name in self._autonomous_agents:
                        del self._autonomous_agents[agent_name]

            # Create and track the task
            task = await self._task_tracker.create_task(
                autonomous_task(), name=f"autonomous_agent_{agent_name}"
            )
            agent_session.task = task

            # Store the session
            self._autonomous_agents[agent_name] = agent_session

            self._console_print(
                f"Started autonomous agent '{agent_name}' with session ID: {session_id}",
                style="green",
            )

            return True

        except Exception as e:
            error_msg = f"Failed to start autonomous agent '{agent_name}': {e}"
            logger.error(error_msg, exc_info=True)
            self._console_print(error_msg, style="red")
            return False

    async def stop_autonomous_agent(self, agent_name: str) -> bool:
        """
        Stop a running autonomous agent.

        Args:
            agent_name: Name of the agent to stop

        Returns:
            True if stopped successfully, False otherwise
        """
        try:
            if agent_name not in self._autonomous_agents:
                self._console_print(
                    f"Autonomous agent '{agent_name}' is not running", style="yellow"
                )
                return False

            agent_session = self._autonomous_agents[agent_name]

            if agent_session.task and not agent_session.task.done():
                agent_session.task.cancel()
                try:
                    await asyncio.wait_for(agent_session.task, timeout=5.0)
                except (asyncio.CancelledError, asyncio.TimeoutError):
                    pass

            # Remove from tracking
            if agent_name in self._autonomous_agents:
                del self._autonomous_agents[agent_name]

            self._console_print(
                f"Stopped autonomous agent '{agent_name}'", style="blue"
            )

            return True

        except Exception as e:
            error_msg = f"Failed to stop autonomous agent '{agent_name}': {e}"
            logger.error(error_msg, exc_info=True)
            self._console_print(error_msg, style="red")
            return False

    async def get_autonomous_agents_status(self) -> List[Dict[str, Any]]:
        """Get status of all autonomous agents."""
        status_list = []

        for agent_name, agent_session in self._autonomous_agents.items():
            status = {
                "name": agent_name,
                "session_id": agent_session.session_id,
                "created_at": agent_session.created_at.isoformat(),
                "status": agent_session.status,
                "task_status": "running"
                if agent_session.task and not agent_session.task.done()
                else "stopped",
                "config": {
                    "mode": agent_session.agent_config.execution.mode.value,
                    "max_concurrent_tasks": agent_session.agent_config.execution.autonomous_config.max_concurrent_tasks,
                    "poll_interval": agent_session.agent_config.execution.autonomous_config.poll_interval,
                },
            }
            status_list.append(status)

        return status_list

    def add_agent_loaded_callback(self, callback: Callable[[AgentConfig], None]):
        """Add callback for when an agent is loaded."""
        self._on_agent_loaded.append(callback)

    def add_agent_switched_callback(self, callback: Callable[[str, str], None]):
        """Add callback for when agent is switched."""
        self._on_agent_switched.append(callback)

    def add_agent_error_callback(self, callback: Callable[[str, Exception], None]):
        """Add callback for when agent encounters an error."""
        self._on_agent_error.append(callback)

    def refresh_agent_discovery(self, cwd: Optional[str] = None) -> List[str]:
        """Refresh agent discovery, useful when project context changes or new agents are added."""
        if cwd is None:
            cwd = os.getcwd()
        return self._agent_loader.refresh_discovery(cwd=cwd)
        
    async def cleanup(self):
        """Clean up all agent resources."""
        try:
            # Stop all autonomous agents
            agent_names = list(self._autonomous_agents.keys())
            for agent_name in agent_names:
                await self.stop_autonomous_agent(agent_name)

            # Clean up task tracker
            await self._task_tracker.cancel_all()

            # Clear cache
            self._agent_loader.clear_cache()

            logger.info("Agent manager cleanup completed")

        except Exception as e:
            logger.error(f"Error during agent manager cleanup: {e}", exc_info=True)


# Global singleton instance
_agent_manager = None
_manager_lock = threading.Lock()


def get_agent_manager() -> AgentManager:
    """Get the global AgentManager instance."""
    global _agent_manager
    with _manager_lock:
        if _agent_manager is None:
            _agent_manager = AgentManager()
        return _agent_manager
