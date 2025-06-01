"""
Performance Benchmark Suite for MCP-Agent Autonomous Components

This module provides comprehensive performance measurement tools to establish
baseline metrics and identify optimization opportunities in the autonomous
components: TaskAnalyzer, ToolDiscovery, DecisionEngine, and MetaCoordinator.
"""

import asyncio
import time
import psutil
import logging
import statistics
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from functools import wraps
import tracemalloc
import json
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.mcp_agent.autonomous.task_analyzer import TaskAnalyzer, TaskAnalysis
from src.mcp_agent.autonomous.tool_discovery import ToolDiscoveryAgent
from src.mcp_agent.autonomous.decision_engine import AutonomousDecisionEngine, TaskAnalyzer as DecisionTaskAnalyzer
from src.mcp_agent.autonomous.meta_coordinator import MetaCoordinator


@dataclass
class PerformanceMetric:
    """Individual performance measurement"""
    
    component: str
    method: str
    execution_time: float
    memory_used: float
    memory_peak: float
    timestamp: datetime
    success: bool
    error_message: str = ""
    additional_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ComponentBenchmark:
    """Benchmark results for a component"""
    
    component_name: str
    total_calls: int
    successful_calls: int
    failed_calls: int
    avg_execution_time: float
    min_execution_time: float
    max_execution_time: float
    std_execution_time: float
    avg_memory_used: float
    peak_memory_used: float
    methods_tested: List[str]
    error_rate: float
    detailed_metrics: List[PerformanceMetric] = field(default_factory=list)


class PerformanceProfiler:
    """High-precision performance profiler"""
    
    def __init__(self):
        self.metrics: List[PerformanceMetric] = []
        self.is_profiling = False
        
    def __enter__(self):
        self.start_profiling()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop_profiling()
    
    def start_profiling(self):
        """Start memory profiling"""
        tracemalloc.start()
        self.is_profiling = True
        
    def stop_profiling(self):
        """Stop memory profiling"""
        if self.is_profiling:
            tracemalloc.stop()
            self.is_profiling = False
    
    def profile_method(self, component: str, method_name: str):
        """Decorator to profile method execution"""
        def decorator(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                return await self._profile_execution(component, method_name, func, *args, **kwargs)
            
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                return asyncio.run(self._profile_execution(component, method_name, func, *args, **kwargs))
            
            return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
        return decorator
    
    async def _profile_execution(self, component: str, method_name: str, func: Callable, *args, **kwargs):
        """Profile function execution"""
        # Start measurements
        start_time = time.perf_counter()
        start_memory = self._get_memory_usage()
        
        if self.is_profiling:
            tracemalloc_start = tracemalloc.get_traced_memory()[0]
        
        success = True
        error_message = ""
        result = None
        
        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
        except Exception as e:
            success = False
            error_message = str(e)
            
        # End measurements
        end_time = time.perf_counter()
        end_memory = self._get_memory_usage()
        
        memory_used = end_memory - start_memory
        peak_memory = memory_used
        
        if self.is_profiling:
            current_memory, peak_traced = tracemalloc.get_traced_memory()
            peak_memory = max(peak_memory, peak_traced - tracemalloc_start)
        
        execution_time = end_time - start_time
        
        # Record metric
        metric = PerformanceMetric(
            component=component,
            method=method_name,
            execution_time=execution_time,
            memory_used=memory_used,
            memory_peak=peak_memory,
            timestamp=datetime.now(),
            success=success,
            error_message=error_message
        )
        
        self.metrics.append(metric)
        
        if not success:
            raise Exception(error_message)
            
        return result
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024


class AutonomousComponentBenchmark:
    """Comprehensive benchmark suite for autonomous components"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.profiler = PerformanceProfiler()
        self.test_tasks = self._create_test_tasks()
        
    def _create_test_tasks(self) -> List[str]:
        """Create diverse test tasks for benchmarking"""
        return [
            "Find information about Python programming",
            "Create a simple web scraper for news articles",
            "Analyze data from a CSV file and generate insights",
            "Automate file organization in a directory",
            "Search for GitHub repositories related to machine learning",
            "Write code to implement a REST API with authentication",
            "Plan and execute a multi-step data processing workflow",
            "Orchestrate multiple agents to research and compile a report",
            "Optimize database queries and analyze performance",
            "Create a comprehensive project documentation website",
            "Implement parallel processing for large dataset analysis",
            "Coordinate multiple tools for complex automation task",
            "Build an intelligent task routing system",
            "Develop iterative refinement process for content creation",
            "Simple file read operation",  # Simple task
            "Get weather information",  # Simple task
            "Quick database query",  # Simple task
        ]
    
    async def run_full_benchmark(self) -> Dict[str, ComponentBenchmark]:
        """Run complete benchmark suite for all components"""
        self.logger.info("Starting comprehensive performance benchmark...")
        
        with self.profiler:
            results = {}
            
            # Benchmark TaskAnalyzer
            self.logger.info("Benchmarking TaskAnalyzer...")
            results['TaskAnalyzer'] = await self._benchmark_task_analyzer()
            
            # Benchmark ToolDiscovery
            self.logger.info("Benchmarking ToolDiscoveryAgent...")
            results['ToolDiscovery'] = await self._benchmark_tool_discovery()
            
            # Benchmark DecisionEngine  
            self.logger.info("Benchmarking DecisionEngine...")
            results['DecisionEngine'] = await self._benchmark_decision_engine()
            
            # Note: MetaCoordinator benchmark would require full MCP setup
            # For now, we'll focus on the core autonomous components
            
        self.logger.info("Benchmark complete!")
        return results
    
    async def _benchmark_task_analyzer(self) -> ComponentBenchmark:
        """Benchmark TaskAnalyzer performance"""
        analyzer = TaskAnalyzer()
        metrics = []
        
        for task in self.test_tasks:
            # Test analyze_task method
            metric = await self._measure_method(
                'TaskAnalyzer', 'analyze_task', 
                analyzer.analyze_task, task
            )
            metrics.append(metric)
            
            # Test individual component methods for more granular analysis
            task_lower = task.lower()
            
            # Test _detect_task_type
            metric = await self._measure_method(
                'TaskAnalyzer', '_detect_task_type',
                analyzer._detect_task_type, task
            )
            metrics.append(metric)
            
            # Test _assess_complexity
            metric = await self._measure_method(
                'TaskAnalyzer', '_assess_complexity',
                analyzer._assess_complexity, task
            )
            metrics.append(metric)
            
            # Test _extract_requirements  
            task_type = analyzer._detect_task_type(task)
            metric = await self._measure_method(
                'TaskAnalyzer', '_extract_requirements',
                analyzer._extract_requirements, task, task_type
            )
            metrics.append(metric)
        
        return self._compile_component_benchmark('TaskAnalyzer', metrics)
    
    async def _benchmark_tool_discovery(self) -> ComponentBenchmark:
        """Benchmark ToolDiscoveryAgent performance"""
        discovery = ToolDiscoveryAgent(None)  # Mock connection manager for now
        metrics = []
        
        # Test server discovery from registries (doesn't require real connections)
        metric = await self._measure_method(
            'ToolDiscovery', '_discover_from_registries',
            discovery._discover_from_registries
        )
        metrics.append(metric)
        
        # Test capability analysis with mock tools
        mock_tools = [
            type('Tool', (), {'name': 'file_read'})(),
            type('Tool', (), {'name': 'web_search'})(),
            type('Tool', (), {'name': 'database_query'})(),
            type('Tool', (), {'name': 'git_commit'})(),
        ]
        
        metric = await self._measure_method(
            'ToolDiscovery', '_analyze_server_capabilities',
            discovery._analyze_server_capabilities, mock_tools, []
        )
        metrics.append(metric)
        
        # Test capability map building
        # First populate some servers
        await discovery._discover_from_registries()
        
        metric = await self._measure_method(
            'ToolDiscovery', '_build_capability_map',
            discovery._build_capability_map
        )
        metrics.append(metric)
        
        # Test server recommendations
        for task in self.test_tasks[:5]:  # Test subset for efficiency
            metric = await self._measure_method(
                'ToolDiscovery', 'get_best_servers_for_task',
                discovery.get_best_servers_for_task, task
            )
            metrics.append(metric)
        
        return self._compile_component_benchmark('ToolDiscovery', metrics)
    
    async def _benchmark_decision_engine(self) -> ComponentBenchmark:
        """Benchmark DecisionEngine performance"""
        engine = AutonomousDecisionEngine()
        metrics = []
        
        # Test task analysis in decision engine
        for task in self.test_tasks:
            metric = await self._measure_method(
                'DecisionEngine', 'task_analyzer.analyze_task',
                engine.task_analyzer.analyze_task, task
            )
            metrics.append(metric)
        
        # Test strategy selection (with mock servers)
        mock_servers = []  # Empty for now, would need MCPServerProfile objects
        
        for task in self.test_tasks[:5]:  # Subset for efficiency
            task_analysis = engine.task_analyzer.analyze_task(task)
            metric = await self._measure_method(
                'DecisionEngine', 'strategy_selector.select_strategy',
                engine.strategy_selector.select_strategy, task_analysis, mock_servers
            )
            metrics.append(metric)
        
        return self._compile_component_benchmark('DecisionEngine', metrics)
    
    async def _measure_method(self, component: str, method_name: str, method: Callable, *args, **kwargs) -> PerformanceMetric:
        """Measure individual method performance"""
        start_time = time.perf_counter()
        start_memory = self._get_memory_usage()
        
        success = True
        error_message = ""
        
        try:
            if asyncio.iscoroutinefunction(method):
                await method(*args, **kwargs)
            else:
                method(*args, **kwargs)
        except Exception as e:
            success = False
            error_message = str(e)
        
        end_time = time.perf_counter()
        end_memory = self._get_memory_usage()
        
        return PerformanceMetric(
            component=component,
            method=method_name,
            execution_time=end_time - start_time,
            memory_used=end_memory - start_memory,
            memory_peak=end_memory - start_memory,
            timestamp=datetime.now(),
            success=success,
            error_message=error_message
        )
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024
    
    def _compile_component_benchmark(self, component_name: str, metrics: List[PerformanceMetric]) -> ComponentBenchmark:
        """Compile individual metrics into component benchmark"""
        successful_metrics = [m for m in metrics if m.success]
        failed_metrics = [m for m in metrics if not m.success]
        
        if not successful_metrics:
            return ComponentBenchmark(
                component_name=component_name,
                total_calls=len(metrics),
                successful_calls=0,
                failed_calls=len(failed_metrics),
                avg_execution_time=0.0,
                min_execution_time=0.0,
                max_execution_time=0.0,
                std_execution_time=0.0,
                avg_memory_used=0.0,
                peak_memory_used=0.0,
                methods_tested=[],
                error_rate=1.0,
                detailed_metrics=metrics
            )
        
        execution_times = [m.execution_time for m in successful_metrics]
        memory_usage = [m.memory_used for m in successful_metrics]
        methods_tested = list(set(m.method for m in metrics))
        
        return ComponentBenchmark(
            component_name=component_name,
            total_calls=len(metrics),
            successful_calls=len(successful_metrics),
            failed_calls=len(failed_metrics),
            avg_execution_time=statistics.mean(execution_times),
            min_execution_time=min(execution_times),
            max_execution_time=max(execution_times),
            std_execution_time=statistics.stdev(execution_times) if len(execution_times) > 1 else 0.0,
            avg_memory_used=statistics.mean(memory_usage),
            peak_memory_used=max(memory_usage),
            methods_tested=methods_tested,
            error_rate=len(failed_metrics) / len(metrics),
            detailed_metrics=metrics
        )
    
    def generate_performance_report(self, results: Dict[str, ComponentBenchmark]) -> str:
        """Generate comprehensive performance report"""
        report = []
        report.append("=" * 80)
        report.append("MCP-AGENT AUTONOMOUS COMPONENTS PERFORMANCE BENCHMARK REPORT")
        report.append("=" * 80)
        report.append(f"Benchmark Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Test Tasks: {len(self.test_tasks)} diverse scenarios")
        report.append("")
        
        # Overall summary
        total_calls = sum(b.total_calls for b in results.values())
        total_successful = sum(b.successful_calls for b in results.values())
        total_failed = sum(b.failed_calls for b in results.values())
        overall_success_rate = (total_successful / total_calls) * 100 if total_calls > 0 else 0
        
        report.append("OVERALL SUMMARY")
        report.append("-" * 40)
        report.append(f"Total Method Calls: {total_calls}")
        report.append(f"Successful Calls: {total_successful}")
        report.append(f"Failed Calls: {total_failed}")
        report.append(f"Overall Success Rate: {overall_success_rate:.1f}%")
        report.append("")
        
        # Component-specific details
        for component_name, benchmark in results.items():
            report.append(f"{component_name.upper()} PERFORMANCE")
            report.append("-" * 40)
            report.append(f"Total Calls: {benchmark.total_calls}")
            report.append(f"Success Rate: {((benchmark.successful_calls / benchmark.total_calls) * 100):.1f}%")
            report.append(f"Average Execution Time: {benchmark.avg_execution_time*1000:.2f}ms")
            report.append(f"Min/Max Execution Time: {benchmark.min_execution_time*1000:.2f}ms / {benchmark.max_execution_time*1000:.2f}ms")
            report.append(f"Standard Deviation: {benchmark.std_execution_time*1000:.2f}ms")
            report.append(f"Average Memory Usage: {benchmark.avg_memory_used:.2f}MB")
            report.append(f"Peak Memory Usage: {benchmark.peak_memory_used:.2f}MB")
            report.append(f"Methods Tested: {', '.join(benchmark.methods_tested)}")
            
            # Performance targets analysis
            target_time_ms = 500  # Target <500ms
            fast_calls = len([m for m in benchmark.detailed_metrics if m.success and m.execution_time * 1000 < target_time_ms])
            target_compliance = (fast_calls / max(benchmark.successful_calls, 1)) * 100
            
            report.append(f"<500ms Target Compliance: {target_compliance:.1f}% ({fast_calls}/{benchmark.successful_calls} calls)")
            
            if benchmark.error_rate > 0:
                report.append(f"Error Rate: {benchmark.error_rate*100:.1f}%")
                
            report.append("")
        
        # Performance bottlenecks identification
        report.append("PERFORMANCE BOTTLENECKS ANALYSIS")
        report.append("-" * 40)
        
        all_metrics = []
        for benchmark in results.values():
            all_metrics.extend([m for m in benchmark.detailed_metrics if m.success])
        
        # Sort by execution time
        slowest_methods = sorted(all_metrics, key=lambda x: x.execution_time, reverse=True)[:10]
        
        report.append("Top 10 Slowest Methods:")
        for i, metric in enumerate(slowest_methods, 1):
            report.append(f"{i:2d}. {metric.component}.{metric.method}: {metric.execution_time*1000:.2f}ms")
        
        report.append("")
        
        # Memory usage analysis
        memory_heavy = sorted(all_metrics, key=lambda x: x.memory_used, reverse=True)[:5]
        report.append("Top 5 Memory-Heavy Methods:")
        for i, metric in enumerate(memory_heavy, 1):
            report.append(f"{i:2d}. {metric.component}.{metric.method}: {metric.memory_used:.2f}MB")
        
        report.append("")
        report.append("OPTIMIZATION RECOMMENDATIONS")
        report.append("-" * 40)
        
        recommendations = []
        
        # Identify components that need optimization
        for component_name, benchmark in results.items():
            if benchmark.avg_execution_time > 0.5:  # >500ms average
                recommendations.append(f"- {component_name}: Average execution time ({benchmark.avg_execution_time*1000:.0f}ms) exceeds 500ms target")
            
            if benchmark.error_rate > 0.1:  # >10% error rate
                recommendations.append(f"- {component_name}: High error rate ({benchmark.error_rate*100:.1f}%) needs investigation")
        
        # Method-specific recommendations
        slow_threshold = 0.1  # 100ms
        slow_methods = [m for m in all_metrics if m.execution_time > slow_threshold]
        if slow_methods:
            recommendations.append(f"- Consider caching for {len(slow_methods)} methods with >100ms execution time")
        
        # Parallel processing opportunities
        if any('_discover' in m.method or '_analyze' in m.method for m in all_metrics):
            recommendations.append("- ToolDiscovery operations could benefit from parallel processing")
        
        if any('analyze_task' in m.method for m in all_metrics):
            recommendations.append("- TaskAnalyzer methods are good candidates for LRU caching")
        
        for rec in recommendations:
            report.append(rec)
        
        if not recommendations:
            report.append("- All components are performing within acceptable ranges")
        
        report.append("")
        report.append("=" * 80)
        
        return "\n".join(report)
    
    def save_detailed_results(self, results: Dict[str, ComponentBenchmark], filename: str = "performance_results.json"):
        """Save detailed results to JSON file"""
        detailed_data = {}
        
        for component_name, benchmark in results.items():
            detailed_data[component_name] = {
                'summary': {
                    'total_calls': benchmark.total_calls,
                    'successful_calls': benchmark.successful_calls,
                    'failed_calls': benchmark.failed_calls,
                    'avg_execution_time_ms': benchmark.avg_execution_time * 1000,
                    'min_execution_time_ms': benchmark.min_execution_time * 1000,
                    'max_execution_time_ms': benchmark.max_execution_time * 1000,
                    'std_execution_time_ms': benchmark.std_execution_time * 1000,
                    'avg_memory_used_mb': benchmark.avg_memory_used,
                    'peak_memory_used_mb': benchmark.peak_memory_used,
                    'error_rate': benchmark.error_rate,
                    'methods_tested': benchmark.methods_tested
                },
                'detailed_metrics': [
                    {
                        'method': m.method,
                        'execution_time_ms': m.execution_time * 1000,
                        'memory_used_mb': m.memory_used,
                        'success': m.success,
                        'timestamp': m.timestamp.isoformat(),
                        'error_message': m.error_message
                    }
                    for m in benchmark.detailed_metrics
                ]
            }
        
        with open(filename, 'w') as f:
            json.dump(detailed_data, f, indent=2, default=str)


async def main():
    """Run the performance benchmark"""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    benchmark = AutonomousComponentBenchmark()
    
    print("Starting MCP-Agent Performance Benchmark...")
    print("This will test TaskAnalyzer, ToolDiscovery, and DecisionEngine components")
    print("=" * 80)
    
    # Run benchmark
    results = await benchmark.run_full_benchmark()
    
    # Generate and display report
    report = benchmark.generate_performance_report(results)
    print(report)
    
    # Save detailed results
    benchmark.save_detailed_results(results)
    print("Detailed results saved to 'performance_results.json'")
    
    # Summary for optimization priorities
    print("\nQUICK OPTIMIZATION PRIORITIES:")
    print("-" * 40)
    
    for component_name, result in results.items():
        avg_time_ms = result.avg_execution_time * 1000
        if avg_time_ms > 500:
            print(f"🔴 {component_name}: {avg_time_ms:.0f}ms (HIGH PRIORITY)")
        elif avg_time_ms > 100:
            print(f"🟡 {component_name}: {avg_time_ms:.0f}ms (MEDIUM PRIORITY)")
        else:
            print(f"🟢 {component_name}: {avg_time_ms:.0f}ms (GOOD)")


if __name__ == "__main__":
    asyncio.run(main())
