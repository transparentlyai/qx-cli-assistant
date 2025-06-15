"""
Model adapter to integrate QX's LiteLLM-based agents with LangGraph.

This module creates a LangChain-compatible model wrapper around QX's
LiteLLM integration to work with langgraph-supervisor.
"""

import logging
from typing import Any, Dict, List, Optional, Union
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage, ToolCall
from langchain_core.outputs import ChatResult, ChatGeneration
from langchain_core.callbacks import CallbackManagerForLLMRun
import json

from qx.core.llm import QXLLMAgent
from qx.cli.quote_bar_component import render_agent_markdown

logger = logging.getLogger(__name__)


class QXLiteLLMAdapter(BaseChatModel):
    """
    Adapter that wraps QX's LiteLLM agent to work with LangChain/LangGraph.
    """
    
    qx_agent: Any  # The QX LLM agent instance
    agent_name: str = "unknown"  # Name of the agent
    langchain_tools: List[Any] = []  # Additional tools bound by LangChain/LangGraph
    
    def __init__(self, qx_agent: QXLLMAgent, **kwargs):
        """Initialize with a QX LLM agent."""
        agent_name = getattr(qx_agent, 'agent_name', 'unknown')
        super().__init__(qx_agent=qx_agent, agent_name=agent_name, **kwargs)
        
    @property
    def _llm_type(self) -> str:
        """Return the type of language model."""
        return f"qx-litellm-{self.agent_name}"
    
    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Generate a response synchronously (required by base class)."""
        # LangGraph typically uses async, so this is just a wrapper
        import asyncio
        return asyncio.run(self._agenerate(messages, stop, run_manager, **kwargs))
    
    async def _agenerate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Generate a response using the QX agent."""
        try:
            # Check if we have handoff tools bound
            if self.langchain_tools:
                logger.info(f"Processing with {len(self.langchain_tools)} LangChain tools available")
                # For now, just log - we need to figure out how to use them
                for tool in self.langchain_tools:
                    logger.debug(f"Available tool: {getattr(tool, 'name', 'unknown')}")
            
            # Convert LangChain messages to QX format
            qx_messages = []
            user_input = ""
            
            for msg in messages:
                if isinstance(msg, SystemMessage):
                    # System messages are handled by agent's own prompt
                    continue
                elif isinstance(msg, HumanMessage):
                    qx_messages.append({"role": "user", "content": msg.content})
                    user_input = msg.content  # Keep last user input
                elif isinstance(msg, AIMessage):
                    qx_messages.append({"role": "assistant", "content": msg.content})
                    
            # If no user input found, use empty string
            if not user_input and qx_messages:
                # Find the last user message
                for msg in reversed(qx_messages):
                    if msg.get("role") == "user":
                        user_input = msg.get("content", "")
                        break
                        
            # Prepare tools for QX agent if we have handoff tools
            if self.langchain_tools:
                # Convert LangChain tools to QX tool format
                for tool in self.langchain_tools:
                    tool_name = getattr(tool, 'name', None)
                    # Check if tool already exists in agent's schema
                    existing_tool_names = [t['function']['name'] for t in self.qx_agent._openai_tools_schema]
                    if tool_name and tool_name not in existing_tool_names:
                        tool_desc = {
                            "name": tool_name,
                            "description": getattr(tool, 'description', f"Tool: {tool_name}"),
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "task_description": {
                                        "type": "string",
                                        "description": "Description of the task to delegate"
                                    }
                                },
                                "required": []
                            }
                        }
                        # Add to OpenAI tools schema format
                        self.qx_agent._openai_tools_schema.append({
                            "type": "function",
                            "function": tool_desc
                        })
            
            # Call QX agent's run method
            result = await self.qx_agent.run(
                user_input=user_input,
                message_history=qx_messages[:-1] if qx_messages else [],  # Exclude current input
                add_user_message_to_history=False  # Already in messages
            )
            
            # Extract response and check for tool calls
            response_text = result.output if hasattr(result, 'output') else str(result)
            tool_calls = []
            
            # Check if QX agent made tool calls
            if hasattr(result, 'tool_calls') and result.tool_calls:
                for tc in result.tool_calls:
                    if tc.get('name', '').startswith('transfer_to_'):
                        tool_calls.append(ToolCall(
                            name=tc['name'],
                            args=tc.get('args', {}),
                            id=tc.get('id', f"call_{tc['name']}")
                        ))
            
            # Create LangChain response message
            if tool_calls:
                # If there are tool calls, create a message with them
                ai_message = AIMessage(
                    content=response_text,
                    tool_calls=tool_calls
                )
            else:
                # Regular message without tool calls
                ai_message = AIMessage(content=response_text)
            
            generation = ChatGeneration(
                message=ai_message,
                generation_info={"agent_name": self.agent_name}
            )
            
            return ChatResult(generations=[generation])
            
        except Exception as e:
            logger.error(f"Error in QX model adapter: {e}", exc_info=True)
            # Return error as response
            generation = ChatGeneration(
                message=AIMessage(content=f"Error: {str(e)}"),
                generation_info={"agent_name": self.agent_name, "error": True}
            )
            return ChatResult(generations=[generation])
    
    @property
    def _identifying_params(self) -> Dict[str, Any]:
        """Return parameters that identify this model."""
        return {
            "agent_name": self.agent_name,
            "model_name": getattr(self.qx_agent, 'model_name', 'unknown'),
            "qx_version": "litellm-adapter-v1"
        }
    
    def bind_tools(self, tools: List[Any], **kwargs) -> "QXLiteLLMAdapter":
        """Bind tools to the model.
        
        This is required by LangGraph. We need to add these tools
        to the QX agent so it can use them.
        """
        logger.debug(f"bind_tools called with {len(tools) if tools else 0} tools")
        # Store the LangChain tools
        self.langchain_tools = tools or []
        
        if tools and hasattr(self.qx_agent, '_tool_functions'):
            # Add handoff tools to the QX agent's tool list
            for tool in tools:
                tool_name = getattr(tool, 'name', None)
                if tool_name and tool_name.startswith('transfer_to_'):
                    logger.info(f"Adding handoff tool to QX agent: {tool_name}")
                    # Create a QX-compatible tool description
                    tool_description = {
                        "name": tool_name,
                        "description": getattr(tool, 'description', f"Transfer to {tool_name.replace('transfer_to_', '')}"),
                        "parameters": {
                            "type": "object",
                            "properties": {},
                            "required": []
                        }
                    }
                    # Add to agent's OpenAI tools schema
                    if hasattr(self.qx_agent, '_openai_tools_schema'):
                        self.qx_agent._openai_tools_schema.append({
                            "type": "function",
                            "function": tool_description
                        })
                        logger.info(f"Added tool {tool_name} to agent's tool list")
                    
        return self


def create_langchain_model(qx_agent: QXLLMAgent) -> BaseChatModel:
    """
    Create a LangChain-compatible model from a QX LLM agent.
    
    Args:
        qx_agent: The QX LLM agent to wrap
        
    Returns:
        LangChain BaseChatModel that can be used with langgraph-supervisor
    """
    return QXLiteLLMAdapter(qx_agent)