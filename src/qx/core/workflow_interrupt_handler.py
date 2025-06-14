"""
Workflow interrupt handler for integrating LangGraph interrupts with QX UI systems.

This module provides a custom interrupt handler that bridges LangGraph's interrupt
system with QX's console manager, BorderedMarkdown, and approval systems.
"""

import asyncio
import logging
from typing import Any, Dict, Optional, Union

from qx.core.interrupt_bridge import get_interrupt_bridge
from qx.cli.quote_bar_component import render_agent_markdown

logger = logging.getLogger(__name__)


class WorkflowInterruptHandler:
    """
    Handles LangGraph workflow interrupts by integrating with QX's UI systems.
    
    This class provides methods to handle different types of interrupts while
    maintaining QX's visual styling and user interaction patterns.
    """
    
    def __init__(self):
        self.interrupt_bridge = get_interrupt_bridge()
        logger.info("🎭 WorkflowInterruptHandler initialized")
    
    async def handle_workflow_interrupt(
        self,
        interrupt_value: Dict[str, Any],
        default_response: str = "continue"
    ) -> Union[str, Dict[str, Any]]:
        """
        Handle a workflow interrupt by processing it through QX's UI systems.
        
        Args:
            interrupt_value: The value passed to LangGraph's interrupt()
            default_response: Default response if handling fails
            
        Returns:
            The user's response to resume the workflow
        """
        try:
            logger.info(f"🎭 Processing workflow interrupt: {interrupt_value.get('type', 'unknown')}")
            
            # Extract interrupt details
            interrupt_type = interrupt_value.get("type", "user_input")
            agent_name = interrupt_value.get("agent_name", "qx-director")
            agent_color = interrupt_value.get("agent_color", "#ff5f00")
            
            # Route to appropriate handler
            if interrupt_type == "user_input":
                return await self._handle_user_input_interrupt(interrupt_value, agent_name, agent_color)
            elif interrupt_type == "satisfaction_check":
                return await self._handle_satisfaction_check_interrupt(interrupt_value, agent_name, agent_color)
            elif interrupt_type == "approval_request":
                return await self._handle_approval_request_interrupt(interrupt_value, agent_name, agent_color)
            else:
                return await self._handle_generic_interrupt(interrupt_value, agent_name, agent_color)
                
        except Exception as e:
            logger.error(f"❌ Error handling workflow interrupt: {e}", exc_info=True)
            return default_response
    
    async def _handle_user_input_interrupt(
        self,
        interrupt_value: Dict[str, Any],
        agent_name: str,
        agent_color: str
    ) -> str:
        """Handle user input requests."""
        message = interrupt_value.get("message", "Please provide your input:")
        
        logger.info("⏸️ User input interrupt - showing QX styled prompt")
        
        # Show QX-styled prompt
        render_agent_markdown(
            f"**Input Request**\n\n{message}",
            agent_name,
            agent_color=agent_color
        )
        
        # Use interrupt bridge for consistent input handling
        response = await self.interrupt_bridge.handle_interrupt(
            {
                "type": "user_input",
                "message": message
            },
            agent_name=agent_name,
            agent_color=agent_color
        )
        
        logger.info(f"▶️ User input received: {response[:50]}...")
        return response
    
    async def _handle_satisfaction_check_interrupt(
        self,
        interrupt_value: Dict[str, Any],
        agent_name: str,
        agent_color: str
    ) -> str:
        """Handle satisfaction check requests."""
        message = interrupt_value.get("message", "Are you satisfied with this result?")
        result = interrupt_value.get("result", "")
        
        logger.info("⏸️ Satisfaction check interrupt - showing QX styled result")
        
        # Show result and satisfaction question using QX styling
        if result:
            result_preview = result[:500] + "..." if len(result) > 500 else result
            render_agent_markdown(
                f"**Task Result**\n\n{result_preview}",
                agent_name,
                agent_color=agent_color
            )
        
        render_agent_markdown(
            f"**Satisfaction Check**\n\n{message}",
            agent_name,
            agent_color=agent_color
        )
        
        # Use interrupt bridge for consistent satisfaction check handling
        response = await self.interrupt_bridge.handle_interrupt(
            {
                "type": "satisfaction_check",
                "message": message,
                "result": result
            },
            agent_name=agent_name,
            agent_color=agent_color
        )
        
        logger.info(f"▶️ Satisfaction response: {response}")
        return response
    
    async def _handle_approval_request_interrupt(
        self,
        interrupt_value: Dict[str, Any],
        agent_name: str,
        agent_color: str
    ) -> str:
        """Handle approval request interrupts."""
        operation = interrupt_value.get("operation", "Action")
        description = interrupt_value.get("description", "")
        
        logger.info(f"⏸️ Approval request interrupt: {operation}")
        
        # Use interrupt bridge for consistent approval handling
        response = await self.interrupt_bridge.handle_interrupt(
            {
                "type": "approval_request",
                "operation": operation,
                "description": description,
                "parameter_name": interrupt_value.get("parameter_name", "action"),
                "parameter_value": interrupt_value.get("parameter_value", description)
            },
            agent_name=agent_name,
            agent_color=agent_color
        )
        
        logger.info(f"▶️ Approval response: {response}")
        return response
    
    async def _handle_generic_interrupt(
        self,
        interrupt_value: Dict[str, Any],
        agent_name: str,
        agent_color: str
    ) -> str:
        """Handle generic interrupts."""
        message = interrupt_value.get("message", "Workflow paused for user input")
        
        logger.info("⏸️ Generic interrupt - showing QX styled message")
        
        # Show generic message using QX styling
        render_agent_markdown(
            f"**Workflow Paused**\n\n{message}",
            agent_name,
            agent_color=agent_color
        )
        
        # Use interrupt bridge for generic handling
        response = await self.interrupt_bridge.handle_interrupt(
            {
                "type": "generic",
                "message": message
            },
            agent_name=agent_name,
            agent_color=agent_color
        )
        
        logger.info(f"▶️ Generic response: {response}")
        return response


# Global interrupt handler instance
_workflow_interrupt_handler: Optional[WorkflowInterruptHandler] = None


def get_workflow_interrupt_handler() -> WorkflowInterruptHandler:
    """Get or create the global workflow interrupt handler."""
    global _workflow_interrupt_handler
    if _workflow_interrupt_handler is None:
        _workflow_interrupt_handler = WorkflowInterruptHandler()
    return _workflow_interrupt_handler


async def handle_langgraph_interrupt(
    interrupt_value: Dict[str, Any],
    default_response: str = "continue"
) -> Union[str, Dict[str, Any]]:
    """
    Convenience function to handle LangGraph interrupts with QX integration.
    
    This function provides the main entry point for processing LangGraph
    interrupt() calls through QX's UI systems.
    """
    handler = get_workflow_interrupt_handler()
    return await handler.handle_workflow_interrupt(interrupt_value, default_response)