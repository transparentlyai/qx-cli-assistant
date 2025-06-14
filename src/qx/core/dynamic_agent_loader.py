"""
Dynamic Agent Loader for QX Unified LangGraph Workflow.

This module provides enhanced agent loading capabilities including:
- Lazy agent initialization for better performance
- Agent capability detection and caching
- Dynamic agent configuration updates
- Workflow-specific agent optimizations
- Agent health monitoring and recovery
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass
from enum import Enum

from qx.core.team_manager import TeamMember, TeamManager
from qx.core.config_manager import ConfigManager
from qx.core.llm import QXLLMAgent

logger = logging.getLogger(__name__)


class AgentStatus(Enum):
    """Agent status enumeration."""
    NOT_LOADED = "not_loaded"
    INITIALIZING = "initializing"
    READY = "ready"
    ERROR = "error"
    DEPRECATED = "deprecated"


@dataclass
class AgentCapability:
    """Represents an agent's capability or skill."""
    name: str
    description: str
    keywords: List[str]
    confidence: float = 1.0  # 0.0 to 1.0
    
    def matches_task(self, task_description: str) -> float:
        """Calculate how well this capability matches a task description."""
        task_lower = task_description.lower()
        score = 0.0
        
        # Check name match
        if self.name.lower() in task_lower:
            score += 0.5
            
        # Check keyword matches
        keyword_matches = sum(1 for keyword in self.keywords if keyword.lower() in task_lower)
        if keyword_matches > 0:
            score += (keyword_matches / len(self.keywords)) * 0.4
            
        # Apply confidence weighting
        return score * self.confidence


@dataclass
class LoadedAgent:
    """Container for a loaded agent with metadata."""
    name: str
    agent: QXLLMAgent
    team_member: TeamMember
    status: AgentStatus
    capabilities: List[AgentCapability]
    load_time: float
    last_used: float
    usage_count: int = 0
    error_count: int = 0
    
    def get_color(self) -> Optional[str]:
        """Get agent color for UI styling."""
        return getattr(self.team_member.agent_config, 'color', None)
    
    def record_usage(self):
        """Record agent usage for analytics."""
        self.usage_count += 1
        self.last_used = time.time()
    
    def record_error(self):
        """Record agent error for monitoring."""
        self.error_count += 1
        logger.warning(f"⚠️ Agent {self.name} error count: {self.error_count}")


class DynamicAgentLoader:
    """
    Enhanced agent loader with dynamic capabilities, lazy loading, and optimization.
    
    Key features:
    - Lazy initialization: Agents are only loaded when needed
    - Capability detection: Automatically detect agent capabilities from config
    - Smart routing: Route tasks to best-suited agents
    - Performance monitoring: Track agent usage and performance
    - Error recovery: Handle agent failures gracefully
    """
    
    def __init__(self, config_manager: ConfigManager, team_manager: TeamManager):
        self.config_manager = config_manager
        self.team_manager = team_manager
        
        # Agent storage and tracking
        self._loaded_agents: Dict[str, LoadedAgent] = {}
        self._agent_locks: Dict[str, asyncio.Lock] = {}
        self._capability_cache: Dict[str, List[AgentCapability]] = {}
        
        # Performance metrics
        self.metrics = {
            "total_loads": 0,
            "load_failures": 0,
            "cache_hits": 0,
            "avg_load_time": 0.0,
            "agent_usage": {}
        }
        
        logger.info("🔧 DynamicAgentLoader initialized")
    
    async def get_agent(self, agent_name: str) -> Optional[LoadedAgent]:
        """
        Get an agent, loading it lazily if needed.
        
        Args:
            agent_name: Name of the agent to load
            
        Returns:
            LoadedAgent instance or None if loading failed
        """
        # Check if agent is already loaded
        if agent_name in self._loaded_agents:
            loaded_agent = self._loaded_agents[agent_name]
            if loaded_agent.status == AgentStatus.READY:
                loaded_agent.record_usage()
                self.metrics["cache_hits"] += 1
                logger.debug(f"🎯 Cache hit for agent: {agent_name}")
                return loaded_agent
            elif loaded_agent.status == AgentStatus.ERROR:
                logger.warning(f"⚠️ Agent {agent_name} in error state, attempting reload")
                await self._unload_agent(agent_name)
        
        # Load agent with lock to prevent concurrent loading
        if agent_name not in self._agent_locks:
            self._agent_locks[agent_name] = asyncio.Lock()
        
        async with self._agent_locks[agent_name]:
            # Double-check after acquiring lock
            if agent_name in self._loaded_agents and self._loaded_agents[agent_name].status == AgentStatus.READY:
                return self._loaded_agents[agent_name]
            
            return await self._load_agent(agent_name)
    
    async def _load_agent(self, agent_name: str) -> Optional[LoadedAgent]:
        """Load an agent with enhanced error handling and capability detection."""
        try:
            logger.info(f"🚀 Loading agent: {agent_name}")
            load_start_time = time.time()
            
            # Get team member configuration
            team_members = self.team_manager.get_team_members()
            if agent_name not in team_members:
                logger.error(f"❌ Agent {agent_name} not found in team configuration")
                return None
            
            team_member = team_members[agent_name]
            
            # Mark as initializing
            self._loaded_agents[agent_name] = LoadedAgent(
                name=agent_name,
                agent=None,  # Will be set after successful initialization
                team_member=team_member,
                status=AgentStatus.INITIALIZING,
                capabilities=[],
                load_time=0.0,
                last_used=time.time()
            )
            
            # Initialize agent
            from qx.core.llm_utils import initialize_agent_with_mcp
            agent = await initialize_agent_with_mcp(
                self.config_manager.mcp_manager,
                team_member.agent_config
            )
            
            if not agent:
                raise Exception("Agent initialization returned None")
            
            # Detect agent capabilities
            capabilities = await self._detect_agent_capabilities(agent_name, team_member)
            
            # Create loaded agent instance
            load_time = time.time() - load_start_time
            loaded_agent = LoadedAgent(
                name=agent_name,
                agent=agent,
                team_member=team_member,
                status=AgentStatus.READY,
                capabilities=capabilities,
                load_time=load_time,
                last_used=time.time()
            )
            
            self._loaded_agents[agent_name] = loaded_agent
            
            # Update metrics
            self.metrics["total_loads"] += 1
            self.metrics["avg_load_time"] = (
                (self.metrics["avg_load_time"] * (self.metrics["total_loads"] - 1) + load_time) /
                self.metrics["total_loads"]
            )
            
            logger.info(f"✅ Agent {agent_name} loaded in {load_time:.2f}s with {len(capabilities)} capabilities")
            return loaded_agent
            
        except Exception as e:
            logger.error(f"❌ Failed to load agent {agent_name}: {e}", exc_info=True)
            
            # Mark as error state
            if agent_name in self._loaded_agents:
                self._loaded_agents[agent_name].status = AgentStatus.ERROR
                self._loaded_agents[agent_name].record_error()
            
            self.metrics["load_failures"] += 1
            return None
    
    async def _detect_agent_capabilities(self, agent_name: str, team_member: TeamMember) -> List[AgentCapability]:
        """Detect agent capabilities from configuration and metadata."""
        capabilities = []
        
        try:
            # Check cache first
            if agent_name in self._capability_cache:
                logger.debug(f"🎯 Using cached capabilities for {agent_name}")
                return self._capability_cache[agent_name]
            
            agent_config = team_member.agent_config
            
            # Extract capabilities from agent configuration
            # Check for system prompt keywords and descriptions
            # Handle both old format (system_prompt) and new format (role/instructions)
            system_prompt = getattr(agent_config, 'system_prompt', '') or ''
            role = getattr(agent_config, 'role', '') or ''
            instructions = getattr(agent_config, 'instructions', '') or ''
            description = getattr(agent_config, 'description', '') or ''
            
            # Combine all text sources for capability detection
            prompt_text = system_prompt or f"{role} {instructions}"
            
            # Analyze tools and functions available to the agent
            tools = getattr(agent_config, 'tools', []) or []
            
            # Predefined capability patterns
            capability_patterns = {
                'file_operations': {
                    'keywords': ['file', 'read', 'write', 'create', 'modify', 'edit'],
                    'description': 'File system operations and manipulation'
                },
                'code_analysis': {
                    'keywords': ['code', 'analyze', 'review', 'debug', 'programming'],
                    'description': 'Code analysis and programming assistance'
                },
                'web_operations': {
                    'keywords': ['web', 'fetch', 'http', 'api', 'request'],
                    'description': 'Web requests and API interactions'
                },
                'shell_execution': {
                    'keywords': ['shell', 'command', 'execute', 'bash', 'terminal'],
                    'description': 'Shell command execution'
                },
                'git_operations': {
                    'keywords': ['git', 'version', 'control', 'commit', 'branch'],
                    'description': 'Git version control operations'
                },
                'data_processing': {
                    'keywords': ['data', 'process', 'transform', 'analyze', 'parse'],
                    'description': 'Data processing and transformation'
                }
            }
            
            # Detect capabilities based on prompt text and tools
            combined_text = f"{prompt_text} {description} {' '.join(tools)}".lower()
            
            for cap_name, cap_info in capability_patterns.items():
                matches = sum(1 for keyword in cap_info['keywords'] if keyword in combined_text)
                if matches > 0:
                    confidence = min(matches / len(cap_info['keywords']), 1.0)
                    capabilities.append(AgentCapability(
                        name=cap_name,
                        description=cap_info['description'],
                        keywords=cap_info['keywords'],
                        confidence=confidence
                    ))
            
            # Add agent-specific capabilities based on name
            if 'developer' in agent_name.lower() or 'swe' in agent_name.lower():
                capabilities.append(AgentCapability(
                    name='software_development',
                    description='Software development and engineering',
                    keywords=['develop', 'software', 'engineer', 'build', 'implement'],
                    confidence=0.9
                ))
            
            # Cache the capabilities
            self._capability_cache[agent_name] = capabilities
            
            logger.debug(f"🔍 Detected {len(capabilities)} capabilities for {agent_name}")
            return capabilities
            
        except Exception as e:
            logger.error(f"❌ Error detecting capabilities for {agent_name}: {e}", exc_info=True)
            return []
    
    async def find_best_agent_for_task(self, task_description: str, exclude_agents: Optional[Set[str]] = None) -> Optional[str]:
        """
        Find the best agent for a given task based on capabilities.
        
        Args:
            task_description: Description of the task to perform
            exclude_agents: Set of agent names to exclude from selection
            
        Returns:
            Name of the best-suited agent or None if no good match
        """
        exclude_agents = exclude_agents or set()
        best_agent = None
        best_score = 0.0
        
        team_members = self.team_manager.get_team_members()
        
        # Score all available agents
        agent_scores = []
        
        for agent_name in team_members.keys():
            if agent_name in exclude_agents or agent_name == "qx-director":
                continue
            
            # Get or detect capabilities
            capabilities = []
            if agent_name in self._capability_cache:
                capabilities = self._capability_cache[agent_name]
            else:
                team_member = team_members[agent_name]
                capabilities = await self._detect_agent_capabilities(agent_name, team_member)
            
            # Calculate task match score
            agent_score = 0.0
            for capability in capabilities:
                agent_score += capability.matches_task(task_description)
            
            # Bonus for agents that are already loaded (performance)
            if agent_name in self._loaded_agents and self._loaded_agents[agent_name].status == AgentStatus.READY:
                agent_score += 0.1
            
            # Penalty for agents with recent errors
            if agent_name in self._loaded_agents:
                loaded_agent = self._loaded_agents[agent_name]
                if loaded_agent.error_count > 0:
                    agent_score *= (1.0 - min(loaded_agent.error_count * 0.1, 0.5))
            
            agent_scores.append((agent_name, agent_score))
        
        # Sort by score and select best
        agent_scores.sort(key=lambda x: x[1], reverse=True)
        
        if agent_scores and agent_scores[0][1] > 0.1:  # Minimum threshold
            best_agent = agent_scores[0][0]
            best_score = agent_scores[0][1]
            
            logger.info(f"🎯 Best agent for task: {best_agent} (score: {best_score:.2f})")
            logger.debug(f"📊 Agent scores: {agent_scores[:3]}")  # Log top 3
        else:
            logger.warning(f"⚠️ No suitable agent found for task: {task_description[:50]}...")
        
        return best_agent
    
    async def preload_critical_agents(self, agent_names: List[str]):
        """Preload critical agents for better performance."""
        logger.info(f"🚀 Preloading {len(agent_names)} critical agents")
        
        tasks = [self.get_agent(agent_name) for agent_name in agent_names]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        loaded_count = sum(1 for result in results if isinstance(result, LoadedAgent))
        logger.info(f"✅ Preloaded {loaded_count}/{len(agent_names)} critical agents")
    
    async def _unload_agent(self, agent_name: str):
        """Unload an agent to free resources."""
        if agent_name in self._loaded_agents:
            logger.info(f"🗑️ Unloading agent: {agent_name}")
            del self._loaded_agents[agent_name]
        
        if agent_name in self._agent_locks:
            del self._agent_locks[agent_name]
    
    def get_loaded_agents(self) -> Dict[str, LoadedAgent]:
        """Get all currently loaded agents."""
        return {name: agent for name, agent in self._loaded_agents.items() if agent.status == AgentStatus.READY}
    
    def get_agent_metrics(self) -> Dict[str, Any]:
        """Get agent loading and usage metrics."""
        loaded_agents = self.get_loaded_agents()
        
        return {
            "loaded_count": len(loaded_agents),
            "total_loads": self.metrics["total_loads"],
            "load_failures": self.metrics["load_failures"],
            "cache_hits": self.metrics["cache_hits"],
            "avg_load_time": self.metrics["avg_load_time"],
            "agent_details": {
                name: {
                    "status": agent.status.value,
                    "usage_count": agent.usage_count,
                    "error_count": agent.error_count,
                    "capabilities": len(agent.capabilities),
                    "load_time": agent.load_time
                }
                for name, agent in loaded_agents.items()
            }
        }
    
    async def cleanup(self):
        """Clean up all loaded agents."""
        logger.info("🧹 Cleaning up dynamic agent loader")
        agent_names = list(self._loaded_agents.keys())
        
        for agent_name in agent_names:
            await self._unload_agent(agent_name)
        
        self._capability_cache.clear()
        logger.info("✅ Dynamic agent loader cleanup completed")