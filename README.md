# QX - AI-Powered Coding CLI Agent

[![Python](https://img.shields.io/badge/Python-3.13+-blue.svg)](https://python.org)
[![LiteLLM](https://img.shields.io/badge/Powered%20by-LiteLLM-purple.svg)](https://docs.litellm.ai/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Models](https://img.shields.io/badge/Models-100+-orange.svg)](docs/MODEL_PROVIDERS.md)
[![Platform](https://img.shields.io/badge/Platform-Linux%20%7C%20macOS%20%7C%20Windows-lightgrey.svg)]()
[![CLI](https://img.shields.io/badge/Interface-CLI-blue.svg)]()

QX is an intelligent command-line interface (CLI) agent designed to assist with software development, DevOps tasks, and code interaction within your project workspace. Built with Python and powered by LiteLLM, QX provides access to 100+ LLM providers with enterprise-grade reliability features.

## ✨ Features

- 🤖 **Multi-LLM Support**: Access 100+ LLM providers (OpenAI, Anthropic, Google, Azure, etc.) through LiteLLM
- 🔄 **Enterprise Reliability**: Automatic retries, fallbacks, and circuit breakers for robust operation
- 🛠️ **Tool Integration**: Extensible plugin system for shell commands, file operations, web searches, and more
- 📁 **Project-Aware**: Automatically understands your project structure and context
- 🔍 **MCP Protocol Support**: Model Context Protocol for enhanced capabilities
- 💬 **Interactive & Streaming**: Real-time streaming responses with rich formatting
- 🎯 **Context Management**: Intelligent context window scaling and management
- 🔒 **Security-First**: Built-in approval workflows for sensitive operations
- ⌨️ **Global Hotkeys**: System-wide hotkey support that works during any operation
- 🎛️ **Advanced Controls**: Real-time toggles for details mode, output control, and approvals

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd qx

# Install dependencies (requires Python 3.13+)
uv install

# Run QX
uv run qx
```

### Configuration

QX uses a **hierarchical configuration system** that loads settings from multiple sources in order of priority. Later sources override earlier ones, allowing for flexible system-wide, user-specific, and project-specific configurations.

> **📖 For detailed model setup instructions and API key acquisition, see the [Model Providers Guide](docs/MODEL_PROVIDERS.md)**

#### Configuration Hierarchy (Lowest to Highest Priority)

1. **📁 System-wide**: `/etc/qx/qx.conf` - Global defaults for all users
2. **👤 User-level**: `~/.config/qx/qx.conf` - Personal user settings
3. **🚀 Project-level**: `<project-directory>/.Q/qx.conf` - **Highest priority**, project-specific overrides

#### How It Works

- **Cascading Override**: Each level inherits from the previous and can override any setting
- **Environment Variables**: Always take precedence over all configuration files
- **Selective Override**: You only need to specify the settings you want to change at each level

#### Example Hierarchy Setup

**System-wide** (`/etc/qx/qx.conf`) - Organization defaults:
```bash
# Company-wide defaults
QX_MODEL_NAME=openrouter/openai/gpt-4o-mini  # Cost-effective default
QX_NUM_RETRIES=3
QX_REQUEST_TIMEOUT=60
```

**User-level** (`~/.config/qx/qx.conf`) - Personal preferences:
```bash
# Personal API key and preferences
OPENROUTER_API_KEY=sk-or-v1-your_personal_key_here
QX_MODEL_NAME=openrouter/anthropic/claude-3.5-sonnet  # Overrides system default
QX_ENABLE_STREAMING=true
```

**Project-level** (`myproject/.Q/qx.conf`) - Project-specific needs:
```bash
# Project-specific overrides for this codebase
QX_MODEL_NAME=openrouter/openai/gpt-4o  # High-performance model for this project
QX_FALLBACK_MODELS=openrouter/anthropic/claude-3.5-sonnet
QX_PROJECT_CONTEXT="This is a Python web application using FastAPI"
```

#### Minimal Configuration

The only required setting is a valid API key and model. Create any of the above files with:

```bash
# Model Configuration (LiteLLM format)
QX_MODEL_NAME=openrouter/anthropic/claude-3.5-sonnet

# API Key (choose one based on your provider)
OPENROUTER_API_KEY=sk-or-v1-your_openrouter_api_key_here
# OPENAI_API_KEY=sk-your_openai_api_key_here
# ANTHROPIC_API_KEY=sk-ant-your_anthropic_api_key_here

# Optional: Model parameters
QX_MODEL_TEMPERATURE=0.7
QX_MODEL_MAX_TOKENS=4096
QX_MODEL_REASONING_EFFORT=medium  # For reasoning models (none, low, medium, high)
```

#### Configuration Discovery

QX automatically discovers and loads configurations in this order:
1. **System defaults** (`/etc/qx/qx.conf`) - Baseline configuration
2. **User preferences** (`~/.config/qx/qx.conf`) - Personal overrides  
3. **Project settings** (`<project>/.Q/qx.conf`) - Project-specific overrides
4. **Environment variables** - Runtime overrides (highest priority)

#### Environment Variable Overrides

Any configuration file setting can be overridden at runtime using environment variables:

```bash
# Override model for a single session
QX_MODEL_NAME=openrouter/openai/gpt-4o uv run qx

# Use different API key temporarily  
OPENROUTER_API_KEY=sk-different-key uv run qx

# Enable debug logging
QX_LOG_LEVEL=DEBUG uv run qx

# Test with fallback models
QX_FALLBACK_MODELS=gpt-4o,claude-3.5-sonnet uv run qx
```

This hierarchical system allows for great flexibility - you can set organization defaults, personal preferences, project-specific settings, and runtime overrides that all work together seamlessly.

For a complete configuration example with all reliability features, see [`qx.conf.example`](qx.conf.example).

## 💡 Usage

### Basic Usage

```bash
# Interactive mode
uv run qx

# Single prompt mode
uv run qx "Help me refactor this function"

# Exit after response
uv run qx "What files are in this project?" --exit
```

### ⌨️ Global Hotkeys

QX supports global hotkeys that work at any time during operation, including while the AI is processing:

| Hotkey | Action | Description |
|--------|--------|-------------|
| **Ctrl+T** | Toggle Details | Show/hide AI reasoning process |
| **Ctrl+A** | Toggle Approve All | Enable/disable automatic approval for tool operations |
| **Ctrl+O** | Toggle Stdout | Show/hide command output during tool execution |
| **Ctrl+P** | Toggle Mode | Switch between PLANNING and IMPLEMENTING modes |
| **Ctrl+R** | History Search | Search command history (available during input) |
| **Ctrl+E** | External Editor | Edit current input in external text editor |
| **Ctrl+C** | Cancel Operation | Interrupt current operation |
| **Ctrl+D** | Exit Application | Gracefully exit QX |
| **F12** | Emergency Cancel | Alternative cancel option |

**Note**: Global hotkeys are automatically suspended during approval prompts to prevent conflicts with user input.

### 📝 External Editor Integration

QX supports editing input in your preferred external text editor using **Ctrl+E**:

#### Supported Editors
- **vi/vim/nvim** - Terminal-based editors
- **nano** - Simple terminal editor
- **code/vscode** - Visual Studio Code (with `--wait` flag)
- **Custom editors** - Any editor can be configured

#### Configuration
Set the `QX_DEFAULT_EDITOR` environment variable to choose your preferred editor:

```bash
# Use Visual Studio Code
export QX_DEFAULT_EDITOR=code

# Use nano for simple editing
export QX_DEFAULT_EDITOR=nano

# Use neovim
export QX_DEFAULT_EDITOR=nvim
```

#### Usage
1. Type some text in the QX prompt
2. Press **Ctrl+E** to open the text in your editor
3. Edit the content and save/exit the editor
4. The updated text appears in the QX input buffer
5. Press Enter to submit or continue editing

### 🛡️ Approval System

QX includes a comprehensive approval system for tool operations:

#### Approval Options
When QX requests permission to perform an operation, you have four choices:

- **Y** (Yes): Approve this single operation
- **N** (No): Deny this operation
- **A** (All): **Approve All** - Automatically approve all subsequent tool operations in this session
- **C** (Cancel): Cancel the operation

#### Approve All Mode
The "Approve All" feature allows you to:
- Press **A** during any tool approval to activate automatic approval for the session
- Use **Ctrl+A** hotkey to toggle Approve All mode on/off at any time
- See visual confirmation when mode is activated/deactivated
- Session-based: Mode automatically resets when QX restarts

#### Example Approval Flow
```
Write: /home/user/project/script.py
--- Content Preview ---
#!/usr/bin/env python3
print("Hello, World!")
--- End Preview ---

Allow Qx to write to file: '/home/user/project/script.py'? (Yes, No, All, Cancel) a
'Approve All' activated for this session.
```

After pressing **A**, all subsequent tool operations will be auto-approved with no further prompts.

### Advanced Usage

```bash
# Enable debug logging
QX_LOG_LEVEL=DEBUG uv run qx

# Use specific model
QX_MODEL_NAME=openrouter/openai/gpt-4o uv run qx

# Enable reliability features
QX_FALLBACK_MODELS=gpt-4o,claude-3.5-sonnet uv run qx
```

## 🔧 Configuration Options

### Core Settings
```bash
QX_MODEL_NAME=openrouter/anthropic/claude-3.5-sonnet  # Primary model
QX_MODEL_TEMPERATURE=0.7                              # Sampling temperature  
QX_MODEL_MAX_TOKENS=4096                             # Max output tokens
QX_MODEL_REASONING_EFFORT=medium                     # Reasoning effort (none, low, medium, high)
QX_ENABLE_STREAMING=true                             # Enable streaming responses
```

### Reliability & Resilience
```bash
# Retry Configuration
QX_NUM_RETRIES=3              # Number of retry attempts
QX_RETRY_DELAY=1.0            # Base delay between retries
QX_BACKOFF_FACTOR=2.0         # Exponential backoff multiplier

# Fallback Models
QX_FALLBACK_MODELS=gpt-4o,claude-3.5-sonnet,gemini-1.5-pro

# Context Window Auto-Scaling
QX_CONTEXT_WINDOW_FALLBACKS={"gpt-3.5-turbo":"gpt-3.5-turbo-16k"}

# Timeout Settings
QX_REQUEST_TIMEOUT=120        # Individual request timeout
QX_FALLBACK_TIMEOUT=45        # Total fallback timeout
```

See [`RELIABILITY.md`](RELIABILITY.md) for complete reliability configuration guide.

## 🌐 Supported Providers

QX supports 100+ LLM providers through [LiteLLM](https://docs.litellm.ai/), including:

- **OpenRouter** (recommended): Access to multiple providers through one API
- **OpenAI**: GPT-4, GPT-3.5, and other OpenAI models
- **Anthropic**: Claude 3.5 Sonnet, Claude 3 Haiku, etc.
- **Google**: Gemini 1.5 Pro, Gemini Flash, etc.
- **Azure OpenAI**: Enterprise-grade OpenAI models
- **Local Models**: Ollama, vLLM, and other local deployments

### Provider Examples

```bash
# OpenRouter (multiple providers through one API)
QX_MODEL_NAME=openrouter/anthropic/claude-3.5-sonnet
OPENROUTER_API_KEY=sk-or-v1-...

# OpenAI Direct
QX_MODEL_NAME=gpt-4o
OPENAI_API_KEY=sk-...

# Anthropic Direct  
QX_MODEL_NAME=claude-3-5-sonnet-20241022
ANTHROPIC_API_KEY=sk-ant-...

# Local Model
QX_MODEL_NAME=ollama/llama3.2
```

For detailed setup instructions, API key acquisition, and model selection guidance, see the **[Model Providers Guide](docs/MODEL_PROVIDERS.md)**.

## 🛠️ Available Tools

QX includes several built-in tools that extend its capabilities:

### Core Tools
- **🖥️ Shell Commands**: Execute system commands with safety checks
- **📁 File Operations**: Read, write, and modify files with approval workflows
- **🌐 Web Search**: Search the web using Brave Search API (via MCP)
- **📊 Project Analysis**: Automatically analyze project structure and dependencies

### Model Context Protocol (MCP)
QX supports MCP servers for extended functionality:
- **Brave Search**: Web search capabilities
- **Custom MCP Servers**: Add your own MCP integrations

Configuration in `.Q/mcp_servers.json`:
```json
{
  "brave-search": {
    "command": "mcp-server-brave-search",
    "args": ["--api-key", "${BRAVE_API_KEY}"]
  }
}
```

## ⌨️ Global Hotkey System

QX includes a sophisticated global hotkey system that provides system-wide key capture capabilities:

### Architecture

- **Global Key Capture**: Uses termios and tty for Unix terminal hotkey detection
- **Suspend/Resume Pattern**: Automatically suspends global hotkeys during user input to prevent conflicts
- **Async/Sync Support**: Handles both synchronous and asynchronous callback functions
- **Terminal Compatibility**: Supports multiple terminal emulators and key sequence patterns

### Key Features

- **Zero Dependencies**: Pure Python implementation using only standard library modules
- **Conflict Prevention**: Intelligent suspend/resume prevents interference with prompt_toolkit input
- **Performance Optimized**: Queue-based overflow protection and timeout handling
- **Comprehensive Key Support**: F-keys, Alt combinations, Ctrl sequences, and navigation keys

### Technical Implementation

The global hotkey system consists of two main components:

1. **GlobalHotkeys Class** (`global_hotkeys.py`):
   - Low-level terminal input capture using termios
   - State machine parsing for multi-character escape sequences
   - Thread-based input listener with async callback support

2. **QXHotkeyManager Class** (`hotkey_manager.py`):
   - High-level hotkey action registration and management
   - Integration between global capture and QX functionality
   - Centralized handler registry for hotkey actions

### Suspend/Resume Pattern

Global hotkeys are automatically suspended during:
- User input prompts (prompt_toolkit active)
- Tool approval dialogs
- Any interactive input operations

This prevents key conflicts and ensures reliable user interaction.

## 🔧 Development & Plugins

QX uses a modern plugin architecture where tools are defined as async functions with Pydantic models for type safety.

### Creating a Plugin

1. **Create Plugin File**: Add a new file in `src/qx/plugins/`
2. **Define Models**: Use Pydantic for input/output validation
3. **Implement Tool**: Create async function with proper type hints
4. **Register**: Plugin auto-discovery handles registration

Example plugin structure:
```python
from pydantic import BaseModel, Field
from rich.console import Console

class MyToolInput(BaseModel):
    task: str = Field(description="Task to perform")

class MyToolOutput(BaseModel):
    result: str = Field(description="Task result")

async def my_tool(console: Console, args: MyToolInput) -> MyToolOutput:
    # Tool implementation here
    return MyToolOutput(result=f"Completed: {args.task}")
```

For comprehensive tool development guidance, see the **[Tool Development Guide](docs/TOOL_DEVELOPMENT.md)**.

## 🧪 Testing & Validation

### Test Reliability Configuration
```bash
python test_reliability.py
```

### Debug Mode
```bash
QX_LOG_LEVEL=DEBUG uv run qx
```

### Validate Configuration
```bash
# Check if configuration is properly loaded
uv run qx --version
```

## 📚 Documentation

### Configuration & Setup
- **[`qx.conf.example`](qx.conf.example)**: Complete configuration reference
- **[Model Providers Guide](docs/MODEL_PROVIDERS.md)**: Comprehensive guide to using different AI models and providers
- **[`RELIABILITY.md`](docs/RELIABILITY.md)**: Reliability and resilience guide
- **[`HOTKEYS.md`](docs/HOTKEYS.md)**: Global hotkey system documentation

### Development & Architecture  
- **[Tool Development Guide](docs/TOOL_DEVELOPMENT.md)**: Complete guide for creating custom tools and plugins
- **[Console Manager Architecture](docs/CONSOLE_MANAGER.md)**: Producer-consumer pattern for concurrent console access

### External References
- **[LiteLLM Docs](https://docs.litellm.ai/)**: Upstream LiteLLM documentation
- **[Model Context Protocol](https://modelcontextprotocol.io/)**: MCP specification and tools

## 🚀 Production Deployment

### High Availability Setup
```bash
# Multi-provider redundancy
QX_MODEL_NAME=openrouter/openai/gpt-4o
QX_FALLBACK_MODELS=openrouter/anthropic/claude-3.5-sonnet,openrouter/google/gemini-1.5-pro

# Aggressive retry policy
QX_NUM_RETRIES=5
QX_REQUEST_TIMEOUT=120
QX_FALLBACK_TIMEOUT=60

# Enable circuit breaker
QX_CIRCUIT_BREAKER_ENABLED=true
QX_CIRCUIT_BREAKER_THRESHOLD=5
```

### Cost Optimization
```bash
# Start with cheaper models, fallback to premium
QX_MODEL_NAME=openrouter/meta-llama/llama-3.1-8b-instruct
QX_FALLBACK_MODELS=openrouter/openai/gpt-3.5-turbo,openrouter/openai/gpt-4o

# Conservative retry policy  
QX_NUM_RETRIES=2
QX_REQUEST_TIMEOUT=60
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests if applicable
5. Commit changes (`git commit -m 'Add amazing feature'`)
6. Push to branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **[LiteLLM](https://github.com/BerriAI/litellm)**: Unified LLM API interface
- **[Rich](https://github.com/Textualize/rich)**: Beautiful terminal formatting
- **[Pydantic](https://github.com/pydantic/pydantic)**: Data validation and serialization
- **[Model Context Protocol](https://modelcontextprotocol.io/)**: Extensible tool integration

---

**QX** - AI-Powered Coding Made Simple 🚀