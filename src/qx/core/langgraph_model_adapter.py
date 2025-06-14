"""
Model adapter to integrate QX's LiteLLM-based agents with LangGraph.

This module creates a LangChain-compatible model wrapper around QX's
LiteLLM integration to work with langgraph-supervisor.
"""

import logging
from typing import Any, Dict, List, Optional, Union
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.outputs import ChatResult, ChatGeneration
from langchain_core.callbacks import CallbackManagerForLLMRun

from qx.core.llm import QXLLMAgent

logger = logging.getLogger(__name__)


class QXLiteLLMAdapter(BaseChatModel):
    """
    Adapter that wraps QX's LiteLLM agent to work with LangChain/LangGraph.
    """
    
    def __init__(self, qx_agent: QXLLMAgent):
        """Initialize with a QX LLM agent."""
        super().__init__()
        self.qx_agent = qx_agent
        self.agent_name = getattr(qx_agent, 'agent_name', 'unknown')
        
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
                        
            # Call QX agent's run method
            result = await self.qx_agent.run(
                user_input=user_input,
                message_history=qx_messages[:-1] if qx_messages else [],  # Exclude current input
                add_user_message_to_history=False  # Already in messages
            )
            
            # Extract response
            response_text = result.output if hasattr(result, 'output') else str(result)
            
            # Create LangChain response
            generation = ChatGeneration(
                message=AIMessage(content=response_text),
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


def create_langchain_model(qx_agent: QXLLMAgent) -> BaseChatModel:
    """
    Create a LangChain-compatible model from a QX LLM agent.
    
    Args:
        qx_agent: The QX LLM agent to wrap
        
    Returns:
        LangChain BaseChatModel that can be used with langgraph-supervisor
    """
    return QXLiteLLMAdapter(qx_agent)