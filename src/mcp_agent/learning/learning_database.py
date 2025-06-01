"""
Learning Database Core for MCP-Agent

High-performance async SQLite database for persistent learning data storage.
Designed for <5ms operations and <5MB memory usage for 10k patterns.

Key Features:
- Async SQLite operations with connection pooling
- Intelligent caching with LRU strategy  
- Schema migrations and version management
- Zero API changes to existing learning system
- Performance monitoring and optimization
"""

import asyncio
import aiosqlite
import json
import logging
import time
import uuid
from collections import OrderedDict
from typing import Dict, List, Optional, Any, Union
from pathlib import Path

from .learning_models import (
    ExecutionPattern,
    PerformanceMetrics,
    PatternFilters,
    LearningMetrics
)


class LRUCache:
    """High-performance LRU cache with memory monitoring."""
    
    def __init__(self, max_size: int = 1000, max_memory_mb: float = 2.0):
        self.max_size = max_size
        self.max_memory_mb = max_memory_mb
        self.cache: OrderedDict[str, Any] = OrderedDict()
        self.access_times: Dict[str, float] = {}
        
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache and mark as recently used."""
        if key in self.cache:
            self.cache.move_to_end(key)
            self.access_times[key] = time.time()
            return self.cache[key]
        return None
    
    def put(self, key: str, value: Any) -> None:
        """Put value in cache with automatic eviction."""
        if key in self.cache:
            self.cache.move_to_end(key)
        else:
            if len(self.cache) >= self.max_size:
                oldest_key = next(iter(self.cache))
                del self.cache[oldest_key]
                self.access_times.pop(oldest_key, None)
        
        self.cache[key] = value
        self.access_times[key] = time.time()
        
        # Check memory usage and evict if needed
        self._check_memory_usage()
    
    def invalidate(self, pattern: str = None) -> None:
        """Invalidate cache entries matching pattern."""
        if pattern is None:
            self.cache.clear()
            self.access_times.clear()
        else:
            keys_to_remove = [k for k in self.cache.keys() if pattern in k]
            for key in keys_to_remove:
                del self.cache[key]
                self.access_times.pop(key, None)
    
    def _check_memory_usage(self) -> None:
        """Check and enforce memory limits."""
        import sys
        
        total_size = sum(sys.getsizeof(v) for v in self.cache.values())
        current_mb = total_size / (1024 * 1024)
        
        # Evict oldest entries if over memory limit
        while current_mb > self.max_memory_mb and self.cache:
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]
            self.access_times.pop(oldest_key, None)
            total_size = sum(sys.getsizeof(v) for v in self.cache.values())
            current_mb = total_size / (1024 * 1024)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        import sys
        total_size = sum(sys.getsizeof(v) for v in self.cache.values())
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "memory_mb": total_size / (1024 * 1024),
            "max_memory_mb": self.max_memory_mb
        }


class LearningDatabase:
    """
    High-performance async SQLite database for learning data storage.
    
    Provides persistent storage for execution patterns, user preferences,
    and performance metrics with sub-5ms operations and intelligent caching.
    """
    
    SCHEMA_VERSION = 1
    
    def __init__(self, db_path: str = "learning.db", pool_size: int = 3):
        """
        Initialize learning database.
        
        Args:
            db_path: Path to SQLite database file
            pool_size: Size of connection pool
        """
        self.db_path = Path(db_path)
        self.pool_size = pool_size
        self.logger = logging.getLogger(__name__)
        
        # Connection pool
        self._connection_pool: Optional[asyncio.Queue] = None
        self._pool_lock = asyncio.Lock()
        
        # Caching system
        self._pattern_cache = LRUCache(max_size=1000, max_memory_mb=2.0)
        self._query_cache = LRUCache(max_size=500, max_memory_mb=1.0)
        
        # Performance tracking
        self.metrics = LearningMetrics()
        self._total_operations = 0
        self._start_time = time.time()
        
        # Prepared statements cache
        self._prepared_statements: Dict[str, str] = {}
        
        self.logger.info(f"LearningDatabase initialized with path: {self.db_path}")
    
    async def initialize(self) -> None:
        """
        Initialize database with schema and connection pool.
        """
        try:
            start_time = time.perf_counter()
            
            # Create database directory if needed
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Initialize connection pool
            await self._initialize_connection_pool()
            
            # Create schema and run migrations
            await self._create_schema()
            await self._run_migrations()
            
            # Create indexes for performance
            await self._create_indexes()
            
            # Cache prepared statements
            self._prepare_statements()
            
            init_time = (time.perf_counter() - start_time) * 1000
            self.logger.info(f"LearningDatabase initialized in {init_time:.3f}ms")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize LearningDatabase: {e}")
            raise
    
    async def store_execution_pattern(self, pattern: ExecutionPattern) -> bool:
        """
        Store execution pattern in database.
        
        Args:
            pattern: ExecutionPattern to store
            
        Returns:
            True if successful, False otherwise
        """
        start_time = time.perf_counter()
        
        try:
            # Generate ID if not provided
            if not pattern.id:
                pattern.id = f"pattern_{uuid.uuid4().hex[:8]}"
            
            # Convert to database format
            pattern_data = pattern.to_dict()
            
            # Store in database
            conn = await self._get_connection()
            try:
                await conn.execute(
                    self._prepared_statements["insert_pattern"],
                    tuple(pattern_data.values())
                )
                await conn.commit()
            finally:
                await self._return_connection(conn)
            
            # Update cache
            cache_key = f"pattern_{pattern.id}"
            self._pattern_cache.put(cache_key, pattern)
            
            # Invalidate related query cache
            self._query_cache.invalidate("retrieve_patterns")
            
            # Update metrics
            self._total_operations += 1
            operation_time = (time.perf_counter() - start_time) * 1000
            self.metrics.database_performance_ms = operation_time
            
            if operation_time > 5.0:  # 5ms target
                self.logger.warning(f"Slow database operation: {operation_time:.3f}ms")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to store execution pattern: {e}")
            return False
    
    async def retrieve_patterns(self, filters: PatternFilters) -> List[ExecutionPattern]:
        """
        Retrieve execution patterns based on filters.
        
        Args:
            filters: PatternFilters to apply
            
        Returns:
            List of matching ExecutionPattern objects
        """
        start_time = time.perf_counter()
        
        try:
            # Generate cache key from filters
            cache_key = f"retrieve_patterns_{hash(str(filters.__dict__))}"
            
            # Check cache first
            cached_result = self._query_cache.get(cache_key)
            if cached_result is not None:
                self.metrics.pattern_cache_hits += 1
                return cached_result
            
            self.metrics.pattern_cache_misses += 1
            
            # Build SQL query from filters
            where_clause, params = filters.to_sql_conditions()
            query = f"""
                SELECT * FROM execution_patterns 
                WHERE {where_clause}
            """
            
            # Execute query
            conn = await self._get_connection()
            try:
                cursor = await conn.execute(query, params)
                rows = await cursor.fetchall()
            finally:
                await self._return_connection(conn)
            
            # Convert to ExecutionPattern objects
            patterns = []
            for row in rows:
                # Convert row to dict
                row_dict = dict(zip([desc[0] for desc in cursor.description], row))
                pattern = ExecutionPattern.from_dict(row_dict)
                patterns.append(pattern)
            
            # Cache result
            self._query_cache.put(cache_key, patterns)
            
            # Update metrics
            operation_time = (time.perf_counter() - start_time) * 1000
            self.metrics.database_performance_ms = operation_time
            
            return patterns
            
        except Exception as e:
            self.logger.error(f"Failed to retrieve patterns: {e}")
            return []
    
    async def update_pattern_weights(self, pattern_id: str, new_weight: float) -> bool:
        """
        Update pattern confidence score (weight).
        
        Args:
            pattern_id: ID of pattern to update
            new_weight: New confidence score
            
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = await self._get_connection()
            try:
                await conn.execute(
                    "UPDATE execution_patterns SET confidence_score = ?, updated_at = ? WHERE id = ?",
                    (new_weight, time.time(), pattern_id)
                )
                await conn.commit()
            finally:
                await self._return_connection(conn)
            
            # Invalidate caches
            self._pattern_cache.invalidate(pattern_id)
            self._query_cache.invalidate("retrieve_patterns")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update pattern weights: {e}")
            return False
    
    async def get_performance_history(self, component: str, days: int) -> List[PerformanceMetrics]:
        """
        Get performance history for a component.
        
        Args:
            component: Component name
            days: Number of days of history
            
        Returns:
            List of PerformanceMetrics
        """
        try:
            min_timestamp = time.time() - (days * 24 * 3600)
            
            conn = await self._get_connection()
            try:
                cursor = await conn.execute(
                    """SELECT * FROM performance_metrics 
                       WHERE component_name = ? AND measured_at >= ?
                       ORDER BY measured_at DESC""",
                    (component, min_timestamp)
                )
                rows = await cursor.fetchall()
            finally:
                await self._return_connection(conn)
            
            # Convert to PerformanceMetrics objects
            metrics = []
            for row in rows:
                row_dict = dict(zip([desc[0] for desc in cursor.description], row))
                metric = PerformanceMetrics(
                    component_name=row_dict["component_name"],
                    metric_name=row_dict["metric_name"],
                    metric_value=row_dict["metric_value"],
                    baseline_value=row_dict["baseline_value"],
                    improvement_percentage=row_dict["improvement_percentage"],
                    sample_count=row_dict["sample_count"],
                    confidence_interval=row_dict["confidence_interval"],
                    measured_at=row_dict["measured_at"],
                    metadata=json.loads(row_dict.get("metadata", "{}"))
                )
                metrics.append(metric)
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Failed to get performance history: {e}")
            return []
    
    async def store_user_preference(self, key: str, value: Any) -> bool:
        """
        Store user preference.
        
        Args:
            key: Preference key
            value: Preference value
            
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = await self._get_connection()
            try:
                await conn.execute(
                    """INSERT OR REPLACE INTO user_preferences (key, value, updated_at)
                       VALUES (?, ?, ?)""",
                    (key, json.dumps(value), time.time())
                )
                await conn.commit()
            finally:
                await self._return_connection(conn)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to store user preference: {e}")
            return False
    
    async def get_user_preferences(self) -> Dict[str, Any]:
        """
        Get all user preferences.
        
        Returns:
            Dictionary of user preferences
        """
        try:
            conn = await self._get_connection()
            try:
                cursor = await conn.execute("SELECT key, value FROM user_preferences")
                rows = await cursor.fetchall()
            finally:
                await self._return_connection(conn)
            
            preferences = {}
            for key, value_json in rows:
                try:
                    preferences[key] = json.loads(value_json)
                except json.JSONDecodeError:
                    preferences[key] = value_json
            
            return preferences
            
        except Exception as e:
            self.logger.error(f"Failed to get user preferences: {e}")
            return {}
    
    async def get_database_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive database statistics.
        
        Returns:
            Dictionary containing database statistics
        """
        try:
            conn = await self._get_connection()
            try:
                # Count patterns
                cursor = await conn.execute("SELECT COUNT(*) FROM execution_patterns")
                pattern_count = (await cursor.fetchone())[0]
                
                # Count preferences
                cursor = await conn.execute("SELECT COUNT(*) FROM user_preferences")
                preference_count = (await cursor.fetchone())[0]
                
                # Count performance metrics
                cursor = await conn.execute("SELECT COUNT(*) FROM performance_metrics")
                metric_count = (await cursor.fetchone())[0]
                
                # Database file size
                db_size_mb = self.db_path.stat().st_size / (1024 * 1024) if self.db_path.exists() else 0
                
            finally:
                await self._return_connection(conn)
            
            # Cache statistics
            pattern_cache_stats = self._pattern_cache.get_stats()
            query_cache_stats = self._query_cache.get_stats()
            
            return {
                "pattern_count": pattern_count,
                "preference_count": preference_count,
                "metric_count": metric_count,
                "database_size_mb": db_size_mb,
                "total_operations": self._total_operations,
                "uptime_seconds": time.time() - self._start_time,
                "avg_operation_time_ms": self.metrics.database_performance_ms,
                "pattern_cache": pattern_cache_stats,
                "query_cache": query_cache_stats,
                "pool_size": self.pool_size
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get database stats: {e}")
            return {"error": str(e)}
    
    # Private helper methods
    
    async def _initialize_connection_pool(self) -> None:
        """Initialize connection pool."""
        async with self._pool_lock:
            if self._connection_pool is not None:
                return
            
            self._connection_pool = asyncio.Queue(maxsize=self.pool_size)
            
            # Create connections
            for _ in range(self.pool_size):
                conn = await aiosqlite.connect(
                    self.db_path,
                    timeout=30.0,
                    isolation_level=None  # Autocommit mode
                )
                
                # Configure for performance
                await conn.execute("PRAGMA journal_mode=WAL")
                await conn.execute("PRAGMA synchronous=NORMAL")
                await conn.execute("PRAGMA cache_size=10000")
                await conn.execute("PRAGMA temp_store=MEMORY")
                
                await self._connection_pool.put(conn)
    
    async def _get_connection(self) -> aiosqlite.Connection:
        """Get connection from pool."""
        if self._connection_pool is None:
            await self._initialize_connection_pool()
        return await self._connection_pool.get()
    
    async def _return_connection(self, conn: aiosqlite.Connection) -> None:
        """Return connection to pool."""
        if self._connection_pool is not None:
            await self._connection_pool.put(conn)
    
    async def _create_schema(self) -> None:
        """Create database schema."""
        conn = await self._get_connection()
        try:
            # Execution patterns table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS execution_patterns (
                    id TEXT PRIMARY KEY,
                    task_type TEXT NOT NULL,
                    pattern_used TEXT NOT NULL,
                    execution_time REAL NOT NULL,
                    success_rate REAL NOT NULL,
                    confidence_score REAL NOT NULL,
                    agent_count INTEGER NOT NULL,
                    complexity_level TEXT NOT NULL,
                    tools_used TEXT,
                    context_factors TEXT,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL,
                    usage_count INTEGER NOT NULL DEFAULT 0
                )
            """)
            
            # User preferences table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS user_preferences (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at REAL NOT NULL
                )
            """)
            
            # Performance metrics table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    component_name TEXT NOT NULL,
                    metric_name TEXT NOT NULL,
                    metric_value REAL NOT NULL,
                    baseline_value REAL NOT NULL,
                    improvement_percentage REAL NOT NULL,
                    sample_count INTEGER NOT NULL,
                    confidence_interval REAL NOT NULL,
                    measured_at REAL NOT NULL,
                    metadata TEXT
                )
            """)
            
            # Schema version table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS schema_version (
                    version INTEGER PRIMARY KEY,
                    applied_at REAL NOT NULL
                )
            """)
            
            await conn.commit()
            
        finally:
            await self._return_connection(conn)
    
    async def _create_indexes(self) -> None:
        """Create performance indexes."""
        conn = await self._get_connection()
        try:
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_patterns_task_type ON execution_patterns(task_type)",
                "CREATE INDEX IF NOT EXISTS idx_patterns_pattern_used ON execution_patterns(pattern_used)",
                "CREATE INDEX IF NOT EXISTS idx_patterns_confidence ON execution_patterns(confidence_score DESC)",
                "CREATE INDEX IF NOT EXISTS idx_patterns_success_rate ON execution_patterns(success_rate DESC)",
                "CREATE INDEX IF NOT EXISTS idx_patterns_created_at ON execution_patterns(created_at)",
                "CREATE INDEX IF NOT EXISTS idx_metrics_component ON performance_metrics(component_name)",
                "CREATE INDEX IF NOT EXISTS idx_metrics_measured_at ON performance_metrics(measured_at)"
            ]
            
            for index_sql in indexes:
                await conn.execute(index_sql)
            
            await conn.commit()
            
        finally:
            await self._return_connection(conn)
    
    async def _run_migrations(self) -> None:
        """Run database migrations."""
        conn = await self._get_connection()
        try:
            # Get current schema version
            try:
                cursor = await conn.execute("SELECT MAX(version) FROM schema_version")
                result = await cursor.fetchone()
                current_version = result[0] if result[0] is not None else 0
            except:
                current_version = 0
            
            # Apply migrations if needed
            if current_version < self.SCHEMA_VERSION:
                # Record migration
                await conn.execute(
                    "INSERT OR REPLACE INTO schema_version (version, applied_at) VALUES (?, ?)",
                    (self.SCHEMA_VERSION, time.time())
                )
                await conn.commit()
                
                self.logger.info(f"Applied schema migration to version {self.SCHEMA_VERSION}")
            
        finally:
            await self._return_connection(conn)
    
    def _prepare_statements(self) -> None:
        """Prepare frequently used SQL statements."""
        self._prepared_statements = {
            "insert_pattern": """
                INSERT OR REPLACE INTO execution_patterns 
                (id, task_type, pattern_used, execution_time, success_rate, 
                 confidence_score, agent_count, complexity_level, tools_used, 
                 context_factors, created_at, updated_at, usage_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
        }
    
    async def shutdown(self) -> None:
        """Gracefully shutdown database."""
        try:
            self.logger.info("Shutting down LearningDatabase...")
            
            # Close all connections
            if self._connection_pool is not None:
                while not self._connection_pool.empty():
                    conn = await self._connection_pool.get()
                    await conn.close()
            
            # Clear caches
            self._pattern_cache.invalidate()
            self._query_cache.invalidate()
            
            self.logger.info("LearningDatabase shutdown complete")
            
        except Exception as e:
            self.logger.error(f"Error during database shutdown: {e}")
