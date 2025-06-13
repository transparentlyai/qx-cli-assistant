# QX Model Providers Guide

## Overview

QX supports 100+ Large Language Models through [LiteLLM](https://docs.litellm.ai/), providing unified access to models from OpenAI, Anthropic, Google, Azure, local deployments, and more. This guide covers how to configure and use different model providers with QX.

## Table of Contents

- [Quick Start](#quick-start)
- [OpenRouter (Recommended)](#openrouter-recommended)
- [Direct Provider Access](#direct-provider-access)
- [Local Models](#local-models)
- [Model Selection Guide](#model-selection-guide)
- [Configuration Examples](#configuration-examples)
- [Cost Optimization](#cost-optimization)
- [Troubleshooting](#troubleshooting)

## Quick Start

### 1. Choose Your Provider

**For beginners**: Start with [OpenRouter](#openrouter-recommended) - single API key, access to all major models

**For enterprise**: Use [direct provider access](#direct-provider-access) for specific vendors

**For privacy**: Set up [local models](#local-models) with Ollama

### 2. Get API Key

Get your API key from your chosen provider (detailed instructions below)

### 3. Configure QX

Add to your configuration file (`~/.config/qx/qx.conf` or project `.Q/config/qx.conf`):

```bash
# Basic configuration
QX_MODEL_NAME=your_model_name
YOUR_PROVIDER_API_KEY=your_api_key_here
```

### 4. Test Configuration

```bash
uv run qx "Hello! Test my configuration."
```

## OpenRouter (Recommended)

OpenRouter provides access to multiple AI providers through a single API, making it the easiest way to get started with QX.

### Why OpenRouter?

- **Single API Key**: Access 100+ models from different providers
- **Unified Billing**: One bill for all model usage
- **Competitive Pricing**: Often cheaper than direct provider access
- **Model Comparison**: Easy to switch between models for testing
- **No Vendor Lock-in**: Switch providers without changing infrastructure

### Getting Started with OpenRouter

#### 1. Create Account

1. Visit [openrouter.ai](https://openrouter.ai)
2. Click "Sign Up" and create an account
3. Verify your email address

#### 2. Get API Key

1. Go to [openrouter.ai/keys](https://openrouter.ai/keys)
2. Click "Create Key"
3. Give it a descriptive name (e.g., "QX Development")
4. Copy the API key (starts with `sk-or-v1-`)

#### 3. Add Credits (Optional)

1. Go to [openrouter.ai/account](https://openrouter.ai/account)
2. Click "Add Credits"
3. Add $5-10 for testing (most models cost $0.001-0.01 per request)

#### 4. Configure QX

Add to your QX configuration:

```bash
# OpenRouter Configuration
OPENROUTER_API_KEY=sk-or-v1-your_api_key_here
QX_MODEL_NAME=openrouter/anthropic/claude-3.5-sonnet

# Optional: Set fallbacks
QX_FALLBACK_MODELS=openrouter/openai/gpt-4o,openrouter/google/gemini-1.5-pro
```

### Popular OpenRouter Models

#### **High Performance** (Premium)
```bash
# Anthropic Claude 3.5 Sonnet - Excellent for coding
QX_MODEL_NAME=openrouter/anthropic/claude-3.5-sonnet

# OpenAI GPT-4o - Great all-around model  
QX_MODEL_NAME=openrouter/openai/gpt-4o

# Google Gemini 1.5 Pro - Strong reasoning
QX_MODEL_NAME=openrouter/google/gemini-1.5-pro
```

#### **Cost-Effective** (Good Performance)
```bash
# OpenAI GPT-4o Mini - Fast and affordable
QX_MODEL_NAME=openrouter/openai/gpt-4o-mini

# Anthropic Claude 3 Haiku - Quick responses
QX_MODEL_NAME=openrouter/anthropic/claude-3-haiku

# Google Gemini 1.5 Flash - Balanced performance
QX_MODEL_NAME=openrouter/google/gemini-1.5-flash
```

#### **Budget-Friendly** (Basic Tasks)
```bash
# Meta Llama 3.1 8B - Open source
QX_MODEL_NAME=openrouter/meta-llama/llama-3.1-8b-instruct

# Mistral 7B - Efficient and capable
QX_MODEL_NAME=openrouter/mistralai/mistral-7b-instruct

# Qwen 2.5 7B - Good for coding
QX_MODEL_NAME=openrouter/qwen/qwen-2.5-7b-instruct
```

### OpenRouter Model Discovery

Find available models at [openrouter.ai/models](https://openrouter.ai/models) or use the format:
```
openrouter/provider/model-name
```

Examples:
- `openrouter/openai/gpt-4o`
- `openrouter/anthropic/claude-3.5-sonnet`
- `openrouter/google/gemini-1.5-pro`
- `openrouter/meta-llama/llama-3.1-70b-instruct`

## Direct Provider Access

For enterprise use or specific provider features, you can connect directly to model providers.

### OpenAI

Direct access to OpenAI's latest models and features.

#### Getting OpenAI API Key

1. Visit [platform.openai.com](https://platform.openai.com)
2. Sign up or log in to your account
3. Go to [API Keys](https://platform.openai.com/api-keys)
4. Click "Create new secret key"
5. Copy the key (starts with `sk-`)

#### Configuration

```bash
# OpenAI Direct Configuration
OPENAI_API_KEY=sk-your_openai_api_key_here
QX_MODEL_NAME=gpt-4o

# Alternative models
# QX_MODEL_NAME=gpt-4o-mini          # Faster, cheaper
# QX_MODEL_NAME=gpt-4                # Previous generation
# QX_MODEL_NAME=gpt-3.5-turbo       # Most affordable
```

#### OpenAI Model Options

```bash
# Latest and greatest
QX_MODEL_NAME=gpt-4o                 # Best overall performance
QX_MODEL_NAME=gpt-4o-mini            # Cost-effective option

# Reasoning models (slower but more thoughtful)
QX_MODEL_NAME=o1-preview             # Advanced reasoning
QX_MODEL_NAME=o1-mini                # Faster reasoning

# Legacy (still capable)
QX_MODEL_NAME=gpt-4                  # Previous flagship
QX_MODEL_NAME=gpt-3.5-turbo          # Budget option
```

### Anthropic

Direct access to Claude models with latest features.

#### Getting Anthropic API Key

1. Visit [console.anthropic.com](https://console.anthropic.com)
2. Sign up for an account
3. Go to [API Keys](https://console.anthropic.com/settings/keys)
4. Click "Create Key"
5. Copy the key (starts with `sk-ant-`)

#### Configuration

```bash
# Anthropic Direct Configuration
ANTHROPIC_API_KEY=sk-ant-your_anthropic_api_key_here
QX_MODEL_NAME=claude-3-5-sonnet-20241022

# Alternative models
# QX_MODEL_NAME=claude-3-5-haiku-20241022   # Faster, cheaper
# QX_MODEL_NAME=claude-3-opus-20240229      # Previous flagship
```

#### Anthropic Model Options

```bash
# Latest models (recommended)
QX_MODEL_NAME=claude-3-5-sonnet-20241022    # Best for coding
QX_MODEL_NAME=claude-3-5-haiku-20241022     # Fast and efficient

# Previous generation
QX_MODEL_NAME=claude-3-opus-20240229        # Most capable legacy model
QX_MODEL_NAME=claude-3-sonnet-20240229      # Balanced legacy option
QX_MODEL_NAME=claude-3-haiku-20240307       # Budget legacy option
```

### Google (Gemini)

Access to Google's Gemini models.

#### Getting Google API Key

1. Visit [Google AI Studio](https://aistudio.google.com)
2. Sign in with your Google account
3. Click "Get API Key"
4. Create a new API key or use existing one
5. Copy the API key

#### Configuration

```bash
# Google Direct Configuration
GOOGLE_API_KEY=your_google_api_key_here
QX_MODEL_NAME=gemini-1.5-pro

# Alternative models
# QX_MODEL_NAME=gemini-1.5-flash        # Faster, cheaper
# QX_MODEL_NAME=gemini-1.0-pro          # Previous generation
```

#### Google Model Options

```bash
# Latest models
QX_MODEL_NAME=gemini-1.5-pro             # Best performance
QX_MODEL_NAME=gemini-1.5-flash           # Fast and efficient

# Previous generation
QX_MODEL_NAME=gemini-1.0-pro             # Legacy option
```

### Azure OpenAI

Enterprise-grade OpenAI models through Microsoft Azure.

#### Getting Azure OpenAI Access

1. Apply for Azure OpenAI Service access at [aka.ms/oai/access](https://aka.ms/oai/access)
2. Once approved, create an Azure OpenAI resource in the Azure portal
3. Deploy a model (e.g., GPT-4)
4. Get your endpoint and API key from the Azure portal

#### Configuration

```bash
# Azure OpenAI Configuration
AZURE_API_KEY=your_azure_api_key_here
AZURE_API_BASE=https://your-resource.openai.azure.com/
AZURE_API_VERSION=2023-12-01-preview
QX_MODEL_NAME=azure/your-deployment-name

# Example with specific deployment
QX_MODEL_NAME=azure/gpt-4o-deployment
```

### AWS Bedrock

Access AI models through Amazon Web Services.

#### Configuration

```bash
# AWS Bedrock Configuration
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION_NAME=us-east-1

# Model examples
QX_MODEL_NAME=bedrock/anthropic.claude-3-sonnet-20240229-v1:0
# QX_MODEL_NAME=bedrock/amazon.titan-text-express-v1
# QX_MODEL_NAME=bedrock/ai21.j2-ultra-v1
```

## Local Models

Run models locally for privacy, cost control, or offline usage.

### Ollama (Recommended for Local)

Ollama makes it easy to run local models on your machine.

#### Installing Ollama

**macOS/Linux:**
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

**Windows:**
Download from [ollama.ai](https://ollama.ai)

#### Setting Up Local Models

```bash
# Install popular models
ollama pull llama3.2           # Meta's Llama 3.2 (3B)
ollama pull llama3.1           # Meta's Llama 3.1 (8B)  
ollama pull codellama          # Code-specialized model
ollama pull mistral            # Mistral 7B
ollama pull qwen2.5-coder      # Qwen code model

# Start Ollama service
ollama serve
```

#### QX Configuration for Ollama

```bash
# Ollama Configuration (no API key needed)
QX_MODEL_NAME=ollama/llama3.2

# Other local models
# QX_MODEL_NAME=ollama/llama3.1
# QX_MODEL_NAME=ollama/codellama
# QX_MODEL_NAME=ollama/mistral
# QX_MODEL_NAME=ollama/qwen2.5-coder
```

### Other Local Options

#### vLLM (Advanced)

For high-performance local deployment:

```bash
# Install vLLM
pip install vllm

# Start vLLM server
python -m vllm.entrypoints.openai.api_server \
  --model microsoft/DialoGPT-medium \
  --port 8000

# Configure QX
QX_MODEL_NAME=openai/microsoft/DialoGPT-medium
OPENAI_API_BASE=http://localhost:8000/v1
OPENAI_API_KEY=dummy
```

#### Hugging Face Transformers

Direct model loading (requires significant RAM):

```bash
# Configure for local Hugging Face model
QX_MODEL_NAME=huggingface/microsoft/DialoGPT-medium
```

## Model Selection Guide

### By Use Case

#### **Coding & Development**
1. **claude-3-5-sonnet** - Best overall for code
2. **gpt-4o** - Strong coding capabilities
3. **qwen2.5-coder** - Specialized code model (local)
4. **codellama** - Code-focused (local)

#### **General Chat & Assistance**
1. **gpt-4o** - Excellent all-around
2. **claude-3-5-sonnet** - Great reasoning
3. **gemini-1.5-pro** - Strong performance
4. **llama3.1** - Good local option

#### **Fast Responses**
1. **gpt-4o-mini** - OpenAI's fast model
2. **claude-3-haiku** - Anthropic's speed model
3. **gemini-1.5-flash** - Google's fast model
4. **llama3.2** - Quick local model

#### **Cost-Sensitive**
1. **gpt-4o-mini** - Best price/performance
2. **claude-3-haiku** - Affordable and capable
3. **llama models** - Free local options
4. **mistral-7b** - Budget-friendly

#### **Privacy/Offline**
1. **ollama/llama3.1** - Capable local model
2. **ollama/qwen2.5-coder** - For coding tasks
3. **ollama/mistral** - Efficient local option

### By Performance Tier

#### **Tier 1: Premium** ($0.01-0.06 per 1K tokens)
- claude-3-5-sonnet
- gpt-4o
- gemini-1.5-pro
- gpt-4

#### **Tier 2: Balanced** ($0.001-0.01 per 1K tokens)
- gpt-4o-mini
- claude-3-haiku
- gemini-1.5-flash
- gpt-3.5-turbo

#### **Tier 3: Budget** ($0.0001-0.001 per 1K tokens)
- llama-3.1-8b (via OpenRouter)
- mistral-7b
- qwen-2.5-7b

#### **Tier 4: Free** (Local)
- ollama/llama3.1
- ollama/mistral
- ollama/qwen2.5-coder

## Configuration Examples

### Single Model Setup

```bash
# Simple OpenRouter configuration
OPENROUTER_API_KEY=sk-or-v1-your_key_here
QX_MODEL_NAME=openrouter/anthropic/claude-3.5-sonnet
QX_MODEL_TEMPERATURE=0.7
QX_MODEL_MAX_TOKENS=4096
```

### Multi-Model Fallback

```bash
# Robust setup with fallbacks
QX_MODEL_NAME=openrouter/anthropic/claude-3.5-sonnet
QX_FALLBACK_MODELS=openrouter/openai/gpt-4o,openrouter/google/gemini-1.5-pro

# Multiple providers for redundancy
OPENROUTER_API_KEY=sk-or-v1-your_openrouter_key
OPENAI_API_KEY=sk-your_openai_key
```

### Cost-Optimized Setup

```bash
# Start cheap, fallback to premium if needed
QX_MODEL_NAME=openrouter/openai/gpt-4o-mini
QX_FALLBACK_MODELS=openrouter/anthropic/claude-3.5-sonnet,openrouter/openai/gpt-4o

# Conservative retry policy to control costs
QX_NUM_RETRIES=2
QX_REQUEST_TIMEOUT=30
```

### Privacy-First Setup

```bash
# Local-only configuration
QX_MODEL_NAME=ollama/llama3.1
# No API keys needed for local models

# Backup local models
QX_FALLBACK_MODELS=ollama/mistral,ollama/qwen2.5-coder
```

### Enterprise Setup

```bash
# Azure OpenAI for compliance
AZURE_API_KEY=your_azure_key
AZURE_API_BASE=https://your-resource.openai.azure.com/
QX_MODEL_NAME=azure/gpt-4o-deployment

# Aggressive retry policy for reliability
QX_NUM_RETRIES=5
QX_REQUEST_TIMEOUT=120
QX_FALLBACK_TIMEOUT=60
```

### Development vs Production

#### Development Configuration
```bash
# ~/.config/qx/qx.conf (personal development)
OPENROUTER_API_KEY=sk-or-v1-dev_key
QX_MODEL_NAME=openrouter/openai/gpt-4o-mini  # Cheaper for testing
QX_LOG_LEVEL=DEBUG
QX_ENABLE_STREAMING=true
```

#### Production Configuration
```bash
# /etc/qx/qx.conf (team/production)
OPENROUTER_API_KEY=sk-or-v1-prod_key
QX_MODEL_NAME=openrouter/anthropic/claude-3.5-sonnet  # High performance
QX_FALLBACK_MODELS=openrouter/openai/gpt-4o
QX_NUM_RETRIES=3
QX_REQUEST_TIMEOUT=60
```

## Cost Optimization

### Strategies

#### 1. **Tier-Based Approach**
```bash
# Start with cheaper models, escalate if needed
QX_MODEL_NAME=openrouter/openai/gpt-4o-mini
QX_FALLBACK_MODELS=openrouter/anthropic/claude-3.5-sonnet
```

#### 2. **Context Window Management**
```bash
# Use smaller context windows to reduce costs
QX_MODEL_MAX_TOKENS=2048          # Reduce output tokens
QX_CONTEXT_WINDOW_TARGET=8192     # Smaller input context
```

#### 3. **Selective Model Usage**
```bash
# Different models for different tasks
# Coding tasks: premium models
# Simple queries: budget models
```

#### 4. **Local Development**
```bash
# Use local models for development
QX_MODEL_NAME=ollama/llama3.1

# Switch to cloud for production
# QX_MODEL_NAME=openrouter/anthropic/claude-3.5-sonnet
```

### Cost Monitoring

Track usage through provider dashboards:

- **OpenRouter**: [openrouter.ai/activity](https://openrouter.ai/activity)
- **OpenAI**: [platform.openai.com/usage](https://platform.openai.com/usage)
- **Anthropic**: [console.anthropic.com/dashboard](https://console.anthropic.com/dashboard)

### Budget Controls

Set spending limits:

```bash
# Conservative retry policy
QX_NUM_RETRIES=2
QX_REQUEST_TIMEOUT=30

# Smaller token limits
QX_MODEL_MAX_TOKENS=1024
```

## Troubleshooting

### Common Issues

#### 1. **API Key Not Working**

**Symptoms**: `AuthenticationError` or `Invalid API key`

**Solutions**:
```bash
# Check key format
echo $OPENROUTER_API_KEY  # Should start with sk-or-v1-
echo $OPENAI_API_KEY      # Should start with sk-

# Verify key is active
curl -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  https://openrouter.ai/api/v1/models

# Check configuration loading
QX_LOG_LEVEL=DEBUG uv run qx --version
```

#### 2. **Model Not Found**

**Symptoms**: `Model not found` or `Invalid model name`

**Solutions**:
```bash
# Check model name format
# Correct: openrouter/anthropic/claude-3.5-sonnet
# Wrong: claude-3.5-sonnet

# List available models
curl -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  https://openrouter.ai/api/v1/models | jq '.data[].id'

# Test with known working model
QX_MODEL_NAME=openrouter/openai/gpt-4o-mini uv run qx "test"
```

#### 3. **Rate Limiting**

**Symptoms**: `Rate limit exceeded` or `Too many requests`

**Solutions**:
```bash
# Increase retry delay
QX_RETRY_DELAY=2.0
QX_BACKOFF_FACTOR=3.0

# Reduce request frequency
QX_REQUEST_TIMEOUT=60

# Use multiple providers
QX_FALLBACK_MODELS=different_provider_model
```

#### 4. **Timeout Issues**

**Symptoms**: `Request timeout` or slow responses

**Solutions**:
```bash
# Increase timeout
QX_REQUEST_TIMEOUT=120

# Use faster models
QX_MODEL_NAME=openrouter/openai/gpt-4o-mini

# Enable fallbacks
QX_FALLBACK_MODELS=fast_backup_model
```

#### 5. **Local Model Issues**

**Symptoms**: Connection errors with local models

**Solutions**:
```bash
# Check Ollama is running
ollama list
curl http://localhost:11434/api/tags

# Restart Ollama
ollama serve

# Verify model is pulled
ollama pull llama3.1
```

### Debug Mode

Enable debug logging to troubleshoot issues:

```bash
QX_LOG_LEVEL=DEBUG uv run qx "debug test"
```

This will show:
- Configuration loading process
- API request details
- Model selection logic
- Error details and stack traces

### Testing Configuration

Verify your setup works:

```bash
# Test basic functionality
uv run qx "Say hello in one word"

# Test with specific model
QX_MODEL_NAME=openrouter/openai/gpt-4o-mini uv run qx "Quick test"

# Test fallback system
QX_MODEL_NAME=invalid_model_name \
QX_FALLBACK_MODELS=openrouter/openai/gpt-4o-mini \
uv run qx "Fallback test"
```

### Performance Optimization

#### For Speed
```bash
# Fast models
QX_MODEL_NAME=openrouter/openai/gpt-4o-mini
QX_MODEL_NAME=openrouter/anthropic/claude-3-haiku

# Reduce context
QX_MODEL_MAX_TOKENS=1024

# Enable streaming
QX_ENABLE_STREAMING=true
```

#### For Quality
```bash
# Premium models
QX_MODEL_NAME=openrouter/anthropic/claude-3.5-sonnet
QX_MODEL_NAME=openrouter/openai/gpt-4o

# Higher temperature for creativity
QX_MODEL_TEMPERATURE=0.8

# More context
QX_MODEL_MAX_TOKENS=4096
```

## Advanced Configuration

### Model-Specific Parameters

```bash
# Reasoning models (OpenAI o1 series)
QX_MODEL_NAME=openrouter/openai/o1-preview
QX_MODEL_REASONING_EFFORT=high  # none, low, medium, high

# Temperature control
QX_MODEL_TEMPERATURE=0.3        # More focused (0.0-2.0)
QX_MODEL_TEMPERATURE=1.0        # More creative

# Token limits
QX_MODEL_MAX_TOKENS=4096        # Response length limit
```

### Provider-Specific Features

#### OpenRouter Features
```bash
# Site and app name for OpenRouter analytics
OPENROUTER_HTTP_REFERER=https://yoursite.com
OPENROUTER_X_TITLE=YourApp

# Model preferences
QX_MODEL_NAME=openrouter/anthropic/claude-3.5-sonnet:beta
```

#### OpenAI Features
```bash
# Function calling
QX_OPENAI_PARALLEL_TOOL_CALLS=true

# Response format (for compatible models)
QX_OPENAI_RESPONSE_FORMAT=json_object
```

### Environment-Specific Configuration

#### CI/CD Environment
```bash
# Non-interactive mode
QX_AUTO_APPROVE=true
QX_ENABLE_STREAMING=false

# Timeout for automated environments
QX_REQUEST_TIMEOUT=30
QX_NUM_RETRIES=1
```

#### Development Environment
```bash
# Verbose logging
QX_LOG_LEVEL=DEBUG
QX_SHOW_SPINNER=true

# Cost-effective model
QX_MODEL_NAME=openrouter/openai/gpt-4o-mini
```

## Getting Help

### Support Resources

- **QX Documentation**: Check other docs in this repository
- **LiteLLM Docs**: [docs.litellm.ai](https://docs.litellm.ai/)
- **OpenRouter Support**: [openrouter.ai/docs](https://openrouter.ai/docs)
- **Provider Documentation**: Check specific provider docs for advanced features

### Community

- **GitHub Issues**: Report bugs or request features
- **Provider Communities**: Join provider-specific communities for model-specific help

---

This guide should help you configure QX with any supported model provider. For the most up-to-date information on available models and pricing, check the provider documentation directly.