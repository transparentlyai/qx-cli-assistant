# QX Core Subsystems Architecture

This document provides a comprehensive overview of the QX codebase architecture, detailing each core subsystem, its responsibilities, and interactions.

## Overview

QX is built on a modular, plugin-based architecture with 11 core subsystems. The design emphasizes extensibility through YAML configuration, dynamic loading, and clear separation of concerns.

## Core Subsystems

### 1. Agent Management Subsystem

**Purpose**: Manages AI agent lifecycle, loading, and execution

**Key Components**:
- `agent_manager.py` - Central orchestrator for agent lifecycle (loading, switching, sessions)
- `agent_loader.py` - Handles YAML-based agent configuration loading and discovery
- `schemas.py` - Defines `AgentConfig` data model with execution modes, model params, constraints

**Features**:
- YAML-based agent discovery from multiple directories
- Dynamic agent switching during runtime
- Agent session management
- Support for interactive, autonomous, and hybrid execution modes

**Interactions**:
- Works with Console Manager for UI output
- Integrates with LLM subsystem for agent execution
- Coordinates with Team Manager for multi-agent scenarios

### 2. Team & Multi-Agent Coordination

**Purpose**: Orchestrates collaborative workflows between multiple agents

**Key Components**:
- `team_manager.py` - Manages team composition, persistence, and agent selection
- `team_mode_manager.py` - Controls team mode state and transitions
- `langgraph_supervisor.py` - Implements LangGraph supervisor pattern for agent delegation
- `langgraph_model_adapter.py` - Adapts QX agents to LangChain/LangGraph models
- `langgraph_tool_adapter.py` - Manages tool binding for LangGraph integration

**Features**:
- Dynamic team composition
- LangGraph-based workflow orchestration
- Agent delegation with supervisor pattern
- Persistent team state management

**Interactions**:
- Uses Agent Manager to load individual agents
- Leverages Console Manager for team-wide communications
- Integrates with LLM subsystem through adapters

### 3. LLM Integration

**Purpose**: Provides unified interface to language models via liteLLM

**Key Components**:
- `llm.py` - Core `QXLLMAgent` class wrapping liteLLM functionality
- `llm_utils.py` - Utilities for agent initialization and MCP integration
- `llm_components/` - Modular components:
  - `config.py` - LiteLLM configuration
  - `messages.py` - Message handling utilities
  - `prompts.py` - Prompt formatting
  - `streaming.py` - Streaming response handling
  - `tools.py` - Tool calling integration

**Features**:
- Unified interface across multiple LLM providers
- Streaming response support with spinners
- Tool/function calling capabilities
- Message history management
- Token usage tracking

**Interactions**:
- Used by Agent Manager for executing agents
- Integrated with Plugin/Tool system for function calling
- Works with Console Manager for streaming outputs

### 4. Console & UI

**Purpose**: Terminal UI, user interactions, and output formatting

**Key Components**:
- `console_manager.py` - Thread-safe console access via producer-consumer pattern
- `cli/qpromp.py` - Main interactive prompt loop using prompt_toolkit
- `cli/commands.py` - Command handling logic (/help, /exit, etc.)
- `cli/theme.py` - Rich terminal theming
- `cli/quote_bar_component.py` - Agent message rendering with color coding
- `cli/completer.py` - Command and file path autocompletion

**Features**:
- Thread-safe console output
- Rich markdown rendering with syntax highlighting
- Agent-specific message styling
- Interactive prompt with history
- Command autocompletion

**Interactions**:
- Used by all subsystems for output
- Integrates with Approval Handler for user confirmations
- Works with Session Manager for conversation persistence

### 5. Configuration Management

**Purpose**: Hierarchical configuration loading and environment management

**Key Components**:
- `config_manager.py` - Main configuration orchestrator

**Features**:
- **3-tier configuration hierarchy**:
  1. System-level: `/etc/qx/qx.conf` (lowest priority)
  2. User-level: `~/.config/qx/qx.conf`
  3. Project-level: `<project>/.Q/config/qx.conf` (highest priority)
  4. Environment variables (final override)
- **Security checks**: Prevents API keys in project configs
- **Context loading**: 
  - User context from `~/.config/qx/user.md`
  - Project context from `<project>/.Q/project.md`
  - Project file tree generation with ignore patterns
- **MCP server configuration management**

**Key Environment Variables**:
- `QX_MODEL_NAME` - LLM model selection
- `QX_MODEL_TEMPERATURE`, `QX_MODEL_MAX_TOKENS` - Model parameters
- `QX_USER_CONTEXT`, `QX_PROJECT_CONTEXT` - Context data
- API keys for various providers

### 6. Tool Plugin System

**Purpose**: Dynamic tool discovery, loading, and execution

**Key Components**:
- `plugin_manager.py` - Plugin discovery and loading
- `plugins/*_plugin.py` - Individual tool implementations

**Plugin Requirements**:
- File must be named `*_plugin.py`
- Tool functions must be named `*_tool`
- Must have Pydantic BaseModel parameter for input schema
- Can optionally accept `console` parameter

**Built-in Plugins**:
- `current_time_plugin` - System time operations
- `execute_shell_plugin` - Shell command execution
- `read_file_plugin` - File reading operations
- `write_file_plugin` - File writing operations
- `web_fetch_plugin` - Web content fetching

**Features**:
- Automatic plugin discovery
- Pydantic-based schema validation
- OpenAI-compatible tool schemas
- Console manager integration for output

### 7. Logging Infrastructure

**Purpose**: Centralized logging configuration and management

**Key Components**:
- `logging_config.py` - Logging setup and configuration

**Features**:
- **Dual-mode logging**:
  - Console mode: Only QX logs to console
  - File mode: All logs (QX + libraries) to file
- **Log level control** via `QX_LOG_LEVEL`
- **LiteLLM logging integration**
- **Library log suppression** for clean console output
- **Global exception handling**

**Environment Variables**:
- `QX_LOG_LEVEL` - Sets logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `QX_LOG_FILE` - Redirects all logs to specified file

### 8. Session & State Management

**Purpose**: Conversation persistence and runtime state tracking

**Key Components**:
- `session_manager.py` - Conversation history persistence
- `state_manager.py` - Runtime state tracking (details mode, etc.)
- `history_utils.py` - History parsing and formatting

**Features**:
- Automatic session saving
- Session recovery with `/recover` command
- Configurable session retention
- State persistence across commands

**Interactions**:
- Used by CLI for session recovery
- Integrated with Agent Manager for agent sessions
- Works with Team Manager for team persistence

### 9. MCP (Model Context Protocol)

**Purpose**: External tool server integration

**Key Components**:
- `mcp_manager.py` - MCP server lifecycle management

**Features**:
- Server discovery from configuration
- Dynamic tool loading from MCP servers
- Connection management
- Tool schema aggregation
- Server health monitoring

**Interactions**:
- Integrated with LLM subsystem for expanded tool access
- Works through Console Manager for server status
- Coordinated by Config Manager for server definitions

### 10. Approval & Security

**Purpose**: User approval flows and security controls

**Key Components**:
- `approval_handler.py` - Approval flow orchestration
- `user_prompts.py` - User interaction primitives

**Features**:
- Dangerous operation approval (file writes, shell commands)
- Approve-all mode toggle (Ctrl+A)
- Security checks for sensitive operations
- Non-interactive mode support

**Interactions**:
- Used by Tool Plugin system for dangerous operations
- Integrates with Console Manager for prompts
- Respects global hotkey state

### 11. Utility & Infrastructure

**Purpose**: Supporting services and shared utilities

**Key Components**:
- `async_utils.py` - Async task management
- `hotkey_manager.py` & `global_hotkeys.py` - Keyboard shortcuts
- `http_client_manager.py` - Shared HTTP client pooling
- `paths.py` - Path resolution utilities
- `constants.py` - System-wide constants

**Features**:
- Global hotkey support (Ctrl+A, Ctrl+T, etc.)
- HTTP client connection pooling
- Path normalization and resolution
- Async utility functions

## Key Architectural Patterns

### 1. YAML-Driven Configuration
Agents are defined entirely in YAML files, allowing for:
- Easy agent creation without code changes
- Version control friendly agent definitions
- Runtime agent discovery and loading

### 2. Producer-Consumer Console
Thread-safe console access ensures:
- No interleaved output from concurrent operations
- Clean separation of UI concerns
- Consistent output formatting

### 3. Singleton Managers
Most subsystems use singleton pattern with global accessors:
- Single source of truth for state
- Easy access from any component
- Lifecycle management

### 4. Plugin Architecture
Tools are dynamically discovered and loaded:
- Extensibility without core changes
- Consistent tool interface
- Schema-driven validation

### 5. Adapter Pattern
LangGraph adapters bridge QX agents to LangChain ecosystem:
- Leverage existing LangChain tools
- Maintain QX-specific features
- Clean integration boundaries

### 6. Layered Architecture
Clear separation between:
- CLI layer (user interaction)
- Core layer (business logic)
- Plugin layer (extensions)

## Configuration Hierarchy

Configuration is loaded in the following priority order (highest to lowest):

1. **Environment variables** (highest priority)
2. **Project configuration** (`<project>/.Q/config/qx.conf`)
3. **User configuration** (`~/.config/qx/qx.conf`)
4. **System configuration** (`/etc/qx/qx.conf`) (lowest priority)

This allows for:
- System-wide defaults
- User-specific preferences
- Project-specific overrides
- Runtime configuration via environment

## Security Considerations

1. **API Key Protection**: API keys are prevented in project configs to avoid version control exposure
2. **Approval Flows**: Dangerous operations require explicit user approval
3. **Path Validation**: File operations validate paths to prevent directory traversal
4. **Command Sanitization**: Shell commands are displayed before execution

## Extension Points

The architecture provides several extension points:

1. **Custom Agents**: Add YAML files to agent directories
2. **Tool Plugins**: Create `*_plugin.py` files with `*_tool` functions
3. **MCP Servers**: Configure external tool servers
4. **Custom Commands**: Extend command handling in CLI
5. **Theme Customization**: Modify console themes and colors

## Future Considerations

The architecture is designed to support:
- Additional LLM providers through liteLLM
- New agent execution modes
- Enhanced team collaboration patterns
- Extended tool ecosystems
- Advanced debugging and monitoring capabilities