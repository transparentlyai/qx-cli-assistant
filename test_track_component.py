#!/usr/bin/env python3
"""Test the track_component function directly."""

import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from qx.core.workflow_monitor import get_workflow_monitor, ExecutionPhase

async def test_track_component():
    """Test if track_component works as async context manager."""
    monitor = get_workflow_monitor()
    
    print("Testing track_component...")
    try:
        # This should work if it's properly an async context manager
        async with monitor.track_component(
            "test_execution_123",
            "test_agent",
            ExecutionPhase.AGENT_EXECUTION,
            {"test": "data"}
        ) as component:
            print("✅ track_component works as async context manager")
            print(f"Component: {component}")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_track_component())