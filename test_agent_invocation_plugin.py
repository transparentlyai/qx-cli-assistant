#!/usr/bin/env python3
"""
Test script for the agent invocation plugin.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from qx.plugins.invoke_agent_plugin import InvokeAgentPluginInput, invoke_agent_tool
from rich.console import Console


async def test_agent_invocation():
    """Test the agent invocation plugin."""
    console = Console()
    
    # Test 1: Try to invoke the default 'qx' agent
    console.print("\n[bold]Test 1: Invoking 'qx' agent[/bold]")
    args = InvokeAgentPluginInput(
        agent_name="qx",
        prompt="What is 2 + 2?",
        timeout=30
    )
    
    result = await invoke_agent_tool(console, args)
    console.print(f"Success: {result.success}")
    console.print(f"Response: {result.response[:100]}..." if len(result.response) > 100 else f"Response: {result.response}")
    if result.error:
        console.print(f"Error: {result.error}")
    
    # Test 2: Try to invoke a non-existent agent
    console.print("\n[bold]Test 2: Invoking non-existent agent[/bold]")
    args = InvokeAgentPluginInput(
        agent_name="non_existent_agent",
        prompt="Hello",
        timeout=10
    )
    
    result = await invoke_agent_tool(console, args)
    console.print(f"Success: {result.success}")
    console.print(f"Error: {result.error}")
    
    # Test 3: Test with context
    console.print("\n[bold]Test 3: Invoking with context[/bold]")
    args = InvokeAgentPluginInput(
        agent_name="qx",
        prompt="Tell me about the project context",
        context={"project_context": "This is a test project for agent invocation"},
        timeout=30
    )
    
    result = await invoke_agent_tool(console, args)
    console.print(f"Success: {result.success}")
    console.print(f"Response preview: {result.response[:200]}..." if len(result.response) > 200 else f"Response: {result.response}")


if __name__ == "__main__":
    asyncio.run(test_agent_invocation())