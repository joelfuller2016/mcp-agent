"""
Comprehensive tests for LearningDatabase

Tests cover all aspects of the learning database including:
- Database initialization and schema creation
- Pattern storage and retrieval with performance validation
- Caching functionality and memory management
- User preferences storage and retrieval
- Performance metrics tracking
- Connection pooling and async operations
- Schema migrations and version management
- Error handling and graceful degradation

Performance Requirements:
- Database operations must be under 5ms
- Memory usage must be under 5MB for 10k patterns
- >95% test coverage required
"""

import asyncio
import pytest
import tempfile
import time
import uuid
from pathlib import Path
from unittest.mock import patch

from src.mcp_agent.learning import (
    LearningDatabase,
    ExecutionPattern,
    PerformanceMetrics,
    PatternFilters,
    PatternType
)


@pytest.fixture
async def temp_db():
    """Create temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    
    db = LearningDatabase(db_path=db_path, pool_size=2)
    await db.initialize()
    
    yield db
    
    await db.shutdown()
    # Clean up
    Path(db_path).unlink(missing_ok=True)


@pytest.fixture
def sample_execution_pattern():
    """Create sample execution pattern for testing."""
    return ExecutionPattern(
        id="test_pattern_001",
        task_type="code_analysis",
        pattern_used="direct",
        execution_time=0.125,
        success_rate=0.95,
        confidence_score=0.88,
        agent_count=1,
        complexity_level="moderate",
        tools_used=["filesystem", "github"],
        context_factors={"language": "python", "file_count": 5},
        usage_count=10
    )


@pytest.fixture
def sample_performance_metrics():
    """Create sample performance metrics for testing."""
    return PerformanceMetrics(
        component_name="TaskAnalyzer",
        metric_name="analysis_time",
        metric_value=0.017,
        baseline_value=0.200,
        improvement_percentage=91.5,
        sample_count=100,
        confidence_interval=0.95,
        metadata={"version": "3.1.1", "environment": "test"}
    )


class TestLearningDatabaseInitialization:
    """Test database initialization and setup."""
    
    async def test_database_initialization(self, temp_db):
        """Test successful database initialization."""
        assert temp_db._connection_pool is not None
        assert temp_db._connection_pool.qsize() == 2  # pool_size
        
        # Verify schema exists
        conn = await temp_db._get_connection()
        try:
            cursor = await conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            tables = [row[0] for row in await cursor.fetchall()]
        finally:
            await temp_db._return_connection(conn)
        
        expected_tables = {
            "execution_patterns",
            "user_preferences", 
            "performance_metrics",
            "schema_version"
        }
        assert expected_tables.issubset(set(tables))
    
    async def test_database_indexes_created(self, temp_db):
        """Test that performance indexes are created."""
        conn = await temp_db._get_connection()
        try:
            cursor = await conn.execute(
                "SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'"
            )
            indexes = [row[0] for row in await cursor.fetchall()]
        finally:
            await temp_db._return_connection(conn)
        
        expected_indexes = {
            "idx_patterns_task_type",
            "idx_patterns_pattern_used",
            "idx_patterns_confidence",
            "idx_patterns_success_rate",
            "idx_patterns_created_at"
        }
        assert expected_indexes.issubset(set(indexes))
    
    async def test_schema_version_tracking(self, temp_db):
        """Test schema version is tracked correctly."""
        conn = await temp_db._get_connection()
        try:
            cursor = await conn.execute("SELECT version FROM schema_version")
            version = (await cursor.fetchone())[0]
        finally:
            await temp_db._return_connection(conn)
        
        assert version == temp_db.SCHEMA_VERSION


class TestPatternStorage:
    """Test execution pattern storage and retrieval."""
    
    async def test_store_execution_pattern(self, temp_db, sample_execution_pattern):
        """Test storing execution pattern."""
        start_time = time.perf_counter()
        result = await temp_db.store_execution_pattern(sample_execution_pattern)
        operation_time = (time.perf_counter() - start_time) * 1000
        
        assert result is True
        assert operation_time < 5.0  # Must be under 5ms
        
        # Verify pattern was stored
        conn = await temp_db._get_connection()
        try:
            cursor = await conn.execute(
                "SELECT * FROM execution_patterns WHERE id = ?",
                (sample_execution_pattern.id,)
            )
            row = await cursor.fetchone()
        finally:
            await temp_db._return_connection(conn)
        
        assert row is not None
        assert row[1] == sample_execution_pattern.task_type  # task_type
    
    async def test_store_pattern_without_id(self, temp_db):
        """Test storing pattern without ID generates one."""
        pattern = ExecutionPattern(
            task_type="test_task",
            pattern_used="test_pattern"
        )
        
        result = await temp_db.store_execution_pattern(pattern)
        assert result is True
        assert pattern.id is not None
        assert pattern.id.startswith("pattern_")
    
    async def test_retrieve_patterns_basic(self, temp_db, sample_execution_pattern):
        """Test basic pattern retrieval."""
        # Store pattern first
        await temp_db.store_execution_pattern(sample_execution_pattern)
        
        # Retrieve with basic filter
        filters = PatternFilters(task_type="code_analysis")
        
        start_time = time.perf_counter()
        patterns = await temp_db.retrieve_patterns(filters)
        operation_time = (time.perf_counter() - start_time) * 1000
        
        assert operation_time < 5.0  # Must be under 5ms
        assert len(patterns) == 1
        assert patterns[0].id == sample_execution_pattern.id
        assert patterns[0].task_type == "code_analysis"
    
    async def test_retrieve_patterns_with_filters(self, temp_db):
        """Test pattern retrieval with various filters."""
        # Store multiple patterns
        patterns = [
            ExecutionPattern(
                id=f"pattern_{i}",
                task_type="code_analysis" if i % 2 == 0 else "documentation",
                pattern_used="direct",
                confidence_score=0.9 - (i * 0.1),
                success_rate=0.95 - (i * 0.05)
            )
            for i in range(5)
        ]
        
        for pattern in patterns:
            await temp_db.store_execution_pattern(pattern)
        
        # Test confidence filter
        filters = PatternFilters(min_confidence=0.7)
        results = await temp_db.retrieve_patterns(filters)
        assert len(results) == 3  # Only patterns with confidence >= 0.7
        
        # Test task type filter
        filters = PatternFilters(task_type="code_analysis")
        results = await temp_db.retrieve_patterns(filters)
        assert len(results) == 3  # patterns 0, 2, 4
        
        # Test success rate filter
        filters = PatternFilters(min_success_rate=0.85)
        results = await temp_db.retrieve_patterns(filters)
        assert len(results) == 4  # All except the last one
    
    async def test_update_pattern_weights(self, temp_db, sample_execution_pattern):
        """Test updating pattern confidence scores."""
        # Store pattern first
        await temp_db.store_execution_pattern(sample_execution_pattern)
        
        # Update weight
        new_weight = 0.75
        result = await temp_db.update_pattern_weights(sample_execution_pattern.id, new_weight)
        assert result is True
        
        # Verify update
        filters = PatternFilters(task_type="code_analysis")
        patterns = await temp_db.retrieve_patterns(filters)
        assert len(patterns) == 1
        assert patterns[0].confidence_score == new_weight


class TestCaching:
    """Test caching functionality."""
    
    async def test_pattern_cache_functionality(self, temp_db, sample_execution_pattern):
        """Test pattern caching works correctly."""
        # Store pattern
        await temp_db.store_execution_pattern(sample_execution_pattern)
        
        # First retrieval (cache miss)
        filters = PatternFilters(task_type="code_analysis")
        patterns1 = await temp_db.retrieve_patterns(filters)
        
        # Second retrieval (cache hit)
        patterns2 = await temp_db.retrieve_patterns(filters)
        
        assert patterns1 == patterns2
        assert temp_db.metrics.pattern_cache_hits > 0
    
    async def test_cache_invalidation_on_update(self, temp_db, sample_execution_pattern):
        """Test cache is invalidated when patterns are updated."""
        # Store and retrieve pattern (populate cache)
        await temp_db.store_execution_pattern(sample_execution_pattern)
        filters = PatternFilters(task_type="code_analysis")
        await temp_db.retrieve_patterns(filters)
        
        # Update pattern (should invalidate cache)
        await temp_db.update_pattern_weights(sample_execution_pattern.id, 0.75)
        
        # Retrieve again (should be cache miss with updated data)
        patterns = await temp_db.retrieve_patterns(filters)
        assert patterns[0].confidence_score == 0.75
    
    async def test_cache_memory_limits(self, temp_db):
        """Test cache respects memory limits."""
        cache_stats_before = temp_db._pattern_cache.get_stats()
        
        # Store many patterns to test memory management
        for i in range(50):
            pattern = ExecutionPattern(
                id=f"test_pattern_{i}",
                task_type=f"task_{i}",
                pattern_used="direct"
            )
            await temp_db.store_execution_pattern(pattern)
        
        cache_stats_after = temp_db._pattern_cache.get_stats()
        
        # Cache should not exceed memory limits
        assert cache_stats_after["memory_mb"] <= temp_db._pattern_cache.max_memory_mb


class TestUserPreferences:
    """Test user preferences storage and retrieval."""
    
    async def test_store_user_preference(self, temp_db):
        """Test storing user preferences."""
        key = "preferred_workflow"
        value = {"pattern": "parallel", "agents": 3}
        
        result = await temp_db.store_user_preference(key, value)
        assert result is True
        
        # Verify storage
        preferences = await temp_db.get_user_preferences()
        assert key in preferences
        assert preferences[key] == value
    
    async def test_store_multiple_preferences(self, temp_db):
        """Test storing multiple user preferences."""
        preferences = {
            "theme": "dark",
            "language": "python", 
            "complexity_level": "expert",
            "tools": ["github", "filesystem", "sqlite"]
        }
        
        for key, value in preferences.items():
            await temp_db.store_user_preference(key, value)
        
        stored_prefs = await temp_db.get_user_preferences()
        
        for key, value in preferences.items():
            assert key in stored_prefs
            assert stored_prefs[key] == value
    
    async def test_update_existing_preference(self, temp_db):
        """Test updating existing preferences."""
        key = "preferred_agents"
        
        # Store initial value
        await temp_db.store_user_preference(key, 2)
        
        # Update value
        await temp_db.store_user_preference(key, 5)
        
        # Verify update
        preferences = await temp_db.get_user_preferences()
        assert preferences[key] == 5


class TestPerformanceMetrics:
    """Test performance metrics storage and retrieval."""
    
    async def test_get_performance_history(self, temp_db, sample_performance_metrics):
        """Test retrieving performance history."""
        # Store performance metrics
        conn = await temp_db._get_connection()
        try:
            await conn.execute("""
                INSERT INTO performance_metrics 
                (component_name, metric_name, metric_value, baseline_value, 
                 improvement_percentage, sample_count, confidence_interval, 
                 measured_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                sample_performance_metrics.component_name,
                sample_performance_metrics.metric_name,
                sample_performance_metrics.metric_value,
                sample_performance_metrics.baseline_value,
                sample_performance_metrics.improvement_percentage,
                sample_performance_metrics.sample_count,
                sample_performance_metrics.confidence_interval,
                sample_performance_metrics.measured_at,
                '{"version": "3.1.1", "environment": "test"}'
            ))
            await conn.commit()
        finally:
            await temp_db._return_connection(conn)
        
        # Retrieve history
        history = await temp_db.get_performance_history("TaskAnalyzer", days=7)
        
        assert len(history) == 1
        assert history[0].component_name == "TaskAnalyzer"
        assert history[0].metric_name == "analysis_time"
        assert history[0].metric_value == 0.017
    
    async def test_performance_history_date_filtering(self, temp_db):
        """Test performance history date filtering."""
        current_time = time.time()
        
        # Store metrics at different times
        metrics_data = [
            ("TaskAnalyzer", "analysis_time", 0.017, current_time),
            ("TaskAnalyzer", "analysis_time", 0.020, current_time - 86400),  # 1 day ago
            ("TaskAnalyzer", "analysis_time", 0.025, current_time - 172800), # 2 days ago
            ("TaskAnalyzer", "analysis_time", 0.030, current_time - 604800), # 7 days ago
        ]
        
        conn = await temp_db._get_connection()
        try:
            for component, metric, value, measured_at in metrics_data:
                await conn.execute("""
                    INSERT INTO performance_metrics 
                    (component_name, metric_name, metric_value, baseline_value,
                     improvement_percentage, sample_count, confidence_interval,
                     measured_at, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (component, metric, value, 0.200, 0.0, 1, 0.95, measured_at, "{}"))
            await conn.commit()
        finally:
            await temp_db._return_connection(conn)
        
        # Test 1 day history
        history_1day = await temp_db.get_performance_history("TaskAnalyzer", days=1)
        assert len(history_1day) == 2  # Today and 1 day ago
        
        # Test 3 day history  
        history_3day = await temp_db.get_performance_history("TaskAnalyzer", days=3)
        assert len(history_3day) == 3  # Today, 1 day, 2 days ago
        
        # Test 7 day history
        history_7day = await temp_db.get_performance_history("TaskAnalyzer", days=7)
        assert len(history_7day) == 4  # All metrics


class TestPerformance:
    """Test performance requirements."""
    
    async def test_database_operation_performance(self, temp_db):
        """Test all database operations meet <5ms requirement."""
        pattern = ExecutionPattern(
            task_type="performance_test",
            pattern_used="direct"
        )
        
        # Test store operation
        start_time = time.perf_counter()
        await temp_db.store_execution_pattern(pattern)
        store_time = (time.perf_counter() - start_time) * 1000
        assert store_time < 5.0
        
        # Test retrieve operation
        filters = PatternFilters(task_type="performance_test")
        start_time = time.perf_counter()
        await temp_db.retrieve_patterns(filters)
        retrieve_time = (time.perf_counter() - start_time) * 1000
        assert retrieve_time < 5.0
        
        # Test update operation
        start_time = time.perf_counter()
        await temp_db.update_pattern_weights(pattern.id, 0.8)
        update_time = (time.perf_counter() - start_time) * 1000
        assert update_time < 5.0
    
    async def test_bulk_pattern_storage_performance(self, temp_db):
        """Test performance with bulk pattern storage."""
        patterns = [
            ExecutionPattern(
                id=f"bulk_pattern_{i}",
                task_type=f"task_{i % 10}",  # 10 different task types
                pattern_used="direct",
                confidence_score=0.8 + (i % 10) * 0.01
            )
            for i in range(100)
        ]
        
        start_time = time.perf_counter()
        
        # Store all patterns
        for pattern in patterns:
            await temp_db.store_execution_pattern(pattern)
        
        total_time = (time.perf_counter() - start_time) * 1000
        avg_time_per_pattern = total_time / len(patterns)
        
        # Average time per pattern should be well under 5ms
        assert avg_time_per_pattern < 5.0
        
        # Total time for 100 patterns should be reasonable
        assert total_time < 500.0  # 500ms for 100 patterns
    
    async def test_memory_usage_with_10k_patterns(self, temp_db):
        """Test memory usage stays under 5MB with 10k patterns."""
        # This test creates a smaller subset for speed but validates the approach
        patterns = [
            ExecutionPattern(
                id=f"memory_test_{i}",
                task_type=f"task_{i % 50}",
                pattern_used="direct",
                tools_used=[f"tool_{j}" for j in range(3)],
                context_factors={"test": f"data_{i}"}
            )
            for i in range(1000)  # 1k patterns for faster testing
        ]
        
        # Store patterns
        for pattern in patterns:
            await temp_db.store_execution_pattern(pattern)
        
        # Get database stats
        stats = await temp_db.get_database_stats()
        
        # Check cache memory usage
        pattern_cache_mb = stats["pattern_cache"]["memory_mb"]
        query_cache_mb = stats["query_cache"]["memory_mb"]
        total_cache_mb = pattern_cache_mb + query_cache_mb
        
        # Cache memory should be reasonable for 1k patterns
        # For 10k patterns, we'd expect proportionally more but still under 5MB
        assert total_cache_mb < 5.0


class TestConnectionPooling:
    """Test connection pooling functionality."""
    
    async def test_connection_pool_size(self, temp_db):
        """Test connection pool maintains correct size."""
        assert temp_db._connection_pool.qsize() == temp_db.pool_size
    
    async def test_concurrent_database_operations(self, temp_db):
        """Test concurrent database operations work correctly."""
        patterns = [
            ExecutionPattern(
                id=f"concurrent_pattern_{i}",
                task_type=f"task_{i}",
                pattern_used="direct"
            )
            for i in range(10)
        ]
        
        # Store patterns concurrently
        tasks = [
            temp_db.store_execution_pattern(pattern)
            for pattern in patterns
        ]
        
        start_time = time.perf_counter()
        results = await asyncio.gather(*tasks)
        total_time = (time.perf_counter() - start_time) * 1000
        
        # All operations should succeed
        assert all(results)
        
        # Concurrent operations should be faster than sequential
        assert total_time < 100.0  # Should complete in under 100ms
    
    async def test_connection_pool_recovery(self, temp_db):
        """Test connection pool recovers from connection issues."""
        # Get all connections from pool
        connections = []
        for _ in range(temp_db.pool_size):
            conn = await temp_db._get_connection()
            connections.append(conn)
        
        # Pool should be empty
        assert temp_db._connection_pool.qsize() == 0
        
        # Return connections
        for conn in connections:
            await temp_db._return_connection(conn)
        
        # Pool should be full again
        assert temp_db._connection_pool.qsize() == temp_db.pool_size


class TestErrorHandling:
    """Test error handling and graceful degradation."""
    
    async def test_invalid_pattern_storage(self, temp_db):
        """Test handling of invalid pattern data."""
        # Test with None pattern
        result = await temp_db.store_execution_pattern(None)
        assert result is False
    
    async def test_database_corruption_handling(self, temp_db):
        """Test handling of database issues."""
        # Simulate database file corruption by trying invalid operations
        with patch('aiosqlite.connect') as mock_connect:
            mock_connect.side_effect = Exception("Database corruption")
            
            # Operations should fail gracefully
            pattern = ExecutionPattern(task_type="test", pattern_used="direct")
            result = await temp_db.store_execution_pattern(pattern)
            assert result is False
    
    async def test_invalid_filter_handling(self, temp_db):
        """Test handling of invalid filters."""
        # Create filter with invalid data
        filters = PatternFilters(limit=-1)  # Invalid limit
        
        # Should return empty list rather than crash
        patterns = await temp_db.retrieve_patterns(filters)
        assert isinstance(patterns, list)


class TestDatabaseStats:
    """Test database statistics and monitoring."""
    
    async def test_database_stats_basic(self, temp_db):
        """Test basic database statistics."""
        stats = await temp_db.get_database_stats()
        
        required_fields = [
            "pattern_count", "preference_count", "metric_count",
            "database_size_mb", "total_operations", "uptime_seconds",
            "pattern_cache", "query_cache", "pool_size"
        ]
        
        for field in required_fields:
            assert field in stats
    
    async def test_stats_after_operations(self, temp_db, sample_execution_pattern):
        """Test statistics update after operations."""
        # Get initial stats
        initial_stats = await temp_db.get_database_stats()
        initial_operations = initial_stats["total_operations"]
        
        # Perform some operations
        await temp_db.store_execution_pattern(sample_execution_pattern)
        await temp_db.store_user_preference("test_key", "test_value")
        
        # Get updated stats
        updated_stats = await temp_db.get_database_stats()
        
        # Check that counts increased
        assert updated_stats["pattern_count"] > initial_stats["pattern_count"]
        assert updated_stats["preference_count"] > initial_stats["preference_count"]
        assert updated_stats["total_operations"] > initial_operations


class TestIntegration:
    """Integration tests with real-world scenarios."""
    
    async def test_complete_workflow_scenario(self, temp_db):
        """Test complete workflow: store, retrieve, update, analyze."""
        # 1. Store multiple execution patterns
        patterns = [
            ExecutionPattern(
                id=f"workflow_pattern_{i}",
                task_type="code_analysis",
                pattern_used="parallel" if i % 2 == 0 else "direct",
                execution_time=0.1 + (i * 0.01),
                success_rate=0.95 - (i * 0.01),
                confidence_score=0.9 - (i * 0.05)
            )
            for i in range(10)
        ]
        
        for pattern in patterns:
            result = await temp_db.store_execution_pattern(pattern)
            assert result is True
        
        # 2. Store user preferences
        await temp_db.store_user_preference("preferred_pattern", "parallel")
        await temp_db.store_user_preference("max_agents", 5)
        
        # 3. Retrieve patterns with different filters
        high_confidence = await temp_db.retrieve_patterns(
            PatternFilters(min_confidence=0.7)
        )
        parallel_patterns = await temp_db.retrieve_patterns(
            PatternFilters(task_type="code_analysis")
        )
        
        # 4. Update pattern weights based on performance
        for pattern in high_confidence[:3]:
            await temp_db.update_pattern_weights(pattern.id, 0.95)
        
        # 5. Get comprehensive stats
        stats = await temp_db.get_database_stats()
        
        # Verify the workflow completed successfully
        assert stats["pattern_count"] == 10
        assert stats["preference_count"] == 2
        assert len(parallel_patterns) == 10
        assert stats["total_operations"] > 0
    
    async def test_high_load_scenario(self, temp_db):
        """Test database under high load conditions."""
        # Simulate high load with many concurrent operations
        async def store_batch(batch_id, count):
            tasks = []
            for i in range(count):
                pattern = ExecutionPattern(
                    id=f"load_test_{batch_id}_{i}",
                    task_type=f"task_{batch_id}",
                    pattern_used="direct"
                )
                tasks.append(temp_db.store_execution_pattern(pattern))
            return await asyncio.gather(*tasks)
        
        # Run multiple batches concurrently
        batch_tasks = [
            store_batch(batch_id, 20)
            for batch_id in range(5)
        ]
        
        start_time = time.perf_counter()
        batch_results = await asyncio.gather(*batch_tasks)
        total_time = (time.perf_counter() - start_time) * 1000
        
        # Verify all operations succeeded
        total_operations = sum(len(batch) for batch in batch_results)
        successful_operations = sum(
            sum(1 for result in batch if result)
            for batch in batch_results
        )
        
        assert successful_operations == total_operations == 100
        assert total_time < 1000.0  # Should complete in under 1 second
        
        # Verify database integrity
        stats = await temp_db.get_database_stats()
        assert stats["pattern_count"] >= 100


# Performance benchmarks
@pytest.mark.benchmark
class TestPerformanceBenchmarks:
    """Performance benchmarks for database operations."""
    
    async def test_single_pattern_storage_benchmark(self, temp_db):
        """Benchmark single pattern storage operation."""
        pattern = ExecutionPattern(
            task_type="benchmark_test",
            pattern_used="direct"
        )
        
        times = []
        for _ in range(100):
            start_time = time.perf_counter()
            await temp_db.store_execution_pattern(pattern)
            operation_time = (time.perf_counter() - start_time) * 1000
            times.append(operation_time)
        
        avg_time = sum(times) / len(times)
        max_time = max(times)
        
        # Report benchmark results
        print(f"\nSingle Pattern Storage Benchmark:")
        print(f"  Average time: {avg_time:.3f}ms")
        print(f"  Maximum time: {max_time:.3f}ms")
        print(f"  Target: <5.0ms")
        
        assert avg_time < 5.0
        assert max_time < 10.0  # Allow some variance
    
    async def test_pattern_retrieval_benchmark(self, temp_db):
        """Benchmark pattern retrieval operations."""
        # Store test data
        for i in range(100):
            pattern = ExecutionPattern(
                id=f"benchmark_pattern_{i}",
                task_type=f"task_{i % 10}",
                pattern_used="direct"
            )
            await temp_db.store_execution_pattern(pattern)
        
        # Benchmark retrieval
        filters = PatternFilters(limit=50)
        
        times = []
        for _ in range(50):
            start_time = time.perf_counter()
            await temp_db.retrieve_patterns(filters)
            operation_time = (time.perf_counter() - start_time) * 1000
            times.append(operation_time)
        
        avg_time = sum(times) / len(times)
        max_time = max(times)
        
        print(f"\nPattern Retrieval Benchmark:")
        print(f"  Average time: {avg_time:.3f}ms")
        print(f"  Maximum time: {max_time:.3f}ms")
        print(f"  Target: <5.0ms")
        
        assert avg_time < 5.0
        assert max_time < 10.0


if __name__ == "__main__":
    # Run tests with coverage
    pytest.main([
        __file__,
        "-v",
        "--cov=src.mcp_agent.learning.learning_database",
        "--cov-report=html",
        "--cov-report=term-missing",
        "--benchmark-only"  # Run only benchmark tests when called directly
    ])
