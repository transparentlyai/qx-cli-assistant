"""
Model adapter to integrate QX's LiteLLM-based agents with LangGraph.

This module creates a LangChain-compatible model wrapper around QX's
LiteLLM integration to work with langgraph-supervisor.
"""

import json
import logging
from typing import Any, Dict, List, Optional, Union
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage, ToolCall
from langchain_core.outputs import ChatResult, ChatGeneration
from langchain_core.callbacks import CallbackManagerForLLMRun
from qx.core.llm import QXLLMAgent
from qx.core.message_utils import extract_last_user_input

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
            # Log available tools if any
            if self.langchain_tools:
                logger.debug(f"Processing with {len(self.langchain_tools)} LangChain tools available")
            
            # Convert LangChain messages to QX format
            qx_messages = []
            user_input = ""
            
            for msg in messages:
                if isinstance(msg, SystemMessage):
                    # Skip system messages - QX agents have their own system prompts
                    continue
                elif isinstance(msg, HumanMessage):
                    qx_messages.append({"role": "user", "content": msg.content})
                    user_input = msg.content  # Keep last user input
                elif isinstance(msg, AIMessage):
                    qx_messages.append({"role": "assistant", "content": msg.content})
                    
            # If no user input found, extract from messages
            if not user_input and qx_messages:
                user_input = extract_last_user_input(qx_messages)
            
            # For supervisor nodes, we need to handle tool calls differently
            # We'll use QX's LLM integration through the agent's _make_litellm_call method
            if self.langchain_tools and any(t.name.startswith('transfer_to_') for t in self.langchain_tools):
                # This is a supervisor - use QX's LLM integration
                
                # Prepare messages for LLM
                llm_messages = []
                for msg in messages:
                    if isinstance(msg, SystemMessage):
                        llm_messages.append({"role": "system", "content": msg.content})
                    elif isinstance(msg, HumanMessage):
                        llm_messages.append({"role": "user", "content": msg.content})
                    elif isinstance(msg, AIMessage):
                        llm_messages.append({"role": "assistant", "content": msg.content})
                
                # Prepare tools for LLM
                tools = []
                for tool in self.langchain_tools:
                    if hasattr(tool, 'name') and tool.name.startswith('transfer_to_'):
                        tools.append({
                            "type": "function",
                            "function": {
                                "name": tool.name,
                                "description": getattr(tool, 'description', ''),
                                "parameters": {
                                    "type": "object",
                                    "properties": {
                                        "task_description": {
                                            "type": "string",
                                            "description": "Description of the task to hand off"
                                        }
                                    },
                                    "required": []
                                }
                            }
                        })
                
                # Use QX's LLM integration through the agent's method
                chat_params = {
                    "model": self.qx_agent.model_name,
                    "messages": llm_messages,
                    "tools": tools if tools else None,
                    "temperature": self.qx_agent.temperature,
                    "stream": False
                }
                
                # Call through QX's LLM integration
                response = await self.qx_agent._make_litellm_call(chat_params)
                
                # Extract response
                message = response.choices[0].message
                response_text = message.content or ""
                tool_calls = []
                
                if hasattr(message, 'tool_calls') and message.tool_calls:
                    for tool_call in message.tool_calls:
                        tool_calls.append(ToolCall(
                            name=tool_call.function.name,
                            args=json.loads(tool_call.function.arguments) if tool_call.function.arguments else {},
                            id=tool_call.id
                        ))
                
                # Create response message
                if tool_calls:
                    ai_message = AIMessage(content=response_text, tool_calls=tool_calls)
                else:
                    ai_message = AIMessage(content=response_text)
                
            else:
                # Regular agent - use QX agent's run method
                result = await self.qx_agent.run(
                    user_input=user_input,
                    message_history=qx_messages[:-1] if qx_messages else [],
                    add_user_message_to_history=False
                )
                
                response_text = result.output if hasattr(result, 'output') else str(result)
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
            "adapter_type": "qx-litellm"
        }
    
    def bind_tools(self, tools: List[Any], **kwargs) -> "QXLiteLLMAdapter":
        """Bind tools to the model.
        
        This is required by LangGraph. We need to add these tools
        to the QX agent so it can use them.
        """
        logger.debug(f"bind_tools called with {len(tools) if tools else 0} tools")
        # Store the LangChain tools
        self.langchain_tools = tools or []
        
        if tools:
            # Initialize _openai_tools_schema if it doesn't exist
            if not hasattr(self.qx_agent, '_openai_tools_schema'):
                self.qx_agent._openai_tools_schema = []
            
            # Also ensure _tool_functions dict exists
            if not hasattr(self.qx_agent, '_tool_functions'):
                self.qx_agent._tool_functions = {}
            
            # Add handoff tools to the QX agent's tool list
            for tool in tools:
                tool_name = getattr(tool, 'name', None)
                if tool_name and tool_name.startswith('transfer_to_'):
                    logger.info(f"Adding handoff tool to QX agent: {tool_name}")
                    # Create a QX-compatible tool description
                    # For handoff tools, we need a simple schema
                    # The langgraph-supervisor expects only a task_description parameter
                    properties = {
                        "task_description": {
                            "type": "string",
                            "description": "Description of the task to hand off"
                        }
                    }
                    required = []  # task_description is optional
                    
                    tool_description = {
                        "name": tool_name,
                        "description": getattr(tool, 'description', f"Transfer to {tool_name.replace('transfer_to_', '')}"),
                        "parameters": {
                            "type": "object",
                            "properties": properties,
                            "required": required
                        }
                    }
                    # Add to agent's OpenAI tools schema
                    if hasattr(self.qx_agent, '_openai_tools_schema'):
                        self.qx_agent._openai_tools_schema.append({
                            "type": "function",
                            "function": tool_description
                        })
                        logger.info(f"Added tool {tool_name} to agent's tool list")
                    
                    # Add a dummy function for the handoff tool
                    # This will be intercepted by LangGraph before actual execution
                    async def handoff_function(**kwargs):
                        return {"status": "handoff", "tool": tool_name, "args": kwargs}
                    
                    self.qx_agent._tool_functions[tool_name] = handoff_function
                    logger.info(f"Added handoff function for {tool_name}")
                    
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