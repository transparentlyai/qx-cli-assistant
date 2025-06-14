#!/usr/bin/env python3
"""Test script to verify task delegation in team mode."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from qx.core.team_mode_manager import get_team_mode_manager
from qx.core.config_manager import ConfigManager
from qx.core.team_manager import get_team_manager
from qx.core.langgraph_supervisor import get_unified_workflow
from qx.cli.theme import themed_console
import anyio

async def test_delegation():
    """Test task delegation through unified workflow."""
    try:
        # Check team mode
        team_mode_manager = get_team_mode_manager()
        print(f"1. Team mode enabled: {team_mode_manager.is_team_mode_enabled()}")
        
        if not team_mode_manager.is_team_mode_enabled():
            print("❌ Team mode is not enabled. Please enable it first.")
            return
        
        # Create config manager
        async with anyio.create_task_group() as task_group:
            config_manager = ConfigManager(themed_console, task_group)
            
            # Check team
            team_manager = get_team_manager(config_manager)
            team_members = team_manager.get_team_members()
            print(f"\n2. Team members: {list(team_members.keys())}")
            
            # Get unified workflow
            workflow = get_unified_workflow(config_manager)
            
            # Test task
            test_task = "Write a simple Python calculator script at ./tmp/calculator.py"
            print(f"\n3. Testing delegation with task: {test_task}")
            
            # Check if workflow should be used
            should_use = await workflow.should_use_unified_workflow(test_task)
            print(f"   Should use workflow: {should_use}")
            
            if should_use:
                print("\n4. Processing with unified workflow...")
                try:
                    # Process the task
                    result = await workflow.process_with_unified_workflow(test_task)
                    print(f"\n5. Result received (length: {len(result)} chars)")
                    print("\n--- WORKFLOW RESULT ---")
                    print(result[:500] + "..." if len(result) > 500 else result)
                    print("--- END RESULT ---")
                    
                    # Check execution metrics
                    metrics = workflow.get_execution_metrics()
                    print(f"\n6. Execution metrics:")
                    print(f"   Total executions: {metrics['execution_metrics']['total_executions']}")
                    print(f"   Routing metrics: {metrics.get('routing_metrics', {})}")
                    
                except Exception as e:
                    print(f"\n❌ Workflow execution failed: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                print("❌ Workflow should be used but returned False")
            
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🧪 Testing QX Task Delegation\n")
    asyncio.run(test_delegation())