"""
Team management system for qx multi-agent workflows.

This module manages a user's team of agents and coordinates their collaboration
through LangGraph workflows.
"""

import asyncio
import json
import logging
import os
import re
import time
from typing import Any, Dict, List, Optional, Set
from pathlib import Path

from qx.core.config_manager import ConfigManager
from qx.core.agent_manager import get_agent_manager
from qx.core.schemas import AgentConfig
from qx.core.console_manager import get_console_manager
from qx.cli.theme import themed_console

logger = logging.getLogger(__name__)


class TeamMember:
    """Represents an agent that's part of the user's team."""
    
    def __init__(self, agent_name: str, agent_config: AgentConfig, capabilities: List[str]):
        self.agent_name = agent_name
        self.agent_config = agent_config
        self.capabilities = capabilities
        self.role_summary = self._extract_role_summary()
        self.console_manager = get_console_manager()
        self.instance_count = 1  # Default to 1 instance
        
    def _extract_role_summary(self) -> str:
        """Extract a brief summary of the agent's role."""
        role_text = self.agent_config.role or ""
        # Take first sentence or first 100 characters
        first_sentence = role_text.split('.')[0]
        if len(first_sentence) > 100:
            return first_sentence[:97] + "..."
        return first_sentence

    def can_handle_task(self, task_description: str) -> float:
        """
        Calculate how well this agent can handle a given task.
        Returns a score between 0.0 and 1.0.
        """
        task_lower = task_description.lower()
        score = 0.0
        
        # Check capabilities
        for capability in self.capabilities:
            if capability.lower() in task_lower:
                score += 0.3
                
        # Check role description
        role_words = self.agent_config.role.lower().split() if self.agent_config.role else []
        for word in task_lower.split():
            if word in role_words:
                score += 0.1
                
        # Check agent description
        if self.agent_config.description:
            desc_words = self.agent_config.description.lower().split()
            for word in task_lower.split():
                if word in desc_words:
                    score += 0.1
        
        # Give software engineering agents a base score for code/file tasks
        code_keywords = ['create', 'write', 'build', 'develop', 'implement', 'file', 'code', 'script', 'html', 'python', 'javascript']
        software_capabilities = ['frontend', 'backend', 'file_management', 'automation', 'testing']
        
        task_has_code_keywords = any(keyword in task_lower for keyword in code_keywords)
        agent_has_software_capabilities = any(cap in self.capabilities for cap in software_capabilities)
        
        if task_has_code_keywords and agent_has_software_capabilities:
            score = max(score, 0.5)  # Give at least 0.5 score for software engineering tasks
        
        return min(score, 1.0)



class TeamManager:
    """Manages the user's team of agents and their collaboration."""
    
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self._team_members: Dict[str, TeamMember] = {}
        self._load_team_from_storage()
        
    def _get_team_storage_path(self) -> Path:
        """Get the path where team composition is stored."""
        # Store in the current project directory if possible, otherwise user config
        project_path = Path.cwd() / ".Q" / "config" / "team.json"
        user_path = Path.home() / ".config" / "qx" / "team.json"
        
        # Create directories if they don't exist
        project_path.parent.mkdir(parents=True, exist_ok=True)
        user_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Prefer project-specific team composition
        return project_path

    def _get_teams_storage_path(self) -> Path:
        """Get the path where all saved teams are stored."""
        # Store in the current project directory if possible, otherwise user config
        project_path = Path.cwd() / ".Q" / "config" / "teams.json"
        user_path = Path.home() / ".config" / "qx" / "teams.json"
        
        # Create directories if they don't exist
        project_path.parent.mkdir(parents=True, exist_ok=True)
        user_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Prefer project-specific teams storage
        return project_path

    def _load_team_from_storage(self, team_name: Optional[str] = None):
        """Load the team composition from persistent storage."""
        if team_name:
            # Load from saved teams
            self._load_saved_team(team_name)
        else:
            # Load current team
            team_file = self._get_team_storage_path()
            if not team_file.exists():
                return
                
            try:
                with open(team_file, 'r') as f:
                    team_data = json.load(f)
                    
                # Clear existing team first
                self._team_members.clear()
                    
                # Reconstruct team members
                agent_manager = get_agent_manager()
                agents_data = team_data.get('agents', {})
                
                # Load agents with instance counts
                for agent_name, agent_info in agents_data.items():
                    instance_count = agent_info.get('instance_count', 1)
                    self._load_agent_member(agent_manager, agent_name, instance_count)
                        
            except (json.JSONDecodeError, FileNotFoundError) as e:
                logger.warning(f"Failed to load team from {team_file}: {e}")

    def _load_saved_team(self, team_name: str):
        """Load a specific saved team from teams.json."""
        teams_file = self._get_teams_storage_path()
        if not teams_file.exists():
            return False
            
        try:
            with open(teams_file, 'r') as f:
                all_teams = json.load(f)
                
            if team_name not in all_teams.get('teams', {}):
                return False
                
            # Clear existing team first
            self._team_members.clear()
                
            # Load the specific team
            team_data = all_teams['teams'][team_name]
            agent_manager = get_agent_manager()
            
            for agent_name, agent_info in team_data.get('agents', {}).items():
                instance_count = agent_info.get('instance_count', 1)
                self._load_agent_member(agent_manager, agent_name, instance_count)
                
            return True
                
        except (json.JSONDecodeError, FileNotFoundError) as e:
            logger.warning(f"Failed to load saved team {team_name} from {teams_file}: {e}")
            return False
    
    def _load_agent_member(self, agent_manager, agent_name: str, instance_count: int):
        """Helper method to load a single agent member."""
        try:
            agent_config = agent_manager.get_agent_config(agent_name, cwd=os.getcwd())
            if agent_config:
                capabilities = self._infer_capabilities(agent_config)
                team_member = TeamMember(agent_name, agent_config, capabilities)
                team_member.instance_count = instance_count
                self._team_members[agent_name] = team_member
                logger.info(f"Loaded team member: {agent_name} ({instance_count} instances)")
        except Exception as e:
            logger.warning(f"Failed to load team member {agent_name}: {e}")

    def _save_team_to_storage(self):
        """Save the current team composition to persistent storage."""
        team_file = self._get_team_storage_path()
        
        # Include instance counts in saved data
        agents_data = {}
        for agent_name, member in self._team_members.items():
            agents_data[agent_name] = {
                'instance_count': getattr(member, 'instance_count', 1)
            }
        
        team_data = {
            'agents': agents_data
        }
        
        try:
            with open(team_file, 'w') as f:
                json.dump(team_data, f, indent=2)
            logger.info(f"Saved current team to {team_file}")
        except Exception as e:
            logger.error(f"Failed to save team to {team_file}: {e}")

    def _save_team_to_teams_file(self, team_name: str):
        """Save the current team to the teams.json file."""
        teams_file = self._get_teams_storage_path()
        
        # Load existing teams or create new structure
        all_teams = {'teams': {}}
        if teams_file.exists():
            try:
                with open(teams_file, 'r') as f:
                    all_teams = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                pass  # Use default structure
        
        # Ensure teams key exists
        if 'teams' not in all_teams:
            all_teams['teams'] = {}
        
        # Prepare team data
        agents_data = {}
        for agent_name, member in self._team_members.items():
            agents_data[agent_name] = {
                'instance_count': getattr(member, 'instance_count', 1)
            }
        
        # Save team with metadata
        all_teams['teams'][team_name] = {
            'agents': agents_data,
            'saved_at': int(time.time())
        }
        
        try:
            with open(teams_file, 'w') as f:
                json.dump(all_teams, f, indent=2)
            logger.info(f"Saved team '{team_name}' to {teams_file}")
        except Exception as e:
            logger.error(f"Failed to save team '{team_name}' to {teams_file}: {e}")
            raise

    def _infer_capabilities(self, agent_config: AgentConfig) -> List[str]:
        """Infer capabilities from agent configuration."""
        capabilities = []
        
        # Extract from description and role
        text_content = f"{agent_config.description or ''} {agent_config.role or ''}"
        text_lower = text_content.lower()
        
        # Common capability patterns
        capability_patterns = {
            'code_review': ['code review', 'review code', 'security', 'audit'],
            'documentation': ['documentation', 'docs', 'writing', 'markdown'],
            'devops': ['devops', 'deployment', 'infrastructure', 'automation'],
            'data_processing': ['data', 'analysis', 'processing', 'csv', 'json'],
            'testing': ['test', 'testing', 'quality assurance', 'qa'],
            'frontend': ['frontend', 'ui', 'react', 'vue', 'angular'],
            'backend': ['backend', 'api', 'server', 'database'],
            'security': ['security', 'vulnerability', 'audit', 'penetration'],
        }
        
        for capability, patterns in capability_patterns.items():
            if any(pattern in text_lower for pattern in patterns):
                capabilities.append(capability)
                
        # Add tool-based capabilities
        if agent_config.tools:
            for tool in agent_config.tools:
                if 'execute_shell' in tool:
                    capabilities.append('automation')
                if 'web_fetch' in tool:
                    capabilities.append('research')
                if 'write_file' in tool:
                    capabilities.append('file_management')
                    
        return capabilities

    async def add_agent(self, agent_name: str, instance_count: int = 1) -> bool:
        """Add an agent to the team with specified instance count."""
        # Get the agent configuration first to check max_instances
        agent_manager = get_agent_manager()
        agent_config = agent_manager.get_agent_config(agent_name, cwd=os.getcwd())
        
        if not agent_config:
            themed_console.print(f"Agent '{agent_name}' not found", style="error")
            return False
        
        # Check max_instances constraint
        max_instances = getattr(agent_config, 'max_instances', 1)
        
        # Check current instance count
        current_instances = 0
        if agent_name in self._team_members:
            current_instances = getattr(self._team_members[agent_name], 'instance_count', 1)
        
        total_instances = current_instances + instance_count
        if total_instances > max_instances:
            themed_console.print(
                f"Cannot add {instance_count} instances. Agent '{agent_name}' allows maximum {max_instances} instances (currently has {current_instances}).",
                style="error"
            )
            return False
            
        # Infer capabilities
        capabilities = self._infer_capabilities(agent_config)
        
        if agent_name in self._team_members:
            # Update existing agent with new instance count
            self._team_members[agent_name].instance_count = total_instances
            themed_console.print(
                f"✓ Updated {agent_name} to {total_instances} instances", 
                style="success"
            )
        else:
            # Add new agent to team
            team_member = TeamMember(agent_name, agent_config, capabilities)
            team_member.instance_count = instance_count
            self._team_members[agent_name] = team_member
            
            if instance_count == 1:
                themed_console.print(f"✓ Added {agent_name} to your team", style="success")
            else:
                themed_console.print(f"✓ Added {agent_name} to your team ({instance_count} instances)", style="success")
        
        if capabilities:
            themed_console.print(f"  Capabilities: {', '.join(capabilities)}", style="dim white")
        
        # Save to storage
        self._save_team_to_storage()
        
        return True

    async def remove_agent(self, agent_name: str) -> bool:
        """Remove an agent from the team."""
        if agent_name not in self._team_members:
            themed_console.print(f"Agent '{agent_name}' is not in your team", style="warning")
            return False
            
        del self._team_members[agent_name]
        self._save_team_to_storage()
        
        themed_console.print(f"✓ Removed {agent_name} from your team", style="success")
        return True

    def clear_team(self):
        """Remove all agents from the team."""
        count = len(self._team_members)
        self._team_members.clear()
        self._save_team_to_storage()
        
        themed_console.print(f"✓ Cleared team ({count} agents removed)", style="success")

    def get_team_status(self) -> Dict[str, Any]:
        """Get the current team status."""
        total_instances = sum(getattr(member, 'instance_count', 1) for member in self._team_members.values())
        
        return {
            'member_count': len(self._team_members),
            'total_instances': total_instances,
            'members': {
                name: {
                    'capabilities': member.capabilities,
                    'role_summary': member.role_summary,
                    'description': member.agent_config.description,
                    'instance_count': getattr(member, 'instance_count', 1),
                    'max_instances': getattr(member.agent_config, 'max_instances', 1)
                }
                for name, member in self._team_members.items()
            }
        }

    def has_team(self) -> bool:
        """Check if the user has any team members."""
        return len(self._team_members) > 0

    def select_best_agents_for_task(self, task_description: str, max_agents: int = 3) -> List[str]:
        """
        Select the best agents from the team to handle a given task.
        Returns a list of agent names sorted by their suitability.
        """
        if not self._team_members:
            return []
            
        # Score each agent
        agent_scores = []
        for agent_name, member in self._team_members.items():
            score = member.can_handle_task(task_description)
            if score > 0.1:  # Only include agents with some relevance
                agent_scores.append((agent_name, score))
                
        # Sort by score and return top agents
        agent_scores.sort(key=lambda x: x[1], reverse=True)
        return [agent_name for agent_name, _ in agent_scores[:max_agents]]

    def get_team_members(self) -> Dict[str, TeamMember]:
        """Get all current team members."""
        return self._team_members.copy()

    def save_team(self, team_name: str) -> bool:
        """Save the current team with a given name."""
        if not team_name.strip():
            themed_console.print("Team name cannot be empty", style="error")
            return False
        
        # Validate team name (no special characters except hyphens and underscores)
        if not re.match(r'^[a-zA-Z0-9_-]+$', team_name):
            themed_console.print("Team name can only contain letters, numbers, hyphens, and underscores", style="error")
            return False
        
        if not self._team_members:
            themed_console.print("No team to save", style="warning")
            return False
        
        try:
            # Check if team already exists
            existing_teams = self.list_saved_teams()
            if team_name in existing_teams:
                themed_console.print(f"Team '{team_name}' already exists and will be overwritten", style="warning")
            
            self._save_team_to_teams_file(team_name)
            member_count = len(self._team_members)
            total_instances = sum(getattr(member, 'instance_count', 1) for member in self._team_members.values())
            themed_console.print(f"✓ Saved team '{team_name}' ({member_count} agents, {total_instances} instances)", style="success")
            return True
        except Exception as e:
            themed_console.print(f"Failed to save team '{team_name}': {e}", style="error")
            return False

    def load_team(self, team_name: str) -> bool:
        """Load a saved team by name."""
        if not team_name.strip():
            themed_console.print("Team name cannot be empty", style="error")
            return False
        
        # Check if team exists in teams.json
        saved_teams = self.list_saved_teams()
        if team_name not in saved_teams:
            themed_console.print(f"Team '{team_name}' not found", style="error")
            return False
        
        try:
            success = self._load_saved_team(team_name)
            
            if not success:
                themed_console.print(f"Team '{team_name}' not found", style="error")
                return False
                
            member_count = len(self._team_members)
            total_instances = sum(getattr(member, 'instance_count', 1) for member in self._team_members.values())
            
            if member_count > 0:
                themed_console.print(f"✓ Loaded team '{team_name}' ({member_count} agents, {total_instances} instances)", style="success")
                
                # Show loaded members
                for agent_name, member in self._team_members.items():
                    instance_count = getattr(member, 'instance_count', 1)
                    if instance_count == 1:
                        themed_console.print(f"  - {agent_name}", style="dim blue")
                    else:
                        themed_console.print(f"  - {agent_name} ({instance_count} instances)", style="dim blue")
                
                # Save as current team
                self._save_team_to_storage()
                
                # Team loaded successfully
                
                return True
            else:
                themed_console.print(f"Team '{team_name}' is empty", style="warning")
                return False
                
        except Exception as e:
            themed_console.print(f"Failed to load team '{team_name}': {e}", style="error")
            return False

    def list_saved_teams(self) -> List[str]:
        """List all saved teams."""
        teams = []
        try:
            # Check teams.json file
            teams_file = self._get_teams_storage_path()
            if teams_file.exists():
                with open(teams_file, 'r') as f:
                    all_teams = json.load(f)
                    teams = list(all_teams.get('teams', {}).keys())
            
                            
        except Exception as e:
            logger.warning(f"Failed to list saved teams: {e}")
        
        return sorted(teams)

    def create_team(self, team_name: str) -> bool:
        """Create a new empty team with the given name."""
        if not team_name.strip():
            themed_console.print("Team name cannot be empty", style="error")
            return False
        
        # Validate team name (no special characters except hyphens and underscores)
        if not re.match(r'^[a-zA-Z0-9_-]+$', team_name):
            themed_console.print("Team name can only contain letters, numbers, hyphens, and underscores", style="error")
            return False
        
        # Check if team already exists
        existing_teams = self.list_saved_teams()
        if team_name in existing_teams:
            themed_console.print(f"Team '{team_name}' already exists. Use /team-load to load it or /team-save to overwrite.", style="error")
            return False
        
        try:
            # Clear current team to create empty team
            self._team_members.clear()
            
            # Save empty team to teams.json
            self._save_team_to_teams_file(team_name)
            
            # Also update current team storage
            self._save_team_to_storage()
            
            themed_console.print(f"✓ Created empty team '{team_name}'", style="success")
            themed_console.print("Use /team-add-member <agent> to add agents to your team", style="dim white")
            return True
            
        except Exception as e:
            themed_console.print(f"Failed to create team '{team_name}': {e}", style="error")
            return False


    def reload_from_storage(self):
        """Reload team from persistent storage, useful when team files change."""
        self._team_members.clear()
        self._load_team_from_storage()
        logger.info("Team reloaded from storage")


# Global team manager instance
_team_manager: Optional[TeamManager] = None


def get_team_manager(config_manager: ConfigManager) -> TeamManager:
    """Get the global team manager instance."""
    global _team_manager
    if _team_manager is None:
        _team_manager = TeamManager(config_manager)
    return _team_manager


def reset_team_manager():
    """Reset the global team manager instance, forcing it to reload from storage."""
    global _team_manager
    _team_manager = None