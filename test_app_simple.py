#!/usr/bin/env python3
"""
Simple test to run the app and debug issues
"""
import os
import sys

# Set environment variables
os.environ["QX_LOG_LEVEL"] = "DEBUG"
os.environ["OPENROUTER_API_KEY"] = os.environ.get("OPENROUTER_API_KEY", "sk-test-key")
os.environ["QX_MODEL_NAME"] = "openai/gpt-3.5-turbo"

# Add project to path
sys.path.insert(0, "/home/mauro/projects/qx/src")

# Run main
from qx.main import main

if __name__ == "__main__":
    print("Starting QX app...")
    main()
    print("QX app ended")