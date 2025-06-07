import asyncio
import logging
import os
from typing import Any, Callable, Dict, List, Optional

from litellm import acompletion
from openai.types.chat import ChatCompletionMessageParam

logger = logging.getLogger(__name__)


class FallbackHandler:
    """Handles timeout fallbacks and retries."""

    def __init__(
        self,
        model_name: str,
        temperature: float,
        max_output_tokens: Optional[int],
        openai_tools_schema: List,
        serialize_messages_func: Callable,
        process_tool_calls_func: Callable,
        console,
    ):
        self.model_name = model_name
        self.temperature = temperature
        self.max_output_tokens = max_output_tokens
        self._openai_tools_schema = openai_tools_schema
        self._serialize_messages_efficiently = serialize_messages_func
        self._process_tool_calls_and_continue = process_tool_calls_func
        self.console = console

    async def handle_timeout_fallback(
        self,
        messages: List[ChatCompletionMessageParam],
        user_input: str,
        recursion_depth: int,
    ) -> Any:
        """Handle timeout by trying 'try again' message as fallback."""
        from qx.core.llm import QXRunResult  # Import here to avoid circular imports

        logger.warning("Attempting timeout fallback with 'try again' message")
        self.console.print(
            "[warning]Request timed out after retries. Asking model to try again...[/]"
        )

        try:
            # Add "try again" as user message and retry once more
            fallback_messages = messages.copy()
            fallback_messages.append({"role": "user", "content": "try again"})

            fallback_params = {
                "model": self.model_name,
                "messages": self._serialize_messages_efficiently(fallback_messages),
                "temperature": self.temperature,
                "tools": self._openai_tools_schema,
                "tool_choice": "auto",
                "stream": False,  # Use non-streaming for fallback
            }

            if self.max_output_tokens is not None:
                fallback_params["max_tokens"] = self.max_output_tokens

            # Use timeout for fallback but allow sufficient time for model response
            response = await asyncio.wait_for(
                acompletion(**fallback_params),
                timeout=240.0,  # 4 minute timeout for fallback (slightly less than main timeout)
            )
            response_message = response.choices[0].message
            fallback_messages.append(response_message)

            if response_message.tool_calls:
                return await self._process_tool_calls_and_continue(
                    response_message, fallback_messages, "try again", recursion_depth
                )
            else:
                return QXRunResult(
                    response_message.content or "Request timed out", fallback_messages
                )

        except Exception as e:
            logger.error(f"Timeout fallback also failed: {e}", exc_info=True)
            self.console.print(
                "[error]Error:[/] Request timed out and fallback failed. Please try again."
            )
            return QXRunResult("Request timed out and retry failed", messages)


class LiteLLMCaller:
    """Handles making LiteLLM API calls with logging."""

    def __init__(self, reliability_config):
        self._reliability_config = reliability_config

    async def make_litellm_call(self, chat_params: Dict[str, Any]) -> Any:
        """Make LiteLLM API call with enhanced error handling and logging."""
        try:
            # Remove None values to clean up parameters
            clean_params = {k: v for k, v in chat_params.items() if v is not None}

            # Log reliability configuration if debug enabled
            if os.environ.get("QX_LOG_LEVEL", "").upper() == "DEBUG":
                logger.debug(
                    f"Making LiteLLM call with model: {clean_params.get('model')}"
                )
                if "fallbacks" in clean_params:
                    logger.debug(
                        f"Fallback models configured: {clean_params['fallbacks']}"
                    )
                if "context_window_fallback_dict" in clean_params:
                    logger.debug(
                        f"Context window fallbacks: {clean_params['context_window_fallback_dict']}"
                    )
                logger.debug(f"Retries: {clean_params.get('num_retries', 0)}")
                logger.debug(f"Timeout: {clean_params.get('timeout', 'default')}")

            return await acompletion(**clean_params)

        except Exception as e:
            error_type = type(e).__name__
            logger.error(f"LiteLLM API call failed ({error_type}): {e}")

            # Log which model/fallbacks were attempted if available
            if self._reliability_config.fallback_models:
                logger.debug(
                    f"Fallback models were available: {self._reliability_config.fallback_models}"
                )

            raise
