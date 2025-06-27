#!/usr/bin/env python
"""Test script to diagnose VertexAI retry mechanism issue with streaming."""

import asyncio
import os
import litellm
from litellm import RateLimitError, acompletion

# Enable debug logging
litellm.set_verbose = True
litellm._turn_on_debug()

# Configure litellm settings
litellm.num_retries = 3
litellm.request_timeout = 120

async def test_vertex_retry_streaming():
    """Test VertexAI with retry mechanism for streaming."""
    
    # Test configuration
    model = os.environ.get("QX_MODEL", "vertex_ai/gemini-1.5-flash")
    
    print(f"Testing model: {model}")
    print(f"LiteLLM version: {litellm.__version__}")
    print(f"Retry settings: num_retries={litellm.num_retries}")
    print()
    
    # Simple test message
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Say hello in one word."}
    ]
    
    # Custom retry logic (similar to QX implementation)
    max_retries = 3
    base_delay = 2.0
    
    for attempt in range(max_retries + 1):
        try:
            print(f"Attempt {attempt + 1} (streaming)...")
            response = await acompletion(
                model=model,
                messages=messages,
                temperature=0.7,
                max_tokens=10,
                stream=True  # Enable streaming
            )
            
            # Process stream
            full_response = ""
            async for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    print(content, end="", flush=True)
            
            print(f"\nSuccess! Full response: {full_response}")
            return full_response
            
        except RateLimitError as e:
            if attempt < max_retries:
                delay = base_delay * (attempt + 1)
                print(f"\nRateLimitError caught: {e}")
                print(f"Retrying in {delay} seconds...")
                await asyncio.sleep(delay)
            else:
                print(f"\nAll retries exhausted. Final error: {e}")
                raise
                
        except Exception as e:
            print(f"\nUnexpected error type: {type(e).__name__}")
            print(f"Error details: {e}")
            
            # Check if it's actually a 429 error
            if hasattr(e, 'response') and hasattr(e.response, 'status_code'):
                print(f"Status code: {e.response.status_code}")
            
            # Check error string for 429
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                print("This looks like a rate limit error but wasn't caught as RateLimitError!")
                
                # Manual retry for 429 errors not caught as RateLimitError
                if attempt < max_retries:
                    delay = base_delay * (attempt + 1)
                    print(f"Manually retrying in {delay} seconds...")
                    await asyncio.sleep(delay)
                    continue
            
            raise

if __name__ == "__main__":
    # Run the test
    print("Testing streaming with retry mechanism...")
    asyncio.run(test_vertex_retry_streaming())