"""
Workflow execution context for QX unified LangGraph integration.

This module provides a context system that allows tools and components
to determine if they're executing within a unified LangGraph workflow
and should use workflow-aware interrupts instead of direct console interaction.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Global workflow context state
_workflow_context: Optional[Dict[str, Any]] = None
_context_lock = asyncio.Lock()


class WorkflowContext:
    """
    Context object representing current workflow execution state.
    
    This context is used by tools and components to determine how to
    handle user interactions (direct console vs. workflow interrupts).
    """
    
    def __init__(
        self,
        workflow_id: str,
        agent_name: str,
        agent_color: Optional[str] = None,
        thread_id: Optional[str] = None,
        use_interrupts: bool = True
    ):
        self.workflow_id = workflow_id
        self.agent_name = agent_name
        self.agent_color = agent_color
        self.thread_id = thread_id
        self.use_interrupts = use_interrupts
        
        logger.debug(f"🔧 Created WorkflowContext: {workflow_id}, agent={agent_name}")
    
    def should_use_interrupts(self) -> bool:
        """Check if this context should use workflow interrupts."""
        return self.use_interrupts
    
    def get_agent_info(self) -> tuple[str, Optional[str]]:
        """Get agent name and color for UI styling."""
        return self.agent_name, self.agent_color
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary for serialization."""
        return {
            "workflow_id": self.workflow_id,
            "agent_name": self.agent_name,
            "agent_color": self.agent_color,
            "thread_id": self.thread_id,
            "use_interrupts": self.use_interrupts
        }


async def set_workflow_context(context: Optional[WorkflowContext]) -> None:
    """Set the current workflow context."""
    global _workflow_context
    async with _context_lock:
        _workflow_context = context.to_dict() if context else None
        if context:
            logger.info(f"🎯 Set workflow context: {context.workflow_id}")
        else:
            logger.info("🔄 Cleared workflow context")


async def get_workflow_context() -> Optional[WorkflowContext]:
    """Get the current workflow context."""
    global _workflow_context
    async with _context_lock:
        if _workflow_context:
            return WorkflowContext(**_workflow_context)
        return None


async def is_in_workflow() -> bool:
    """Check if currently executing within a workflow."""
    context = await get_workflow_context()
    return context is not None


async def should_use_workflow_interrupts() -> bool:
    """Check if tools should use workflow interrupts instead of direct console interaction."""
    context = await get_workflow_context()
    return context.should_use_interrupts() if context else False


@asynccontextmanager
async def workflow_execution_context(
    workflow_id: str,
    agent_name: str,
    agent_color: Optional[str] = None,
    thread_id: Optional[str] = None,
    use_interrupts: bool = True
):
    """
    Async context manager for workflow execution.
    
    Usage:
        async with workflow_execution_context("unified", "qx-director", "#ff5f00"):
            # Tool executions within this context will use workflow interrupts
            result = await some_tool_execution()
    """
    context = WorkflowContext(
        workflow_id=workflow_id,
        agent_name=agent_name,
        agent_color=agent_color,
        thread_id=thread_id,
        use_interrupts=use_interrupts
    )
    
    # Set context
    await set_workflow_context(context)
    
    try:
        logger.info(f"🎬 ENTER workflow context: {workflow_id}")
        yield context
    finally:
        logger.info(f"🎬 EXIT workflow context: {workflow_id}")
        # Clear context
        await set_workflow_context(None)


async def get_current_agent_info() -> tuple[Optional[str], Optional[str]]:
    """Get current agent name and color from workflow context."""
    context = await get_workflow_context()
    if context:
        return context.get_agent_info()
    return None, None


# Legacy compatibility for synchronous code
def get_workflow_context_sync() -> Optional[WorkflowContext]:
    """Synchronous version of get_workflow_context (for backward compatibility)."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If we're already in an async context, we can't use asyncio.run
            # Create a new task and wait for it
            task = asyncio.create_task(get_workflow_context())
            return None  # Return None in sync context when async loop is running
        else:
            return asyncio.run(get_workflow_context())
    except RuntimeError:
        # No event loop running
        return None


def is_in_workflow_sync() -> bool:
    """Synchronous version of is_in_workflow (for backward compatibility)."""
    context = get_workflow_context_sync()
    return context is not None