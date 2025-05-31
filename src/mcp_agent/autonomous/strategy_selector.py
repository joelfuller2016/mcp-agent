"""
Autonomous Strategy Selector

This module provides intelligent strategy selection for MCP-agent workflows,
automatically choosing optimal execution patterns based on task analysis.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
import json

from ..workflows.llm.augmented_llm import AugmentedLLM
from ..workflows.parallel.parallel_llm import ParallelLLM
from ..workflows.router.router_llm import LLMRouter
from ..workflows.orchestrator.orchestrator import Orchestrator
from ..workflows.swarm.swarm import AnthropicSwarm
from ..workflows.evaluator_optimizer.evaluator_optimizer import EvaluatorOptimizerLLM

from .discovery import AutonomousDiscovery, MCPToolInfo
from ..capabilities.capability_mapper import CapabilityMapper


class ExecutionStrategy(Enum):
    """Available execution strategies for autonomous coordination"""
    DIRECT = "direct"                    # Single agent with tools
    PARALLEL = "parallel"                # Fan-out/fan-in pattern
    ROUTER = "router"                    # Route to best specialist
    ORCHESTRATOR = "orchestrator"        # Plan and coordinate execution
    SWARM = "swarm"                      # Multi-agent with handoffs
    EVALUATOR_OPTIMIZER = "evaluator_optimizer"  # Iterative refinement
    ADAPTIVE_HYBRID = "adaptive_hybrid"  # Dynamic combination


@dataclass 
class StrategyRecommendation:
    """Recommendation for execution strategy"""
    strategy: ExecutionStrategy
    confidence: float
    reasoning: str
    estimated_complexity: int
    required_tools: List[str]
    estimated_duration: float
    success_probability: float
    alternative_strategies: List[ExecutionStrategy]


@dataclass
class TaskAnalysis:
    """Analysis of a task for strategy selection"""
    description: str
    complexity_score: int  # 1-10
    tool_requirements: List[str]
    skill_requirements: List[str]
    interdependencies: bool
    time_sensitivity: str  # "low", "medium", "high"
    quality_requirements: str  # "standard", "high", "critical"
    coordination_needs: bool
    parallel_potential: float  # 0.0-1.0


class AutonomousStrategySelector:
    """
    Intelligent strategy selector for autonomous MCP-agent coordination
    
    Analyzes tasks and selects optimal execution patterns based on:
    - Task complexity and requirements
    - Available tools and capabilities
    - Performance history and success rates
    - Quality and time constraints
    """
    
    def __init__(self, discovery: AutonomousDiscovery):
        self.discovery = discovery
        self.capability_mapper = CapabilityMapper()
        self.logger = logging.getLogger(__name__)
        
        # Strategy performance tracking
        self.strategy_performance: Dict[str, Dict[str, float]] = {}
        
        # Configuration thresholds
        self.complexity_thresholds = {
            ExecutionStrategy.DIRECT: (1, 3),
            ExecutionStrategy.PARALLEL: (3, 6),
            ExecutionStrategy.ROUTER: (2, 5), 
            ExecutionStrategy.ORCHESTRATOR: (5, 8),
            ExecutionStrategy.SWARM: (6, 10),
            ExecutionStrategy.EVALUATOR_OPTIMIZER: (4, 7),
            ExecutionStrategy.ADAPTIVE_HYBRID: (7, 10)
        }
        
        # Quality requirement mappings
        self.quality_strategy_preferences = {
            "standard": [ExecutionStrategy.DIRECT, ExecutionStrategy.PARALLEL],
            "high": [ExecutionStrategy.ORCHESTRATOR, ExecutionStrategy.EVALUATOR_OPTIMIZER],
            "critical": [ExecutionStrategy.EVALUATOR_OPTIMIZER, ExecutionStrategy.ADAPTIVE_HYBRID]
        }
    
    async def analyze_task(self, task_description: str, 
                          context: Optional[Dict[str, Any]] = None) -> TaskAnalysis:
        """
        Analyze a task to understand its requirements and characteristics
        
        Args:
            task_description: Natural language task description
            context: Optional context information
            
        Returns:
            TaskAnalysis with detailed task characteristics
        """
        
        self.logger.info(f"Analyzing task: {task_description[:100]}...")
        
        # Extract capability requirements
        required_capabilities = await self.capability_mapper.analyze_task_requirements(
            task_description
        )
        
        # Calculate complexity score based on multiple factors
        complexity_score = await self._calculate_complexity_score(
            task_description, required_capabilities
        )
        
        # Analyze interdependencies
        interdependencies = await self._detect_interdependencies(
            task_description, required_capabilities
        )
        
        # Assess parallel potential
        parallel_potential = await self._assess_parallel_potential(
            task_description, required_capabilities
        )
        
        # Extract quality and time requirements
        quality_req = self._extract_quality_requirements(task_description, context)
        time_sensitivity = self._extract_time_sensitivity(task_description, context)
        
        # Determine coordination needs
        coordination_needs = await self._assess_coordination_needs(
            task_description, required_capabilities
        )
        
        analysis = TaskAnalysis(
            description=task_description,
            complexity_score=complexity_score,
            tool_requirements=required_capabilities,
            skill_requirements=self._extract_skill_requirements(required_capabilities),
            interdependencies=interdependencies,
            time_sensitivity=time_sensitivity,
            quality_requirements=quality_req,
            coordination_needs=coordination_needs,
            parallel_potential=parallel_potential
        )
        
        self.logger.info(f"Task analysis complete. Complexity: {complexity_score}, "
                        f"Tools needed: {len(required_capabilities)}")
        
        return analysis
    
    async def recommend_strategy(self, 
                               task_analysis: TaskAnalysis,
                               available_tools: Optional[List[MCPToolInfo]] = None) -> StrategyRecommendation:
        """
        Recommend optimal execution strategy based on task analysis
        
        Args:
            task_analysis: Analysis of the task
            available_tools: Available MCP tools (discovered if not provided)
            
        Returns:
            StrategyRecommendation with detailed strategy selection
        """
        
        if available_tools is None:
            available_tools = list((await self.discovery.discover_available_tools()).values())
        
        # Score each strategy
        strategy_scores = {}
        
        for strategy in ExecutionStrategy:
            score = await self._score_strategy(strategy, task_analysis, available_tools)
            strategy_scores[strategy] = score
        
        # Select best strategy
        best_strategy = max(strategy_scores.keys(), key=lambda s: strategy_scores[s])
        confidence = strategy_scores[best_strategy]
        
        # Generate reasoning
        reasoning = await self._generate_strategy_reasoning(
            best_strategy, task_analysis, available_tools
        )
        
        # Find required tools
        required_tools = await self._find_required_tools(
            task_analysis.tool_requirements, available_tools
        )
        
        # Estimate metrics
        estimated_duration = self._estimate_duration(best_strategy, task_analysis)
        success_probability = self._estimate_success_probability(
            best_strategy, task_analysis, available_tools
        )
        
        # Find alternative strategies
        sorted_strategies = sorted(
            strategy_scores.keys(), 
            key=lambda s: strategy_scores[s], 
            reverse=True
        )
        alternatives = sorted_strategies[1:4]  # Top 3 alternatives
        
        recommendation = StrategyRecommendation(
            strategy=best_strategy,
            confidence=confidence,
            reasoning=reasoning,
            estimated_complexity=task_analysis.complexity_score,
            required_tools=required_tools,
            estimated_duration=estimated_duration,
            success_probability=success_probability,
            alternative_strategies=alternatives
        )
        
        self.logger.info(f"Strategy recommendation: {best_strategy.value} "
                        f"(confidence: {confidence:.2f})")
        
        return recommendation
    
    async def _calculate_complexity_score(self, 
                                        task_description: str,
                                        capabilities: List[str]) -> int:
        """Calculate task complexity score (1-10)"""
        
        complexity = 1
        task_lower = task_description.lower()
        
        # Base complexity from number of capabilities needed
        complexity += min(3, len(capabilities))
        
        # Complexity keywords
        high_complexity_keywords = [
            "analyze", "complex", "comprehensive", "detailed", "thorough",
            "multiple", "various", "coordinate", "integrate", "optimize"
        ]
        
        medium_complexity_keywords = [
            "create", "build", "develop", "process", "manage", "organize"
        ]
        
        # Add complexity based on keywords
        high_matches = sum(1 for kw in high_complexity_keywords if kw in task_lower)
        medium_matches = sum(1 for kw in medium_complexity_keywords if kw in task_lower)
        
        complexity += high_matches * 2 + medium_matches
        
        # Complexity from capability types
        capability_complexity = sum(
            self.capability_mapper.get_capability_complexity(cap) 
            for cap in capabilities
        )
        complexity += min(3, capability_complexity // 3)
        
        # Multi-step indicators
        if any(indicator in task_lower for indicator in ["then", "after", "first", "next", "finally"]):
            complexity += 2
        
        # Quality indicators  
        if any(qual in task_lower for qual in ["perfect", "best", "optimal", "excellent"]):
            complexity += 1
        
        return min(10, max(1, complexity))
    
    async def _detect_interdependencies(self, 
                                      task_description: str,
                                      capabilities: List[str]) -> bool:
        """Detect if task has interdependencies between steps"""
        
        task_lower = task_description.lower()
        
        # Sequential indicators
        sequential_indicators = [
            "then", "after", "before", "once", "when", "following",
            "depends on", "requires", "based on", "using the results"
        ]
        
        return any(indicator in task_lower for indicator in sequential_indicators)
    
    async def _assess_parallel_potential(self, 
                                       task_description: str,
                                       capabilities: List[str]) -> float:
        """Assess potential for parallel execution (0.0-1.0)"""
        
        task_lower = task_description.lower()
        potential = 0.0
        
        # Independent subtasks indicated
        parallel_indicators = [
            "simultaneously", "parallel", "at the same time", "independently",
            "separate", "different", "multiple", "various"
        ]
        
        if any(indicator in task_lower for indicator in parallel_indicators):
            potential += 0.4
        
        # Multiple diverse capabilities suggest parallelization
        unique_categories = set(cap.split(':')[0] for cap in capabilities)
        if len(unique_categories) > 1:
            potential += 0.3
        
        # No sequential dependencies
        if not await self._detect_interdependencies(task_description, capabilities):
            potential += 0.3
        
        return min(1.0, potential)
    
    def _extract_quality_requirements(self, 
                                    task_description: str,
                                    context: Optional[Dict[str, Any]]) -> str:
        """Extract quality requirements from task description"""
        
        task_lower = task_description.lower()
        
        critical_keywords = ["critical", "essential", "crucial", "perfect", "flawless"]
        high_keywords = ["excellent", "high quality", "best", "optimal", "thorough"]
        
        if context and context.get("quality_level"):
            return context["quality_level"]
        
        if any(kw in task_lower for kw in critical_keywords):
            return "critical"
        elif any(kw in task_lower for kw in high_keywords):
            return "high"
        else:
            return "standard"
    
    def _extract_time_sensitivity(self, 
                                task_description: str,
                                context: Optional[Dict[str, Any]]) -> str:
        """Extract time sensitivity from task description"""
        
        task_lower = task_description.lower()
        
        high_urgency = ["urgent", "asap", "immediately", "quickly", "fast", "rush"]
        medium_urgency = ["soon", "promptly", "timely", "deadline"]
        
        if context and context.get("deadline"):
            return "high"
        
        if any(kw in task_lower for kw in high_urgency):
            return "high"
        elif any(kw in task_lower for kw in medium_urgency):
            return "medium"
        else:
            return "low"
    
    def _extract_skill_requirements(self, capabilities: List[str]) -> List[str]:
        """Extract high-level skill requirements from capabilities"""
        
        skill_map = {
            "development": ["coding", "git", "software engineering"],
            "search": ["research", "information gathering"],
            "data": ["data analysis", "database management"],
            "automation": ["workflow design", "process automation"],
            "cognitive": ["reasoning", "analysis", "problem solving"],
            "filesystem": ["file management"],
            "network": ["web operations"]
        }
        
        skills = set()
        for cap in capabilities:
            category = cap.split(':')[0]
            if category in skill_map:
                skills.update(skill_map[category])
        
        return list(skills)
    
    async def _assess_coordination_needs(self, 
                                       task_description: str,
                                       capabilities: List[str]) -> bool:
        """Assess if task needs coordination between agents"""
        
        task_lower = task_description.lower()
        
        coordination_indicators = [
            "coordinate", "collaborate", "work together", "combine",
            "integrate", "merge", "synthesize", "aggregate"
        ]
        
        # High coordination if many capabilities or coordination keywords
        return (len(capabilities) > 3 or 
                any(indicator in task_lower for indicator in coordination_indicators))
    
    async def _score_strategy(self, 
                            strategy: ExecutionStrategy,
                            task_analysis: TaskAnalysis,
                            available_tools: List[MCPToolInfo]) -> float:
        """Score a strategy for the given task (0.0-1.0)"""
        
        score = 0.0
        
        # Complexity match score
        min_complexity, max_complexity = self.complexity_thresholds[strategy]
        if min_complexity <= task_analysis.complexity_score <= max_complexity:
            score += 0.3
        elif task_analysis.complexity_score < min_complexity:
            score += 0.1  # Strategy too complex
        else:
            score += 0.05  # Strategy too simple
        
        # Quality requirements match
        quality_strategies = self.quality_strategy_preferences.get(
            task_analysis.quality_requirements, []
        )
        if strategy in quality_strategies:
            score += 0.2
        
        # Strategy-specific scoring
        if strategy == ExecutionStrategy.DIRECT:
            # Good for simple, single-tool tasks
            score += 0.3 if len(task_analysis.tool_requirements) <= 2 else 0.1
            score += 0.2 if not task_analysis.coordination_needs else 0.0
            
        elif strategy == ExecutionStrategy.PARALLEL:
            # Good for independent parallel tasks
            score += task_analysis.parallel_potential * 0.3
            score += 0.2 if not task_analysis.interdependencies else 0.0
            
        elif strategy == ExecutionStrategy.ROUTER:
            # Good for routing to specialists
            score += 0.2 if len(set(cap.split(':')[0] for cap in task_analysis.tool_requirements)) > 1 else 0.1
            
        elif strategy == ExecutionStrategy.ORCHESTRATOR:
            # Good for complex coordinated tasks
            score += 0.3 if task_analysis.coordination_needs else 0.1
            score += 0.2 if task_analysis.interdependencies else 0.1
            
        elif strategy == ExecutionStrategy.SWARM:
            # Good for dynamic, conversational tasks
            score += 0.3 if "conversation" in task_analysis.description.lower() else 0.1
            score += 0.2 if task_analysis.complexity_score >= 6 else 0.0
            
        elif strategy == ExecutionStrategy.EVALUATOR_OPTIMIZER:
            # Good for high-quality requirements
            score += 0.4 if task_analysis.quality_requirements in ["high", "critical"] else 0.1
            score += 0.1 if task_analysis.time_sensitivity == "low" else 0.0
            
        elif strategy == ExecutionStrategy.ADAPTIVE_HYBRID:
            # Good for very complex tasks
            score += 0.4 if task_analysis.complexity_score >= 8 else 0.0
        
        # Historical performance factor
        if strategy.value in self.strategy_performance:
            historical_score = self.strategy_performance[strategy.value].get("success_rate", 0.5)
            score += historical_score * 0.1
        
        # Tool availability factor
        available_tool_names = [tool.name for tool in available_tools]
        required_tools = await self._find_required_tools(
            task_analysis.tool_requirements, available_tools
        )
        tool_availability = len(required_tools) / max(1, len(task_analysis.tool_requirements))
        score += tool_availability * 0.1
        
        return min(1.0, score)
    
    async def _generate_strategy_reasoning(self, 
                                         strategy: ExecutionStrategy,
                                         task_analysis: TaskAnalysis,
                                         available_tools: List[MCPToolInfo]) -> str:
        """Generate human-readable reasoning for strategy selection"""
        
        reasons = []
        
        # Complexity reasoning
        reasons.append(f"Task complexity ({task_analysis.complexity_score}/10) fits {strategy.value} pattern")
        
        # Tool requirements
        tool_count = len(task_analysis.tool_requirements)
        if tool_count == 1:
            reasons.append("Single tool requirement suggests direct execution")
        elif tool_count <= 3:
            reasons.append("Moderate tool requirements allow for focused approach")
        else:
            reasons.append("Multiple tools require coordination")
        
        # Quality requirements
        if task_analysis.quality_requirements == "critical":
            reasons.append("Critical quality requirements demand iterative refinement")
        elif task_analysis.quality_requirements == "high":
            reasons.append("High quality requirements benefit from structured approach")
        
        # Parallel potential
        if task_analysis.parallel_potential > 0.7:
            reasons.append("High parallel potential enables concurrent execution")
        elif task_analysis.parallel_potential < 0.3:
            reasons.append("Low parallel potential requires sequential execution")
        
        # Interdependencies
        if task_analysis.interdependencies:
            reasons.append("Task interdependencies require coordinated execution")
        else:
            reasons.append("Independent subtasks allow flexible execution")
        
        # Strategy-specific reasoning
        strategy_specific = {
            ExecutionStrategy.DIRECT: "Simple execution with single agent",
            ExecutionStrategy.PARALLEL: "Parallel execution for independent subtasks",
            ExecutionStrategy.ROUTER: "Route to specialized agents for efficiency",
            ExecutionStrategy.ORCHESTRATOR: "Orchestrated coordination for complex workflow",
            ExecutionStrategy.SWARM: "Dynamic multi-agent collaboration",
            ExecutionStrategy.EVALUATOR_OPTIMIZER: "Iterative refinement for quality",
            ExecutionStrategy.ADAPTIVE_HYBRID: "Adaptive strategy for maximum flexibility"
        }
        
        reasons.append(strategy_specific[strategy])
        
        return "; ".join(reasons)
    
    async def _find_required_tools(self, 
                                 capabilities: List[str],
                                 available_tools: List[MCPToolInfo]) -> List[str]:
        """Find tools required for given capabilities"""
        
        required_tools = []
        
        for capability in capabilities:
            best_tools = await self.discovery.get_tools_for_capability(capability)
            
            if best_tools:
                # Select best available tool for this capability
                available_best = [tool for tool in best_tools 
                                if tool.name in [t.name for t in available_tools]]
                
                if available_best:
                    required_tools.append(available_best[0].name)
        
        return list(set(required_tools))  # Remove duplicates
    
    def _estimate_duration(self, 
                          strategy: ExecutionStrategy,
                          task_analysis: TaskAnalysis) -> float:
        """Estimate execution duration in minutes"""
        
        base_duration = task_analysis.complexity_score * 2  # 2 minutes per complexity point
        
        strategy_multipliers = {
            ExecutionStrategy.DIRECT: 1.0,
            ExecutionStrategy.PARALLEL: 0.7,  # Faster due to parallelization
            ExecutionStrategy.ROUTER: 1.1,   # Slight overhead for routing
            ExecutionStrategy.ORCHESTRATOR: 1.3,  # Coordination overhead
            ExecutionStrategy.SWARM: 1.2,    # Communication overhead
            ExecutionStrategy.EVALUATOR_OPTIMIZER: 2.0,  # Iteration overhead
            ExecutionStrategy.ADAPTIVE_HYBRID: 1.5  # Adaptation overhead
        }
        
        multiplier = strategy_multipliers.get(strategy, 1.0)
        
        # Quality requirements adjustment
        if task_analysis.quality_requirements == "critical":
            multiplier *= 1.5
        elif task_analysis.quality_requirements == "high":
            multiplier *= 1.2
        
        return base_duration * multiplier
    
    def _estimate_success_probability(self, 
                                    strategy: ExecutionStrategy,
                                    task_analysis: TaskAnalysis,
                                    available_tools: List[MCPToolInfo]) -> float:
        """Estimate probability of successful execution"""
        
        base_probability = 0.7  # Base 70% success rate
        
        # Complexity adjustment
        complexity_factor = max(0.2, 1.0 - (task_analysis.complexity_score - 5) * 0.1)
        base_probability *= complexity_factor
        
        # Tool availability adjustment
        required_tools = task_analysis.tool_requirements
        available_capabilities = len([tool for tool in available_tools 
                                    if any(cap.category.value in req for req in required_tools 
                                          for cap in tool.capabilities)])
        
        if required_tools:
            tool_factor = min(1.0, available_capabilities / len(required_tools))
            base_probability *= tool_factor
        
        # Strategy-specific adjustments
        strategy_adjustments = {
            ExecutionStrategy.DIRECT: 0.1 if task_analysis.complexity_score <= 3 else -0.1,
            ExecutionStrategy.PARALLEL: 0.1 if task_analysis.parallel_potential > 0.7 else -0.1,
            ExecutionStrategy.ORCHESTRATOR: 0.1 if task_analysis.coordination_needs else -0.1,
            ExecutionStrategy.EVALUATOR_OPTIMIZER: 0.2 if task_analysis.quality_requirements == "critical" else 0.0
        }
        
        adjustment = strategy_adjustments.get(strategy, 0.0)
        base_probability += adjustment
        
        # Historical performance
        if strategy.value in self.strategy_performance:
            historical_success = self.strategy_performance[strategy.value].get("success_rate", 0.7)
            base_probability = (base_probability + historical_success) / 2
        
        return max(0.1, min(0.95, base_probability))
    
    async def update_strategy_performance(self, 
                                        strategy: ExecutionStrategy,
                                        success: bool,
                                        duration: float,
                                        quality_score: float):
        """Update performance tracking for a strategy"""
        
        strategy_key = strategy.value
        
        if strategy_key not in self.strategy_performance:
            self.strategy_performance[strategy_key] = {
                "success_rate": 0.0,
                "avg_duration": 0.0,
                "avg_quality": 0.0,
                "total_executions": 0,
                "successful_executions": 0
            }
        
        metrics = self.strategy_performance[strategy_key]
        metrics["total_executions"] += 1
        
        if success:
            metrics["successful_executions"] += 1
        
        # Update success rate
        metrics["success_rate"] = metrics["successful_executions"] / metrics["total_executions"]
        
        # Update average duration (exponential moving average)
        alpha = 0.1
        metrics["avg_duration"] = (
            alpha * duration + (1 - alpha) * metrics["avg_duration"]
        )
        
        # Update average quality
        metrics["avg_quality"] = (
            alpha * quality_score + (1 - alpha) * metrics["avg_quality"]
        )
        
        self.logger.info(f"Updated performance for {strategy_key}: "
                        f"success_rate={metrics['success_rate']:.2f}")
    
    def get_strategy_performance_summary(self) -> Dict[str, Any]:
        """Get summary of strategy performance metrics"""
        
        summary = {
            "total_strategies": len(self.strategy_performance),
            "strategies": {}
        }
        
        for strategy, metrics in self.strategy_performance.items():
            summary["strategies"][strategy] = {
                "success_rate": round(metrics["success_rate"], 3),
                "avg_duration": round(metrics["avg_duration"], 2),
                "avg_quality": round(metrics["avg_quality"], 3),
                "total_executions": metrics["total_executions"]
            }
        
        return summary
