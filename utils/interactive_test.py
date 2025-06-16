#!/usr/bin/env python3
"""
Interactive test for the minimal 3-agent team.
Allows user to enter queries and see how the team responds.
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

async def test_interactive():
    """Interactive testing of team agents."""
    print("🎯 Interactive Team Mode Test")
    print("=" * 50)
    
    # Change to project root
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(project_root)
    print(f"📁 Working directory: {os.getcwd()}")
    
    try:
        import anyio
        from qx.core.config_manager import ConfigManager
        from qx.core.langgraph_supervisor import get_unified_workflow
        
        async with anyio.create_task_group() as tg:
            # Initialize
            config_manager = ConfigManager(None, parent_task_group=tg)
            config_manager.load_configurations()
            
            # Create and build workflow
            workflow = get_unified_workflow(config_manager)
            await workflow.build_team_workflow()
            print("✅ Team workflow ready!")
            
            print("\n📋 Available agents:")
            print("  - qx-director (supervisor)")
            print("  - code-writer (creates code files)")
            print("  - tester (runs and tests code)")
            
            # Interactive loop
            while True:
                print("\n💭 Enter your request (or 'quit' to exit):")
                user_query = input("> ").strip()
                
                if user_query.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye!")
                    break
                
                if not user_query:
                    print("❗ Please enter a request or 'quit' to exit")
                    continue
                
                try:
                    print(f"\n🔄 Processing: '{user_query}'...")
                    result = await workflow.process_input(user_query)
                    print(f"\n✅ Completed: {result}")
                except Exception as e:
                    print(f"\n❌ Error: {e}")
            
            return True
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_interactive())
    sys.exit(0 if success else 1)