"""
Learning System Data Models for MCP-Agent

This module defines the core data structures used throughout the learning system.
All models are designed for high performance and minimal memory footprint.
"""

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Union


class PatternType(Enum):
    """Types of patterns that can be learned."""
    
    EXECUTION_PATTERN = "execution_pattern"
    USER_PREFERENCE = "user_preference"
    PERFORMANCE_OPTIMIZATION = "performance_optimization"
    TASK_CLASSIFICATION = "task_classification"
    AGENT_SELECTION = "agent_selection"
    WORKFLOW_ROUTING = "workflow_routing"


class LearningPhase(Enum):
    """Learning system phases."""
    
    INITIALIZATION = "initialization"
    PATTERN_COLLECTION = "pattern_collection"
    ANALYSIS = "analysis"
    OPTIMIZATION = "optimization"
    APPLICATION = "application"


@dataclass
class ExecutionPattern:
    """
    Represents a learned pattern from task execution.
    
    Designed for minimal memory footprint and fast serialization.
    """
    
    id: Optional[str] = None
    task_type: str = ""
    pattern_used: str = ""
    execution_time: float = 0.0
    success_rate: float = 1.0
    confidence_score: float = 0.0
    agent_count: int = 1
    complexity_level: str = "simple"
    tools_used: List[str] = field(default_factory=list)
    context_factors: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    usage_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage."""
        return {
            "id": self.id,
            "task_type": self.task_type,
            "pattern_used": self.pattern_used,
            "execution_time": self.execution_time,
            "success_rate": self.success_rate,
            "confidence_score": self.confidence_score,
            "agent_count": self.agent_count,
            "complexity_level": self.complexity_level,
            "tools_used": ",".join(self.tools_used),
            "context_factors": str(self.context_factors),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "usage_count": self.usage_count
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExecutionPattern":
        """Create from dictionary (database retrieval)."""
        tools_used = data.get("tools_used", "").split(",") if data.get("tools_used") else []
        tools_used = [tool.strip() for tool in tools_used if tool.strip()]
        
        try:
            context_factors = eval(data.get("context_factors", "{}"))
            if not isinstance(context_factors, dict):
                context_factors = {}
        except:
            context_factors = {}
        
        return cls(
            id=data.get("id"),
            task_type=data.get("task_type", ""),
            pattern_used=data.get("pattern_used", ""),
            execution_time=float(data.get("execution_time", 0.0)),
            success_rate=float(data.get("success_rate", 1.0)),
            confidence_score=float(data.get("confidence_score", 0.0)),
            agent_count=int(data.get("agent_count", 1)),
            complexity_level=data.get("complexity_level", "simple"),
            tools_used=tools_used,
            context_factors=context_factors,
            created_at=float(data.get("created_at", time.time())),
            updated_at=float(data.get("updated_at", time.time())),
            usage_count=int(data.get("usage_count", 0))
        )


@dataclass
class LearningContext:
    """
    Context information for learning operations.
    
    Provides all necessary context for making learning decisions.
    """
    
    task_description: str = ""
    current_pattern: str = ""
    available_tools: List[str] = field(default_factory=list)
    user_preferences: Dict[str, Any] = field(default_factory=dict)
    performance_history: Dict[str, float] = field(default_factory=dict)
    session_data: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    
    def get_context_signature(self) -> str:
        """Generate a unique signature for this context."""
        import hashlib
        
        context_str = f"{self.task_description}_{self.current_pattern}_{len(self.available_tools)}"
        return hashlib.md5(context_str.encode()).hexdigest()[:12]


@dataclass
class PerformanceMetrics:
    """
    Performance tracking data for learning optimization.
    """
    
    component_name: str = ""
    metric_name: str = ""
    metric_value: float = 0.0
    baseline_value: float = 0.0
    improvement_percentage: float = 0.0
    sample_count: int = 1
    confidence_interval: float = 0.95
    measured_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def calculate_improvement(self) -> float:
        """Calculate improvement percentage."""
        if self.baseline_value == 0:
            return 0.0
        return ((self.metric_value - self.baseline_value) / self.baseline_value) * 100


@dataclass
class LearningMetrics:
    """
    Metrics for learning system performance.
    """
    
    patterns_learned: int = 0
    learning_accuracy: float = 0.0
    adaptation_speed: float = 0.0
    memory_usage_mb: float = 0.0
    learning_overhead_ms: float = 0.0
    database_performance_ms: float = 0.0
    pattern_cache_hits: int = 0
    pattern_cache_misses: int = 0
    last_updated: float = field(default_factory=time.time)
    
    def get_cache_hit_ratio(self) -> float:
        """Calculate cache hit ratio."""
        total = self.pattern_cache_hits + self.pattern_cache_misses
        return (self.pattern_cache_hits / total) if total > 0 else 0.0


class LearningModule(ABC):
    """
    Abstract base class for all learning modules.
    
    Provides a consistent interface for different types of learning.
    """
    
    def __init__(self, name: str):
        self.name = name
        self.enabled = True
        self.learning_phase = LearningPhase.INITIALIZATION
        self.metrics = LearningMetrics()
    
    @abstractmethod
    async def learn_from_execution(self, pattern: ExecutionPattern) -> bool:
        """Learn from a completed execution pattern."""
        pass
    
    @abstractmethod
    async def get_recommendations(self, context: LearningContext) -> List[Dict[str, Any]]:
        """Get recommendations based on learned patterns."""
        pass
    
    @abstractmethod
    async def update_performance_metrics(self, metrics: PerformanceMetrics) -> None:
        """Update performance tracking metrics."""
        pass
    
    @abstractmethod
    def get_learning_status(self) -> Dict[str, Any]:
        """Get current learning status and metrics."""
        pass
    
    def enable(self) -> None:
        """Enable this learning module."""
        self.enabled = True
    
    def disable(self) -> None:
        """Disable this learning module."""
        self.enabled = False
    
    def is_enabled(self) -> bool:
        """Check if this learning module is enabled."""
        return self.enabled


@dataclass
class PatternFilters:
    """
    Filters for querying patterns from the learning database.
    """
    
    pattern_type: Optional[PatternType] = None
    task_type: Optional[str] = None
    min_confidence: float = 0.0
    min_success_rate: float = 0.0
    max_age_seconds: Optional[float] = None
    limit: int = 100
    offset: int = 0
    
    def to_sql_conditions(self) -> tuple[str, List[Any]]:
        """Convert filters to SQL WHERE conditions and parameters."""
        conditions = []
        params = []
        
        if self.pattern_type:
            conditions.append("pattern_type = ?")
            params.append(self.pattern_type.value)
        
        if self.task_type:
            conditions.append("task_type = ?")
            params.append(self.task_type)
        
        if self.min_confidence > 0:
            conditions.append("confidence_score >= ?")
            params.append(self.min_confidence)
        
        if self.min_success_rate > 0:
            conditions.append("success_rate >= ?")
            params.append(self.min_success_rate)
        
        if self.max_age_seconds:
            min_timestamp = time.time() - self.max_age_seconds
            conditions.append("created_at >= ?")
            params.append(min_timestamp)
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        where_clause += f" ORDER BY confidence_score DESC, success_rate DESC LIMIT {self.limit} OFFSET {self.offset}"
        
        return where_clause, params
