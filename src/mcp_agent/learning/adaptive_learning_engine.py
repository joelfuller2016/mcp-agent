"""
Adaptive Learning Engine for MCP-Agent

The AdaptiveLearningEngine is the central coordinator for all learning activities
in the MCP-Agent autonomous framework. It manages learning modules, tracks execution
patterns, and provides intelligent recommendations based on learned knowledge.

Key Features:
- Sub-millisecond learning operations (<0.01ms overhead)
- Async, non-blocking architecture
- Pattern caching for high performance
- Module-based extensibility
- Performance monitoring and optimization
"""

import asyncio
import logging
import time
import weakref
from typing import Dict, List, Optional, Any, Type, Set
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
import uuid

from .learning_models import (
    ExecutionPattern,
    LearningContext,
    PerformanceMetrics,
    LearningModule,
    LearningMetrics,
    PatternType,
    LearningPhase
)


class AdaptiveLearningEngine:
    """
    Central coordinator for all learning activities in MCP-Agent.
    
    This engine manages multiple learning modules, coordinates pattern tracking,
    and provides intelligent recommendations based on accumulated knowledge.
    
    Design Principles:
    - Minimal performance overhead (<0.01ms per learning operation)
    - Async-first architecture for non-blocking operations
    - Extensible module system for different learning types
    - High-performance pattern caching
    - Graceful degradation if learning fails
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Learning modules registry
        self.learning_modules: Dict[str, LearningModule] = {}
        self.module_types: Dict[PatternType, List[LearningModule]] = defaultdict(list)
        
        # Performance tracking
        self.pattern_cache: Dict[str, ExecutionPattern] = {}
        self.cache_access_times: Dict[str, float] = {}
        self.metrics = LearningMetrics()
        
        # Async coordination
        self._lock = asyncio.Lock()
        self._executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="learning")
        
        # State management
        self.is_initialized = False
        self.learning_phase = LearningPhase.INITIALIZATION
        self._pattern_update_tasks: Set[asyncio.Task] = set()
        
        # Performance monitoring
        self._start_time = time.time()
        self._total_operations = 0
        self._last_metrics_update = time.time()
        
        self.logger.info("AdaptiveLearningEngine initialized")
    
    async def initialize(self) -> bool:
        """
        Initialize the learning engine.
        
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            start_time = time.perf_counter()
            
            # Initialize core components
            self.learning_phase = LearningPhase.INITIALIZATION
            
            # Clear any existing state
            await self._clear_cache()
            
            # Initialize metrics tracking
            self.metrics = LearningMetrics()
            self.metrics.last_updated = time.time()
            
            # Mark as initialized
            self.is_initialized = True
            self.learning_phase = LearningPhase.PATTERN_COLLECTION
            
            init_time = (time.perf_counter() - start_time) * 1000
            self.logger.info(f"AdaptiveLearningEngine initialized in {init_time:.3f}ms")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize AdaptiveLearningEngine: {e}")
            return False
    
    async def register_learning_module(self, module: LearningModule) -> bool:
        """
        Register a learning module with the engine.
        
        Args:
            module: The learning module to register
            
        Returns:
            True if registration successful, False otherwise
        """
        try:
            if not isinstance(module, LearningModule):
                raise ValueError(f"Module must inherit from LearningModule")
            
            async with self._lock:
                # Register module
                self.learning_modules[module.name] = module
                
                # Enable by default
                module.enable()
                
                self.logger.info(f"Registered learning module: {module.name}")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to register learning module {module.name}: {e}")
            return False
    
    async def unregister_learning_module(self, module_name: str) -> bool:
        """
        Unregister a learning module.
        
        Args:
            module_name: Name of the module to unregister
            
        Returns:
            True if unregistration successful, False otherwise
        """
        try:
            async with self._lock:
                if module_name in self.learning_modules:
                    del self.learning_modules[module_name]
                    self.logger.info(f"Unregistered learning module: {module_name}")
                    return True
                else:
                    self.logger.warning(f"Module {module_name} not found for unregistration")
                    return False
                    
        except Exception as e:
            self.logger.error(f"Failed to unregister learning module {module_name}: {e}")
            return False
    
    async def track_execution_pattern(self, pattern: ExecutionPattern) -> bool:
        """
        Track an execution pattern for learning.
        
        This is a high-performance, async method designed for minimal overhead.
        
        Args:
            pattern: The execution pattern to learn from
            
        Returns:
            True if tracking successful, False otherwise
        """
        if not self.is_initialized:
            return False
        
        start_time = time.perf_counter()
        
        try:
            # Generate unique pattern ID if not provided
            if not pattern.id:
                pattern.id = f"pattern_{uuid.uuid4().hex[:8]}"
            
            # Update timestamps
            pattern.updated_at = time.time()
            pattern.usage_count += 1
            
            # Cache the pattern for fast access
            cache_key = self._get_pattern_cache_key(pattern)
            self.pattern_cache[cache_key] = pattern
            self.cache_access_times[cache_key] = time.time()
            
            # Create async task for module learning (non-blocking)
            task = asyncio.create_task(self._notify_modules_async(pattern))
            self._pattern_update_tasks.add(task)
            task.add_done_callback(self._pattern_update_tasks.discard)
            
            # Update metrics
            self._total_operations += 1
            execution_time = (time.perf_counter() - start_time) * 1000
            self.metrics.learning_overhead_ms = execution_time
            
            # Update cache metrics
            self.metrics.pattern_cache_hits += 1
            
            # Log if overhead is too high
            if execution_time > 0.01:  # 0.01ms target
                self.logger.warning(f"Learning overhead: {execution_time:.4f}ms (target: <0.01ms)")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to track execution pattern: {e}")
            return False
    
    async def get_recommendations(self, context: LearningContext) -> List[Dict[str, Any]]:
        """
        Get learning-based recommendations for a given context.
        
        Args:
            context: The learning context for recommendations
            
        Returns:
            List of recommendations from all enabled learning modules
        """
        if not self.is_initialized:
            return []
        
        start_time = time.perf_counter()
        recommendations = []
        
        try:
            # Check cache first
            cache_key = context.get_context_signature()
            if cache_key in self.pattern_cache:
                cached_pattern = self.pattern_cache[cache_key]
                self.metrics.pattern_cache_hits += 1
                
                # Create basic recommendation from cached pattern
                recommendations.append({
                    "source": "cache",
                    "pattern": cached_pattern.pattern_used,
                    "confidence": cached_pattern.confidence_score,
                    "execution_time": cached_pattern.execution_time,
                    "success_rate": cached_pattern.success_rate
                })
            else:
                self.metrics.pattern_cache_misses += 1
            
            # Get recommendations from all enabled modules
            for module_name, module in self.learning_modules.items():
                if module.is_enabled():
                    try:
                        module_recommendations = await module.get_recommendations(context)
                        for rec in module_recommendations:
                            rec["source_module"] = module_name
                            recommendations.append(rec)
                    except Exception as e:
                        self.logger.warning(f"Module {module_name} failed to provide recommendations: {e}")
            
            # Sort by confidence score
            recommendations.sort(key=lambda x: x.get("confidence", 0.0), reverse=True)
            
            # Update performance metrics
            recommendation_time = (time.perf_counter() - start_time) * 1000
            self.metrics.adaptation_speed = recommendation_time
            
            return recommendations[:10]  # Return top 10 recommendations
            
        except Exception as e:
            self.logger.error(f"Failed to get recommendations: {e}")
            return []
    
    async def update_performance_metrics(self, metrics: PerformanceMetrics) -> bool:
        """
        Update performance metrics for learning optimization.
        
        Args:
            metrics: Performance metrics to update
            
        Returns:
            True if update successful, False otherwise
        """
        try:
            # Update learning metrics
            self.metrics.last_updated = time.time()
            
            # Notify all enabled modules
            for module in self.learning_modules.values():
                if module.is_enabled():
                    try:
                        await module.update_performance_metrics(metrics)
                    except Exception as e:
                        self.logger.warning(f"Module {module.name} failed to update metrics: {e}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update performance metrics: {e}")
            return False
    
    def get_learning_status(self) -> Dict[str, Any]:
        """
        Get comprehensive learning system status.
        
        Returns:
            Dictionary containing learning system status and metrics
        """
        try:
            # Calculate uptime
            uptime_seconds = time.time() - self._start_time
            
            # Collect module statuses
            module_statuses = {}
            for name, module in self.learning_modules.items():
                module_statuses[name] = {
                    "enabled": module.is_enabled(),
                    "phase": module.learning_phase.value,
                    "status": module.get_learning_status()
                }
            
            return {
                "initialized": self.is_initialized,
                "learning_phase": self.learning_phase.value,
                "uptime_seconds": uptime_seconds,
                "total_operations": self._total_operations,
                "registered_modules": list(self.learning_modules.keys()),
                "module_statuses": module_statuses,
                "cache_size": len(self.pattern_cache),
                "cache_hit_ratio": self.metrics.get_cache_hit_ratio(),
                "learning_overhead_ms": self.metrics.learning_overhead_ms,
                "adaptation_speed_ms": self.metrics.adaptation_speed,
                "patterns_learned": self.metrics.patterns_learned,
                "memory_usage_mb": self.metrics.memory_usage_mb,
                "last_updated": self.metrics.last_updated
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get learning status: {e}")
            return {"error": str(e)}
    
    async def optimize_performance(self) -> Dict[str, Any]:
        """
        Optimize learning system performance.
        
        Returns:
            Dictionary containing optimization results
        """
        try:
            start_time = time.perf_counter()
            optimizations = []
            
            # Clean up old cache entries
            cache_cleaned = await self._cleanup_cache()
            optimizations.append(f"Cleaned {cache_cleaned} cache entries")
            
            # Update learning phase if needed
            if self.learning_phase == LearningPhase.PATTERN_COLLECTION:
                if self.metrics.patterns_learned > 100:
                    self.learning_phase = LearningPhase.ANALYSIS
                    optimizations.append("Advanced to ANALYSIS phase")
            
            # Calculate memory usage
            await self._update_memory_metrics()
            
            optimization_time = (time.perf_counter() - start_time) * 1000
            
            return {
                "optimization_time_ms": optimization_time,
                "optimizations_applied": optimizations,
                "cache_size": len(self.pattern_cache),
                "memory_usage_mb": self.metrics.memory_usage_mb
            }
            
        except Exception as e:
            self.logger.error(f"Failed to optimize performance: {e}")
            return {"error": str(e)}
    
    # Private helper methods
    
    def _get_pattern_cache_key(self, pattern: ExecutionPattern) -> str:
        """Generate cache key for execution pattern."""
        return f"{pattern.task_type}_{pattern.pattern_used}_{pattern.complexity_level}"
    
    async def _notify_modules_async(self, pattern: ExecutionPattern) -> None:
        """Notify all learning modules of new pattern (async)."""
        for module in self.learning_modules.values():
            if module.is_enabled():
                try:
                    await module.learn_from_execution(pattern)
                    self.metrics.patterns_learned += 1
                except Exception as e:
                    self.logger.warning(f"Module {module.name} failed to learn from pattern: {e}")
    
    async def _clear_cache(self) -> None:
        """Clear pattern cache."""
        self.pattern_cache.clear()
        self.cache_access_times.clear()
        self.metrics.pattern_cache_hits = 0
        self.metrics.pattern_cache_misses = 0
    
    async def _cleanup_cache(self, max_age_seconds: float = 3600) -> int:
        """Clean up old cache entries."""
        current_time = time.time()
        cleaned_count = 0
        
        # Find expired entries
        expired_keys = [
            key for key, access_time in self.cache_access_times.items()
            if current_time - access_time > max_age_seconds
        ]
        
        # Remove expired entries
        for key in expired_keys:
            self.pattern_cache.pop(key, None)
            self.cache_access_times.pop(key, None)
            cleaned_count += 1
        
        return cleaned_count
    
    async def _update_memory_metrics(self) -> None:
        """Update memory usage metrics."""
        import sys
        
        # Calculate approximate memory usage
        cache_size = sum(sys.getsizeof(pattern) for pattern in self.pattern_cache.values())
        module_size = sum(sys.getsizeof(module) for module in self.learning_modules.values())
        
        self.metrics.memory_usage_mb = (cache_size + module_size) / (1024 * 1024)
    
    async def shutdown(self) -> None:
        """Gracefully shutdown the learning engine."""
        try:
            self.logger.info("Shutting down AdaptiveLearningEngine...")
            
            # Wait for pending pattern updates
            if self._pattern_update_tasks:
                await asyncio.gather(*self._pattern_update_tasks, return_exceptions=True)
            
            # Shutdown executor
            self._executor.shutdown(wait=True)
            
            # Clear state
            await self._clear_cache()
            self.learning_modules.clear()
            self.is_initialized = False
            
            self.logger.info("AdaptiveLearningEngine shutdown complete")
            
        except Exception as e:
            self.logger.error(f"Error during learning engine shutdown: {e}")
