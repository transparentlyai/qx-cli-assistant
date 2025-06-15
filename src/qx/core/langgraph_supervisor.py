"""
Simplified LangGraph Supervisor implementation using langgraph-supervisor library.

This module implements the supervisor pattern where:
- All agents are defined in YAML
- Leverages handoff mechanisms for agent delegation
- Maintains QX's constraints (liteLLM, console manager, tool plugins, etc.)
"""

import logging
import uuid
from typing import Dict, List, Optional, Any
from enum import Enum

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.store.memory import InMemoryStore
from langgraph.graph import MessagesState, StateGraph, START, END
from typing_extensions import TypedDict, Literal
from typing import Annotated
import operator

# Import langgraph-supervisor components
from langgraph_supervisor import create_handoff_tool
from langgraph.types import Command

from qx.core.team_manager import get_team_manager, TeamMember
from qx.core.config_manager import ConfigManager
from qx.core.console_manager import get_console_manager
from qx.core.langgraph_tool_adapter import get_tool_adapter
from qx.core.langgraph_model_adapter import create_langchain_model
from qx.core.llm_utils import initialize_agent_with_mcp
from qx.core.mcp_manager import MCPManager
from qx.core.llm import QXLLMAgent

logger = logging.getLogger(__name__)


class NodeType(Enum):
    """Types of nodes in the workflow."""
    SUPERVISOR = "supervisor"
    AGENT = "agent"


# Extended state for team mode with conversation memory
class TeamState(MessagesState):
    """Extended state for team mode workflow."""
    task_context: str = ""  # Current task description
    current_task: Optional[str] = None  # Active task ID
    agent_outputs: Annotated[List[Dict[str, Any]], operator.add] = []  # Outputs from agents
    error_info: Optional[str] = None  # Error information
    active_agent: str = "qx-director"  # Currently active agent
    reasoning: str = ""  # Supervisor's reasoning for routing


class UnifiedWorkflow:
    """
    Unified workflow implementing the LangGraph supervisor pattern for team mode.
    """
    
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.team_manager = get_team_manager(config_manager)
        self.console_manager = get_console_manager()
        
        # Workflow components - will be created fresh for each session
        self.workflow_app = None
        self.checkpointer = None
        self.store = None
        
        # Track current execution
        self.current_thread_id = None
        
    def _get_or_create_mcp_manager(self) -> MCPManager:
        """Get existing MCP manager or create a new one."""
        mcp_manager = getattr(self.config_manager, 'mcp_manager', None)
        if not mcp_manager:
            console = getattr(self.config_manager, 'console', self.console_manager.console)
            task_group = getattr(self.config_manager, 'task_group', None)
            mcp_manager = MCPManager(console, task_group)
        return mcp_manager
    
    def _build_agent_prompt(self, agent_config) -> str:
        """Build prompt from agent configuration."""
        role = getattr(agent_config, 'role', '') or ''
        instructions = getattr(agent_config, 'instructions', '') or ''
        system_prompt = getattr(agent_config, 'system_prompt', '') or ''
        
        # Combine into agent prompt
        return system_prompt or f"{role}\n\n{instructions}"
    
    def _display_agent_output(self, content: str, agent_name: str, agent_color: str = '#808080'):
        """Display agent output through console manager."""
        from qx.cli.quote_bar_component import render_agent_markdown
        render_agent_markdown(
            content,
            agent_name,
            agent_color=agent_color
        )
    
    async def _create_unified_node(self, 
                                   agent_name: str, 
                                   team_member: TeamMember,
                                   node_type: NodeType,
                                   handoff_tools: List[Any] = None) -> callable:
        """
        Create a unified node function that works for both supervisor and regular agents.
        
        Args:
            agent_name: Name of the agent
            team_member: TeamMember object with agent configuration
            node_type: Type of node (SUPERVISOR or AGENT)
            handoff_tools: List of handoff tools (only for supervisor)
            
        Returns:
            Async function that processes state and returns Command
        """
        
        async def unified_node(state: TeamState) -> Command:
            """Unified node that processes state and returns to supervisor or ends."""
            try:
                agent_config = team_member.agent_config
                
                # Build agent prompt
                agent_prompt = self._build_agent_prompt(agent_config)
                
                # For supervisor, replace team members placeholder
                if node_type == NodeType.SUPERVISOR and '{team_members}' in agent_prompt:
                    team_context = self._build_team_context()
                    agent_prompt = agent_prompt.replace('{team_members}', team_context)
                
                # Get or create MCP manager
                mcp_manager = self._get_or_create_mcp_manager()
                
                # Initialize agent based on type
                if node_type == NodeType.SUPERVISOR:
                    # Create a minimal supervisor LLM agent without base tools
                    console = getattr(self.console_manager, '_default_console', None)
                    if not console:
                        from qx.cli.theme import themed_console
                        console = themed_console
                    
                    llm_agent = QXLLMAgent(
                        model_name=getattr(agent_config.model, 'name', 'openrouter/google/gemini-2.5-pro-preview-06-05'),
                        system_prompt=agent_prompt,
                        tools=[],  # No base tools for supervisor
                        console=console,
                        temperature=getattr(agent_config.model.parameters, 'temperature', 0.7),
                        agent_name=agent_name,
                        agent_color=getattr(agent_config, 'color', '#ff5f00')
                    )
                else:
                    # Regular agent with tools
                    llm_agent = await initialize_agent_with_mcp(
                        mcp_manager=mcp_manager,
                        agent_config=agent_config
                    )
                    
                    if not llm_agent:
                        raise Exception(f"Failed to initialize LLM agent for {agent_name}")
                
                # Create LangChain-compatible model
                langchain_model = create_langchain_model(llm_agent)
                langchain_model.agent_name = agent_name
                
                # Bind handoff tools for supervisor
                if node_type == NodeType.SUPERVISOR and handoff_tools:
                    langchain_model = langchain_model.bind_tools(handoff_tools)
                
                # Prepare messages
                messages = state.get("messages", [])
                system_msg = SystemMessage(content=agent_prompt)
                full_messages = [system_msg] + messages
                
                # Invoke the model
                response = await langchain_model.ainvoke(full_messages)
                
                # Display output
                agent_color = getattr(agent_config, 'color', '#808080')
                if hasattr(response, "content") and response.content:
                    self._display_agent_output(response.content, agent_name, agent_color)
                
                # Handle routing based on node type
                if node_type == NodeType.SUPERVISOR:
                    # Check for tool calls (delegation)
                    if hasattr(response, "tool_calls") and response.tool_calls:
                        for tool_call in response.tool_calls:
                            # Handle both dict and object formats
                            if isinstance(tool_call, dict):
                                tool_name = tool_call.get("name", "")
                                tool_args = tool_call.get("args", {})
                            else:
                                tool_name = getattr(tool_call, "name", "")
                                tool_args = getattr(tool_call, "args", {})
                                
                            if tool_name.startswith("transfer_to_"):
                                target_agent = tool_name.replace("transfer_to_", "")
                                task_desc = tool_args.get("task_description", "") if isinstance(tool_args, dict) else ""
                                return Command(
                                    goto=target_agent,
                                    update={
                                        "active_agent": target_agent,
                                        "task_context": task_desc
                                    }
                                )
                    
                    # Check for exit signals
                    content = response.content.lower() if hasattr(response, "content") else ""
                    if any(word in content for word in ["goodbye", "done", "completed", "finished"]):
                        return Command(goto=END)
                    
                    # If no tool calls, end current iteration (prevents infinite recursion)
                    if not (hasattr(response, "tool_calls") and response.tool_calls):
                        return Command(
                            goto=END,
                            update={"messages": state["messages"] + [response]}
                        )
                    
                    # Otherwise continue conversation
                    return Command(
                        goto="supervisor",
                        update={"messages": state["messages"] + [response]}
                    )
                else:
                    # Regular agent - return to supervisor
                    return Command(
                        goto="supervisor",
                        update={
                            "messages": state["messages"] + [AIMessage(content=response.content, name=agent_name)],
                            "agent_outputs": [{"agent": agent_name, "output": response.content}],
                            "active_agent": "qx-director"
                        }
                    )
                    
            except Exception as e:
                logger.error(f"Error in {node_type.value} node {agent_name}: {e}", exc_info=True)
                self._display_agent_output(
                    f"Error in {agent_name}: {str(e)}",
                    agent_name,
                    getattr(team_member.agent_config, 'color', '#808080')
                )
                
                # Return error state
                return Command(
                    goto="supervisor" if node_type == NodeType.AGENT else END,
                    update={
                        "error_info": str(e),
                        "messages": state["messages"] + [AIMessage(content=f"Error: {str(e)}", name=agent_name)],
                        "active_agent": "qx-director"
                    }
                )
        
        # Set function name for debugging
        unified_node.__name__ = f"{agent_name}_node"
        return unified_node
    
    def _build_team_context(self) -> str:
        """Build team context string for supervisor prompt."""
        team_context = ""
        for agent_name, team_member in self.team_manager.get_team_members().items():
            if agent_name.lower() != "qx-director":
                desc = getattr(team_member.agent_config, 'description', 'Specialist agent')
                team_context += f"- **transfer_to_{agent_name}**: {desc}\n"
        return team_context
    
    async def build_team_workflow(self):
        """Build the unified workflow using langgraph-supervisor pattern."""
        try:
            logger.info("🏗️ Building unified workflow with langgraph-supervisor pattern")
            
            team_members = self.team_manager.get_team_members()
            if not team_members:
                raise ValueError("No team members found. Add agents to your team first.")
                
            # Build the graph using StateGraph
            builder = StateGraph(TeamState)
            
            # Track agent nodes and handoff tools
            agent_nodes = {}
            handoff_tools = []
            director_member = None
            
            # Separate director from other agents
            for agent_name, team_member in team_members.items():
                if agent_name.lower() == "qx-director":
                    director_member = team_member
                else:
                    # Create handoff tool for this agent
                    handoff_tool = create_handoff_tool(
                        agent_name=agent_name,
                        description=getattr(team_member.agent_config, 'description', f'Transfer to {agent_name}')
                    )
                    handoff_tools.append(handoff_tool)
                    
            if not director_member:
                raise ValueError("qx-director not found in team configuration. The director agent is required.")
                
            # Create supervisor node with handoff tools
            supervisor_node = await self._create_unified_node(
                "qx-director",
                director_member,
                NodeType.SUPERVISOR,
                handoff_tools
            )
            builder.add_node("supervisor", supervisor_node)
            
            # Create nodes for all other agents
            for agent_name, team_member in team_members.items():
                if agent_name.lower() != "qx-director":
                    agent_node = await self._create_unified_node(
                        agent_name,
                        team_member,
                        NodeType.AGENT
                    )
                    agent_nodes[agent_name] = agent_node
                    builder.add_node(agent_name, agent_node)
                    
            if not agent_nodes:
                raise ValueError("No specialist agents could be created. Team must have at least one agent besides the director.")
                
            logger.info(f"Created {len(agent_nodes)} specialist agent nodes")
            
            # Add edges
            builder.add_edge(START, "supervisor")  # Start with supervisor
            
            # Add edges from all agents back to supervisor
            for agent_name in agent_nodes:
                builder.add_edge(agent_name, "supervisor")
            
            # Create fresh checkpointer and store
            self.checkpointer = InMemorySaver()
            self.store = InMemoryStore()
            
            # Compile the graph
            self.workflow_app = builder.compile(
                checkpointer=self.checkpointer,
                store=self.store
            )
            
            logger.info("✅ Workflow compiled successfully with all agents as nodes")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to build workflow: {e}", exc_info=True)
            raise
    
    async def process_input(self, user_input: str = "", thread_id: Optional[str] = None) -> str:
        """Process user input through the workflow."""
        if not self.workflow_app:
            # Build workflow if not already built
            logger.warning("Workflow not initialized, building now...")
            await self.build_team_workflow()
                
        # Use existing thread or create new one
        if not thread_id:
            thread_id = self.current_thread_id or str(uuid.uuid4())
            self.current_thread_id = thread_id
            
        try:
            # Create the input state
            if user_input:
                messages = [HumanMessage(content=user_input)]
                logger.info(f"Sending message to workflow: '{user_input}'")
            else:
                # Empty input - supervisor will ask for input
                messages = []
                logger.info("Sending empty messages to workflow")
                
            # Initialize full state
            input_state = {
                "messages": messages,
                "task_context": "",
                "current_task": None,
                "agent_outputs": [],
                "error_info": None,
                "active_agent": "qx-director",
                "reasoning": ""
            }
                
            # Configure the execution
            config = {
                "configurable": {
                    "thread_id": thread_id
                }
            }
            
            # Execute the workflow
            logger.info(f"🚀 Executing workflow with thread_id: {thread_id}")
            result = await self.workflow_app.ainvoke(
                input_state,
                config=config
            )
            
            # The response is already displayed by agents
            # Return success indicator
            return "Workflow completed"
                
        except Exception as e:
            logger.error(f"❌ Workflow execution error: {e}", exc_info=True)
            return f"Error during workflow execution: {str(e)}"
    
    async def start_continuous_workflow(self):
        """Start the workflow in continuous mode for team interaction."""
        logger.info("🎯 Starting continuous workflow mode")
        
        # Build workflow fresh for this session
        await self.build_team_workflow()
        
        # Initialize thread for conversation
        thread_id = str(uuid.uuid4())
        logger.info(f"Starting new conversation with thread_id: {thread_id}")
        
        # Import qpromp to reuse its infrastructure
        from qx.cli.qpromp import qpromp
        
        # Get prompts and messages from director config
        team_members = self.team_manager.get_team_members()
        director_member = team_members.get('qx-director')
        
        # Set defaults
        initial_prompt = "**How can I help you today?**"
        goodbye_message = "Goodbye! 👋"
        
        # Override with YAML config if available
        if director_member and director_member.agent_config:
            config = director_member.agent_config
            initial_prompt = getattr(config, 'initial_prompt', initial_prompt)
            goodbye_message = getattr(config, 'goodbye_message', goodbye_message)
        
        # Display initial prompt
        self._display_agent_output(
            initial_prompt.strip(),
            "qx-director",
            "#ff5f00"
        )
        
        # Use qpromp's infrastructure for input loop
        while True:
            try:
                # Get user input via qpromp
                user_input = await qpromp(
                    prompt_text="Qx Director",
                    mode="team",
                    enable_hotkeys=True,
                    show_global_hotkeys=True,
                    show_local_hotkeys=True,
                    show_navigation_footer=True
                )
                
                if not user_input or not user_input.strip():
                    continue
                    
                # Check for exit commands
                if user_input.lower().strip() in ["exit", "quit", "goodbye", "bye"]:
                    logger.info("👋 User requested exit")
                    self._display_agent_output(
                        goodbye_message.strip(),
                        "qx-director",
                        "#ff5f00"
                    )
                    break
                
                # Process user input through the workflow
                logger.info(f"Processing user input: '{user_input}'")
                response = await self.process_input(user_input, thread_id)
                
                # Response is already displayed by the agents
                # Just continue the loop for next input
                
            except KeyboardInterrupt:
                logger.info("⏹️ Workflow interrupted by user")
                self._display_agent_output(
                    "Workflow interrupted. Goodbye! 👋",
                    "qx-director",
                    "#ff5f00"
                )
                break
            except EOFError:
                logger.info("👋 User requested exit (Ctrl+D)")
                break
            except Exception as e:
                logger.error(f"❌ Error in continuous workflow: {e}", exc_info=True)
                self._display_agent_output(
                    f"**Error:** {str(e)}\n\nPlease try again.",
                    "qx-director",
                    "#ff5f00"
                )
                # Continue with a new thread after error
                thread_id = str(uuid.uuid4())


def get_unified_workflow(config_manager: ConfigManager) -> UnifiedWorkflow:
    """Create a new unified workflow instance.
    
    Each call creates a fresh instance to ensure clean state.
    """
    logger.info("Creating new UnifiedWorkflow instance")
    return UnifiedWorkflow(config_manager)