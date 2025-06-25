#!/usr/bin/env python3
"""
Example usage of the Agent Invocation Service.
Demonstrates how to programmatically call agents with prompts.
"""

import asyncio
import os
from pathlib import Path
import sys

# Add the src directory to the Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from qx.core.agent_invocation import AgentInvocationService, invoke_agent


async def simple_invocation_example():
    """Simple example of invoking an agent"""
    print("=== Simple Agent Invocation Example ===\n")
    
    # Invoke the default QX agent with a simple prompt
    response = await invoke_agent(
        agent_name="qx",
        prompt="What is the Python code to read a JSON file?",
        timeout=30
    )
    
    if response.success:
        print(f"Agent: {response.agent_name}")
        print(f"Prompt: {response.prompt}")
        print(f"Response:\n{response.response}")
        print(f"\nExecution time: {response.duration_seconds:.2f} seconds")
    else:
        print(f"Error: {response.error}")


async def batch_invocation_example():
    """Example of batch processing multiple prompts"""
    print("\n=== Batch Agent Invocation Example ===\n")
    
    service = AgentInvocationService()
    
    prompts = [
        "What is a Python list comprehension?",
        "How do I handle exceptions in Python?",
        "What is the difference between async and sync functions?"
    ]
    
    # Process multiple prompts concurrently
    responses = await service.invoke_agent_batch(
        agent_name="qx",
        prompts=prompts,
        timeout=30,
        max_concurrent=2
    )
    
    for i, response in enumerate(responses):
        print(f"\n--- Prompt {i+1} ---")
        print(f"Q: {response.prompt}")
        if response.success:
            print(f"A: {response.response[:200]}...")  # First 200 chars
        else:
            print(f"Error: {response.error}")


async def custom_context_example():
    """Example with custom context variables"""
    print("\n=== Custom Context Example ===\n")
    
    # Custom context for the agent
    context = {
        "user_context": "Senior Python developer working on web APIs",
        "project_context": "FastAPI web application with PostgreSQL",
        "project_files": "api/, models/, tests/",
        "ignore_paths": "__pycache__, .git"
    }
    
    response = await invoke_agent(
        agent_name="qx",
        prompt="How should I structure my API endpoints?",
        context=context,
        timeout=45
    )
    
    if response.success:
        print(f"Response with custom context:\n{response.response[:500]}...")
    else:
        print(f"Error: {response.error}")


async def agent_comparison_example():
    """Example comparing responses from different agents"""
    print("\n=== Agent Comparison Example ===\n")
    
    service = AgentInvocationService()
    
    # Check available agents
    available_agents = await service.list_available_agents()
    print(f"Available agents: {', '.join(available_agents)}\n")
    
    prompt = "Review this Python code for best practices: def add(a,b): return a+b"
    
    # Try with different agents if available
    agents_to_try = ["qx", "code_reviewer"]
    
    for agent_name in agents_to_try:
        if agent_name in available_agents:
            print(f"\n--- {agent_name} ---")
            response = await service.invoke_agent(
                agent_name=agent_name,
                prompt=prompt,
                timeout=30
            )
            
            if response.success:
                print(f"Response:\n{response.response[:300]}...")
            else:
                print(f"Error: {response.error}")
        else:
            print(f"\n--- {agent_name} ---")
            print(f"Agent '{agent_name}' not available")


async def message_history_example():
    """Example using message history for context"""
    print("\n=== Message History Example ===\n")
    
    service = AgentInvocationService()
    
    # First interaction
    response1 = await service.invoke_agent(
        agent_name="qx",
        prompt="I'm building a Python CLI tool. What's the best way to handle command-line arguments?",
        use_message_history=True
    )
    
    if response1.success:
        print("First response:", response1.response[:200], "...\n")
        
        # Follow-up using message history
        response2 = await service.invoke_agent(
            agent_name="qx",
            prompt="Can you show me a simple example using the approach you recommended?",
            use_message_history=True
        )
        
        if response2.success:
            print("Follow-up response:", response2.response[:300], "...")
        else:
            print(f"Follow-up error: {response2.error}")
    else:
        print(f"Initial error: {response1.error}")


async def main():
    """Run all examples"""
    try:
        await simple_invocation_example()
        await batch_invocation_example()
        await custom_context_example()
        await agent_comparison_example()
        await message_history_example()
        
    except KeyboardInterrupt:
        print("\n\nExamples interrupted by user")
    except Exception as e:
        print(f"\n\nError running examples: {e}")


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())