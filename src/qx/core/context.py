from dataclasses import dataclass
from typing import Optional # Added Optional for future flexibility

from rich.console import Console as RichConsole

@dataclass
class QXToolDependencies:
    """
    Holds dependencies that can be injected into PydanticAI tools via RunContext.
    """
    console: RichConsole
    # Potentially other shared dependencies can be added here later,
    # e.g., a shared HTTP client, config access, etc.

    # Example of adding another dependency:
    # another_service: Optional[Any] = None 