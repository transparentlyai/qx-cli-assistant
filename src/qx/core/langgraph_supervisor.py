"""
LangGraph supervisor system for qx multi-agent workflows.

This module implements a two-layer agent architecture:

1. USER LAYER:
   - qx-director: User-facing coordinator agent (outside team graph)
   - Can be manually selected with `qx -a qx-director` or `/agents switch qx-director`
   - Provides strategic planning, architecture, and high-level coordination
   - Acts as the main agent when explicitly chosen by user

2. SYSTEM LAYER (Team Graph):
   - task_delegator.system.agent: Internal delegation engine (inside team graph)
   - Used automatically by LangGraph supervisor for task routing
   - Pure delegation without explanation or planning
   - Routes tasks to specialist agents (full_stack_swe, data_analyst, etc.)

ARCHITECTURAL FLOW:
User Request → qx-director (if selected) → Task Delegator → Specialist Agents
            OR
User Request → Task Delegator (if team mode enabled) → Specialist Agents

This module integrates LangGraph with qx's existing agent system, using the
official langgraph-supervisor library for team coordination.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import MessagesState, StateGraph
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.store.memory import InMemoryStore

# Handle Send import - may not be available in all LangGraph versions
try:
    from langgraph.graph import Send
except ImportError:
    # Fallback for older versions or different import path
    try:
        from langgraph.types import Send
    except ImportError:
        # Create a simple Send fallback if not available
        from dataclasses import dataclass
        from typing import Any
        
        @dataclass
        class Send:
            node: str
            arg: Any
from langgraph_supervisor import create_supervisor
from langgraph.prebuilt import create_react_agent

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
    task_completed: bool = False
    execution_count: int = 0


class QxAgentWrapper:
    """
    Wrapper to make qx agents compatible with langgraph-supervisor.
    
    This adapter allows QX's native agents to work within the LangGraph team graph
    system by providing the interface expected by langgraph-supervisor while
    preserving QX's console management, tool integration, and agent behavior.
    """
    
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
            
            # Execute the agent with proper console context
            # Use the same execution pattern as the main agent in llm.py
            from qx.core.llm import query_llm
            from qx.cli.theme import themed_console
            
            # Execute using the same infrastructure as main agent
            result = await query_llm(
                llm_agent,
                user_input,
                message_history=messages[:-1] if len(messages) > 1 else [],
                console=themed_console,
                config_manager=self.config_manager
            )
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
    """
    Main supervisor class that orchestrates team workflows using langgraph-supervisor.
    
    This class implements the SYSTEM LAYER of the two-layer architecture:
    - Manages the LangGraph team graph with specialist agents
    - Uses task_delegator.system.agent for internal task routing
    - Handles parallel execution and result synthesis
    - Provides fallback mechanisms when team coordination fails
    
    Note: This is NOT the user-facing qx-director agent, but rather the internal
    team coordination system that works behind the scenes.
    """
    
    def __init__(self, config_manager: ConfigManager, main_llm_agent: QXLLMAgent):
        self.config_manager = config_manager
        self.main_llm_agent = main_llm_agent
        self.team_manager = get_team_manager(config_manager)
        self.supervisor_graph = None
        
        # Configuration options with backward-compatible defaults
        self.supervisor_timeout = 300.0  # 5 minutes timeout (preserves current behavior)
        self.debug_mode = False  # Enhanced debug logging disabled by default
        self.output_mode = "last_message"  # Preserves current default
        self.add_handoff_messages = True  # Preserves current setting
        self.memory_type = "in_memory"  # Current default behavior
        self.supervisor_name = "qx_task_delegator"  # Current setting
        
        # Load configuration overrides if available (fully backward compatible)
        self._load_configuration_overrides()
        
    def _load_configuration_overrides(self):
        """
        Load configuration overrides from environment or config files.
        Fully backward compatible - only overrides if explicitly set.
        """
        try:
            # Load from environment variables (safe defaults)
            import os
            
            # Timeout configuration
            env_timeout = os.environ.get('QX_SUPERVISOR_TIMEOUT')
            if env_timeout:
                try:
                    self.supervisor_timeout = float(env_timeout)
                    logger.debug(f"Using supervisor timeout from environment: {self.supervisor_timeout}s")
                except ValueError:
                    logger.warning(f"Invalid supervisor timeout value: {env_timeout}, using default")
            
            # Debug mode configuration
            env_debug = os.environ.get('QX_SUPERVISOR_DEBUG_MODE', '').lower()
            if env_debug in ('true', '1', 'yes', 'on'):
                self.debug_mode = True
                logger.debug("Enhanced debug mode enabled via environment variable")
            
            # Output mode configuration
            env_output_mode = os.environ.get('QX_SUPERVISOR_OUTPUT_MODE')
            if env_output_mode in ('last_message', 'full_history'):
                self.output_mode = env_output_mode
                logger.debug(f"Using output mode from environment: {self.output_mode}")
            
            # Memory type configuration
            env_memory_type = os.environ.get('QX_SUPERVISOR_MEMORY_TYPE')
            if env_memory_type in ('in_memory', 'persistent'):
                self.memory_type = env_memory_type
                logger.debug(f"Using memory type from environment: {self.memory_type}")
                
        except Exception as e:
            logger.debug(f"Error loading configuration overrides (using defaults): {e}")
            logger.debug(f"Configuration error details - timeout: {self.supervisor_timeout}, "
                        f"debug_mode: {self.debug_mode}, output_mode: {self.output_mode}")
            logger.debug("All configuration errors are non-fatal - using safe defaults")
            # Continue with defaults - no impact on functionality
    
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
            logger.debug("Entering decompose_task_node")
            themed_console.print("🔄 Decomposing task...", style="dim yellow")
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
            
            # Use Task Decomposer system agent
            try:
                from qx.core.agent_loader import AgentLoader
                from qx.core.llm_utils import initialize_agent_with_mcp
                import os
                
                agent_loader = AgentLoader()
                decomposer_config = agent_loader.get_agent_config("Task Decomposer", cwd=os.getcwd())
                
                if decomposer_config:
                    # Create the task decomposer agent
                    decomposer_agent = await initialize_agent_with_mcp(
                        self.config_manager.mcp_manager,
                        decomposer_config
                    )
                    
                    # Format the context for the decomposer
                    formatted_prompt = decomposer_config.context.format(
                        user_input=user_input,
                        agent_capabilities=json.dumps(agent_capabilities, indent=2)
                    )
                    
                    # Use the decomposer agent to analyze the task
                    result = await decomposer_agent.run(formatted_prompt)
                    response_text = result.output if hasattr(result, 'output') else str(result)
                else:
                    raise Exception("Task Decomposer system agent not found")
                    
            except Exception as e:
                logger.warning(f"Could not use Task Decomposer system agent: {e}")
                # Fallback to main agent with inline prompt
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
            logger.debug(f"Entering agent_execution_node for {agent_name}")
            themed_console.print(f"🤖 Executing with {agent_name}...", style="dim cyan")
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
        
        # Add memory saver for state persistence
        memory = MemorySaver()
        return workflow.compile(checkpointer=memory)
    
    async def process_with_team(self, user_input: str, message_history: Optional[List] = None) -> str:
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
            
            # Try the proper supervisor pattern first
            try:
                return await self.process_with_proper_supervisor(user_input, message_history)
            except Exception as e:
                logger.warning(f"Proper supervisor failed, using fallback: {e}")
                themed_console.print(f"⚠️ Supervisor pattern failed, using direct delegation...", style="yellow")
            
            # FALLBACK: Use simplified direct delegation
            suitable_agents = self.team_manager.select_best_agents_for_task(user_input)
            if suitable_agents:
                best_agent_name = suitable_agents[0]
                themed_console.print(f"🎯 Delegating to {best_agent_name}...", style="dim green")
                
                team_member = team_members[best_agent_name]
                wrapper = self._create_agent_wrapper(best_agent_name, team_member)
                
                # Create state for direct execution
                state = {"messages": [HumanMessage(content=user_input)]}
                
                # Add timeout to prevent hanging
                try:
                    result = await asyncio.wait_for(wrapper.invoke(state), timeout=300.0)  # 5 minutes
                except asyncio.TimeoutError:
                    themed_console.print("⚠️ Agent execution timed out, falling back to supervisor", style="yellow")
                    result = await self.main_llm_agent.run(user_input)
                    return result.output if hasattr(result, 'output') else str(result)
                
                if result and "messages" in result and result["messages"]:
                    return result["messages"][-1].content
                else:
                    return "Task completed successfully"
            
            # Fallback: Build the workflow graph (original complex approach)
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
                "requires_synthesis": False,
                "task_completed": False,
                "execution_count": 0
            }
            
            # Execute the workflow with state persistence
            import uuid
            thread_id = str(uuid.uuid4())
            config = {"configurable": {"thread_id": thread_id}}
            final_state = await workflow.ainvoke(initial_state, config=config)
            
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
    
    async def process_with_proper_supervisor(self, user_input: str, message_history: Optional[List] = None) -> str:
        """
        Process using the proper langgraph-supervisor library approach.
        
        This method implements the SYSTEM LAYER delegation:
        1. Creates LangChain-compatible react agents from QX team members
        2. Uses task_delegator.system.agent as the internal delegation engine
        3. Creates handoff tools (delegate_to_[agent_name]) for routing
        4. Executes tasks through the LangGraph supervisor pattern
        
        This is the internal team coordination system, not user-facing coordination.
        """
        try:
            team_members = self.team_manager.get_team_members()
            if not team_members:
                result = await self.main_llm_agent.run(user_input)
                return result.output if hasattr(result, 'output') else str(result)
            
            themed_console.print(f"🎯 Using proper supervisor pattern...", style="dim green")
            
            # Create react agents for each team member
            logger.debug(f"Creating react agents for {len(team_members)} team members")
            react_agents = []
            for agent_name, team_member in team_members.items():
                logger.debug(f"Creating react agent for {agent_name}")
                try:
                    # Convert QX agent to LangGraph react agent
                    from qx.core.llm_utils import initialize_agent_with_mcp
                    llm_agent = await initialize_agent_with_mcp(
                        self.config_manager.mcp_manager, 
                        team_member.agent_config
                    )
                    
                    # Create a LangChain-compatible LLM wrapper for the agent
                    def create_langchain_llm_wrapper(qx_agent):
                        """Create a minimal LangChain-compatible LLM wrapper"""
                        from langchain_core.language_models.base import BaseLanguageModel
                        from langchain_core.messages import AIMessage
                        
                        from langchain_core.runnables import Runnable
                        
                        class QXLLMWrapper(Runnable):
                            def __init__(self, qx_agent):
                                self.qx_agent = qx_agent
                            
                            def invoke(self, input, config=None, **kwargs):
                                if isinstance(input, str):
                                    content = input
                                elif hasattr(input, 'content'):
                                    content = input.content
                                elif isinstance(input, list) and len(input) > 0:
                                    # Handle list of messages
                                    last_msg = input[-1]
                                    content = getattr(last_msg, 'content', str(last_msg))
                                else:
                                    content = str(input)
                                
                                import asyncio
                                result = asyncio.run(self.qx_agent.run(content))
                                response_text = result.output if hasattr(result, 'output') else str(result)
                                return AIMessage(content=response_text)
                            
                            def bind_tools(self, tools, **kwargs):
                                # Store tools for later use
                                logger.debug(f"Agent {self.qx_agent.agent_name} binding {len(tools)} tools: {[getattr(t, 'name', 'unknown') for t in tools]}")
                                self._bound_tools = tools
                                return self
                            
                            @property
                            def _llm_type(self):
                                return "qx_llm_wrapper"
                            
                            @property
                            def _identifying_params(self):
                                """Return identifying parameters for the model."""
                                return {
                                    "model_name": getattr(self.qx_agent, 'model_name', 'qx_agent'),
                                    "agent_name": getattr(self.qx_agent, 'agent_name', 'unknown'),
                                    "wrapper_type": "qx_llm_wrapper"
                                }
                            
                            async def ainvoke(self, input, config=None, **kwargs):
                                """Async version of invoke for LangChain compatibility."""
                                return self.invoke(input, config, **kwargs)
                            
                            async def astream(self, input, config=None, **kwargs):
                                """Async streaming version for LangChain compatibility."""
                                result = await self.ainvoke(input, config, **kwargs)
                                yield result
                        
                        return QXLLMWrapper(qx_agent)
                    
                    langchain_llm = create_langchain_llm_wrapper(llm_agent)
                    
                    # Convert QX tools to LangChain tools
                    tools = []
                    if hasattr(llm_agent, '_openai_tools_schema') and llm_agent._openai_tools_schema:
                        # Convert QX tools to basic LangChain tools
                        from langchain_core.tools import tool
                        
                        @tool
                        def write_file(file_path: str, content: str) -> str:
                            """Write content to a file."""
                            try:
                                import os
                                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                                with open(file_path, 'w') as f:
                                    f.write(content)
                                return f"Successfully wrote content to {file_path}"
                            except Exception as e:
                                return f"Error writing file: {e}"
                        
                        @tool
                        def read_file(file_path: str) -> str:
                            """Read content from a file."""
                            try:
                                with open(file_path, 'r') as f:
                                    return f.read()
                            except Exception as e:
                                return f"Error reading file: {e}"
                        
                        tools = [write_file, read_file]
                    
                    # Create react agent with better prompt
                    agent_prompt = f"""You are {agent_name}, a {team_member.agent_config.description}

Role: {team_member.agent_config.role}

Instructions: {team_member.agent_config.instructions}

Always use the available tools when needed to complete tasks effectively."""
                    
                    react_agent = create_react_agent(
                        model=langchain_llm,
                        tools=tools,
                        name=agent_name,
                        prompt=agent_prompt
                    )
                    react_agents.append(react_agent)
                    themed_console.print(f"✓ Created react agent: {agent_name}", style="dim green")
                    
                except Exception as e:
                    # Enhanced error context for agent creation failures
                    agent_context = {
                        "agent_name": agent_name,
                        "agent_description": getattr(team_member.agent_config, 'description', 'unknown'),
                        "model_name": getattr(team_member.agent_config, 'model', {}).get('name', 'unknown'),
                        "enabled": getattr(team_member.agent_config, 'enabled', 'unknown'),
                        "tools_available": len(tools) if 'tools' in locals() else 0
                    }
                    
                    logger.warning(f"Failed to create react agent for {agent_name}: {e}")
                    logger.debug(f"Agent creation context: {agent_context}")
                    
                    # Provide specific troubleshooting guidance
                    if "mcp" in str(e).lower():
                        logger.warning(f"MCP initialization issue for {agent_name} - check MCP manager configuration")
                    elif "model" in str(e).lower():
                        logger.warning(f"Model configuration issue for {agent_name} - check agent YAML model settings")
                    elif "tool" in str(e).lower():
                        logger.warning(f"Tool integration issue for {agent_name} - check agent tool configuration")
                    else:
                        logger.warning(f"General agent creation issue for {agent_name} - check agent YAML configuration")
            
            if not react_agents:
                # Enhanced fallback handling with better context
                logger.warning(f"No react agents could be created from {len(team_members)} team members")
                logger.warning("Falling back to main agent - check agent configurations and error messages above")
                themed_console.print("⚠️ No team agents available, using main agent instead...", style="warning")
                
                # Fallback to main agent
                result = await self.main_llm_agent.run(user_input)
                return result.output if hasattr(result, 'output') else str(result)
            
            # Use Task Delegator system agent configuration
            # This is the SYSTEM LAYER agent that handles internal task routing
            # within the LangGraph team graph (not the user-facing qx-director)
            try:
                agent_loader = AgentLoader()
                supervisor_config = agent_loader.get_agent_config("Task Delegator", cwd=os.getcwd())
                
                if supervisor_config:
                    # Create agent list for the context
                    agent_list = chr(10).join([
                        f"- {agent.name}: {team_members[agent.name].agent_config.description}" 
                        for agent in react_agents
                    ])
                    
                    # Create delegation tools list
                    delegation_tools = [f"delegate_to_{agent.name}" for agent in react_agents]
                    delegation_tools_str = chr(10).join([f"- {tool}" for tool in delegation_tools])
                    
                    # Format the context for the supervisor
                    supervisor_prompt = supervisor_config.context.format(
                        agent_list=agent_list,
                        delegation_tools=delegation_tools_str
                    )
                    
                    # Also use the role and instructions
                    supervisor_prompt = f"{supervisor_config.role}\n\n{supervisor_config.instructions}\n\n{supervisor_prompt}"
                else:
                    raise Exception("Task Delegator system agent not found")
                    
            except Exception as e:
                logger.warning(f"Could not use Task Delegator system agent: {e}")
                # Fallback to inline prompt
                supervisor_prompt = f"""You are a team supervisor managing {len(react_agents)} specialized agents.

Available agents:
{chr(10).join([f"- {agent.name}: {team_members[agent.name].agent_config.description}" for agent in react_agents])}

Your job is to:
1. Analyze the user's request
2. Use the appropriate handoff tool to delegate to the best specialist agent
3. Ensure the task is completed successfully

CRITICAL: You MUST call the delegation tools instead of describing what you would do. 
When you receive requests, immediately call the appropriate delegate_to_[agent_name] tool.
Do NOT write explanations or descriptions - just call the tool directly."""
            
            # Create LangChain wrapper for main supervisor LLM
            def create_langchain_llm_wrapper(qx_agent):
                """Create a minimal LangChain-compatible LLM wrapper"""
                from langchain_core.language_models.base import BaseLanguageModel
                from langchain_core.messages import AIMessage
                
                from langchain_core.runnables import Runnable
                
                class QXLLMWrapper(Runnable):
                    def __init__(self, qx_agent):
                        self.qx_agent = qx_agent
                    
                    def invoke(self, input, config=None, **kwargs):
                        if isinstance(input, str):
                            content = input
                        elif hasattr(input, 'content'):
                            content = input.content
                        elif isinstance(input, list) and len(input) > 0:
                            # Handle list of messages
                            last_msg = input[-1]
                            content = getattr(last_msg, 'content', str(last_msg))
                        else:
                            content = str(input)
                        
                        logger.debug(f"Supervisor invoke called with: {content[:100]}")
                        
                        # Check if we have tools bound and should use them
                        if hasattr(self, '_bound_tools') and self._bound_tools:
                            # For supervisor with handoff tools, we need to decide whether to delegate
                            # Based on the content, determine if we should call a handoff tool
                            should_delegate = self._should_delegate(content)
                            if should_delegate:
                                # Call the handoff tool
                                logger.debug(f"Delegating with handoff tool")
                                return self._call_handoff_tool(content)
                        
                        logger.debug(f"No delegation, using QX agent directly")
                        import asyncio
                        result = asyncio.run(self.qx_agent.run(content))
                        response_text = result.output if hasattr(result, 'output') else str(result)
                        return AIMessage(content=response_text)
                    
                    def _should_delegate(self, content):
                        # Check if we have any delegation tools available
                        if hasattr(self, '_bound_tools') and self._bound_tools:
                            delegation_tools = [t for t in self._bound_tools if getattr(t, 'name', '').startswith('delegate_to')]
                            return len(delegation_tools) > 0
                        return False
                    
                    def _call_handoff_tool(self, content):
                        # Call the appropriate handoff tool based on available agents
                        from langchain_core.messages import AIMessage, ToolCall
                        import uuid
                        
                        # Find the best tool to call based on available bound tools
                        if hasattr(self, '_bound_tools') and self._bound_tools:
                            delegation_tools = [t for t in self._bound_tools if getattr(t, 'name', '').startswith('delegate_to')]
                            if delegation_tools:
                                # For now, use the first available delegation tool
                                # TODO: In the future, we could add logic to select the best agent based on task content
                                selected_tool = delegation_tools[0]
                                tool_name = selected_tool.name
                                tool_call_id = str(uuid.uuid4())
                                tool_call = ToolCall(
                                    name=tool_name,
                                    args={"task_description": content},
                                    id=tool_call_id
                                )
                                
                                agent_name = tool_name.replace('delegate_to_', '').replace('delegate_to', '')
                                logger.debug(f"Supervisor calling handoff tool: {tool_call.name}")
                                return AIMessage(
                                    content=f"Delegating to {agent_name} agent",
                                    tool_calls=[tool_call]
                                )
                        
                        # Fallback if no tools available
                        return AIMessage(content="No delegation tools available")
                    
                    def bind_tools(self, tools, **kwargs):
                        # Store tools for later use AND dynamically add them to the QX agent
                        logger.debug(f"Supervisor model binding {len(tools)} tools: {[getattr(t, 'name', 'unknown') for t in tools]}")
                        self._bound_tools = tools
                        
                        # Dynamically add handoff tools to the QX agent's tool system
                        for tool in tools:
                            tool_name = getattr(tool, 'name', 'unknown')
                            if tool_name.startswith('delegate_to'):
                                logger.debug(f"Adding handoff tool {tool_name} to QX agent")
                                self._add_handoff_tool_to_qx_agent(tool)
                        
                        return self
                    
                    def _add_handoff_tool_to_qx_agent(self, langchain_tool):
                        """Add a LangChain handoff tool to the QX agent's tool system"""
                        tool_name = langchain_tool.name
                        
                        # Create an async function that will be called by QX agent
                        async def handoff_function(task_description=None, **kwargs):
                            logger.debug(f"QX agent calling handoff tool {tool_name}")
                            
                            # Extract the agent name from the tool name (delegate_to_agent_name -> agent_name)
                            agent_name = tool_name.replace('delegate_to', '').replace('delegate_to_', '')
                            
                            # Get task description from various possible sources
                            if not task_description:
                                # Check if it's in the args object
                                args_obj = kwargs.get('args')
                                if args_obj and hasattr(args_obj, 'task_description'):
                                    task_description = args_obj.task_description
                                else:
                                    task_description = kwargs.get('task_description', kwargs.get('input', 'No task description provided'))
                            
                            logger.info(f"Delegating to {agent_name} with task: {task_description[:100]}...")
                            
                            # Find the target agent and execute the task
                            try:
                                # Get the parent supervisor reference
                                parent_supervisor = getattr(self.qx_agent, '_parent_supervisor', None)
                                if not parent_supervisor:
                                    return f"Successfully initiated delegation to {agent_name}: {task_description[:100]}..."
                                
                                team_members = parent_supervisor.team_manager.get_team_members()
                                if agent_name in team_members:
                                    target_member = team_members[agent_name]
                                    
                                    # Get agent color early for use throughout
                                    agent_color = getattr(target_member.agent_config, 'color', None)
                                    
                                    # Create the target agent with proper console manager integration
                                    from qx.core.llm_utils import initialize_agent_with_mcp
                                    target_agent = await initialize_agent_with_mcp(
                                        parent_supervisor.config_manager.mcp_manager,
                                        target_member.agent_config
                                    )
                                    
                                    # Ensure the target agent has console manager access for approval requests
                                    # Use the same console manager as the main agent for consistency
                                    if hasattr(parent_supervisor, 'main_llm_agent') and hasattr(parent_supervisor.main_llm_agent, 'console'):
                                        target_agent.console = parent_supervisor.main_llm_agent.console
                                    
                                    # Set up agent context for approval handlers to show proper BorderedMarkdown
                                    from qx.core.approval_handler import set_global_agent_context
                                    set_global_agent_context(agent_name, agent_color)
                                    
                                    # Display delegation using BorderedMarkdown
                                    from qx.cli.quote_bar_component import render_agent_markdown
                                    render_agent_markdown(
                                        f"**Delegated Task:** {task_description[:200]}...",
                                        agent_name,
                                        agent_color=agent_color,
                                        console=target_agent.console if hasattr(target_agent, 'console') else None
                                    )
                                    
                                    # Execute the task with the target agent using proper console context
                                    from qx.core.llm import query_llm
                                    result = await query_llm(
                                        target_agent,
                                        task_description,
                                        message_history=[],
                                        console=target_agent.console if hasattr(target_agent, 'console') else None,
                                        config_manager=parent_supervisor.config_manager
                                    )
                                    response = result.output if hasattr(result, 'output') else str(result)
                                    
                                    # Display completion using BorderedMarkdown
                                    render_agent_markdown(
                                        f"**Task Completed:** {response[:150]}...",
                                        agent_name,
                                        agent_color=agent_color,
                                        console=target_agent.console if hasattr(target_agent, 'console') else None
                                    )
                                    
                                    return f"Task completed by {agent_name}: {response[:200]}..."
                                else:
                                    return f"Agent {agent_name} not found in team"
                            except Exception as e:
                                logger.error(f"Error executing delegated task: {e}")
                                return f"Error delegating to {agent_name}: {str(e)}"
                        
                        # Add to QX agent's tool functions
                        self.qx_agent._tool_functions[tool_name] = handoff_function
                        
                        # Create a Pydantic model for the tool input
                        from pydantic import BaseModel, Field
                        
                        class HandoffInput(BaseModel):
                            task_description: str = Field(description="Detailed description of the task to delegate")
                        
                        # Add to tool input models
                        self.qx_agent._tool_input_models[tool_name] = HandoffInput
                        
                        # Create schema for the tool
                        tool_schema = {
                            "name": tool_name,
                            "description": f"Delegate task to {tool_name.replace('delegate_to', '').replace('delegate_to_', '')} agent",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "task_description": {
                                        "type": "string",
                                        "description": "Detailed description of the task to delegate"
                                    }
                                },
                                "required": ["task_description"]
                            }
                        }
                        
                        # Add to QX agent's tool schema
                        try:
                            from openai.types.chat import ChatCompletionToolParam
                            from openai.types.shared_params.function_definition import FunctionDefinition
                            
                            self.qx_agent._openai_tools_schema.append(
                                ChatCompletionToolParam(
                                    type="function",
                                    function=FunctionDefinition(**tool_schema)
                                )
                            )
                            logger.debug(f"Successfully added {tool_name} to QX agent tool system")
                        except Exception as e:
                            logger.warning(f"Error adding tool schema for {tool_name}: {e}")
                    
                    @property
                    def _identifying_params(self):
                        """Return identifying parameters for the model."""
                        return {
                            "model_name": getattr(self.qx_agent, 'model_name', 'qx_supervisor'),
                            "agent_name": getattr(self.qx_agent, 'agent_name', 'supervisor'),
                            "wrapper_type": "qx_llm_wrapper"
                        }
                    
                    async def ainvoke(self, input, config=None, **kwargs):
                        """Async version of invoke for LangChain compatibility."""
                        return self.invoke(input, config, **kwargs)
                    
                    async def astream(self, input, config=None, **kwargs):
                        """Async streaming version for LangChain compatibility."""
                        result = await self.ainvoke(input, config, **kwargs)
                        yield result
                    
                    @property
                    def _llm_type(self):
                        return "qx_llm_wrapper"
                
                return QXLLMWrapper(qx_agent)
            
            supervisor_llm = create_langchain_llm_wrapper(self.main_llm_agent)
            
            # Set parent supervisor reference for handoff tools
            self.main_llm_agent._parent_supervisor = self
            
            # Enhanced logging: Starting supervisor creation
            logger.info(f"Creating LangGraph supervisor with {len(react_agents)} react agents")
            logger.debug(f"Supervisor configuration - handoff_tool_prefix: 'delegate_to', output_mode: '{self.output_mode}'")
            logger.debug(f"Supervisor name: '{self.supervisor_name}', add_handoff_messages: {self.add_handoff_messages}")
            logger.debug(f"Supervisor prompt length: {len(supervisor_prompt)} characters")
            if self.debug_mode:
                logger.debug(f"Enhanced debug mode is ENABLED (timeout: {self.supervisor_timeout}s)")
            else:
                logger.debug(f"Debug mode is disabled (timeout: {self.supervisor_timeout}s)")
            
            # Use create_supervisor with automatic handoff tool creation
            supervisor = create_supervisor(
                react_agents,
                model=supervisor_llm,
                prompt=supervisor_prompt,
                handoff_tool_prefix="delegate_to",  # This creates tools like delegate_to_[agent_name]
                output_mode=self.output_mode,  # Configurable output mode
                supervisor_name=self.supervisor_name,  # Configurable supervisor name
                add_handoff_messages=self.add_handoff_messages  # Configurable handoff messages
            )
            
            # Enhanced logging: Supervisor successfully created
            logger.info(f"✓ LangGraph supervisor created successfully with name: {self.supervisor_name}")
            logger.debug(f"Supervisor created with nodes: {list(supervisor.nodes.keys()) if hasattr(supervisor, 'nodes') else 'unknown'}")
            logger.debug(f"Supervisor graph type: {type(supervisor)}")
            
            # Debug: Print supervisor info
            logger.info(f"Created supervisor with {len(react_agents)} agents")
            logger.info(f"Agent names: {[agent.name for agent in react_agents]}")
            logger.info(f"Supervisor model: {type(self.main_llm_agent.llm)}")
            
            # Check if model supports tool calling
            has_bind_tools = hasattr(self.main_llm_agent.llm, 'bind_tools')
            has_with_structured_output = hasattr(self.main_llm_agent.llm, 'with_structured_output')
            logger.info(f"Model supports bind_tools: {has_bind_tools}")
            logger.info(f"Model supports with_structured_output: {has_with_structured_output}")
            
            if not has_bind_tools:
                themed_console.print(f"⚠️ Model {type(self.main_llm_agent.llm)} may not support tool calling", style="yellow")
            
            # Enhanced logging: Memory configuration
            logger.debug("Configuring supervisor memory with InMemorySaver and InMemoryStore")
            
            # Compile with proper memory configuration (matching official docs)
            checkpointer = InMemorySaver()
            store = InMemoryStore()
            app = supervisor.compile(
                checkpointer=checkpointer,
                store=store
            )
            
            logger.info("✓ Supervisor compiled successfully with memory configuration")
            
            # Enhanced logging: Execution setup
            import uuid
            thread_id = str(uuid.uuid4())
            config = {"configurable": {"thread_id": thread_id}}
            
            logger.info(f"Starting supervisor execution with thread_id: {thread_id}")
            logger.debug(f"Invoking supervisor with user_input: {user_input[:100]}...")
            logger.debug(f"Execution config: {config}")
            logger.debug(f"Using timeout: {self.supervisor_timeout}s")
            
            # Use configurable timeout for supervisor execution
            # Format messages with conversation history for proper context
            formatted_messages = []
            
            if message_history:
                # Convert message history to the format expected by LangGraph
                for msg in message_history:
                    if hasattr(msg, 'role') and hasattr(msg, 'content'):
                        # Pydantic message object
                        formatted_messages.append({
                            "role": msg.role,
                            "content": msg.content
                        })
                    elif isinstance(msg, dict) and "role" in msg and "content" in msg:
                        # Dict message
                        formatted_messages.append({
                            "role": msg["role"],
                            "content": msg["content"]
                        })
                
                # Add current user input if not already included
                if not formatted_messages or formatted_messages[-1].get("content") != user_input:
                    formatted_messages.append({"role": "user", "content": user_input})
            else:
                # No history, just current input
                formatted_messages = [{"role": "user", "content": user_input}]
            
            logger.debug(f"Sending {len(formatted_messages)} messages to supervisor (including conversation history)")
            
            result = await asyncio.wait_for(
                app.ainvoke({
                    "messages": formatted_messages
                }, config=config),
                timeout=self.supervisor_timeout
            )
            
            # Enhanced logging: Result processing
            logger.info("✓ Supervisor execution completed successfully")
            logger.debug(f"Supervisor result type: {type(result)}")
            logger.debug(f"Result keys: {list(result.keys()) if isinstance(result, dict) else 'not a dict'}")
            
            if result and "messages" in result and result["messages"]:
                logger.debug(f"Found {len(result['messages'])} messages in result")
                last_message = result["messages"][-1]
                logger.debug(f"Last message type: {type(last_message)}")
                
                if hasattr(last_message, 'content'):
                    response = last_message.content
                    logger.info(f"✓ Retrieved response content ({len(response)} characters)")
                    return response
                elif isinstance(last_message, dict):
                    response = last_message.get('content', 'Task completed successfully')
                    logger.info(f"✓ Retrieved response from dict content ({len(response)} characters)")
                    return response
                else:
                    response = str(last_message)
                    logger.info(f"✓ Retrieved response as string ({len(response)} characters)")
                    return response
            else:
                logger.warning("No messages found in supervisor result, returning default response")
                return "Task completed successfully"
                
        except asyncio.TimeoutError as e:
            # Enhanced timeout error handling
            logger.error(f"Supervisor execution timed out after {self.supervisor_timeout}s for user input: {user_input[:100]}...")
            logger.error(f"Consider increasing QX_SUPERVISOR_TIMEOUT environment variable (current: {self.supervisor_timeout}s)")
            themed_console.print(f"⚠️ Team workflow timed out after {self.supervisor_timeout}s, falling back to main agent...", style="warning")
            
            # Fallback to main agent with timeout context
            result = await self.main_llm_agent.run(user_input)
            return result.output if hasattr(result, 'output') else str(result)
            
        except Exception as e:
            # Enhanced general error handling with better context
            error_context = {
                "supervisor_name": self.supervisor_name,
                "output_mode": self.output_mode,
                "debug_mode": self.debug_mode,
                "timeout": self.supervisor_timeout,
                "input_length": len(user_input),
                "team_size": len(self.team_manager.get_team_members())
            }
            
            logger.error(f"Error in proper supervisor workflow: {e}", exc_info=True)
            logger.error(f"Supervisor context: {error_context}")
            logger.error(f"User input (first 200 chars): {user_input[:200]}...")
            
            # Provide helpful troubleshooting information
            if "tool" in str(e).lower():
                logger.error("Possible tool-related error - check agent tool configurations and handoff tools")
            elif "model" in str(e).lower():
                logger.error("Possible model-related error - check QX model configuration and LangChain compatibility")
            elif "message" in str(e).lower():
                logger.error("Possible message handling error - check input format and message processing")
            
            # Fallback to main agent
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