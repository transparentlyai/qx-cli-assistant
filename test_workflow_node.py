#!/usr/bin/env python3
"""Test the workflow node execution pattern."""

import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from qx.core.workflow_monitor import track_agent_execution
from qx.core.workflow_debug_logger import get_debug_logger

async def simulate_specialist_node():
    """Simulate what happens in the specialist node."""
    execution_id = "test_execution_123"
    agent_name = "test_agent"
    
    debug_logger = get_debug_logger()
    
    print("Starting node simulation...")
    
    try:
        # This is the pattern used in the actual code
        async with track_agent_execution(execution_id, agent_name, {"task_description": "test task"}) as agent_execution:
            print(f"✅ Inside track_agent_execution context")
            
            # Use debug logger
            with debug_logger.log_node_execution(execution_id, agent_name, agent_name):
                print(f"✅ Inside log_node_execution context")
                
                # Simulate some work
                await asyncio.sleep(0.1)
                
                print("✅ Work completed successfully")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(simulate_specialist_node())