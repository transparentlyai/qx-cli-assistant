# LLM module - modularized components for LLM interaction

# Import key functions and classes
from .prompts import load_and_format_system_prompt
from .config import configure_litellm, ReliabilityConfig, validate_api_keys
from .messages import MessageCache, get_message_role, has_system_message
from .streaming import StreamingHandler
from .tools import ToolProcessor
from .fallbacks import FallbackHandler, LiteLLMCaller

# Main agent class is still in the parent llm.py to maintain import paths
# Import it here for convenience (avoiding circular imports by importing after the modules above)
try:
    from ..llm import QXLLMAgent, initialize_llm_agent, query_llm, QXRunResult
except ImportError:
    # This might happen during development/testing - these will be available at runtime
    pass

__all__ = [
    # Core functions
    "load_and_format_system_prompt",
    "configure_litellm",
    "validate_api_keys",
    # Classes
    "ReliabilityConfig",
    "MessageCache",
    "StreamingHandler",
    "ToolProcessor",
    "FallbackHandler",
    "LiteLLMCaller",
    # Utility functions
    "get_message_role",
    "has_system_message",
    # Main classes (if available)
    "QXLLMAgent",
    "QXRunResult",
    "initialize_llm_agent",
    "query_llm",
]
