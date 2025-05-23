import asyncio
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Callable
import json # Import json for parsing tool arguments

from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam, ChatCompletionToolParam
from rich.console import Console as RichConsole
from rich.text import Text

from qx.core.plugin_manager import PluginManager
from qx.core.user_prompts import request_confirmation

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
        tools: List[Tuple[Callable, Dict[str, Any]]], # List of (function, openai_tool_schema)
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
        self.thinking_budget = thinking_budget # This maps to OpenRouter's reasoning.max_tokens
        
        self._tool_functions: Dict[str, Callable] = {}
        self._openai_tools_schema: List[ChatCompletionToolParam] = []
        
        for func, schema in tools:
            self._tool_functions[func.__name__] = func
            self._openai_tools_schema.append(ChatCompletionToolParam(type="function", function=schema))

        self.client = self._initialize_openai_client()
        logger.info(f"QXLLMAgent initialized with model: {self.model_name}")
        logger.info(f"Registered {len(self._tool_functions)} tool functions.")

    def _initialize_openai_client(self) -> OpenAI:
        """Initializes the OpenAI client for OpenRouter."""
        openrouter_api_key = os.environ.get("OPENROUTER_API_KEY")
        if not openrouter_api_key:
            self.console.print(
                "[error]Error:[/] OPENROUTER_API_KEY environment variable not set."
            )
            raise ValueError("OPENROUTER_API_KEY not set.")

        return OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=openrouter_api_key,
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
        messages.append({"role": "system", "content": self.system_prompt})

        if message_history:
            messages.extend(message_history)
        
        messages.append({"role": "user", "content": user_input})

        # Parameters for the chat completion
        chat_params: Dict[str, Any] = {
            "model": self.model_name,
            "messages": messages,
            "temperature": self.temperature,
            "tools": self._openai_tools_schema,
            "tool_choice": "auto", # Allow model to choose tools
        }

        if self.max_output_tokens:
            chat_params["max_tokens"] = self.max_output_tokens
        
        # OpenRouter-specific parameters like 'reasoning' go into extra_body
        extra_body_params = {}
        if self.thinking_budget:
            extra_body_params["reasoning"] = {"max_tokens": self.thinking_budget}

        if extra_body_params:
            chat_params["extra_body"] = extra_body_params


        try:
            response = await self.client.chat.completions.create(**chat_params)
            
            response_message = response.choices[0].message
            messages.append(response_message) # Add assistant's response to history

            if response_message.tool_calls:
                for tool_call in response_message.tool_calls:
                    function_name = tool_call.function.name
                    function_args = tool_call.function.arguments

                    if function_name not in self._tool_functions:
                        error_msg = f"LLM attempted to call unknown tool: {function_name}"
                        logger.error(error_msg)
                        self.console.print(f"[error]{error_msg}[/error]")
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": function_name,
                            "content": f"Error: Unknown tool '{function_name}'"
                        })
                        # Continue to next turn with error message
                        return await self.run(user_input, messages) # Pass updated messages
                    
                    tool_func = self._tool_functions[function_name]
                    
                    try:
                        # Parse arguments. LLM might provide invalid JSON.
                        parsed_args = {}
                        if function_args:
                            try:
                                parsed_args = json.loads(function_args)
                            except json.JSONDecodeError:
                                error_msg = f"LLM provided invalid JSON arguments for tool '{function_name}': {function_args}"
                                logger.error(error_msg)
                                self.console.print(f"[error]{error_msg}[/error]")
                                messages.append({
                                    "role": "tool",
                                    "tool_call_id": tool_call.id,
                                    "name": function_name,
                                    "content": f"Error: Invalid arguments for tool '{function_name}'"
                                })
                                return await self.run(user_input, messages) # Pass updated messages

                        # Execute the tool function
                        # Pass console directly to tool functions
                        tool_output = tool_func(console=self.console, **parsed_args)
                        
                        # Tool output is expected to be a Pydantic BaseModel.
                        # Convert it to a dictionary for the LLM.
                        if hasattr(tool_output, 'model_dump_json'):
                            tool_output_content = tool_output.model_dump_json()
                        else:
                            tool_output_content = str(tool_output) # Fallback for non-Pydantic outputs

                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": function_name,
                            "content": tool_output_content
                        })
                        
                        # Recursively call run with updated messages to allow LLM to process tool output
                        return await self.run(user_input, messages)

                    except Exception as e:
                        error_msg = f"Error executing tool '{function_name}': {e}"
                        logger.error(error_msg, exc_info=True)
                        self.console.print(f"[error]{error_msg}[/error]")
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": function_name,
                            "content": f"Error: Tool execution failed: {e}"
                        })
                        return await self.run(user_input, messages) # Pass updated messages
            else:
                # If no tool calls, it's a final message
                # Return a simple object that mimics pydantic_ai.RunResult for main.py
                class QXRunResult:
                    def __init__(self, output_content: str, all_msgs: List[ChatCompletionMessageParam]):
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

        # load_plugins now returns (function, openai_tool_schema) tuples
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
        # Default model settings (can be made configurable later)
        temperature = float(os.environ.get("QX_LLM_TEMPERATURE", "0.7"))
        max_output_tokens = int(os.environ.get("QX_LLM_MAX_OUTPUT_TOKENS", "4096"))
        thinking_budget = int(os.environ.get("QX_LLM_THINKING_BUDGET", "2000")) # OpenRouter specific

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
    console: RichConsole, # Kept for consistency, but agent has its own console
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
