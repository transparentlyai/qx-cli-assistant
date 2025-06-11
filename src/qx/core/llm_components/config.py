import json
import logging
import os
from typing import Dict, List

import litellm

logger = logging.getLogger(__name__)


class ReliabilityConfig:
    """Handles reliability configuration parsing and storage."""

    def __init__(self):
        self.fallback_models: List[str] = []
        self.context_window_fallbacks: Dict[str, str] = {}
        self.fallback_api_keys: Dict[str, str] = {}
        self.fallback_api_bases: Dict[str, str] = {}
        self.fallback_timeout: float = 45.0
        self.fallback_cooldown: float = 60.0
        self.retry_delay: float = 1.0
        self.max_retry_delay: float = 60.0
        self.backoff_factor: float = 2.0

    def load_from_environment(self) -> None:
        """Parse and setup reliability configuration from environment variables."""
        # Parse fallback models
        fallback_models_str = os.environ.get("QX_FALLBACK_MODELS", "")
        if fallback_models_str:
            self.fallback_models = [
                model.strip() for model in fallback_models_str.split(",")
            ]

        # Parse context window fallbacks
        context_fallbacks_str = os.environ.get("QX_CONTEXT_WINDOW_FALLBACKS", "{}")
        try:
            self.context_window_fallbacks = json.loads(context_fallbacks_str)
        except json.JSONDecodeError:
            logger.warning(
                "Invalid JSON for QX_CONTEXT_WINDOW_FALLBACKS, using empty dict"
            )
            self.context_window_fallbacks = {}

        # Parse fallback API keys
        fallback_keys_str = os.environ.get("QX_FALLBACK_API_KEYS", "{}")
        try:
            self.fallback_api_keys = json.loads(fallback_keys_str)
        except json.JSONDecodeError:
            logger.warning("Invalid JSON for QX_FALLBACK_API_KEYS, using empty dict")
            self.fallback_api_keys = {}

        # Parse fallback API bases
        fallback_bases_str = os.environ.get("QX_FALLBACK_API_BASES", "{}")
        try:
            self.fallback_api_bases = json.loads(fallback_bases_str)
        except json.JSONDecodeError:
            logger.warning("Invalid JSON for QX_FALLBACK_API_BASES, using empty dict")
            self.fallback_api_bases = {}

        # Set up timeout and retry configuration
        self.fallback_timeout = float(os.environ.get("QX_FALLBACK_TIMEOUT", "45"))
        self.fallback_cooldown = float(os.environ.get("QX_FALLBACK_COOLDOWN", "60"))
        self.retry_delay = float(os.environ.get("QX_RETRY_DELAY", "1.0"))
        self.max_retry_delay = float(os.environ.get("QX_MAX_RETRY_DELAY", "60.0"))
        self.backoff_factor = float(os.environ.get("QX_BACKOFF_FACTOR", "2.0"))

        logger.debug(f"Reliability config - Fallback models: {self.fallback_models}")
        logger.debug(f"Context window fallbacks: {self.context_window_fallbacks}")
        logger.debug(f"Fallback timeout: {self.fallback_timeout}s")


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


def configure_litellm() -> ReliabilityConfig:
    """Configure LiteLLM settings and return reliability configuration."""
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

    # Parse and return reliability configuration
    reliability_config = ReliabilityConfig()
    reliability_config.load_from_environment()

    return reliability_config
