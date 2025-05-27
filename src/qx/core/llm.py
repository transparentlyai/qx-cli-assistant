import asyncio  # noqa: F401
import json
import logging
import os
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Type, cast

import httpx
from openai import AsyncOpenAI
from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionToolMessageParam,
    ChatCompletionToolParam,
    ChatCompletionUserMessageParam,
)
from openai.types.shared_params.function_definition import FunctionDefinition
from pydantic import BaseModel, ValidationError
from rich.console import Console as RichConsole

from qx.core.plugin_manager import PluginManager
from qx.core.mcp_manager import MCPManager # New import

logger = logging.getLogger(__name__)


def load_and_format_system_prompt() -> str:
    """
    Loads the system prompt from the markdown file and formats it with
    environment variables.
    """
    try:
        current_dir = Path(__file__).parent
        prompt_path = current_dir.parent / "prompts" / "system-prompt.md"

        if not prompt_path.exists():
            logger.error(f"System prompt file not found at {prompt_path}")
            return "You are a helpful AI assistant."

        template = prompt_path.read_text(encoding="utf-8")
        user_context = os.environ.get("QX_USER_CONTEXT", "")
        project_context = os.environ.get("QX_PROJECT_CONTEXT", "")
        project_files = os.environ.get("QX_PROJECT_FILES", "")

        formatted_prompt = template.replace("{user_context}", user_context)
        formatted_prompt = formatted_prompt.replace(
            "{project_context}", project_context
        )
        formatted_prompt = formatted_prompt.replace("{project_files}", project_files)
        return formatted_prompt
    except Exception as e:
        logger.error(f"Failed to load or format system prompt: {e}", exc_info=True)
        return "You are a helpful AI assistant."


class QXLLMAgent:
    """
    Encapsulates the LLM client and manages interactions, including tool calling.
    """

    def __init__(
        self,
        model_name: str,
        system_prompt: str,
        tools: List[Tuple[Callable, Dict[str, Any], Type[BaseModel]]],
        console: RichConsole,
        temperature: float = 0.7,
        max_output_tokens: Optional[int] = None,
        reasoning_effort: Optional[str] = None,
        enable_streaming: bool = True,
    ):
        self.model_name = model_name
        self.system_prompt = system_prompt
        self.console = console
        self.temperature = temperature
        self.max_output_tokens = max_output_tokens
        self.reasoning_effort = reasoning_effort
        self.enable_streaming = enable_streaming

        self._tool_functions: Dict[str, Callable] = {}
        self._openai_tools_schema: List[ChatCompletionToolParam] = []
        self._tool_input_models: Dict[str, Type[BaseModel]] = {}

        for func, schema, input_model_class in tools:
            self._tool_functions[func.__name__] = func
            
            # Handle different schema formats (regular plugins vs MCP tools)
            if "function" in schema:
                # MCP tools format: {"type": "function", "function": {...}}
                function_def = schema["function"]
            else:
                # Regular plugins format: {"name": ..., "description": ..., "parameters": ...}
                function_def = schema
                
            self._openai_tools_schema.append(
                ChatCompletionToolParam(
                    type="function", function=FunctionDefinition(**function_def)
                )
            )
            self._tool_input_models[func.__name__] = input_model_class
            logger.debug(f"QXLLMAgent: Registered tool function '{func.__name__}' with schema name '{function_def.get('name')}'")

        self.client = self._initialize_openai_client()
        logger.info(f"QXLLMAgent initialized with model: {self.model_name}")
        logger.info(f"Registered {len(self._tool_functions)} tool functions.")
        
        # Debug: Log all registered tools for troubleshooting
        logger.info("Registered tool functions:")
        for tool_name in self._tool_functions.keys():
            logger.info(f"  - {tool_name}")
        logger.info("OpenAI tool schemas:")
        for schema in self._openai_tools_schema:
            logger.info(f"  - {schema['function']['name'] if 'function' in schema and 'name' in schema['function'] else 'unnamed'}")

    def _initialize_openai_client(self) -> AsyncOpenAI:
        """Initializes the OpenAI client for OpenRouter."""
        openrouter_api_key = os.environ.get("OPENROUTER_API_KEY")
        if not openrouter_api_key:
            self.console.print(
                "[red]Error:[/red] OPENROUTER_API_KEY environment variable not set."
            )
            raise ValueError("OPENROUTER_API_KEY not set.")

        return AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=openrouter_api_key,
            http_client=httpx.AsyncClient(),
        )

    async def run(
        self,
        user_input: str,
        message_history: Optional[List[ChatCompletionMessageParam]] = None,
    ) -> Any:
        """
        Runs the LLM agent, handling conversation turns and tool calls.
        Returns the final message content or tool output.
        """
        messages: List[ChatCompletionMessageParam] = []
        messages.append(
            cast(
                ChatCompletionSystemMessageParam,
                {"role": "system", "content": self.system_prompt},
            )
        )

        if message_history:
            messages.extend(message_history)

        messages.append(
            cast(
                ChatCompletionUserMessageParam, {"role": "user", "content": user_input}
            )
        )

        # Parameters for the chat completion
        chat_params: Dict[str, Any] = {
            "model": self.model_name,
            "messages": [
                msg.model_dump() if isinstance(msg, BaseModel) else msg
                for msg in messages
            ],
            "temperature": self.temperature,
            "tools": self._openai_tools_schema,
            "tool_choice": "auto",
        }

        if self.max_output_tokens is not None:
            chat_params["max_tokens"] = self.max_output_tokens

        # OpenRouter-specific parameters like 'reasoning' go into extra_body
        extra_body_params = {}
        if self.reasoning_effort is not None:
            # Pass reasoning_effort as 'effort' string
            extra_body_params["reasoning"] = {"effort": self.reasoning_effort}

        if extra_body_params:
            chat_params["extra_body"] = extra_body_params

        try:
            logger.debug(f"LLM Request Parameters: {json.dumps(chat_params, indent=2)}")
            
            if self.enable_streaming:
                # Add streaming parameter
                chat_params["stream"] = True
                return await self._handle_streaming_response(chat_params, messages, user_input)
            else:
                response = await self.client.chat.completions.create(**chat_params)
                logger.debug(f"LLM Raw Response: {response.model_dump_json(indent=2)}")

                response_message = response.choices[0].message
                messages.append(response_message)

                if response_message.tool_calls:
                    return await self._process_tool_calls_and_continue(response_message, messages, user_input)
                else:
                    return QXRunResult(response_message.content, messages)

        except Exception as e:
            logger.error(f"Error during LLM chat completion: {e}", exc_info=True)
            self.console.print(f"[red]Error:[/red] LLM chat completion: {e}")
            return None


    async def _handle_streaming_response(
        self, 
        chat_params: Dict[str, Any], 
        messages: List[ChatCompletionMessageParam], 
        user_input: str
    ) -> Any:
        """Handle streaming response from OpenRouter API."""
        from rich.live import Live
        from rich.markdown import Markdown
        import asyncio
        import time
        
        accumulated_content = ""
        accumulated_tool_calls = []
        current_tool_call = None
        
        # Create a Live display for real-time updates
        # Use the underlying Rich console if QXConsole wrapper
        rich_console = getattr(self.console, '_console', self.console)
        with Live(console=rich_console, auto_refresh=True, refresh_per_second=8) as live:
            # Show initial blinking cursor to indicate thinking
            initial_cursor = "█" if int(time.time() * 4) % 2 == 0 else " "
            live.update(f"[dim]{initial_cursor}[/dim]")
            
            try:
                stream = await self.client.chat.completions.create(**chat_params)
                
                async for chunk in stream:
                    if not chunk.choices:
                        continue
                    
                    choice = chunk.choices[0]
                    delta = choice.delta
                    
                    # Handle content streaming
                    content_updated = False
                    if delta.content:
                        accumulated_content += delta.content
                        content_updated = True
                    
                    # Always update with blinking cursor (even if no new content)
                    # Add blinking cursor effect - alternate between block and space
                    cursor = "█" if int(time.time() * 4) % 2 == 0 else " "
                    if accumulated_content:
                        content_with_cursor = accumulated_content + "\n" + cursor
                        markdown = Markdown(content_with_cursor)
                        live.update(markdown)
                    elif not content_updated:
                        # Show just blinking cursor when waiting for first content
                        live.update(f"[dim]{cursor}[/dim]")
                    
                    # Handle tool call streaming
                    if delta.tool_calls:
                        for tool_call_delta in delta.tool_calls:
                            # Start new tool call
                            if tool_call_delta.index is not None:
                                # Ensure we have enough space in the list
                                while len(accumulated_tool_calls) <= tool_call_delta.index:
                                    accumulated_tool_calls.append({
                                        "id": None,
                                        "type": "function",
                                        "function": {"name": "", "arguments": ""}
                                    })
                                
                                current_tool_call = accumulated_tool_calls[tool_call_delta.index]
                                
                                if tool_call_delta.id:
                                    current_tool_call["id"] = tool_call_delta.id
                                
                                if tool_call_delta.function:
                                    if tool_call_delta.function.name:
                                        current_tool_call["function"]["name"] = tool_call_delta.function.name
                                    if tool_call_delta.function.arguments:
                                        current_tool_call["function"]["arguments"] += tool_call_delta.function.arguments
                    
                    # Check if stream is finished
                    if choice.finish_reason:
                        # Show final content without cursor
                        if accumulated_content:
                            final_markdown = Markdown(accumulated_content)
                            live.update(final_markdown)
                        break
                
                # Clear the live display
                live.update("")
                
            except Exception as e:
                logger.error(f"Error during streaming: {e}", exc_info=True)
                # Fall back to non-streaming
                chat_params["stream"] = False
                response = await self.client.chat.completions.create(**chat_params)
                response_message = response.choices[0].message
                messages.append(response_message)
                
                if response_message.tool_calls:
                    return await self._process_tool_calls_and_continue(response_message, messages, user_input)
                else:
                    return QXRunResult(response_message.content, messages)
        
        # Create response message from accumulated data
        response_message_dict = {
            "role": "assistant",
            "content": accumulated_content if accumulated_content else None
        }
        
        if accumulated_tool_calls:
            # Convert accumulated tool calls to proper format
            tool_calls = []
            for tc in accumulated_tool_calls:
                if tc["id"] and tc["function"]["name"]:
                    tool_calls.append({
                        "id": tc["id"],
                        "type": "function",
                        "function": {
                            "name": tc["function"]["name"],
                            "arguments": tc["function"]["arguments"]
                        }
                    })
            response_message_dict["tool_calls"] = tool_calls
        
        # Convert to proper message format
        from openai.types.chat.chat_completion_message import ChatCompletionMessage
        response_message = ChatCompletionMessage(**response_message_dict)
        messages.append(response_message)
        
        # Display final content if any
        if accumulated_content and accumulated_content.strip():
            markdown = Markdown(accumulated_content)
            self.console.print(markdown)
            self.console.print("\n")
        
        # Process tool calls if any
        if accumulated_tool_calls:
            return await self._process_tool_calls_and_continue(response_message, messages, user_input)
        else:
            return QXRunResult(accumulated_content, messages)
    
    async def _process_tool_calls_and_continue(
        self, 
        response_message, 
        messages: List[ChatCompletionMessageParam], 
        user_input: str
    ) -> Any:
        """Process tool calls and continue the conversation."""
        if not response_message.tool_calls:
            return QXRunResult(response_message.content, messages)
        
        # Process all tool calls before making the next LLM request
        for tool_call in response_message.tool_calls:
            function_name = tool_call.function.name
            function_args = tool_call.function.arguments

            if function_name not in self._tool_functions:
                error_msg = (
                    f"LLM attempted to call unknown tool: {function_name}"
                )
                logger.error(error_msg)
                self.console.print(f"[red]{error_msg}[/red]")
                messages.append(
                    cast(
                        ChatCompletionToolMessageParam,
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
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
                        self.console.print(f"[red]{error_msg}[/red]")
                        messages.append(
                            cast(
                                ChatCompletionToolMessageParam,
                                {
                                    "role": "tool",
                                    "tool_call_id": tool_call.id,
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
                    self.console.print(f"[red]{error_msg}[/red]")
                    messages.append(
                        cast(
                            ChatCompletionToolMessageParam,
                            {
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "content": f"Error: Invalid parameters for tool '{function_name}'. Details: {ve}",
                            },
                        )
                    )
                    continue

                tool_output = await tool_func(
                    console=self.console, args=tool_args_instance
                )

                if hasattr(tool_output, "model_dump_json"):
                    tool_output_content = tool_output.model_dump_json()
                else:
                    tool_output_content = str(tool_output)

                messages.append(
                    cast(
                        ChatCompletionToolMessageParam,
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": tool_output_content,
                        },
                    )
                )

            except Exception as e:
                error_msg = f"Error executing tool '{function_name}': {e}"
                logger.error(error_msg, exc_info=True)
                self.console.print(f"[red]{error_msg}[/red]")
                messages.append(
                    cast(
                        ChatCompletionToolMessageParam,
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": f"Error: Tool execution failed: {e}. This might be due to an internal tool error or an unexpected argument type.",
                        },
                    )
                )

        # After processing all tool calls, make one recursive call
        return await self.run(user_input, messages)


class QXRunResult:
    def __init__(
        self,
        output_content: str,
        all_msgs: List[ChatCompletionMessageParam],
    ):
        self.output = output_content
        self._all_messages = all_msgs

    def all_messages(self) -> List[ChatCompletionMessageParam]:
        return self._all_messages


def initialize_llm_agent(
    model_name_str: str,
    console: RichConsole,
    mcp_manager: MCPManager, # New parameter
    enable_streaming: bool = True,
) -> Optional[QXLLMAgent]:
    """
    Initializes the QXLLMAgent with system prompt and discovered tools.
    """
    system_prompt_content = load_and_format_system_prompt()

    plugin_manager = PluginManager()
    try:
        import sys

        src_path = Path(__file__).parent.parent.parent
        if str(src_path) not in sys.path:
            sys.path.insert(0, str(src_path))

        registered_tools = plugin_manager.load_plugins(plugin_package_path="qx.plugins")
        if not registered_tools:
            logger.warning(
                "No tools were loaded by the PluginManager. Agent will have no tools."
            )
        else:
            logger.info(f"Loaded {len(registered_tools)} tools via PluginManager.")

    except Exception as e:
        logger.error(f"Failed to load plugins: {e}", exc_info=True)
        console.print(f"[red]Error:[/red] Failed to load tools: {e}")
        registered_tools = []

    # Add MCP tools to the list of registered tools
    mcp_tools = mcp_manager.get_active_tools()
    if mcp_tools:
        registered_tools.extend(mcp_tools)
        logger.info(f"Added {len(mcp_tools)} tools from active MCP servers.")

    try:
        temperature = float(os.environ.get("QX_MODEL_TEMPERATURE", "0.7"))
        max_output_tokens = int(os.environ.get("QX_MODEL_MAX_TOKENS", "4096"))

        # Retrieve reasoning_effort as a string directly
        reasoning_effort: Optional[str] = os.environ.get("QX_MODEL_REASONING_EFFORT")
        if reasoning_effort and reasoning_effort.lower() not in [
            "high",
            "medium",
            "low",
        ]:
            logger.warning(
                f"Invalid value for QX_MODEL_REASONING_EFFORT: '{reasoning_effort}'. Expected 'high', 'medium', or 'low'. Setting to None."
            )
            reasoning_effort = None

        agent = QXLLMAgent(
            model_name=model_name_str,
            system_prompt=system_prompt_content,
            tools=registered_tools, # Pass combined tools
            console=console,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            reasoning_effort=reasoning_effort,
            enable_streaming=enable_streaming,
        )
        return agent

    except Exception as e:
        logger.error(f"Failed to initialize QXLLMAgent: {e}", exc_info=True)
        console.print(f"[red]Error:[/red] Init LLM Agent: {e}")
        return None


async def query_llm(
    agent: QXLLMAgent,
    user_input: str,
    console: RichConsole,
    message_history: Optional[List[ChatCompletionMessageParam]] = None,
) -> Optional[Any]:
    """
    Queries the LLM agent.
    """
    try:
        result = await agent.run(
            user_input,
            message_history=message_history,
        )
        return result
    except Exception as e:
        logger.error(f"Error during LLM query: {e}", exc_info=True)
        console.print(f"[red]Error:[/red] LLM query: {e}")
        return None
