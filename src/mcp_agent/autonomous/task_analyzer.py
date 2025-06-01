"""
Task Analyzer for autonomous MCP-Agent.

This module analyzes user tasks to understand their complexity, requirements,
and optimal execution strategies.
"""

import logging
import re
from typing import Dict, List, Set, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

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


class TaskAnalyzer:
    """
    Analyzes tasks to understand their requirements and optimal execution approach.

    This class uses pattern matching, keyword analysis, and heuristics to
    understand what a task requires and how it should be executed.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Keyword patterns for task type detection
        self.task_type_patterns = {
            TaskType.INFORMATION_RETRIEVAL: [
                "find",
                "search",
                "get",
                "fetch",
                "retrieve",
                "look up",
                "what is",
                "show me",
                "tell me about",
                "information about",
            ],
            TaskType.CONTENT_CREATION: [
                "create",
                "write",
                "generate",
                "make",
                "build",
                "compose",
                "draft",
                "design",
                "develop content",
            ],
            TaskType.DATA_ANALYSIS: [
                "analyze",
                "examine",
                "evaluate",
                "assess",
                "compare",
                "statistics",
                "trends",
                "patterns",
                "insights",
                "metrics",
            ],
            TaskType.FILE_OPERATIONS: [
                "file",
                "directory",
                "folder",
                "save",
                "load",
                "copy",
                "move",
                "delete",
                "read file",
                "write file",
            ],
            TaskType.WEB_AUTOMATION: [
                "website",
                "web page",
                "browser",
                "navigate",
                "click",
                "fill form",
                "screenshot",
                "scrape",
            ],
            TaskType.CODE_DEVELOPMENT: [
                "code",
                "program",
                "script",
                "function",
                "api",
                "repository",
                "commit",
                "github",
                "programming",
            ],
            TaskType.PROJECT_MANAGEMENT: [
                "project",
                "task",
                "milestone",
                "plan",
                "schedule",
                "organize",
                "manage",
                "workflow",
                "kanban",
            ],
            TaskType.RESEARCH: [
                "research",
                "investigate",
                "study",
                "explore",
                "survey",
                "comprehensive analysis",
                "deep dive",
            ],
            TaskType.COMMUNICATION: [
                "email",
                "message",
                "send",
                "notify",
                "communicate",
                "contact",
                "call",
                "meeting",
            ],
            TaskType.REASONING: [
                "think",
                "reason",
                "solve",
                "calculate",
                "logic",
                "problem solving",
                "decision",
                "strategy",
            ],
        }

        # Complexity indicators
        self.complexity_indicators = {
            TaskComplexity.SIMPLE: [
                "simple",
                "basic",
                "quick",
                "just",
                "only",
                "single",
            ],
            TaskComplexity.MODERATE: [
                "multiple",
                "several",
                "few",
                "some",
                "and",
                "then",
            ],
            TaskComplexity.COMPLEX: [
                "complex",
                "detailed",
                "comprehensive",
                "thorough",
                "analyze",
                "compare",
                "evaluate",
            ],
            TaskComplexity.VERY_COMPLEX: [
                "very complex",
                "sophisticated",
                "advanced",
                "multi-step",
                "orchestrate",
                "coordinate",
                "plan and execute",
            ],
        }

    def analyze_task(self, task_description: str) -> TaskAnalysis:
        """
        Analyze a task description and return detailed analysis.

        Args:
            task_description: Natural language description of the task

        Returns:
            TaskAnalysis with all detected requirements and recommendations
        """
        self.logger.debug(f"Analyzing task: {task_description}")

        # Detect task type
        task_type = self._detect_task_type(task_description)

        # Assess complexity
        complexity = self._assess_complexity(task_description)

        # Extract requirements
        requirements = self._extract_requirements(task_description, task_type)

        # Estimate steps
        estimated_steps = self._estimate_steps(task_description, complexity)

        # Recommend execution pattern
        recommended_pattern = self._recommend_pattern(
            task_type, complexity, requirements
        )

        # Get alternative patterns
        alternative_patterns = self._get_alternative_patterns(
            task_type, complexity, requirements
        )

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
        )

        self.logger.info(
            f"Task analysis complete: {task_type.value}, {complexity.value}, "
            f"{recommended_pattern.value} pattern recommended"
        )

        return analysis

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
            "and",
            "then",
            "after",
            "before",
            "while",
            "also",
            "additionally",
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

    def _extract_requirements(
        self, task_description: str, task_type: TaskType
    ) -> List[TaskRequirement]:
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

    def _recommend_pattern(
        self,
        task_type: TaskType,
        complexity: TaskComplexity,
        requirements: List[TaskRequirement],
    ) -> ExecutionPattern:
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

    def _get_alternative_patterns(
        self,
        task_type: TaskType,
        complexity: TaskComplexity,
        requirements: List[TaskRequirement],
    ) -> List[ExecutionPattern]:
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

    def _calculate_confidence(
        self, task_description: str, task_type: TaskType, complexity: TaskComplexity
    ) -> float:
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
            "github",
            "database",
            "sql",
            "web",
            "file",
            "email",
            "analyze",
            "create",
            "search",
            "automate",
        ]

        keyword_matches = sum(
            1 for keyword in specific_keywords if keyword in task_lower
        )
        confidence += min(keyword_matches * 0.1, 0.3)

        # Cap at 0.95
        return min(confidence, 0.95)

    def get_analysis_summary(self, analysis: TaskAnalysis) -> str:
        """Get a human-readable summary of the task analysis."""
        return (
            f"Task Type: {analysis.task_type.value}\n"
            f"Complexity: {analysis.complexity.value}\n"
            f"Recommended Pattern: {analysis.recommended_pattern.value}\n"
            f"Required Capabilities: {', '.join(cap.value for cap in analysis.required_capabilities)}\n"
            f"Estimated Steps: {analysis.estimated_steps}\n"
            f"Confidence: {analysis.confidence:.2f}"
        )
