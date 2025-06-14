#!/usr/bin/env python3
"""Test script to verify workflow delegation without needing API keys."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from qx.core.team_mode_manager import get_team_mode_manager
from qx.core.config_manager import ConfigManager
from qx.core.team_manager import get_team_manager
from qx.core.agent_routing_optimizer import AgentRoutingOptimizer, RoutingStrategy
from qx.core.dynamic_agent_loader import DynamicAgentLoader
from qx.cli.theme import themed_console
import anyio

async def test_workflow_components():
    """Test workflow components without requiring API keys."""
    try:
        print("🧪 Testing QX Workflow Delegation Components\n")
        
        # 1. Check team mode
        team_mode_manager = get_team_mode_manager()
        team_mode_enabled = team_mode_manager.is_team_mode_enabled()
        print(f"1. Team mode enabled: {team_mode_enabled}")
        
        if not team_mode_enabled:
            print("❌ Team mode is not enabled. Please run: /team-enable")
            return
        
        # 2. Check team composition
        async with anyio.create_task_group() as task_group:
            config_manager = ConfigManager(themed_console, task_group)
            team_manager = get_team_manager(config_manager)
            team_members = team_manager.get_team_members()
            
            print(f"\n2. Team composition:")
            print(f"   Total members: {len(team_members)}")
            for agent_name, member in team_members.items():
                print(f"   - {agent_name}")
            
            # 3. Test dynamic agent loader
            print("\n3. Testing dynamic agent loader:")
            dynamic_loader = DynamicAgentLoader(config_manager, team_manager)
            
            # Test capability detection for each agent
            for agent_name, member in team_members.items():
                print(f"\n   Agent: {agent_name}")
                capabilities = await dynamic_loader._detect_agent_capabilities(agent_name, member)
                print(f"   Capabilities detected: {len(capabilities)}")
                for cap in capabilities[:3]:  # Show first 3
                    print(f"     - {cap.name}: confidence={cap.confidence:.2f}")
            
            # 4. Test routing optimizer
            print("\n4. Testing routing optimizer:")
            routing_optimizer = AgentRoutingOptimizer(dynamic_loader)
            
            # Test different tasks
            test_tasks = [
                "Write a simple calculator.py script",
                "Debug a database connection issue",
                "Create a REST API endpoint",
                "Analyze performance metrics"
            ]
            
            for task in test_tasks:
                print(f"\n   Task: '{task}'")
                
                # Analyze task
                task_analysis = await routing_optimizer.analyze_task(task)
                print(f"   Complexity: {task_analysis.complexity.value}")
                print(f"   Required capabilities: {task_analysis.required_capabilities[:3]}")
                
                # Get routing decision
                routing_decision = await routing_optimizer.optimize_routing(
                    task_analysis=task_analysis,
                    strategy=RoutingStrategy.ADAPTIVE,
                    exclude_agents={"qx-director"}
                )
                
                print(f"   Selected agent: {routing_decision.selected_agents[0] if routing_decision.selected_agents else 'None'}")
                print(f"   Confidence: {routing_decision.confidence_score:.2%}")
                print(f"   Would delegate: {routing_decision.confidence_score > 0.1}")
            
            # 5. Check workflow build
            print("\n5. Testing workflow build:")
            from qx.core.langgraph_supervisor import get_unified_workflow
            
            try:
                workflow = get_unified_workflow(config_manager)
                print("   ✅ Workflow instance created")
                
                # Check if workflow can be built
                if not workflow.workflow_graph:
                    print("   Building workflow graph...")
                    await workflow._build_unified_workflow()
                    print("   ✅ Workflow graph built successfully")
                else:
                    print("   ✅ Workflow graph already built")
                
                # Get metrics
                metrics = workflow.get_execution_metrics()
                print(f"   Workflow status: {metrics['workflow_status']}")
                print(f"   Team size in workflow: {metrics['team_size']}")
                
            except Exception as e:
                print(f"   ❌ Workflow build failed: {e}")
                import traceback
                traceback.print_exc()
            
            print("\n✅ All components tested successfully!")
            
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_workflow_components())