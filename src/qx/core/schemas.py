import os
from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum

from qx.core.constants import (
    AGENT_NAME_DEFAULT,
    AGENT_VERSION_DEFAULT,
    AGENT_DESCRIPTION_DEFAULT,
    AGENT_CONTEXT_DEFAULT,
    AGENT_OUTPUT_DEFAULT,
    AGENT_TOOLS_DEFAULT,
    AGENT_TEMPERATURE_DEFAULT,
    AGENT_MAX_TOKENS_DEFAULT,
    AGENT_TOP_P_DEFAULT,
    AGENT_FREQUENCY_PENALTY_DEFAULT,
    AGENT_PRESENCE_PENALTY_DEFAULT,
    AGENT_REASONING_BUDGET_DEFAULT,
    AGENT_EXECUTION_MODE_DEFAULT,
    AGENT_MAX_EXECUTION_TIME_DEFAULT,
    AGENT_MAX_ITERATIONS_DEFAULT,
    AGENT_AUTONOMOUS_ENABLED_DEFAULT,
    AGENT_MAX_CONCURRENT_TASKS_DEFAULT,
    AGENT_TASK_TIMEOUT_DEFAULT,
    AGENT_HEARTBEAT_INTERVAL_DEFAULT,
    AGENT_AUTO_RESTART_DEFAULT,
    AGENT_POLL_INTERVAL_DEFAULT,
    AGENT_MAX_FILE_SIZE_DEFAULT,
    AGENT_ALLOWED_PATHS_DEFAULT,
    AGENT_FORBIDDEN_PATHS_DEFAULT,
    AGENT_APPROVAL_REQUIRED_TOOLS_DEFAULT,
    AGENT_MAX_TOOL_CALLS_DEFAULT,
    AGENT_USE_CONSOLE_MANAGER_DEFAULT,
    AGENT_SOURCE_IDENTIFIER_DEFAULT,
    AGENT_ENABLE_RICH_OUTPUT_DEFAULT,
    AGENT_LOG_INTERACTIONS_DEFAULT,
)


class UserCreate(BaseModel):
    username: str
    email: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


# Agent Configuration Schemas


class AgentExecutionMode(str, Enum):
    INTERACTIVE = "interactive"
    AUTONOMOUS = "autonomous"
    HYBRID = "hybrid"


class AgentModelParameters(BaseModel):
    temperature: Optional[float] = Field(
        default_factory=lambda: float(
            os.environ.get("QX_AGENT_TEMPERATURE", str(AGENT_TEMPERATURE_DEFAULT))
        ),
        ge=0.0,
        le=2.0,
    )
    max_tokens: Optional[int] = Field(
        default_factory=lambda: int(
            os.environ.get("QX_AGENT_MAX_TOKENS", str(AGENT_MAX_TOKENS_DEFAULT))
        ),
        gt=0,
    )
    top_p: Optional[float] = Field(
        default_factory=lambda: float(
            os.environ.get("QX_AGENT_TOP_P", str(AGENT_TOP_P_DEFAULT))
        ),
        ge=0.0,
        le=1.0,
    )
    frequency_penalty: Optional[float] = Field(
        default_factory=lambda: float(
            os.environ.get(
                "QX_AGENT_FREQUENCY_PENALTY", str(AGENT_FREQUENCY_PENALTY_DEFAULT)
            )
        ),
        ge=-2.0,
        le=2.0,
    )
    presence_penalty: Optional[float] = Field(
        default_factory=lambda: float(
            os.environ.get(
                "QX_AGENT_PRESENCE_PENALTY", str(AGENT_PRESENCE_PENALTY_DEFAULT)
            )
        ),
        ge=-2.0,
        le=2.0,
    )
    reasoning_budget: Optional[str] = Field(
        default_factory=lambda: os.environ.get(
            "QX_AGENT_REASONING_BUDGET", AGENT_REASONING_BUDGET_DEFAULT
        )
    )


class AgentModel(BaseModel):
    name: str = Field(
        ..., description="Model name (e.g., openrouter/anthropic/claude-3.5-sonnet)"
    )
    parameters: AgentModelParameters = Field(default_factory=AgentModelParameters)


class AgentAutonomousConfig(BaseModel):
    enabled: bool = Field(
        default_factory=lambda: os.environ.get(
            "QX_AGENT_AUTONOMOUS_ENABLED", "false"
        ).lower()
        == "true"
        if os.environ.get("QX_AGENT_AUTONOMOUS_ENABLED")
        else AGENT_AUTONOMOUS_ENABLED_DEFAULT
    )
    max_concurrent_tasks: int = Field(
        default_factory=lambda: int(
            os.environ.get(
                "QX_AGENT_MAX_CONCURRENT_TASKS", str(AGENT_MAX_CONCURRENT_TASKS_DEFAULT)
            )
        ),
        ge=1,
        le=10,
    )
    task_timeout: int = Field(
        default_factory=lambda: int(
            os.environ.get("QX_AGENT_TASK_TIMEOUT", str(AGENT_TASK_TIMEOUT_DEFAULT))
        ),
        gt=0,
    )
    heartbeat_interval: int = Field(
        default_factory=lambda: int(
            os.environ.get(
                "QX_AGENT_HEARTBEAT_INTERVAL", str(AGENT_HEARTBEAT_INTERVAL_DEFAULT)
            )
        ),
        gt=0,
    )
    auto_restart: bool = Field(
        default_factory=lambda: os.environ.get("QX_AGENT_AUTO_RESTART", "false").lower()
        == "true"
        if os.environ.get("QX_AGENT_AUTO_RESTART")
        else AGENT_AUTO_RESTART_DEFAULT
    )
    poll_interval: int = Field(
        default_factory=lambda: int(
            os.environ.get("QX_AGENT_POLL_INTERVAL", str(AGENT_POLL_INTERVAL_DEFAULT))
        ),
        gt=0,
    )


class AgentConstraints(BaseModel):
    max_file_size: str = Field(
        default_factory=lambda: os.environ.get(
            "QX_AGENT_MAX_FILE_SIZE", AGENT_MAX_FILE_SIZE_DEFAULT
        )
    )
    allowed_paths: List[str] = Field(
        default_factory=lambda: os.environ.get("QX_AGENT_ALLOWED_PATHS", "./").split(
            ","
        )
        if os.environ.get("QX_AGENT_ALLOWED_PATHS")
        else AGENT_ALLOWED_PATHS_DEFAULT
    )
    forbidden_paths: List[str] = Field(
        default_factory=lambda: os.environ.get(
            "QX_AGENT_FORBIDDEN_PATHS", "/etc,/sys,/proc"
        ).split(",")
        if os.environ.get("QX_AGENT_FORBIDDEN_PATHS")
        else AGENT_FORBIDDEN_PATHS_DEFAULT
    )
    approval_required_tools: List[str] = Field(
        default_factory=lambda: os.environ.get(
            "QX_AGENT_APPROVAL_REQUIRED_TOOLS", ""
        ).split(",")
        if os.environ.get("QX_AGENT_APPROVAL_REQUIRED_TOOLS")
        else AGENT_APPROVAL_REQUIRED_TOOLS_DEFAULT
    )
    max_tool_calls_per_turn: int = Field(
        default_factory=lambda: int(
            os.environ.get("QX_AGENT_MAX_TOOL_CALLS", str(AGENT_MAX_TOOL_CALLS_DEFAULT))
        ),
        gt=0,
    )


class AgentConsoleConfig(BaseModel):
    use_console_manager: bool = Field(
        default_factory=lambda: os.environ.get(
            "QX_AGENT_USE_CONSOLE_MANAGER", "true"
        ).lower()
        == "true"
        if os.environ.get("QX_AGENT_USE_CONSOLE_MANAGER")
        else AGENT_USE_CONSOLE_MANAGER_DEFAULT
    )
    source_identifier: Optional[str] = Field(
        default_factory=lambda: os.environ.get("QX_AGENT_SOURCE_IDENTIFIER")
        or AGENT_SOURCE_IDENTIFIER_DEFAULT
    )
    enable_rich_output: bool = Field(
        default_factory=lambda: os.environ.get(
            "QX_AGENT_ENABLE_RICH_OUTPUT", "true"
        ).lower()
        == "true"
        if os.environ.get("QX_AGENT_ENABLE_RICH_OUTPUT")
        else AGENT_ENABLE_RICH_OUTPUT_DEFAULT
    )
    log_interactions: bool = Field(
        default_factory=lambda: os.environ.get(
            "QX_AGENT_LOG_INTERACTIONS", "true"
        ).lower()
        == "true"
        if os.environ.get("QX_AGENT_LOG_INTERACTIONS")
        else AGENT_LOG_INTERACTIONS_DEFAULT
    )


class AgentExecutionConfig(BaseModel):
    mode: AgentExecutionMode = Field(
        default_factory=lambda: AgentExecutionMode(
            os.environ.get("QX_AGENT_EXECUTION_MODE", AGENT_EXECUTION_MODE_DEFAULT)
        )
    )
    autonomous_config: AgentAutonomousConfig = Field(
        default_factory=AgentAutonomousConfig
    )
    constraints: AgentConstraints = Field(default_factory=AgentConstraints)
    console: AgentConsoleConfig = Field(default_factory=AgentConsoleConfig)


class AgentLifecycleHooks(BaseModel):
    on_start: Optional[str] = Field(default=None)
    on_task_received: Optional[str] = Field(default=None)
    on_error: Optional[str] = Field(default=None)
    on_shutdown: Optional[str] = Field(default=None)


class AgentConfig(BaseModel):
    """Complete agent configuration schema that preserves existing YAML structure"""

    # Basic agent metadata
    name: Optional[str] = Field(
        default_factory=lambda: os.environ.get("QX_AGENT_NAME", AGENT_NAME_DEFAULT)
    )
    version: Optional[str] = Field(
        default_factory=lambda: os.environ.get(
            "QX_AGENT_VERSION", AGENT_VERSION_DEFAULT
        )
    )
    description: Optional[str] = Field(
        default_factory=lambda: os.environ.get(
            "QX_AGENT_DESCRIPTION", AGENT_DESCRIPTION_DEFAULT
        )
    )

    # Core agent configuration (preserving existing structure)
    role: str = Field(..., description="Agent role and persona")
    instructions: str = Field(..., description="Detailed operational guidelines")
    context: Optional[str] = Field(
        default_factory=lambda: os.environ.get("QX_AGENT_CONTEXT")
        or AGENT_CONTEXT_DEFAULT,
        description="Context template with placeholders",
    )
    output: Optional[str] = Field(
        default_factory=lambda: os.environ.get("QX_AGENT_OUTPUT")
        or AGENT_OUTPUT_DEFAULT,
        description="Response formatting guidelines",
    )

    # Tools configuration
    tools: List[str] = Field(
        default_factory=lambda: os.environ.get("QX_AGENT_TOOLS", "").split(",")
        if os.environ.get("QX_AGENT_TOOLS")
        else AGENT_TOOLS_DEFAULT,
        description="Available tools for the agent",
    )

    # Model configuration (preserving existing structure)
    model: AgentModel = Field(..., description="LLM model configuration")

    # Execution constraints (preserving existing structure)
    max_execution_time: Optional[int] = Field(
        default_factory=lambda: int(
            os.environ.get(
                "QX_AGENT_MAX_EXECUTION_TIME", str(AGENT_MAX_EXECUTION_TIME_DEFAULT)
            )
        ),
        gt=0,
    )
    max_iterations: Optional[int] = Field(
        default_factory=lambda: int(
            os.environ.get("QX_AGENT_MAX_ITERATIONS", str(AGENT_MAX_ITERATIONS_DEFAULT))
        ),
        gt=0,
    )

    # New modular agent capabilities
    execution: AgentExecutionConfig = Field(default_factory=AgentExecutionConfig)
    lifecycle: AgentLifecycleHooks = Field(default_factory=AgentLifecycleHooks)

    # Additional metadata
    created_at: Optional[str] = Field(default=None)
    updated_at: Optional[str] = Field(default=None)
    tags: List[str] = Field(default_factory=list)
