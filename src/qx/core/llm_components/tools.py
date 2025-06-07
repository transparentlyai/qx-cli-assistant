import asyncio
import json
import logging
import os
from typing import Any, Callable, Dict, List, Type, cast

import httpx
from openai.types.chat import ChatCompletionMessageParam, ChatCompletionToolMessageParam
from pydantic import BaseModel, ValidationError
from rich.console import Console as RichConsoleClass

from qx.cli.theme import themed_console

logger = logging.getLogger(__name__)


class ToolProcessor:
    """Handles tool calls and execution."""

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

    async def process_tool_calls_and_continue(
        self,
        response_message,
        messages: List[ChatCompletionMessageParam],
        user_input: str,
        recursion_depth: int = 0,
    ) -> Any:
        """Process tool calls and continue the conversation."""
        from qx.core.llm import QXRunResult  # Import here to avoid circular imports

        if not response_message.tool_calls:
            # Ensure we have content to return
            content = response_message.content if response_message.content else ""
            return QXRunResult(content, messages)

        tool_tasks = []
        for tool_call in response_message.tool_calls:
            function_name = tool_call.function.name
            function_args = tool_call.function.arguments
            tool_call_id = tool_call.id

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

            tool_func = self._tool_functions[function_name]
            tool_input_model = self._tool_input_models[function_name]

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

                try:
                    tool_args_instance = tool_input_model(**parsed_args)
                except ValidationError as ve:
                    error_msg = f"LLM provided invalid parameters for tool '{function_name}'. Validation errors: {ve}"
                    logger.error(error_msg, exc_info=True)

                    themed_console.print(f"[error]{error_msg}[/]")

                    # Create a more actionable error message for the LLM
                    error_details = []
                    for error in ve.errors():
                        field_path = " -> ".join(str(loc) for loc in error["loc"])
                        error_type = error["type"]
                        msg = error["msg"]
                        error_details.append(
                            f"Field '{field_path}': {msg} ({error_type})"
                        )

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
                            actionable_error += (
                                f"\n\nRequired fields: {', '.join(required_fields)}"
                            )

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

                # If validation passes, add the task to the list
                tool_tasks.append(
                    {
                        "tool_call_id": tool_call_id,
                        "function_name": function_name,
                        "coroutine": tool_func(
                            console=RichConsoleClass(), args=tool_args_instance
                        ),
                    }
                )

            except Exception as e:
                # This catch is for errors during parsing/validation, not tool execution
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

        # Execute all collected tool tasks in parallel with timeout
        if tool_tasks:
            # Create tasks with individual timeouts
            async def run_tool_with_timeout(task_info):
                try:
                    return await asyncio.wait_for(
                        task_info["coroutine"],
                        timeout=120.0,  # 2 minute timeout per tool to allow for complex operations
                    )
                except asyncio.TimeoutError:
                    error_msg = (
                        f"Tool '{task_info['function_name']}' timed out after 2 minutes"
                    )
                    logger.error(error_msg)
                    return Exception(error_msg)

            results = await asyncio.gather(
                *[run_tool_with_timeout(task) for task in tool_tasks],
                return_exceptions=True,
            )

            for i, result in enumerate(results):
                tool_call_info = tool_tasks[i]
                tool_call_id = tool_call_info["tool_call_id"]
                function_name = tool_call_info["function_name"]

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

                # Log tool response if QX_LOG_SENT is set (since we're sending it to the model)
                if os.getenv("QX_LOG_SENT"):
                    logger.info(
                        f"Sending tool response to LLM:\n{json.dumps(tool_message, indent=2)}"
                    )

                messages.append(
                    cast(
                        ChatCompletionToolMessageParam,
                        tool_message,
                    )
                )

        # After processing all tool calls (or attempting to), make one recursive call
        # The model needs to generate a response based on the tool outputs
        # We pass a special marker that won't be added to messages but triggers response generation
        try:
            tool_count = 0
            for m in messages:
                role = (
                    m.get("role") if isinstance(m, dict) else getattr(m, "role", None)
                )
                if role == "tool":
                    tool_count += 1
            logger.debug(f"Sending {tool_count} tool responses to LLM")

            # Check if we're approaching recursion limit before continuing
            if recursion_depth >= 8:
                logger.warning(
                    f"Approaching recursion limit (depth {recursion_depth}), forcing final response"
                )
                # Add a system message to encourage the LLM to provide a final response
                final_system_msg = cast(
                    ChatCompletionMessageParam,
                    {
                        "role": "user",
                        "content": "Please provide a final response based on the tool results above. Do not make any more tool calls.",
                    },
                )
                messages.append(final_system_msg)

            result = await self._run(
                "__CONTINUE_AFTER_TOOLS__", messages, recursion_depth + 1
            )
            logger.debug("Tool response continuation completed successfully")
            return result
        except (asyncio.TimeoutError, httpx.TimeoutException) as e:
            # Handle timeout specifically to avoid excessive retries
            logger.warning(f"Timeout during tool continuation: {e}")
            self.console.print(
                "[warning]Warning:[/] Tool execution completed but response generation timed out"
            )
            # Return partial result with tool responses included
            return QXRunResult(
                "Tool execution completed but response generation timed out", messages
            )
        except Exception as e:
            logger.error(f"Error continuing after tool execution: {e}", exc_info=True)
            self.console.print(
                f"[error]Error:[/] Failed to continue after tool execution: {e}"
            )
            # Return partial result with tool responses included
            return QXRunResult(
                "Tool execution completed but continuation failed", messages
            )
