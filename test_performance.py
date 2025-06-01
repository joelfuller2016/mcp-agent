#!/usr/bin/env python3
"""
Performance Benchmarking Suite for MCP-Agent Autonomous Components

This script provides comprehensive performance testing and benchmarking for the
autonomous components to measure response times, memory usage, and optimization effectiveness.
"""

import sys
import os
import time
import asyncio
import statistics
import psutil
import tracemalloc
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import json

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

try:
    from mcp_agent.autonomous.task_analyzer_optimized import TaskLevelCachedAnalyzer
    from mcp_agent.autonomous.task_analyzer import TaskAnalyzer as OriginalTaskAnalyzer
    from mcp_agent.autonomous.tool_discovery import ToolDiscoveryAgent
    from mcp_agent.autonomous.decision_engine import AutonomousDecisionEngine
    from mcp_agent.autonomous.meta_coordinator import MetaCoordinator
    from mcp_agent.mcp.mcp_connection_manager import MCPConnectionManager
    print("[OK] Performance test imports: SUCCESS")
except ImportError as e:
    print(f"[FAIL] Performance test imports: FAILED - {e}")
    sys.exit(1)


@dataclass
class PerformanceMetrics:
    """Container for performance measurement results."""
    
    component_name: str
    operation_name: str
    execution_time_ms: float
    memory_usage_mb: float
    memory_peak_mb: float
    cpu_usage_percent: float
    cache_hit_rate: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0
    success: bool = True
    error_message: str = ""


@dataclass
class BenchmarkResult:
    """Results from a complete benchmark run."""
    
    component_name: str
    total_operations: int
    successful_operations: int
    avg_execution_time_ms: float
    min_execution_time_ms: float
    max_execution_time_ms: float
    avg_memory_usage_mb: float
    peak_memory_usage_mb: float
    cache_hit_rate: float
    target_met: bool  # <500ms target
    performance_improvement: float = 0.0  # vs baseline


class PerformanceBenchmark:
    """Main performance benchmarking class."""
    
    def __init__(self):
        self.results: List[PerformanceMetrics] = []
        self.baseline_results: Dict[str, BenchmarkResult] = {}
        
        # Test data for consistent benchmarking
        self.test_tasks = [
            "Create a simple Python script to read a file",
            "Search for information about MCP protocol and analyze the results",
            "Build a web automation script to scrape product data from an e-commerce site",
            "Analyze data from multiple CSV files and generate a comprehensive report",
            "Create a GitHub repository with proper documentation and commit some code",
            "Set up a database connection and query customer information",
            "Automate email sending with attachments and track responses",
            "Research the latest AI developments and create a summary document",
            "Optimize website performance by analyzing page load times",
            "Create a project management workflow with task tracking and notifications"
        ]
    
    def start_performance_monitoring(self):
        """Start memory and CPU monitoring."""
        tracemalloc.start()
        return psutil.cpu_percent(interval=None), psutil.virtual_memory().used / 1024 / 1024
    
    def stop_performance_monitoring(self, start_cpu: float, start_memory: float) -> tuple:
        """Stop monitoring and return metrics."""
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        end_cpu = psutil.cpu_percent(interval=None)
        end_memory = psutil.virtual_memory().used / 1024 / 1024
        
        return (
            current / 1024 / 1024,  # Current memory MB
            peak / 1024 / 1024,     # Peak memory MB
            end_cpu - start_cpu,    # CPU usage delta
        )
    
    async def benchmark_task_analyzer(self, use_optimized: bool = True) -> BenchmarkResult:
        """Benchmark TaskAnalyzer performance."""
        
        component_name = "TaskAnalyzer_Optimized" if use_optimized else "TaskAnalyzer_Original"
        print(f"\n🔍 Benchmarking {component_name}...")
        
        # Initialize the analyzer
        if use_optimized:
            analyzer = TaskLevelCachedAnalyzer(cache_size=128)
        else:
            analyzer = OriginalTaskAnalyzer()
        
        metrics_list = []
        
        # Warm up cache (for optimized version)
        if use_optimized and hasattr(analyzer, 'analyze_task'):
            for task in self.test_tasks[:3]:
                analyzer.analyze_task(task)
        
        # Benchmark each test task
        for i, task in enumerate(self.test_tasks):
            print(f"  Testing task {i+1}/{len(self.test_tasks)}: {task[:50]}...")
            
            start_cpu, start_memory = self.start_performance_monitoring()
            start_time = time.perf_counter()
            
            try:
                # Execute the task analysis
                if hasattr(analyzer, 'analyze_task'):
                    result = analyzer.analyze_task(task)
                else:
                    result = analyzer.analyze_task(task)
                
                end_time = time.perf_counter()
                execution_time = (end_time - start_time) * 1000  # Convert to ms
                
                memory_current, memory_peak, cpu_usage = self.stop_performance_monitoring(start_cpu, start_memory)
                
                # Get cache metrics if available
                cache_hit_rate = 0.0
                cache_hits = 0
                cache_misses = 0
                
                if use_optimized and hasattr(analyzer, 'get_cache_info'):
                    cache_info = analyzer.get_cache_info()
                    if cache_info and 'hit_rate' in cache_info:
                        cache_hit_rate = cache_info['hit_rate']
                    if cache_info and 'cache_stats' in cache_info:
                        stats = cache_info['cache_stats']
                        cache_hits = stats.get('cache_hits', 0)
                        cache_misses = stats.get('cache_misses', 0)
                
                metrics = PerformanceMetrics(
                    component_name=component_name,
                    operation_name=f"analyze_task_{i+1}",
                    execution_time_ms=execution_time,
                    memory_usage_mb=memory_current,
                    memory_peak_mb=memory_peak,
                    cpu_usage_percent=cpu_usage,
                    cache_hit_rate=cache_hit_rate,
                    cache_hits=cache_hits,
                    cache_misses=cache_misses,
                    success=True
                )
                
                metrics_list.append(metrics)
                self.results.append(metrics)
                
            except Exception as e:
                end_time = time.perf_counter()
                execution_time = (end_time - start_time) * 1000
                
                metrics = PerformanceMetrics(
                    component_name=component_name,
                    operation_name=f"analyze_task_{i+1}",
                    execution_time_ms=execution_time,
                    memory_usage_mb=0,
                    memory_peak_mb=0,
                    cpu_usage_percent=0,
                    success=False,
                    error_message=str(e)
                )
                
                metrics_list.append(metrics)
                self.results.append(metrics)
                print(f"    ❌ Error: {str(e)}")
        
        # Calculate benchmark results
        successful_metrics = [m for m in metrics_list if m.success]
        execution_times = [m.execution_time_ms for m in successful_metrics]
        memory_usage = [m.memory_usage_mb for m in successful_metrics]
        memory_peaks = [m.memory_peak_mb for m in successful_metrics]
        
        if execution_times:
            avg_cache_hit_rate = statistics.mean([m.cache_hit_rate for m in successful_metrics])
            
            benchmark_result = BenchmarkResult(
                component_name=component_name,
                total_operations=len(metrics_list),
                successful_operations=len(successful_metrics),
                avg_execution_time_ms=statistics.mean(execution_times),
                min_execution_time_ms=min(execution_times),
                max_execution_time_ms=max(execution_times),
                avg_memory_usage_mb=statistics.mean(memory_usage) if memory_usage else 0,
                peak_memory_usage_mb=max(memory_peaks) if memory_peaks else 0,
                cache_hit_rate=avg_cache_hit_rate,
                target_met=statistics.mean(execution_times) < 500  # <500ms target
            )
        else:
            benchmark_result = BenchmarkResult(
                component_name=component_name,
                total_operations=len(metrics_list),
                successful_operations=0,
                avg_execution_time_ms=0,
                min_execution_time_ms=0,
                max_execution_time_ms=0,
                avg_memory_usage_mb=0,
                peak_memory_usage_mb=0,
                cache_hit_rate=0,
                target_met=False
            )
        
        return benchmark_result
    
    async def benchmark_tool_discovery(self) -> BenchmarkResult:
        """Benchmark ToolDiscovery performance."""
        
        print("\n🔧 Benchmarking ToolDiscoveryAgent...")
        
        # Mock connection manager for testing
        class MockConnectionManager:
            async def list_connected_servers(self):
                return ["fetch", "filesystem", "github", "sqlite", "puppeteer"]
            
            async def list_tools(self, server_name):
                return [f"tool_{i}" for i in range(5)]
            
            async def list_resources(self, server_name):
                return [f"resource_{i}" for i in range(3)]
            
            async def connect_server(self, server_name):
                return True
        
        discovery_agent = ToolDiscoveryAgent(MockConnectionManager())
        metrics_list = []
        
        # Test discovery operations
        operations = [
            ("discover_available_servers", lambda: discovery_agent.discover_available_servers()),
            ("get_capability_coverage", lambda: discovery_agent.get_capability_coverage()),
            ("export_discovery_results", lambda: discovery_agent.export_discovery_results()),
        ]
        
        for op_name, operation in operations:
            print(f"  Testing {op_name}...")
            
            start_cpu, start_memory = self.start_performance_monitoring()
            start_time = time.perf_counter()
            
            try:
                if asyncio.iscoroutinefunction(operation):
                    await operation()
                else:
                    operation()
                
                end_time = time.perf_counter()
                execution_time = (end_time - start_time) * 1000
                
                memory_current, memory_peak, cpu_usage = self.stop_performance_monitoring(start_cpu, start_memory)
                
                metrics = PerformanceMetrics(
                    component_name="ToolDiscoveryAgent",
                    operation_name=op_name,
                    execution_time_ms=execution_time,
                    memory_usage_mb=memory_current,
                    memory_peak_mb=memory_peak,
                    cpu_usage_percent=cpu_usage,
                    success=True
                )
                
                metrics_list.append(metrics)
                self.results.append(metrics)
                
            except Exception as e:
                print(f"    ❌ Error in {op_name}: {str(e)}")
                metrics = PerformanceMetrics(
                    component_name="ToolDiscoveryAgent",
                    operation_name=op_name,
                    execution_time_ms=0,
                    memory_usage_mb=0,
                    memory_peak_mb=0,
                    cpu_usage_percent=0,
                    success=False,
                    error_message=str(e)
                )
                metrics_list.append(metrics)
                self.results.append(metrics)
        
        # Calculate results
        successful_metrics = [m for m in metrics_list if m.success]
        execution_times = [m.execution_time_ms for m in successful_metrics]
        
        if execution_times:
            benchmark_result = BenchmarkResult(
                component_name="ToolDiscoveryAgent",
                total_operations=len(metrics_list),
                successful_operations=len(successful_metrics),
                avg_execution_time_ms=statistics.mean(execution_times),
                min_execution_time_ms=min(execution_times),
                max_execution_time_ms=max(execution_times),
                avg_memory_usage_mb=statistics.mean([m.memory_usage_mb for m in successful_metrics]),
                peak_memory_usage_mb=max([m.memory_peak_mb for m in successful_metrics]),
                cache_hit_rate=0,
                target_met=statistics.mean(execution_times) < 500
            )
        else:
            benchmark_result = BenchmarkResult(
                component_name="ToolDiscoveryAgent",
                total_operations=len(metrics_list),
                successful_operations=0,
                avg_execution_time_ms=0,
                min_execution_time_ms=0,
                max_execution_time_ms=0,
                avg_memory_usage_mb=0,
                peak_memory_usage_mb=0,
                cache_hit_rate=0,
                target_met=False
            )
        
        return benchmark_result
    
    async def benchmark_decision_engine(self) -> BenchmarkResult:
        """Benchmark DecisionEngine performance."""
        
        print("\n🧠 Benchmarking AutonomousDecisionEngine...")
        
        decision_engine = AutonomousDecisionEngine()
        metrics_list = []
        
        # Mock available servers
        class MockServerProfile:
            def __init__(self, name):
                self.name = name
                self.capabilities = []
        
        available_servers = [MockServerProfile(f"server_{i}") for i in range(5)]
        
        # Test decision operations on each task
        for i, task in enumerate(self.test_tasks[:5]):  # Limit to 5 for faster testing
            print(f"  Testing decision for task {i+1}: {task[:50]}...")
            
            start_cpu, start_memory = self.start_performance_monitoring()
            start_time = time.perf_counter()
            
            try:
                task_analysis, strategy_recommendation = decision_engine.analyze_and_recommend(
                    task, available_servers
                )
                
                end_time = time.perf_counter()
                execution_time = (end_time - start_time) * 1000
                
                memory_current, memory_peak, cpu_usage = self.stop_performance_monitoring(start_cpu, start_memory)
                
                metrics = PerformanceMetrics(
                    component_name="AutonomousDecisionEngine",
                    operation_name=f"analyze_and_recommend_{i+1}",
                    execution_time_ms=execution_time,
                    memory_usage_mb=memory_current,
                    memory_peak_mb=memory_peak,
                    cpu_usage_percent=cpu_usage,
                    success=True
                )
                
                metrics_list.append(metrics)
                self.results.append(metrics)
                
            except Exception as e:
                print(f"    ❌ Error: {str(e)}")
                metrics = PerformanceMetrics(
                    component_name="AutonomousDecisionEngine",
                    operation_name=f"analyze_and_recommend_{i+1}",
                    execution_time_ms=0,
                    memory_usage_mb=0,
                    memory_peak_mb=0,
                    cpu_usage_percent=0,
                    success=False,
                    error_message=str(e)
                )
                metrics_list.append(metrics)
                self.results.append(metrics)
        
        # Calculate results
        successful_metrics = [m for m in metrics_list if m.success]
        execution_times = [m.execution_time_ms for m in successful_metrics]
        
        if execution_times:
            benchmark_result = BenchmarkResult(
                component_name="AutonomousDecisionEngine",
                total_operations=len(metrics_list),
                successful_operations=len(successful_metrics),
                avg_execution_time_ms=statistics.mean(execution_times),
                min_execution_time_ms=min(execution_times),
                max_execution_time_ms=max(execution_times),
                avg_memory_usage_mb=statistics.mean([m.memory_usage_mb for m in successful_metrics]),
                peak_memory_usage_mb=max([m.memory_peak_mb for m in successful_metrics]),
                cache_hit_rate=0,
                target_met=statistics.mean(execution_times) < 500
            )
        else:
            benchmark_result = BenchmarkResult(
                component_name="AutonomousDecisionEngine",
                total_operations=len(metrics_list),
                successful_operations=0,
                avg_execution_time_ms=0,
                min_execution_time_ms=0,
                max_execution_time_ms=0,
                avg_memory_usage_mb=0,
                peak_memory_usage_mb=0,
                cache_hit_rate=0,
                target_met=False
            )
        
        return benchmark_result
    
    def print_benchmark_results(self, results: List[BenchmarkResult]):
        """Print formatted benchmark results."""
        
        print("\n" + "="*80)
        print("🚀 PERFORMANCE BENCHMARK RESULTS")
        print("="*80)
        
        for result in results:
            print(f"\n📊 {result.component_name}")
            print("-" * 50)
            print(f"Total Operations:     {result.total_operations}")
            print(f"Successful:           {result.successful_operations}")
            print(f"Success Rate:         {(result.successful_operations/result.total_operations)*100:.1f}%")
            print(f"Avg Execution Time:   {result.avg_execution_time_ms:.2f}ms")
            print(f"Min Execution Time:   {result.min_execution_time_ms:.2f}ms")
            print(f"Max Execution Time:   {result.max_execution_time_ms:.2f}ms")
            print(f"Avg Memory Usage:     {result.avg_memory_usage_mb:.2f}MB")
            print(f"Peak Memory Usage:    {result.peak_memory_usage_mb:.2f}MB")
            
            if result.cache_hit_rate > 0:
                print(f"Cache Hit Rate:       {result.cache_hit_rate:.1f}%")
            
            target_status = "✅ MET" if result.target_met else "❌ NOT MET"
            print(f"<500ms Target:        {target_status}")
            
            if result.performance_improvement != 0:
                improvement = f"{result.performance_improvement:+.1f}%"
                print(f"Performance Change:   {improvement}")
        
        # Overall summary
        print(f"\n" + "="*50)
        print("📈 OVERALL SUMMARY")
        print("="*50)
        
        avg_execution_time = statistics.mean([r.avg_execution_time_ms for r in results if r.successful_operations > 0])
        targets_met = sum(1 for r in results if r.target_met)
        total_components = len(results)
        
        print(f"Components Tested:    {total_components}")
        print(f"Targets Met:          {targets_met}/{total_components} ({(targets_met/total_components)*100:.1f}%)")
        print(f"Overall Avg Time:     {avg_execution_time:.2f}ms")
        
        if avg_execution_time < 500:
            print("🎉 Overall performance target MET!")
        else:
            print("⚠️  Overall performance target NOT MET - optimization needed")
    
    def save_results_to_file(self, results: List[BenchmarkResult], filename: str = "performance_results.json"):
        """Save benchmark results to JSON file."""
        
        data = {
            "timestamp": datetime.now().isoformat(),
            "results": []
        }
        
        for result in results:
            data["results"].append({
                "component_name": result.component_name,
                "total_operations": result.total_operations,
                "successful_operations": result.successful_operations,
                "avg_execution_time_ms": result.avg_execution_time_ms,
                "min_execution_time_ms": result.min_execution_time_ms,
                "max_execution_time_ms": result.max_execution_time_ms,
                "avg_memory_usage_mb": result.avg_memory_usage_mb,
                "peak_memory_usage_mb": result.peak_memory_usage_mb,
                "cache_hit_rate": result.cache_hit_rate,
                "target_met": result.target_met,
                "performance_improvement": result.performance_improvement
            })
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"\n💾 Results saved to {filename}")
    
    async def run_full_benchmark(self) -> List[BenchmarkResult]:
        """Run complete performance benchmark suite."""
        
        print("🏁 Starting MCP-Agent Performance Benchmark Suite")
        print("=" * 60)
        
        results = []
        
        # Benchmark TaskAnalyzer (both original and optimized)
        try:
            original_result = await self.benchmark_task_analyzer(use_optimized=False)
            results.append(original_result)
        except Exception as e:
            print(f"❌ TaskAnalyzer (Original) benchmark failed: {e}")
        
        try:
            optimized_result = await self.benchmark_task_analyzer(use_optimized=True)
            results.append(optimized_result)
            
            # Calculate improvement
            if len(results) >= 2 and results[-2].successful_operations > 0:
                improvement = ((results[-2].avg_execution_time_ms - optimized_result.avg_execution_time_ms) / 
                              results[-2].avg_execution_time_ms) * 100
                optimized_result.performance_improvement = improvement
        except Exception as e:
            print(f"❌ TaskAnalyzer (Optimized) benchmark failed: {e}")
        
        # Benchmark ToolDiscoveryAgent
        try:
            tool_discovery_result = await self.benchmark_tool_discovery()
            results.append(tool_discovery_result)
        except Exception as e:
            print(f"❌ ToolDiscoveryAgent benchmark failed: {e}")
        
        # Benchmark DecisionEngine
        try:
            decision_engine_result = await self.benchmark_decision_engine()
            results.append(decision_engine_result)
        except Exception as e:
            print(f"❌ DecisionEngine benchmark failed: {e}")
        
        return results


async def main():
    """Main benchmarking function."""
    
    print("🚀 MCP-Agent Performance Optimization Benchmarking")
    print("=" * 60)
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Python Version: {sys.version}")
    print(f"System: {os.name}")
    
    benchmark = PerformanceBenchmark()
    
    try:
        results = await benchmark.run_full_benchmark()
        
        # Print results
        benchmark.print_benchmark_results(results)
        
        # Save results
        benchmark.save_results_to_file(results)
        
        print(f"\n✅ Benchmark completed successfully!")
        print(f"End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Return success/failure based on targets
        targets_met = sum(1 for r in results if r.target_met)
        return targets_met == len(results)
        
    except Exception as e:
        print(f"❌ Benchmark failed: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
