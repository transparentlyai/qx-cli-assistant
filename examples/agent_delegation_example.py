#!/usr/bin/env python3
"""
Example demonstrating agent delegation using the invoke_agent_tool plugin.

This example shows how agents can delegate tasks to other specialized agents.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from qx.core.agent_invocation import AgentInvocationService  # noqa: E402


async def demonstrate_delegation():
    """Demonstrate agent delegation capabilities."""

    # Create agent invocation service
    service = AgentInvocationService()

    # Example 1: Direct invocation of CodeAnalyzer
    print("\n=== Example 1: Direct Code Analysis ===")
    response = await service.invoke_agent(
        agent_name="CodeAnalyzer",
        prompt="""Analyze the following Python code for quality issues:

```python
def process_data(data):
    result = []
    for i in range(len(data)):
        if data[i] > 0:
            result.append(data[i] * 2)
    return result
```""",
        timeout=30,
    )

    if response.success:
        print(f"CodeAnalyzer Response:\n{response.response}")
    else:
        print(f"Error: {response.error}")

    # Example 2: ProjectManager delegating to multiple agents
    print("\n\n=== Example 2: Project Manager Delegation ===")
    response = await service.invoke_agent(
        agent_name="ProjectManager",
        prompt="""I need help with a new Python project. Please:
1. Analyze the code quality of the invoke_agent_plugin.py file
2. Suggest improvements for better error handling
3. Create a summary report of findings""",
        timeout=60,
    )

    if response.success:
        print(f"ProjectManager Response:\n{response.response}")
    else:
        print(f"Error: {response.error}")

    # Example 3: Qx agent delegating specialized analysis
    print("\n\n=== Example 3: Qx Delegating Specialized Task ===")
    response = await service.invoke_agent(
        agent_name="Qx",
        prompt="""I'm working on the agent invocation plugin. 
Can you delegate a security analysis of the invoke_agent_plugin.py to the CodeAnalyzer agent?
Focus on potential security vulnerabilities in the agent invocation mechanism.""",
        timeout=60,
    )

    if response.success:
        print(f"Qx Response:\n{response.response}")
    else:
        print(f"Error: {response.error}")


async def list_available_agents():
    """List all available agents."""
    service = AgentInvocationService()
    agents = await service.list_available_agents()

    print("\n=== Available Agents ===")
    for agent in agents:
        info = await service.get_agent_info(agent)
        if info:
            can_delegate = info.get("can_delegate", False)
            description = info.get("description", "No description")
            print(f"- {agent}: {description}")
            print(f"  Can delegate: {can_delegate}")
            if info.get("tools"):
                print(f"  Tools: {', '.join(info['tools'][:5])}")
            print()


async def main():
    """Run the examples."""
    # Set a model if not already set
    if not os.environ.get("QX_MODEL_NAME"):
        os.environ["QX_MODEL_NAME"] = "openrouter/anthropic/claude-3.5-sonnet"

    # List available agents
    await list_available_agents()

    # Run delegation examples
    await demonstrate_delegation()


if __name__ == "__main__":
    asyncio.run(main())
