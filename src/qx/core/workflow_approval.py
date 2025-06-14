"""
Workflow-aware approval system for QX plugins.

This module provides approval handling that works both in workflow contexts
(using LangGraph interrupts) and direct console contexts (using ApprovalHandler).
"""

import logging
from typing import Any, Optional, Tuple

from rich.console import Console
from qx.core.approval_handler import ApprovalHandler
from qx.core.workflow_context import get_workflow_context, should_use_workflow_interrupts

logger = logging.getLogger(__name__)


class WorkflowAwareApprovalHandler:
    """
    Approval handler that automatically selects between workflow interrupts
    and direct console interaction based on the current execution context.
    """
    
    def __init__(self, console: Console, use_console_manager: bool = True):
        self.console = console
        self.approval_handler = ApprovalHandler(console, use_console_manager)
        logger.debug("🎭 WorkflowAwareApprovalHandler initialized")
    
    async def request_approval(
        self,
        operation: str,
        parameter_name: str,
        parameter_value: str,
        prompt_message: str,
        content_to_display: Optional[Any] = None,
    ) -> Tuple[str, Optional[str]]:
        """
        Request approval using workflow interrupts or direct console interaction.
        
        Args:
            operation: The operation being performed (e.g., "Write file", "Execute command")
            parameter_name: The name of the parameter (e.g., "path", "command")
            parameter_value: The value of the parameter
            prompt_message: The question to ask the user
            content_to_display: Optional content to display
            
        Returns:
            A tuple of (status, chosen_key)
        """
        try:
            # Check if we're in a workflow context that should use interrupts
            if await should_use_workflow_interrupts():
                return await self._handle_workflow_approval(
                    operation, parameter_name, parameter_value, 
                    prompt_message, content_to_display
                )
            else:
                # Use standard approval handler for direct console interaction
                return await self.approval_handler.request_approval(
                    operation, parameter_name, parameter_value,
                    prompt_message, content_to_display
                )
        except Exception as e:
            logger.error(f"❌ Error in workflow-aware approval: {e}", exc_info=True)
            # Fallback to standard approval handler
            return await self.approval_handler.request_approval(
                operation, parameter_name, parameter_value,
                prompt_message, content_to_display
            )
    
    async def _handle_workflow_approval(
        self,
        operation: str,
        parameter_name: str,
        parameter_value: str,
        prompt_message: str,
        content_to_display: Optional[Any] = None,
    ) -> Tuple[str, Optional[str]]:
        """Handle approval request within workflow context using interrupts."""
        from langgraph.types import interrupt
        from langgraph.errors import GraphInterrupt
        
        logger.info(f"🎯 Workflow approval request: {operation}")
        
        # Get current workflow context for agent styling
        workflow_context = await get_workflow_context()
        agent_name = workflow_context.agent_name if workflow_context else "agent"
        agent_color = workflow_context.agent_color if workflow_context else None
        
        # Create interrupt payload for approval request
        interrupt_payload = {
            "type": "approval_request",
            "operation": operation,
            "parameter_name": parameter_name,
            "parameter_value": parameter_value,
            "description": f"{operation}: {parameter_value}",
            "prompt_message": prompt_message,
            "content_to_display": content_to_display,
            "agent_name": agent_name,
            "agent_color": agent_color
        }
        
        # Use LangGraph interrupt to pause workflow and request approval
        try:
            # The interrupt() call will raise GraphInterrupt to pause the workflow
            # This is expected behavior - not an error
            approval_response = interrupt(interrupt_payload)
            
            # This code will execute after the workflow resumes with the approval response
            # Parse the response from interrupt bridge
            if approval_response == "approved":
                logger.info(f"✅ Workflow approval granted: {operation}")
                return "approved", "y"
            elif approval_response == "denied":
                logger.info(f"❌ Workflow approval denied: {operation}")
                return "denied", "n"
            elif approval_response in ["session_approved", "approved"]:
                logger.info(f"🔄 Workflow session approval: {operation}")
                return "session_approved", "a"
            else:
                logger.info(f"🚫 Workflow approval cancelled: {operation}")
                return "cancelled", "c"
                
        except GraphInterrupt:
            # This is expected - the interrupt raises GraphInterrupt to pause the workflow
            # The exception should be propagated up to pause execution
            raise
        except Exception as e:
            # Only catch non-GraphInterrupt exceptions as actual errors
            logger.error(f"❌ Unexpected error in workflow interrupt approval: {e}", exc_info=True)
            # If interrupt fails unexpectedly, fall back to denial for safety
            return "denied", "n"
    
    def set_agent_context(self, agent_name: str, agent_color: Optional[str] = None) -> None:
        """Set agent context for styling (delegates to standard approval handler)."""
        self.approval_handler.set_agent_context(agent_name, agent_color)
    
    def clear_agent_context(self) -> None:
        """Clear agent context (delegates to standard approval handler)."""
        self.approval_handler.clear_agent_context()
    
    def print_outcome(self, action: str, outcome: str, success: bool = True):
        """Print operation outcome (delegates to standard approval handler)."""
        self.approval_handler.print_outcome(action, outcome, success)


async def create_workflow_aware_approval_handler(
    console: Console, 
    use_console_manager: bool = True
) -> WorkflowAwareApprovalHandler:
    """
    Factory function to create a workflow-aware approval handler.
    
    This is the recommended way for plugins to create approval handlers
    that work in both workflow and direct console contexts.
    """
    return WorkflowAwareApprovalHandler(console, use_console_manager)


# Convenience function for simple approval requests
async def request_workflow_aware_approval(
    console: Console,
    operation: str,
    parameter_name: str,
    parameter_value: str,
    prompt_message: str,
    content_to_display: Optional[Any] = None,
    use_console_manager: bool = True
) -> Tuple[str, Optional[str]]:
    """
    Convenience function for one-off approval requests.
    
    Creates a temporary workflow-aware approval handler and makes the request.
    """
    handler = await create_workflow_aware_approval_handler(console, use_console_manager)
    return await handler.request_approval(
        operation, parameter_name, parameter_value,
        prompt_message, content_to_display
    )