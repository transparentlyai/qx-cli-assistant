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
from qx.core.workflow_context import workflow_execution_context, get_workflow_context
from qx.core.interrupt_bridge import get_interrupt_bridge
from qx.core.langgraph_tool_adapter import get_tool_adapter
from qx.core.langgraph_model_adapter import create_langchain_model
from qx.core.langgraph_interrupt_adapter import get_interrupt_adapter
from qx.core.llm_utils import initialize_agent_with_mcp
from qx.core.mcp_manager import MCPManager

logger = logging.getLogger(__name__)


class UnifiedWorkflowV2:
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
                
            # Create all agents from YAML configurations
            agents = []
            for agent_name, team_member in team_members.items():
                agent = await self.create_agent_from_yaml(agent_name, team_member)
                if agent:
                    agents.append(agent)
                    
            if not agents:
                logger.error("No agents could be created")
                return False
                
            logger.info(f"Created {len(agents)} agents from team configuration")
            
            # Create supervisor prompt that handles routing
            supervisor_prompt = """
            You are a team coordinator managing multiple specialized agents.
            
            Routing guidelines:
            - For greetings, simple questions, or general conversation: Handle directly
            - For programming tasks: Route to agents with coding capabilities
            - For research or analysis: Route to agents with research capabilities
            - For complex tasks: Break down and route to appropriate specialists
            
            Always maintain conversation context and ensure smooth handoffs between agents.
            When an agent completes a task, check if the user is satisfied before continuing.
            """
            
            # Get the first agent's model for supervisor
            # We need to get the langchain model from the first team member
            first_agent_name = list(team_members.keys())[0]
            first_team_member = team_members[first_agent_name]
            
            # Create a supervisor agent config
            supervisor_config = first_team_member.agent_config
            supervisor_config.name = "supervisor"
            
            # Get MCP manager from config manager
            mcp_manager = getattr(self.config_manager, 'mcp_manager', None)
            if not mcp_manager:
                # Create a minimal MCP manager if needed
                console = getattr(self.config_manager, 'console', self.console_manager.console)
                task_group = getattr(self.config_manager, 'task_group', None)
                mcp_manager = MCPManager(console, task_group)
            
            first_llm_agent = await initialize_agent_with_mcp(
                mcp_manager=mcp_manager,
                agent_config=supervisor_config
            )
            supervisor_model = create_langchain_model(first_llm_agent) if first_llm_agent else None
            
            if not supervisor_model:
                logger.error("Failed to create supervisor model")
                return False
            
            # Create the supervisor workflow
            workflow = create_supervisor(
                agents,
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
        
        # Initialize with empty input to let supervisor ask for input
        thread_id = str(uuid.uuid4())
        
        while True:
            try:
                # Process with current thread
                response = await self.process_input("", thread_id)
                
                # Check for exit conditions
                if "goodbye" in response.lower() or "exit" in response.lower():
                    logger.info("👋 User requested exit")
                    break
                    
                # Continue with same thread for context
                await asyncio.sleep(0.1)  # Small delay for system stability
                
            except KeyboardInterrupt:
                logger.info("⏹️ Workflow interrupted by user")
                break
            except Exception as e:
                logger.error(f"❌ Error in continuous workflow: {e}", exc_info=True)
                break


# Singleton instance management
_unified_workflow_instance: Optional[UnifiedWorkflowV2] = None


def get_unified_workflow_v2(config_manager: ConfigManager) -> UnifiedWorkflowV2:
    """Get or create the unified workflow instance."""
    global _unified_workflow_instance
    
    if _unified_workflow_instance is None:
        _unified_workflow_instance = UnifiedWorkflowV2(config_manager)
        logger.info("Created new UnifiedWorkflowV2 instance")
    
    return _unified_workflow_instance