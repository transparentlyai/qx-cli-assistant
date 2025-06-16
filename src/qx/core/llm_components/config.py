import json
import logging
import os
from typing import Dict, List

import litellm

logger = logging.getLogger(__name__)




def validate_api_keys() -> None:
    """Validate that required API keys are present."""
    # Check for any provider API key
    api_keys = [
        "OPENROUTER_API_KEY",
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "AZURE_API_KEY",
        "GOOGLE_API_KEY",
    ]

    has_valid_key = any(os.environ.get(key) for key in api_keys)

    if not has_valid_key:
        from rich.console import Console

        Console().print(
            "[error]Error:[/] No valid API key found. Please set one of: "
            + ", ".join(api_keys)
        )
        raise ValueError("No valid API key found.")


def configure_litellm() -> None:
    """Configure LiteLLM settings."""
    # Set up HTTP debugging if enabled (shows actual HTTP requests to providers)
    if os.environ.get("QX_DEBUG_HTTP", "").lower() in ("true", "1", "yes"):
        logger.warning("HTTP debugging enabled - this will log API keys and request payloads!")
        # Use LiteLLM's official debug mode
        litellm._turn_on_debug()
        litellm.json_logs = True
        # This will show the actual POST requests sent to OpenRouter
        logger.info("LiteLLM debug mode enabled - you'll see raw HTTP requests to providers")
    
    # Set up debugging if enabled, but only if not using file logging
    log_file_path = os.getenv("QX_LOG_FILE")
    if os.environ.get("QX_LOG_LEVEL", "ERROR").upper() == "DEBUG" and not log_file_path:
        litellm.set_verbose = True
    elif log_file_path:
        # When using file logging, disable LiteLLM's verbose mode to prevent console output
        litellm.set_verbose = False

    # Configure timeout settings
    litellm.request_timeout = float(os.environ.get("QX_REQUEST_TIMEOUT", "120"))

    # Configure retries
    litellm.num_retries = int(os.environ.get("QX_NUM_RETRIES", "3"))

    # Configure drop unsupported params behavior
    litellm.drop_params = True

    # Set up API key validation
    validate_api_keys()
