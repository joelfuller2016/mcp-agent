"""
Cached Task Analyzer for autonomous MCP-Agent with Performance Optimizations.

This module provides an enhanced TaskAnalyzer with intelligent caching to improve
performance consistency and reduce response time variance through LRU caching,
smart cache key generation, and performance monitoring.
"""

import logging
import re
import hashlib
import os
from typing import Dict, List, Set, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from functools import lru_cache, wraps
import time
from collections import defaultdict

from .tool_capability_mapper import ToolCategory


class TaskComplexity(Enum):
    """Task complexity levels."""

    SIMPLE = "simple"  # Single tool, single step
    MODERATE = "moderate"  # Multiple tools, sequential steps
    COMPLEX = "complex"  # Multiple agents, parallel execution
    VERY_COMPLEX = "very_complex"  # Multi-stage, requires planning


class TaskType(Enum):
    """Types of tasks."""

    INFORMATION_RETRIEVAL = "information_retrieval"
    CONTENT_CREATION = "content_creation"
    DATA_ANALYSIS = "data_analysis"
    FILE_OPERATIONS = "file_operations"
    WEB_AUTOMATION = "web_automation"
    CODE_DEVELOPMENT = "code_development"
    PROJECT_MANAGEMENT = "project_management"
    RESEARCH = "research"
    COMMUNICATION = "communication"
    REASONING = "reasoning"


class ExecutionPattern(Enum):
    """Recommended execution patterns."""

    DIRECT = "direct"  # Single agent, direct execution
    PARALLEL = "parallel"  # Multiple agents in parallel
    SEQUENTIAL = "sequential"  # Multiple agents in sequence
    ROUTER = "router"  # Route to appropriate agent
    ORCHESTRATOR = "orchestrator"  # Complex planning and execution
    SWARM = "swarm"  # Multi-agent collaboration
    EVALUATOR_OPTIMIZER = "evaluator_optimizer"  # Iterative refinement


@dataclass
class TaskRequirement:
    """Represents a requirement for task execution."""

    capability: ToolCategory
    priority: int  # 1-5, higher is more important
    optional: bool = False


@dataclass
class TaskAnalysis:
    """Results of task analysis."""

    task_description: str
    task_type: TaskType
    complexity: TaskComplexity
    requirements: List[TaskRequirement]
    estimated_steps: int
    recommended_pattern: ExecutionPattern
    alternative_patterns: List[ExecutionPattern]
    required_capabilities: Set[ToolCategory]
    confidence: float  # 0-1, confidence in analysis
    
    # Cache metadata
    cache_hit: bool = False
    analysis_time_ms: float = 0.0


@dataclass 
class CacheStatistics:
    """Cache performance statistics."""
    
    total_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    total_time_saved_ms: float = 0.0
    avg_hit_time_ms: float = 0.0
    avg_miss_time_ms: float = 0.0
    
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


class CacheUtilities:
    """Utilities for cache key generation and management."""
    
    # Common stop words to normalize task descriptions
    STOP_WORDS = {
        'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
        'of', 'with', 'by', 'from', 'up', 'about', 'into', 'through', 'during',
        'before', 'after', 'above', 'below', 'between', 'among', 'please', 'could',
        'would', 'should', 'can', 'may', 'might', 'will', 'shall'
    }
    
    @staticmethod
    def normalize_task_description(task_description: str) -> str:
        """Normalize task description for better cache key generation."""
        # Convert to lowercase
        normalized = task_description.lower().strip()
        
        # Remove extra whitespace
        normalized = re.sub(r'\s+', ' ', normalized)
        
        # Remove common punctuation at the end
        normalized = re.sub(r'[.!?]+$', '', normalized)
        
        # Optional: Remove stop words for better similarity matching
        # (This is conservative - only removing very common ones)
        words = normalized.split()
        filtered_words = [word for word in words if word not in CacheUtilities.STOP_WORDS or len(words) <= 3]
        
        # Only apply stop word filtering if it doesn't make the key too short
        if len(filtered_words) >= 2:
            normalized = ' '.join(filtered_words)
        
        return normalized
    
    @staticmethod
    def generate_cache_key(task_description: str, method_name: str = "", additional_data: Any = None) -> str:
        """Generate a consistent cache key for task data."""
        # Normalize the task description
        normalized_task = CacheUtilities.normalize_task_description(task_description)
        
        # Create the base key
        key_parts = [method_name, normalized_task]
        
        # Add additional data if provided
        if additional_data is not None:
            if hasattr(additional_data, 'value'):  # Handle Enum types
                key_parts.append(str(additional_data.value))
            else:
                key_parts.append(str(additional_data))
        
        # Create hash for consistent key length
        key_string = "|".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    @staticmethod
    def make_hashable(obj: Any) -> Any:
        """Convert potentially unhashable objects to hashable equivalents."""
        if isinstance(obj, dict):
            return tuple(sorted(obj.items()))
        elif isinstance(obj, list):
            return tuple(obj)
        elif isinstance(obj, set):
            return tuple(sorted(obj))
        else:
            return obj


def cache_aware(cache_size: int = 128, cache_stats_key: str = "default"):
    """
    Decorator for caching method results with performance tracking.
    
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
            
            # Check if we have cache info before call
            cache_info_before = cached_func.cache_info()
            
            try:
                # Call the cached function directly (lru_cache handles hashability)
                result = cached_func(self, *args, **kwargs)
                
                # Calculate timing
                end_time = time.perf_counter()
                execution_time_ms = (end_time - start_time) * 1000
                
                # Check if this was a cache hit
                cache_info_after = cached_func.cache_info()
                was_cache_hit = cache_info_after.hits > cache_info_before.hits
                
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
    """
    Enhanced TaskAnalyzer with intelligent caching for improved performance consistency.
    
    This analyzer maintains full backward compatibility while adding:
    - LRU caching for frequently accessed methods
    - Smart cache key generation based on task similarity  
    - Configurable cache sizes
    - Performance monitoring and statistics
    - Cache warming capabilities
    """

    def __init__(self, 
                 cache_config: Optional[Dict[str, int]] = None,
                 enable_cache_stats: bool = True):
        """
        Initialize the cached task analyzer.
        
        Args:
            cache_config: Dictionary of cache sizes for different methods
            enable_cache_stats: Whether to track cache performance statistics
        """
        self.logger = logging.getLogger(__name__)
        
        # Cache configuration with defaults
        self.cache_config = cache_config or {
            'analyze_task': int(os.getenv('TASK_ANALYZER_CACHE_SIZE', '128')),
            'detect_task_type': int(os.getenv('TASK_TYPE_CACHE_SIZE', '64')),
            'assess_complexity': int(os.getenv('COMPLEXITY_CACHE_SIZE', '64')),
            'extract_requirements': int(os.getenv('REQUIREMENTS_CACHE_SIZE', '32')),
            'estimate_steps': int(os.getenv('STEPS_CACHE_SIZE', '32'))
        }
        
        # Initialize cache statistics
        self._cache_stats = defaultdict(CacheStatistics) if enable_cache_stats else None
        
        # Keyword patterns for task type detection (cached as class attributes)
        self.task_type_patterns = {
            TaskType.INFORMATION_RETRIEVAL: [
                "find", "search", "get", "fetch", "retrieve", "look up",
                "what is", "show me", "tell me about", "information about",
            ],
            TaskType.CONTENT_CREATION: [
                "create", "write", "generate", "make", "build", "compose",
                "draft", "design", "develop content",
            ],
            TaskType.DATA_ANALYSIS: [
                "analyze", "examine", "evaluate", "assess", "compare",
                "statistics", "trends", "patterns", "insights", "metrics",
            ],
            TaskType.FILE_OPERATIONS: [
                "file", "directory", "folder", "save", "load", "copy",
                "move", "delete", "read file", "write file",
            ],
            TaskType.WEB_AUTOMATION: [
                "website", "web page", "browser", "navigate", "click",
                "fill form", "screenshot", "scrape",
            ],
            TaskType.CODE_DEVELOPMENT: [
                "code", "program", "script", "function", "api", "repository",
                "commit", "github", "programming",
            ],
            TaskType.PROJECT_MANAGEMENT: [
                "project", "task", "milestone", "plan", "schedule",
                "organize", "manage", "workflow", "kanban",
            ],
            TaskType.RESEARCH: [
                "research", "investigate", "study", "explore", "survey",
                "comprehensive analysis", "deep dive",
            ],
            TaskType.COMMUNICATION: [
                "email", "message", "send", "notify", "communicate",
                "contact", "call", "meeting",
            ],
            TaskType.REASONING: [
                "think", "reason", "solve", "calculate", "logic",
                "problem solving", "decision", "strategy",
            ],
        }

        # Complexity indicators
        self.complexity_indicators = {
            TaskComplexity.SIMPLE: [
                "simple", "basic", "quick", "just", "only", "single",
            ],
            TaskComplexity.MODERATE: [
                "multiple", "several", "few", "some", "and", "then",
            ],
            TaskComplexity.COMPLEX: [
                "complex", "detailed", "comprehensive", "thorough",
                "analyze", "compare", "evaluate",
            ],
            TaskComplexity.VERY_COMPLEX: [
                "very complex", "sophisticated", "advanced", "multi-step",
                "orchestrate", "coordinate", "plan and execute",
            ],
        }

    def analyze_task(self, task_description: str) -> TaskAnalysis:
        """
        Analyze a task description and return detailed analysis with caching.

        Args:
            task_description: Natural language description of the task

        Returns:
            TaskAnalysis with all detected requirements and recommendations
        """
        start_time = time.perf_counter()
        
        # Generate cache key for the entire analysis
        cache_key = CacheUtilities.generate_cache_key(task_description, "analyze_task")
        
        self.logger.debug(f"Analyzing task: {task_description}")

        # Check if we have cached result
        cached_result = self._get_cached_analysis(cache_key)
        if cached_result:
            cached_result.cache_hit = True
            cached_result.analysis_time_ms = (time.perf_counter() - start_time) * 1000
            self.logger.debug(f"Cache hit for task analysis: {cache_key[:8]}...")
            return cached_result

        # Perform full analysis
        task_type = self._detect_task_type_cached(task_description)
        complexity = self._assess_complexity_cached(task_description)
        requirements = self._extract_requirements_cached(task_description, task_type)
        estimated_steps = self._estimate_steps_cached(task_description, complexity)
        
        # Recommend execution pattern
        recommended_pattern = self._recommend_pattern(task_type, complexity, requirements)
        
        # Get alternative patterns
        alternative_patterns = self._get_alternative_patterns(task_type, complexity, requirements)
        
        # Extract required capabilities
        required_capabilities = {
            req.capability for req in requirements if not req.optional
        }
        
        # Calculate confidence
        confidence = self._calculate_confidence(task_description, task_type, complexity)

        analysis = TaskAnalysis(
            task_description=task_description,
            task_type=task_type,
            complexity=complexity,
            requirements=requirements,
            estimated_steps=estimated_steps,
            recommended_pattern=recommended_pattern,
            alternative_patterns=alternative_patterns,
            required_capabilities=required_capabilities,
            confidence=confidence,
            cache_hit=False,
            analysis_time_ms=(time.perf_counter() - start_time) * 1000
        )

        # Cache the result
        self._cache_analysis(cache_key, analysis)

        self.logger.info(
            f"Task analysis complete: {task_type.value}, {complexity.value}, "
            f"{recommended_pattern.value} pattern recommended"
        )

        return analysis

    @cache_aware(cache_size=64, cache_stats_key="detect_task_type")
    def _detect_task_type_cached(self, task_description: str) -> TaskType:
        """Cached version of task type detection."""
        return self._detect_task_type(task_description)

    @cache_aware(cache_size=64, cache_stats_key="assess_complexity")  
    def _assess_complexity_cached(self, task_description: str) -> TaskComplexity:
        """Cached version of complexity assessment."""
        return self._assess_complexity(task_description)

    @cache_aware(cache_size=32, cache_stats_key="extract_requirements")
    def _extract_requirements_cached(self, task_description: str, task_type: TaskType) -> List[TaskRequirement]:
        """Cached version of requirements extraction."""
        return self._extract_requirements(task_description, task_type)

    @cache_aware(cache_size=32, cache_stats_key="estimate_steps")
    def _estimate_steps_cached(self, task_description: str, complexity: TaskComplexity) -> int:
        """Cached version of step estimation."""
        return self._estimate_steps(task_description, complexity)

    # Original methods (unchanged for compatibility)
    def _detect_task_type(self, task_description: str) -> TaskType:
        """Detect the primary type of the task."""
        task_lower = task_description.lower()
        scores = {}

        for task_type, keywords in self.task_type_patterns.items():
            score = sum(1 for keyword in keywords if keyword in task_lower)
            if score > 0:
                scores[task_type] = score

        if scores:
            return max(scores, key=scores.get)
        else:
            return TaskType.INFORMATION_RETRIEVAL  # Default

    def _assess_complexity(self, task_description: str) -> TaskComplexity:
        """Assess the complexity of the task."""
        task_lower = task_description.lower()

        # Count complexity indicators
        complexity_scores = {}
        for complexity, indicators in self.complexity_indicators.items():
            score = sum(1 for indicator in indicators if indicator in task_lower)
            complexity_scores[complexity] = score

        # Additional heuristics
        # Length-based complexity
        word_count = len(task_description.split())
        if word_count > 50:
            complexity_scores[TaskComplexity.VERY_COMPLEX] += 2
        elif word_count > 25:
            complexity_scores[TaskComplexity.COMPLEX] += 1
        elif word_count > 10:
            complexity_scores[TaskComplexity.MODERATE] += 1

        # Multiple verbs indicate complexity
        action_words = [
            "and", "then", "after", "before", "while", "also", "additionally",
        ]
        action_count = sum(1 for word in action_words if word in task_lower)
        if action_count >= 3:
            complexity_scores[TaskComplexity.VERY_COMPLEX] += 2
        elif action_count >= 2:
            complexity_scores[TaskComplexity.COMPLEX] += 1
        elif action_count >= 1:
            complexity_scores[TaskComplexity.MODERATE] += 1

        # Determine final complexity
        if complexity_scores:
            return max(complexity_scores, key=complexity_scores.get)
        else:
            return TaskComplexity.SIMPLE

    def _extract_requirements(self, task_description: str, task_type: TaskType) -> List[TaskRequirement]:
        """Extract capability requirements from the task."""
        requirements = []
        task_lower = task_description.lower()

        # Map task types to likely requirements
        base_requirements = {
            TaskType.INFORMATION_RETRIEVAL: [
                TaskRequirement(ToolCategory.SEARCH, 5),
                TaskRequirement(ToolCategory.WEB, 4),
                TaskRequirement(ToolCategory.FILE_SYSTEM, 3, optional=True),
            ],
            TaskType.CONTENT_CREATION: [
                TaskRequirement(ToolCategory.CREATION, 5),
                TaskRequirement(ToolCategory.FILE_SYSTEM, 4),
                TaskRequirement(ToolCategory.WEB, 2, optional=True),
            ],
            TaskType.DATA_ANALYSIS: [
                TaskRequirement(ToolCategory.DATA, 5),
                TaskRequirement(ToolCategory.ANALYSIS, 5),
                TaskRequirement(ToolCategory.FILE_SYSTEM, 4),
            ],
            TaskType.FILE_OPERATIONS: [TaskRequirement(ToolCategory.FILE_SYSTEM, 5)],
            TaskType.WEB_AUTOMATION: [
                TaskRequirement(ToolCategory.WEB, 5),
                TaskRequirement(ToolCategory.AUTOMATION, 4),
            ],
            TaskType.CODE_DEVELOPMENT: [
                TaskRequirement(ToolCategory.DEVELOPMENT, 5),
                TaskRequirement(ToolCategory.FILE_SYSTEM, 4),
                TaskRequirement(ToolCategory.WEB, 3, optional=True),
            ],
            TaskType.PROJECT_MANAGEMENT: [
                TaskRequirement(ToolCategory.AUTOMATION, 5),
                TaskRequirement(ToolCategory.FILE_SYSTEM, 4),
                TaskRequirement(ToolCategory.COMMUNICATION, 3, optional=True),
            ],
            TaskType.RESEARCH: [
                TaskRequirement(ToolCategory.SEARCH, 5),
                TaskRequirement(ToolCategory.WEB, 5),
                TaskRequirement(ToolCategory.ANALYSIS, 4),
                TaskRequirement(ToolCategory.FILE_SYSTEM, 3),
            ],
            TaskType.COMMUNICATION: [TaskRequirement(ToolCategory.COMMUNICATION, 5)],
            TaskType.REASONING: [
                TaskRequirement(ToolCategory.COGNITIVE, 5),
                TaskRequirement(ToolCategory.REASONING, 5),
            ],
        }

        # Start with base requirements
        requirements.extend(base_requirements.get(task_type, []))

        # Add specific requirements based on keywords
        keyword_requirements = {
            "github": ToolCategory.DEVELOPMENT,
            "database": ToolCategory.DATA,
            "sql": ToolCategory.DATA,
            "web": ToolCategory.WEB,
            "browser": ToolCategory.WEB,
            "file": ToolCategory.FILE_SYSTEM,
            "search": ToolCategory.SEARCH,
            "analyze": ToolCategory.ANALYSIS,
            "think": ToolCategory.COGNITIVE,
            "reason": ToolCategory.REASONING,
            "automate": ToolCategory.AUTOMATION,
            "email": ToolCategory.COMMUNICATION,
        }

        for keyword, capability in keyword_requirements.items():
            if keyword in task_lower:
                # Add if not already present
                if not any(req.capability == capability for req in requirements):
                    requirements.append(TaskRequirement(capability, 4))

        return requirements

    def _estimate_steps(self, task_description: str, complexity: TaskComplexity) -> int:
        """Estimate the number of steps required."""
        base_steps = {
            TaskComplexity.SIMPLE: 1,
            TaskComplexity.MODERATE: 3,
            TaskComplexity.COMPLEX: 6,
            TaskComplexity.VERY_COMPLEX: 10,
        }

        steps = base_steps[complexity]

        # Adjust based on content
        task_lower = task_description.lower()
        step_indicators = ["and", "then", "after", "next", "also", "additionally"]
        additional_steps = sum(
            1 for indicator in step_indicators if indicator in task_lower
        )

        return steps + additional_steps

    def _recommend_pattern(self, task_type: TaskType, complexity: TaskComplexity, requirements: List[TaskRequirement]) -> ExecutionPattern:
        """Recommend the best execution pattern."""
        # Simple tasks use direct execution
        if complexity == TaskComplexity.SIMPLE:
            return ExecutionPattern.DIRECT

        # Very complex tasks need orchestration
        if complexity == TaskComplexity.VERY_COMPLEX:
            return ExecutionPattern.ORCHESTRATOR

        # Multiple high-priority requirements suggest parallel execution
        high_priority_reqs = [req for req in requirements if req.priority >= 4]
        if len(high_priority_reqs) >= 3:
            return ExecutionPattern.PARALLEL

        # Research tasks benefit from orchestration
        if task_type == TaskType.RESEARCH:
            return ExecutionPattern.ORCHESTRATOR

        # Analysis tasks might benefit from evaluator-optimizer
        if task_type == TaskType.DATA_ANALYSIS:
            return ExecutionPattern.EVALUATOR_OPTIMIZER

        # Communication tasks might use swarm
        if task_type == TaskType.COMMUNICATION:
            return ExecutionPattern.SWARM

        # Default to router for moderate complexity
        if complexity == TaskComplexity.MODERATE:
            return ExecutionPattern.ROUTER
        else:
            return ExecutionPattern.PARALLEL

    def _get_alternative_patterns(self, task_type: TaskType, complexity: TaskComplexity, requirements: List[TaskRequirement]) -> List[ExecutionPattern]:
        """Get alternative execution patterns."""
        recommended = self._recommend_pattern(task_type, complexity, requirements)

        alternatives = []

        # Always consider direct if not already recommended
        if recommended != ExecutionPattern.DIRECT:
            alternatives.append(ExecutionPattern.DIRECT)

        # Complex tasks can use multiple patterns
        if complexity in [TaskComplexity.COMPLEX, TaskComplexity.VERY_COMPLEX]:
            patterns = [
                ExecutionPattern.PARALLEL,
                ExecutionPattern.ORCHESTRATOR,
                ExecutionPattern.SWARM,
            ]
            alternatives.extend([p for p in patterns if p != recommended])

        # Remove duplicates and limit to 3 alternatives
        alternatives = list(dict.fromkeys(alternatives))[:3]

        return alternatives

    def _calculate_confidence(self, task_description: str, task_type: TaskType, complexity: TaskComplexity) -> float:
        """Calculate confidence in the analysis."""
        confidence = 0.5  # Base confidence

        # Higher confidence for longer, more detailed descriptions
        word_count = len(task_description.split())
        if word_count > 20:
            confidence += 0.2
        elif word_count > 10:
            confidence += 0.1

        # Higher confidence for specific keywords
        task_lower = task_description.lower()
        specific_keywords = [
            "github", "database", "sql", "web", "file", "email",
            "analyze", "create", "search", "automate",
        ]

        keyword_matches = sum(
            1 for keyword in specific_keywords if keyword in task_lower
        )
        confidence += min(keyword_matches * 0.1, 0.3)

        # Cap at 0.95
        return min(confidence, 0.95)

    # Cache management methods
    def _get_cached_analysis(self, cache_key: str) -> Optional[TaskAnalysis]:
        """Get cached analysis result if available."""
        # This is a simplified cache - in a full implementation, 
        # you might use Redis or a more sophisticated cache
        # For now, we rely on the method-level caching
        return None

    def _cache_analysis(self, cache_key: str, analysis: TaskAnalysis) -> None:
        """Cache analysis result."""
        # Cache storage implementation would go here
        pass

    def get_cache_statistics(self) -> Dict[str, CacheStatistics]:
        """Get comprehensive cache performance statistics."""
        return dict(self._cache_stats) if self._cache_stats else {}

    def clear_all_caches(self) -> None:
        """Clear all method caches."""
        methods_with_cache = [
            '_detect_task_type_cached',
            '_assess_complexity_cached', 
            '_extract_requirements_cached',
            '_estimate_steps_cached'
        ]
        
        for method_name in methods_with_cache:
            if hasattr(self, method_name):
                method = getattr(self, method_name)
                if hasattr(method, 'cache_clear'):
                    method.cache_clear()
                    self.logger.info(f"Cleared cache for {method_name}")
        
        # Reset cache statistics
        if self._cache_stats:
            self._cache_stats.clear()

    def get_cache_info(self) -> Dict[str, Any]:
        """Get cache information for all cached methods."""
        cache_info = {}
        methods_with_cache = [
            '_detect_task_type_cached',
            '_assess_complexity_cached',
            '_extract_requirements_cached', 
            '_estimate_steps_cached'
        ]
        
        for method_name in methods_with_cache:
            if hasattr(self, method_name):
                method = getattr(self, method_name)
                if hasattr(method, 'cache_info'):
                    cache_info[method_name] = method.cache_info()
        
        return cache_info

    def warm_cache(self, common_tasks: List[str]) -> None:
        """Warm up the cache with common task patterns."""
        self.logger.info(f"Warming cache with {len(common_tasks)} common tasks...")
        
        for task in common_tasks:
            try:
                # This will populate the caches
                self.analyze_task(task)
            except Exception as e:
                self.logger.warning(f"Failed to warm cache for task '{task}': {e}")
        
        self.logger.info("Cache warming complete")

    def get_analysis_summary(self, analysis: TaskAnalysis) -> str:
        """Get a human-readable summary of the task analysis."""
        cache_info = " (cached)" if analysis.cache_hit else ""
        timing_info = f" [{analysis.analysis_time_ms:.2f}ms]"
        
        return (
            f"Task Type: {analysis.task_type.value}\n"
            f"Complexity: {analysis.complexity.value}\n"
            f"Recommended Pattern: {analysis.recommended_pattern.value}\n"
            f"Required Capabilities: {', '.join(cap.value for cap in analysis.required_capabilities)}\n"
            f"Estimated Steps: {analysis.estimated_steps}\n"
            f"Confidence: {analysis.confidence:.2f}\n"
            f"Performance: {timing_info}{cache_info}"
        )


# Backward compatibility - alias to the original class name
TaskAnalyzer = CachedTaskAnalyzer
