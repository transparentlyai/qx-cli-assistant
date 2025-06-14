"""
Unified LangGraph workflow system for qx multi-agent coordination.

This module implements a single LangGraph workflow where:

1. qx-director is the START node and primary human interface
2. All team agents are nodes within the same unified graph
3. Human-in-the-loop interactions flow through the console manager
4. Shared checkpoint system maintains conversation context across all nodes
5. All agent interactions use BorderedMarkdown with proper colors

ARCHITECTURAL FLOW:
START → qx-director (human interface) → [specialist nodes] → synthesis → END
           ↓                              ↓
       interrupt()                  back to director
   (human input/approval)           (results/questions)

Key Features:
- Single unified LangGraph execution
- Shared conversation memory across all agents
- Console manager integration for all outputs
- Human approval gates using interrupt()
- Comprehensive logging for debugging
"""

import asyncio
import json
import logging
import time
import uuid
from typing import Any, Dict, List, Optional, Tuple

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import MessagesState, StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.store.memory import InMemoryStore
from langgraph.types import interrupt, Command

# Remove old supervisor dependencies - using clean LangGraph approach
# No longer using langgraph-supervisor library or create_react_agent

from qx.core.team_manager import get_team_manager, TeamManager, TeamMember
from qx.core.config_manager import ConfigManager
from qx.core.agent_manager import get_agent_manager
from qx.core.llm import QXLLMAgent
from qx.cli.theme import themed_console
from qx.core.agent_loader import AgentLoader
from qx.core.interrupt_bridge import get_interrupt_bridge
from qx.core.workflow_context import workflow_execution_context
from qx.core.dynamic_agent_loader import DynamicAgentLoader
from qx.core.agent_routing_optimizer import AgentRoutingOptimizer, RoutingStrategy
from qx.core.workflow_monitor import get_workflow_monitor, track_workflow_execution, track_agent_execution, MonitoringLevel
from qx.core.workflow_debug_logger import get_debug_logger, LogLevel

logger = logging.getLogger(__name__)


class QXWorkflowState(MessagesState):
    """Unified state for QX LangGraph workflow."""
    
    # Core workflow state
    user_input: str = ""
    current_node: str = ""
    workflow_stage: str = ""  # "director", "specialist", "synthesis", "complete"
    
    # Task management
    task_description: str = ""
    selected_agent: str = ""
    agent_results: Dict[str, str] = {}
    
    # Human interaction
    awaiting_approval: bool = False
    approval_context: Dict[str, Any] = {}
    human_response: str = ""
    
    # Execution tracking
    execution_start_time: float = 0.0
    node_timings: Dict[str, float] = {}
    error_context: Dict[str, Any] = {}


# Removed QxAgentWrapper - using direct agent integration


class UnifiedLangGraphWorkflow:
    """
    Unified LangGraph workflow that integrates qx-director as the main human interface node
    with all team agents as specialized nodes in a single graph.
    
    Key responsibilities:
    - Create unified StateGraph with qx-director as START node
    - Integrate human-in-the-loop through interrupt() and console manager
    - Manage shared checkpoint system for conversation continuity
    - Coordinate specialist agent execution within the graph
    - Provide comprehensive logging for debugging
    """
    
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.team_manager = get_team_manager(config_manager)
        
        # Enhanced dynamic agent loading system
        self.dynamic_agent_loader = DynamicAgentLoader(config_manager, self.team_manager)
        
        # Advanced routing optimization system
        self.routing_optimizer = AgentRoutingOptimizer(self.dynamic_agent_loader)
        
        # Comprehensive workflow monitoring system
        self.workflow_monitor = get_workflow_monitor(MonitoringLevel.STANDARD)
        
        # Comprehensive debugging system
        self.debug_logger = get_debug_logger(LogLevel.STANDARD)
        
        # Unified workflow components
        self.workflow_graph = None
        self.checkpointer = InMemorySaver()
        self.store = InMemoryStore()
        
        # Enhanced logging configuration
        self.debug_mode = True  # Always enable comprehensive logging
        self.execution_timeout = 300.0  # 5 minutes timeout
        
        # Performance tracking
        self.execution_metrics = {
            "total_executions": 0,
            "node_performance": {},
            "error_counts": {},
            "average_response_time": 0.0,
            "agent_metrics": {},
            "routing_metrics": {}
        }
        
        logger.info("🚀 UnifiedLangGraphWorkflow initialized with dynamic agent loading")
        logger.debug(f"📊 Config: timeout={self.execution_timeout}s, debug={self.debug_mode}")
        logger.debug(f"💾 Checkpoint system: {type(self.checkpointer).__name__}")

    def _load_environment_config(self):
        """Load configuration from environment variables."""
        import os
        
        # Timeout configuration
        env_timeout = os.environ.get('QX_WORKFLOW_TIMEOUT')
        if env_timeout:
            try:
                self.execution_timeout = float(env_timeout)
                logger.info(f"⚙️ Using workflow timeout from environment: {self.execution_timeout}s")
            except ValueError:
                logger.warning(f"⚠️ Invalid workflow timeout value: {env_timeout}, using default")
        
        # Enhanced debug mode
        env_debug = os.environ.get('QX_WORKFLOW_DEBUG', 'true').lower()
        self.debug_mode = env_debug in ('true', '1', 'yes', 'on')
        logger.info(f"🐛 Debug mode: {'ENABLED' if self.debug_mode else 'DISABLED'}")
        
        logger.debug(f"🔧 Environment config loaded: timeout={self.execution_timeout}s, debug={self.debug_mode}")

    async def _get_agent_for_workflow(self, agent_name: str) -> Optional[QXLLMAgent]:
        """Get an agent for workflow execution using dynamic loading."""
        try:
            loaded_agent = await self.dynamic_agent_loader.get_agent(agent_name)
            if loaded_agent and loaded_agent.agent:
                logger.debug(f"🎯 Retrieved agent {agent_name} (usage: {loaded_agent.usage_count})")
                return loaded_agent.agent
            else:
                logger.error(f"❌ Failed to load agent: {agent_name}")
                return None
        except Exception as e:
            logger.error(f"❌ Error getting agent {agent_name}: {e}", exc_info=True)
            return None

    async def _build_unified_workflow(self):
        """Build the unified LangGraph workflow with qx-director as START node."""
        try:
            logger.info("🏗️ Building unified LangGraph workflow")
            build_start_time = time.time()
            
            # Create the unified workflow graph
            workflow = StateGraph(QXWorkflowState)
            
            # Add qx-director as the main human interface node
            workflow.add_node("qx-director", self._director_node)
            logger.info("✅ Added qx-director as main interface node")
            
            # Add specialist agent nodes (using dynamic loading)
            team_members = self.team_manager.get_team_members()
            specialist_count = 0
            
            # Preload critical agents for better performance
            critical_agents = [name for name in team_members.keys() if name != "qx-director"]
            if critical_agents:
                logger.info(f"🚀 Preloading {len(critical_agents)} specialist agents")
                await self.dynamic_agent_loader.preload_critical_agents(critical_agents)
            
            for agent_name, team_member in team_members.items():
                if agent_name != "qx-director":  # Skip director, already added
                    # Create node function for this specialist (agent loaded lazily)
                    node_func = self._create_dynamic_specialist_node(agent_name, team_member)
                    workflow.add_node(agent_name, node_func)
                    specialist_count += 1
                    logger.info(f"✅ Added dynamic specialist node: {agent_name}")
            
            # Add synthesis node for combining results
            workflow.add_node("synthesis", self._synthesis_node)
            logger.info("✅ Added synthesis node")
            
            # Set up graph flow
            workflow.set_entry_point("qx-director")
            
            # Director can route to any specialist or synthesis
            from langgraph.graph import END
            workflow.add_conditional_edges(
                "qx-director",
                self._route_from_director,
                {
                    "end": END,
                    "synthesis": "synthesis",
                    "qx-director": "qx-director",  # Allow routing back to director
                    **{name: name for name in team_members.keys() if name != "qx-director"}
                }
            )
            
            # All specialists return to director for coordination
            for agent_name in team_members.keys():
                if agent_name != "qx-director":
                    workflow.add_edge(agent_name, "qx-director")
            
            # Synthesis returns to director
            workflow.add_edge("synthesis", "qx-director")
            
            # Compile the workflow with checkpoint system
            self.workflow_graph = workflow.compile(
                checkpointer=self.checkpointer,
                store=self.store
            )
            
            build_time = time.time() - build_start_time
            logger.info(f"Unified workflow built successfully in {build_time:.2f}s")
            logger.info(f"Workflow stats: 1 director + {specialist_count} specialists + 1 synthesis node")
            
            # Log comprehensive graph structure for debugging
            all_nodes = ["qx-director"] + list(team_members.keys()) + ["synthesis"]
            all_nodes = [node for node in all_nodes if node != "qx-director" or all_nodes.count(node) == 1]  # Remove duplicates
            
            graph_edges = []
            # Director to specialists
            for agent_name in team_members.keys():
                if agent_name != "qx-director":
                    graph_edges.append(("qx-director", agent_name))
                    graph_edges.append((agent_name, "qx-director"))
            # Director to synthesis and synthesis back
            graph_edges.append(("qx-director", "synthesis"))
            graph_edges.append(("synthesis", "qx-director"))
            
            self.debug_logger.log_graph_structure(all_nodes, graph_edges)
            
        except Exception as e:
            logger.error(f"❌ Failed to build unified workflow: {e}", exc_info=True)
            self.workflow_graph = None
            raise

    async def rebuild_workflow(self):
        """Rebuild the unified workflow when team composition changes."""
        logger.info("🔄 Rebuilding unified workflow")
        await self._build_unified_workflow()

    async def should_use_unified_workflow(self, user_input: str) -> bool:
        """Determine if the unified workflow should be used."""
        # Always use unified workflow when team mode is enabled
        if not self.team_manager.has_team():
            logger.debug("🚫 No team available, skipping unified workflow")
            return False
        
        # Build workflow if it doesn't exist yet
        if not self.workflow_graph:
            logger.info("🏗️ Building unified workflow on demand")
            try:
                await self._build_unified_workflow()
            except Exception as e:
                logger.error(f"❌ Failed to build unified workflow: {e}", exc_info=True)
                return False
            
        logger.info(f"✅ Using unified workflow for: {user_input[:50]}...")
        return True

    async def _get_director_agent(self) -> Optional[QXLLMAgent]:
        """Get or create the qx-director agent using dynamic loading."""
        try:
            director_agent = await self._get_agent_for_workflow("qx-director")
            if director_agent:
                logger.info("✅ qx-director agent loaded via dynamic loading")
                return director_agent
            else:
                logger.warning("⚠️ qx-director agent could not be loaded")
                return None
                
        except Exception as e:
            logger.error(f"❌ Failed to load qx-director agent: {e}", exc_info=True)
            return None
    
    async def _director_node(self, state: QXWorkflowState) -> QXWorkflowState:
        """Main qx-director node that handles human interaction and task coordination."""
        execution_id = state.get("execution_id", "unknown")
        node_start_time = time.time()
        
        # Use debug logger for comprehensive node tracking
        with self.debug_logger.log_node_execution(execution_id, "qx-director", "qx-director"):
            self.debug_logger.log_node_input(execution_id, "qx-director", state)
            
            try:
                # Update state
                updated_state = {
                    **state,
                    "current_node": "qx-director",
                    "workflow_stage": "director"
                }
                
                # Handle different workflow stages
                stage = state.get("workflow_stage", "")
                
                if stage == "" or stage == "director":
                    # Initial user input - decide on next action
                    user_input = state.get("user_input", "")
                    
                    if not user_input:
                        # Get user input through LangGraph interrupt with QX styling
                        interrupt_payload = {
                            "type": "user_input",
                            "message": "What would you like me to help you with?",
                            "agent_name": "qx-director",
                            "agent_color": "#ff5f00"
                        }
                        self.debug_logger.log_interrupt_start(execution_id, "user_input", interrupt_payload)
                        
                        # Show QX-styled prompt before interrupt
                        from qx.cli.quote_bar_component import render_agent_markdown
                        render_agent_markdown(
                            "**Ready for your request**\n\nWhat would you like me to help you with?",
                            "qx-director",
                            agent_color="#ff5f00"
                        )
                        
                        # Use LangGraph interrupt to pause and wait for user input
                        user_response = interrupt(interrupt_payload)
                        
                        # Log human response and resumption
                        self.debug_logger.log_human_response(execution_id, user_response)
                        self.debug_logger.log_interrupt_resume(execution_id, "user_input")
                        
                        updated_state["user_input"] = user_response
                        updated_state["human_response"] = user_response
                
                    # Analyze task and decide routing
                    updated_state["workflow_stage"] = "routing"
                
                elif stage == "routing":
                    # Route to appropriate specialist or handle directly
                    user_input = state.get("user_input", "")
                    team_members = self.team_manager.get_team_members()
                    
                    # Check if we have any specialists (team size >= 2 means director + at least 1 specialist)
                    if len(team_members) >= 2:
                        # Use advanced routing optimizer
                        task_analysis = await self.routing_optimizer.analyze_task(user_input)
                        routing_decision = await self.routing_optimizer.optimize_routing(
                            task_analysis=task_analysis,
                            strategy=RoutingStrategy.ADAPTIVE,
                            exclude_agents={"qx-director"}
                        )
                        
                        if routing_decision.selected_agents and routing_decision.confidence_score > 0.1:
                            selected_agent = routing_decision.selected_agents[0]  # Use primary agent
                            updated_state["selected_agent"] = selected_agent
                            updated_state["task_description"] = user_input
                            updated_state["task_analysis"] = task_analysis
                            updated_state["routing_decision"] = routing_decision
                            updated_state["workflow_stage"] = "specialist_execution"
                            
                            logger.info(f"🎯 Optimized routing to specialist: {selected_agent} (confidence: {routing_decision.confidence_score:.2f})")
                            
                            # Show enhanced routing decision
                            from qx.cli.quote_bar_component import render_agent_markdown
                            routing_details = (
                                f"**Optimized Routing Decision**\n\n"
                                f"• **Selected Agent:** {selected_agent}\n"
                                f"• **Task Complexity:** {task_analysis.complexity.value.title()}\n"
                                f"• **Confidence:** {routing_decision.confidence_score:.1%}\n"
                                f"• **Strategy:** {routing_decision.routing_strategy.value.replace('_', ' ').title()}\n"
                                f"• **Reasoning:** {routing_decision.reasoning}\n\n"
                                f"**Task:** {user_input[:150]}..."
                            )
                            render_agent_markdown(
                                routing_details,
                                "qx-director",
                                agent_color="#ff5f00"
                            )
                        else:
                            # Handle directly if no suitable specialist found or low confidence
                            logger.info(f"🎯 No suitable specialist found or low confidence ({routing_decision.confidence_score:.2f}), handling directly")
                            updated_state["workflow_stage"] = "direct_response"
                    else:
                        # No specialists available, handle directly
                        updated_state["workflow_stage"] = "direct_response"
                
                elif stage == "specialist_execution":
                    # Specialist has completed, review results and record routing outcome
                    agent_results = state.get("agent_results", {})
                    routing_decision = state.get("routing_decision")
                    task_analysis = state.get("task_analysis")
                    
                    # Record routing outcome for learning
                    if routing_decision and task_analysis:
                        selected_agent = state.get("selected_agent")
                        if selected_agent and selected_agent in agent_results:
                            # Calculate actual execution time
                            node_timings = state.get("node_timings", {})
                            actual_duration = node_timings.get(selected_agent, 0.0)
                            
                            # Record successful routing outcome
                            self.routing_optimizer.record_routing_outcome(
                                decision=routing_decision,
                                actual_agents=[selected_agent],
                                actual_duration=actual_duration,
                                success=True
                            )
                            
                            logger.debug(f"📊 Recorded successful routing outcome for {selected_agent}: {actual_duration:.1f}s")
                    if agent_results:
                        # Show results and ask for approval or next steps
                        latest_result = list(agent_results.values())[-1]
                        
                        # Ensure result is a string
                        if isinstance(latest_result, list):
                            latest_result = "\n".join(str(item) for item in latest_result)
                        elif not isinstance(latest_result, str):
                            latest_result = str(latest_result)
                        
                        # Update stage to prevent re-routing to same specialist
                        updated_state["workflow_stage"] = "awaiting_satisfaction"
                        
                        # Ask user if they're satisfied or need more work
                        logger.info("⏸️ INTERRUPT: Checking user satisfaction")
                        
                        # Show only the satisfaction check - the agent result was already displayed
                        from qx.cli.quote_bar_component import render_agent_markdown
                        render_agent_markdown(
                            f"**Are you satisfied with this result, or would you like me to do anything else?**",
                            "qx-director",
                            agent_color="#ff5f00"
                        )
                        
                        # Use LangGraph interrupt to pause and wait for user feedback
                        from langgraph.errors import GraphInterrupt
                        try:
                            user_feedback = interrupt({
                                "type": "satisfaction_check",
                                "message": "Are you satisfied with this result, or would you like me to do anything else?",
                                "result": latest_result,
                                "agent_name": "qx-director",
                                "agent_color": "#ff5f00"
                            })
                            
                            updated_state["human_response"] = user_feedback
                            
                            if "satisfied" in user_feedback.lower() or "done" in user_feedback.lower() or "thanks" in user_feedback.lower():
                                updated_state["workflow_stage"] = "complete"
                            else:
                                # User wants more work
                                updated_state["user_input"] = user_feedback
                                updated_state["workflow_stage"] = "routing"
                                
                            logger.info(f"▶️ RESUME: User feedback: {user_feedback[:50]}...")
                        except GraphInterrupt:
                            # This is expected - propagate to pause the workflow
                            raise
                
                elif stage == "awaiting_satisfaction":
                    # We're waiting for user satisfaction feedback
                    # This should only be reached after interrupt resume
                    # The interrupt handler should have set human_response
                    user_feedback = state.get("human_response", "")
                    if user_feedback:
                        if "satisfied" in user_feedback.lower() or "done" in user_feedback.lower() or "thanks" in user_feedback.lower():
                            updated_state["workflow_stage"] = "complete"
                        else:
                            # User wants more work
                            updated_state["user_input"] = user_feedback
                            updated_state["workflow_stage"] = "routing"
                    else:
                        # No feedback yet, stay in awaiting state
                        logger.debug("Still awaiting user satisfaction feedback")
                
                elif stage == "direct_response":
                    # Director handles the task directly
                    director_agent = await self._get_director_agent()
                    if director_agent:
                        user_input = state.get("user_input", "")
                        
                        # Execute director within workflow context
                        async with workflow_execution_context(
                            workflow_id="unified_workflow",
                            agent_name="qx-director",
                            agent_color="#ff5f00",
                            thread_id=f"workflow_{time.time()}",
                            use_interrupts=True
                        ):
                            result = await director_agent.run(user_input)
                            response = result.output if hasattr(result, 'output') else str(result)
                        
                        # Display director response with QX styling
                        from qx.cli.quote_bar_component import render_agent_markdown
                        render_agent_markdown(
                            f"**Task Complete**\n\n{response}",
                            "qx-director",
                            agent_color="#ff5f00"
                        )
                        
                        updated_state["agent_results"] = {"qx-director": response}
                        updated_state["workflow_stage"] = "complete"
                        
                        logger.info(f"✅ Director handled task directly: {len(response)} chars")
                
                # Record timing
                node_time = time.time() - node_start_time
                timings = state.get("node_timings", {})
                timings["qx-director"] = timings.get("qx-director", 0) + node_time
                updated_state["node_timings"] = timings
                
                logger.info(f"🎯 EXIT director_node: stage={updated_state.get('workflow_stage')}, duration={node_time:.2f}s")
                logger.debug(f"📤 Director output state: {json.dumps({k: str(v)[:100] for k, v in updated_state.items() if k not in ['messages', 'node_timings']}, indent=2)}")
                
                return updated_state
                
            except Exception as e:
                logger.error(f"❌ Error in director_node: {e}", exc_info=True)
                error_state = {
                    **state,
                    "workflow_stage": "error",
                    "error_context": {"node": "qx-director", "error": str(e)}
                }
                return error_state
    
    def _create_dynamic_specialist_node(self, agent_name: str, team_member: TeamMember):
        """Create a dynamic specialist node function that loads agents on demand."""
        
        async def dynamic_specialist_node(state: QXWorkflowState) -> QXWorkflowState:
            execution_id = state.get("execution_id", "unknown")
            node_start_time = time.time()
            
            # Start agent execution monitoring
            async with track_agent_execution(execution_id, agent_name, {"task_description": state.get("task_description", "")}) as agent_execution:
                # Use debug logger for comprehensive node tracking
                with self.debug_logger.log_node_execution(execution_id, agent_name, agent_name):
                    self.debug_logger.log_node_input(execution_id, agent_name, state)
                    try:
                        # Get task description
                        task_description = state.get("task_description", state.get("user_input", ""))
                    
                        # Dynamically load the agent
                        agent = await self._get_agent_for_workflow(agent_name)
                        if not agent:
                            logger.error(f"❌ Failed to load agent {agent_name} for execution")
                            error_state = {
                                **state,
                                "workflow_stage": "error",
                                "error_context": {"node": agent_name, "error": f"Agent {agent_name} could not be loaded"}
                            }
                            return error_state
                
                        # Get agent color for context
                        agent_color = getattr(team_member.agent_config, 'color', None)
                        
                        # Execute agent within workflow context
                        async with workflow_execution_context(
                            workflow_id="unified_workflow",
                            agent_name=agent_name,
                            agent_color=agent_color,
                            thread_id=f"workflow_{time.time()}",
                            use_interrupts=True
                        ):
                            # Display agent activity
                            from qx.cli.quote_bar_component import render_agent_markdown
                            
                            render_agent_markdown(
                                f"**Working on task**\n\n{task_description[:200]}...",
                                agent_name,
                                agent_color=agent_color
                            )
                            
                            # Execute the specialist agent
                            logger.debug(f"🔧 Executing {agent_name} with task: {task_description[:100]}...")
                            result = await agent.run(task_description)
                            
                            # Extract response from result, handling different formats
                            if hasattr(result, 'output'):
                                response = result.output
                            else:
                                response = result
                            
                            # Ensure response is a string
                            if isinstance(response, list):
                                # If it's a list, join the elements
                                response = "\n".join(str(item) for item in response)
                            elif not isinstance(response, str):
                                response = str(response)
                        
                        # Agent already displayed its response through QX's system
                        # No need to display again here
                        logger.debug(f"📝 {agent_name} completed task, response captured")
                        
                        # Update agent results
                        agent_results = state.get("agent_results", {})
                        agent_results[agent_name] = response
                        
                        # Record timing
                        node_time = time.time() - node_start_time
                        timings = state.get("node_timings", {})
                        timings[agent_name] = node_time
                        
                        updated_state = {
                            **state,
                            "current_node": agent_name,
                            "agent_results": agent_results,
                            "node_timings": timings,
                            "workflow_stage": "specialist_execution"
                        }
                        
                        logger.info(f"✅ EXIT dynamic_specialist_node: {agent_name}, duration={node_time:.2f}s, response_length={len(response)}")
                        logger.debug(f"📤 {agent_name} output: {response[:100]}...")
                        
                        return updated_state
                        
                    except Exception as e:
                        logger.error(f"❌ Error in dynamic_specialist_node {agent_name}: {e}", exc_info=True)
                        error_state = {
                            **state,
                            "workflow_stage": "error",
                            "error_context": {"node": agent_name, "error": str(e)}
                        }
                        return error_state
        
        return dynamic_specialist_node
    
    async def _synthesis_node(self, state: QXWorkflowState) -> QXWorkflowState:
        """Synthesis node that combines results from multiple agents."""
        node_start_time = time.time()
        logger.info("🔗 ENTER synthesis_node")
        
        try:
            agent_results = state.get("agent_results", {})
            
            if len(agent_results) <= 1:
                # No synthesis needed
                logger.info("🔗 No synthesis needed (single or no results)")
                return {
                    **state,
                    "current_node": "synthesis",
                    "workflow_stage": "specialist_execution"
                }
            
            # Combine multiple agent results
            logger.info(f"🔗 Synthesizing {len(agent_results)} agent results")
            
            synthesis_content = "## Combined Results\n\n"
            for agent_name, result in agent_results.items():
                # Ensure result is a string
                if isinstance(result, list):
                    result_str = "\n".join(str(item) for item in result)
                elif not isinstance(result, str):
                    result_str = str(result)
                else:
                    result_str = result
                synthesis_content += f"### {agent_name}\n{result_str}\n\n"
            
            # Display synthesis with QX styling
            from qx.cli.quote_bar_component import render_agent_markdown
            render_agent_markdown(
                f"**Synthesis Complete**\n\n{synthesis_content}",
                "synthesis",
                agent_color="#9d4edd"  # Purple color for synthesis node
            )
            
            # Update results with synthesis
            agent_results["synthesis"] = synthesis_content
            
            # Record timing
            node_time = time.time() - node_start_time
            timings = state.get("node_timings", {})
            timings["synthesis"] = node_time
            
            updated_state = {
                **state,
                "current_node": "synthesis",
                "agent_results": agent_results,
                "node_timings": timings,
                "workflow_stage": "specialist_execution"
            }
            
            logger.info(f"✅ EXIT synthesis_node: duration={node_time:.2f}s")
            return updated_state
            
        except Exception as e:
            logger.error(f"❌ Error in synthesis_node: {e}", exc_info=True)
            return {
                **state,
                "workflow_stage": "error",
                "error_context": {"node": "synthesis", "error": str(e)}
            }
    
    def _route_from_director(self, state: QXWorkflowState) -> str:
        """Routing function to determine next node from director."""
        logger.debug("🔀 Routing from director")
        
        workflow_stage = state.get("workflow_stage", "")
        selected_agent = state.get("selected_agent", "")
        
        logger.debug(f"🔀 Routing decision: stage={workflow_stage}, selected_agent={selected_agent}")
        
        if workflow_stage == "complete" or workflow_stage == "error":
            logger.info("🏁 Workflow complete, routing to END")
            return "end"
        elif workflow_stage == "specialist_execution" and selected_agent:
            logger.info(f"➡️ Routing to specialist: {selected_agent}")
            return selected_agent
        elif workflow_stage == "awaiting_satisfaction":
            # Stay in director to handle satisfaction response
            logger.debug("⏸️ Awaiting satisfaction feedback, staying in director")
            return "qx-director"
        elif len(state.get("agent_results", {})) > 1:
            logger.info("🔗 Multiple results, routing to synthesis")
            return "synthesis"
        else:
            # Stay in director for more processing
            logger.debug("🔄 Staying in director for more processing")
            return "qx-director"

    async def process_with_unified_workflow(self, user_input: str, message_history: Optional[List] = None) -> str:
        """Process user request through the unified LangGraph workflow."""
        execution_id = f"workflow_{int(time.time() * 1000)}"
        
        # Start comprehensive workflow monitoring and debug logging
        async with track_workflow_execution(execution_id, user_input) as workflow_execution:
            try:
                execution_start_time = time.time()
                
                # Create thread ID and start debug logging
                thread_id = str(uuid.uuid4())
                self.debug_logger.log_graph_start(thread_id, execution_id, user_input)
                
                # Ensure workflow is built
                if not self.workflow_graph:
                    logger.info("Building workflow graph...")
                    await self._build_unified_workflow()
                    
                if not self.workflow_graph:
                    raise Exception("Failed to build unified workflow graph")
            
                # Create initial state
                config = {"configurable": {"thread_id": thread_id}}
                
                initial_state = {
                    "user_input": user_input,
                    "messages": [HumanMessage(content=user_input)],
                    "workflow_stage": "director",
                    "execution_start_time": execution_start_time,
                    "node_timings": {},
                    "agent_results": {},
                    "current_node": "",
                    "task_description": "",
                    "selected_agent": "",
                    "awaiting_approval": False,
                    "approval_context": {},
                    "human_response": "",
                    "error_context": {},
                    "execution_id": execution_id,
                    "thread_id": thread_id
                }
                
                # Log graph state and execution start
                self.debug_logger.log_graph_state(execution_id, initial_state)
                logger.info(f"Invoking workflow: thread_id={thread_id}, execution_id={execution_id}")
                
                # Execute the workflow with comprehensive debug logging
                final_state = await asyncio.wait_for(
                    self.workflow_graph.ainvoke(initial_state, config=config),
                    timeout=self.execution_timeout
                )
            
                # Extract final response and log completion
                agent_results = final_state.get("agent_results", {})
                total_time = time.time() - execution_start_time
                
                if agent_results:
                    # Get the most relevant result (synthesis if available, otherwise latest agent result)
                    if "synthesis" in agent_results:
                        final_response = agent_results["synthesis"]
                        response_source = "synthesis"
                    else:
                        final_response = list(agent_results.values())[-1]
                        response_source = list(agent_results.keys())[-1]
                    
                    # Ensure final_response is a string
                    if isinstance(final_response, list):
                        final_response = "\n".join(str(item) for item in final_response)
                    elif not isinstance(final_response, str):
                        final_response = str(final_response)
                    
                    # Log workflow completion with debug logger
                    result_summary = f"source={response_source}, length={len(final_response)}"
                    self.debug_logger.log_graph_complete(execution_id, total_time, result_summary)
                    self.debug_logger.log_performance_summary(execution_id)
                    
                    # Update enhanced performance metrics
                    self.execution_metrics["total_executions"] += 1
                    self.execution_metrics["average_response_time"] = (
                        (self.execution_metrics["average_response_time"] * (self.execution_metrics["total_executions"] - 1) + total_time) /
                        self.execution_metrics["total_executions"]
                    )
                    self.execution_metrics["routing_metrics"] = self.routing_optimizer.get_routing_metrics()
                    
                    return final_response
                else:
                    logger.warning("No agent results in final state")
                    self.debug_logger.log_graph_complete(execution_id, total_time, "no_results")
                    return "Task completed, but no specific results were generated."
                    
            except asyncio.TimeoutError as e:
                # Log timeout error with debug logger
                error_state = {"timeout": self.execution_timeout, "execution_id": execution_id}
                self.debug_logger.log_workflow_error(execution_id, e, error_state)
                
                self.execution_metrics["error_counts"]["timeout"] = self.execution_metrics["error_counts"].get("timeout", 0) + 1
                return f"Workflow execution timed out after {self.execution_timeout} seconds. Please try a simpler request."
                
            except Exception as e:
                # Log comprehensive error with debug logger
                error_state = {"execution_id": execution_id, "workflow_stage": "execution"}
                self.debug_logger.log_workflow_error(execution_id, e, error_state)
                
                error_type = type(e).__name__
                self.execution_metrics["error_counts"][error_type] = self.execution_metrics["error_counts"].get(error_type, 0) + 1
                return f"An error occurred during workflow execution: {str(e)}"

    def get_execution_metrics(self) -> Dict[str, Any]:
        """Get comprehensive performance and execution metrics."""
        metrics = {
            "execution_metrics": self.execution_metrics.copy(),
            "workflow_status": "built" if self.workflow_graph else "not_built",
            "checkpointer_type": type(self.checkpointer).__name__,
            "team_size": len(self.team_manager.get_team_members()),
            "debug_mode": self.debug_mode,
            "timeout": self.execution_timeout,
            "agent_metrics": self.dynamic_agent_loader.get_agent_metrics(),
            "routing_metrics": self.routing_optimizer.get_routing_metrics(),
            "monitoring_analytics": self.workflow_monitor.get_performance_analytics()
        }
        return metrics

    async def cleanup(self):
        """Clean up resources including dynamic agent loader and workflow monitor."""
        logger.info("🧹 Cleaning up UnifiedLangGraphWorkflow")
        try:
            # Cleanup workflow monitor
            await self.workflow_monitor.cleanup()
            
            # Cleanup dynamic agent loader
            await self.dynamic_agent_loader.cleanup()
            
            # Clear workflow graph
            self.workflow_graph = None
            
            # Clear checkpoint data if needed
            if hasattr(self.checkpointer, 'clear'):
                self.checkpointer.clear()
            
            # Clear store data if needed
            if hasattr(self.store, 'clear'):
                self.store.clear()
                
            logger.info("✅ Cleanup completed")
        except Exception as e:
            logger.error(f"❌ Error during cleanup: {e}", exc_info=True)


# Global workflow instance
_unified_workflow: Optional[UnifiedLangGraphWorkflow] = None


def get_unified_workflow(config_manager: ConfigManager) -> UnifiedLangGraphWorkflow:
    """Get the global unified workflow instance."""
    global _unified_workflow
    if _unified_workflow is None:
        _unified_workflow = UnifiedLangGraphWorkflow(config_manager)
    return _unified_workflow


async def rebuild_unified_workflow():
    """Rebuild the unified workflow when team changes."""
    global _unified_workflow
    if _unified_workflow is not None:
        await _unified_workflow.rebuild_workflow()


def get_langgraph_supervisor(config_manager: ConfigManager, main_llm_agent: QXLLMAgent = None) -> UnifiedLangGraphWorkflow:
    """Get the global unified workflow instance (legacy name for compatibility)."""
    return get_unified_workflow(config_manager)


async def rebuild_supervisor_workflow():
    """Rebuild the unified workflow when team changes (legacy name for compatibility)."""
    await rebuild_unified_workflow()


# Removed old supervisor implementation - replaced with unified workflow