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
from pydantic import BaseModel
from rich.console import Console as RichConsole

from qx.core.plugin_manager import PluginManager

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
        thinking_budget: Optional[int] = None,
    ):
        self.model_name = model_name
        self.system_prompt = system_prompt
        self.console = console
        self.temperature = temperature
        self.max_output_tokens = max_output_tokens
        self.thinking_budget = thinking_budget

        self._tool_functions: Dict[str, Callable] = {}
        self._openai_tools_schema: List[ChatCompletionToolParam] = []
        self._tool_input_models: Dict[str, Type[BaseModel]] = {}

        for func, schema, input_model_class in tools:
            self._tool_functions[func.__name__] = func
            self._openai_tools_schema.append(
                ChatCompletionToolParam(
                    type="function", function=FunctionDefinition(**schema)
                )
            )
            self._tool_input_models[func.__name__] = input_model_class

        self.client = self._initialize_openai_client()
        logger.info(f"QXLLMAgent initialized with model: {self.model_name}")
        logger.info(f"Registered {len(self._tool_functions)} tool functions.")

    def _initialize_openai_client(self) -> AsyncOpenAI:
        """Initializes the OpenAI client for OpenRouter."""
        openrouter_api_key = os.environ.get("OPENROUTER_API_KEY")
        if not openrouter_api_key:
            self.console.print(
                "[error]Error:[/] OPENROUTER_API_KEY environment variable not set."
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
        if self.thinking_budget is not None:
            extra_body_params["reasoning"] = {"max_tokens": self.thinking_budget}

        if extra_body_params:
            chat_params["extra_body"] = extra_body_params

        try:
            logger.debug(f"LLM Request Parameters: {json.dumps(chat_params, indent=2)}")
            response = await self.client.chat.completions.create(**chat_params)
            logger.debug(f"LLM Raw Response: {response.model_dump_json(indent=2)}")

            response_message = response.choices[0].message
            messages.append(response_message)

            if response_message.tool_calls:
                for tool_call in response_message.tool_calls:
                    function_name = tool_call.function.name
                    function_args = tool_call.function.arguments

                    if function_name not in self._tool_functions:
                        error_msg = (
                            f"LLM attempted to call unknown tool: {function_name}"
                        )
                        logger.error(error_msg)
                        self.console.print(f"[error]{error_msg}[/error]")
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
                        return await self.run(user_input, messages)

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
                                self.console.print(f"[error]{error_msg}[/error]")
                                messages.append(
                                    cast(
                                        ChatCompletionToolMessageParam,
                                        {
                                            "role": "tool",
                                            "tool_call_id": tool_call.id,
                                            "content": f"Error: Invalid arguments for tool '{function_name}'",
                                        },
                                    )
                                )
                                return await self.run(user_input, messages)

                        tool_args_instance = tool_input_model(**parsed_args)

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

                        return await self.run(user_input, messages)

                    except Exception as e:
                        error_msg = f"Error executing tool '{function_name}': {e}"
                        logger.error(error_msg, exc_info=True)
                        self.console.print(f"[error]{error_msg}[/error]")
                        messages.append(
                            cast(
                                ChatCompletionToolMessageParam,
                                {
                                    "role": "tool",
                                    "tool_call_id": tool_call.id,
                                    "content": f"Error: Tool execution failed: {e}",
                                },
                            )
                        )
                        return await self.run(user_input, messages)
            else:

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

                return QXRunResult(response_message.content, messages)

        except Exception as e:
            logger.error(f"Error during LLM chat completion: {e}", exc_info=True)
            self.console.print(f"[error]Error during LLM chat completion: {e}[/error]")
            return None


def initialize_llm_agent(
    model_name_str: str,
    console: RichConsole,
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
        console.print(f"[error]Error:[/] Failed to load tools: {e}")
        registered_tools = []

    try:
        temperature = float(os.environ.get("QX_MODEL_TEMPERATURE", "0.7"))
        max_output_tokens = int(os.environ.get("QX_MODEL_MAX_TOKENS", "4096"))
        thinking_budget = int(os.environ.get("QX_MODEL_REASONING_MAX_TOKENS", "2000"))

        agent = QXLLMAgent(
            model_name=model_name_str,
            system_prompt=system_prompt_content,
            tools=registered_tools,
            console=console,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            thinking_budget=thinking_budget,
        )
        return agent

    except Exception as e:
        logger.error(f"Failed to initialize QXLLMAgent: {e}", exc_info=True)
        console.print(f"[error]Error:[/] Init LLM Agent: {e}")
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
        console.print(f"[error]Error:[/] LLM query: {e}")
        return None
