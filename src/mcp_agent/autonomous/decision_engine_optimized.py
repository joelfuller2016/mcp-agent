"""
Cached Decision Engine for Autonomous MCP Agent with Performance Optimizations

This module provides an enhanced AutonomousDecisionEngine with intelligent caching
to improve decision-making performance and reduce response time variance.
"""

import logging
import time
import hashlib
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from functools import lru_cache, wraps
from collections import defaultdict
import json

from .tool_capability_mapper import MCPServerProfile, ToolCapability


class WorkflowPattern(Enum):
    """Available workflow patterns"""

    DIRECT = "direct"  # Single agent with tools
    PARALLEL = "parallel"  # Fan-out to multiple agents
    ROUTER = "router"  # Route to best agent/tool
    SWARM = "swarm"  # Multi-agent coordination
    ORCHESTRATOR = "orchestrator"  # Complex planning and execution
    EVALUATOR_OPTIMIZER = "evaluator_optimizer"  # Iterative refinement


class TaskComplexity(Enum):
    """Task complexity levels"""

    SIMPLE = 1  # Single operation
    MODERATE = 2  # Multiple steps, sequential
    COMPLEX = 3  # Multiple steps, some parallelizable
    ADVANCED = 4  # Multi-agent coordination needed
    EXPERT = 5  # Complex planning and orchestration


@dataclass
class TaskAnalysis:
    """Analysis of a task including complexity and requirements"""

    description: str
    complexity: TaskComplexity
    required_capabilities: List[str]
    estimated_steps: int
    parallelizable: bool
    requires_iteration: bool
    requires_human_input: bool
    confidence: float
    
    # Cache metadata
    cache_hit: bool = False
    analysis_time_ms: float = 0.0


@dataclass
class StrategyRecommendation:
    """Recommendation for task execution strategy"""

    pattern: WorkflowPattern
    reasoning: str
    required_servers: List[str]
    estimated_execution_time: int
    confidence: float
    fallback_patterns: List[WorkflowPattern]
    
    # Cache metadata
    cache_hit: bool = False
    selection_time_ms: float = 0.0


@dataclass
class CacheStatistics:
    """Cache performance statistics for decision engine."""
    
    total_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    avg_hit_time_ms: float = 0.0
    avg_miss_time_ms: float = 0.0
    total_time_saved_ms: float = 0.0

    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate percentage."""
        if self.total_requests == 0:
            return 0.0
        return (self.cache_hits / self.total_requests) * 100

    @property
    def miss_rate(self) -> float:
        """Calculate cache miss rate percentage."""
        return 100.0 - self.hit_rate


class DecisionCacheUtilities:
    """Utilities for decision cache key generation and management."""
    
    # Common stop words for task normalization
    STOP_WORDS = {
        'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'up', 'about', 'into', 'through', 'during',
        'before', 'after', 'above', 'below', 'between', 'among', 'please', 'could',
        'would', 'should', 'can', 'may', 'might', 'will', 'shall'
    }
    
    @staticmethod
    def normalize_task_description(task_description: str) -> str:
        """Normalize task description for better cache key generation."""
        import re
        
        # Convert to lowercase and strip
        normalized = task_description.lower().strip()
        
        # Remove extra whitespace
        normalized = re.sub(r'\s+', ' ', normalized)
        
        # Remove common punctuation
        normalized = re.sub(r'[.!?]+$', '', normalized)
        
        # Remove stop words for better similarity matching
        words = normalized.split()
        filtered_words = [
            word for word in words 
            if word not in DecisionCacheUtilities.STOP_WORDS or len(words) <= 3
        ]
        
        # Only apply stop word filtering if it doesn't make the key too short
        if len(filtered_words) >= 2:
            normalized = ' '.join(filtered_words)
        
        return normalized
    
    @staticmethod
    def generate_cache_key(task_description: str, servers_config: List[str] = None) -> str:
        """Generate a consistent cache key for decision data."""
        # Normalize the task description
        normalized_task = DecisionCacheUtilities.normalize_task_description(task_description)
        
        # Create key components
        key_parts = [normalized_task]
        
        # Add server configuration if provided
        if servers_config:
            sorted_servers = sorted(servers_config)
            key_parts.append("|".join(sorted_servers))
        
        # Create hash for consistent key length
        key_string = "|".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()


def cache_decision_result(cache_size: int = 64, cache_stats_key: str = "default"):
    """
    Decorator for caching decision method results with performance tracking.
    
    Args:
        cache_size: Maximum number of cached results
        cache_stats_key: Key for tracking cache statistics
    """
    def decorator(func):
        # Create the cached version of the function
        cached_func = lru_cache(maxsize=cache_size)(func)
        
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # Start timing
            start_time = time.perf_counter()
            
            # Check cache info before call
            cache_info_before = cached_func.cache_info()
            
            try:
                # Call the cached function
                result = cached_func(self, *args, **kwargs)
                
                # Calculate timing
                end_time = time.perf_counter()
                execution_time_ms = (end_time - start_time) * 1000
                
                # Check if this was a cache hit
                cache_info_after = cached_func.cache_info()
                was_cache_hit = cache_info_after.hits > cache_info_before.hits
                
                # Update result with cache metadata if possible
                if hasattr(result, 'cache_hit'):
                    result.cache_hit = was_cache_hit
                if hasattr(result, 'analysis_time_ms'):
                    result.analysis_time_ms = execution_time_ms
                elif hasattr(result, 'selection_time_ms'):
                    result.selection_time_ms = execution_time_ms
                
                # Update cache statistics
                if hasattr(self, '_cache_stats') and self._cache_stats:
                    stats = self._cache_stats[cache_stats_key]
                    stats.total_requests += 1
                    
                    if was_cache_hit:
                        stats.cache_hits += 1
                        stats.avg_hit_time_ms = (
                            (stats.avg_hit_time_ms * (stats.cache_hits - 1) + execution_time_ms)
                            / stats.cache_hits
                        )
                    else:
                        stats.cache_misses += 1
                        stats.avg_miss_time_ms = (
                            (stats.avg_miss_time_ms * (stats.cache_misses - 1) + execution_time_ms)
                            / stats.cache_misses
                        )
                
                return result
                
            except Exception as e:
                # Update miss statistics on error
                if hasattr(self, '_cache_stats') and self._cache_stats:
                    stats = self._cache_stats[cache_stats_key]
                    stats.total_requests += 1
                    stats.cache_misses += 1
                raise e
        
        # Attach cache info access
        wrapper.cache_info = cached_func.cache_info
        wrapper.cache_clear = cached_func.cache_clear
        
        return wrapper
    return decorator


class CachedTaskAnalyzer:
    """Task analyzer with intelligent caching for improved performance."""

    def __init__(self, enable_cache_stats: bool = True):
        self.logger = logging.getLogger(__name__)
        self._cache_stats = defaultdict(CacheStatistics) if enable_cache_stats else None
        self._complexity_keywords = self._load_complexity_keywords()
        self._capability_keywords = self._load_capability_keywords()

    def _load_complexity_keywords(self) -> Dict[TaskComplexity, List[str]]:
        """Load keywords that indicate different complexity levels"""
        return {
            TaskComplexity.SIMPLE: [
                "read", "get", "show", "display", "list", "find", "check",
                "view", "see", "look", "what is", "tell me",
            ],
            TaskComplexity.MODERATE: [
                "create", "write", "update", "modify", "edit", "change",
                "search and", "analyze", "compare", "format", "convert",
            ],
            TaskComplexity.COMPLEX: [
                "integrate", "combine", "coordinate", "manage", "organize",
                "process multiple", "handle several", "work with different",
                "cross-reference", "correlate",
            ],
            TaskComplexity.ADVANCED: [
                "optimize", "intelligent", "adaptive", "autonomous", "decide",
                "collaborate", "negotiate", "multi-agent", "swarm", "coordinate teams",
            ],
            TaskComplexity.EXPERT: [
                "orchestrate", "comprehensive analysis", "end-to-end",
                "full lifecycle", "strategic planning", "complex workflow",
                "enterprise-scale",
            ],
        }

    def _load_capability_keywords(self) -> Dict[str, List[str]]:
        """Load keywords that indicate required capabilities"""
        return {
            "file_management": [
                "file", "folder", "directory", "document", "save",
                "load", "read file", "write file", "organize files",
            ],
            "web_automation": [
                "website", "web page", "browser", "navigate", "click",
                "form", "scrape", "screenshot", "web data",
            ],
            "information_retrieval": [
                "search", "find information", "look up", "research",
                "google", "web search", "query", "discover",
            ],
            "development": [
                "code", "repository", "github", "git", "programming",
                "software", "commit", "pull request", "issue", "development",
            ],
            "database": [
                "database", "query", "sql", "data analysis", "table",
                "records", "sqlite", "postgres", "data storage",
            ],
            "cognitive": [
                "think", "reason", "analyze", "decide", "plan",
                "strategy", "logic", "problem solving", "reasoning",
            ],
            "productivity": [
                "task", "project", "management", "organize", "schedule",
                "deadline", "milestone", "tracking",
            ],
            "communication": [
                "message", "email", "chat", "notification", "send",
                "receive", "slack", "teams", "communicate",
            ],
        }

    @cache_decision_result(cache_size=128, cache_stats_key="analyze_task")
    def analyze_task(self, task_description: str) -> TaskAnalysis:
        """Analyze a task with caching support."""
        self.logger.debug(f"Analyzing task: {task_description}")

        # Determine complexity
        complexity = self._assess_complexity(task_description)

        # Identify required capabilities
        required_capabilities = self._identify_capabilities(task_description)

        # Estimate steps
        estimated_steps = self._estimate_steps(task_description, complexity)

        # Check if parallelizable
        parallelizable = self._is_parallelizable(task_description)

        # Check if requires iteration
        requires_iteration = self._requires_iteration(task_description)

        # Check if requires human input
        requires_human_input = self._requires_human_input(task_description)

        # Calculate confidence
        confidence = self._calculate_confidence(task_description)

        analysis = TaskAnalysis(
            description=task_description,
            complexity=complexity,
            required_capabilities=required_capabilities,
            estimated_steps=estimated_steps,
            parallelizable=parallelizable,
            requires_iteration=requires_iteration,
            requires_human_input=requires_human_input,
            confidence=confidence,
        )

        self.logger.info(
            f"Task analysis complete: complexity={complexity.name}, "
            f"capabilities={required_capabilities}, steps={estimated_steps}"
        )

        return analysis

    def _assess_complexity(self, task_description: str) -> TaskComplexity:
        """Assess the complexity level of a task"""
        task_lower = task_description.lower()
        max_complexity = TaskComplexity.SIMPLE

        for complexity, keywords in self._complexity_keywords.items():
            if any(keyword in task_lower for keyword in keywords):
                if complexity.value > max_complexity.value:
                    max_complexity = complexity

        # Additional complexity indicators
        if " and " in task_lower or " then " in task_lower:
            max_complexity = TaskComplexity(min(max_complexity.value + 1, 5))

        if len(task_description.split()) > 30:
            max_complexity = TaskComplexity(min(max_complexity.value + 1, 5))

        return max_complexity

    def _identify_capabilities(self, task_description: str) -> List[str]:
        """Identify required capabilities from task description"""
        task_lower = task_description.lower()
        required_capabilities = []

        for capability, keywords in self._capability_keywords.items():
            if any(keyword in task_lower for keyword in keywords):
                required_capabilities.append(capability)

        return required_capabilities

    def _estimate_steps(self, task_description: str, complexity: TaskComplexity) -> int:
        """Estimate number of steps required"""
        base_steps = {
            TaskComplexity.SIMPLE: 1,
            TaskComplexity.MODERATE: 3,
            TaskComplexity.COMPLEX: 7,
            TaskComplexity.ADVANCED: 12,
            TaskComplexity.EXPERT: 20,
        }

        # Count explicit step indicators
        step_indicators = (
            task_description.lower().count(" and ")
            + task_description.lower().count(" then ")
            + task_description.lower().count(",")
        )

        return base_steps[complexity] + step_indicators

    def _is_parallelizable(self, task_description: str) -> bool:
        """Check if task can be parallelized"""
        parallel_indicators = [
            "simultaneously", "at the same time", "in parallel", "concurrently",
            "multiple", "different", "various", "several",
        ]

        sequential_indicators = [
            "then", "after", "next", "following", "subsequently",
            "once", "step by step", "in order", "sequential",
        ]

        task_lower = task_description.lower()

        parallel_score = sum(
            1 for indicator in parallel_indicators if indicator in task_lower
        )
        sequential_score = sum(
            1 for indicator in sequential_indicators if indicator in task_lower
        )

        return parallel_score > sequential_score

    def _requires_iteration(self, task_description: str) -> bool:
        """Check if task requires iterative refinement"""
        iteration_indicators = [
            "improve", "optimize", "refine", "iterate", "perfect",
            "enhance", "better", "quality", "review", "feedback", "revise",
        ]

        task_lower = task_description.lower()
        return any(indicator in task_lower for indicator in iteration_indicators)

    def _requires_human_input(self, task_description: str) -> bool:
        """Check if task requires human input"""
        human_indicators = [
            "approve", "confirm", "review", "check with", "ask",
            "verify", "permission", "authorization", "human", "manual", "interactive",
        ]

        task_lower = task_description.lower()
        return any(indicator in task_lower for indicator in human_indicators)

    def _calculate_confidence(self, task_description: str) -> float:
        """Calculate confidence in task analysis"""
        confidence = 0.8

        # Higher confidence for clear, specific tasks
        if len(task_description.split()) > 5:
            confidence += 0.1

        # Lower confidence for vague tasks
        vague_indicators = ["something", "somehow", "maybe", "perhaps", "might"]
        if any(indicator in task_description.lower() for indicator in vague_indicators):
            confidence -= 0.2

        # Higher confidence for tasks with specific verbs
        specific_verbs = ["create", "read", "update", "delete", "search", "analyze"]
        if any(verb in task_description.lower() for verb in specific_verbs):
            confidence += 0.1

        return max(0.0, min(1.0, confidence))


class CachedStrategySelector:
    """Strategy selector with intelligent caching for pattern selection."""

    def __init__(self, enable_cache_stats: bool = True):
        self.logger = logging.getLogger(__name__)
        self._cache_stats = defaultdict(CacheStatistics) if enable_cache_stats else None
        self._pattern_criteria = self._load_pattern_criteria()

    def _load_pattern_criteria(self) -> Dict[WorkflowPattern, Dict[str, Any]]:
        """Load criteria for selecting each workflow pattern"""
        return {
            WorkflowPattern.DIRECT: {
                "max_complexity": TaskComplexity.MODERATE,
                "max_steps": 3,
                "parallelizable": False,
                "single_capability": True,
                "description": "Single agent with direct tool access",
            },
            WorkflowPattern.PARALLEL: {
                "min_complexity": TaskComplexity.MODERATE,
                "parallelizable": True,
                "multiple_capabilities": True,
                "independent_subtasks": True,
                "description": "Fan-out to specialized agents, fan-in results",
            },
            WorkflowPattern.ROUTER: {
                "min_capabilities": 2,
                "classification_needed": True,
                "single_best_choice": True,
                "description": "Route to most appropriate agent or tool",
            },
            WorkflowPattern.SWARM: {
                "min_complexity": TaskComplexity.ADVANCED,
                "multi_agent_coordination": True,
                "conversational": True,
                "handoffs_needed": True,
                "description": "Multi-agent collaboration with handoffs",
            },
            WorkflowPattern.ORCHESTRATOR: {
                "min_complexity": TaskComplexity.COMPLEX,
                "min_steps": 5,
                "planning_required": True,
                "dependencies": True,
                "description": "High-level planning with automatic parallelization",
            },
            WorkflowPattern.EVALUATOR_OPTIMIZER: {
                "requires_iteration": True,
                "quality_focus": True,
                "refinement_needed": True,
                "description": "Iterative refinement with evaluation",
            },
        }

    @cache_decision_result(cache_size=64, cache_stats_key="select_strategy")
    def select_strategy(
        self, task_analysis: TaskAnalysis, available_servers: List[MCPServerProfile]
    ) -> StrategyRecommendation:
        """Select optimal strategy with caching support."""
        self.logger.debug(
            f"Selecting strategy for {task_analysis.complexity.name} task"
        )

        # Score each pattern
        pattern_scores = {}
        for pattern in WorkflowPattern:
            pattern_scores[pattern] = self._score_pattern(
                pattern, task_analysis, available_servers
            )

        # Select best pattern
        best_pattern = max(pattern_scores.keys(), key=lambda p: pattern_scores[p])
        best_score = pattern_scores[best_pattern]

        # Generate reasoning
        reasoning = self._generate_reasoning(best_pattern, task_analysis)

        # Identify required servers
        required_servers = self._identify_required_servers(
            best_pattern, task_analysis, available_servers
        )

        # Estimate execution time
        execution_time = self._estimate_execution_time(best_pattern, task_analysis)

        # Select fallback patterns
        fallback_patterns = self._select_fallback_patterns(pattern_scores, best_pattern)

        recommendation = StrategyRecommendation(
            pattern=best_pattern,
            reasoning=reasoning,
            required_servers=required_servers,
            estimated_execution_time=execution_time,
            confidence=best_score,
            fallback_patterns=fallback_patterns,
        )

        self.logger.info(
            f"Selected strategy: {best_pattern.value} (confidence: {best_score:.2f})"
        )

        return recommendation

    def _score_pattern(
        self,
        pattern: WorkflowPattern,
        task_analysis: TaskAnalysis,
        available_servers: List[MCPServerProfile],
    ) -> float:
        """Score how well a pattern fits the task"""
        criteria = self._pattern_criteria[pattern]
        score = 0.0
        total_criteria = 0

        # Complexity checks
        if "max_complexity" in criteria:
            total_criteria += 1
            if task_analysis.complexity.value <= criteria["max_complexity"].value:
                score += 1.0
            else:
                score -= 0.5

        if "min_complexity" in criteria:
            total_criteria += 1
            if task_analysis.complexity.value >= criteria["min_complexity"].value:
                score += 1.0
            else:
                score -= 0.3

        # Steps checks
        if "max_steps" in criteria:
            total_criteria += 1
            if task_analysis.estimated_steps <= criteria["max_steps"]:
                score += 1.0
            else:
                score -= 0.3

        if "min_steps" in criteria:
            total_criteria += 1
            if task_analysis.estimated_steps >= criteria["min_steps"]:
                score += 1.0
            else:
                score -= 0.2

        # Capability checks
        if "single_capability" in criteria and criteria["single_capability"]:
            total_criteria += 1
            if len(task_analysis.required_capabilities) == 1:
                score += 1.0
            else:
                score -= 0.4

        if "multiple_capabilities" in criteria and criteria["multiple_capabilities"]:
            total_criteria += 1
            if len(task_analysis.required_capabilities) > 1:
                score += 1.0
            else:
                score -= 0.3

        if "min_capabilities" in criteria:
            total_criteria += 1
            if len(task_analysis.required_capabilities) >= criteria["min_capabilities"]:
                score += 1.0
            else:
                score -= 0.4

        # Parallelization check
        if "parallelizable" in criteria:
            total_criteria += 1
            if task_analysis.parallelizable == criteria["parallelizable"]:
                score += 1.0
            else:
                score -= 0.2

        # Iteration check
        if "requires_iteration" in criteria and criteria["requires_iteration"]:
            total_criteria += 1
            if task_analysis.requires_iteration:
                score += 1.0
            else:
                score -= 0.6

        # Planning check
        if "planning_required" in criteria and criteria["planning_required"]:
            total_criteria += 1
            if task_analysis.complexity.value >= TaskComplexity.COMPLEX.value:
                score += 1.0
            else:
                score -= 0.4

        # Multi-agent coordination check
        if (
            "multi_agent_coordination" in criteria
            and criteria["multi_agent_coordination"]
        ):
            total_criteria += 1
            if (
                task_analysis.complexity.value >= TaskComplexity.ADVANCED.value
                and len(task_analysis.required_capabilities) > 2
            ):
                score += 1.0
            else:
                score -= 0.5

        # Normalize score
        if total_criteria > 0:
            score = max(0.0, score / total_criteria)
        else:
            score = 0.5  # Default score if no criteria

        return min(1.0, score)

    def _generate_reasoning(
        self, pattern: WorkflowPattern, task_analysis: TaskAnalysis
    ) -> str:
        """Generate human-readable reasoning for pattern selection"""
        base_reasoning = self._pattern_criteria[pattern]["description"]

        specific_reasons = []

        if pattern == WorkflowPattern.DIRECT:
            specific_reasons.append(
                f"Task complexity is {task_analysis.complexity.name}"
            )
            specific_reasons.append(
                f"Only {task_analysis.estimated_steps} steps required"
            )

        elif pattern == WorkflowPattern.PARALLEL:
            specific_reasons.append("Task can be parallelized")
            specific_reasons.append(
                f"Multiple capabilities needed: {task_analysis.required_capabilities}"
            )

        elif pattern == WorkflowPattern.ORCHESTRATOR:
            specific_reasons.append(
                f"Complex task with {task_analysis.estimated_steps} steps"
            )
            specific_reasons.append("Requires planning and coordination")

        elif pattern == WorkflowPattern.EVALUATOR_OPTIMIZER:
            specific_reasons.append("Task requires iterative refinement")
            specific_reasons.append("Quality improvement needed")

        elif pattern == WorkflowPattern.SWARM:
            specific_reasons.append("Multi-agent coordination required")
            specific_reasons.append("Complex interactions between agents")

        reasoning = f"{base_reasoning}. "
        if specific_reasons:
            reasoning += "Selected because: " + "; ".join(specific_reasons)

        return reasoning

    def _identify_required_servers(
        self,
        pattern: WorkflowPattern,
        task_analysis: TaskAnalysis,
        available_servers: List[MCPServerProfile],
    ) -> List[str]:
        """Identify which servers are needed for the selected pattern"""
        required_servers = []

        # Match capabilities to available servers
        for capability in task_analysis.required_capabilities:
            for server in available_servers:
                for server_capability in server.capabilities:
                    if capability in server_capability.category:
                        if server.name not in required_servers:
                            required_servers.append(server.name)
                        break

        return required_servers

    def _estimate_execution_time(
        self, pattern: WorkflowPattern, task_analysis: TaskAnalysis
    ) -> int:
        """Estimate execution time in seconds"""
        base_times = {
            WorkflowPattern.DIRECT: 10,
            WorkflowPattern.PARALLEL: 20,
            WorkflowPattern.ROUTER: 15,
            WorkflowPattern.SWARM: 45,
            WorkflowPattern.ORCHESTRATOR: 60,
            WorkflowPattern.EVALUATOR_OPTIMIZER: 90,
        }

        base_time = base_times[pattern]
        complexity_multiplier = task_analysis.complexity.value
        steps_multiplier = max(1, task_analysis.estimated_steps // 3)

        return base_time * complexity_multiplier * steps_multiplier

    def _select_fallback_patterns(
        self,
        pattern_scores: Dict[WorkflowPattern, float],
        best_pattern: WorkflowPattern,
    ) -> List[WorkflowPattern]:
        """Select fallback patterns in case the primary fails"""
        # Sort patterns by score, excluding the best one
        sorted_patterns = sorted(
            [(p, s) for p, s in pattern_scores.items() if p != best_pattern],
            key=lambda x: x[1],
            reverse=True,
        )

        # Return top 2 fallback patterns
        return [p for p, s in sorted_patterns[:2] if s > 0.3]


class CachedAutonomousDecisionEngine:
    """
    Enhanced autonomous decision engine with intelligent caching.
    
    Combines task analysis and strategy selection with performance optimizations:
    - LRU caching for decision results
    - Cache performance monitoring
    - Smart cache key generation
    - Memory-efficient cache management
    """

    def __init__(self, enable_cache_stats: bool = True):
        self.logger = logging.getLogger(__name__)
        
        # Initialize cached components
        self.task_analyzer = CachedTaskAnalyzer(enable_cache_stats)
        self.strategy_selector = CachedStrategySelector(enable_cache_stats)
        
        # Cache statistics aggregation
        self._cache_stats = defaultdict(CacheStatistics) if enable_cache_stats else None

    def analyze_and_recommend(
        self, task_description: str, available_servers: List[MCPServerProfile]
    ) -> Tuple[TaskAnalysis, StrategyRecommendation]:
        """Analyze task and recommend execution strategy with caching."""
        start_time = time.perf_counter()
        
        self.logger.info(f"Processing decision request for: {task_description[:50]}...")

        # Analyze the task (cached)
        task_analysis = self.task_analyzer.analyze_task(task_description)

        # Select strategy (cached)
        strategy_recommendation = self.strategy_selector.select_strategy(
            task_analysis, available_servers
        )
        
        # Calculate total decision time
        total_time_ms = (time.perf_counter() - start_time) * 1000

        self.logger.info(
            f"Decision complete: {strategy_recommendation.pattern.value} "
            f"pattern recommended with {strategy_recommendation.confidence:.2f} confidence "
            f"in {total_time_ms:.2f}ms"
        )

        return task_analysis, strategy_recommendation

    def explain_decision(
        self,
        task_analysis: TaskAnalysis,
        strategy_recommendation: StrategyRecommendation,
    ) -> str:
        """Generate detailed explanation of the decision"""
        
        # Add cache performance info
        cache_info = ""
        if hasattr(task_analysis, 'cache_hit') and hasattr(strategy_recommendation, 'cache_hit'):
            analysis_cache = "cached" if task_analysis.cache_hit else "computed"
            strategy_cache = "cached" if strategy_recommendation.cache_hit else "computed"
            
            analysis_time = getattr(task_analysis, 'analysis_time_ms', 0)
            strategy_time = getattr(strategy_recommendation, 'selection_time_ms', 0)
            
            cache_info = f"""
Performance Information:
- Task analysis: {analysis_cache} ({analysis_time:.2f}ms)
- Strategy selection: {strategy_cache} ({strategy_time:.2f}ms)
- Total decision time: {analysis_time + strategy_time:.2f}ms
"""

        explanation = f"""
Task Analysis:
- Complexity: {task_analysis.complexity.name}
- Required capabilities: {", ".join(task_analysis.required_capabilities)}
- Estimated steps: {task_analysis.estimated_steps}
- Parallelizable: {task_analysis.parallelizable}
- Requires iteration: {task_analysis.requires_iteration}
- Analysis confidence: {task_analysis.confidence:.2f}

Strategy Recommendation:
- Selected pattern: {strategy_recommendation.pattern.value.upper()}
- Reasoning: {strategy_recommendation.reasoning}
- Required servers: {", ".join(strategy_recommendation.required_servers)}
- Estimated execution time: {strategy_recommendation.estimated_execution_time}s
- Recommendation confidence: {strategy_recommendation.confidence:.2f}
- Fallback patterns: {", ".join([p.value for p in strategy_recommendation.fallback_patterns])}
{cache_info}"""
        
        return explanation
    
    def get_cache_statistics(self) -> Dict[str, CacheStatistics]:
        """Get comprehensive cache performance statistics."""
        combined_stats = {}
        
        # Get statistics from task analyzer
        if hasattr(self.task_analyzer, '_cache_stats') and self.task_analyzer._cache_stats:
            for key, stats in self.task_analyzer._cache_stats.items():
                combined_stats[f"task_analyzer_{key}"] = stats
        
        # Get statistics from strategy selector
        if hasattr(self.strategy_selector, '_cache_stats') and self.strategy_selector._cache_stats:
            for key, stats in self.strategy_selector._cache_stats.items():
                combined_stats[f"strategy_selector_{key}"] = stats
        
        return combined_stats
    
    def get_cache_performance_summary(self) -> Dict[str, Any]:
        """Get a summary of cache performance across all components."""
        stats = self.get_cache_statistics()
        
        if not stats:
            return {"cache_enabled": False}
        
        # Aggregate statistics
        total_requests = sum(s.total_requests for s in stats.values())
        total_hits = sum(s.cache_hits for s in stats.values())
        total_misses = sum(s.cache_misses for s in stats.values())
        
        avg_hit_time = 0.0
        avg_miss_time = 0.0
        
        if total_hits > 0:
            avg_hit_time = sum(s.avg_hit_time_ms * s.cache_hits for s in stats.values()) / total_hits
        
        if total_misses > 0:
            avg_miss_time = sum(s.avg_miss_time_ms * s.cache_misses for s in stats.values()) / total_misses
        
        hit_rate = (total_hits / max(total_requests, 1)) * 100
        
        return {
            "cache_enabled": True,
            "total_requests": total_requests,
            "cache_hits": total_hits,
            "cache_misses": total_misses,
            "hit_rate": round(hit_rate, 1),
            "avg_hit_time_ms": round(avg_hit_time, 2),
            "avg_miss_time_ms": round(avg_miss_time, 2),
            "performance_improvement": round(
                max(0, avg_miss_time - avg_hit_time), 2
            ) if avg_hit_time > 0 else 0,
            "time_saved_estimate_ms": round(
                total_hits * max(0, avg_miss_time - avg_hit_time), 2
            ) if avg_hit_time > 0 else 0,
        }
    
    def clear_all_caches(self) -> None:
        """Clear all caches in the decision engine."""
        # Clear task analyzer caches
        if hasattr(self.task_analyzer, 'analyze_task'):
            if hasattr(self.task_analyzer.analyze_task, 'cache_clear'):
                self.task_analyzer.analyze_task.cache_clear()
        
        # Clear strategy selector caches  
        if hasattr(self.strategy_selector, 'select_strategy'):
            if hasattr(self.strategy_selector.select_strategy, 'cache_clear'):
                self.strategy_selector.select_strategy.cache_clear()
        
        # Reset cache statistics
        if self.task_analyzer._cache_stats:
            self.task_analyzer._cache_stats.clear()
        if self.strategy_selector._cache_stats:
            self.strategy_selector._cache_stats.clear()
            
        self.logger.info("All decision engine caches cleared")

    def warm_cache(self, common_tasks: List[str], mock_servers: List[MCPServerProfile] = None) -> None:
        """Warm up caches with common task patterns."""
        if not mock_servers:
            # Create some mock servers for cache warming
            mock_servers = []
        
        self.logger.info(f"Warming decision engine cache with {len(common_tasks)} tasks...")
        
        for task in common_tasks:
            try:
                self.analyze_and_recommend(task, mock_servers)
            except Exception as e:
                self.logger.warning(f"Failed to warm cache for task '{task}': {e}")
        
        self.logger.info("Decision engine cache warming complete")


# Backward compatibility alias
AutonomousDecisionEngine = CachedAutonomousDecisionEngine
