"""
Task-Level Cached Task Analyzer with True Cache Hits

This implementation adds task-level caching to achieve actual cache hits
for identical and similar tasks.
"""

import logging
import re
import hashlib
import os
import time
from typing import Dict, List, Set, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from functools import lru_cache
from collections import defaultdict

from .tool_capability_mapper import ToolCategory


class TaskComplexity(Enum):
    """Task complexity levels."""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    VERY_COMPLEX = "very_complex"


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
    DIRECT = "direct"
    PARALLEL = "parallel"
    SEQUENTIAL = "sequential"
    ROUTER = "router"
    ORCHESTRATOR = "orchestrator"
    SWARM = "swarm"
    EVALUATOR_OPTIMIZER = "evaluator_optimizer"


@dataclass
class TaskRequirement:
    """Represents a requirement for task execution."""
    capability: ToolCategory
    priority: int
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
    confidence: float
    cache_hit: bool = False
    analysis_time_ms: float = 0.0


class TaskLevelCachedAnalyzer:
    """
    Task Analyzer with task-level caching for true cache hits.
    
    This implementation caches complete task analysis results
    using normalized task descriptions as keys.
    """

    def __init__(self, cache_size: int = 128):
        """Initialize with configurable cache size."""
        self.logger = logging.getLogger(__name__)
        self.cache_size = cache_size
        
        # Create cached analysis function
        self._cached_analyze = lru_cache(maxsize=cache_size)(self._analyze_task_internal)
        
        # Performance tracking
        self.cache_stats = {
            'total_requests': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'total_time_saved_ms': 0.0
        }

        # Initialize task patterns
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

    @staticmethod
    def normalize_task(task_description: str) -> str:
        """Normalize task description for caching."""
        # Convert to lowercase and strip
        normalized = task_description.lower().strip()
        
        # Remove extra whitespace
        normalized = re.sub(r'\s+', ' ', normalized)
        
        # Remove common punctuation
        normalized = re.sub(r'[.!?]+$', '', normalized)
        
        # Remove common articles and prepositions for better matching
        stop_words = {'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        words = normalized.split()
        
        # Only filter stop words if we have enough words left
        filtered_words = [w for w in words if w not in stop_words or len(words) <= 3]
        if len(filtered_words) >= 2:
            normalized = ' '.join(filtered_words)
        
        return normalized

    def analyze_task(self, task_description: str) -> TaskAnalysis:
        """
        Analyze a task with caching support.
        
        Args:
            task_description: Natural language description of the task
            
        Returns:
            TaskAnalysis with cache information
        """
        start_time = time.perf_counter()
        
        # Normalize task for cache key
        normalized_task = self.normalize_task(task_description)
        
        # Track cache stats
        self.cache_stats['total_requests'] += 1
        
        # Get cache info before call
        cache_info_before = self._cached_analyze.cache_info()
        
        # Call cached function
        result = self._cached_analyze(normalized_task)
        
        # Check if cache was hit
        cache_info_after = self._cached_analyze.cache_info()
        was_cache_hit = cache_info_after.hits > cache_info_before.hits
        
        # Update cache statistics
        if was_cache_hit:
            self.cache_stats['cache_hits'] += 1
        else:
            self.cache_stats['cache_misses'] += 1
        
        # Calculate timing
        end_time = time.perf_counter()
        analysis_time = (end_time - start_time) * 1000
        
        # Create final result with original task description
        final_result = TaskAnalysis(
            task_description=task_description,  # Keep original description
            task_type=result.task_type,
            complexity=result.complexity,
            requirements=result.requirements,
            estimated_steps=result.estimated_steps,
            recommended_pattern=result.recommended_pattern,
            alternative_patterns=result.alternative_patterns,
            required_capabilities=result.required_capabilities,
            confidence=result.confidence,
            cache_hit=was_cache_hit,
            analysis_time_ms=analysis_time
        )
        
        self.logger.debug(
            f"Task analysis: {task_description[:50]}... "
            f"({analysis_time:.2f}ms, {'cached' if was_cache_hit else 'computed'})"
        )
        
        return final_result

    def _analyze_task_internal(self, normalized_task: str) -> TaskAnalysis:
        """Internal analysis method that gets cached."""
        # Detect task type
        task_type = self._detect_task_type(normalized_task)
        
        # Assess complexity
        complexity = self._assess_complexity(normalized_task)
        
        # Extract requirements
        requirements = self._extract_requirements(normalized_task, task_type)
        
        # Estimate steps
        estimated_steps = self._estimate_steps(normalized_task, complexity)
        
        # Recommend execution pattern
        recommended_pattern = self._recommend_pattern(task_type, complexity, requirements)
        
        # Get alternative patterns
        alternative_patterns = self._get_alternative_patterns(task_type, complexity, requirements)
        
        # Extract required capabilities
        required_capabilities = {
            req.capability for req in requirements if not req.optional
        }
        
        # Calculate confidence
        confidence = self._calculate_confidence(normalized_task, task_type, complexity)

        return TaskAnalysis(
            task_description=normalized_task,
            task_type=task_type,
            complexity=complexity,
            requirements=requirements,
            estimated_steps=estimated_steps,
            recommended_pattern=recommended_pattern,
            alternative_patterns=alternative_patterns,
            required_capabilities=required_capabilities,
            confidence=confidence
        )

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
            return TaskType.INFORMATION_RETRIEVAL

    def _assess_complexity(self, task_description: str) -> TaskComplexity:
        """Assess the complexity of the task."""
        task_lower = task_description.lower()

        complexity_scores = {}
        for complexity, indicators in self.complexity_indicators.items():
            score = sum(1 for indicator in indicators if indicator in task_lower)
            complexity_scores[complexity] = score

        # Length-based complexity
        word_count = len(task_description.split())
        if word_count > 50:
            complexity_scores[TaskComplexity.VERY_COMPLEX] += 2
        elif word_count > 25:
            complexity_scores[TaskComplexity.COMPLEX] += 1
        elif word_count > 10:
            complexity_scores[TaskComplexity.MODERATE] += 1

        # Multiple action words indicate complexity
        action_words = ["and", "then", "after", "before", "while", "also", "additionally"]
        action_count = sum(1 for word in action_words if word in task_lower)
        if action_count >= 3:
            complexity_scores[TaskComplexity.VERY_COMPLEX] += 2
        elif action_count >= 2:
            complexity_scores[TaskComplexity.COMPLEX] += 1
        elif action_count >= 1:
            complexity_scores[TaskComplexity.MODERATE] += 1

        if complexity_scores:
            return max(complexity_scores, key=complexity_scores.get)
        else:
            return TaskComplexity.SIMPLE

    def _extract_requirements(self, task_description: str, task_type: TaskType) -> List[TaskRequirement]:
        """Extract capability requirements from the task."""
        requirements = []
        task_lower = task_description.lower()

        # Base requirements by task type
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

        requirements.extend(base_requirements.get(task_type, []))

        # Keyword-based requirements
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

        # Count step indicators
        task_lower = task_description.lower()
        step_indicators = ["and", "then", "after", "next", "also", "additionally"]
        additional_steps = sum(1 for indicator in step_indicators if indicator in task_lower)

        return steps + additional_steps

    def _recommend_pattern(self, task_type: TaskType, complexity: TaskComplexity, requirements: List[TaskRequirement]) -> ExecutionPattern:
        """Recommend the best execution pattern."""
        if complexity == TaskComplexity.SIMPLE:
            return ExecutionPattern.DIRECT

        if complexity == TaskComplexity.VERY_COMPLEX:
            return ExecutionPattern.ORCHESTRATOR

        high_priority_reqs = [req for req in requirements if req.priority >= 4]
        if len(high_priority_reqs) >= 3:
            return ExecutionPattern.PARALLEL

        if task_type == TaskType.RESEARCH:
            return ExecutionPattern.ORCHESTRATOR

        if task_type == TaskType.DATA_ANALYSIS:
            return ExecutionPattern.EVALUATOR_OPTIMIZER

        if task_type == TaskType.COMMUNICATION:
            return ExecutionPattern.SWARM

        if complexity == TaskComplexity.MODERATE:
            return ExecutionPattern.ROUTER
        else:
            return ExecutionPattern.PARALLEL

    def _get_alternative_patterns(self, task_type: TaskType, complexity: TaskComplexity, requirements: List[TaskRequirement]) -> List[ExecutionPattern]:
        """Get alternative execution patterns."""
        recommended = self._recommend_pattern(task_type, complexity, requirements)
        alternatives = []

        if recommended != ExecutionPattern.DIRECT:
            alternatives.append(ExecutionPattern.DIRECT)

        if complexity in [TaskComplexity.COMPLEX, TaskComplexity.VERY_COMPLEX]:
            patterns = [
                ExecutionPattern.PARALLEL,
                ExecutionPattern.ORCHESTRATOR,
                ExecutionPattern.SWARM,
            ]
            alternatives.extend([p for p in patterns if p != recommended])

        return list(dict.fromkeys(alternatives))[:3]

    def _calculate_confidence(self, task_description: str, task_type: TaskType, complexity: TaskComplexity) -> float:
        """Calculate confidence in the analysis."""
        confidence = 0.5

        word_count = len(task_description.split())
        if word_count > 20:
            confidence += 0.2
        elif word_count > 10:
            confidence += 0.1

        task_lower = task_description.lower()
        specific_keywords = [
            "github", "database", "sql", "web", "file", "email",
            "analyze", "create", "search", "automate",
        ]

        keyword_matches = sum(1 for keyword in specific_keywords if keyword in task_lower)
        confidence += min(keyword_matches * 0.1, 0.3)

        return min(confidence, 0.95)

    def get_cache_info(self) -> Dict[str, Any]:
        """Get cache information and statistics."""
        cache_info = self._cached_analyze.cache_info()
        
        return {
            'cache_stats': self.cache_stats,
            'cache_info': {
                'hits': cache_info.hits,
                'misses': cache_info.misses,
                'current_size': cache_info.currsize,
                'max_size': cache_info.maxsize
            },
            'hit_rate': (self.cache_stats['cache_hits'] / max(self.cache_stats['total_requests'], 1)) * 100
        }

    def clear_cache(self) -> None:
        """Clear the analysis cache."""
        self._cached_analyze.cache_clear()
        self.cache_stats = {
            'total_requests': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'total_time_saved_ms': 0.0
        }
        self.logger.info("Cache cleared")

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


# Alias for compatibility and testing
TaskAnalyzer = TaskLevelCachedAnalyzer
