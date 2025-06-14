"""
Workflow-Enhanced Tool Processor.

This module provides an enhanced version of the tool processor that integrates
with the workflow tool system for better context awareness, coordination,
and performance monitoring.
"""

import asyncio
import json
import logging
import time
from typing import Any, Callable, Dict, List, Type, cast

from openai.types.chat import ChatCompletionMessageParam, ChatCompletionToolMessageParam
from pydantic import BaseModel, ValidationError
from rich.console import Console as RichConsoleClass

from qx.cli.theme import themed_console
from qx.core.workflow_context import get_workflow_context
from qx.core.workflow_tool_integration import (
    get_workflow_tool_integrator,
    ToolExecutionMode,
    execute_workflow_aware_tool
)
from qx.core.workflow_monitor import track_tool_execution
from qx.core.workflow_debug_logger import get_debug_logger

logger = logging.getLogger(__name__)


class WorkflowEnhancedToolProcessor:
    """
    Enhanced tool processor with workflow integration capabilities.
    
    This processor extends the standard tool processor with:
    - Workflow context awareness
    - Enhanced tool coordination
    - Performance monitoring
    - Error recovery mechanisms
    - Result caching
    """
    
    def __init__(
        self,
        tool_functions: Dict[str, Callable],
        tool_input_models: Dict[str, Type[BaseModel]],
        console,
        run_func: Callable,
    ):
        self._tool_functions = tool_functions
        self._tool_input_models = tool_input_models
        self.console = console
        self._run = run_func
        
        # Initialize workflow tool integrator and debug logger
        self.tool_integrator = get_workflow_tool_integrator()
        self.debug_logger = get_debug_logger()
        
        # Register all tools with the integrator
        self._register_tools_with_integrator()
        
        # Performance tracking
        self.execution_metrics = {
            "total_tool_calls": 0,
            "workflow_aware_calls": 0,
            "parallel_executions": 0,
            "error_recoveries": 0
        }
        
        logger.info("🔧 WorkflowEnhancedToolProcessor initialized")
    
    def _register_tools_with_integrator(self):
        """Register all tools with the workflow tool integrator."""
        for tool_name, tool_func in self._tool_functions.items():
            # Determine if tool supports workflow context based on signature
            import inspect
            sig = inspect.signature(tool_func)
            supports_context = 'workflow_context' in sig.parameters
            
            self.tool_integrator.register_tool(
                tool_name=tool_name,
                tool_function=tool_func,
                metadata={
                    'supports_workflow_context': supports_context,
                    'input_model': self._tool_input_models.get(tool_name).__name__ if tool_name in self._tool_input_models else None
                }
            )
            
            logger.debug(f"🔧 Registered tool {tool_name} with integrator (context_aware: {supports_context})")
    
    async def process_tool_calls_and_continue(
        self,
        response_message,
        messages: List[ChatCompletionMessageParam],
        user_input: str,
        recursion_depth: int = 0,
    ) -> Any:
        """Process tool calls with enhanced workflow integration."""
        from qx.core.llm import QXRunResult  # Import here to avoid circular imports
        
        if not response_message.tool_calls:
            # Ensure we have content to return
            content = response_message.content if response_message.content else ""
            return QXRunResult(content, messages)
        
        # Get workflow context for enhanced processing
        workflow_context = await get_workflow_context()
        execution_id = getattr(workflow_context, 'workflow_id', 'unknown') if workflow_context else 'unknown'
        
        if workflow_context:
            self.execution_metrics["workflow_aware_calls"] += 1
            logger.info(f"Processing {len(response_message.tool_calls)} tool calls in workflow context for agent {workflow_context.agent_name}")
        else:
            logger.info(f"Processing {len(response_message.tool_calls)} tool calls in standalone mode")
        
        self.execution_metrics["total_tool_calls"] += len(response_message.tool_calls)
        
        # Prepare enhanced tool tasks
        tool_tasks = []
        task_metadata = []
        
        for tool_call in response_message.tool_calls:
            function_name = tool_call.function.name
            function_args = tool_call.function.arguments
            tool_call_id = tool_call.id
            
            # Validate tool exists
            if function_name not in self._tool_functions:
                error_msg = f"LLM attempted to call unknown tool: {function_name}"
                logger.error(error_msg)
                
                themed_console.print(f"[error]{error_msg}[/]")
                messages.append(
                    cast(
                        ChatCompletionToolMessageParam,
                        {
                            "role": "tool",
                            "tool_call_id": tool_call_id,
                            "content": f"Error: Unknown tool '{function_name}'",
                        },
                    )
                )
                continue
            
            # Parse and validate arguments
            try:
                parsed_args = {}
                if function_args:
                    try:
                        parsed_args = json.loads(function_args)
                    except json.JSONDecodeError:
                        error_msg = f"LLM provided invalid JSON arguments for tool '{function_name}': {function_args}"
                        logger.error(error_msg)
                        
                        themed_console.print(f"[error]{error_msg}[/]")
                        messages.append(
                            cast(
                                ChatCompletionToolMessageParam,
                                {
                                    "role": "tool",
                                    "tool_call_id": tool_call_id,
                                    "content": f"Error: Invalid JSON arguments for tool '{function_name}'. Please ensure arguments are valid JSON.",
                                },
                            )
                        )
                        continue
                
                # Validate with Pydantic model
                tool_input_model = self._tool_input_models[function_name]
                try:
                    tool_args_instance = tool_input_model(**parsed_args)
                except ValidationError as ve:
                    error_msg = f"LLM provided invalid parameters for tool '{function_name}'. Validation errors: {ve}"
                    logger.error(error_msg, exc_info=True)
                    
                    # Create actionable error message
                    error_details = []
                    for error in ve.errors():
                        field_path = " -> ".join(str(loc) for loc in error["loc"])
                        error_type = error["type"]
                        msg = error["msg"]
                        error_details.append(f"Field '{field_path}': {msg} ({error_type})")
                    
                    actionable_error = (
                        f"Tool '{function_name}' validation failed:\n"
                        + "\n".join(error_details)
                    )
                    
                    if hasattr(tool_input_model, "model_fields"):
                        required_fields = [
                            name
                            for name, field in tool_input_model.model_fields.items()
                            if field.is_required()
                        ]
                        if required_fields:
                            actionable_error += f"\n\nRequired fields: {', '.join(required_fields)}"
                    
                    themed_console.print(f"[error]{error_msg}[/]")
                    messages.append(
                        cast(
                            ChatCompletionToolMessageParam,
                            {
                                "role": "tool",
                                "tool_call_id": tool_call_id,
                                "content": actionable_error,
                            },
                        )
                    )
                    continue
                
                # Create enhanced tool execution task
                task_metadata.append({
                    "tool_call_id": tool_call_id,
                    "function_name": function_name,
                    "args": tool_args_instance,
                    "workflow_context": workflow_context
                })
                
                # Log tool call with debug logger
                tool_args_dict = tool_args_instance.model_dump() if hasattr(tool_args_instance, 'model_dump') else {}
                
                # Create coroutine with workflow awareness and debug logging
                if workflow_context:
                    # Use workflow-aware execution with debug logging
                    coroutine = self._execute_tool_with_debug_logging(
                        execution_id,
                        function_name,
                        tool_args_dict,
                        tool_args_instance,
                        user_input,
                        use_workflow_context=True
                    )
                else:
                    # Use standard execution with debug logging
                    coroutine = self._execute_tool_with_debug_logging(
                        execution_id,
                        function_name,
                        tool_args_dict,
                        tool_args_instance,
                        user_input,
                        use_workflow_context=False
                    )
                
                tool_tasks.append({
                    "tool_call_id": tool_call_id,
                    "function_name": function_name,
                    "coroutine": coroutine,
                    "metadata": task_metadata[-1]
                })
                
            except Exception as e:
                error_msg = f"Error preparing tool call '{function_name}': {e}"
                logger.error(error_msg, exc_info=True)
                
                themed_console.print(f"[error]{error_msg}[/]")
                messages.append(
                    cast(
                        ChatCompletionToolMessageParam,
                        {
                            "role": "tool",
                            "tool_call_id": tool_call_id,
                            "content": f"Error: Failed to prepare tool call: {e}",
                        },
                    )
                )
        
        # Execute enhanced tool tasks
        if tool_tasks:
            self.execution_metrics["parallel_executions"] += 1
            results = await self._execute_enhanced_tool_tasks(tool_tasks)
            
            # Process results and update messages
            for i, result in enumerate(results):
                task_info = tool_tasks[i]
                tool_call_id = task_info["tool_call_id"]
                function_name = task_info["function_name"]
                
                if isinstance(result, Exception):
                    error_msg = f"Error executing tool '{function_name}': {result}"
                    logger.error(error_msg, exc_info=True)
                    
                    themed_console.print(f"[error]{error_msg}[/]")
                    tool_output_content = f"Error: Tool execution failed: {result}. This might be due to an internal tool error or an unexpected argument type."
                else:
                    if hasattr(result, "model_dump_json"):
                        tool_output_content = result.model_dump_json()
                    else:
                        tool_output_content = str(result)
                
                tool_message = {
                    "role": "tool",
                    "tool_call_id": tool_call_id,
                    "content": tool_output_content,
                }
                
                # Log tool response if enabled
                import os
                if os.getenv("QX_LOG_SENT"):
                    logger.info(f"Sending tool response to LLM:\n{json.dumps(tool_message, indent=2)}")
                
                messages.append(cast(ChatCompletionToolMessageParam, tool_message))
        
        # Continue with LLM after tool execution
        try:
            tool_count = sum(1 for m in messages if (m.get("role") if isinstance(m, dict) else getattr(m, "role", None)) == "tool")
            logger.debug(f"Sending {tool_count} tool responses to LLM")
            
            # Check recursion limit
            if recursion_depth >= 8:
                logger.warning(f"Approaching recursion limit (depth {recursion_depth}), forcing final response")
                final_system_msg = cast(
                    ChatCompletionMessageParam,
                    {
                        "role": "user",
                        "content": "Please provide a final response based on the tool results above. Do not make any more tool calls.",
                    },
                )
                messages.append(final_system_msg)
            
            return await self._run(user_input, messages, recursion_depth + 1)
            
        except Exception as e:
            logger.error(f"Error in enhanced tool processor continuation: {e}", exc_info=True)
            return QXRunResult(f"Error processing tool results: {e}", messages)
    
    async def _execute_tool_with_debug_logging(
        self,
        execution_id: str,
        function_name: str,
        tool_args_dict: Dict[str, Any],
        tool_args_instance: BaseModel,
        user_input: str,
        use_workflow_context: bool = True
    ):
        """Execute a tool with comprehensive debug logging and monitoring."""
        # Use debug logger for tool execution tracking
        with self.debug_logger.log_tool_execution(execution_id, function_name, tool_args_dict):
            # Track tool execution with monitoring
            tool_execution_manager = await track_tool_execution(execution_id, function_name, {"args": str(tool_args_instance)})
            async with tool_execution_manager as tool_execution:
                try:
                    if use_workflow_context:
                        # Prepare tool arguments
                        tool_args = {
                            'console': RichConsoleClass(),
                            'args': tool_args_instance
                        }
                        
                        # Execute with workflow integration
                        result = await execute_workflow_aware_tool(
                            tool_name=function_name,
                            tool_args=tool_args,
                            execution_mode=ToolExecutionMode.WORKFLOW_AWARE,
                            task_description=user_input
                        )
                        
                        if result.success:
                            self.debug_logger.log_tool_result(execution_id, function_name, result.result)
                            return result.result
                        else:
                            raise Exception(result.error or "Tool execution failed")
                    else:
                        # Standard tool execution
                        tool_func = self._tool_functions[function_name]
                        result = await tool_func(
                            console=RichConsoleClass(), 
                            args=tool_args_instance
                        )
                        
                        self.debug_logger.log_tool_result(execution_id, function_name, result)
                        return result
                        
                except Exception as e:
                    logger.error(f"Error in tool execution: {e}", exc_info=True)
                    raise
    
    async def _execute_enhanced_tool_tasks(self, tool_tasks: List[Dict]) -> List[Any]:
        """Execute tool tasks with enhanced error handling and coordination."""
        
        async def run_tool_with_timeout_and_recovery(task_info):
            try:
                return await asyncio.wait_for(
                    task_info["coroutine"],
                    timeout=120.0  # 2 minute timeout per tool
                )
            except asyncio.TimeoutError:
                error_msg = f"Tool '{task_info['function_name']}' timed out after 2 minutes"
                logger.error(error_msg)
                return Exception(error_msg)
            except Exception as e:
                # Attempt error recovery if in workflow context
                if task_info.get("metadata", {}).get("workflow_context"):
                    logger.warning(f"⚠️ Tool {task_info['function_name']} failed, attempting recovery")
                    self.execution_metrics["error_recoveries"] += 1
                    
                    # Could implement recovery strategies here
                    # For now, just log and return the error
                
                return e
        
        # Execute all tasks in parallel
        results = await asyncio.gather(
            *[run_tool_with_timeout_and_recovery(task) for task in tool_tasks],
            return_exceptions=True
        )
        
        # Log execution summary
        successful_tools = [
            task["function_name"] for i, task in enumerate(tool_tasks) 
            if not isinstance(results[i], Exception)
        ]
        failed_tools = [
            task["function_name"] for i, task in enumerate(tool_tasks) 
            if isinstance(results[i], Exception)
        ]
        
        if successful_tools:
            logger.info(f"✅ Successfully executed tools: {', '.join(successful_tools)}")
        if failed_tools:
            logger.warning(f"❌ Failed tools: {', '.join(failed_tools)}")
        
        return results
    
    def get_processor_metrics(self) -> Dict[str, Any]:
        """Get enhanced tool processor metrics."""
        return {
            "execution_metrics": self.execution_metrics.copy(),
            "tool_integrator_metrics": self.tool_integrator.get_tool_metrics(),
            "registered_tools": list(self._tool_functions.keys())
        }