"""
LangGraph supervisor system for qx multi-agent workflows.

This module integrates LangGraph with qx's existing agent system, using the
official langgraph-supervisor library for team coordination.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import MessagesState
from langgraph_supervisor import create_supervisor

from qx.core.team_manager import get_team_manager, TeamManager, TeamMember
from qx.core.config_manager import ConfigManager
from qx.core.agent_manager import get_agent_manager
from qx.core.llm import QXLLMAgent
from qx.cli.theme import themed_console

logger = logging.getLogger(__name__)


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
    
    async def process_with_team(self, user_input: str) -> str:
        """Process a user request using the team workflow with existing qx agents."""
        try:
            team_members = self.team_manager.get_team_members()
            if not team_members:
                return "No team members available. Processing with main agent."
            
            # Show that we're using team workflow
            themed_console.print(
                f"🤖 Processing with team ({len(team_members)} agents available)...", 
                style="dim cyan"
            )
            
            # Use supervisor to delegate the task
            selected_agents = self.team_manager.select_best_agents_for_task(user_input, max_agents=2)
            
            if not selected_agents:
                themed_console.print("📝 No suitable team agents found, handling directly...", style="dim yellow")
                result = await self.main_llm_agent.run(user_input)
                return result.output if hasattr(result, 'output') else str(result)
            
            # Process with selected agents sequentially
            agent_results = {}
            for agent_name in selected_agents:
                if agent_name in team_members:
                    team_member = team_members[agent_name]
                    wrapper = self._create_agent_wrapper(agent_name, team_member)
                    
                    # Create state for the agent
                    state = {
                        "messages": [HumanMessage(content=user_input)]
                    }
                    
                    # Execute agent
                    result = await wrapper.invoke(state)
                    if result and "messages" in result and result["messages"]:
                        agent_results[agent_name] = result["messages"][-1].content
            
            # Synthesize results if multiple agents were used
            if len(agent_results) > 1:
                synthesis_prompt = f"""
Task: {user_input}

Agent Results:
"""
                for agent_name, result in agent_results.items():
                    synthesis_prompt += f"\n{agent_name}: {result}\n"
                    
                synthesis_prompt += """
Please synthesize these agent results into a comprehensive, unified response that addresses the original task.
Focus on combining the insights and removing any redundancy.
"""
                
                # Use main agent to synthesize
                result = await self.main_llm_agent.run(synthesis_prompt)
                return result.output if hasattr(result, 'output') else str(result)
            
            # Return single agent result
            elif agent_results:
                return list(agent_results.values())[0]
            
            # Fallback
            themed_console.print("📝 No agent results, handling directly...", style="dim yellow")
            result = await self.main_llm_agent.run(user_input)
            return result.output if hasattr(result, 'output') else str(result)
            
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