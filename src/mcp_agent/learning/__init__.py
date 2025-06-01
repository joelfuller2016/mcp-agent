"""
MCP-Agent Learning System

This module provides adaptive learning capabilities for the MCP-Agent autonomous framework.
The learning system enables the agent to improve its decision-making and performance over time
through pattern recognition, user preference learning, and performance optimization.

Key Components:
- AdaptiveLearningEngine: Central coordinator for all learning activities
- LearningDatabase: Async SQLite-based storage for learning data (NEW in v3.1.1)
- ExecutionPatternLearner: Learns from workflow execution patterns
- UserPreferenceLearner: Personalizes behavior based on user preferences
- PerformanceOptimizer: Continuously optimizes algorithm performance

Performance Requirements:
- Sub-millisecond learning hooks (<0.01ms overhead)
- Async, non-blocking database operations (<5ms)
- Maintains 100% system reliability
- Backward compatible with existing components
"""

from .adaptive_learning_engine import AdaptiveLearningEngine
from .learning_database import LearningDatabase
from .learning_models import (
    ExecutionPattern,
    LearningContext,
    PerformanceMetrics,
    LearningModule,
    PatternType,
    LearningMetrics,
    PatternFilters
)

__all__ = [
    "AdaptiveLearningEngine",
    "LearningDatabase",
    "ExecutionPattern",
    "LearningContext",
    "PerformanceMetrics",
    "LearningModule",
    "PatternType",
    "LearningMetrics",
    "PatternFilters"
]

__version__ = "3.1.1"
