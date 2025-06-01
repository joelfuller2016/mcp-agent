#!/usr/bin/env python3
"""
Load Testing Suite for Optimized MCP-Agent Components (Windows Compatible)

This script validates performance under concurrent multi-user scenarios to ensure
the optimized components meet scalability targets and maintain performance under load.
"""

import sys
import os
import time
import asyncio
import statistics
import json
import threading
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

try:
    from mcp_agent.autonomous.task_analyzer_cached import CachedTaskAnalyzer
    from mcp_agent.autonomous.tool_discovery_optimized import ParallelToolDiscoveryAgent  
    print("[OK] Load test imports: SUCCESS")
    USING_OPTIMIZED = True
except ImportError as e:
    # Fallback to original components
    from mcp_agent.autonomous.task_analyzer import TaskAnalyzer as CachedTaskAnalyzer
    from mcp_agent.autonomous.tool_discovery import ToolDiscoveryAgent as ParallelToolDiscoveryAgent
    print("[OK] Fallback to original components: SUCCESS")
    USING_OPTIMIZED = False


@dataclass
class LoadTestMetrics:
    """Metrics collected during load testing."""
    
    test_name: str
    concurrent_users: int
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_response_time_ms: float
    min_response_time_ms: float
    max_response_time_ms: float
    p95_response_time_ms: float
    requests_per_second: float
    errors: List[str] = field(default_factory=list)


@dataclass
class ConcurrentTaskResult:
    """Result from a single concurrent task execution."""
    
    task_id: int
    success: bool
    response_time_ms: float
    error_message: str = ""


class MockConnectionManager:
    """Thread-safe mock connection manager for load testing."""
    
    def __init__(self):
        self.connected_servers = [
            "fetch", "filesystem", "github", "sqlite", "puppeteer", 
            "brave-search", "sequential-thinking"
        ]
        
        self.server_tools = {
            "fetch": ["fetch_url", "fetch_html", "fetch_json"],
            "filesystem": ["read_file", "write_file", "list_directory"],
            "github": ["create_repo", "create_issue", "create_pr"],
            "sqlite": ["query", "create_table", "insert_data"],
            "puppeteer": ["navigate", "click", "fill_form"],
            "brave-search": ["web_search", "news_search"],
            "sequential-thinking": ["think_step", "reason_through"]
        }
        
        # Add thread safety
        self._lock = threading.Lock()
    
    async def list_connected_servers(self):
        await asyncio.sleep(0.001)  # Simulate network latency
        return self.connected_servers
    
    async def list_tools(self, server_name):
        await asyncio.sleep(0.002)  # Simulate network latency
        tools = []
        for tool_name in self.server_tools.get(server_name, []):
            tools.append(type('Tool', (), {'name': tool_name})())
        return tools
    
    async def list_resources(self, server_name):
        await asyncio.sleep(0.001)
        resources = []
        for i in range(3):  # 3 resources per server
            resources.append(type('Resource', (), {'name': f"{server_name}_resource_{i}"})())
        return resources


class LoadTestSuite:
    """Load testing suite for optimized components."""
    
    def __init__(self):
        self.mock_connection_manager = MockConnectionManager()
        self.test_results = []
        
        # Test scenarios with varying complexity
        self.test_scenarios = [
            "Create a simple Python script to read a file",
            "Search for information about machine learning and analyze results",
            "Build a web automation script to collect data from multiple sources",
            "Analyze large dataset and generate comprehensive statistical report",
            "Create GitHub repository with documentation and automated testing",
            "Set up database connection and perform complex queries",
            "Research AI trends and create executive summary",
            "Develop microservices architecture with deployment pipeline"
        ]
        
        # Load test configurations
        self.load_test_configs = [
            {"users": 1, "requests": 5, "name": "Baseline"},
            {"users": 3, "requests": 15, "name": "Light_Load"},
            {"users": 5, "requests": 25, "name": "Medium_Load"},
            {"users": 10, "requests": 40, "name": "Heavy_Load"}
        ]
    
    async def execute_single_task(self, task_id: int, task_description: str, 
                                  components: Dict[str, Any]) -> ConcurrentTaskResult:
        """Execute a single task and measure performance."""
        
        start_time = time.perf_counter()
        
        try:
            # Task Analysis
            task_analysis = components['task_analyzer'].analyze_task(task_description)
            
            # Tool Discovery  
            discovered_servers = await components['tool_discovery'].discover_available_servers()
            
            # Server Selection
            relevant_servers = components['tool_discovery'].get_best_servers_for_task(
                task_description, max_servers=3
            )
            
            total_time = (time.perf_counter() - start_time) * 1000
            
            return ConcurrentTaskResult(
                task_id=task_id,
                success=True,
                response_time_ms=total_time
            )
            
        except Exception as e:
            total_time = (time.perf_counter() - start_time) * 1000
            
            return ConcurrentTaskResult(
                task_id=task_id,
                success=False,
                response_time_ms=total_time,
                error_message=str(e)
            )
    
    async def run_concurrent_load_test(self, concurrent_users: int, 
                                       requests_per_user: int) -> LoadTestMetrics:
        """Run a load test with specified concurrency."""
        
        test_name = f"{concurrent_users}_users_{requests_per_user}_requests"
        print(f"\nRunning Load Test: {test_name}")
        print(f"  Concurrent Users: {concurrent_users}")
        print(f"  Total Requests: {concurrent_users * requests_per_user}")
        
        # Initialize shared components
        components = {
            'task_analyzer': CachedTaskAnalyzer(),
            'tool_discovery': ParallelToolDiscoveryAgent(
                self.mock_connection_manager,
                max_concurrent_operations=concurrent_users
            )
        }
        
        # Prepare tasks
        all_tasks = []
        task_id = 0
        
        for user in range(concurrent_users):
            for request in range(requests_per_user):
                task_description = self.test_scenarios[task_id % len(self.test_scenarios)]
                all_tasks.append((task_id, task_description))
                task_id += 1
        
        # Execute load test
        start_time = time.perf_counter()
        
        # Create semaphore to control concurrency
        semaphore = asyncio.Semaphore(concurrent_users)
        
        async def execute_with_semaphore(task_data):
            async with semaphore:
                task_id, task_description = task_data
                return await self.execute_single_task(task_id, task_description, components)
        
        # Execute all tasks concurrently
        results = await asyncio.gather(
            *[execute_with_semaphore(task_data) for task_data in all_tasks],
            return_exceptions=True
        )
        
        end_time = time.perf_counter()
        total_test_time = end_time - start_time
        
        # Process results
        successful_results = []
        failed_results = []
        errors = []
        
        for result in results:
            if isinstance(result, Exception):
                failed_results.append(result)
                errors.append(str(result))
            elif result.success:
                successful_results.append(result)
            else:
                failed_results.append(result)
                errors.append(result.error_message)
        
        # Calculate metrics
        if successful_results:
            response_times = [r.response_time_ms for r in successful_results]
            
            # Calculate percentiles safely
            p95_time = response_times[0]  # Default to first value
            if len(response_times) > 1:
                sorted_times = sorted(response_times)
                p95_index = int(0.95 * len(sorted_times))
                p95_time = sorted_times[min(p95_index, len(sorted_times) - 1)]
            
            metrics = LoadTestMetrics(
                test_name=test_name,
                concurrent_users=concurrent_users,
                total_requests=len(all_tasks),
                successful_requests=len(successful_results),
                failed_requests=len(failed_results),
                avg_response_time_ms=statistics.mean(response_times),
                min_response_time_ms=min(response_times),
                max_response_time_ms=max(response_times),
                p95_response_time_ms=p95_time,
                requests_per_second=len(successful_results) / total_test_time,
                errors=errors[:5]  # Limit to first 5 errors
            )
        else:
            # No successful requests
            metrics = LoadTestMetrics(
                test_name=test_name,
                concurrent_users=concurrent_users,
                total_requests=len(all_tasks),
                successful_requests=0,
                failed_requests=len(failed_results),
                avg_response_time_ms=0,
                min_response_time_ms=0,
                max_response_time_ms=0,
                p95_response_time_ms=0,
                requests_per_second=0,
                errors=errors[:5]
            )
        
        # Print test results
        success_rate = (metrics.successful_requests / metrics.total_requests) * 100
        print(f"  Results:")
        print(f"    Success Rate: {success_rate:.1f}%")
        print(f"    Avg Response Time: {metrics.avg_response_time_ms:.2f}ms")
        print(f"    P95 Response Time: {metrics.p95_response_time_ms:.2f}ms")
        print(f"    Requests/sec: {metrics.requests_per_second:.2f}")
        
        if metrics.avg_response_time_ms < 500:
            print(f"    Performance Target: [PASS] MET (<500ms)")
        else:
            print(f"    Performance Target: [FAIL] NOT MET ({metrics.avg_response_time_ms:.0f}ms)")
        
        return metrics
    
    async def run_full_load_test_suite(self) -> List[LoadTestMetrics]:
        """Run the complete load testing suite."""
        
        print("MCP-Agent Load Testing Suite")
        print("=" * 60)
        print(f"Using Optimized Components: {USING_OPTIMIZED}")
        print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Test Configurations: {len(self.load_test_configs)}")
        
        all_results = []
        
        # Warm up components
        print("\nWarming up components...")
        warmup_components = {
            'task_analyzer': CachedTaskAnalyzer(),
            'tool_discovery': ParallelToolDiscoveryAgent(self.mock_connection_manager)
        }
        
        for scenario in self.test_scenarios[:2]:
            try:
                await self.execute_single_task(0, scenario, warmup_components)
            except Exception:
                pass  # Warmup failures are non-critical
        
        print("   [OK] Warmup complete")
        
        # Run each load test configuration
        for i, config in enumerate(self.load_test_configs, 1):
            print(f"\nLoad Test {i}/{len(self.load_test_configs)}: {config['name']}")
            
            try:
                metrics = await self.run_concurrent_load_test(
                    config['users'], 
                    config['requests'] // config['users']
                )
                all_results.append(metrics)
                
                # Brief pause between tests
                await asyncio.sleep(1)
                
            except Exception as e:
                print(f"  [FAIL] Load test failed: {e}")
                # Create failed metrics entry
                failed_metrics = LoadTestMetrics(
                    test_name=f"{config['name']}_FAILED",
                    concurrent_users=config['users'],
                    total_requests=config['requests'],
                    successful_requests=0,
                    failed_requests=config['requests'],
                    avg_response_time_ms=0,
                    min_response_time_ms=0,
                    max_response_time_ms=0,
                    p95_response_time_ms=0,
                    requests_per_second=0,
                    errors=[str(e)]
                )
                all_results.append(failed_metrics)
        
        # Print comprehensive results
        self.print_load_test_results(all_results)
        
        # Save results
        self.save_load_test_results(all_results)
        
        return all_results
    
    def print_load_test_results(self, results: List[LoadTestMetrics]):
        """Print comprehensive load test results."""
        
        print("\n" + "="*80)
        print("LOAD TEST RESULTS SUMMARY")
        print("="*80)
        
        # Overall statistics
        successful_tests = [r for r in results if r.successful_requests > 0]
        total_requests = sum(r.total_requests for r in results)
        total_successful = sum(r.successful_requests for r in results)
        
        if total_requests > 0:
            overall_success_rate = (total_successful / total_requests) * 100
            print(f"Overall Success Rate: {overall_success_rate:.1f}%")
        
        if successful_tests:
            avg_response_times = [r.avg_response_time_ms for r in successful_tests]
            max_throughput = max(r.requests_per_second for r in successful_tests)
            
            print(f"Response Time Range: {min(avg_response_times):.2f}ms - {max(avg_response_times):.2f}ms")
            print(f"Maximum Throughput: {max_throughput:.2f} requests/sec")
        
        print(f"Tests Completed: {len(results)}")
        
        # Detailed results table
        print(f"\nDetailed Results:")
        print("-" * 80)
        print(f"{'Test Name':<15} {'Users':<6} {'Success%':<8} {'Avg(ms)':<8} {'P95(ms)':<8} {'RPS':<8}")
        print("-" * 80)
        
        for result in results:
            success_rate = (result.successful_requests / result.total_requests) * 100 if result.total_requests > 0 else 0
            
            print(f"{result.test_name[:14]:<15} "
                  f"{result.concurrent_users:<6} "
                  f"{success_rate:<7.1f}% "
                  f"{result.avg_response_time_ms:<7.1f} "
                  f"{result.p95_response_time_ms:<7.1f} "
                  f"{result.requests_per_second:<7.1f}")
        
        # Performance assessment
        print(f"\n" + "="*50)
        print("PERFORMANCE ASSESSMENT")
        print("="*50)
        
        # Check if performance targets are met
        target_met_tests = [r for r in successful_tests if r.avg_response_time_ms < 500]
        target_percentage = (len(target_met_tests) / max(len(successful_tests), 1)) * 100
        
        print(f"Performance Target (<500ms): {target_percentage:.1f}% of tests")
        
        if target_percentage == 100 and len(successful_tests) > 0:
            print("[EXCELLENT] All load tests meet performance targets!")
        elif target_percentage >= 80:
            print("[GOOD] Most load tests meet performance targets")
        elif target_percentage >= 60:
            print("[FAIR] Some performance degradation under load")
        else:
            print("[POOR] Significant performance issues under load")
        
        # Scalability assessment
        if len(successful_tests) >= 2:
            baseline = min(successful_tests, key=lambda x: x.concurrent_users)
            peak_load = max(successful_tests, key=lambda x: x.concurrent_users)
            
            if baseline.avg_response_time_ms > 0:
                response_time_degradation = ((peak_load.avg_response_time_ms - baseline.avg_response_time_ms) / 
                                           baseline.avg_response_time_ms) * 100
                
                print(f"\nScalability Analysis:")
                print(f"  Baseline ({baseline.concurrent_users} users): {baseline.avg_response_time_ms:.2f}ms")
                print(f"  Peak Load ({peak_load.concurrent_users} users): {peak_load.avg_response_time_ms:.2f}ms")
                print(f"  Performance Degradation: {response_time_degradation:.1f}%")
                
                if response_time_degradation < 50:
                    print("  [EXCELLENT] Excellent scalability")
                elif response_time_degradation < 100:
                    print("  [GOOD] Good scalability")
                elif response_time_degradation < 200:
                    print("  [FAIR] Fair scalability")
                else:
                    print("  [POOR] Poor scalability")
    
    def save_load_test_results(self, results: List[LoadTestMetrics]):
        """Save load test results to JSON file."""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"load_test_results_{timestamp}.json"
        
        data = {
            "timestamp": datetime.now().isoformat(),
            "using_optimized_components": USING_OPTIMIZED,
            "total_tests": len(results),
            "successful_tests": len([r for r in results if r.successful_requests > 0]),
            "results": []
        }
        
        for result in results:
            data["results"].append({
                "test_name": result.test_name,
                "concurrent_users": result.concurrent_users,
                "total_requests": result.total_requests,
                "successful_requests": result.successful_requests,
                "failed_requests": result.failed_requests,
                "success_rate": (result.successful_requests / result.total_requests) * 100 if result.total_requests > 0 else 0,
                "avg_response_time_ms": result.avg_response_time_ms,
                "min_response_time_ms": result.min_response_time_ms,
                "max_response_time_ms": result.max_response_time_ms,
                "p95_response_time_ms": result.p95_response_time_ms,
                "requests_per_second": result.requests_per_second,
                "errors": result.errors,
                "performance_target_met": result.avg_response_time_ms < 500
            })
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"\nLoad test results saved to {filename}")


async def main():
    """Main load testing function."""
    
    try:
        load_test_suite = LoadTestSuite()
        results = await load_test_suite.run_full_load_test_suite()
        
        # Determine overall success
        successful_tests = [r for r in results if r.successful_requests > 0]
        target_met_tests = [r for r in successful_tests if r.avg_response_time_ms < 500]
        
        if len(target_met_tests) == len(successful_tests) and len(successful_tests) > 0:
            print(f"\n[SUCCESS] All load tests passed performance targets!")
            return True
        elif len(successful_tests) > 0:
            print(f"\n[PARTIAL] Some load tests passed, some had performance issues")
            return False
        else:
            print(f"\n[FAILED] All load tests failed")
            return False
            
    except Exception as e:
        print(f"[ERROR] Load testing failed: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
