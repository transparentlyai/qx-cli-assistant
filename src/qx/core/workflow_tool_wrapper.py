"""
Workflow Tool Wrapper for Enhanced Integration.

This module provides automatic wrapper functionality to make existing QX tools
workflow-aware without requiring changes to the tool implementations.
"""

import asyncio
import functools
import inspect
import logging
from typing import Any, Callable, Dict, Optional

from qx.core.workflow_context import get_workflow_context
from qx.core.workflow_tool_integration import (
    get_workflow_tool_integrator, 
    ToolExecutionMode, 
    register_workflow_tool
)

logger = logging.getLogger(__name__)


def workflow_aware_tool(
    tool_name: Optional[str] = None,
    dependencies: Optional[set] = None,
    execution_mode: ToolExecutionMode = ToolExecutionMode.WORKFLOW_AWARE,
    enable_caching: bool = False
):
    """
    Decorator to make any tool function workflow-aware.
    
    This decorator automatically:
    - Detects workflow context
    - Adds workflow information to tool execution
    - Integrates with the workflow tool system
    - Provides enhanced error handling and logging
    
    Args:
        tool_name: Name for the tool (defaults to function name)
        dependencies: Set of tool dependencies
        execution_mode: Default execution mode
        enable_caching: Whether to enable result caching
    
    Usage:
        @workflow_aware_tool(tool_name="enhanced_file_writer")
        async def write_file_tool(console, args):
            # Tool implementation remains unchanged
            pass
    """
    
    def decorator(func: Callable) -> Callable:
        # Get tool name from function if not provided
        actual_tool_name = tool_name or func.__name__
        
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Get workflow context
            workflow_context = await get_workflow_context()
            
            if workflow_context:
                # Add workflow context information to kwargs if tool supports it
                sig = inspect.signature(func)
                if 'workflow_context' in sig.parameters:
                    kwargs['workflow_context'] = {
                        'agent_name': workflow_context.agent_name,
                        'agent_color': workflow_context.agent_color,
                        'workflow_id': workflow_context.workflow_id,
                        'thread_id': workflow_context.thread_id
                    }
                
                # Add workflow execution ID for tracking
                if 'execution_id' in sig.parameters:
                    kwargs['execution_id'] = f"workflow_{workflow_context.workflow_id}_{int(asyncio.get_event_loop().time() * 1000)}"
                
                logger.debug(f"🎯 Executing workflow-aware tool {actual_tool_name} for agent {workflow_context.agent_name}")
            
            # Execute the original function
            try:
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                
                if workflow_context:
                    logger.debug(f"✅ Workflow-aware tool {actual_tool_name} completed successfully")
                
                return result
                
            except Exception as e:
                if workflow_context:
                    logger.error(f"❌ Workflow-aware tool {actual_tool_name} failed: {e}")
                raise
        
        # Register the wrapped tool with the integrator
        register_workflow_tool(
            tool_name=actual_tool_name,
            tool_function=wrapper,
            dependencies=dependencies,
            supports_workflow_context=True,
            execution_mode=execution_mode.value,
            enable_caching=enable_caching,
            original_function=func.__name__
        )
        
        logger.info(f"🔧 Enhanced tool {actual_tool_name} with workflow awareness")
        return wrapper
    
    return decorator


def make_tool_workflow_aware(
    tool_function: Callable,
    tool_name: Optional[str] = None,
    dependencies: Optional[set] = None
) -> Callable:
    """
    Programmatically make an existing tool workflow-aware.
    
    This function can be used to wrap existing tools without using decorators.
    
    Args:
        tool_function: The existing tool function
        tool_name: Name for the tool (defaults to function name)
        dependencies: Set of tool dependencies
    
    Returns:
        Workflow-aware version of the tool
    """
    actual_tool_name = tool_name or tool_function.__name__
    
    @functools.wraps(tool_function)
    async def workflow_aware_wrapper(*args, **kwargs):
        # Get workflow context
        workflow_context = await get_workflow_context()
        
        if workflow_context:
            # Inject workflow context if the tool can accept it
            sig = inspect.signature(tool_function)
            
            # Add workflow metadata to console if available
            if args and hasattr(args[0], 'print'):  # Likely a console object
                console = args[0]
                if hasattr(console, 'workflow_context'):
                    console.workflow_context = {
                        'agent_name': workflow_context.agent_name,
                        'agent_color': workflow_context.agent_color
                    }
            
            logger.debug(f"🎯 Executing enhanced tool {actual_tool_name} in workflow context")
        
        # Execute original tool
        if asyncio.iscoroutinefunction(tool_function):
            return await tool_function(*args, **kwargs)
        else:
            return tool_function(*args, **kwargs)
    
    # Register with integrator
    register_workflow_tool(
        tool_name=actual_tool_name,
        tool_function=workflow_aware_wrapper,
        dependencies=dependencies,
        supports_workflow_context=True,
        enhanced_version=True
    )
    
    return workflow_aware_wrapper


def auto_enhance_plugin_tools():
    """
    Automatically enhance all registered plugin tools with workflow awareness.
    
    This function scans for existing tool functions and makes them workflow-aware.
    """
    logger.info("🔧 Auto-enhancing plugin tools with workflow awareness")
    
    # List of known tool functions to enhance
    tool_mappings = [
        {
            'module': 'qx.plugins.write_file_plugin',
            'function': 'write_file_tool',
            'dependencies': set()
        },
        {
            'module': 'qx.plugins.read_file_plugin', 
            'function': 'read_file_tool',
            'dependencies': set()
        },
        {
            'module': 'qx.plugins.execute_shell_plugin',
            'function': 'execute_shell_tool',
            'dependencies': set()
        },
        {
            'module': 'qx.plugins.web_fetch_plugin',
            'function': 'web_fetch_tool',
            'dependencies': set()
        },
        {
            'module': 'qx.plugins.worktree_manager_plugin',
            'function': 'worktree_manager_tool',
            'dependencies': set()
        }
    ]
    
    enhanced_count = 0
    
    for tool_info in tool_mappings:
        try:
            # Import module and get function
            module_name = tool_info['module']
            function_name = tool_info['function']
            
            module = __import__(module_name, fromlist=[function_name])
            if hasattr(module, function_name):
                tool_function = getattr(module, function_name)
                
                # Create workflow-aware version
                enhanced_tool = make_tool_workflow_aware(
                    tool_function=tool_function,
                    tool_name=function_name,
                    dependencies=tool_info['dependencies']
                )
                
                # Replace the original function in the module
                setattr(module, f"{function_name}_workflow_aware", enhanced_tool)
                
                enhanced_count += 1
                logger.info(f"✅ Enhanced {module_name}.{function_name}")
                
        except Exception as e:
            logger.warning(f"⚠️ Could not enhance tool {tool_info}: {e}")
    
    logger.info(f"🎉 Auto-enhanced {enhanced_count} plugin tools with workflow awareness")


class WorkflowToolProxy:
    """
    Proxy class that intercepts tool calls and adds workflow awareness.
    
    This can be used to wrap entire tool modules or classes.
    """
    
    def __init__(self, target_object: Any, tool_prefix: str = ""):
        self._target = target_object
        self._tool_prefix = tool_prefix
        self._enhanced_methods = {}
        
        logger.debug(f"🔧 Created WorkflowToolProxy for {type(target_object).__name__}")
    
    def __getattr__(self, name: str):
        attr = getattr(self._target, name)
        
        # If it's a callable method, make it workflow-aware
        if callable(attr) and not name.startswith('_'):
            if name not in self._enhanced_methods:
                tool_name = f"{self._tool_prefix}{name}" if self._tool_prefix else name
                self._enhanced_methods[name] = make_tool_workflow_aware(
                    tool_function=attr,
                    tool_name=tool_name
                )
            
            return self._enhanced_methods[name]
        
        return attr
    
    def __setattr__(self, name: str, value: Any):
        if name.startswith('_'):
            super().__setattr__(name, value)
        else:
            setattr(self._target, name, value)


def create_workflow_tool_proxy(target_object: Any, tool_prefix: str = "") -> WorkflowToolProxy:
    """
    Create a workflow-aware proxy for an object with tool methods.
    
    Args:
        target_object: Object to proxy
        tool_prefix: Prefix to add to tool names
    
    Returns:
        Workflow-aware proxy object
    """
    return WorkflowToolProxy(target_object, tool_prefix)