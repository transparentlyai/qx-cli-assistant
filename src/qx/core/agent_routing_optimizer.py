"""
Agent Routing Optimizer for QX Unified LangGraph Workflow.

This module provides advanced agent routing and optimization capabilities including:
- Task complexity analysis
- Agent workload balancing
- Performance-based routing decisions
- Learning from past routing decisions
- Multi-agent collaboration optimization
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import json

from qx.core.dynamic_agent_loader import DynamicAgentLoader, LoadedAgent, AgentCapability

logger = logging.getLogger(__name__)


class TaskComplexity(Enum):
    """Task complexity levels for routing optimization."""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    EXPERT = "expert"


class RoutingStrategy(Enum):
    """Routing strategies for different scenarios."""
    BEST_MATCH = "best_match"  # Route to agent with best capability match
    LOAD_BALANCED = "load_balanced"  # Consider agent workload
    PERFORMANCE_OPTIMIZED = "performance_optimized"  # Route based on past performance
    COLLABORATIVE = "collaborative"  # Multi-agent approach
    ADAPTIVE = "adaptive"  # Learn and adapt routing decisions


@dataclass
class TaskAnalysis:
    """Analysis result for a task."""
    task_description: str
    complexity: TaskComplexity
    required_capabilities: List[str]
    estimated_duration: float  # in seconds
    requires_collaboration: bool
    priority: int  # 1-10, higher is more important
    task_hash: str = field(init=False)
    
    def __post_init__(self):
        # Generate hash for task identification
        task_data = f"{self.task_description}_{self.complexity.value}_{sorted(self.required_capabilities)}"
        self.task_hash = hashlib.md5(task_data.encode()).hexdigest()[:12]


@dataclass
class RoutingDecision:
    """Result of a routing decision."""
    task_analysis: TaskAnalysis
    selected_agents: List[str]
    routing_strategy: RoutingStrategy
    confidence_score: float  # 0.0 to 1.0
    reasoning: str
    estimated_completion_time: float
    alternatives: List[Tuple[str, float]] = field(default_factory=list)  # (agent, score) pairs
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/analysis."""
        return {
            "task_hash": self.task_analysis.task_hash,
            "task_description": self.task_analysis.task_description[:100],
            "complexity": self.task_analysis.complexity.value,
            "selected_agents": self.selected_agents,
            "strategy": self.routing_strategy.value,
            "confidence": self.confidence_score,
            "reasoning": self.reasoning,
            "estimated_time": self.estimated_completion_time
        }


@dataclass
class RoutingHistory:
    """Historical record of routing decisions and outcomes."""
    decision: RoutingDecision
    actual_agents: List[str]
    actual_duration: float
    success: bool
    user_satisfaction: Optional[float] = None  # 0.0 to 1.0 if available
    error_details: Optional[str] = None
    timestamp: float = field(default_factory=time.time)
    
    def get_performance_score(self) -> float:
        """Calculate performance score for this routing decision."""
        if not self.success:
            return 0.0
        
        # Base score from success
        score = 0.6
        
        # Bonus for meeting time estimates
        time_accuracy = min(self.decision.estimated_completion_time / max(self.actual_duration, 1.0), 2.0)
        score += (time_accuracy - 1.0) * 0.2  # +/-0.2 based on time accuracy
        
        # Bonus for user satisfaction if available
        if self.user_satisfaction is not None:
            score += self.user_satisfaction * 0.2
        
        return max(0.0, min(1.0, score))


class AgentRoutingOptimizer:
    """
    Advanced agent routing optimizer that learns from past decisions
    and optimizes routing based on multiple factors.
    """
    
    def __init__(self, dynamic_agent_loader: DynamicAgentLoader):
        self.agent_loader = dynamic_agent_loader
        
        # Historical data for learning
        self.routing_history: List[RoutingHistory] = []
        self.agent_performance: Dict[str, Dict[str, float]] = {}  # agent -> metric -> value
        self.task_patterns: Dict[str, List[str]] = {}  # task_type -> successful_agents
        
        # Optimization settings
        self.max_history_size = 1000
        self.learning_rate = 0.1
        self.performance_decay = 0.95  # Decay older performance data
        
        # Routing preferences
        self.default_strategy = RoutingStrategy.ADAPTIVE
        self.enable_learning = True
        
        logger.info("🎯 AgentRoutingOptimizer initialized")
    
    async def analyze_task(self, task_description: str) -> TaskAnalysis:
        """Analyze a task to understand its requirements and complexity."""
        task_lower = task_description.lower()
        
        # Determine complexity based on keywords and length
        complexity = self._assess_task_complexity(task_description)
        
        # Extract required capabilities
        required_capabilities = self._extract_required_capabilities(task_description)
        
        # Estimate duration based on complexity and past data
        estimated_duration = self._estimate_task_duration(complexity, required_capabilities)
        
        # Check if collaboration is beneficial
        requires_collaboration = self._assess_collaboration_need(task_description, complexity)
        
        # Determine priority (could be enhanced with user input)
        priority = self._assess_task_priority(task_description)
        
        analysis = TaskAnalysis(
            task_description=task_description,
            complexity=complexity,
            required_capabilities=required_capabilities,
            estimated_duration=estimated_duration,
            requires_collaboration=requires_collaboration,
            priority=priority
        )
        
        logger.debug(f"🔍 Task analysis: {complexity.value} complexity, {len(required_capabilities)} capabilities needed")
        return analysis
    
    async def optimize_routing(
        self, 
        task_analysis: TaskAnalysis,
        available_agents: Optional[List[str]] = None,
        strategy: Optional[RoutingStrategy] = None,
        exclude_agents: Optional[Set[str]] = None
    ) -> RoutingDecision:
        """
        Generate optimized routing decision for a task.
        
        Args:
            task_analysis: Analysis of the task to route
            available_agents: List of available agents (None = all agents)
            strategy: Routing strategy to use (None = default adaptive)
            exclude_agents: Agents to exclude from consideration
        
        Returns:
            RoutingDecision with optimized agent selection
        """
        start_time = time.time()
        exclude_agents = exclude_agents or set()
        exclude_agents.add("qx-director")  # Director manages routing, doesn't execute tasks
        
        strategy = strategy or self.default_strategy
        
        logger.info(f"🎯 Optimizing routing for {task_analysis.complexity.value} task using {strategy.value} strategy")
        
        # Get available agents and their current status
        if available_agents is None:
            team_members = self.agent_loader.team_manager.get_team_members()
            available_agents = [name for name in team_members.keys() if name not in exclude_agents]
        else:
            available_agents = [name for name in available_agents if name not in exclude_agents]
        
        if not available_agents:
            logger.warning("⚠️ No available agents for routing")
            return RoutingDecision(
                task_analysis=task_analysis,
                selected_agents=[],
                routing_strategy=strategy,
                confidence_score=0.0,
                reasoning="No available agents",
                estimated_completion_time=0.0
            )
        
        # Apply routing strategy
        if strategy == RoutingStrategy.ADAPTIVE and self.enable_learning:
            decision = await self._adaptive_routing(task_analysis, available_agents)
        elif strategy == RoutingStrategy.PERFORMANCE_OPTIMIZED:
            decision = await self._performance_optimized_routing(task_analysis, available_agents)
        elif strategy == RoutingStrategy.LOAD_BALANCED:
            decision = await self._load_balanced_routing(task_analysis, available_agents)
        elif strategy == RoutingStrategy.COLLABORATIVE:
            decision = await self._collaborative_routing(task_analysis, available_agents)
        else:  # BEST_MATCH or fallback
            decision = await self._best_match_routing(task_analysis, available_agents)
        
        optimization_time = time.time() - start_time
        logger.info(f"✅ Routing optimized in {optimization_time:.3f}s: {decision.selected_agents} (confidence: {decision.confidence_score:.2f})")
        
        return decision
    
    async def _adaptive_routing(self, task_analysis: TaskAnalysis, available_agents: List[str]) -> RoutingDecision:
        """Adaptive routing that learns from historical performance."""
        # Get performance scores for each agent on similar tasks
        agent_scores = {}
        
        for agent_name in available_agents:
            # Base capability score
            capability_score = await self._calculate_capability_score(agent_name, task_analysis)
            
            # Historical performance score
            performance_score = self._get_historical_performance_score(agent_name, task_analysis)
            
            # Current load penalty
            load_penalty = await self._calculate_load_penalty(agent_name)
            
            # Combine scores with weights
            final_score = (
                capability_score * 0.4 +
                performance_score * 0.4 +
                (1.0 - load_penalty) * 0.2
            )
            
            agent_scores[agent_name] = final_score
        
        # Select best agent(s)
        sorted_agents = sorted(agent_scores.items(), key=lambda x: x[1], reverse=True)
        
        if task_analysis.requires_collaboration and len(sorted_agents) > 1:
            # Select top 2-3 agents for collaboration
            selected_agents = [agent for agent, _ in sorted_agents[:min(3, len(sorted_agents))]]
            confidence = (sorted_agents[0][1] + sorted_agents[1][1]) / 2.0
            reasoning = f"Collaborative approach with top {len(selected_agents)} agents"
        else:
            # Select single best agent
            selected_agents = [sorted_agents[0][0]]
            confidence = sorted_agents[0][1]
            reasoning = f"Best adaptive match based on capabilities and performance"
        
        estimated_time = self._estimate_completion_time(selected_agents, task_analysis)
        
        return RoutingDecision(
            task_analysis=task_analysis,
            selected_agents=selected_agents,
            routing_strategy=RoutingStrategy.ADAPTIVE,
            confidence_score=confidence,
            reasoning=reasoning,
            estimated_completion_time=estimated_time,
            alternatives=sorted_agents[len(selected_agents):len(selected_agents)+3]
        )
    
    async def _best_match_routing(self, task_analysis: TaskAnalysis, available_agents: List[str]) -> RoutingDecision:
        """Simple best capability match routing."""
        agent_scores = {}
        
        for agent_name in available_agents:
            score = await self._calculate_capability_score(agent_name, task_analysis)
            agent_scores[agent_name] = score
        
        if not agent_scores:
            selected_agent = available_agents[0] if available_agents else ""
            confidence = 0.1
        else:
            sorted_agents = sorted(agent_scores.items(), key=lambda x: x[1], reverse=True)
            selected_agent = sorted_agents[0][0]
            confidence = sorted_agents[0][1]
        
        estimated_time = self._estimate_completion_time([selected_agent], task_analysis)
        
        return RoutingDecision(
            task_analysis=task_analysis,
            selected_agents=[selected_agent] if selected_agent else [],
            routing_strategy=RoutingStrategy.BEST_MATCH,
            confidence_score=confidence,
            reasoning="Best capability match",
            estimated_completion_time=estimated_time
        )
    
    async def _performance_optimized_routing(self, task_analysis: TaskAnalysis, available_agents: List[str]) -> RoutingDecision:
        """Route based primarily on historical performance."""
        agent_scores = {}
        
        for agent_name in available_agents:
            # Weight performance more heavily
            capability_score = await self._calculate_capability_score(agent_name, task_analysis)
            performance_score = self._get_historical_performance_score(agent_name, task_analysis)
            
            final_score = capability_score * 0.3 + performance_score * 0.7
            agent_scores[agent_name] = final_score
        
        sorted_agents = sorted(agent_scores.items(), key=lambda x: x[1], reverse=True)
        selected_agent = sorted_agents[0][0] if sorted_agents else ""
        confidence = sorted_agents[0][1] if sorted_agents else 0.1
        
        estimated_time = self._estimate_completion_time([selected_agent], task_analysis)
        
        return RoutingDecision(
            task_analysis=task_analysis,
            selected_agents=[selected_agent] if selected_agent else [],
            routing_strategy=RoutingStrategy.PERFORMANCE_OPTIMIZED,
            confidence_score=confidence,
            reasoning="Performance-optimized selection",
            estimated_completion_time=estimated_time,
            alternatives=sorted_agents[1:4]
        )
    
    async def _load_balanced_routing(self, task_analysis: TaskAnalysis, available_agents: List[str]) -> RoutingDecision:
        """Route considering agent workload balancing."""
        agent_scores = {}
        
        for agent_name in available_agents:
            capability_score = await self._calculate_capability_score(agent_name, task_analysis)
            load_penalty = await self._calculate_load_penalty(agent_name)
            
            # Balance capability with load
            final_score = capability_score * (1.0 - load_penalty * 0.5)
            agent_scores[agent_name] = final_score
        
        sorted_agents = sorted(agent_scores.items(), key=lambda x: x[1], reverse=True)
        selected_agent = sorted_agents[0][0] if sorted_agents else ""
        confidence = sorted_agents[0][1] if sorted_agents else 0.1
        
        estimated_time = self._estimate_completion_time([selected_agent], task_analysis)
        
        return RoutingDecision(
            task_analysis=task_analysis,
            selected_agents=[selected_agent] if selected_agent else [],
            routing_strategy=RoutingStrategy.LOAD_BALANCED,
            confidence_score=confidence,
            reasoning="Load-balanced selection",
            estimated_completion_time=estimated_time
        )
    
    async def _collaborative_routing(self, task_analysis: TaskAnalysis, available_agents: List[str]) -> RoutingDecision:
        """Route for multi-agent collaboration."""
        # Always select multiple agents for collaboration
        agent_scores = {}
        
        for agent_name in available_agents:
            score = await self._calculate_capability_score(agent_name, task_analysis)
            agent_scores[agent_name] = score
        
        sorted_agents = sorted(agent_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Select top 2-3 agents with complementary capabilities
        selected_agents = [agent for agent, _ in sorted_agents[:min(3, len(sorted_agents))]]
        
        if len(selected_agents) > 1:
            confidence = sum(score for _, score in sorted_agents[:len(selected_agents)]) / len(selected_agents)
        else:
            confidence = sorted_agents[0][1] if sorted_agents else 0.1
        
        estimated_time = self._estimate_completion_time(selected_agents, task_analysis) * 1.2  # Collaboration overhead
        
        return RoutingDecision(
            task_analysis=task_analysis,
            selected_agents=selected_agents,
            routing_strategy=RoutingStrategy.COLLABORATIVE,
            confidence_score=confidence,
            reasoning=f"Collaborative approach with {len(selected_agents)} agents",
            estimated_completion_time=estimated_time
        )
    
    async def _calculate_capability_score(self, agent_name: str, task_analysis: TaskAnalysis) -> float:
        """Calculate how well an agent's capabilities match a task."""
        if agent_name in self.agent_loader._capability_cache:
            capabilities = self.agent_loader._capability_cache[agent_name]
        else:
            # Get capabilities from team member
            team_members = self.agent_loader.team_manager.get_team_members()
            if agent_name not in team_members:
                return 0.0
            
            team_member = team_members[agent_name]
            capabilities = await self.agent_loader._detect_agent_capabilities(agent_name, team_member)
        
        if not capabilities:
            return 0.1  # Minimum score
        
        # Calculate match score
        total_score = 0.0
        for capability in capabilities:
            capability_score = capability.matches_task(task_analysis.task_description)
            total_score += capability_score
        
        # Normalize score
        return min(total_score / len(capabilities), 1.0)
    
    def _get_historical_performance_score(self, agent_name: str, task_analysis: TaskAnalysis) -> float:
        """Get historical performance score for an agent on similar tasks."""
        if agent_name not in self.agent_performance:
            return 0.5  # Neutral score for unknown agents
        
        agent_perf = self.agent_performance[agent_name]
        
        # Look for performance on similar task types
        task_type = self._categorize_task(task_analysis)
        if task_type in agent_perf:
            return agent_perf[task_type]
        
        # Return overall performance score
        return agent_perf.get('overall', 0.5)
    
    async def _calculate_load_penalty(self, agent_name: str) -> float:
        """Calculate load penalty for an agent (0.0 = no load, 1.0 = fully loaded)."""
        loaded_agents = self.agent_loader.get_loaded_agents()
        
        if agent_name not in loaded_agents:
            return 0.0  # Not loaded = no current load
        
        loaded_agent = loaded_agents[agent_name]
        
        # Simple load calculation based on recent usage
        current_time = time.time()
        time_since_last_use = current_time - loaded_agent.last_used
        
        if time_since_last_use < 10:  # Used in last 10 seconds
            return 0.8
        elif time_since_last_use < 60:  # Used in last minute
            return 0.4
        else:
            return 0.1  # Not recently used
    
    def _assess_task_complexity(self, task_description: str) -> TaskComplexity:
        """Assess task complexity based on content analysis."""
        task_lower = task_description.lower()
        
        # Complexity indicators
        complex_keywords = ['complex', 'advanced', 'intricate', 'sophisticated', 'comprehensive', 'detailed']
        moderate_keywords = ['analyze', 'implement', 'develop', 'create', 'build', 'design']
        simple_keywords = ['read', 'write', 'list', 'show', 'display', 'check']
        
        # Check for expert-level indicators
        if any(keyword in task_lower for keyword in ['architecture', 'algorithm', 'optimization', 'performance']):
            return TaskComplexity.EXPERT
        
        # Check for complex indicators
        if any(keyword in task_lower for keyword in complex_keywords) or len(task_description) > 200:
            return TaskComplexity.COMPLEX
        
        # Check for moderate indicators
        if any(keyword in task_lower for keyword in moderate_keywords):
            return TaskComplexity.MODERATE
        
        # Default to simple
        return TaskComplexity.SIMPLE
    
    def _extract_required_capabilities(self, task_description: str) -> List[str]:
        """Extract required capabilities from task description."""
        task_lower = task_description.lower()
        capabilities = []
        
        capability_keywords = {
            'file_operations': ['file', 'read', 'write', 'create', 'delete', 'modify'],
            'code_analysis': ['code', 'analyze', 'review', 'debug', 'programming'],
            'web_operations': ['web', 'fetch', 'http', 'api', 'request', 'download'],
            'shell_execution': ['command', 'execute', 'run', 'shell', 'terminal'],
            'git_operations': ['git', 'commit', 'branch', 'merge', 'version control'],
            'data_processing': ['data', 'process', 'analyze', 'transform', 'parse']
        }
        
        for capability, keywords in capability_keywords.items():
            if any(keyword in task_lower for keyword in keywords):
                capabilities.append(capability)
        
        return capabilities or ['general']
    
    def _estimate_task_duration(self, complexity: TaskComplexity, capabilities: List[str]) -> float:
        """Estimate task duration in seconds."""
        base_times = {
            TaskComplexity.SIMPLE: 30.0,
            TaskComplexity.MODERATE: 120.0,
            TaskComplexity.COMPLEX: 300.0,
            TaskComplexity.EXPERT: 600.0
        }
        
        base_time = base_times[complexity]
        
        # Add time for multiple capabilities
        if len(capabilities) > 1:
            base_time *= (1.0 + (len(capabilities) - 1) * 0.3)
        
        return base_time
    
    def _assess_collaboration_need(self, task_description: str, complexity: TaskComplexity) -> bool:
        """Assess if task would benefit from multiple agents."""
        task_lower = task_description.lower()
        
        # Collaboration indicators
        collaboration_keywords = ['multiple', 'various', 'different', 'combine', 'integrate', 'coordinate']
        
        # Complex tasks often benefit from collaboration
        if complexity in [TaskComplexity.COMPLEX, TaskComplexity.EXPERT]:
            return True
        
        # Check for explicit collaboration needs
        if any(keyword in task_lower for keyword in collaboration_keywords):
            return True
        
        # Tasks with multiple capabilities might benefit
        capabilities = self._extract_required_capabilities(task_description)
        return len(capabilities) > 2
    
    def _assess_task_priority(self, task_description: str) -> int:
        """Assess task priority (1-10)."""
        task_lower = task_description.lower()
        
        # High priority indicators
        if any(keyword in task_lower for keyword in ['urgent', 'critical', 'important', 'asap']):
            return 9
        
        # Medium priority indicators  
        if any(keyword in task_lower for keyword in ['please', 'need', 'should']):
            return 6
        
        # Default priority
        return 5
    
    def _categorize_task(self, task_analysis: TaskAnalysis) -> str:
        """Categorize task for performance tracking."""
        if task_analysis.required_capabilities:
            return task_analysis.required_capabilities[0]
        return 'general'
    
    def _estimate_completion_time(self, selected_agents: List[str], task_analysis: TaskAnalysis) -> float:
        """Estimate completion time for selected agents."""
        if not selected_agents:
            return task_analysis.estimated_duration
        
        # Base estimation
        base_time = task_analysis.estimated_duration
        
        # Adjust for multiple agents (some overhead but potential parallelization)
        if len(selected_agents) > 1:
            base_time *= 0.8  # 20% faster with collaboration
            base_time += 30.0  # 30 seconds coordination overhead
        
        return base_time
    
    def record_routing_outcome(
        self, 
        decision: RoutingDecision,
        actual_agents: List[str],
        actual_duration: float,
        success: bool,
        user_satisfaction: Optional[float] = None,
        error_details: Optional[str] = None
    ):
        """Record the outcome of a routing decision for learning."""
        history_entry = RoutingHistory(
            decision=decision,
            actual_agents=actual_agents,
            actual_duration=actual_duration,
            success=success,
            user_satisfaction=user_satisfaction,
            error_details=error_details
        )
        
        self.routing_history.append(history_entry)
        
        # Maintain history size limit
        if len(self.routing_history) > self.max_history_size:
            self.routing_history = self.routing_history[-self.max_history_size:]
        
        # Update agent performance metrics
        self._update_agent_performance(history_entry)
        
        logger.info(f"📊 Recorded routing outcome: {success}, duration: {actual_duration:.1f}s")
    
    def _update_agent_performance(self, history_entry: RoutingHistory):
        """Update agent performance metrics based on outcome."""
        if not self.enable_learning:
            return
        
        performance_score = history_entry.get_performance_score()
        task_type = self._categorize_task(history_entry.decision.task_analysis)
        
        for agent_name in history_entry.actual_agents:
            if agent_name not in self.agent_performance:
                self.agent_performance[agent_name] = {}
            
            agent_perf = self.agent_performance[agent_name]
            
            # Update task-specific performance
            current_score = agent_perf.get(task_type, 0.5)
            new_score = current_score * (1 - self.learning_rate) + performance_score * self.learning_rate
            agent_perf[task_type] = new_score
            
            # Update overall performance
            overall_score = agent_perf.get('overall', 0.5)
            new_overall = overall_score * (1 - self.learning_rate) + performance_score * self.learning_rate
            agent_perf['overall'] = new_overall
    
    def get_routing_metrics(self) -> Dict[str, Any]:
        """Get comprehensive routing optimization metrics."""
        recent_decisions = self.routing_history[-50:] if self.routing_history else []
        
        if recent_decisions:
            success_rate = sum(1 for h in recent_decisions if h.success) / len(recent_decisions)
            avg_confidence = sum(h.decision.confidence_score for h in recent_decisions) / len(recent_decisions)
            avg_duration = sum(h.actual_duration for h in recent_decisions) / len(recent_decisions)
        else:
            success_rate = 0.0
            avg_confidence = 0.0
            avg_duration = 0.0
        
        return {
            "total_decisions": len(self.routing_history),
            "recent_success_rate": success_rate,
            "average_confidence": avg_confidence,
            "average_duration": avg_duration,
            "agent_performance": self.agent_performance.copy(),
            "strategies_used": {
                strategy.value: sum(1 for h in recent_decisions if h.decision.routing_strategy == strategy)
                for strategy in RoutingStrategy
            },
            "complexity_distribution": {
                complexity.value: sum(1 for h in recent_decisions if h.decision.task_analysis.complexity == complexity)
                for complexity in TaskComplexity
            }
        }