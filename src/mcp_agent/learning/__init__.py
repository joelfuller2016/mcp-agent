"""
MCP-Agent Learning System

This module provides adaptive learning capabilities for the MCP-Agent autonomous framework.
The learning system enables the agent to improve its decision-making and performance over time
through pattern recognition, user preference learning, and performance optimization.

Key Components:
- AdaptiveLearningEngine: Central coordinator for all learning activities
- LearningDatabase: Async SQLite-based storage for learning data
- ExecutionPatternLearner: Learns from workflow execution patterns
- UserPreferenceLearner: Personalizes behavior based on user preferences
- PerformanceOptimizer: Continuously optimizes algorithm performance

Performance Requirements:
- Sub-millisecond learning hooks (<0.01ms overhead)
- Async, non-blocking database operations (<0.005ms)
- Maintains 100% system reliability
- Backward compatible with existing components
"""

from .adaptive_learning_engine import AdaptiveLearningEngine
from .learning_models import (
    ExecutionPattern,
    LearningContext,
    PerformanceMetrics,
    LearningModule,
    PatternType,
    LearningMetrics
)

__all__ = [
    "AdaptiveLearningEngine",
    "ExecutionPattern", 
    "LearningContext",
    "PerformanceMetrics",
    "LearningModule",
    "PatternType",
    "LearningMetrics"
]

__version__ = "3.1.0"
