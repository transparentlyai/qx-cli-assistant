#!/usr/bin/env python3
"""Test if track_agent_execution is properly an async context manager."""

import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from qx.core.workflow_monitor import track_agent_execution
import inspect

async def test_context_manager():
    print(f"track_agent_execution type: {type(track_agent_execution)}")
    print(f"Is coroutine function: {inspect.iscoroutinefunction(track_agent_execution)}")
    print(f"Module: {track_agent_execution.__module__}")
    
    # Try to use it
    try:
        result = track_agent_execution("test_id", "test_agent", {})
        print(f"Result type when called: {type(result)}")
        
        # Check if it's an async context manager
        if hasattr(result, '__aenter__') and hasattr(result, '__aexit__'):
            print("✅ Has __aenter__ and __aexit__ methods")
            
            # Actually try to use it
            async with result as ctx:
                print(f"✅ Works as async context manager, context: {ctx}")
        else:
            print("❌ Missing async context manager methods")
            print(f"Methods: {[m for m in dir(result) if not m.startswith('_')]}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_context_manager())