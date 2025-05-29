#!/bin/bash
# Clean test run

# Remove old log
rm -f ~/tmp/qx.log

# Set environment
export QX_LOG_LEVEL=DEBUG
export OPENROUTER_API_KEY="${OPENROUTER_API_KEY:-sk-test}"
export QX_MODEL_NAME="openai/gpt-3.5-turbo"

# Add project to Python path
export PYTHONPATH="/home/mauro/projects/qx/src:$PYTHONPATH"

# Run QX
cd /home/mauro/projects/qx
python -m qx.main