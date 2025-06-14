#!/usr/bin/env python3

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from qx.core.team_mode_manager import get_team_mode_manager
from qx.core.config_manager import ConfigManager
from qx.core.team_manager import get_team_manager
from qx.cli.theme import themed_console
import anyio

async def debug_team():
    try:
        # Check team mode
        team_mode_manager = get_team_mode_manager()
        print(f"Team mode enabled: {team_mode_manager.is_team_mode_enabled()}")
        
        # Create config manager
        async with anyio.create_task_group() as task_group:
            config_manager = ConfigManager(themed_console, task_group)
            
            # Check team manager
            team_manager = get_team_manager(config_manager)
            print(f"Team members: {team_manager.get_team_members()}")
            print(f"Has team: {team_manager.has_team()}")
            
            # Check if unified workflow should be used
            try:
                from qx.core.langgraph_supervisor import get_unified_workflow
                workflow = get_unified_workflow(config_manager)
                should_use = await workflow.should_use_unified_workflow("test message")
                print(f"Should use unified workflow: {should_use}")
            except Exception as workflow_error:
                print(f"Workflow test failed: {workflow_error}")
                import traceback
                traceback.print_exc()
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_team())