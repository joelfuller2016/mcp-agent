"""
Test suite for Adaptive Learning Engine Foundation

This test validates the core learning infrastructure including:
- AdaptiveLearningEngine initialization and basic operations
- ExecutionPattern tracking and caching
- LearningModule registration and management
- Performance metrics and monitoring
"""

import asyncio
import time
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from mcp_agent.learning.adaptive_learning_engine import AdaptiveLearningEngine
from mcp_agent.learning.learning_models import (
    ExecutionPattern, 
    LearningContext, 
    PerformanceMetrics,
    LearningModule,
    PatternType
)


class TestLearningModule(LearningModule):
    """Test learning module for validation."""
    
    def __init__(self, name: str):
        super().__init__(name)
        self.learned_patterns = []
        self.recommendations_provided = 0
    
    async def learn_from_execution(self, pattern: ExecutionPattern) -> bool:
        """Learn from execution pattern."""
        self.learned_patterns.append(pattern)
        return True
    
    async def get_recommendations(self, context: LearningContext) -> list:
        """Get recommendations."""
        self.recommendations_provided += 1
        return [{
            "pattern": "test_pattern",
            "confidence": 0.85,
            "source": "test_module"
        }]
    
    async def update_performance_metrics(self, metrics: PerformanceMetrics) -> None:
        """Update performance metrics."""
        pass
    
    def get_learning_status(self) -> dict:
        """Get learning status."""
        return {
            "patterns_learned": len(self.learned_patterns),
            "recommendations_provided": self.recommendations_provided
        }


async def test_adaptive_learning_engine():
    """Test the AdaptiveLearningEngine implementation."""
    
    print("Testing Adaptive Learning Engine Foundation")
    print("=" * 60)
    
    # Test 1: Engine Initialization
    print("\nTest 1: Engine Initialization")
    engine = AdaptiveLearningEngine()
    
    assert not engine.is_initialized, "Engine should not be initialized initially"
    
    init_success = await engine.initialize()
    assert init_success, "Engine initialization should succeed"
    assert engine.is_initialized, "Engine should be marked as initialized"
    
    print("✅ Engine initialization successful")
    
    # Test 2: Learning Module Registration
    print("\nTest 2: Learning Module Registration")
    
    test_module = TestLearningModule("test_module")
    registration_success = await engine.register_learning_module(test_module)
    
    assert registration_success, "Module registration should succeed"
    assert "test_module" in engine.learning_modules, "Module should be in registry"
    assert engine.learning_modules["test_module"].is_enabled(), "Module should be enabled"
    
    print("✅ Learning module registration successful")
    
    # Test 3: Execution Pattern Tracking
    print("\nTest 3: Execution Pattern Tracking")
    
    # Create test execution pattern
    pattern = ExecutionPattern(
        task_type="test_task",
        pattern_used="direct",
        execution_time=0.005,
        success_rate=1.0,
        confidence_score=0.9,
        tools_used=["filesystem", "fetch"]
    )
    
    # Track pattern
    start_time = time.perf_counter()
    tracking_success = await engine.track_execution_pattern(pattern)
    tracking_time = (time.perf_counter() - start_time) * 1000
    
    assert tracking_success, "Pattern tracking should succeed"
    assert tracking_time < 0.1, f"Tracking should be fast (<0.1ms), took {tracking_time:.4f}ms"
    assert len(engine.pattern_cache) > 0, "Pattern should be cached"
    
    print(f"✅ Pattern tracking successful (took {tracking_time:.4f}ms)")
    
    # Test 4: Recommendations
    print("\nTest 4: Learning Recommendations")
    
    context = LearningContext(
        task_description="Test task for recommendations",
        current_pattern="direct",
        available_tools=["filesystem", "fetch"]
    )
    
    start_time = time.perf_counter()
    recommendations = await engine.get_recommendations(context)
    recommendation_time = (time.perf_counter() - start_time) * 1000
    
    assert isinstance(recommendations, list), "Recommendations should be a list"
    assert len(recommendations) > 0, "Should get at least one recommendation"
    assert recommendation_time < 1.0, f"Recommendations should be fast (<1ms), took {recommendation_time:.4f}ms"
    
    print(f"✅ Recommendations successful (got {len(recommendations)} recommendations in {recommendation_time:.4f}ms)")
    
    # Test 5: Performance Metrics
    print("\nTest 5: Performance Metrics")
    
    metrics = PerformanceMetrics(
        component_name="test_component",
        metric_name="response_time",
        metric_value=0.015,
        baseline_value=0.020
    )
    
    metrics_success = await engine.update_performance_metrics(metrics)
    assert metrics_success, "Performance metrics update should succeed"
    
    print("✅ Performance metrics update successful")
    
    # Test 6: Learning Status
    print("\nTest 6: Learning Status")
    
    status = engine.get_learning_status()
    
    assert isinstance(status, dict), "Status should be a dictionary"
    assert status["initialized"] == True, "Status should show initialized"
    assert "test_module" in status["registered_modules"], "Test module should be listed"
    assert status["cache_size"] > 0, "Cache should have entries"
    
    print("✅ Learning status retrieval successful")
    
    # Test 7: Performance Optimization
    print("\nTest 7: Performance Optimization")
    
    optimization_results = await engine.optimize_performance()
    
    assert isinstance(optimization_results, dict), "Optimization results should be a dictionary"
    assert "optimization_time_ms" in optimization_results, "Should include optimization time"
    
    print("✅ Performance optimization successful")
    
    # Test 8: Module Learning Verification
    print("\nTest 8: Module Learning Verification")
    
    # Wait for async learning to complete
    await asyncio.sleep(0.01)
    
    module_status = test_module.get_learning_status()
    assert module_status["patterns_learned"] > 0, "Module should have learned patterns"
    assert module_status["recommendations_provided"] > 0, "Module should have provided recommendations"
    
    print("✅ Module learning verification successful")
    
    # Test 9: Resource Cleanup
    print("\nTest 9: Resource Cleanup")
    
    await engine.shutdown()
    assert not engine.is_initialized, "Engine should be shutdown"
    
    print("✅ Resource cleanup successful")
    
    # Final Performance Report
    print("\n" + "=" * 60)
    print("ADAPTIVE LEARNING ENGINE FOUNDATION: ALL TESTS PASSED ✅")
    print(f"Pattern tracking performance: {tracking_time:.4f}ms (target: <0.01ms)")
    print(f"Recommendation performance: {recommendation_time:.4f}ms (target: <1.0ms)")
    print(f"Cache hit ratio: {engine.metrics.get_cache_hit_ratio():.2%}")
    print("Foundation is ready for next phase implementation")
    print("=" * 60)


async def performance_benchmark():
    """Benchmark the learning engine performance."""
    
    print("\nPerformance Benchmark")
    print("-" * 30)
    
    engine = AdaptiveLearningEngine()
    await engine.initialize()
    
    # Register test module
    test_module = TestLearningModule("benchmark_module")
    await engine.register_learning_module(test_module)
    
    # Benchmark pattern tracking
    patterns_to_track = 1000
    start_time = time.perf_counter()
    
    for i in range(patterns_to_track):
        pattern = ExecutionPattern(
            task_type=f"benchmark_task_{i % 10}",
            pattern_used="direct",
            execution_time=0.001 + (i % 5) * 0.001,
            success_rate=0.95 + (i % 5) * 0.01,
            confidence_score=0.8 + (i % 2) * 0.1
        )
        await engine.track_execution_pattern(pattern)
    
    total_time = time.perf_counter() - start_time
    avg_time_per_pattern = (total_time / patterns_to_track) * 1000
    
    print(f"Tracked {patterns_to_track} patterns in {total_time:.4f}s")
    print(f"Average time per pattern: {avg_time_per_pattern:.6f}ms")
    print(f"Target: <0.01ms per pattern")
    
    if avg_time_per_pattern < 0.01:
        print("✅ Performance benchmark PASSED")
    else:
        print("⚠️ Performance benchmark needs optimization")
    
    await engine.shutdown()


if __name__ == "__main__":
    # Run tests
    asyncio.run(test_adaptive_learning_engine())
    
    # Run performance benchmark
    asyncio.run(performance_benchmark())
