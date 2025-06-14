"""
Enhanced Tool Integration with Workflow Context Propagation.

This module provides advanced tool integration capabilities for the unified
LangGraph workflow, including:
- Tool execution context awareness
- Workflow state propagation to tools
- Inter-tool communication and coordination
- Tool result caching and optimization
- Tool error recovery and fallback mechanisms
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional, Set, Tuple, Union, Callable
from dataclasses import dataclass, field
from enum import Enum

from qx.core.workflow_context import get_workflow_context, WorkflowContext

logger = logging.getLogger(__name__)


class ToolExecutionMode(Enum):
    """Tool execution modes for different workflow contexts."""
    STANDALONE = "standalone"  # Tool runs independently
    WORKFLOW_AWARE = "workflow_aware"  # Tool has access to workflow context
    COORDINATED = "coordinated"  # Tool coordinates with other tools
    CACHED = "cached"  # Tool uses cached results when available


@dataclass
class ToolExecutionContext:
    """Enhanced context for tool execution within workflows."""
    tool_name: str
    workflow_context: Optional[WorkflowContext]
    execution_mode: ToolExecutionMode
    agent_name: Optional[str] = None
    agent_color: Optional[str] = None
    task_description: Optional[str] = None
    workflow_state: Dict[str, Any] = field(default_factory=dict)
    tool_chain: List[str] = field(default_factory=list)  # Tools executed in this chain
    execution_id: str = field(default_factory=lambda: f"exec_{int(time.time() * 1000)}")
    
    def is_in_workflow(self) -> bool:
        """Check if tool is executing within a workflow."""
        return self.workflow_context is not None
    
    def get_agent_info(self) -> Tuple[Optional[str], Optional[str]]:
        """Get agent name and color for UI styling."""
        if self.workflow_context:
            return self.workflow_context.get_agent_info()
        return self.agent_name, self.agent_color
    
    def add_tool_to_chain(self, tool_name: str):
        """Add tool to execution chain for tracking."""
        if tool_name not in self.tool_chain:
            self.tool_chain.append(tool_name)


@dataclass
class ToolResult:
    """Enhanced tool result with workflow integration metadata."""
    tool_name: str
    success: bool
    result: Any
    execution_time: float
    context: ToolExecutionContext
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "tool_name": self.tool_name,
            "success": self.success,
            "result": self.result,
            "execution_time": self.execution_time,
            "error": self.error,
            "metadata": self.metadata,
            "execution_id": self.context.execution_id,
            "agent_name": self.context.agent_name
        }


class WorkflowToolIntegrator:
    """
    Enhanced tool integrator that provides workflow-aware tool execution,
    context propagation, and advanced coordination capabilities.
    """
    
    def __init__(self):
        self.tool_registry: Dict[str, Callable] = {}
        self.tool_metadata: Dict[str, Dict[str, Any]] = {}
        self.execution_cache: Dict[str, ToolResult] = {}
        self.tool_dependencies: Dict[str, Set[str]] = {}
        
        # Performance and coordination tracking
        self.execution_metrics = {
            "total_executions": 0,
            "cache_hits": 0,
            "workflow_executions": 0,
            "tool_performance": {},
            "coordination_events": 0
        }
        
        logger.info("🔧 WorkflowToolIntegrator initialized")
    
    def register_tool(
        self, 
        tool_name: str, 
        tool_function: Callable,
        dependencies: Optional[Set[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Register a tool with the integrator."""
        self.tool_registry[tool_name] = tool_function
        self.tool_dependencies[tool_name] = dependencies or set()
        self.tool_metadata[tool_name] = metadata or {}
        
        logger.debug(f"🔧 Registered tool: {tool_name} with {len(dependencies or [])} dependencies")
    
    async def execute_tool_with_context(
        self,
        tool_name: str,
        tool_args: Dict[str, Any],
        execution_mode: ToolExecutionMode = ToolExecutionMode.WORKFLOW_AWARE,
        task_description: Optional[str] = None
    ) -> ToolResult:
        """Execute a tool with enhanced workflow context integration."""
        start_time = time.time()
        
        try:
            # Get current workflow context
            workflow_context = await get_workflow_context()
            
            # Create enhanced execution context
            exec_context = ToolExecutionContext(
                tool_name=tool_name,
                workflow_context=workflow_context,
                execution_mode=execution_mode,
                task_description=task_description
            )
            
            if workflow_context:
                exec_context.agent_name, exec_context.agent_color = workflow_context.get_agent_info()
                self.execution_metrics["workflow_executions"] += 1
                logger.info(f"🎯 Executing tool {tool_name} in workflow context for agent {exec_context.agent_name}")
            else:
                logger.info(f"🔧 Executing tool {tool_name} in standalone mode")
            
            # Check cache if appropriate
            if execution_mode == ToolExecutionMode.CACHED:
                cache_key = self._generate_cache_key(tool_name, tool_args, exec_context)
                cached_result = self.execution_cache.get(cache_key)
                if cached_result:
                    self.execution_metrics["cache_hits"] += 1
                    logger.debug(f"🎯 Cache hit for tool {tool_name}")
                    return cached_result
            
            # Execute tool with context
            result = await self._execute_tool_core(tool_name, tool_args, exec_context)
            
            # Create enhanced result
            execution_time = time.time() - start_time
            tool_result = ToolResult(
                tool_name=tool_name,
                success=True,
                result=result,
                execution_time=execution_time,
                context=exec_context,
                metadata={
                    "execution_mode": execution_mode.value,
                    "workflow_aware": exec_context.is_in_workflow(),
                    "tool_chain": exec_context.tool_chain.copy()
                }
            )
            
            # Cache result if appropriate
            if execution_mode == ToolExecutionMode.CACHED:
                cache_key = self._generate_cache_key(tool_name, tool_args, exec_context)
                self.execution_cache[cache_key] = tool_result
            
            # Update metrics
            self._update_tool_metrics(tool_name, execution_time, True)
            
            logger.info(f"✅ Tool {tool_name} executed successfully in {execution_time:.2f}s")
            return tool_result
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"❌ Tool {tool_name} execution failed: {e}", exc_info=True)
            
            # Create error result
            error_result = ToolResult(
                tool_name=tool_name,
                success=False,
                result=None,
                execution_time=execution_time,
                context=exec_context,
                error=str(e)
            )
            
            # Update metrics
            self._update_tool_metrics(tool_name, execution_time, False)
            
            return error_result
    
    async def _execute_tool_core(
        self, 
        tool_name: str, 
        tool_args: Dict[str, Any], 
        context: ToolExecutionContext
    ) -> Any:
        """Core tool execution with context propagation."""
        if tool_name not in self.tool_registry:
            raise ValueError(f"Tool {tool_name} not registered")
        
        tool_function = self.tool_registry[tool_name]
        context.add_tool_to_chain(tool_name)
        
        # Prepare enhanced arguments with context
        enhanced_args = tool_args.copy()
        
        # Add workflow context to tool args if the tool supports it
        if context.is_in_workflow() and self._tool_supports_context(tool_name):
            enhanced_args['workflow_context'] = {
                'agent_name': context.agent_name,
                'agent_color': context.agent_color,
                'task_description': context.task_description,
                'execution_id': context.execution_id,
                'tool_chain': context.tool_chain
            }
        
        # Execute tool with timeout and context
        try:
            if asyncio.iscoroutinefunction(tool_function):
                result = await asyncio.wait_for(
                    tool_function(**enhanced_args),
                    timeout=300.0  # 5 minute timeout
                )
            else:
                result = await asyncio.to_thread(tool_function, **enhanced_args)
            
            return result
            
        except asyncio.TimeoutError:
            raise Exception(f"Tool {tool_name} execution timed out after 5 minutes")
    
    async def execute_coordinated_tool_chain(
        self,
        tool_chain: List[Tuple[str, Dict[str, Any]]],
        task_description: Optional[str] = None
    ) -> List[ToolResult]:
        """Execute a coordinated chain of tools with shared context."""
        logger.info(f"🔗 Executing coordinated tool chain: {[tool[0] for tool in tool_chain]}")
        
        results = []
        shared_context = {}
        
        for i, (tool_name, tool_args) in enumerate(tool_chain):
            # Add shared context from previous tools
            enhanced_args = tool_args.copy()
            enhanced_args['shared_context'] = shared_context
            enhanced_args['chain_position'] = i
            enhanced_args['chain_total'] = len(tool_chain)
            
            # Execute tool
            result = await self.execute_tool_with_context(
                tool_name=tool_name,
                tool_args=enhanced_args,
                execution_mode=ToolExecutionMode.COORDINATED,
                task_description=task_description
            )
            
            results.append(result)
            
            # Update shared context with result
            if result.success:
                shared_context[f"{tool_name}_result"] = result.result
                shared_context[f"{tool_name}_metadata"] = result.metadata
            else:
                logger.warning(f"⚠️ Tool {tool_name} failed in chain, continuing with remaining tools")
        
        self.execution_metrics["coordination_events"] += 1
        logger.info(f"✅ Coordinated tool chain completed: {len([r for r in results if r.success])}/{len(results)} successful")
        
        return results
    
    def _tool_supports_context(self, tool_name: str) -> bool:
        """Check if a tool supports workflow context parameters."""
        metadata = self.tool_metadata.get(tool_name, {})
        return metadata.get('supports_workflow_context', False)
    
    def _generate_cache_key(
        self, 
        tool_name: str, 
        tool_args: Dict[str, Any], 
        context: ToolExecutionContext
    ) -> str:
        """Generate cache key for tool execution."""
        # Create deterministic key from tool name, args, and relevant context
        import hashlib
        import json
        
        cache_data = {
            'tool_name': tool_name,
            'args': sorted(tool_args.items()),
            'agent_name': context.agent_name,
            'task_description': context.task_description
        }
        
        cache_str = json.dumps(cache_data, sort_keys=True)
        return hashlib.md5(cache_str.encode()).hexdigest()
    
    def _update_tool_metrics(self, tool_name: str, execution_time: float, success: bool):
        """Update tool performance metrics."""
        self.execution_metrics["total_executions"] += 1
        
        if tool_name not in self.execution_metrics["tool_performance"]:
            self.execution_metrics["tool_performance"][tool_name] = {
                "executions": 0,
                "successes": 0,
                "total_time": 0.0,
                "avg_time": 0.0
            }
        
        tool_metrics = self.execution_metrics["tool_performance"][tool_name]
        tool_metrics["executions"] += 1
        tool_metrics["total_time"] += execution_time
        tool_metrics["avg_time"] = tool_metrics["total_time"] / tool_metrics["executions"]
        
        if success:
            tool_metrics["successes"] += 1
    
    def get_tool_metrics(self) -> Dict[str, Any]:
        """Get comprehensive tool execution metrics."""
        return {
            "execution_summary": {
                "total_executions": self.execution_metrics["total_executions"],
                "cache_hits": self.execution_metrics["cache_hits"],
                "workflow_executions": self.execution_metrics["workflow_executions"],
                "coordination_events": self.execution_metrics["coordination_events"],
                "cache_hit_rate": (
                    self.execution_metrics["cache_hits"] / max(self.execution_metrics["total_executions"], 1)
                )
            },
            "tool_performance": self.execution_metrics["tool_performance"].copy(),
            "registered_tools": list(self.tool_registry.keys()),
            "tool_dependencies": {
                tool: list(deps) for tool, deps in self.tool_dependencies.items()
            }
        }
    
    def clear_cache(self):
        """Clear tool execution cache."""
        cache_size = len(self.execution_cache)
        self.execution_cache.clear()
        logger.info(f"🗑️ Cleared tool cache: {cache_size} entries removed")
    
    async def validate_tool_dependencies(self, tool_name: str) -> bool:
        """Validate that all tool dependencies are available."""
        if tool_name not in self.tool_dependencies:
            return True
        
        dependencies = self.tool_dependencies[tool_name]
        missing_deps = []
        
        for dep in dependencies:
            if dep not in self.tool_registry:
                missing_deps.append(dep)
        
        if missing_deps:
            logger.error(f"❌ Tool {tool_name} missing dependencies: {missing_deps}")
            return False
        
        logger.debug(f"✅ Tool {tool_name} dependencies validated")
        return True


# Global tool integrator instance
_workflow_tool_integrator: Optional[WorkflowToolIntegrator] = None


def get_workflow_tool_integrator() -> WorkflowToolIntegrator:
    """Get or create the global workflow tool integrator."""
    global _workflow_tool_integrator
    if _workflow_tool_integrator is None:
        _workflow_tool_integrator = WorkflowToolIntegrator()
    return _workflow_tool_integrator


async def execute_workflow_aware_tool(
    tool_name: str,
    tool_args: Dict[str, Any],
    execution_mode: ToolExecutionMode = ToolExecutionMode.WORKFLOW_AWARE,
    task_description: Optional[str] = None
) -> ToolResult:
    """
    Convenience function for executing tools with workflow awareness.
    
    This is the main entry point for workflow-aware tool execution.
    """
    integrator = get_workflow_tool_integrator()
    return await integrator.execute_tool_with_context(
        tool_name=tool_name,
        tool_args=tool_args,
        execution_mode=execution_mode,
        task_description=task_description
    )


def register_workflow_tool(
    tool_name: str,
    tool_function: Callable,
    dependencies: Optional[Set[str]] = None,
    supports_workflow_context: bool = True,
    **metadata
):
    """
    Register a tool for workflow-aware execution.
    
    Args:
        tool_name: Name of the tool
        tool_function: Function to execute
        dependencies: Set of tool names this tool depends on
        supports_workflow_context: Whether tool can accept workflow context
        **metadata: Additional tool metadata
    """
    integrator = get_workflow_tool_integrator()
    
    # Add workflow context support to metadata
    tool_metadata = metadata.copy()
    tool_metadata['supports_workflow_context'] = supports_workflow_context
    
    integrator.register_tool(
        tool_name=tool_name,
        tool_function=tool_function,
        dependencies=dependencies,
        metadata=tool_metadata
    )
    
    logger.info(f"🔧 Registered workflow tool: {tool_name} (context_aware: {supports_workflow_context})")