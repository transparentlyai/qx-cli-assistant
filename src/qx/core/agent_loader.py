# src/qx/core/agent_loader.py
"""
Agent configuration loader with YAML parsing and template context injection.
Follows existing config patterns for hierarchical discovery and loading.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import logging

from qx.core.schemas import AgentConfig
from qx.core.paths import USER_HOME_DIR, _find_project_root

logger = logging.getLogger(__name__)


@dataclass
class AgentLoadResult:
    """Result of agent loading operation"""

    agent: Optional[AgentConfig] = None
    error: Optional[str] = None
    source_path: Optional[Path] = None

    @property
    def success(self) -> bool:
        return self.agent is not None


class AgentLoader:
    """
    Agent configuration loader that discovers and loads agents from YAML files.
    Follows hierarchical loading pattern similar to existing config management.
    """

    def __init__(self):
        self._agents_cache: Dict[str, AgentConfig] = {}
        self._discovered_agents: Optional[List[str]] = None
        self._last_discovery_cwd: Optional[str] = None  # Track CWD for cache invalidation

    def get_agent_search_paths(self, cwd: Optional[str] = None) -> List[Path]:
        """
        Get agent search paths in priority order (lowest to highest):
        1. System agents: /etc/qx/agents/
        2. User agents: ~/.config/qx/agents/
        3. Project agents: <project>/.Q/agents/
        4. Local agents: ./src/qx/agents/ (for development)
        """
        paths = []

        # System agents
        system_agents_path = Path("/etc/qx/agents")
        if system_agents_path.exists():
            paths.append(system_agents_path)

        # User agents
        user_agents_path = USER_HOME_DIR / ".config" / "qx" / "agents"
        if user_agents_path.exists():
            paths.append(user_agents_path)

        # Project agents
        if cwd:
            project_root = _find_project_root(cwd)
            if project_root:
                project_agents_path = project_root / ".Q" / "agents"
                if project_agents_path.exists():
                    paths.append(project_agents_path)

        # Local development agents (always include if exists)
        if cwd:
            local_agents_path = Path(cwd) / "src" / "qx" / "agents"
        else:
            local_agents_path = Path.cwd() / "src" / "qx" / "agents"

        if local_agents_path.exists():
            paths.append(local_agents_path)

        return paths

    def discover_agents(self, cwd: Optional[str] = None) -> List[str]:
        """
        Discover all available agent names from all search paths.
        Returns list of agent names (without .agent.yaml suffix).
        
        Args:
            cwd: Current working directory for project-specific agent discovery
        """
        # Use current working directory if not provided
        if cwd is None:
            cwd = os.getcwd()
            
        # Invalidate cache if working directory changed (for project-specific agents)
        if self._last_discovery_cwd != cwd:
            self._discovered_agents = None
            self._last_discovery_cwd = cwd
            
        # Return cached results if available
        if self._discovered_agents is not None:
            return self._discovered_agents

        agent_names = set()
        search_paths = self.get_agent_search_paths(cwd)

        for agents_dir in search_paths:
            try:
                if not agents_dir.exists():
                    continue

                for agent_file in agents_dir.glob("*.agent.yaml"):
                    # Extract agent name from filename (remove .agent.yaml)
                    agent_name = agent_file.stem.replace(".agent", "")
                    agent_names.add(agent_name)

            except Exception as e:
                logger.warning(f"Error discovering agents in {agents_dir}: {e}")

        self._discovered_agents = sorted(list(agent_names))
        return self._discovered_agents

    def find_agent_file(
        self, agent_name: str, cwd: Optional[str] = None
    ) -> Optional[Path]:
        """
        Find agent file by name, searching in priority order.
        Returns the highest priority path containing the agent.
        """
        search_paths = self.get_agent_search_paths(cwd)

        # Search in reverse order to get highest priority first
        for agents_dir in reversed(search_paths):
            agent_file = agents_dir / f"{agent_name}.agent.yaml"
            if agent_file.exists() and agent_file.is_file():
                return agent_file

        return None

    def load_agent_yaml(self, agent_path: Path) -> Dict[str, Any]:
        """
        Load and parse YAML agent configuration file.
        """
        try:
            with open(agent_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if not isinstance(data, dict):
                raise ValueError(
                    f"Agent file must contain a YAML object, got {type(data)}"
                )

            return data

        except Exception as e:
            raise ValueError(f"Failed to parse agent YAML: {e}")

    def inject_template_context(
        self, agent_data: Dict[str, Any], context: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Inject template context into agent configuration.
        Replaces placeholders like {user_context}, {project_context}, etc.
        """

        def replace_templates(obj):
            if isinstance(obj, str):
                # Replace template placeholders
                for key, value in context.items():
                    placeholder = "{" + key + "}"
                    obj = obj.replace(placeholder, value or "")
                return obj
            elif isinstance(obj, dict):
                return {k: replace_templates(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [replace_templates(item) for item in obj]
            else:
                return obj

        return replace_templates(agent_data)

    def validate_and_create_agent(self, agent_data: Dict[str, Any]) -> AgentConfig:
        """
        Validate agent data and create AgentConfig instance.
        """
        try:
            # Ensure model configuration exists with environment variable fallback
            if "model" not in agent_data:
                from qx.core.constants import DEFAULT_MODEL

                agent_data["model"] = {
                    "name": os.environ.get("QX_MODEL_NAME", DEFAULT_MODEL)
                }
            elif (
                isinstance(agent_data.get("model"), dict)
                and "name" not in agent_data["model"]
            ):
                from qx.core.constants import DEFAULT_MODEL

                agent_data["model"]["name"] = os.environ.get(
                    "QX_MODEL_NAME", DEFAULT_MODEL
                )

            # Create AgentConfig with validation
            return AgentConfig(**agent_data)
        except Exception as e:
            raise ValueError(f"Agent configuration validation failed: {e}")

    def load_agent(
        self,
        agent_name: str,
        context: Optional[Dict[str, str]] = None,
        cwd: Optional[str] = None,
    ) -> AgentLoadResult:
        """
        Load agent configuration by name with optional template context injection.

        Args:
            agent_name: Name of the agent (without .agent.yaml suffix)
            context: Template context for placeholder replacement
            cwd: Current working directory for path resolution

        Returns:
            AgentLoadResult with agent config or error information
        """
        try:
            # Check cache first
            cache_key = f"{agent_name}:{hash(str(context))}"
            if cache_key in self._agents_cache:
                return AgentLoadResult(
                    agent=self._agents_cache[cache_key],
                    source_path=self.find_agent_file(agent_name, cwd),
                )

            # Find agent file
            agent_path = self.find_agent_file(agent_name, cwd)
            if not agent_path:
                return AgentLoadResult(
                    error=f"Agent '{agent_name}' not found in any search path"
                )

            # Load YAML data
            agent_data = self.load_agent_yaml(agent_path)

            # Inject template context if provided
            if context:
                agent_data = self.inject_template_context(agent_data, context)

            # Validate and create agent config
            agent_config = self.validate_and_create_agent(agent_data)

            # Update metadata - preserve YAML name if specified, otherwise use filename
            if not agent_config.name or agent_config.name.strip() == "":
                agent_config.name = agent_name
            
            if not agent_config.execution.console.source_identifier:
                agent_config.execution.console.source_identifier = agent_name.upper()

            # Cache the result
            self._agents_cache[cache_key] = agent_config

            return AgentLoadResult(agent=agent_config, source_path=agent_path)

        except Exception as e:
            logger.error(f"Failed to load agent '{agent_name}': {e}")
            return AgentLoadResult(error=str(e))

    def load_default_agent(
        self, context: Optional[Dict[str, str]] = None, cwd: Optional[str] = None
    ) -> AgentLoadResult:
        """
        Load the default 'qx' agent configuration.
        This maintains backward compatibility with existing system.
        """
        return self.load_agent("qx", context=context, cwd=cwd)

    def reload_agent(
        self,
        agent_name: str,
        context: Optional[Dict[str, str]] = None,
        cwd: Optional[str] = None,
    ) -> AgentLoadResult:
        """
        Reload agent configuration, clearing cache for the agent.
        """
        # Clear cache for this agent
        cache_keys_to_remove = [
            key for key in self._agents_cache.keys() if key.startswith(f"{agent_name}:")
        ]
        for key in cache_keys_to_remove:
            del self._agents_cache[key]

        # Clear discovered agents cache to pick up new files
        self._discovered_agents = None

        return self.load_agent(agent_name, context=context, cwd=cwd)

    def clear_cache(self):
        """Clear all cached agent configurations."""
        self._agents_cache.clear()
        self._discovered_agents = None
        self._last_discovery_cwd = None
        
    def refresh_discovery(self, cwd: Optional[str] = None) -> List[str]:
        """Force refresh of agent discovery, useful when project context changes."""
        self._discovered_agents = None
        self._last_discovery_cwd = None
        return self.discover_agents(cwd)

    def get_agent_info(
        self, agent_name: str, cwd: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get basic information about an agent without fully loading it.
        """
        agent_path = self.find_agent_file(agent_name, cwd)
        if not agent_path:
            return None

        try:
            agent_data = self.load_agent_yaml(agent_path)
            return {
                "name": agent_name,
                "description": agent_data.get("description", "No description"),
                "version": agent_data.get("version", "Unknown"),
                "tools": agent_data.get("tools", []),
                "model": agent_data.get("model", {}),
                "path": str(agent_path),
                "execution_mode": agent_data.get("execution", {}).get(
                    "mode", "interactive"
                ),
            }
        except Exception as e:
            logger.error(f"Failed to get info for agent '{agent_name}': {e}")
            return None


# Global singleton instance
_agent_loader = None


def get_agent_loader() -> AgentLoader:
    """Get the global AgentLoader instance."""
    global _agent_loader
    if _agent_loader is None:
        _agent_loader = AgentLoader()
    return _agent_loader
