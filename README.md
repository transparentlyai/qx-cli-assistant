# QX - AI-Powered Coding CLI Agent

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

Create a configuration file at one of these locations (in order of priority):

1. `<project-directory>/.Q/qx.conf` (project-level, highest priority)
2. `~/.config/qx/qx.conf` (user-level)
3. `/etc/qx/qx.conf` (system-wide, lowest priority)

**Minimal Configuration:**
```bash
# Model Configuration (LiteLLM format)
QX_MODEL_NAME=openrouter/anthropic/claude-3.5-sonnet

# API Key (choose one based on your provider)
OPENROUTER_API_KEY=sk-or-v1-your_openrouter_api_key_here
# OPENAI_API_KEY=sk-your_openai_api_key_here
# ANTHROPIC_API_KEY=sk-ant-your_anthropic_api_key_here
```

For a complete configuration example with reliability features, see [`qx.conf.example`](qx.conf.example).

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

QX supports all LiteLLM providers including:

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

- **[`qx.conf.example`](qx.conf.example)**: Complete configuration reference
- **[`RELIABILITY.md`](RELIABILITY.md)**: Reliability and resilience guide  
- **[LiteLLM Docs](https://docs.litellm.ai/)**: Upstream LiteLLM documentation
- **[Plugin Development](#development--plugins)**: How to create custom tools

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