# src/qx/core/agent_invocation.py
"""
Agent invocation service for programmatic agent execution.
Allows calling agents with prompts and receiving responses asynchronously.
"""

import asyncio
import logging
import os
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from datetime import datetime
from pathlib import Path

from qx.core.agent_loader import get_agent_loader
from qx.core.agent_manager import get_agent_manager
from qx.core.mcp_manager import MCPManager
from qx.core.llm_utils import initialize_agent_with_mcp
from qx.core.llm import QXLLMAgent
from qx.core.schemas import AgentConfig
from openai.types.chat import ChatCompletionMessageParam

logger = logging.getLogger(__name__)


@dataclass
class AgentResponse:
    """Response from agent invocation"""
    agent_name: str
    prompt: str
    response: str
    messages: List[ChatCompletionMessageParam]
    success: bool
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None


class BufferedConsole:
    """
    A console replacement that buffers output instead of printing.
    Used to capture agent responses without console interaction.
    """
    def __init__(self):
        self.buffer: List[str] = []
        
    def print(self, *args, **kwargs):
        """Capture print output to buffer"""
        # Convert args to string and append to buffer
        output = " ".join(str(arg) for arg in args)
        self.buffer.append(output)
        
    def get_output(self) -> str:
        """Get all buffered output as a single string"""
        return "\n".join(self.buffer)
        
    def clear(self):
        """Clear the output buffer"""
        self.buffer.clear()


class AgentInvocationService:
    """
    Service for programmatically invoking agents with prompts.
    Handles agent loading, initialization, and async execution.
    """
    
    def __init__(self, mcp_manager: Optional[MCPManager] = None):
        """
        Initialize the agent invocation service.
        
        Args:
            mcp_manager: Optional MCP manager instance. If not provided,
                        a new one will be created when needed.
        """
        self._agent_loader = get_agent_loader()
        self._agent_manager = get_agent_manager()
        self._mcp_manager = mcp_manager
        self._active_invocations: Dict[str, asyncio.Task] = {}
        
    async def _get_or_create_mcp_manager(self) -> MCPManager:
        """Get existing MCP manager or create a new one"""
        if self._mcp_manager is None:
            # Create a minimal MCP manager for agent invocation
            self._mcp_manager = MCPManager()
            # Initialize without starting servers (for lightweight usage)
            await self._mcp_manager.initialize(start_servers=False)
        return self._mcp_manager
        
    async def invoke_agent(
        self,
        agent_name: str,
        prompt: str,
        context: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None,
        use_message_history: bool = False
    ) -> AgentResponse:
        """
        Invoke an agent with a prompt and return the response.
        
        Args:
            agent_name: Name of the agent to invoke
            prompt: The prompt/query to send to the agent
            context: Optional template context for agent configuration
            timeout: Optional timeout in seconds (defaults to agent's max_execution_time)
            use_message_history: Whether to use the agent's existing message history
            
        Returns:
            AgentResponse with the agent's response and metadata
        """
        started_at = datetime.now()
        invocation_id = f"{agent_name}_{started_at.timestamp()}"
        
        try:
            # Load agent configuration
            load_result = self._agent_loader.load_agent(
                agent_name, 
                context=context or self._get_default_context(),
                cwd=os.getcwd()
            )
            
            if not load_result.success or load_result.agent is None:
                return AgentResponse(
                    agent_name=agent_name,
                    prompt=prompt,
                    response="",
                    messages=[],
                    success=False,
                    error=f"Failed to load agent: {load_result.error}",
                    started_at=started_at,
                    completed_at=datetime.now()
                )
                
            agent_config = load_result.agent
            
            # Use agent's timeout if not specified
            if timeout is None:
                timeout = agent_config.max_execution_time
            
            # Create the invocation task
            task = asyncio.create_task(
                self._execute_agent(
                    agent_config, 
                    prompt, 
                    use_message_history,
                    invocation_id
                )
            )
            
            # Track active invocation
            self._active_invocations[invocation_id] = task
            
            try:
                # Wait for completion with timeout
                response = await asyncio.wait_for(task, timeout=timeout)
                response.started_at = started_at
                response.completed_at = datetime.now()
                response.duration_seconds = (
                    response.completed_at - started_at
                ).total_seconds()
                return response
                
            except asyncio.TimeoutError:
                # Cancel the task if it times out
                task.cancel()
                return AgentResponse(
                    agent_name=agent_name,
                    prompt=prompt,
                    response="",
                    messages=[],
                    success=False,
                    error=f"Agent execution timed out after {timeout} seconds",
                    started_at=started_at,
                    completed_at=datetime.now()
                )
            finally:
                # Clean up tracking
                self._active_invocations.pop(invocation_id, None)
                
        except Exception as e:
            logger.error(f"Error invoking agent {agent_name}: {e}", exc_info=True)
            return AgentResponse(
                agent_name=agent_name,
                prompt=prompt,
                response="",
                messages=[],
                success=False,
                error=str(e),
                started_at=started_at,
                completed_at=datetime.now()
            )
            
    async def _execute_agent(
        self,
        agent_config: AgentConfig,
        prompt: str,
        use_message_history: bool,
        invocation_id: str
    ) -> AgentResponse:
        """
        Execute the agent with the given prompt.
        This runs in a separate task/thread.
        """
        buffered_console = BufferedConsole()
        
        try:
            # Get or create MCP manager
            mcp_manager = await self._get_or_create_mcp_manager()
            
            # Initialize LLM agent with the agent configuration
            llm_agent = await initialize_agent_with_mcp(
                mcp_manager=mcp_manager,
                agent_config=agent_config
            )
            
            # Replace console with buffered version
            llm_agent.console = buffered_console
            
            # Get message history if requested
            message_history = None
            if use_message_history:
                # Get the agent's preserved message history
                message_history = self._agent_manager.get_agent_message_history(
                    agent_config.name
                )
            
            # Run the agent with the prompt
            result = await llm_agent.run(
                user_input=prompt,
                message_history=message_history,
                add_user_message_to_history=True
            )
            
            # Extract response and messages
            if hasattr(result, 'content') and hasattr(result, 'messages'):
                response_content = result.content
                response_messages = result.messages
            else:
                # Fallback for string responses
                response_content = str(result)
                response_messages = []
            
            # Optionally save updated message history
            if use_message_history and response_messages:
                self._agent_manager.save_agent_message_history(
                    agent_config.name,
                    response_messages
                )
            
            return AgentResponse(
                agent_name=agent_config.name,
                prompt=prompt,
                response=response_content,
                messages=response_messages,
                success=True,
                error=None
            )
            
        except Exception as e:
            logger.error(
                f"Error executing agent {agent_config.name} (invocation {invocation_id}): {e}",
                exc_info=True
            )
            return AgentResponse(
                agent_name=agent_config.name,
                prompt=prompt,
                response="",
                messages=[],
                success=False,
                error=str(e)
            )
            
    async def invoke_agent_batch(
        self,
        agent_name: str,
        prompts: List[str],
        context: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None,
        max_concurrent: int = 3
    ) -> List[AgentResponse]:
        """
        Invoke an agent with multiple prompts concurrently.
        
        Args:
            agent_name: Name of the agent to invoke
            prompts: List of prompts to process
            context: Optional template context
            timeout: Optional timeout per prompt
            max_concurrent: Maximum concurrent invocations
            
        Returns:
            List of AgentResponse objects in the same order as prompts
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def invoke_with_semaphore(prompt: str, index: int) -> tuple[int, AgentResponse]:
            async with semaphore:
                response = await self.invoke_agent(
                    agent_name=agent_name,
                    prompt=prompt,
                    context=context,
                    timeout=timeout,
                    use_message_history=False  # Each prompt is independent
                )
                return index, response
                
        # Create tasks for all prompts
        tasks = [
            invoke_with_semaphore(prompt, i) 
            for i, prompt in enumerate(prompts)
        ]
        
        # Execute all tasks
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Sort results by original index and handle exceptions
        responses = [None] * len(prompts)
        for result in results:
            if isinstance(result, Exception):
                # Create error response for exceptions
                logger.error(f"Batch invocation error: {result}")
                # Find which prompt failed - this is a fallback
                continue
            else:
                index, response = result
                responses[index] = response
                
        # Fill in any missing responses with errors
        for i, response in enumerate(responses):
            if response is None:
                responses[i] = AgentResponse(
                    agent_name=agent_name,
                    prompt=prompts[i],
                    response="",
                    messages=[],
                    success=False,
                    error="Failed during batch processing"
                )
                
        return responses
        
    def _get_default_context(self) -> Dict[str, str]:
        """Get default context for template substitution"""
        return {
            "user_context": os.environ.get("QX_USER_CONTEXT", ""),
            "project_context": os.environ.get("QX_PROJECT_CONTEXT", ""),
            "project_files": os.environ.get("QX_PROJECT_FILES", ""),
            "ignore_paths": "",
        }
        
    async def list_available_agents(self) -> List[str]:
        """List all available agents that can be invoked"""
        return self._agent_loader.discover_agents(cwd=os.getcwd())
        
    async def get_agent_info(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific agent"""
        return self._agent_loader.get_agent_info(agent_name, cwd=os.getcwd())
        
    def get_active_invocations(self) -> List[str]:
        """Get list of currently active agent invocations"""
        return list(self._active_invocations.keys())
        
    async def cancel_invocation(self, invocation_id: str) -> bool:
        """
        Cancel an active agent invocation.
        
        Returns:
            True if cancelled, False if not found
        """
        task = self._active_invocations.get(invocation_id)
        if task and not task.done():
            task.cancel()
            return True
        return False


# Convenience functions for simple usage
async def invoke_agent(
    agent_name: str,
    prompt: str,
    context: Optional[Dict[str, str]] = None,
    timeout: Optional[int] = None
) -> AgentResponse:
    """
    Simple function to invoke an agent with a prompt.
    
    Example:
        response = await invoke_agent("code_reviewer", "Review this function for security issues")
        print(response.response)
    """
    service = AgentInvocationService()
    return await service.invoke_agent(agent_name, prompt, context, timeout)


async def invoke_agent_sync_wrapper(
    agent_name: str,
    prompt: str,
    context: Optional[Dict[str, str]] = None,
    timeout: Optional[int] = None
) -> AgentResponse:
    """
    Wrapper for synchronous code to call the async agent invocation.
    
    Example:
        import asyncio
        response = asyncio.run(invoke_agent_sync_wrapper("qx", "Help me write a function"))
    """
    return await invoke_agent(agent_name, prompt, context, timeout)