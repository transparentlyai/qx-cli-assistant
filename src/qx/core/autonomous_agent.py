# src/qx/core/autonomous_agent.py
"""
Autonomous agent execution engine for independent task processing.
Integrates with existing async infrastructure and console management.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from enum import Enum

from qx.core.schemas import AgentConfig
from qx.core.async_utils import TaskTracker
from qx.core.console_manager import get_console_manager
from qx.core.llm import QXLLMAgent
from qx.core.llm_utils import initialize_agent_with_mcp
from qx.core.mcp_manager import MCPManager

logger = logging.getLogger(__name__)


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class AutonomousTask:
    """Represents a task for autonomous agent execution"""

    id: str
    description: str
    content: str
    priority: TaskPriority = TaskPriority.MEDIUM
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[str] = None
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 2
    timeout: int = 300  # seconds

    @property
    def duration(self) -> Optional[timedelta]:
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        return None

    @property
    def is_expired(self) -> bool:
        if self.started_at:
            return (datetime.now() - self.started_at).total_seconds() > self.timeout
        return False


class AutonomousAgentRunner:
    """
    Manages autonomous agent execution with task queuing, scheduling, and monitoring.
    Integrates with existing console manager and async infrastructure.
    """

    def __init__(self, agent_config: AgentConfig, mcp_manager: MCPManager):
        self.agent_config = agent_config
        self.mcp_manager = mcp_manager
        self.agent_name = agent_config.name or "autonomous_agent"
        self.source_id = (
            agent_config.execution.console.source_identifier or self.agent_name.upper()
        )

        # Task management
        self._task_queue: asyncio.Queue[AutonomousTask] = asyncio.Queue()
        self._active_tasks: Dict[str, AutonomousTask] = {}
        self._completed_tasks: List[AutonomousTask] = []
        self._task_history: List[AutonomousTask] = []

        # Execution state
        self._running = False
        self._llm_agent: Optional[QXLLMAgent] = None
        self._task_tracker = TaskTracker()
        self._console_manager = None
        self._worker_tasks: Set[asyncio.Task] = set()

        # Configuration
        self.max_concurrent_tasks = (
            agent_config.execution.autonomous_config.max_concurrent_tasks
        )
        self.poll_interval = agent_config.execution.autonomous_config.poll_interval
        self.heartbeat_interval = (
            agent_config.execution.autonomous_config.heartbeat_interval
        )
        self.auto_restart = agent_config.execution.autonomous_config.auto_restart

        # Statistics
        self._stats: Dict[str, Any] = {
            "tasks_processed": 0,
            "tasks_failed": 0,
            "total_runtime": 0.0,
            "start_time": None,
            "last_heartbeat": None,
        }

    def _get_console_manager(self):
        """Lazy initialization of console manager"""
        if self._console_manager is None:
            try:
                self._console_manager = get_console_manager()
            except Exception as e:
                logger.warning(f"Console manager not available: {e}")
        return self._console_manager

    def _console_print(self, message: str, **kwargs):
        """Safe console printing with fallback"""
        try:
            console_manager = self._get_console_manager()
            if console_manager and console_manager._running:
                console_manager.print(
                    message, source_identifier=self.source_id, **kwargs
                )
            else:
                logger.info(f"[{self.source_id}] {message}")
        except Exception as e:
            logger.error(f"Console print failed: {e}")
            logger.info(f"[{self.source_id}] {message}")

    async def initialize(self) -> bool:
        """Initialize the autonomous agent runner"""
        try:
            self._console_print("Initializing autonomous agent runner...", style="blue")

            # Initialize LLM agent
            self._llm_agent = await initialize_agent_with_mcp(
                mcp_manager=self.mcp_manager, agent_config=self.agent_config
            )

            if not self._llm_agent:
                self._console_print("Failed to initialize LLM agent", style="red")
                return False

            # Execute startup lifecycle hook
            if self.agent_config.lifecycle.on_start:
                self._console_print(f"Startup: {self.agent_config.lifecycle.on_start}")

            self._stats["start_time"] = datetime.now().timestamp()
            self._console_print(
                "Autonomous agent runner initialized successfully", style="green"
            )
            return True

        except Exception as e:
            error_msg = f"Failed to initialize autonomous agent runner: {e}"
            logger.error(error_msg, exc_info=True)
            self._console_print(error_msg, style="red")
            return False

    async def start(self) -> bool:
        """Start the autonomous agent runner"""
        if self._running:
            self._console_print("Agent runner is already running", style="yellow")
            return False

        if not await self.initialize():
            return False

        try:
            self._running = True
            self._console_print(
                f"Starting autonomous agent '{self.agent_name}'", style="green"
            )

            # Start worker tasks
            for i in range(self.max_concurrent_tasks):
                worker_task = await self._task_tracker.create_task(
                    self._worker_loop(worker_id=i),
                    name=f"autonomous_worker_{i}",
                    error_handler=self._handle_worker_error,
                )
                self._worker_tasks.add(worker_task)

            # Start heartbeat task
            heartbeat_task = await self._task_tracker.create_task(
                self._heartbeat_loop(),
                name="autonomous_heartbeat",
                error_handler=self._handle_heartbeat_error,
            )
            self._worker_tasks.add(heartbeat_task)

            self._console_print(
                f"Started {len(self._worker_tasks)} worker tasks", style="blue"
            )
            return True

        except Exception as e:
            error_msg = f"Failed to start autonomous agent runner: {e}"
            logger.error(error_msg, exc_info=True)
            self._console_print(error_msg, style="red")
            await self.stop()
            return False

    async def stop(self) -> bool:
        """Stop the autonomous agent runner"""
        if not self._running:
            return True

        try:
            self._console_print("Stopping autonomous agent runner...", style="yellow")
            self._running = False

            # Cancel all worker tasks
            for task in self._worker_tasks:
                if not task.done():
                    task.cancel()

            # Wait for tasks to complete with timeout
            if self._worker_tasks:
                try:
                    await asyncio.wait_for(
                        asyncio.gather(*self._worker_tasks, return_exceptions=True),
                        timeout=10.0,
                    )
                except asyncio.TimeoutError:
                    self._console_print(
                        "Timeout waiting for worker tasks to stop", style="yellow"
                    )

            self._worker_tasks.clear()

            # Execute shutdown lifecycle hook
            if self.agent_config.lifecycle.on_shutdown:
                self._console_print(
                    f"Shutdown: {self.agent_config.lifecycle.on_shutdown}"
                )

            # Update stats
            if self._stats["start_time"]:
                self._stats["total_runtime"] = (
                    datetime.now().timestamp() - self._stats["start_time"]
                )

            self._console_print("Autonomous agent runner stopped", style="blue")
            return True

        except Exception as e:
            error_msg = f"Error stopping autonomous agent runner: {e}"
            logger.error(error_msg, exc_info=True)
            self._console_print(error_msg, style="red")
            return False

    async def add_task(self, task: AutonomousTask) -> bool:
        """Add a task to the execution queue"""
        try:
            await self._task_queue.put(task)
            self._console_print(
                f"Added task: {task.description} (Priority: {task.priority.value})"
            )

            # Execute task received lifecycle hook
            if self.agent_config.lifecycle.on_task_received:
                self._console_print(
                    f"Task received: {self.agent_config.lifecycle.on_task_received}"
                )

            return True

        except Exception as e:
            error_msg = f"Failed to add task: {e}"
            logger.error(error_msg, exc_info=True)
            self._console_print(error_msg, style="red")
            return False

    async def _worker_loop(self, worker_id: int):
        """Main worker loop for processing tasks"""
        worker_name = f"Worker-{worker_id}"

        while self._running:
            try:
                # Wait for task with timeout
                try:
                    task = await asyncio.wait_for(
                        self._task_queue.get(), timeout=self.poll_interval
                    )
                except asyncio.TimeoutError:
                    continue

                # Process the task
                await self._process_task(task, worker_name)

            except asyncio.CancelledError:
                logger.debug(f"{worker_name} cancelled")
                break
            except Exception as e:
                logger.error(f"Error in {worker_name}: {e}", exc_info=True)
                await asyncio.sleep(1)  # Brief pause on error

    async def _process_task(self, task: AutonomousTask, worker_name: str):
        """Process a single task"""
        task_id = task.id

        try:
            # Update task status
            task.status = TaskStatus.RUNNING
            task.started_at = datetime.now()
            self._active_tasks[task_id] = task

            self._console_print(
                f"{worker_name} processing task: {task.description}", style="blue"
            )

            # Process with LLM agent
            if self._llm_agent:
                try:
                    # Create a timeout for the task
                    result = await asyncio.wait_for(
                        self._execute_task_with_llm(task), timeout=task.timeout
                    )

                    # Task completed successfully
                    task.status = TaskStatus.COMPLETED
                    task.completed_at = datetime.now()
                    task.result = result

                    self._console_print(
                        f"{worker_name} completed task: {task.description}",
                        style="green",
                    )
                    self._stats["tasks_processed"] += 1

                except asyncio.TimeoutError:
                    # Task timed out
                    task.status = TaskStatus.FAILED
                    task.completed_at = datetime.now()
                    task.error = f"Task timed out after {task.timeout} seconds"

                    self._console_print(
                        f"{worker_name} task timed out: {task.description}", style="red"
                    )
                    self._stats["tasks_failed"] += 1

                except Exception as e:
                    # Task execution failed
                    task.status = TaskStatus.FAILED
                    task.completed_at = datetime.now()
                    task.error = str(e)

                    logger.error(f"Task execution failed: {e}", exc_info=True)
                    self._console_print(
                        f"{worker_name} task failed: {task.description} - {e}",
                        style="red",
                    )
                    self._stats["tasks_failed"] += 1

                    # Execute error lifecycle hook
                    if self.agent_config.lifecycle.on_error:
                        self._console_print(
                            f"Error handling: {self.agent_config.lifecycle.on_error}"
                        )
            else:
                task.status = TaskStatus.FAILED
                task.completed_at = datetime.now()
                task.error = "LLM agent not available"
                self._stats["tasks_failed"] += 1

        except Exception as e:
            # Unexpected error
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.now()
            task.error = f"Unexpected error: {e}"
            logger.error(
                f"Unexpected error processing task {task_id}: {e}", exc_info=True
            )
            self._stats["tasks_failed"] += 1

        finally:
            # Clean up
            if task_id in self._active_tasks:
                del self._active_tasks[task_id]

            self._completed_tasks.append(task)
            self._task_history.append(task)

            # Limit history size
            if len(self._task_history) > 1000:
                self._task_history = self._task_history[-500:]

    async def _execute_task_with_llm(self, task: AutonomousTask) -> str:
        """Execute task using the LLM agent"""
        if not self._llm_agent:
            raise RuntimeError("LLM agent not available")

        # Prepare the prompt for the task
        prompt = f"""
Task: {task.description}

Instructions: {task.content}

Please complete this task autonomously. Provide a clear response with your actions and results.
"""

        # Execute with the LLM agent
        response = await self._llm_agent.run(user_input=prompt, message_history=None)

        return response

    async def _heartbeat_loop(self):
        """Heartbeat loop for monitoring and health checks"""
        while self._running:
            try:
                await asyncio.sleep(self.heartbeat_interval)

                current_time = datetime.now()
                self._stats["last_heartbeat"] = current_time.timestamp()

                # Log heartbeat
                active_count = len(self._active_tasks)
                queue_size = self._task_queue.qsize()

                logger.debug(
                    f"Heartbeat - Active: {active_count}, Queue: {queue_size}, "
                    f"Processed: {self._stats['tasks_processed']}, "
                    f"Failed: {self._stats['tasks_failed']}"
                )

                # Check for expired tasks
                expired_tasks = [
                    task for task in self._active_tasks.values() if task.is_expired
                ]

                for task in expired_tasks:
                    self._console_print(
                        f"Task expired: {task.description}", style="yellow"
                    )
                    task.status = TaskStatus.FAILED
                    task.error = "Task expired"

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in heartbeat loop: {e}", exc_info=True)

    def _handle_worker_error(self, error: Exception):
        """Handle worker task errors"""
        logger.error(f"Worker task error: {error}", exc_info=True)
        self._console_print(f"Worker error: {error}", style="red")

    def _handle_heartbeat_error(self, error: Exception):
        """Handle heartbeat task errors"""
        logger.error(f"Heartbeat task error: {error}", exc_info=True)

    def get_status(self) -> Dict[str, Any]:
        """Get current status of the autonomous agent runner"""
        return {
            "agent_name": self.agent_name,
            "running": self._running,
            "active_tasks": len(self._active_tasks),
            "queue_size": self._task_queue.qsize(),
            "worker_count": len(self._worker_tasks),
            "stats": self._stats.copy(),
            "config": {
                "max_concurrent_tasks": self.max_concurrent_tasks,
                "poll_interval": self.poll_interval,
                "heartbeat_interval": self.heartbeat_interval,
                "auto_restart": self.auto_restart,
            },
        }

    def get_task_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent task history"""
        recent_tasks = self._task_history[-limit:] if limit > 0 else self._task_history

        return [
            {
                "id": task.id,
                "description": task.description,
                "status": task.status.value,
                "priority": task.priority.value,
                "created_at": task.created_at.isoformat(),
                "started_at": task.started_at.isoformat() if task.started_at else None,
                "completed_at": task.completed_at.isoformat()
                if task.completed_at
                else None,
                "duration_seconds": task.duration.total_seconds()
                if task.duration
                else None,
                "retry_count": task.retry_count,
                "error": task.error,
            }
            for task in recent_tasks
        ]
