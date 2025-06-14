#!/usr/bin/env python3
"""Debug script to understand why tasks aren't being delegated to specialist agents."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from qx.core.team_mode_manager import get_team_mode_manager
from qx.core.config_manager import ConfigManager
from qx.core.team_manager import get_team_manager
from qx.cli.theme import themed_console
from qx.core.agent_routing_optimizer import AgentRoutingOptimizer, RoutingStrategy, TaskComplexity
from qx.core.dynamic_agent_loader import DynamicAgentLoader
import anyio

async def debug_routing():
    try:
        # Check team mode
        team_mode_manager = get_team_mode_manager()
        print(f"\n=== TEAM MODE DEBUG ===")
        print(f"Team mode enabled: {team_mode_manager.is_team_mode_enabled()}")
        
        # Create config manager
        async with anyio.create_task_group() as task_group:
            config_manager = ConfigManager(themed_console, task_group)
            
            # Check team manager
            team_manager = get_team_manager(config_manager)
            team_members = team_manager.get_team_members()
            print(f"\n=== TEAM MEMBERS ===")
            for name, member in team_members.items():
                print(f"- {name}: {member.agent_config.name if member.agent_config else 'No config'}")
            print(f"Has team: {team_manager.has_team()}")
            print(f"Team size: {len(team_members)}")
            
            # Test the routing optimizer
            print(f"\n=== ROUTING OPTIMIZER TEST ===")
            dynamic_loader = DynamicAgentLoader(config_manager, team_manager)
            routing_optimizer = AgentRoutingOptimizer(dynamic_loader)
            
            # Test task analysis
            test_tasks = [
                "Write a Python script to analyze data",
                "Create a React component for a dashboard",
                "Build a full-stack web application",
                "Read a file and show its contents",
                "Debug this code issue"
            ]
            
            for task in test_tasks:
                print(f"\n--- Testing task: '{task}' ---")
                
                # Analyze task
                task_analysis = await routing_optimizer.analyze_task(task)
                print(f"Task complexity: {task_analysis.complexity.value}")
                print(f"Required capabilities: {task_analysis.required_capabilities}")
                print(f"Requires collaboration: {task_analysis.requires_collaboration}")
                
                # Test routing with different strategies
                for strategy in [RoutingStrategy.ADAPTIVE, RoutingStrategy.BEST_MATCH]:
                    print(f"\nStrategy: {strategy.value}")
                    routing_decision = await routing_optimizer.optimize_routing(
                        task_analysis=task_analysis,
                        strategy=strategy,
                        exclude_agents={"qx-director"}
                    )
                    
                    print(f"Selected agents: {routing_decision.selected_agents}")
                    print(f"Confidence score: {routing_decision.confidence_score:.2f}")
                    print(f"Reasoning: {routing_decision.reasoning}")
                    print(f"Alternatives: {routing_decision.alternatives[:3]}")
            
            # Test the workflow routing logic
            print(f"\n=== WORKFLOW ROUTING LOGIC TEST ===")
            from qx.core.langgraph_supervisor import get_unified_workflow
            workflow = get_unified_workflow(config_manager)
            
            # Check if workflow can be built
            print("Building workflow...")
            await workflow._build_unified_workflow()
            print(f"Workflow built: {workflow.workflow_graph is not None}")
            
            # Test the routing condition with different states
            test_states = [
                {
                    "workflow_stage": "routing",
                    "user_input": "Write a Python script",
                    "selected_agent": "",
                },
                {
                    "workflow_stage": "specialist_execution",
                    "selected_agent": "full_stack_swe",
                },
                {
                    "workflow_stage": "direct_response",
                    "selected_agent": "",
                }
            ]
            
            for i, state in enumerate(test_states):
                print(f"\nTest state {i+1}:")
                print(f"  Stage: {state['workflow_stage']}")
                print(f"  Selected agent: {state.get('selected_agent', 'none')}")
                route = workflow._route_from_director(state)
                print(f"  Route decision: {route}")
                
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Set a dummy API key to avoid initialization errors
    import os
    os.environ['OPENROUTER_API_KEY'] = 'dummy-key-for-testing'
    
    asyncio.run(debug_routing())