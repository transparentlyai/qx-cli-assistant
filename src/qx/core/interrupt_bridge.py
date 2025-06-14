"""
LangGraph Interrupt Bridge for QX Human-in-the-Loop Integration.

This module bridges LangGraph's interrupt() system with QX's existing 
approval handlers, console manager, and BorderedMarkdown UI system.

Key responsibilities:
- Convert LangGraph interrupt payloads to QX approval requests
- Integrate with QX's console manager for thread-safe output
- Preserve agent colors and BorderedMarkdown styling
- Handle F-key hotkeys and prompt_toolkit functionality during interrupts
- Maintain approve-all session state across workflow interrupts
"""

import asyncio
import logging
from typing import Any, Dict, Optional, Union

from rich.console import Console
from qx.core.approval_handler import ApprovalHandler, set_global_agent_context
from qx.core.console_manager import get_console_manager
from qx.core.user_prompts import get_user_choice_from_options_async, is_approve_all_active, _suspend_global_hotkeys, _resume_global_hotkeys
from qx.cli.quote_bar_component import render_agent_markdown

logger = logging.getLogger(__name__)


class InterruptBridge:
    """
    Bridges LangGraph interrupt() calls with QX's human approval system.
    
    This class handles the conversion of LangGraph interrupt payloads into
    QX-style approval requests while preserving all existing UI patterns,
    agent colors, and console manager integration.
    """
    
    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
        self.approval_handler = ApprovalHandler(self.console, use_console_manager=True)
        self._console_manager = None
        
        try:
            self._console_manager = get_console_manager()
        except Exception as e:
            logger.debug(f"Console manager not available: {e}")
    
    async def handle_interrupt(
        self, 
        interrupt_payload: Dict[str, Any], 
        agent_name: Optional[str] = None,
        agent_color: Optional[str] = None
    ) -> Union[str, Dict[str, Any]]:
        """
        Handle a LangGraph interrupt by converting it to QX approval flow.
        
        Args:
            interrupt_payload: The payload from LangGraph interrupt()
            agent_name: Name of the agent making the request
            agent_color: Color for agent UI theming
            
        Returns:
            User response (string or dict based on interrupt type)
        """
        # Suspend global hotkeys during interrupt handling
        hotkeys_suspended = _suspend_global_hotkeys()
        
        try:
            logger.info(f"🎭 Processing interrupt: type={interrupt_payload.get('type', 'unknown')}")
            logger.debug(f"📦 Interrupt payload: {interrupt_payload}")
            
            # Set agent context for consistent styling
            if agent_name:
                set_global_agent_context(agent_name, agent_color)
                self.approval_handler.set_agent_context(agent_name, agent_color)
            
            interrupt_type = interrupt_payload.get("type", "user_input")
            
            if interrupt_type == "user_input":
                return await self._handle_user_input_interrupt(interrupt_payload, agent_name, agent_color)
            elif interrupt_type == "satisfaction_check":
                return await self._handle_satisfaction_check(interrupt_payload, agent_name, agent_color)
            elif interrupt_type == "approval_request":
                return await self._handle_approval_request(interrupt_payload, agent_name, agent_color)
            elif interrupt_type == "task_delegation":
                return await self._handle_task_delegation(interrupt_payload, agent_name, agent_color)
            else:
                # Generic interrupt handling
                return await self._handle_generic_interrupt(interrupt_payload, agent_name, agent_color)
                
        except Exception as e:
            logger.error(f"❌ Error handling interrupt: {e}", exc_info=True)
            # Return a safe default response
            return "continue"
        finally:
            # Always resume global hotkeys
            if hotkeys_suspended:
                _resume_global_hotkeys()
    
    async def _handle_user_input_interrupt(
        self, 
        payload: Dict[str, Any], 
        agent_name: Optional[str], 
        agent_color: Optional[str]
    ) -> str:
        """Handle user input requests from workflow."""
        message = payload.get("message", "Please provide your input:")
        
        logger.info(f"⏸️ User input requested: {message[:50]}...")
        
        # Use agent-styled markdown for the input request
        if agent_name:
            render_agent_markdown(
                f"**Input Request**\n\n{message}",
                agent_name,
                agent_color=agent_color,
                console=self.console
            )
        else:
            # Fallback to console manager or direct console
            if self._console_manager:
                self._console_manager.print(f"Input: {message}", console=self.console)
            else:
                self.console.print(f"Input: {message}")
        
        # Get user input using QX's input system
        prompt_text = "Your response: "
        
        if self._console_manager:
            # Use console manager's blocking input
            response = self._console_manager.request_input_blocking(
                prompt_text=prompt_text,
                console=self.console
            )
        else:
            # Fallback to Rich Prompt
            from rich.prompt import Prompt
            response = Prompt.ask(prompt_text, console=self.console)
        
        response = response or ""
        logger.info(f"▶️ User response received: {response[:50] if response else 'empty'}...")
        return response
    
    async def _handle_satisfaction_check(
        self, 
        payload: Dict[str, Any], 
        agent_name: Optional[str], 
        agent_color: Optional[str]
    ) -> str:
        """Handle satisfaction checks after task completion."""
        message = payload.get("message", "Are you satisfied with this result?")
        result = payload.get("result", "")
        
        logger.info(f"⏸️ Satisfaction check requested")
        
        # Display the result using agent-styled markdown
        if agent_name:
            result_preview = result[:500] + "..." if len(result) > 500 else result
            render_agent_markdown(
                f"**Task Result**\n\n{result_preview}",
                agent_name,
                agent_color=agent_color,
                console=self.console
            )
            
            # Show satisfaction question
            render_agent_markdown(
                f"**Satisfaction Check**\n\n{message}",
                agent_name,
                agent_color=agent_color,
                console=self.console
            )
        else:
            # Fallback display
            if self._console_manager:
                self._console_manager.print(f"Result: {result[:200]}...", console=self.console)
                self._console_manager.print(message, console=self.console)
            else:
                self.console.print(f"Result: {result[:200]}...")
                self.console.print(message)
        
        # Check if auto-approve is active
        if await is_approve_all_active():
            logger.info("🔄 Auto-approve active, continuing workflow")
            return "satisfied - continuing"
        
        # Get user choice
        options = [
            ("y", "Yes, satisfied", "satisfied"),
            ("c", "Continue with more work", "continue"),
            ("r", "Redo/modify", "redo"),
        ]
        
        choice = await self._get_user_choice(options, "Continue? ", agent_name, agent_color)
        
        if choice == "y":
            return "satisfied - task complete"
        elif choice == "c":
            return "continue with more work"
        else:
            return "redo the task"
    
    async def _handle_approval_request(
        self, 
        payload: Dict[str, Any], 
        agent_name: Optional[str], 
        agent_color: Optional[str]
    ) -> str:
        """Handle approval requests for actions."""
        operation = payload.get("operation", "Action")
        description = payload.get("description", "")
        parameter_name = payload.get("parameter_name", "action")
        parameter_value = payload.get("parameter_value", description)
        
        logger.info(f"⏸️ Approval request: {operation}")
        
        # Use QX's existing approval system
        prompt_message = payload.get("prompt_message", f"Approve {operation.lower()}?")
        status, chosen_key = await self.approval_handler.request_approval(
            operation=operation,
            parameter_name=parameter_name,
            parameter_value=parameter_value,
            prompt_message=prompt_message,
            content_to_display=payload.get("content_to_display")
        )
        
        logger.info(f"▶️ Approval response: {status}")
        
        # Convert QX approval status to workflow-friendly response
        if status == "approved":
            return "approved"
        elif status == "session_approved":
            return "session_approved"
        elif status == "denied":
            return "denied"
        else:
            return "cancelled"
    
    async def _handle_task_delegation(
        self, 
        payload: Dict[str, Any], 
        agent_name: Optional[str], 
        agent_color: Optional[str]
    ) -> Dict[str, Any]:
        """Handle task delegation requests."""
        task = payload.get("task", "")
        available_agents = payload.get("available_agents", [])
        
        logger.info(f"⏸️ Task delegation request: {task[:50]}...")
        
        # Display task delegation request
        if agent_name:
            agents_list = "\\n".join([f"- {agent}" for agent in available_agents])
            render_agent_markdown(
                f"**Task Delegation**\\n\\nTask: {task}\\n\\nAvailable Agents:\\n{agents_list}",
                agent_name,
                agent_color=agent_color,
                console=self.console
            )
        
        # For now, return automatic delegation (this can be enhanced later)
        if available_agents:
            selected_agent = available_agents[0]  # Select first available agent
            logger.info(f"▶️ Auto-delegating to: {selected_agent}")
            return {"selected_agent": selected_agent, "delegate": True}
        else:
            return {"delegate": False}
    
    async def _handle_generic_interrupt(
        self, 
        payload: Dict[str, Any], 
        agent_name: Optional[str], 
        agent_color: Optional[str]
    ) -> str:
        """Handle generic interrupts that don't fit other categories."""
        message = payload.get("message", "Workflow paused for user input")
        question = payload.get("question", message)
        
        logger.info(f"⏸️ Generic interrupt: {question[:50]}...")
        
        # Display the question using agent styling
        if agent_name:
            render_agent_markdown(
                f"**Workflow Pause**\\n\\n{question}",
                agent_name,
                agent_color=agent_color,
                console=self.console
            )
        else:
            if self._console_manager:
                self._console_manager.print(question, console=self.console)
            else:
                self.console.print(question)
        
        # Simple continue/stop choice
        options = [
            ("c", "Continue", "continue"),
            ("s", "Stop", "stop"),
        ]
        
        choice = await self._get_user_choice(options, "Action? ", agent_name, agent_color)
        
        return "continue" if choice == "c" else "stop"
    
    async def _get_user_choice(
        self, 
        options: list, 
        prompt_text: str, 
        agent_name: Optional[str], 
        agent_color: Optional[str]
    ) -> str:
        """Get user choice using QX's choice system."""
        valid_keys = [key for key, _, _ in options]
        
        # Format display options with highlighting
        colored_display_texts = []
        for key, text, _ in options:
            colored_text = f"[highlight]{text[0]}[/highlight]{text[1:]}"
            colored_display_texts.append(colored_text)
        
        prompt_choices = ", ".join(colored_display_texts)
        full_prompt_text = f"{prompt_text} ({prompt_choices}) "
        
        # Use console manager for choice if available
        if self._console_manager:
            chosen_key = self._console_manager.request_choice_blocking(
                prompt_text_with_options=full_prompt_text,
                valid_choices=valid_keys,
                console=self.console,
                default_choice=None
            )
        else:
            # Fallback to async choice function
            chosen_key = await get_user_choice_from_options_async(
                self.console,
                full_prompt_text,
                valid_keys,
                default_choice=None,
            )
        
        return chosen_key or valid_keys[0]  # Default to first option if no choice


# Global bridge instance
_interrupt_bridge: Optional[InterruptBridge] = None


def get_interrupt_bridge(console: Optional[Console] = None) -> InterruptBridge:
    """Get or create the global interrupt bridge instance."""
    global _interrupt_bridge
    if _interrupt_bridge is None:
        _interrupt_bridge = InterruptBridge(console)
    return _interrupt_bridge


async def handle_workflow_interrupt(
    interrupt_payload: Dict[str, Any], 
    agent_name: Optional[str] = None,
    agent_color: Optional[str] = None
) -> Union[str, Dict[str, Any]]:
    """
    Convenience function to handle workflow interrupts.
    
    This is the main entry point for converting LangGraph interrupt() calls
    into QX approval workflows.
    """
    bridge = get_interrupt_bridge()
    return await bridge.handle_interrupt(interrupt_payload, agent_name, agent_color)