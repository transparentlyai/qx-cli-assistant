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

from langchain_core.messages import HumanMessage, AIMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.store.memory import InMemoryStore

# Import langgraph-supervisor components
from langgraph_supervisor import create_supervisor
from langgraph.prebuilt import create_react_agent
from langgraph.types import interrupt

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


class UnifiedWorkflow:
    """
    Simplified unified workflow using langgraph-supervisor library.
    """
    
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.team_manager = get_team_manager(config_manager)
        self.console_manager = get_console_manager()
        
        # Workflow components
        self.workflow_app = None
        self.checkpointer = InMemorySaver()
        self.store = InMemoryStore()
        
        # Track current execution
        self.current_thread_id = None
        
    async def create_agent_from_yaml(self, agent_name: str, team_member: TeamMember):
        """Create a LangGraph agent from YAML configuration."""
        agent_config = team_member.agent_config
        
        # Get the agent's role and instructions
        role = getattr(agent_config, 'role', '') or ''
        instructions = getattr(agent_config, 'instructions', '') or ''
        system_prompt = getattr(agent_config, 'system_prompt', '') or ''
        
        # Combine into agent prompt
        agent_prompt = system_prompt or f"{role}\n\n{instructions}"
        
        # Get tools for this agent using the adapter
        tool_adapter = get_tool_adapter()
        tools = tool_adapter.load_tools_for_agent(agent_name)
        
        # Create liteLLM wrapper for this agent
        # Get MCP manager from config manager
        mcp_manager = getattr(self.config_manager, 'mcp_manager', None)
        if not mcp_manager:
            # Create a minimal MCP manager if needed
            console = getattr(self.config_manager, 'console', self.console_manager.console)
            task_group = getattr(self.config_manager, 'task_group', None)
            mcp_manager = MCPManager(console, task_group)
        
        llm_agent = await initialize_agent_with_mcp(
            mcp_manager=mcp_manager,
            agent_config=agent_config
        )
        
        if not llm_agent:
            logger.error(f"Failed to initialize LLM agent for {agent_name}")
            return None
            
        # Create LangChain-compatible model using adapter
        langchain_model = create_langchain_model(llm_agent)
            
        # Create the agent using langgraph-supervisor
        agent = create_react_agent(
            model=langchain_model,
            tools=tools,
            name=agent_name,
            prompt=agent_prompt
        )
        logger.info(f"✅ Created agent '{agent_name}' using langgraph-supervisor")
            
        return agent
    
    
    async def build_team_workflow(self):
        """Build the unified workflow using langgraph-supervisor."""
        try:
            logger.info("🏗️ Building unified workflow with langgraph-supervisor")
            
            team_members = self.team_manager.get_team_members()
            if not team_members:
                logger.warning("No team members found")
                return False
                
            # Separate qx-director from other agents
            director_config = None
            director_member = None
            specialist_agents = []
            
            for agent_name, team_member in team_members.items():
                if agent_name.lower() == "qx-director":
                    director_config = team_member.agent_config
                    director_member = team_member
                else:
                    # Create specialist agents (not the director)
                    agent = await self.create_agent_from_yaml(agent_name, team_member)
                    if agent:
                        specialist_agents.append(agent)
                    
            if not director_config:
                logger.error("qx-director not found in team configuration")
                return False
                
            if not specialist_agents:
                logger.error("No specialist agents could be created")
                return False
                
            logger.info(f"Created {len(specialist_agents)} specialist agents")
            
            # Log available agents for delegation
            agent_names = [agent.name for agent in specialist_agents if hasattr(agent, 'name')]
            logger.info(f"Available agents for delegation: {', '.join(agent_names)}")
            
            # Build team context with available agents
            team_context = "## Available Specialist Agents:\n\n"
            for agent in specialist_agents:
                if hasattr(agent, 'name'):
                    agent_name = agent.name
                    # Get agent description from team member config
                    for tm_name, tm in team_members.items():
                        if tm_name == agent_name:
                            desc = getattr(tm.agent_config, 'description', 'Specialist agent')
                            team_context += f"- **transfer_to_{agent_name}**: {desc}\n"
                            break
            
            # Get supervisor prompt from qx-director's configuration
            director_role = getattr(director_config, 'role', '') or ''
            director_instructions = getattr(director_config, 'instructions', '') or ''
            
            # Replace {team_members} placeholder with actual team context
            director_instructions = director_instructions.replace('{team_members}', team_context)
            
            # Use director's role and instructions as supervisor prompt
            supervisor_prompt = f"{director_role}\n\n{director_instructions}\n\n{team_context}"
            
            logger.info("Using qx-director configuration for supervisor")
            
            # Get MCP manager from config manager
            mcp_manager = getattr(self.config_manager, 'mcp_manager', None)
            if not mcp_manager:
                # Create a minimal MCP manager if needed
                console = getattr(self.config_manager, 'console', self.console_manager.console)
                task_group = getattr(self.config_manager, 'task_group', None)
                mcp_manager = MCPManager(console, task_group)
            
            # Create supervisor model using qx-director configuration
            supervisor_llm_agent = await initialize_agent_with_mcp(
                mcp_manager=mcp_manager,
                agent_config=director_config
            )
            supervisor_model = create_langchain_model(supervisor_llm_agent) if supervisor_llm_agent else None
            
            if not supervisor_model:
                logger.error("Failed to create supervisor model")
                return False
            
            # Create the supervisor workflow with specialist agents only
            workflow = create_supervisor(
                specialist_agents,  # Only specialist agents, not the director
                model=supervisor_model,
                prompt=supervisor_prompt,
                output_mode="last_message"  # Only return the last message
            )
            
            # Compile with checkpointer for conversation memory
            self.workflow_app = workflow.compile(
                checkpointer=self.checkpointer,
                store=self.store
            )
            logger.info("✅ Workflow compiled successfully with langgraph-supervisor")
                
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to build workflow: {e}", exc_info=True)
            return False
    
    async def process_input(self, user_input: str = "", thread_id: Optional[str] = None) -> str:
        """Process user input through the workflow."""
        if not self.workflow_app:
            # Build workflow if not already built
            success = await self.build_team_workflow()
            if not success:
                return "Failed to initialize team workflow"
                
        # Use existing thread or create new one
        if not thread_id:
            thread_id = self.current_thread_id or str(uuid.uuid4())
            self.current_thread_id = thread_id
            
        try:
            # Create the input message
            if user_input:
                messages = [HumanMessage(content=user_input)]
            else:
                # Empty input - supervisor will ask for input
                messages = []
                
            # Configure the execution
            config = {
                "configurable": {
                    "thread_id": thread_id
                }
            }
            
            # Execute the workflow
            logger.info(f"🚀 Executing workflow with thread_id: {thread_id}")
            result = await self.workflow_app.ainvoke(
                {"messages": messages},
                config=config
            )
            
            # Extract the response
            if "messages" in result and result["messages"]:
                last_message = result["messages"][-1]
                if hasattr(last_message, "content"):
                    return last_message.content
                else:
                    return str(last_message)
            else:
                return "No response generated"
                
        except Exception as e:
            logger.error(f"❌ Workflow execution error: {e}", exc_info=True)
            return f"Error during workflow execution: {str(e)}"
    
    async def start_continuous_workflow(self):
        """Start the workflow in continuous mode for team interaction."""
        logger.info("🎯 Starting continuous workflow mode")
        
        # Initialize thread for conversation
        thread_id = str(uuid.uuid4())
        
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
        
        while True:
            try:
                # Display prompt from the director
                render_agent_markdown(
                    "**What would you like me to help you with?**",
                    "qx-director",
                    agent_color="#ff5f00"
                )
                
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
                        "Goodbye! 👋",
                        "qx-director",
                        agent_color="#ff5f00"
                    )
                    break
                
                # Process user input through the workflow
                response = await self.process_input(user_input, thread_id)
                
                # Response is already displayed by the agents
                # Just continue the loop for next input
                
            except KeyboardInterrupt:
                logger.info("⏹️ Workflow interrupted by user")
                render_agent_markdown(
                    "Workflow interrupted. Goodbye! 👋",
                    "qx-director",
                    agent_color="#ff5f00"
                )
                break
            except EOFError:
                logger.info("👋 User requested exit (Ctrl+D)")
                break
            except Exception as e:
                logger.error(f"❌ Error in continuous workflow: {e}", exc_info=True)
                render_agent_markdown(
                    f"**Error:** {str(e)}\n\nPlease try again.",
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