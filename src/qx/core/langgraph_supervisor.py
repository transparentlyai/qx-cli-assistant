"""
LangGraph supervisor system for qx multi-agent workflows.

This module integrates LangGraph with qx's existing agent system, allowing qx
to act as a supervisor that coordinates team agents through a LangGraph workflow.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, TypedDict, Annotated
from pathlib import Path

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.graph.message import add_messages

from qx.core.team_manager import get_team_manager, TeamManager, TeamMember
from qx.core.config_manager import ConfigManager
from qx.core.agent_manager import get_agent_manager
from qx.core.llm import QXLLMAgent
from qx.cli.theme import themed_console

logger = logging.getLogger(__name__)


class TeamWorkflowState(TypedDict):
    """State for the team workflow graph."""
    messages: Annotated[List[BaseMessage], add_messages]
    current_task: str
    selected_agents: List[str] 
    agent_results: Dict[str, str]
    supervisor_decision: str
    next_agent: Optional[str]
    final_response: Optional[str]


class QxAgentNode:
    """Wrapper to make qx agents compatible with LangGraph nodes."""
    
    def __init__(self, agent_name: str, team_member: TeamMember, llm_agent: QXLLMAgent):
        self.agent_name = agent_name
        self.team_member = team_member
        self.llm_agent = llm_agent
        
    async def __call__(self, state: TeamWorkflowState) -> Dict[str, Any]:
        """Execute the agent node."""
        try:
            # Get the current task and any relevant context
            task = state.get("current_task", "")
            messages = state.get("messages", [])
            
            # Show progress
            self.team_member.show_progress(f"Working on: {task[:50]}...")
            
            # Build context for the agent
            context_messages = []
            if messages:
                # Include recent conversation context
                context_messages.extend(messages[-3:])  # Last 3 messages for context
            
            # Add the specific task
            task_message = HumanMessage(content=f"Task: {task}")
            context_messages.append(task_message)
            
            # Execute the agent
            result = await self.llm_agent.run(task, context_messages)
            response = result.output if hasattr(result, 'output') else str(result)
            
            # Send result message
            self.team_member.send_message(f"Completed task: {response[:100]}...")
            
            # Update state
            return {
                "agent_results": {**state.get("agent_results", {}), self.agent_name: response},
                "messages": [AIMessage(content=response, name=self.agent_name)]
            }
            
        except Exception as e:
            logger.error(f"Error in agent node {self.agent_name}: {e}", exc_info=True)
            error_msg = f"Error: {str(e)}"
            return {
                "agent_results": {**state.get("agent_results", {}), self.agent_name: error_msg},
                "messages": [AIMessage(content=error_msg, name=self.agent_name)]
            }


class SupervisorNode:
    """The supervisor node that coordinates team agents."""
    
    def __init__(self, team_manager: TeamManager, main_llm_agent: QXLLMAgent):
        self.team_manager = team_manager
        self.main_llm_agent = main_llm_agent
        
    async def __call__(self, state: TeamWorkflowState) -> Dict[str, Any]:
        """Supervisor decision logic."""
        try:
            task = state.get("current_task", "")
            agent_results = state.get("agent_results", {})
            
            # If no agents have worked on this yet, select agents
            if not agent_results:
                selected_agents = self.team_manager.select_best_agents_for_task(task, max_agents=2)
                
                if not selected_agents:
                    # No suitable team agents, handle directly
                    return {
                        "supervisor_decision": "handle_directly",
                        "next_agent": None,
                        "selected_agents": []
                    }
                
                # Select the best agent to start with
                return {
                    "supervisor_decision": "delegate",
                    "next_agent": selected_agents[0],
                    "selected_agents": selected_agents
                }
            
            # If we have results, decide what to do next
            selected_agents = state.get("selected_agents", [])
            completed_agents = set(agent_results.keys())
            remaining_agents = [agent for agent in selected_agents if agent not in completed_agents]
            
            if remaining_agents:
                # More agents to consult
                return {
                    "supervisor_decision": "delegate",
                    "next_agent": remaining_agents[0]
                }
            
            # All selected agents have completed, synthesize results
            return {
                "supervisor_decision": "synthesize",
                "next_agent": None
            }
            
        except Exception as e:
            logger.error(f"Error in supervisor node: {e}", exc_info=True)
            return {
                "supervisor_decision": "handle_directly",
                "next_agent": None
            }


class SynthesisNode:
    """Node that synthesizes results from multiple agents."""
    
    def __init__(self, main_llm_agent: QXLLMAgent):
        self.main_llm_agent = main_llm_agent
        
    async def __call__(self, state: TeamWorkflowState) -> Dict[str, Any]:
        """Synthesize agent results into final response."""
        try:
            task = state.get("current_task", "")
            agent_results = state.get("agent_results", {})
            
            if not agent_results:
                # No agent results to synthesize
                return {"final_response": "No agent results to synthesize."}
            
            # Build synthesis prompt
            synthesis_prompt = f"""
Task: {task}

Agent Results:
"""
            for agent_name, result in agent_results.items():
                synthesis_prompt += f"\n{agent_name}: {result}\n"
                
            synthesis_prompt += """
Please synthesize these agent results into a comprehensive, unified response that addresses the original task.
Focus on combining the insights and removing any redundancy.
"""
            
            # Generate synthesis
            result = await self.main_llm_agent.run(synthesis_prompt)
            final_response = result.output if hasattr(result, 'output') else str(result)
            
            return {
                "final_response": final_response,
                "messages": [AIMessage(content=final_response, name="qx_supervisor")]
            }
            
        except Exception as e:
            logger.error(f"Error in synthesis node: {e}", exc_info=True)
            return {"final_response": f"Error synthesizing results: {str(e)}"}


class LangGraphSupervisor:
    """Main supervisor class that orchestrates team workflows using LangGraph."""
    
    def __init__(self, config_manager: ConfigManager, main_llm_agent: QXLLMAgent):
        self.config_manager = config_manager
        self.main_llm_agent = main_llm_agent
        self.team_manager = get_team_manager(config_manager)
        self.workflow_graph: Optional[StateGraph] = None
        # Note: _build_workflow will be called asynchronously when needed
        
    async def _build_workflow(self):
        """Build the LangGraph workflow with current team composition."""
        try:
            # Create the state graph
            workflow = StateGraph(TeamWorkflowState)
            
            # Add supervisor node
            supervisor = SupervisorNode(self.team_manager, self.main_llm_agent)
            workflow.add_node("supervisor", supervisor)
            
            # Add synthesis node
            synthesis = SynthesisNode(self.main_llm_agent)
            workflow.add_node("synthesis", synthesis)
            
            # Add agent nodes for current team members
            team_members = self.team_manager.get_team_members()
            for agent_name, team_member in team_members.items():
                # Create LLM agent for this team member
                try:
                    from qx.core.llm_utils import initialize_agent_with_mcp
                    agent_llm = await initialize_agent_with_mcp(
                        self.config_manager.mcp_manager, 
                        team_member.agent_config
                    )
                    if agent_llm:
                        agent_node = QxAgentNode(agent_name, team_member, agent_llm)
                        workflow.add_node(agent_name, agent_node)
                except Exception as e:
                    logger.warning(f"Failed to create LLM agent for {agent_name}: {e}")
            
            # Set entry point
            workflow.set_entry_point("supervisor")
            
            # Add conditional edges from supervisor
            def route_supervisor_decision(state: TeamWorkflowState) -> str:
                decision = state.get("supervisor_decision", "handle_directly")
                next_agent = state.get("next_agent")
                
                if decision == "handle_directly":
                    return END
                elif decision == "delegate" and next_agent:
                    return next_agent
                elif decision == "synthesize":
                    return "synthesis"
                else:
                    return END
            
            workflow.add_conditional_edges(
                "supervisor",
                route_supervisor_decision,
                {agent_name: agent_name for agent_name in team_members.keys()} | 
                {"synthesis": "synthesis", END: END}
            )
            
            # Add edges from agent nodes back to supervisor
            for agent_name in team_members.keys():
                workflow.add_edge(agent_name, "supervisor")
            
            # Add edge from synthesis to end
            workflow.add_edge("synthesis", END)
            
            # Compile the workflow
            self.workflow_graph = workflow.compile()
            
            logger.info(f"Built LangGraph workflow with {len(team_members)} team members")
            
        except Exception as e:
            logger.error(f"Error building workflow: {e}", exc_info=True)
            self.workflow_graph = None
    
    async def rebuild_workflow(self):
        """Rebuild the workflow when team composition changes."""
        await self._build_workflow()
    
    async def should_use_team_workflow(self, user_input: str) -> bool:
        """Determine if the request should use the team workflow."""
        # Use team workflow if:
        # 1. User has team members
        # 2. The task could benefit from specialist agents
        
        if not self.team_manager.has_team():
            return False
            
        if not self.workflow_graph:
            # Try to build workflow if not already built
            await self._build_workflow()
            if not self.workflow_graph:
                return False
        
        # Check if any team agents can handle this task
        suitable_agents = self.team_manager.select_best_agents_for_task(user_input)
        return len(suitable_agents) > 0
    
    async def process_with_team(self, user_input: str) -> str:
        """Process a user request using the team workflow."""
        if not self.workflow_graph:
            return "Team workflow not available. Processing with main agent."
        
        try:
            # Create initial state
            initial_state = TeamWorkflowState(
                messages=[HumanMessage(content=user_input)],
                current_task=user_input,
                selected_agents=[],
                agent_results={},
                supervisor_decision="",
                next_agent=None,
                final_response=None
            )
            
            # Show that we're using team workflow
            team_members = self.team_manager.get_team_members()
            themed_console.print(
                f"🤖 Processing with team ({len(team_members)} agents available)...", 
                style="dim cyan"
            )
            
            # Execute the workflow
            result = await self.workflow_graph.ainvoke(initial_state)
            
            # Return the final response
            final_response = result.get("final_response")
            if final_response:
                return final_response
            
            # If no team agents handled it, fall back to supervisor decision
            supervisor_decision = result.get("supervisor_decision", "")
            if supervisor_decision == "handle_directly":
                themed_console.print("📝 No suitable team agents found, handling directly...", style="dim yellow")
                result = await self.main_llm_agent.run(user_input)
                return result.output if hasattr(result, 'output') else str(result)
            
            return "Team workflow completed but no final response generated."
            
        except Exception as e:
            logger.error(f"Error in team workflow: {e}", exc_info=True)
            themed_console.print(f"⚠️ Team workflow error, falling back to main agent...", style="warning")
            result = await self.main_llm_agent.run(user_input)
            return result.output if hasattr(result, 'output') else str(result)


# Global supervisor instance
_supervisor: Optional[LangGraphSupervisor] = None


def get_langgraph_supervisor(config_manager: ConfigManager, main_llm_agent: QXLLMAgent) -> LangGraphSupervisor:
    """Get the global LangGraph supervisor instance."""
    global _supervisor
    if _supervisor is None:
        _supervisor = LangGraphSupervisor(config_manager, main_llm_agent)
    return _supervisor


async def rebuild_supervisor_workflow():
    """Rebuild the supervisor workflow when team changes."""
    global _supervisor
    if _supervisor is not None:
        await _supervisor.rebuild_workflow()