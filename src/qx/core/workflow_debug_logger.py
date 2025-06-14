"""
Comprehensive Debugging System for QX Unified LangGraph Workflow.

This module implements multi-level logging strategy with structured patterns
for graph execution, node operations, human interactions, tool execution,
and performance monitoring as outlined in Phase 4.
"""

import json
import logging
import time
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass
from enum import Enum
import threading
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class LogLevel(Enum):
    """Debug logging levels for different components."""
    MINIMAL = "minimal"     # Only critical events
    STANDARD = "standard"   # Standard operations
    DETAILED = "detailed"   # Detailed execution flow
    VERBOSE = "verbose"     # All debug information


@dataclass
class ExecutionContext:
    """Execution context for tracking workflow state."""
    thread_id: str
    execution_id: str
    current_node: Optional[str] = None
    start_time: float = 0.0
    node_timings: Dict[str, float] = None
    error_context: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.node_timings is None:
            self.node_timings = {}
        if self.error_context is None:
            self.error_context = {}


class WorkflowDebugLogger:
    """
    Comprehensive debugging logger for LangGraph workflow execution.
    
    Implements structured logging patterns for:
    - Graph execution flow
    - Node operations with timing
    - Human interactions and interrupts
    - Tool execution details
    - Error context and performance metrics
    """
    
    def __init__(self, log_level: LogLevel = LogLevel.STANDARD):
        self.log_level = log_level
        self.execution_contexts: Dict[str, ExecutionContext] = {}
        self._lock = threading.Lock()
        
        # Performance tracking
        self.performance_metrics = {
            "total_executions": 0,
            "node_performance": {},
            "error_counts": {},
            "interrupt_counts": {},
            "tool_performance": {}
        }
        
        logger.info(f"WorkflowDebugLogger initialized with {log_level.value} logging level")
    
    def set_log_level(self, level: LogLevel):
        """Set the debugging log level."""
        self.log_level = level
        logger.info(f"Debug logging level set to: {level.value}")
    
    # Graph Execution Logging
    def log_graph_start(self, thread_id: str, execution_id: str, user_input: str):
        """Log LangGraph execution start."""
        with self._lock:
            context = ExecutionContext(
                thread_id=thread_id,
                execution_id=execution_id,
                start_time=time.time()
            )
            self.execution_contexts[execution_id] = context
        
        logger.info(f"LangGraph START: thread_id={thread_id}, execution_id={execution_id}, user_input='{user_input[:100]}...'")
        
        if self.log_level in [LogLevel.DETAILED, LogLevel.VERBOSE]:
            logger.debug(f"LangGraph START Details: full_input='{user_input}'")
    
    def log_graph_state(self, execution_id: str, current_state: Dict[str, Any]):
        """Log current graph state."""
        if self.log_level in [LogLevel.DETAILED, LogLevel.VERBOSE]:
            # Filter sensitive data for logging
            safe_state = {k: str(v)[:200] if len(str(v)) > 200 else v 
                         for k, v in current_state.items() 
                         if k not in ['messages', 'error_context']}
            logger.debug(f"Graph State [{execution_id}]: {json.dumps(safe_state, indent=2)}")
    
    def log_next_nodes(self, execution_id: str, next_nodes: List[str]):
        """Log next nodes to be executed."""
        if self.log_level in [LogLevel.DETAILED, LogLevel.VERBOSE]:
            logger.debug(f"Next Nodes [{execution_id}]: {next_nodes}")
    
    def log_graph_complete(self, execution_id: str, total_duration: float, result_summary: str):
        """Log LangGraph execution completion."""
        context = self.execution_contexts.get(execution_id)
        if context:
            with self._lock:
                del self.execution_contexts[execution_id]
        
        logger.info(f"LangGraph COMPLETE: execution_id={execution_id}, duration={total_duration:.3f}s, result='{result_summary[:100]}...'")
        
        if self.log_level in [LogLevel.DETAILED, LogLevel.VERBOSE] and context:
            logger.debug(f"LangGraph Performance [{execution_id}]: node_timings={context.node_timings}")
        
        # Update performance metrics
        self.performance_metrics["total_executions"] += 1
    
    # Node Execution Logging
    @contextmanager
    def log_node_execution(self, execution_id: str, node_name: str, agent_name: Optional[str] = None):
        """Context manager for node execution logging with timing."""
        start_time = time.time()
        
        # Log node entry
        if agent_name:
            logger.info(f"Node ENTER: {node_name}, agent={agent_name}, execution_id={execution_id}")
        else:
            logger.info(f"Node ENTER: {node_name}, execution_id={execution_id}")
        
        # Update context
        context = self.execution_contexts.get(execution_id)
        if context:
            context.current_node = node_name
        
        try:
            yield
            
            # Successful completion
            duration = time.time() - start_time
            duration_ms = duration * 1000
            
            logger.info(f"Node EXIT: {node_name}, duration={duration_ms:.1f}ms")
            
            # Update performance tracking
            if context:
                context.node_timings[node_name] = duration
            
            if node_name not in self.performance_metrics["node_performance"]:
                self.performance_metrics["node_performance"][node_name] = {
                    "total_executions": 0,
                    "total_duration": 0.0,
                    "avg_duration": 0.0
                }
            
            perf = self.performance_metrics["node_performance"][node_name]
            perf["total_executions"] += 1
            perf["total_duration"] += duration
            perf["avg_duration"] = perf["total_duration"] / perf["total_executions"]
            
        except Exception as e:
            # Error handling
            duration = time.time() - start_time
            duration_ms = duration * 1000
            
            logger.error(f"Node ERROR: {node_name}, duration={duration_ms:.1f}ms, error={str(e)}")
            
            # Update error context
            if context:
                context.error_context = {
                    "node": node_name,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "duration": duration
                }
            
            # Update error counts
            error_key = f"{node_name}_{type(e).__name__}"
            self.performance_metrics["error_counts"][error_key] = \
                self.performance_metrics["error_counts"].get(error_key, 0) + 1
            
            raise
    
    def log_node_input(self, execution_id: str, node_name: str, node_input: Dict[str, Any]):
        """Log node input data."""
        if self.log_level == LogLevel.VERBOSE:
            safe_input = {k: str(v)[:100] if len(str(v)) > 100 else v 
                         for k, v in node_input.items() 
                         if k not in ['messages']}
            logger.debug(f"Node Input [{node_name}]: {json.dumps(safe_input, indent=2)}")
    
    def log_node_output(self, execution_id: str, node_name: str, node_output: Dict[str, Any]):
        """Log node output data."""
        if self.log_level == LogLevel.VERBOSE:
            safe_output = {k: str(v)[:100] if len(str(v)) > 100 else v 
                          for k, v in node_output.items() 
                          if k not in ['messages']}
            logger.debug(f"Node Output [{node_name}]: {json.dumps(safe_output, indent=2)}")
    
    # Human Interaction Logging
    def log_interrupt_start(self, execution_id: str, interrupt_type: str, payload: Dict[str, Any]):
        """Log interrupt initiation."""
        logger.info(f"INTERRUPT: type={interrupt_type}, execution_id={execution_id}")
        
        if self.log_level in [LogLevel.DETAILED, LogLevel.VERBOSE]:
            safe_payload = {k: str(v)[:100] if len(str(v)) > 100 else v for k, v in payload.items()}
            logger.debug(f"INTERRUPT Payload [{interrupt_type}]: {json.dumps(safe_payload, indent=2)}")
        
        # Update interrupt counts
        self.performance_metrics["interrupt_counts"][interrupt_type] = \
            self.performance_metrics["interrupt_counts"].get(interrupt_type, 0) + 1
    
    def log_human_response(self, execution_id: str, human_response: str):
        """Log human response to interrupt."""
        logger.info(f"Human Response [{execution_id}]: '{human_response[:100]}...'")
        
        if self.log_level == LogLevel.VERBOSE:
            logger.debug(f"Human Response Full [{execution_id}]: '{human_response}'")
    
    def log_interrupt_resume(self, execution_id: str, interrupt_type: str):
        """Log workflow resumption after interrupt."""
        logger.info(f"RESUME: continuing from {interrupt_type} interrupt, execution_id={execution_id}")
    
    # Tool Execution Logging
    @contextmanager
    def log_tool_execution(self, execution_id: str, tool_name: str, tool_args: Dict[str, Any]):
        """Context manager for tool execution logging."""
        start_time = time.time()
        
        # Log tool call
        if self.log_level in [LogLevel.DETAILED, LogLevel.VERBOSE]:
            safe_args = {k: str(v)[:100] if len(str(v)) > 100 else v for k, v in tool_args.items()}
            logger.debug(f"Tool CALL: {tool_name}, args={json.dumps(safe_args)}")
        else:
            logger.debug(f"Tool CALL: {tool_name}")
        
        try:
            yield
            
            # Successful completion
            duration = time.time() - start_time
            duration_ms = duration * 1000
            
            logger.debug(f"Tool COMPLETE: {tool_name}, duration={duration_ms:.1f}ms")
            
            # Update tool performance
            if tool_name not in self.performance_metrics["tool_performance"]:
                self.performance_metrics["tool_performance"][tool_name] = {
                    "total_calls": 0,
                    "total_duration": 0.0,
                    "avg_duration": 0.0,
                    "error_count": 0
                }
            
            perf = self.performance_metrics["tool_performance"][tool_name]
            perf["total_calls"] += 1
            perf["total_duration"] += duration
            perf["avg_duration"] = perf["total_duration"] / perf["total_calls"]
            
        except Exception as e:
            # Error handling
            duration = time.time() - start_time
            duration_ms = duration * 1000
            
            logger.error(f"Tool ERROR: {tool_name}, duration={duration_ms:.1f}ms, error={str(e)}")
            
            # Update error tracking
            if tool_name in self.performance_metrics["tool_performance"]:
                self.performance_metrics["tool_performance"][tool_name]["error_count"] += 1
            
            raise
    
    def log_tool_result(self, execution_id: str, tool_name: str, tool_result: Any):
        """Log tool execution result."""
        if self.log_level == LogLevel.VERBOSE:
            result_str = str(tool_result)[:200] if tool_result else "None"
            logger.debug(f"Tool RESULT [{tool_name}]: {result_str}")
    
    # Error and Performance Logging
    def log_workflow_error(self, execution_id: str, error: Exception, error_state: Dict[str, Any]):
        """Log comprehensive workflow error with context."""
        context = self.execution_contexts.get(execution_id)
        
        error_info = {
            "execution_id": execution_id,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "current_node": context.current_node if context else "unknown",
            "error_state": {k: str(v)[:100] for k, v in error_state.items()}
        }
        
        logger.error(f"Workflow ERROR: {json.dumps(error_info, indent=2)}")
        
        # Log full execution context if available
        if context and self.log_level in [LogLevel.DETAILED, LogLevel.VERBOSE]:
            logger.error(f"Error Context [{execution_id}]: node_timings={context.node_timings}")
    
    def log_performance_summary(self, execution_id: str):
        """Log performance summary for execution."""
        context = self.execution_contexts.get(execution_id)
        if not context:
            return
        
        total_time = time.time() - context.start_time
        total_time_ms = total_time * 1000
        
        logger.info(f"Performance Summary [{execution_id}]: total_duration={total_time_ms:.1f}ms")
        
        if self.log_level in [LogLevel.DETAILED, LogLevel.VERBOSE]:
            logger.debug(f"Performance Details [{execution_id}]: node_times={context.node_timings}")
    
    # Checkpoint State Logging
    def log_checkpoint_save(self, thread_id: str, state_keys: List[str]):
        """Log checkpoint save operation."""
        if self.log_level in [LogLevel.DETAILED, LogLevel.VERBOSE]:
            logger.debug(f"Checkpoint SAVE: thread_id={thread_id}, state_keys={state_keys}")
    
    def log_checkpoint_load(self, thread_id: str, loaded_state: Dict[str, Any]):
        """Log checkpoint load operation."""
        if self.log_level in [LogLevel.DETAILED, LogLevel.VERBOSE]:
            safe_state = {k: str(v)[:50] for k, v in loaded_state.items() if k != 'messages'}
            logger.debug(f"Checkpoint LOAD: thread_id={thread_id}, loaded_state={safe_state}")
    
    # Agent Context Logging
    def log_agent_context(self, agent_name: str, agent_color: Optional[str], tool_count: int):
        """Log agent context setup."""
        logger.info(f"Agent Context: name={agent_name}, color={agent_color}, tools={tool_count}")
    
    def log_agent_config(self, agent_name: str, agent_config: Dict[str, Any]):
        """Log agent configuration details."""
        if self.log_level in [LogLevel.DETAILED, LogLevel.VERBOSE]:
            safe_config = {k: str(v)[:100] for k, v in agent_config.items()}
            logger.debug(f"Agent Config [{agent_name}]: {json.dumps(safe_config, indent=2)}")
    
    # Console Manager Integration Logging
    def log_console_render(self, title: str, color: Optional[str], content_length: int):
        """Log console rendering operations."""
        if self.log_level == LogLevel.VERBOSE:
            logger.debug(f"Console Render: title={title}, color={color}, content_length={content_length}")
    
    def log_console_interrupt_handler(self, handler_type: str, response: str):
        """Log console interrupt handler operations."""
        if self.log_level in [LogLevel.DETAILED, LogLevel.VERBOSE]:
            logger.debug(f"Console Interrupt Handler: type={handler_type}, response='{response[:50]}...'")
    
    # Diagnostic Features
    def log_graph_structure(self, nodes: List[str], edges: List[tuple]):
        """Log complete graph structure at startup."""
        logger.info(f"Graph Structure: nodes={len(nodes)}, edges={len(edges)}")
        
        if self.log_level in [LogLevel.DETAILED, LogLevel.VERBOSE]:
            logger.debug(f"Graph Nodes: {nodes}")
            logger.debug(f"Graph Edges: {edges}")
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get comprehensive performance metrics."""
        return {
            "summary": self.performance_metrics.copy(),
            "active_executions": len(self.execution_contexts),
            "log_level": self.log_level.value
        }
    
    def generate_debug_report(self, execution_id: Optional[str] = None) -> str:
        """Generate comprehensive debug report."""
        lines = []
        lines.append("QX Workflow Debug Report")
        lines.append("=" * 50)
        lines.append(f"Generated at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"Log Level: {self.log_level.value}")
        lines.append("")
        
        if execution_id and execution_id in self.execution_contexts:
            # Specific execution report
            context = self.execution_contexts[execution_id]
            lines.append(f"Execution Report: {execution_id}")
            lines.append("-" * 30)
            lines.append(f"Thread ID: {context.thread_id}")
            lines.append(f"Current Node: {context.current_node}")
            lines.append(f"Node Timings: {context.node_timings}")
            if context.error_context:
                lines.append(f"Error Context: {context.error_context}")
        else:
            # Performance summary
            metrics = self.performance_metrics
            lines.append("Performance Summary")
            lines.append("-" * 30)
            lines.append(f"Total Executions: {metrics['total_executions']}")
            lines.append(f"Active Executions: {len(self.execution_contexts)}")
            
            if metrics["node_performance"]:
                lines.append("\nNode Performance:")
                for node, perf in metrics["node_performance"].items():
                    lines.append(f"  {node}: {perf['avg_duration']:.3f}s avg ({perf['total_executions']} executions)")
            
            if metrics["tool_performance"]:
                lines.append("\nTool Performance:")
                for tool, perf in metrics["tool_performance"].items():
                    lines.append(f"  {tool}: {perf['avg_duration']:.3f}s avg ({perf['total_calls']} calls, {perf['error_count']} errors)")
            
            if metrics["error_counts"]:
                lines.append("\nError Counts:")
                for error, count in metrics["error_counts"].items():
                    lines.append(f"  {error}: {count}")
        
        return "\n".join(lines)


# Global debug logger instance
_debug_logger: Optional[WorkflowDebugLogger] = None


def get_debug_logger(log_level: LogLevel = LogLevel.STANDARD) -> WorkflowDebugLogger:
    """Get the global debug logger instance."""
    global _debug_logger
    if _debug_logger is None:
        _debug_logger = WorkflowDebugLogger(log_level)
    return _debug_logger


def set_debug_log_level(level: LogLevel):
    """Set the global debug logging level."""
    debug_logger = get_debug_logger()
    debug_logger.set_log_level(level)