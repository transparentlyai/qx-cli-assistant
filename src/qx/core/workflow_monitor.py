"""
Comprehensive Workflow Execution Monitoring and Debugging System.

This module provides real-time monitoring, debugging, and analytics capabilities
for the QX Unified LangGraph Workflow system including:
- Real-time execution tracking with visual representation
- Performance bottleneck detection and analysis  
- Error tracking with recovery suggestions
- Workflow visualization and state inspection
- Agent performance analytics
- Tool execution monitoring
- Memory and resource usage tracking
"""

import asyncio
import json
import logging
import time
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import threading
from contextlib import asynccontextmanager
import sys
from pathlib import Path

from qx.cli.theme import themed_console

logger = logging.getLogger(__name__)


class MonitoringLevel(Enum):
    """Monitoring detail levels."""
    MINIMAL = "minimal"       # Only critical events
    STANDARD = "standard"     # Standard monitoring
    DETAILED = "detailed"     # Detailed execution tracking  
    DEBUG = "debug"          # Full debug information


class ExecutionPhase(Enum):
    """Workflow execution phases."""
    INITIALIZATION = "initialization"
    ROUTING = "routing"
    AGENT_EXECUTION = "agent_execution"
    TOOL_EXECUTION = "tool_execution"
    SYNTHESIS = "synthesis"
    HUMAN_INTERACTION = "human_interaction"
    COMPLETION = "completion"
    ERROR_HANDLING = "error_handling"


@dataclass
class ExecutionEvent:
    """Individual execution event for monitoring."""
    timestamp: float
    phase: ExecutionPhase
    event_type: str  # "start", "end", "error", "warning", "info"
    component: str   # Agent name, tool name, or system component
    details: Dict[str, Any]
    duration: Optional[float] = None
    memory_usage: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "phase": self.phase.value,
            "event_type": self.event_type,
            "component": self.component,
            "details": self.details,
            "duration": self.duration,
            "memory_usage": self.memory_usage
        }


@dataclass 
class PerformanceMetrics:
    """Performance metrics for workflow components."""
    component_name: str
    total_executions: int = 0
    total_duration: float = 0.0
    average_duration: float = 0.0
    min_duration: float = float('inf')
    max_duration: float = 0.0
    error_count: int = 0
    success_rate: float = 1.0
    memory_peak: float = 0.0
    last_execution: Optional[float] = None
    
    def update(self, duration: float, success: bool, memory_usage: Optional[float] = None):
        """Update metrics with new execution data."""
        self.total_executions += 1
        self.total_duration += duration
        self.average_duration = self.total_duration / self.total_executions
        self.min_duration = min(self.min_duration, duration)
        self.max_duration = max(self.max_duration, duration)
        self.last_execution = time.time()
        
        if not success:
            self.error_count += 1
        
        self.success_rate = (self.total_executions - self.error_count) / self.total_executions
        
        if memory_usage:
            self.memory_peak = max(self.memory_peak, memory_usage)


@dataclass
class WorkflowExecution:
    """Complete workflow execution tracking."""
    execution_id: str
    start_time: float
    end_time: Optional[float] = None
    user_input: str = ""
    current_phase: ExecutionPhase = ExecutionPhase.INITIALIZATION
    events: List[ExecutionEvent] = field(default_factory=list)
    active_agents: Set[str] = field(default_factory=set)
    active_tools: Set[str] = field(default_factory=set)
    error_count: int = 0
    warning_count: int = 0
    total_duration: float = 0.0
    memory_peak: float = 0.0
    
    @property
    def is_active(self) -> bool:
        return self.end_time is None
    
    @property
    def duration(self) -> float:
        if self.end_time:
            return self.end_time - self.start_time
        return time.time() - self.start_time


class WorkflowMonitor:
    """
    Comprehensive workflow monitoring and debugging system.
    
    Provides real-time tracking, performance analytics, error detection,
    and debugging capabilities for the unified LangGraph workflow.
    """
    
    def __init__(self, monitoring_level: MonitoringLevel = MonitoringLevel.STANDARD):
        self.monitoring_level = monitoring_level
        self.active_executions: Dict[str, WorkflowExecution] = {}
        self.completed_executions: List[WorkflowExecution] = []
        self.performance_metrics: Dict[str, PerformanceMetrics] = {}
        
        # Real-time monitoring
        self.real_time_enabled = False
        self.visualization_enabled = False
        self.alert_thresholds = {
            "max_duration": 300.0,  # 5 minutes
            "max_memory": 1024.0,   # 1GB
            "error_rate": 0.1       # 10%
        }
        
        # Background monitoring thread
        self._monitor_thread: Optional[threading.Thread] = None
        self._monitor_stop_event = threading.Event()
        
        # Event listeners
        self._event_listeners: List[callable] = []
        
        logger.info(f"🔍 WorkflowMonitor initialized with {monitoring_level.value} monitoring level")
    
    def enable_real_time_monitoring(self, enable_visualization: bool = True):
        """Enable real-time monitoring with optional visualization."""
        self.real_time_enabled = True
        self.visualization_enabled = enable_visualization
        
        if not self._monitor_thread or not self._monitor_thread.is_alive():
            self._monitor_stop_event.clear()
            self._monitor_thread = threading.Thread(
                target=self._background_monitoring_loop,
                daemon=True
            )
            self._monitor_thread.start()
            logger.info("🔄 Real-time monitoring enabled")
    
    def disable_real_time_monitoring(self):
        """Disable real-time monitoring."""
        self.real_time_enabled = False
        if self._monitor_thread:
            self._monitor_stop_event.set()
            logger.info("⏹️ Real-time monitoring disabled")
    
    def add_event_listener(self, listener: callable):
        """Add an event listener for custom monitoring logic."""
        self._event_listeners.append(listener)
        logger.debug(f"📡 Added event listener: {listener.__name__}")
    
    @asynccontextmanager
    async def track_execution(self, execution_id: str, user_input: str = ""):
        """Context manager for tracking complete workflow execution."""
        execution = WorkflowExecution(
            execution_id=execution_id,
            start_time=time.time(),
            user_input=user_input
        )
        
        self.active_executions[execution_id] = execution
        
        try:
            if self.monitoring_level in [MonitoringLevel.DETAILED, MonitoringLevel.DEBUG]:
                logger.info(f"🚀 Started tracking execution: {execution_id}")
                
            yield execution
            
        except Exception as e:
            await self._record_event(
                execution_id=execution_id,
                phase=ExecutionPhase.ERROR_HANDLING,
                event_type="error",
                component="workflow",
                details={"error": str(e), "error_type": type(e).__name__}
            )
            raise
            
        finally:
            execution.end_time = time.time()
            execution.total_duration = execution.duration
            
            # Move to completed executions
            if execution_id in self.active_executions:
                del self.active_executions[execution_id]
            
            self.completed_executions.append(execution)
            
            # Maintain history limit
            if len(self.completed_executions) > 100:
                self.completed_executions = self.completed_executions[-100:]
            
            if self.monitoring_level in [MonitoringLevel.DETAILED, MonitoringLevel.DEBUG]:
                logger.info(f"✅ Completed tracking execution: {execution_id} ({execution.duration:.2f}s)")
    
    @asynccontextmanager 
    async def track_component(
        self, 
        execution_id: str, 
        component: str, 
        phase: ExecutionPhase,
        details: Optional[Dict[str, Any]] = None
    ):
        """Context manager for tracking individual component execution."""
        start_time = time.time()
        start_memory = self._get_memory_usage()
        
        await self._record_event(
            execution_id=execution_id,
            phase=phase,
            event_type="start",
            component=component,
            details=details or {},
            memory_usage=start_memory
        )
        
        try:
            yield
            
            # Successful completion
            end_time = time.time()
            duration = end_time - start_time
            end_memory = self._get_memory_usage()
            
            await self._record_event(
                execution_id=execution_id,
                phase=phase,
                event_type="end",
                component=component,
                details={"success": True},
                duration=duration,
                memory_usage=end_memory
            )
            
            # Update performance metrics
            self._update_performance_metrics(component, duration, True, end_memory)
            
        except Exception as e:
            # Error handling
            end_time = time.time()
            duration = end_time - start_time
            
            await self._record_event(
                execution_id=execution_id,
                phase=phase,
                event_type="error",
                component=component,
                details={
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "success": False
                },
                duration=duration
            )
            
            # Update performance metrics
            self._update_performance_metrics(component, duration, False)
            raise
    
    async def _record_event(
        self,
        execution_id: str,
        phase: ExecutionPhase,
        event_type: str,
        component: str,
        details: Dict[str, Any],
        duration: Optional[float] = None,
        memory_usage: Optional[float] = None
    ):
        """Record a monitoring event."""
        event = ExecutionEvent(
            timestamp=time.time(),
            phase=phase,
            event_type=event_type,
            component=component,
            details=details,
            duration=duration,
            memory_usage=memory_usage
        )
        
        # Add to active execution if it exists
        if execution_id in self.active_executions:
            execution = self.active_executions[execution_id]
            execution.events.append(event)
            execution.current_phase = phase
            
            # Update execution state
            if event_type == "error":
                execution.error_count += 1
            elif event_type == "warning":
                execution.warning_count += 1
                
            if memory_usage:
                execution.memory_peak = max(execution.memory_peak, memory_usage)
        
        # Real-time processing
        if self.real_time_enabled:
            await self._process_real_time_event(event, execution_id)
        
        # Notify event listeners
        for listener in self._event_listeners:
            try:
                await listener(event, execution_id)
            except Exception as e:
                logger.warning(f"⚠️ Event listener error: {e}")
        
        # Debug logging
        if self.monitoring_level == MonitoringLevel.DEBUG:
            logger.debug(f"📊 Event: {event.event_type} | {event.component} | {event.phase.value}")
    
    async def _process_real_time_event(self, event: ExecutionEvent, execution_id: str):
        """Process events in real-time for alerts and visualization."""
        
        # Check for performance alerts
        if event.duration and event.duration > self.alert_thresholds["max_duration"]:
            await self._trigger_alert(
                "PERFORMANCE",
                f"Component {event.component} exceeded maximum duration: {event.duration:.1f}s",
                event,
                execution_id
            )
        
        if event.memory_usage and event.memory_usage > self.alert_thresholds["max_memory"]:
            await self._trigger_alert(
                "MEMORY",
                f"Component {event.component} exceeded memory threshold: {event.memory_usage:.1f}MB",
                event,
                execution_id
            )
        
        # Error rate monitoring
        if event.component in self.performance_metrics:
            metrics = self.performance_metrics[event.component]
            if metrics.success_rate < (1.0 - self.alert_thresholds["error_rate"]):
                await self._trigger_alert(
                    "ERROR_RATE",
                    f"Component {event.component} error rate: {(1.0 - metrics.success_rate):.1%}",
                    event,
                    execution_id
                )
        
        # Real-time visualization
        if self.visualization_enabled:
            await self._update_visualization(event, execution_id)
    
    async def _trigger_alert(self, alert_type: str, message: str, event: ExecutionEvent, execution_id: str):
        """Trigger a monitoring alert."""
        alert_message = f"🚨 {alert_type} ALERT: {message}"
        
        # Log the alert
        logger.warning(alert_message)
        
        # Display in console if appropriate monitoring level
        if self.monitoring_level in [MonitoringLevel.DETAILED, MonitoringLevel.DEBUG]:
            themed_console.print(f"[yellow]{alert_message}[/]")
    
    async def _update_visualization(self, event: ExecutionEvent, execution_id: str):
        """Update real-time visualization (simplified version)."""
        if self.monitoring_level == MonitoringLevel.DEBUG:
            # Simple console-based visualization
            phase_emoji = {
                ExecutionPhase.INITIALIZATION: "🚀",
                ExecutionPhase.ROUTING: "🎯", 
                ExecutionPhase.AGENT_EXECUTION: "🤖",
                ExecutionPhase.TOOL_EXECUTION: "🔧",
                ExecutionPhase.SYNTHESIS: "🔗",
                ExecutionPhase.HUMAN_INTERACTION: "👤",
                ExecutionPhase.COMPLETION: "✅",
                ExecutionPhase.ERROR_HANDLING: "❌"
            }
            
            emoji = phase_emoji.get(event.phase, "📊")
            status = "🟢" if event.event_type == "end" else "🟡" if event.event_type == "start" else "🔴"
            
            viz_line = f"{emoji} {status} {event.component} | {event.phase.value}"
            if event.duration:
                viz_line += f" | {event.duration:.2f}s"
            
            themed_console.print(f"[dim]{viz_line}[/]")
    
    def _update_performance_metrics(
        self, 
        component: str, 
        duration: float, 
        success: bool, 
        memory_usage: Optional[float] = None
    ):
        """Update performance metrics for a component."""
        if component not in self.performance_metrics:
            self.performance_metrics[component] = PerformanceMetrics(component)
        
        self.performance_metrics[component].update(duration, success, memory_usage)
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024  # Convert to MB
        except ImportError:
            # Fallback if psutil not available
            import resource
            return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024  # Convert to MB
        except Exception:
            return 0.0
    
    def _background_monitoring_loop(self):
        """Background thread for continuous monitoring."""
        while not self._monitor_stop_event.is_set():
            try:
                # Check for stale executions
                current_time = time.time()
                stale_executions = []
                
                for exec_id, execution in self.active_executions.items():
                    if current_time - execution.start_time > 600:  # 10 minutes
                        stale_executions.append(exec_id)
                
                for exec_id in stale_executions:
                    logger.warning(f"⚠️ Stale execution detected: {exec_id}")
                
                # Resource monitoring
                current_memory = self._get_memory_usage()
                if current_memory > self.alert_thresholds["max_memory"]:
                    logger.warning(f"⚠️ High memory usage detected: {current_memory:.1f}MB")
                
                time.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                logger.error(f"❌ Error in monitoring loop: {e}")
                time.sleep(10)  # Wait longer on error
    
    def get_execution_summary(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive summary of an execution."""
        # Check active executions first
        execution = self.active_executions.get(execution_id)
        if not execution:
            # Check completed executions
            for completed in self.completed_executions:
                if completed.execution_id == execution_id:
                    execution = completed
                    break
        
        if not execution:
            return None
        
        # Calculate phase timings
        phase_timings = {}
        phase_events = {}
        
        for event in execution.events:
            phase_name = event.phase.value
            if phase_name not in phase_events:
                phase_events[phase_name] = []
            phase_events[phase_name].append(event)
        
        for phase_name, events in phase_events.items():
            start_events = [e for e in events if e.event_type == "start"]
            end_events = [e for e in events if e.event_type == "end"]
            
            if start_events and end_events:
                phase_start = min(e.timestamp for e in start_events)
                phase_end = max(e.timestamp for e in end_events)
                phase_timings[phase_name] = phase_end - phase_start
        
        return {
            "execution_id": execution.execution_id,
            "user_input": execution.user_input,
            "start_time": execution.start_time,
            "end_time": execution.end_time,
            "duration": execution.duration,
            "current_phase": execution.current_phase.value,
            "is_active": execution.is_active,
            "event_count": len(execution.events),
            "error_count": execution.error_count,
            "warning_count": execution.warning_count,
            "active_agents": list(execution.active_agents),
            "active_tools": list(execution.active_tools),
            "memory_peak": execution.memory_peak,
            "phase_timings": phase_timings,
            "events": [event.to_dict() for event in execution.events[-10:]]  # Last 10 events
        }
    
    def get_performance_analytics(self) -> Dict[str, Any]:
        """Get comprehensive performance analytics."""
        total_executions = len(self.completed_executions)
        if total_executions == 0:
            return {"message": "No completed executions to analyze"}
        
        # Overall statistics
        total_duration = sum(e.duration for e in self.completed_executions)
        avg_duration = total_duration / total_executions
        error_rate = sum(1 for e in self.completed_executions if e.error_count > 0) / total_executions
        
        # Component performance
        component_stats = {}
        for component, metrics in self.performance_metrics.items():
            component_stats[component] = {
                "total_executions": metrics.total_executions,
                "average_duration": metrics.average_duration,
                "min_duration": metrics.min_duration if metrics.min_duration != float('inf') else 0.0,
                "max_duration": metrics.max_duration,
                "success_rate": metrics.success_rate,
                "error_count": metrics.error_count,
                "memory_peak": metrics.memory_peak
            }
        
        # Identify bottlenecks
        bottlenecks = []
        for component, metrics in self.performance_metrics.items():
            if metrics.average_duration > 60.0:  # > 1 minute
                bottlenecks.append({
                    "component": component,
                    "average_duration": metrics.average_duration,
                    "reason": "High average duration"
                })
            if metrics.success_rate < 0.9:  # < 90% success rate
                bottlenecks.append({
                    "component": component,
                    "success_rate": metrics.success_rate,
                    "reason": "Low success rate"
                })
        
        return {
            "overview": {
                "total_executions": total_executions,
                "active_executions": len(self.active_executions),
                "average_duration": avg_duration,
                "error_rate": error_rate,
                "monitoring_level": self.monitoring_level.value,
                "real_time_enabled": self.real_time_enabled
            },
            "component_performance": component_stats,
            "bottlenecks": bottlenecks,
            "recent_executions": [
                {
                    "execution_id": e.execution_id,
                    "duration": e.duration,
                    "error_count": e.error_count,
                    "user_input": e.user_input[:50] + "..." if len(e.user_input) > 50 else e.user_input
                }
                for e in self.completed_executions[-5:]  # Last 5 executions
            ]
        }
    
    def generate_debug_report(self, execution_id: Optional[str] = None) -> str:
        """Generate a comprehensive debug report."""
        report_lines = []
        report_lines.append("🔍 QX Workflow Debug Report")
        report_lines.append("=" * 50)
        report_lines.append(f"Generated at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"Monitoring Level: {self.monitoring_level.value}")
        report_lines.append("")
        
        if execution_id:
            # Specific execution report
            summary = self.get_execution_summary(execution_id)
            if summary:
                report_lines.append(f"📊 Execution Report: {execution_id}")
                report_lines.append("-" * 30)
                report_lines.append(f"Duration: {summary['duration']:.2f}s")
                report_lines.append(f"Current Phase: {summary['current_phase']}")
                report_lines.append(f"Events: {summary['event_count']}")
                report_lines.append(f"Errors: {summary['error_count']}")
                report_lines.append(f"Warnings: {summary['warning_count']}")
                report_lines.append(f"Memory Peak: {summary['memory_peak']:.1f}MB")
                
                if summary['phase_timings']:
                    report_lines.append("\n⏱️ Phase Timings:")
                    for phase, duration in summary['phase_timings'].items():
                        report_lines.append(f"  {phase}: {duration:.2f}s")
            else:
                report_lines.append(f"❌ Execution {execution_id} not found")
        else:
            # General analytics report
            analytics = self.get_performance_analytics()
            
            if "overview" in analytics:
                overview = analytics["overview"]
                report_lines.append("📈 Performance Overview")
                report_lines.append("-" * 30)
                report_lines.append(f"Total Executions: {overview['total_executions']}")
                report_lines.append(f"Active Executions: {overview['active_executions']}")
                report_lines.append(f"Average Duration: {overview['average_duration']:.2f}s")
                report_lines.append(f"Error Rate: {overview['error_rate']:.1%}")
                
                if analytics.get("bottlenecks"):
                    report_lines.append("\n⚠️ Performance Bottlenecks:")
                    for bottleneck in analytics["bottlenecks"]:
                        report_lines.append(f"  {bottleneck['component']}: {bottleneck['reason']}")
                
                if analytics.get("component_performance"):
                    report_lines.append("\n🔧 Component Performance:")
                    for comp, stats in analytics["component_performance"].items():
                        report_lines.append(f"  {comp}: {stats['average_duration']:.2f}s avg, {stats['success_rate']:.1%} success")
        
        return "\n".join(report_lines)
    
    async def cleanup(self):
        """Clean up monitoring resources."""
        logger.info("🧹 Cleaning up WorkflowMonitor")
        
        # Stop background monitoring
        self.disable_real_time_monitoring()
        
        # Clear event listeners
        self._event_listeners.clear()
        
        # Archive active executions
        for execution in self.active_executions.values():
            execution.end_time = time.time()
            self.completed_executions.append(execution)
        
        self.active_executions.clear()
        
        logger.info("✅ WorkflowMonitor cleanup completed")


# Global monitor instance
_workflow_monitor: Optional[WorkflowMonitor] = None


def get_workflow_monitor(monitoring_level: MonitoringLevel = MonitoringLevel.STANDARD) -> WorkflowMonitor:
    """Get the global workflow monitor instance."""
    global _workflow_monitor
    if _workflow_monitor is None:
        _workflow_monitor = WorkflowMonitor(monitoring_level)
    return _workflow_monitor


async def set_monitoring_level(level: MonitoringLevel):
    """Set the global monitoring level."""
    monitor = get_workflow_monitor()
    monitor.monitoring_level = level
    logger.info(f"🔍 Monitoring level set to: {level.value}")


# Convenience functions for easy integration
from contextlib import asynccontextmanager

@asynccontextmanager
async def track_workflow_execution(execution_id: str, user_input: str = ""):
    """Context manager for tracking workflow execution."""
    monitor = get_workflow_monitor()
    async with monitor.track_execution(execution_id, user_input) as execution:
        yield execution


@asynccontextmanager
async def track_agent_execution(execution_id: str, agent_name: str, details: Optional[Dict] = None):
    """Context manager for tracking agent execution."""
    monitor = get_workflow_monitor()
    async with monitor.track_component(
        execution_id, 
        agent_name, 
        ExecutionPhase.AGENT_EXECUTION, 
        details
    ) as component:
        yield component


async def track_tool_execution(execution_id: str, tool_name: str, details: Optional[Dict] = None):
    """Context manager for tracking tool execution."""
    monitor = get_workflow_monitor()
    return monitor.track_component(
        execution_id,
        tool_name,
        ExecutionPhase.TOOL_EXECUTION,
        details
    )