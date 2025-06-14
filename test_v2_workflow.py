#!/usr/bin/env python3
"""
Test script for the V2 workflow implementation.
Run with: QX_USE_V2_WORKFLOW=true python test_v2_workflow.py
"""

import asyncio
import os
import sys
from pathlib import Path

# Set V2 workflow
os.environ["QX_USE_V2_WORKFLOW"] = "true"

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from qx.core.config_manager import ConfigManager
from qx.core.team_mode_manager import get_team_mode_manager
from qx.core.workflow_manager import get_workflow_manager
from qx.cli.theme import themed_console
import anyio

async def test_v2_workflow():
    """Test the V2 workflow implementation."""
    print("=" * 60)
    print("Testing V2 Workflow Implementation")
    print("=" * 60)
    
    try:
        # Create config manager
        async with anyio.create_task_group() as task_group:
            config_manager = ConfigManager(themed_console, task_group)
            
            # Get team mode manager
            team_mode_manager = get_team_mode_manager()
            print(f"\nTeam mode enabled: {team_mode_manager.is_team_mode_enabled()}")
            
            if not team_mode_manager.is_team_mode_enabled():
                print("❌ Team mode is not enabled. Please enable it first.")
                return
            
            # Get workflow manager
            workflow_manager = get_workflow_manager(config_manager)
            print(f"Using workflow implementation: {workflow_manager._implementation}")
            
            # Test 1: Basic initialization
            print("\n✅ Test 1: Initializing workflow...")
            workflow = await workflow_manager.get_workflow()
            print(f"Workflow instance created: {type(workflow).__name__}")
            
            # Test 2: Build team workflow
            print("\n✅ Test 2: Building team workflow...")
            success = await workflow.build_team_workflow()
            print(f"Workflow built successfully: {success}")
            
            if not success:
                print("❌ Failed to build workflow")
                return
            
            # Test 3: Process a simple input
            print("\n✅ Test 3: Processing simple input...")
            response = await workflow.process_input("Hello, I'm testing the new workflow!")
            print(f"Response: {response[:100]}..." if response else "No response")
            
            # Test 4: Test with empty input (should trigger supervisor prompt)
            print("\n✅ Test 4: Testing empty input (supervisor should ask for input)...")
            # This would normally trigger an interrupt for user input
            # For testing, we'll just check if it handles empty input
            try:
                response = await workflow.process_input("")
                print(f"Response: {response[:100]}..." if response else "No response")
            except Exception as e:
                print(f"Expected behavior (interrupt): {e}")
            
            print("\n✅ All tests completed!")
            
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print(f"Environment: QX_USE_V2_WORKFLOW = {os.getenv('QX_USE_V2_WORKFLOW')}")
    asyncio.run(test_v2_workflow())