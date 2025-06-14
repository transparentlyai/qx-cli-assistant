#!/usr/bin/env python3
"""Test script to verify team mode routing fixes."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from qx.core.team_mode_manager import get_team_mode_manager
from qx.core.config_manager import ConfigManager
from qx.core.team_manager import get_team_manager
from qx.core.dynamic_agent_loader import DynamicAgentLoader
from qx.core.agent_routing_optimizer import AgentRoutingOptimizer, RoutingStrategy
from qx.cli.theme import themed_console
import anyio

async def test_routing_fix():
    """Test the routing fix for team mode."""
    try:
        # Check team mode
        team_mode_manager = get_team_mode_manager()
        print(f"1. Team mode enabled: {team_mode_manager.is_team_mode_enabled()}")
        
        # Create config manager
        async with anyio.create_task_group() as task_group:
            config_manager = ConfigManager(themed_console, task_group)
            
            # Check team manager
            team_manager = get_team_manager(config_manager)
            team_members = team_manager.get_team_members()
            print(f"\n2. Team members: {list(team_members.keys())}")
            print(f"   Team size: {len(team_members)}")
            print(f"   Has team: {team_manager.has_team()}")
            
            # Test capability detection
            print("\n3. Testing capability detection:")
            dynamic_loader = DynamicAgentLoader(config_manager, team_manager)
            
            for agent_name, team_member in team_members.items():
                if agent_name == "full_stack_swe":
                    capabilities = await dynamic_loader._detect_agent_capabilities(agent_name, team_member)
                    print(f"   Agent: {agent_name}")
                    print(f"   Detected capabilities:")
                    for cap in capabilities:
                        print(f"     - {cap.name}: {cap.description} (confidence: {cap.confidence:.2f})")
            
            # Test routing optimizer
            print("\n4. Testing routing optimizer:")
            routing_optimizer = AgentRoutingOptimizer(dynamic_loader)
            
            test_task = "Write a Python function to calculate fibonacci numbers"
            task_analysis = await routing_optimizer.analyze_task(test_task)
            print(f"   Task: {test_task}")
            print(f"   Complexity: {task_analysis.complexity.value}")
            print(f"   Required capabilities: {task_analysis.required_capabilities}")
            
            # Test routing decision
            routing_decision = await routing_optimizer.optimize_routing(
                task_analysis=task_analysis,
                strategy=RoutingStrategy.ADAPTIVE,
                exclude_agents={"qx-director"}
            )
            print(f"\n   Routing decision:")
            print(f"     Selected agents: {routing_decision.selected_agents}")
            print(f"     Confidence: {routing_decision.confidence_score:.2f}")
            print(f"     Reasoning: {routing_decision.reasoning}")
            
            # Test workflow condition
            print("\n5. Testing workflow condition:")
            print(f"   Team size >= 2: {len(team_members) >= 2}")
            print(f"   Should route to specialists: {len(team_members) >= 2 and routing_decision.selected_agents and routing_decision.confidence_score > 0.3}")
            
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_routing_fix())