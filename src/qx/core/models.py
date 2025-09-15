MODELS = (
    {
        "name": "gemini-2.5-pro",
        "model": "vertex_ai/gemini-2.5-pro",
        "description": "2.5 pro via Vertex AI",
        "accepts": ("thinking"),
        "max_input_tokens": 1048576,  # 1M tokens
        "max_output_tokens": 65535,  # 64K tokens
    },
    {
        "name": "gemini-2.5-flash",
        "model": "vertex_ai/gemini-2.5-flash",
        "description": "2.5 flash via Vertex AI",
        "accepts": ("thinking"),
        "max_input_tokens": 1048576,  # 1M tokens
        "max_output_tokens": 65535,  # 64K tokens
    },
    {
        "name": "gemini-2.5-flash-lite",
        "model": "vertex_ai/gemini-2.5-flash-lite",
        "description": "2.5 flash via Vertex AI",
        "max_input_tokens": 1_048_576,  # 1M tokens
        "max_output_tokens": 65535,  # 64K tokens
    },
    {
        "name": "gemini-2.0-flash",
        "model": "vertex_ai/gemini-2.0-flash-001",
        "description": "GA Gemini 2.0 flash via Vertex AI",
        "max_input_tokens": 1048576,  # 1M tokens
        "max_output_tokens": 8192,  # 8K tokens
    },
)
