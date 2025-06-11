"""
LangGraph supervisor system for qx multi-agent workflows.

This module integrates LangGraph with qx's existing agent system, using the
official langgraph-supervisor library for team coordination.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import MessagesState, StateGraph, Send
from langgraph_supervisor import create_supervisor

from qx.core.team_manager import get_team_manager, TeamManager, TeamMember
from qx.core.config_manager import ConfigManager
from qx.core.agent_manager import get_agent_manager
from qx.core.llm import QXLLMAgent
from qx.cli.theme import themed_console

logger = logging.getLogger(__name__)


class TaskState(MessagesState):
    """Extended state for task decomposition and parallel execution."""
    
    # Task decomposition
    main_task: str = ""
    subtasks: List[Dict[str, Any]] = []
    task_assignments: Dict[str, List[Dict[str, Any]]] = {}
    
    # Execution tracking
    agent_results: Dict[str, str] = {}
    completed_subtasks: List[str] = []
    
    # Agent execution state
    assigned_subtasks: List[Dict[str, Any]] = []
    current_agent: str = ""
    instance_id: str = ""
    
    # Workflow control
    can_parallelize: bool = False
    requires_synthesis: bool = False


class QxAgentWrapper:
    """Wrapper to make qx agents compatible with langgraph-supervisor."""
    
    def __init__(self, agent_name: str, team_member: TeamMember, config_manager: ConfigManager):
        self.name = agent_name
        self.team_member = team_member
        self.config_manager = config_manager
        self._llm_agent = None
        
    async def _get_llm_agent(self):
        """Lazy initialize the LLM agent."""
        if self._llm_agent is None:
            try:
                from qx.core.llm_utils import initialize_agent_with_mcp
                self._llm_agent = await initialize_agent_with_mcp(
                    self.config_manager.mcp_manager, 
                    self.team_member.agent_config
                )
            except Exception as e:
                logger.error(f"Failed to initialize LLM agent for {self.name}: {e}")
        return self._llm_agent
        
    async def invoke(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Invoke the agent with the given state."""
        llm_agent = await self._get_llm_agent()
        if not llm_agent:
            error_msg = f"Agent {self.name} is not available"
            return {
                "messages": [AIMessage(content=error_msg, name=self.name)]
            }
            
        try:
            # Extract user message from state
            messages = state.get("messages", [])
            if messages:
                last_message = messages[-1]
                if hasattr(last_message, 'content'):
                    user_input = last_message.content
                elif isinstance(last_message, dict):
                    user_input = last_message.get('content', '')
                else:
                    user_input = str(last_message)
            else:
                user_input = "Please help with the current task."
            
            # Show agent activation with BorderedMarkdown
            self._display_agent_activity(user_input)
            
            # Execute the agent
            result = await llm_agent.run(user_input, messages[:-1] if len(messages) > 1 else [])
            response = result.output if hasattr(result, 'output') else str(result)
            
            # Send result message
            self.team_member.send_message(f"Completed: {response[:100]}...")
            
            return {
                "messages": [AIMessage(content=response, name=self.name)]
            }
            
        except Exception as e:
            logger.error(f"Error in agent {self.name}: {e}", exc_info=True)
            error_msg = f"Error in {self.name}: {str(e)}"
            return {
                "messages": [AIMessage(content=error_msg, name=self.name)]
            }
    
    def _display_agent_activity(self, task_description: str):
        """Display agent activity using BorderedMarkdown with agent colors."""
        from qx.cli.quote_bar_component import render_agent_markdown, get_agent_color
        
        agent_color = self.team_member.agent_config.get('color')
        
        # Truncate long tasks for display
        display_task = task_description[:100] + "..." if len(task_description) > 100 else task_description
        
        markdown_content = f"Working on: {display_task}"
        
        # Use console manager for thread-safe output
        console_manager = self.team_member.console_manager
        if console_manager and hasattr(console_manager, 'console'):
            render_agent_markdown(
                markdown_content,
                self.name,  # This becomes the title automatically
                agent_color=agent_color,
                console=console_manager.console
            )
        else:
            # Fallback to direct rendering
            render_agent_markdown(
                markdown_content, 
                self.name,  # This becomes the title automatically
                agent_color=agent_color
            )

    # Add stream method for compatibility
    async def astream(self, state: Dict[str, Any]):
        """Stream method for compatibility."""
        result = await self.invoke(state)
        yield result


class LangGraphSupervisor:
    """Main supervisor class that orchestrates team workflows using langgraph-supervisor."""
    
    def __init__(self, config_manager: ConfigManager, main_llm_agent: QXLLMAgent):
        self.config_manager = config_manager
        self.main_llm_agent = main_llm_agent
        self.team_manager = get_team_manager(config_manager)
        self.supervisor_graph = None
        
    def _create_agent_wrapper(self, agent_name: str, team_member: TeamMember) -> QxAgentWrapper:
        """Create a wrapper for a qx agent."""
        return QxAgentWrapper(agent_name, team_member, self.config_manager)
    
    async def _build_supervisor(self):
        """Build the supervisor using langgraph-supervisor with existing qx agents."""
        try:
            team_members = self.team_manager.get_team_members()
            
            if not team_members:
                logger.warning("No team members available for supervisor")
                return
            
            # Create agent wrappers for each team member
            agent_wrappers = []
            for agent_name, team_member in team_members.items():
                wrapper = self._create_agent_wrapper(agent_name, team_member)
                agent_wrappers.append(wrapper)
                logger.info(f"Created agent wrapper for {agent_name}")
            
            if not agent_wrappers:
                logger.warning("No valid agent wrappers created for supervisor")
                return
            
            # Use the main LLM agent as the supervisor model
            # Since langgraph-supervisor needs a ChatModel, we'll create a minimal wrapper
            from qx.core.llm_utils import get_model_for_supervisor
            supervisor_model = await get_model_for_supervisor(self.main_llm_agent)
            
            # Create supervisor prompt
            supervisor_prompt = """You are a supervisor managing a team of specialized agents. 
            Your role is to analyze incoming tasks and delegate them to the most appropriate agent(s) on your team.
            
            Available agents:
            """
            for agent_name, team_member in team_members.items():
                supervisor_prompt += f"- {agent_name}: {team_member.agent_config.get('prompt', 'General purpose agent')}\n"
            
            supervisor_prompt += "\nAnalyze the task and delegate to the most suitable agent(s)."
            
            # For now, use a simplified approach - directly use existing LLM for delegation
            # The full langgraph-supervisor integration would require more complex model wrapping
            logger.info(f"Prepared supervisor with {len(agent_wrappers)} agent wrappers")
            self.supervisor_graph = None  # Will implement custom delegation logic
            
        except Exception as e:
            logger.error(f"Error building supervisor: {e}", exc_info=True)
            self.supervisor_graph = None
    
    async def rebuild_workflow(self):
        """Rebuild the supervisor when team composition changes."""
        await self._build_supervisor()
    
    async def should_use_team_workflow(self, user_input: str) -> bool:
        """Determine if the request should use the team workflow."""
        # Check if current agent can delegate
        if not getattr(self.main_llm_agent, 'can_delegate', False):
            return False
            
        if not self.team_manager.has_team():
            return False
        
        # Check if any team agents can handle this task
        suitable_agents = self.team_manager.select_best_agents_for_task(user_input)
        return len(suitable_agents) > 0
    
    async def decompose_task_node(self, state: TaskState) -> TaskState:
        """
        LangGraph node that decomposes user input into parallelizable subtasks.
        """
        try:
            # Extract user input from messages
            user_input = ""
            if state.get("messages"):
                last_message = state["messages"][-1]
                if hasattr(last_message, 'content'):
                    user_input = last_message.content
                elif isinstance(last_message, dict):
                    user_input = last_message.get('content', '')
            
            if not user_input:
                return {**state, "main_task": "No input provided", "can_parallelize": False}
            
            # Get available team members and their capabilities
            team_members = self.team_manager.get_team_members()
            agent_capabilities = {}
            for agent_name, member in team_members.items():
                specializations = []
                if hasattr(member.agent_config, 'specializations'):
                    specializations = member.agent_config.specializations
                elif hasattr(member.agent_config, '__dict__'):
                    specializations = getattr(member.agent_config, 'specializations', [])
                
                agent_capabilities[agent_name] = {
                    'description': getattr(member.agent_config, 'description', ''),
                    'specializations': specializations
                }
            
            decomposition_prompt = f"""
Analyze this user request and break it down into independent subtasks that can be assigned to specialized agents.

User Request: {user_input}

Available Agents and Their Capabilities:
{json.dumps(agent_capabilities, indent=2)}

Your task is to:
1. Identify if this request can be broken into smaller, independent subtasks
2. Create specific subtasks that match agent specializations
3. Determine if subtasks can run in parallel
4. Ensure each subtask is actionable and well-defined

Return your analysis in this JSON format:
{{
    "main_task": "Brief description of the overall objective",
    "can_parallelize": true/false,
    "subtasks": [
        {{
            "id": "subtask_1",
            "description": "Specific, actionable description of what needs to be done",
            "type": "category like 'analysis', 'implementation', 'documentation', 'testing'",
            "estimated_complexity": "low/medium/high",
            "required_capabilities": ["list", "of", "needed", "skills"]
        }}
    ]
}}

Guidelines:
- Only create subtasks if they add value through specialization
- Each subtask should be independently executable
- Avoid creating too many tiny subtasks (aim for 2-4 meaningful ones)
- If the task is simple, set can_parallelize to false and create only one subtask
- Match subtask types to available agent capabilities
"""

            # Use the main LLM agent to analyze and decompose the task
            result = await self.main_llm_agent.run(decomposition_prompt)
            response_text = result.output if hasattr(result, 'output') else str(result)
            
            # Extract JSON from the response
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                decomposition = json.loads(json_match.group())
                
                # Validate the structure
                required_keys = ['main_task', 'can_parallelize', 'subtasks']
                if all(key in decomposition for key in required_keys):
                    logger.info(f"Task decomposed into {len(decomposition['subtasks'])} subtasks")
                    
                    # Show decomposition to user
                    themed_console.print(
                        f"🧩 Task decomposed into {len(decomposition['subtasks'])} subtasks", 
                        style="dim cyan"
                    )
                    
                    return {
                        **state,
                        "main_task": decomposition["main_task"],
                        "subtasks": decomposition["subtasks"],
                        "can_parallelize": decomposition["can_parallelize"],
                        "requires_synthesis": len(decomposition["subtasks"]) > 1
                    }
                else:
                    logger.warning("Decomposition missing required keys, falling back to single task")
            else:
                logger.warning("Could not extract JSON from decomposition response")
                
        except Exception as e:
            logger.error(f"Error in task decomposition: {e}", exc_info=True)
        
        # Fallback: treat as single task
        return {
            **state,
            "main_task": user_input,
            "can_parallelize": False,
            "subtasks": [
                {
                    "id": "main_task",
                    "description": user_input,
                    "type": "general",
                    "estimated_complexity": "medium",
                    "required_capabilities": []
                }
            ],
            "requires_synthesis": False
        }
    
    def route_to_agents(self, state: TaskState, agent_node_mapping: Dict[str, List[str]]) -> List[Send]:
        """
        LangGraph routing function that assigns subtasks to appropriate agent instances.
        Returns Send objects for parallel execution with load balancing.
        """
        sends = []
        
        if not state.get("can_parallelize", False):
            # Route single task to best agent instance
            user_input = ""
            if state.get("messages"):
                last_message = state["messages"][-1]
                if hasattr(last_message, 'content'):
                    user_input = last_message.content
                elif isinstance(last_message, dict):
                    user_input = last_message.get('content', '')
            
            best_agents = self.team_manager.select_best_agents_for_task(user_input, max_agents=1)
            if best_agents:
                agent_name = best_agents[0]
                # Select least loaded instance (for now, just use first available)
                if agent_name in agent_node_mapping:
                    selected_node = agent_node_mapping[agent_name][0]
                    sends.append(Send(selected_node, state))
            
            return sends
        
        # Route subtasks to specialized agent instances with load balancing
        subtasks = state.get("subtasks", [])
        task_assignments = {}
        agent_instance_counters = {name: 0 for name in agent_node_mapping.keys()}
        
        for subtask in subtasks:
            # Find best agent type for this subtask
            best_agents = self.team_manager.select_best_agents_for_task(
                subtask["description"], max_agents=1
            )
            
            if best_agents:
                agent_name = best_agents[0]
                
                # Select instance using round-robin load balancing
                if agent_name in agent_node_mapping:
                    available_nodes = agent_node_mapping[agent_name]
                    instance_index = agent_instance_counters[agent_name] % len(available_nodes)
                    selected_node = available_nodes[instance_index]
                    agent_instance_counters[agent_name] += 1
                    
                    if selected_node not in task_assignments:
                        task_assignments[selected_node] = []
                    task_assignments[selected_node].append(subtask)
        
        # Create Send objects for each agent instance with their assigned subtasks
        for node_name, assigned_subtasks in task_assignments.items():
            # Extract agent name and instance from node name
            if node_name.startswith("agent_"):
                agent_info = node_name[6:]  # Remove "agent_" prefix
                if "_" in agent_info:
                    agent_name, instance_id = agent_info.rsplit("_", 1)
                else:
                    agent_name = agent_info
                    instance_id = "0"
            else:
                agent_name = "unknown"
                instance_id = "0"
            
            agent_state = {
                **state,
                "assigned_subtasks": assigned_subtasks,
                "current_agent": agent_name,
                "instance_id": instance_id
            }
            sends.append(Send(node_name, agent_state))
        
        # Update state with assignments
        state["task_assignments"] = task_assignments
        
        # If no agents assigned, route to main agent
        if not sends:
            sends.append(Send("agent_main", state))
        
        return sends
    
    async def agent_execution_node(self, state: TaskState, agent_name: str, instance_id: int = 0) -> TaskState:
        """
        LangGraph node that executes subtasks for a specific agent instance.
        """
        try:
            team_members = self.team_manager.get_team_members()
            
            # Create unique identifier for this agent instance
            agent_instance_key = f"{agent_name}_{instance_id}" if instance_id > 0 else agent_name
            
            # Handle main agent execution
            if agent_name == "main" or agent_name not in team_members:
                user_input = ""
                if state.get("messages"):
                    last_message = state["messages"][-1]
                    if hasattr(last_message, 'content'):
                        user_input = last_message.content
                    elif isinstance(last_message, dict):
                        user_input = last_message.get('content', '')
                
                result = await self.main_llm_agent.run(user_input)
                response = result.output if hasattr(result, 'output') else str(result)
                
                return {
                    **state,
                    "agent_results": {**state.get("agent_results", {}), "main": response},
                    "completed_subtasks": state.get("completed_subtasks", []) + ["main_task"]
                }
            
            # Handle specialized agent execution
            team_member = team_members[agent_name]
            wrapper = self._create_agent_wrapper(agent_name, team_member)
            
            # Get assigned subtasks for this agent instance
            assigned_subtasks = state.get("assigned_subtasks", [])
            
            if assigned_subtasks:
                # Process assigned subtasks
                subtask_results = []
                for subtask in assigned_subtasks:
                    # Show which instance is working on the task
                    if instance_id > 0:
                        themed_console.print(
                            f"🤖 {agent_name}#{instance_id} working on: {subtask['description'][:60]}...",
                            style="dim cyan"
                        )
                    else:
                        themed_console.print(
                            f"🤖 {agent_name} working on: {subtask['description'][:60]}...",
                            style="dim cyan"
                        )
                    
                    # Create focused state for this subtask
                    subtask_state = {
                        "messages": [HumanMessage(content=subtask["description"])]
                    }
                    
                    # Execute subtask
                    result = await wrapper.invoke(subtask_state)
                    if result and "messages" in result and result["messages"]:
                        subtask_results.append({
                            "subtask_id": subtask["id"],
                            "result": result["messages"][-1].content
                        })
                
                # Combine subtask results for this agent instance
                instance_label = f"{agent_name}#{instance_id}" if instance_id > 0 else agent_name
                combined_result = f"Agent {instance_label} completed {len(subtask_results)} subtasks:\n\n"
                for sr in subtask_results:
                    combined_result += f"Subtask {sr['subtask_id']}: {sr['result']}\n\n"
                
                return {
                    **state,
                    "agent_results": {**state.get("agent_results", {}), agent_instance_key: combined_result},
                    "completed_subtasks": state.get("completed_subtasks", []) + [st["id"] for st in assigned_subtasks]
                }
            else:
                # Fallback to original task
                user_input = ""
                if state.get("messages"):
                    last_message = state["messages"][-1]
                    if hasattr(last_message, 'content'):
                        user_input = last_message.content
                    elif isinstance(last_message, dict):
                        user_input = last_message.get('content', '')
                
                agent_state = {
                    "messages": [HumanMessage(content=user_input)]
                }
                
                result = await wrapper.invoke(agent_state)
                response = result["messages"][-1].content if result and "messages" in result and result["messages"] else "No response"
                
                return {
                    **state,
                    "agent_results": {**state.get("agent_results", {}), agent_instance_key: response},
                    "completed_subtasks": state.get("completed_subtasks", []) + ["main_task"]
                }
                
        except Exception as e:
            logger.error(f"Error in agent {agent_name}#{instance_id} execution: {e}", exc_info=True)
            error_result = f"Error in agent {agent_name}#{instance_id}: {str(e)}"
            
            return {
                **state,
                "agent_results": {**state.get("agent_results", {}), agent_instance_key: error_result},
                "completed_subtasks": state.get("completed_subtasks", [])
            }
    
    async def synthesis_node(self, state: TaskState) -> TaskState:
        """
        LangGraph node that synthesizes results from multiple agents into a unified response.
        """
        try:
            agent_results = state.get("agent_results", {})
            main_task = state.get("main_task", "")
            subtasks = state.get("subtasks", [])
            
            if not agent_results:
                return {**state, "messages": state.get("messages", []) + [AIMessage(content="No results to synthesize")]}
            
            # If only one result, return it directly
            if len(agent_results) == 1:
                result = list(agent_results.values())[0]
                return {**state, "messages": state.get("messages", []) + [AIMessage(content=result)]}
            
            # Synthesize multiple results
            synthesis_prompt = f"""
You are synthesizing results from multiple specialized agents who worked on different aspects of this task:

Main Task: {main_task}

Subtasks and Agent Results:
"""
            
            # Include subtask context for better synthesis
            for agent_name, result in agent_results.items():
                # Find which subtasks this agent worked on
                agent_subtasks = []
                task_assignments = state.get("task_assignments", {})
                if agent_name in task_assignments:
                    agent_subtasks = [st["description"] for st in task_assignments[agent_name]]
                
                synthesis_prompt += f"""
Agent: {agent_name}
Assigned Subtasks: {', '.join(agent_subtasks) if agent_subtasks else 'Main task'}
Result: {result}

---
"""
            
            synthesis_prompt += """
Your task is to synthesize these agent results into a comprehensive, unified response that:

1. Addresses the original main task completely
2. Integrates insights from all agents seamlessly
3. Eliminates redundancy while preserving important details
4. Maintains logical flow and coherence
5. Provides actionable conclusions or next steps

Create a well-structured response that feels like a single, cohesive analysis rather than separate agent outputs.
"""

            # Use main agent to synthesize
            result = await self.main_llm_agent.run(synthesis_prompt)
            synthesized_response = result.output if hasattr(result, 'output') else str(result)
            
            themed_console.print("🔗 Synthesizing agent results into unified response", style="dim cyan")
            
            return {
                **state, 
                "messages": state.get("messages", []) + [AIMessage(content=synthesized_response)]
            }
            
        except Exception as e:
            logger.error(f"Error in synthesis: {e}", exc_info=True)
            # Fallback: concatenate results
            agent_results = state.get("agent_results", {})
            fallback_response = "Results from team agents:\n\n"
            for agent_name, result in agent_results.items():
                fallback_response += f"**{agent_name}:**\n{result}\n\n"
            
            return {
                **state,
                "messages": state.get("messages", []) + [AIMessage(content=fallback_response)]
            }
    
    def _build_workflow_graph(self) -> StateGraph:
        """
        Build the LangGraph workflow for parallel task execution.
        """
        # Create workflow graph with custom TaskState
        workflow = StateGraph(TaskState)
        
        # Add decomposition node
        workflow.add_node("decompose", self.decompose_task_node)
        
        # Add synthesis node
        workflow.add_node("synthesize", self.synthesis_node)
        
        # Add agent execution nodes dynamically based on available team members and their instances
        team_members = self.team_manager.get_team_members()
        agent_node_mapping = {}
        
        for agent_name, team_member in team_members.items():
            instance_count = getattr(team_member, 'instance_count', 1)
            
            # Create multiple nodes for agents with multiple instances
            for instance_id in range(instance_count):
                node_name = f"agent_{agent_name}" if instance_count == 1 else f"agent_{agent_name}_{instance_id}"
                workflow.add_node(
                    node_name,
                    lambda state, name=agent_name, inst_id=instance_id: self.agent_execution_node(state, name, inst_id)
                )
                
                # Track all node names for this agent type
                if agent_name not in agent_node_mapping:
                    agent_node_mapping[agent_name] = []
                agent_node_mapping[agent_name].append(node_name)
        
        # Add main agent node as fallback
        workflow.add_node("agent_main", lambda state: self.agent_execution_node(state, "main"))
        
        # Set entry point
        workflow.set_entry_point("decompose")
        
        # Add conditional routing from decompose to agents
        # Create routing map for all agent nodes (including instances)
        routing_map = {"agent_main": "agent_main"}
        for agent_name, node_names in agent_node_mapping.items():
            for node_name in node_names:
                routing_map[node_name] = node_name
        
        workflow.add_conditional_edges(
            "decompose",
            lambda state: self.route_to_agents(state, agent_node_mapping),
            routing_map
        )
        
        # All agent nodes lead to synthesis
        for agent_name, node_names in agent_node_mapping.items():
            for node_name in node_names:
                workflow.add_edge(node_name, "synthesize")
        workflow.add_edge("agent_main", "synthesize")
        
        # Set finish point
        workflow.set_finish_point("synthesize")
        
        return workflow.compile()
    
    async def process_with_team(self, user_input: str) -> str:
        """Process a user request using the new LangGraph-based parallel team workflow."""
        try:
            team_members = self.team_manager.get_team_members()
            if not team_members:
                return "No team members available. Processing with main agent."
            
            # Show that we're using team workflow
            themed_console.print(
                f"🤖 Processing with team ({len(team_members)} agents available)...", 
                style="dim cyan"
            )
            
            # Build the workflow graph
            workflow = self._build_workflow_graph()
            
            # Create initial state
            initial_state = {
                "messages": [HumanMessage(content=user_input)],
                "main_task": "",
                "subtasks": [],
                "task_assignments": {},
                "agent_results": {},
                "completed_subtasks": [],
                "assigned_subtasks": [],
                "current_agent": "",
                "instance_id": "",
                "can_parallelize": False,
                "requires_synthesis": False
            }
            
            # Execute the workflow
            final_state = await workflow.ainvoke(initial_state)
            
            # Extract the final response
            if final_state.get("messages"):
                last_message = final_state["messages"][-1]
                if hasattr(last_message, 'content'):
                    return last_message.content
                elif isinstance(last_message, dict):
                    return last_message.get('content', 'No response generated')
            
            # Fallback if no proper response
            agent_results = final_state.get("agent_results", {})
            if agent_results:
                return "\n\n".join(agent_results.values())
            
            return "No response generated from team workflow"
            
        except Exception as e:
            logger.error(f"Error in LangGraph team workflow: {e}", exc_info=True)
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