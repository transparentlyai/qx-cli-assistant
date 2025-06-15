"""
Tool adapter to integrate QX's tool plugin system with LangGraph agents.

This module bridges QX's dynamic tool system with the tool format expected
by LangGraph agents.
"""

import logging
from typing import Any, Callable, Dict, List, Optional
from langchain_core.tools import Tool
from pydantic import BaseModel

from qx.core.console_manager import get_console_manager

logger = logging.getLogger(__name__)


class QXToolAdapter:
    """Adapts QX tools to work with LangGraph agents."""
    
    def __init__(self):
        self.console_manager = get_console_manager()
        
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
            LangChain Tool compatible with LangGraph agents
        """
        
        async def wrapped_tool_func(**kwargs):
            """Wrapper that handles QX-specific tool execution."""
            # Prepare arguments for QX tool
            tool_args = {
                'console': self.console_manager,
                'args': tool_schema(**kwargs) if tool_schema else kwargs
            }
            
            # Execute the tool
            result = await tool_func(**tool_args)
            
            # Convert result to string if needed
            if hasattr(result, 'model_dump_json'):
                return result.model_dump_json()
            else:
                return str(result)
        
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
    
    def load_tools_for_agent(self, agent_name: str, agent_config=None) -> List[Tool]:
        """
        Load all tools available for a specific agent.
        
        Args:
            agent_name: Name of the agent
            agent_config: Optional agent configuration with tools list
            
        Returns:
            List of LangChain Tools
        """
        tools = []
        tool_names = []
        
        # Get tools from agent config
        if agent_config and hasattr(agent_config, 'tools'):
            # Convert tool names from YAML format (e.g., 'read_file_tool' -> 'read_file')
            for tool_name in agent_config.tools:
                # Remove '_tool' suffix if present
                clean_name = tool_name.replace('_tool', '') if tool_name.endswith('_tool') else tool_name
                tool_names.append(clean_name)
        else:
            # No tools specified in agent config
            logger.warning(f"Agent '{agent_name}' has no tools specified in configuration")
            return []
        
        for tool_name in tool_names:
            # Get tool from QX's plugin system
            tool_func, tool_schema = self._get_qx_tool(tool_name)
            if not tool_func:
                raise ValueError(f"Tool '{tool_name}' not found for agent '{agent_name}'")
            
            tool = self.create_langchain_tool(tool_name, tool_func, tool_schema)
            tools.append(tool)
            logger.debug(f"Loaded tool '{tool_name}' for agent '{agent_name}'")
                
        logger.info(f"Loaded {len(tools)} tools for agent '{agent_name}'")
        return tools
    
    def _get_qx_tool(self, tool_name: str) -> tuple[Callable, BaseModel]:
        """
        Get a QX tool function and its schema.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Tuple of (tool_function, argument_schema)
            
        Raises:
            ValueError: If tool is not found
            ImportError: If tool module cannot be imported
        """
        # Import the specific plugin module
        if tool_name == "write_file":
            from qx.plugins.write_file_plugin import write_file_tool, WriteFilePluginInput
            return write_file_tool, WriteFilePluginInput
        elif tool_name == "read_file":
            from qx.plugins.read_file_plugin import read_file_tool, ReadFilePluginInput
            return read_file_tool, ReadFilePluginInput
        elif tool_name == "execute_shell":
            from qx.plugins.execute_shell_plugin import execute_shell_tool, ExecuteShellPluginInput
            return execute_shell_tool, ExecuteShellPluginInput
        elif tool_name == "web_fetch":
            from qx.plugins.web_fetch_plugin import web_fetch_tool, WebFetchPluginInput
            return web_fetch_tool, WebFetchPluginInput
        elif tool_name == "worktree_manager":
            from qx.plugins.worktree_manager_plugin import worktree_manager_tool, WorktreeManagerPluginInput
            return worktree_manager_tool, WorktreeManagerPluginInput
        elif tool_name == "current_time":
            from qx.plugins.current_time_plugin import current_time_tool, CurrentTimePluginInput
            return current_time_tool, CurrentTimePluginInput
        else:
            raise ValueError(f"Tool '{tool_name}' not found in plugin registry")


# Singleton instance
_tool_adapter_instance: Optional[QXToolAdapter] = None


def get_tool_adapter() -> QXToolAdapter:
    """Get or create the tool adapter instance."""
    global _tool_adapter_instance
    
    if _tool_adapter_instance is None:
        _tool_adapter_instance = QXToolAdapter()
        
    return _tool_adapter_instance