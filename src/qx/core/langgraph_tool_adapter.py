"""
Tool adapter to integrate QX's tool plugin system with LangGraph agents.

This module bridges QX's dynamic tool system with the tool format expected
by langgraph-supervisor's create_react_agent.
"""

import logging
from typing import Any, Callable, Dict, List, Optional
from langchain_core.tools import Tool
from pydantic import BaseModel

from qx.core.console_manager import get_console_manager
from qx.core.workflow_context import get_workflow_context

logger = logging.getLogger(__name__)


class QXToolAdapter:
    """Adapts QX tools to work with LangGraph agents."""
    
    def __init__(self):
        self.console_manager = get_console_manager()
        self._tool_registry = {}
        
    def create_langchain_tool(self, 
                            tool_name: str, 
                            tool_func: Callable,
                            tool_schema: Optional[BaseModel] = None) -> Tool:
        """
        Convert a QX tool function into a LangChain Tool.
        
        Args:
            tool_name: Name of the tool
            tool_func: The QX tool function
            tool_schema: Pydantic model for tool arguments
            
        Returns:
            LangChain Tool compatible with create_react_agent
        """
        
        async def wrapped_tool_func(**kwargs):
            """Wrapper that handles QX-specific tool execution."""
            try:
                # Get workflow context if available
                workflow_context = await get_workflow_context()
                
                # Prepare arguments for QX tool
                tool_args = {
                    'console': self.console_manager,
                    'args': tool_schema(**kwargs) if tool_schema else kwargs
                }
                
                # Add workflow context if tool supports it
                if workflow_context:
                    tool_args['workflow_context'] = workflow_context
                    
                # Execute the tool
                result = await tool_func(**tool_args)
                
                # Convert result to string if needed
                if hasattr(result, 'model_dump_json'):
                    return result.model_dump_json()
                else:
                    return str(result)
                    
            except Exception as e:
                logger.error(f"Error executing tool {tool_name}: {e}", exc_info=True)
                return f"Error: {str(e)}"
        
        # Create tool description
        description = f"QX tool: {tool_name}"
        if tool_schema and hasattr(tool_schema, '__doc__') and tool_schema.__doc__:
            description = tool_schema.__doc__.strip()
            
        # Create the LangChain tool
        return Tool(
            name=tool_name,
            func=wrapped_tool_func,
            description=description,
            args_schema=tool_schema
        )
    
    def load_tools_for_agent(self, agent_name: str) -> List[Tool]:
        """
        Load all tools available for a specific agent.
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            List of LangChain Tools
        """
        tools = []
        
        # Map agent names to their typical tools
        agent_tool_mapping = {
            "full_stack_swe": [
                "write_file", "read_file", "execute_shell", 
                "search_code", "list_files"
            ],
            "qx-director": [],  # Director typically doesn't need tools
            # Add more agent-tool mappings as needed
        }
        
        tool_names = agent_tool_mapping.get(agent_name, [])
        
        for tool_name in tool_names:
            try:
                # Get tool from QX's plugin system
                tool_func, tool_schema = self._get_qx_tool(tool_name)
                if tool_func:
                    tool = self.create_langchain_tool(tool_name, tool_func, tool_schema)
                    tools.append(tool)
                    logger.debug(f"Loaded tool '{tool_name}' for agent '{agent_name}'")
            except Exception as e:
                logger.error(f"Failed to load tool '{tool_name}': {e}")
                
        logger.info(f"Loaded {len(tools)} tools for agent '{agent_name}'")
        return tools
    
    def _get_qx_tool(self, tool_name: str) -> tuple[Optional[Callable], Optional[BaseModel]]:
        """
        Get a QX tool function and its schema.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Tuple of (tool_function, argument_schema)
        """
        # TODO: Integrate with actual QX tool plugin system
        # This is a placeholder that should connect to the real tool registry
        
        # For now, return None to indicate tool not found
        logger.debug(f"Tool '{tool_name}' lookup (placeholder)")
        return None, None


# Singleton instance
_tool_adapter_instance: Optional[QXToolAdapter] = None


def get_tool_adapter() -> QXToolAdapter:
    """Get or create the tool adapter instance."""
    global _tool_adapter_instance
    
    if _tool_adapter_instance is None:
        _tool_adapter_instance = QXToolAdapter()
        
    return _tool_adapter_instance