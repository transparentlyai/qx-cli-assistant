"""
Simplified LangGraph Supervisor implementation using langgraph-supervisor library.

This module implements the proper supervisor pattern where:
- All agents are defined in YAML (no hardcoded director)
- Uses create_supervisor() and create_react_agent() from the library
- Leverages built-in handoff mechanisms
- Maintains QX's constraints (liteLLM, console manager, tool plugins, etc.)
"""

import asyncio
import logging
import time
import uuid
from typing import Dict, List, Optional, Any
from pathlib import Path

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.store.memory import InMemoryStore
from langgraph.graph import MessagesState, StateGraph, START, END
from typing_extensions import TypedDict, Literal
from typing import Annotated
import operator

# Import langgraph-supervisor components
from langgraph_supervisor import create_handoff_tool
from langgraph.prebuilt import create_react_agent
from langgraph.types import interrupt, Command

from qx.core.team_manager import get_team_manager, TeamManager, TeamMember
from qx.core.config_manager import ConfigManager
from qx.core.console_manager import get_console_manager
from qx.core.workflow_context import get_workflow_context
from qx.core.interrupt_bridge import get_interrupt_bridge
from qx.core.langgraph_tool_adapter import get_tool_adapter
from qx.core.langgraph_model_adapter import create_langchain_model
from qx.core.langgraph_interrupt_adapter import get_interrupt_adapter
from qx.core.llm_utils import initialize_agent_with_mcp
from qx.core.mcp_manager import MCPManager

logger = logging.getLogger(__name__)


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
    Simplified unified workflow using langgraph-supervisor library.
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
        
    async def create_agent_node(self, agent_name: str, team_member: TeamMember):
        """Create an agent node that wraps the agent for the graph."""
        
        async def agent_node(state: TeamState) -> Command[Literal["supervisor"]]:
            """Agent node that processes state and returns to supervisor."""
            try:
                # Create the agent from YAML
                agent_config = team_member.agent_config
                
                # Get the agent's role and instructions
                role = getattr(agent_config, 'role', '') or ''
                instructions = getattr(agent_config, 'instructions', '') or ''
                system_prompt = getattr(agent_config, 'system_prompt', '') or ''
                
                # Combine into agent prompt
                agent_prompt = system_prompt or f"{role}\n\n{instructions}"
                
                # Get tools for this agent using the adapter
                tool_adapter = get_tool_adapter()
                tools = tool_adapter.load_tools_for_agent(agent_name, agent_config)
                
                # Create liteLLM wrapper for this agent
                mcp_manager = getattr(self.config_manager, 'mcp_manager', None)
                if not mcp_manager:
                    console = getattr(self.config_manager, 'console', self.console_manager.console)
                    task_group = getattr(self.config_manager, 'task_group', None)
                    mcp_manager = MCPManager(console, task_group)
                
                llm_agent = await initialize_agent_with_mcp(
                    mcp_manager=mcp_manager,
                    agent_config=agent_config
                )
                
                if not llm_agent:
                    raise Exception(f"Failed to initialize LLM agent for {agent_name}")
                    
                # Create LangChain-compatible model using adapter
                langchain_model = create_langchain_model(llm_agent)
                langchain_model.agent_name = agent_name  # Set agent name for display
                    
                # Create the agent using create_react_agent
                agent = create_react_agent(
                    model=langchain_model,
                    tools=tools,
                    name=agent_name,
                    prompt=agent_prompt
                )
                
                # Invoke the agent with current state
                result = await agent.ainvoke(state)
                
                # Extract the response
                if "messages" in result and result["messages"]:
                    last_message = result["messages"][-1]
                    
                    # Display output immediately via console manager
                    from qx.cli.quote_bar_component import render_agent_markdown
                    agent_color = getattr(agent_config, 'color', '#808080')
                    
                    if hasattr(last_message, "content"):
                        render_agent_markdown(
                            last_message.content,
                            agent_name,
                            agent_color=agent_color
                        )
                    
                    # Return control to supervisor with updated state
                    return Command(
                        goto="supervisor",
                        update={
                            "messages": state["messages"] + [AIMessage(content=last_message.content, name=agent_name)],
                            "agent_outputs": [{"agent": agent_name, "output": last_message.content}],
                            "active_agent": "qx-director"  # Return control to director
                        }
                    )
                else:
                    # No response from agent
                    return Command(
                        goto="supervisor",
                        update={"active_agent": "qx-director"}
                    )
                    
            except Exception as e:
                logger.error(f"Error in agent node {agent_name}: {e}", exc_info=True)
                # Return error to supervisor
                return Command(
                    goto="supervisor",
                    update={
                        "error_info": str(e),
                        "messages": state["messages"] + [AIMessage(content=f"Error in {agent_name}: {str(e)}", name=agent_name)],
                        "active_agent": "qx-director"
                    }
                )
        
        # Set the function name for debugging
        agent_node.__name__ = f"{agent_name}_node"
        return agent_node
    
    
    async def build_team_workflow(self):
        """Build the unified workflow using langgraph-supervisor pattern."""
        try:
            logger.info("🏗️ Building unified workflow with langgraph-supervisor pattern")
            
            team_members = self.team_manager.get_team_members()
            if not team_members:
                logger.warning("No team members found")
                return False
                
            # Build the graph using StateGraph
            builder = StateGraph(TeamState)
            
            # Track agent nodes and handoff tools
            agent_nodes = {}
            handoff_tools = []
            director_config = None
            director_member = None
            
            # Create nodes for ALL agents (including director)
            for agent_name, team_member in team_members.items():
                if agent_name.lower() == "qx-director":
                    director_config = team_member.agent_config
                    director_member = team_member
                else:
                    # Create agent node
                    agent_node = await self.create_agent_node(agent_name, team_member)
                    agent_nodes[agent_name] = agent_node
                    builder.add_node(agent_name, agent_node)
                    
                    # Create handoff tool for this agent
                    handoff_tool = create_handoff_tool(
                        agent_name=agent_name,
                        description=getattr(team_member.agent_config, 'description', f'Transfer to {agent_name}')
                    )
                    handoff_tools.append(handoff_tool)
                    
            if not director_config:
                logger.error("qx-director not found in team configuration")
                return False
                
            if not agent_nodes:
                logger.error("No specialist agents could be created")
                return False
                
            logger.info(f"Created {len(agent_nodes)} specialist agent nodes")
            
            # Build team context for supervisor prompt
            team_context = ""
            for agent_name, team_member in team_members.items():
                if agent_name.lower() != "qx-director":
                    desc = getattr(team_member.agent_config, 'description', 'Specialist agent')
                    team_context += f"- **transfer_to_{agent_name}**: {desc}\n"
            
            # Create supervisor node using qx-director
            async def supervisor_node(state: TeamState) -> Command:
                """Supervisor node that routes to agents or ends conversation."""
                try:
                    # Get supervisor configuration
                    director_role = getattr(director_config, 'role', '') or ''
                    director_instructions = getattr(director_config, 'instructions', '') or ''
                    
                    # Replace {team_members} placeholder
                    director_instructions = director_instructions.replace('{team_members}', team_context)
                    
                    # Create supervisor prompt
                    supervisor_prompt = f"{director_role}\n\n{director_instructions}"
                    
                    # Get MCP manager
                    mcp_manager = getattr(self.config_manager, 'mcp_manager', None)
                    if not mcp_manager:
                        console = getattr(self.config_manager, 'console', self.console_manager.console)
                        task_group = getattr(self.config_manager, 'task_group', None)
                        mcp_manager = MCPManager(console, task_group)
                    
                    # Create supervisor LLM (without base tools, only handoff tools)
                    temp_config = director_config.copy()
                    temp_config.tools = []  # Clear base tools
                    
                    supervisor_llm_agent = await initialize_agent_with_mcp(
                        mcp_manager=mcp_manager,
                        agent_config=temp_config
                    )
                    
                    if not supervisor_llm_agent:
                        raise Exception("Failed to create supervisor LLM")
                    
                    # Create LangChain model and bind handoff tools
                    supervisor_model = create_langchain_model(supervisor_llm_agent)
                    supervisor_model = supervisor_model.bind_tools(handoff_tools)
                    
                    # Create the supervisor agent
                    supervisor_agent = create_react_agent(
                        model=supervisor_model,
                        tools=handoff_tools,
                        name="qx-director",
                        prompt=supervisor_prompt
                    )
                    
                    # Invoke supervisor
                    result = await supervisor_agent.ainvoke(state)
                    
                    # Check if supervisor wants to end or delegate
                    if "messages" in result and result["messages"]:
                        last_message = result["messages"][-1]
                        
                        # Display supervisor's message
                        from qx.cli.quote_bar_component import render_agent_markdown
                        director_color = getattr(director_config, 'color', '#ff5f00')
                        
                        if hasattr(last_message, "content") and last_message.content:
                            render_agent_markdown(
                                last_message.content,
                                "qx-director",
                                agent_color=director_color
                            )
                        
                        # Check for tool calls (delegation)
                        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
                            for tool_call in last_message.tool_calls:
                                if tool_call.get("name", "").startswith("transfer_to_"):
                                    agent_name = tool_call["name"].replace("transfer_to_", "")
                                    if agent_name in agent_nodes:
                                        return Command(
                                            goto=agent_name,
                                            update={
                                                "active_agent": agent_name,
                                                "task_context": tool_call.get("args", {}).get("task_description", "")
                                            }
                                        )
                        
                        # Check for exit signals
                        content = last_message.content.lower() if hasattr(last_message, "content") else ""
                        if any(word in content for word in ["goodbye", "done", "completed", "finished"]):
                            return Command(goto="__end__")
                    
                    # Default: continue conversation
                    return Command(
                        goto="supervisor",  # Loop back to supervisor
                        update={"messages": state["messages"] + result.get("messages", [])}
                    )
                    
                except Exception as e:
                    logger.error(f"Error in supervisor node: {e}", exc_info=True)
                    from qx.cli.quote_bar_component import render_agent_markdown
                    render_agent_markdown(
                        f"Error in supervisor: {str(e)}",
                        "qx-director",
                        agent_color="#ff5f00"
                    )
                    return Command(goto="__end__")
            
            # Add supervisor node
            builder.add_node("supervisor", supervisor_node)
            
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
            return False
    
    async def process_input(self, user_input: str = "", thread_id: Optional[str] = None) -> str:
        """Process user input through the workflow."""
        if not self.workflow_app:
            # Build workflow if not already built
            logger.warning("Workflow not initialized, building now...")
            success = await self.build_team_workflow()
            if not success:
                return "Failed to initialize team workflow"
                
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
        success = await self.build_team_workflow()
        if not success:
            logger.error("Failed to build team workflow")
            return
        
        # Initialize thread for conversation
        thread_id = str(uuid.uuid4())
        logger.info(f"Starting new conversation with thread_id: {thread_id}")
        
        # Import necessary components for proper QX integration
        from prompt_toolkit import PromptSession
        from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
        from prompt_toolkit.shortcuts.prompt import CompleteStyle
        from prompt_toolkit.styles import Style
        from prompt_toolkit.formatted_text import HTML
        from qx.cli.history import QXHistory
        from qx.cli.completer import QXCompleter
        from qx.core.paths import QX_HISTORY_FILE
        from qx.cli.quote_bar_component import render_agent_markdown
        
        # Initialize QX components
        qx_history = QXHistory(QX_HISTORY_FILE)
        qx_completer = QXCompleter()
        
        # Create prompt style matching qx-director color
        prompt_style = Style.from_dict({
            "prompt": "#ff5f00",  # qx-director color
        })
        
        # Create prompt session with QX's standard configuration
        session = PromptSession(
            history=qx_history,
            auto_suggest=AutoSuggestFromHistory(),
            enable_history_search=False,
            completer=qx_completer,
            complete_style=CompleteStyle.COLUMN,
            mouse_support=False,
            style=prompt_style
        )
        
        # Get prompts and messages from director config
        team_members = self.team_manager.get_team_members()
        director_member = team_members.get('qx-director')
        
        # Set defaults
        initial_prompt = "**How can I help you today?**"
        goodbye_message = "Goodbye! 👋"
        interrupted_message = "Workflow interrupted. Goodbye! 👋"
        error_message_template = "**Error:** {error}\n\nPlease try again."
        
        # Override with YAML config if available
        if director_member and director_member.agent_config:
            config = director_member.agent_config
            initial_prompt = getattr(config, 'initial_prompt', initial_prompt)
            goodbye_message = getattr(config, 'goodbye_message', goodbye_message)
            interrupted_message = getattr(config, 'interrupted_message', interrupted_message)
            error_message_template = getattr(config, 'error_message_template', error_message_template)
        
        # Display initial prompt once
        render_agent_markdown(
            initial_prompt.strip(),
            "qx-director",
            agent_color="#ff5f00"
        )
        
        while True:
            try:
                
                # Get user input using prompt_toolkit session
                prompt_text = HTML('<style fg="#ff5f00">Qx Director</style> &gt; ')
                user_input = await session.prompt_async(prompt_text)
                
                if not user_input or not user_input.strip():
                    continue
                    
                # Save to history
                qx_history.append_string(user_input)
                
                # Check for exit commands
                if user_input.lower().strip() in ["exit", "quit", "goodbye", "bye"]:
                    logger.info("👋 User requested exit")
                    render_agent_markdown(
                        goodbye_message.strip(),
                        "qx-director",
                        agent_color="#ff5f00"
                    )
                    break
                
                # Process user input through the workflow
                logger.info(f"Processing user input: '{user_input}'")
                response = await self.process_input(user_input, thread_id)
                
                # Response is already displayed by the agents
                # Just continue the loop for next input
                
            except KeyboardInterrupt:
                logger.info("⏹️ Workflow interrupted by user")
                render_agent_markdown(
                    interrupted_message.strip(),
                    "qx-director",
                    agent_color="#ff5f00"
                )
                break
            except EOFError:
                logger.info("👋 User requested exit (Ctrl+D)")
                break
            except Exception as e:
                logger.error(f"❌ Error in continuous workflow: {e}", exc_info=True)
                error_msg = error_message_template.format(error=str(e))
                render_agent_markdown(
                    error_msg.strip(),
                    "qx-director",
                    agent_color="#ff5f00"
                )
                # Continue with a new thread after error
                thread_id = str(uuid.uuid4())


# Note: No singleton management - each team mode session gets a fresh instance
# This ensures clean state without persisted conversations


def get_unified_workflow(config_manager: ConfigManager) -> UnifiedWorkflow:
    """Create a new unified workflow instance.
    
    Each call creates a fresh instance to ensure clean state.
    """
    logger.info("Creating new UnifiedWorkflow instance")
    return UnifiedWorkflow(config_manager)