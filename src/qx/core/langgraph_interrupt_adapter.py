"""
Interrupt adapter for LangGraph supervisor workflow.

This module handles interrupts and approvals in the simplified workflow,
ensuring they go through QX's console manager.
"""

import logging
from typing import Any, Dict, Optional
from langchain_core.messages import HumanMessage

from qx.core.console_manager import get_console_manager
from qx.core.interrupt_bridge import get_interrupt_bridge
from qx.cli.quote_bar_component import render_agent_markdown

logger = logging.getLogger(__name__)


class LangGraphInterruptAdapter:
    """Handles interrupts in the LangGraph supervisor workflow."""
    
    def __init__(self):
        self.console_manager = get_console_manager()
        self.interrupt_bridge = get_interrupt_bridge()
        
    async def handle_supervisor_interrupt(self, interrupt_data: Dict[str, Any]) -> str:
        """
        Handle interrupts from the supervisor workflow.
        
        Args:
            interrupt_data: Data about the interrupt request
            
        Returns:
            User response as string
        """
        interrupt_type = interrupt_data.get("type", "unknown")
        
        if interrupt_type == "user_input":
            # Supervisor is asking for initial input
            return await self._get_user_input(interrupt_data)
        elif interrupt_type == "approval":
            # Tool approval request
            return await self._get_approval(interrupt_data)
        elif interrupt_type == "satisfaction_check":
            # Checking if user is satisfied
            return await self._get_satisfaction_feedback(interrupt_data)
        else:
            logger.warning(f"Unknown interrupt type: {interrupt_type}")
            return ""
            
    async def _get_user_input(self, interrupt_data: Dict[str, Any]) -> str:
        """Get user input through console manager."""
        message = interrupt_data.get("message", "What would you like me to help you with?")
        agent_name = interrupt_data.get("agent_name", "supervisor")
        agent_color = interrupt_data.get("agent_color", "#ff5f00")
        
        # Display prompt using QX styling
        render_agent_markdown(
            f"**{message}**",
            agent_name,
            agent_color=agent_color
        )
        
        # Get input through interrupt bridge
        response = await self.interrupt_bridge.get_user_input(
            prompt="",  # Already displayed above
            agent_name=agent_name
        )
        
        return response
        
    async def _get_approval(self, interrupt_data: Dict[str, Any]) -> str:
        """Get approval for an action."""
        action = interrupt_data.get("action", "perform action")
        details = interrupt_data.get("details", {})
        agent_name = interrupt_data.get("agent_name", "unknown")
        agent_color = interrupt_data.get("agent_color")
        
        # Display approval request
        render_agent_markdown(
            f"**Permission Request**\n\n{action}",
            agent_name,
            agent_color=agent_color
        )
        
        # Get approval through interrupt bridge
        approved = await self.interrupt_bridge.get_approval(
            action=action,
            details=details,
            agent_name=agent_name
        )
        
        return "approved" if approved else "denied"
        
    async def _get_satisfaction_feedback(self, interrupt_data: Dict[str, Any]) -> str:
        """Check if user is satisfied with results."""
        message = interrupt_data.get("message", "Are you satisfied with this result?")
        agent_name = interrupt_data.get("agent_name", "supervisor")
        agent_color = interrupt_data.get("agent_color", "#ff5f00")
        
        # Display satisfaction check
        render_agent_markdown(
            f"**{message}**",
            agent_name,
            agent_color=agent_color
        )
        
        # Get response through interrupt bridge
        response = await self.interrupt_bridge.get_user_input(
            prompt="",  # Already displayed above
            agent_name=agent_name
        )
        
        return response


# Singleton instance
_interrupt_adapter_instance: Optional[LangGraphInterruptAdapter] = None


def get_interrupt_adapter() -> LangGraphInterruptAdapter:
    """Get or create the interrupt adapter instance."""
    global _interrupt_adapter_instance
    
    if _interrupt_adapter_instance is None:
        _interrupt_adapter_instance = LangGraphInterruptAdapter()
        
    return _interrupt_adapter_instance