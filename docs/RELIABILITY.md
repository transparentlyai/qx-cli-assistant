# QX Reliability & Resilience Features

QX includes comprehensive reliability features powered by LiteLLM to ensure robust and fault-tolerant LLM interactions.

## 🎯 Overview

The reliability system provides multiple layers of fault tolerance:

1. **Automatic Retries** - Retry failed requests with exponential backoff
2. **Model Fallbacks** - Switch to backup models if primary fails  
3. **Context Window Fallbacks** - Auto-scale to larger context models when needed
4. **Multi-Provider Redundancy** - Use multiple API keys/endpoints
5. **Circuit Breaker** - Prevent cascade failures
6. **Intelligent Timeouts** - Configurable timeout handling

## 🔧 Configuration Variables

### Retry Configuration
```bash
QX_NUM_RETRIES=3              # Number of retry attempts for failed requests  
QX_RETRY_DELAY=1.0            # Base delay between retries in seconds
QX_MAX_RETRY_DELAY=60.0       # Maximum delay between retries
QX_BACKOFF_FACTOR=2.0         # Exponential backoff multiplier
```

### Timeout Settings
```bash
QX_REQUEST_TIMEOUT=120        # Individual request timeout (seconds)
QX_CONNECT_TIMEOUT=30         # Connection timeout (seconds) 
QX_READ_TIMEOUT=300           # Read timeout for streaming (seconds)
QX_FALLBACK_TIMEOUT=45        # Total timeout for fallback attempts (seconds)
```

### Model Fallbacks
```bash
# Comma-separated list of backup models
QX_FALLBACK_MODELS=openrouter/openai/gpt-4o,openrouter/anthropic/claude-3.5-sonnet,openrouter/google/gemini-1.5-pro

# Cooldown period for rate-limited models
QX_FALLBACK_COOLDOWN=60       # Seconds to wait before retrying rate-limited model
```

### Context Window Fallbacks
```bash
# JSON mapping for automatic context window scaling
QX_CONTEXT_WINDOW_FALLBACKS={"gpt-3.5-turbo":"gpt-3.5-turbo-16k","gpt-4":"gpt-4-32k","claude-3-haiku":"claude-3-sonnet"}
```

### Multi-Provider Redundancy
```bash
# Backup API keys (JSON format)
QX_FALLBACK_API_KEYS={"openai":["sk-backup1","sk-backup2"],"anthropic":["sk-ant-backup1"]}

# Backup API endpoints (JSON format)
QX_FALLBACK_API_BASES={"azure":[{"api_key":"key1","api_base":"https://backup1.azure.com"},{"api_key":"key2","api_base":"https://backup2.azure.com"}]}
```

### Circuit Breaker
```bash
QX_CIRCUIT_BREAKER_ENABLED=true
QX_CIRCUIT_BREAKER_THRESHOLD=5    # Number of failures before opening circuit
QX_CIRCUIT_BREAKER_TIMEOUT=300    # Circuit breaker timeout in seconds
```

## 📋 Configuration Examples

### High Availability Setup
```bash
# Primary model with multiple fallbacks
QX_MODEL_NAME=openrouter/openai/gpt-4o
QX_FALLBACK_MODELS=openrouter/anthropic/claude-3.5-sonnet,openrouter/google/gemini-1.5-pro,openrouter/meta-llama/llama-3.1-405b-instruct

# Aggressive retry policy
QX_NUM_RETRIES=5
QX_REQUEST_TIMEOUT=120
QX_FALLBACK_TIMEOUT=60
QX_RETRY_DELAY=2.0
QX_BACKOFF_FACTOR=1.5
```

### Cost-Optimized with Fallbacks
```bash
# Start with cheaper model, fallback to premium
QX_MODEL_NAME=openrouter/meta-llama/llama-3.1-8b-instruct  
QX_FALLBACK_MODELS=openrouter/openai/gpt-3.5-turbo,openrouter/openai/gpt-4o-mini

# Conservative retry policy
QX_NUM_RETRIES=2
QX_REQUEST_TIMEOUT=60
QX_FALLBACK_TIMEOUT=30
```

### Context Window Auto-Scaling
```bash
# Automatically scale context window when needed
QX_MODEL_NAME=gpt-3.5-turbo
QX_CONTEXT_WINDOW_FALLBACKS={"gpt-3.5-turbo":"gpt-3.5-turbo-16k","gpt-4":"gpt-4-32k"}

# Allow more time for larger context processing
QX_REQUEST_TIMEOUT=180
QX_FALLBACK_TIMEOUT=90
```

### Multi-Region Azure Setup
```bash
# Primary Azure deployment with regional fallbacks
QX_MODEL_NAME=azure/gpt-4
QX_FALLBACK_API_BASES={"azure":[
  {"api_key":"eastus_key","api_base":"https://eastus.openai.azure.com"},
  {"api_key":"westus_key","api_base":"https://westus.openai.azure.com"},
  {"api_key":"europe_key","api_base":"https://europe.openai.azure.com"}
]}

# Quick failover between regions
QX_NUM_RETRIES=1
QX_REQUEST_TIMEOUT=45
QX_FALLBACK_TIMEOUT=30
```

## 🧪 Testing Reliability

Use the provided test script to verify your reliability configuration:

```bash
python test_reliability.py
```

This will:
- ✅ Load and validate all reliability settings
- ✅ Test agent initialization with fallback models
- ✅ Verify timeout and retry configurations  
- ✅ Display comprehensive configuration summary

## 🔍 Monitoring & Debugging

### Enable Debug Logging
```bash
QX_LOG_LEVEL=DEBUG
```

This provides detailed logs about:
- Which models are being attempted
- Fallback triggers and reasons
- Retry attempts and delays
- Timeout events
- Circuit breaker state changes

### Log Examples
```
DEBUG: Making LiteLLM call with model: openrouter/openai/gpt-4o
DEBUG: Fallback models configured: ['openrouter/anthropic/claude-3.5-sonnet', 'openrouter/google/gemini-1.5-pro']
DEBUG: Retries: 3
DEBUG: Timeout: 120
ERROR: LiteLLM API call failed (RateLimitError): Rate limit exceeded
DEBUG: Fallback models were available: ['openrouter/anthropic/claude-3.5-sonnet', 'openrouter/google/gemini-1.5-pro']
```

## 🚀 Benefits

### 1. **Increased Uptime**
- Automatic failover between models/providers
- Intelligent retry logic with exponential backoff
- Circuit breaker prevents cascade failures

### 2. **Cost Optimization** 
- Start with cheaper models, fallback to premium
- Context window auto-scaling prevents unnecessary costs
- Rate limit handling with cooldown periods

### 3. **Performance Resilience**
- Multiple timeout layers (connect, read, total)
- Parallel provider redundancy
- Smart cooldown for rate-limited endpoints

### 4. **Developer Experience**
- Zero-code reliability - just configure environment variables
- Comprehensive logging and monitoring
- Easy testing and validation

## 🎛️ Best Practices

1. **Start Conservative**: Begin with 2-3 retries and moderate timeouts
2. **Layer Fallbacks**: Use different provider types (OpenRouter → Direct → Local)
3. **Monitor Costs**: Fallbacks can increase usage - monitor spending
4. **Test Configurations**: Use the test script to validate setups
5. **Log Strategically**: Enable debug logging only when needed
6. **Regional Diversity**: Use multiple regions for cloud providers

## 🔗 Related Documentation

- [LiteLLM Reliability Docs](https://docs.litellm.ai/docs/completion/reliable_completions)
- [QX Configuration Guide](qx.conf.example)
- [LiteLLM Provider List](https://docs.litellm.ai/docs/providers)

---

*QX Reliability features are powered by [LiteLLM](https://github.com/BerriAI/litellm) - a unified interface for 100+ LLM providers.*