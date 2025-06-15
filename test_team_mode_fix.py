#!/usr/bin/env python
"""Test script to verify team mode fix."""

import asyncio
import logging
import os
import sys

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(project_root, 'src'))

# Configure logging to file
log_file = '/home/mauro/tmp/qx_test.log'
os.makedirs(os.path.dirname(log_file), exist_ok=True)
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

async def test_team_mode():
    """Test the team mode implementation."""
    try:
        # Import required modules
        import anyio
        from qx.core.config_manager import ConfigManager
        from qx.core.langgraph_supervisor import get_unified_workflow
        from qx.core.team_mode_manager import get_team_mode_manager
        from qx.core.team_manager import get_team_manager
        
        print("🔧 Testing Team Mode Implementation...")
        
        # Create task group for ConfigManager
        async with anyio.create_task_group() as tg:
            # Create config manager
            config_manager = ConfigManager(None, parent_task_group=tg)
            config_manager.load_configurations()
        
            # Enable team mode
            team_mode_manager = get_team_mode_manager()
            team_mode_manager.set_team_mode_enabled(True, project_level=True)
            print("✅ Team mode enabled")
            
            # Get team manager and check team composition
            team_manager = get_team_manager(config_manager)
            team_status = team_manager.get_team_status()
            print(f"📋 Team members: {list(team_status['members'].keys())}")
            
            if not team_manager.has_team():
                print("⚠️  No team members found. Adding default team...")
                # Add qx-director and qx agent to team
                await team_manager.add_agent("qx-director")
                await team_manager.add_agent("qx")
                team_status = team_manager.get_team_status()
                print(f"📋 Updated team members: {list(team_status['members'].keys())}")
            
            # Create workflow
            workflow = get_unified_workflow(config_manager)
            print("🏗️  Building team workflow...")
            
            success = await workflow.build_team_workflow()
            if success:
                print("✅ Team workflow built successfully!")
                
                # Test processing a simple input
                print("\n🧪 Testing workflow execution...")
                response = await workflow.process_input("Hello, can you help me?")
                print(f"✅ Workflow executed. Response type: {type(response)}")
                
            else:
                print("❌ Failed to build team workflow")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_team_mode())