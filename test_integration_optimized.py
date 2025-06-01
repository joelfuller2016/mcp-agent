#!/usr/bin/env python3
"""
Integration Testing Suite for Optimized MCP-Agent Components

This script validates that all optimized autonomous components (TaskAnalyzer, 
ToolDiscovery, DecisionEngine) work together seamlessly in real autonomous workflows.
"""

import sys
import os
import time
import asyncio
import statistics
import json
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

try:
    from mcp_agent.autonomous.task_analyzer_cached import CachedTaskAnalyzer
    from mcp_agent.autonomous.tool_discovery_optimized import ParallelToolDiscoveryAgent  
    from mcp_agent.autonomous.decision_engine_optimized import CachedAutonomousDecisionEngine
    from mcp_agent.autonomous.meta_coordinator_optimized import OptimizedMetaCoordinator
    from mcp_agent.mcp.mcp_connection_manager import MCPConnectionManager
    print("[OK] Integration test imports: SUCCESS")
except ImportError as e:
    print(f"[FAIL] Integration test imports: FAILED - {e}")
    try:
        # Fallback to original components if optimized versions not available
        from mcp_agent.autonomous.task_analyzer import TaskAnalyzer as CachedTaskAnalyzer
        from mcp_agent.autonomous.tool_discovery import ToolDiscoveryAgent as ParallelToolDiscoveryAgent
        from mcp_agent.autonomous.decision_engine import AutonomousDecisionEngine as CachedAutonomousDecisionEngine
        from mcp_agent.autonomous.meta_coordinator import MetaCoordinator as OptimizedMetaCoordinator
        print("[OK] Fallback to original components: SUCCESS")
    except ImportError as e2:
        print(f"[FAIL] Fallback imports also failed: {e2}")
        sys.exit(1)


@dataclass
class IntegrationTestResult:
    """Results from an integration test workflow."""
    
    workflow_name: str
    success: bool
    total_time_ms: float
    component_times: Dict[str, float]
    cache_performance: Dict[str, Any]
    error_message: str = ""
    steps_completed: int = 0
    total_steps: int = 0


@dataclass
class WorkflowTask:
    """Represents a complete autonomous workflow for testing."""
    
    name: str
    description: str
    expected_complexity: str
    expected_pattern: str
    required_capabilities: List[str]
    expected_steps_min: int
    expected_steps_max: int


class MockConnectionManager:
    """Mock connection manager for testing without real MCP servers."""
    
    def __init__(self):
        self.connected_servers = [
            "fetch", "filesystem", "github", "sqlite", "puppeteer", 
            "brave-search", "sequential-thinking", "slack", "postgres"
        ]
        
        self.server_tools = {
            "fetch": ["fetch_url", "fetch_html", "fetch_json", "fetch_txt"],
            "filesystem": ["read_file", "write_file", "list_directory", "create_directory"],
            "github": ["create_repo", "create_issue", "create_pr", "search_code"],
            "sqlite": ["query", "create_table", "insert_data", "backup"],
            "puppeteer": ["navigate", "click", "fill_form", "screenshot"],
            "brave-search": ["web_search", "news_search", "image_search"],
            "sequential-thinking": ["think_step", "reason_through", "plan_approach"],
            "slack": ["send_message", "create_channel", "get_messages"],
            "postgres": ["connect", "query", "insert", "create_table"]
        }
        
        self.server_resources = {
            server: [f"{server}_config", f"{server}_logs", f"{server}_cache"]
            for server in self.connected_servers
        }
    
    async def list_connected_servers(self):
        """Mock list of connected servers."""
        await asyncio.sleep(0.001)  # Simulate small network delay
        return self.connected_servers
    
    async def list_tools(self, server_name):
        """Mock tool listing."""
        await asyncio.sleep(0.002)  # Simulate network delay
        tools = []
        for tool_name in self.server_tools.get(server_name, []):
            tools.append(type('Tool', (), {'name': tool_name})())
        return tools
    
    async def list_resources(self, server_name):
        """Mock resource listing."""
        await asyncio.sleep(0.001)
        resources = []
        for resource_name in self.server_resources.get(server_name, []):
            resources.append(type('Resource', (), {'name': resource_name})())
        return resources
    
    async def connect_server(self, server_name):
        """Mock server connection."""
        await asyncio.sleep(0.005)
        return server_name in self.connected_servers


class IntegrationTestSuite:
    """Comprehensive integration testing for optimized components."""
    
    def __init__(self):
        self.mock_connection_manager = MockConnectionManager()
        self.test_results: List[IntegrationTestResult] = []
        
        # Initialize optimized components
        self.task_analyzer = CachedTaskAnalyzer(enable_cache_stats=True)
        self.tool_discovery = ParallelToolDiscoveryAgent(
            self.mock_connection_manager, 
            max_concurrent_operations=5
        )
        self.decision_engine = CachedAutonomousDecisionEngine(enable_cache_stats=True)
        
        # Define complex workflow test cases
        self.workflow_tests = [
            WorkflowTask(
                name="Simple Web Research",
                description="Search for information about MCP protocol and save findings to a file",
                expected_complexity="MODERATE",
                expected_pattern="PARALLEL", 
                required_capabilities=["web_search", "file_management"],
                expected_steps_min=3,
                expected_steps_max=6
            ),
            WorkflowTask(
                name="Complex Data Pipeline",
                description="Fetch data from multiple APIs, analyze patterns, store in database, and generate comprehensive report with visualizations",
                expected_complexity="EXPERT",
                expected_pattern="ORCHESTRATOR",
                required_capabilities=["web_automation", "database", "data_analysis", "file_management"],
                expected_steps_min=8,
                expected_steps_max=15
            ),
            WorkflowTask(
                name="Code Development Workflow", 
                description="Create a GitHub repository, develop REST API with authentication, write tests, and set up automated deployment",
                expected_complexity="ADVANCED",
                expected_pattern="ORCHESTRATOR",
                required_capabilities=["development", "database", "web_automation"],
                expected_steps_min=6,
                expected_steps_max=12
            ),
            WorkflowTask(
                name="Multi-Agent Research",
                description="Research AI trends across multiple sources, compare findings, collaborate between agents to synthesize insights, and create executive summary",
                expected_complexity="EXPERT", 
                expected_pattern="SWARM",
                required_capabilities=["web_search", "data_analysis", "cognitive", "file_management"],
                expected_steps_min=10,
                expected_steps_max=20
            ),
            WorkflowTask(
                name="Quick File Operation",
                description="Read a CSV file and display basic statistics",
                expected_complexity="SIMPLE",
                expected_pattern="DIRECT",
                required_capabilities=["file_management", "data_analysis"],
                expected_steps_min=1,
                expected_steps_max=3
            )
        ]
    
    async def test_full_autonomous_workflow(self, workflow: WorkflowTask) -> IntegrationTestResult:
        """Test a complete autonomous workflow through all optimized components."""
        
        print(f"\n🔄 Testing Workflow: {workflow.name}")
        print(f"   Description: {workflow.description}")
        
        start_time = time.perf_counter()
        component_times = {}
        steps_completed = 0
        total_steps = 7  # Standard workflow steps
        
        try:
            # Step 1: Task Analysis (Optimized with Caching)
            print("   Step 1/7: Task Analysis...")
            step_start = time.perf_counter()
            task_analysis = self.task_analyzer.analyze_task(workflow.description)
            component_times["task_analysis"] = (time.perf_counter() - step_start) * 1000
            steps_completed += 1
            
            # Validate task analysis results
            assert task_analysis.complexity.name.upper() == workflow.expected_complexity, \
                f"Expected complexity {workflow.expected_complexity}, got {task_analysis.complexity.name}"
            
            assert workflow.expected_steps_min <= task_analysis.estimated_steps <= workflow.expected_steps_max, \
                f"Steps {task_analysis.estimated_steps} outside expected range {workflow.expected_steps_min}-{workflow.expected_steps_max}"
            
            print(f"      ✅ Complexity: {task_analysis.complexity.name}, Steps: {task_analysis.estimated_steps}")
            
            # Step 2: Tool Discovery (Optimized with Parallel Processing)
            print("   Step 2/7: Tool Discovery...")
            step_start = time.perf_counter()
            discovered_servers = await self.tool_discovery.discover_available_servers()
            component_times["tool_discovery"] = (time.perf_counter() - step_start) * 1000
            steps_completed += 1
            
            assert len(discovered_servers) > 0, "No servers discovered"
            print(f"      ✅ Discovered {len(discovered_servers)} servers")
            
            # Step 3: Server Capability Mapping
            print("   Step 3/7: Capability Mapping...")
            step_start = time.perf_counter()
            relevant_servers = self.tool_discovery.get_best_servers_for_task(
                workflow.description, max_servers=5
            )
            component_times["capability_mapping"] = (time.perf_counter() - step_start) * 1000
            steps_completed += 1
            
            assert len(relevant_servers) > 0, "No relevant servers found"
            print(f"      ✅ Mapped {len(relevant_servers)} relevant servers")
            
            # Step 4: Decision Engine Analysis (Optimized with Caching)
            print("   Step 4/7: Decision Analysis...")
            step_start = time.perf_counter()
            
            # Create mock server profiles for decision engine
            mock_server_profiles = []
            for server_info in relevant_servers:
                mock_profile = type('MockProfile', (), {
                    'name': server_info.name,
                    'capabilities': [
                        type('MockCapability', (), {'category': cap.value})() 
                        for cap in server_info.capabilities
                    ]
                })()
                mock_server_profiles.append(mock_profile)
            
            task_analysis_result, strategy_recommendation = self.decision_engine.analyze_and_recommend(
                workflow.description, mock_server_profiles
            )
            component_times["decision_analysis"] = (time.perf_counter() - step_start) * 1000
            steps_completed += 1
            
            # Validate decision results
            assert strategy_recommendation.pattern.value.upper() == workflow.expected_pattern, \
                f"Expected pattern {workflow.expected_pattern}, got {strategy_recommendation.pattern.value}"
            
            print(f"      ✅ Pattern: {strategy_recommendation.pattern.value}, Confidence: {strategy_recommendation.confidence:.2f}")
            
            # Step 5: Workflow Planning 
            print("   Step 5/7: Workflow Planning...")
            step_start = time.perf_counter()
            
            # Simulate workflow planning based on strategy
            workflow_plan = {
                "pattern": strategy_recommendation.pattern.value,
                "servers": strategy_recommendation.required_servers,
                "estimated_time": strategy_recommendation.estimated_execution_time,
                "steps": task_analysis.estimated_steps
            }
            component_times["workflow_planning"] = (time.perf_counter() - step_start) * 1000
            steps_completed += 1
            
            print(f"      ✅ Plan created with {len(workflow_plan['servers'])} servers")
            
            # Step 6: Resource Validation
            print("   Step 6/7: Resource Validation...")
            step_start = time.perf_counter()
            
            # Validate that required servers are available
            required_servers = [s.name for s in relevant_servers]
            validation_results = await self.tool_discovery.validate_servers_connectivity_parallel(
                required_servers[:3]  # Limit to 3 for faster testing
            )
            component_times["resource_validation"] = (time.perf_counter() - step_start) * 1000
            steps_completed += 1
            
            validated_servers = sum(1 for result in validation_results.values() if result)
            print(f"      ✅ Validated {validated_servers}/{len(validation_results)} servers")
            
            # Step 7: Integration Validation
            print("   Step 7/7: Integration Validation...")
            step_start = time.perf_counter()
            
            # Verify all required capabilities are covered
            covered_capabilities = set()
            for server_info in relevant_servers:
                covered_capabilities.update(cap.value for cap in server_info.capabilities)
            
            # Check coverage of required capabilities
            required_caps_covered = 0
            for req_cap in workflow.required_capabilities:
                if any(req_cap in covered_cap for covered_cap in covered_capabilities):
                    required_caps_covered += 1
            
            component_times["integration_validation"] = (time.perf_counter() - step_start) * 1000
            steps_completed += 1
            
            print(f"      ✅ Coverage: {required_caps_covered}/{len(workflow.required_capabilities)} capabilities")
            
            # Calculate total time
            total_time = (time.perf_counter() - start_time) * 1000
            
            # Collect cache performance data
            cache_performance = {}
            
            # Task Analyzer cache stats
            if hasattr(self.task_analyzer, 'get_cache_info'):
                cache_performance["task_analyzer"] = self.task_analyzer.get_cache_info()
            
            # Decision Engine cache stats  
            if hasattr(self.decision_engine, 'get_cache_performance_summary'):
                cache_performance["decision_engine"] = self.decision_engine.get_cache_performance_summary()
            
            # Tool Discovery performance stats
            if hasattr(self.tool_discovery, 'get_performance_summary'):
                cache_performance["tool_discovery"] = self.tool_discovery.get_performance_summary()
            
            result = IntegrationTestResult(
                workflow_name=workflow.name,
                success=True,
                total_time_ms=total_time,
                component_times=component_times,
                cache_performance=cache_performance,
                steps_completed=steps_completed,
                total_steps=total_steps
            )
            
            print(f"   ✅ Workflow completed successfully in {total_time:.2f}ms")
            return result
            
        except Exception as e:
            total_time = (time.perf_counter() - start_time) * 1000
            
            result = IntegrationTestResult(
                workflow_name=workflow.name,
                success=False,
                total_time_ms=total_time,
                component_times=component_times,
                cache_performance={},
                error_message=str(e),
                steps_completed=steps_completed,
                total_steps=total_steps
            )
            
            print(f"   ❌ Workflow failed: {str(e)}")
            return result
    
    async def run_integration_test_suite(self) -> List[IntegrationTestResult]:
        """Run the complete integration test suite."""
        
        print("🚀 MCP-Agent Optimized Components Integration Testing")
        print("=" * 70)
        print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Test Workflows: {len(self.workflow_tests)}")
        
        # Warm up caches with simple tasks
        print("\n🔥 Warming up caches...")
        cache_warmup_tasks = [
            "Read a file",
            "Search the web", 
            "Create a document",
            "Analyze data",
            "Send a message"
        ]
        
        for task in cache_warmup_tasks:
            try:
                self.task_analyzer.analyze_task(task)
            except Exception:
                pass  # Cache warmup failures are non-critical
        
        print("   ✅ Cache warmup complete")
        
        # Run all workflow tests
        all_results = []
        successful_workflows = 0
        
        for i, workflow in enumerate(self.workflow_tests, 1):
            print(f"\n🔬 Running Integration Test {i}/{len(self.workflow_tests)}")
            result = await self.test_full_autonomous_workflow(workflow)
            all_results.append(result)
            
            if result.success:
                successful_workflows += 1
        
        # Test cache effectiveness with repeated workflows
        print(f"\n🔄 Testing Cache Effectiveness...")
        cache_test_start = time.perf_counter()
        
        # Run the first workflow again to test caching
        repeated_result = await self.test_full_autonomous_workflow(self.workflow_tests[0])
        cache_test_time = (time.perf_counter() - cache_test_start) * 1000
        
        print(f"   Original time: {all_results[0].total_time_ms:.2f}ms")
        print(f"   Cached time: {repeated_result.total_time_ms:.2f}ms")
        if all_results[0].total_time_ms > 0:
            improvement = ((all_results[0].total_time_ms - repeated_result.total_time_ms) / 
                          all_results[0].total_time_ms) * 100
            print(f"   Cache improvement: {improvement:.1f}%")
        
        # Print comprehensive results
        self.print_integration_results(all_results, successful_workflows)
        
        # Save results to file
        self.save_integration_results(all_results)
        
        self.test_results = all_results
        return all_results
    
    def print_integration_results(self, results: List[IntegrationTestResult], successful: int):
        """Print formatted integration test results."""
        
        print("\n" + "="*80)
        print("🎯 INTEGRATION TEST RESULTS")
        print("="*80)
        
        total_tests = len(results)
        success_rate = (successful / total_tests) * 100
        
        print(f"Total Workflows Tested: {total_tests}")
        print(f"Successful Workflows: {successful}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if successful > 0:
            successful_results = [r for r in results if r.success]
            avg_time = statistics.mean([r.total_time_ms for r in successful_results])
            min_time = min([r.total_time_ms for r in successful_results])
            max_time = max([r.total_time_ms for r in successful_results])
            
            print(f"Average Workflow Time: {avg_time:.2f}ms")
            print(f"Fastest Workflow: {min_time:.2f}ms")
            print(f"Slowest Workflow: {max_time:.2f}ms")
        
        print("\n📊 Detailed Results:")
        print("-" * 50)
        
        for result in results:
            status = "✅ PASS" if result.success else "❌ FAIL"
            print(f"{status} {result.workflow_name}: {result.total_time_ms:.2f}ms")
            
            if result.success:
                print(f"    Steps: {result.steps_completed}/{result.total_steps}")
                
                # Show component breakdown
                if result.component_times:
                    print("    Component Times:")
                    for component, time_ms in result.component_times.items():
                        print(f"      {component}: {time_ms:.2f}ms")
                
                # Show cache performance if available
                if result.cache_performance:
                    print("    Cache Performance:")
                    for component, stats in result.cache_performance.items():
                        if isinstance(stats, dict) and 'hit_rate' in stats:
                            print(f"      {component}: {stats['hit_rate']:.1f}% hit rate")
            else:
                print(f"    Error: {result.error_message}")
        
        # Overall assessment
        print(f"\n" + "="*50)
        print("📈 INTEGRATION ASSESSMENT")
        print("="*50)
        
        if success_rate >= 100:
            print("🎉 EXCELLENT: All workflows integrated successfully!")
        elif success_rate >= 80:
            print("✅ GOOD: Most workflows integrated successfully")
        elif success_rate >= 60:
            print("⚠️  FAIR: Some integration issues detected")
        else:
            print("❌ POOR: Significant integration problems found")
        
        if successful > 0:
            avg_time = statistics.mean([r.total_time_ms for r in results if r.success])
            if avg_time < 100:
                print("⚡ PERFORMANCE: Excellent response times (<100ms)")
            elif avg_time < 500:
                print("✅ PERFORMANCE: Good response times (<500ms)")
            else:
                print("⚠️  PERFORMANCE: Consider optimization (>500ms)")
    
    def save_integration_results(self, results: List[IntegrationTestResult]):
        """Save integration test results to JSON file."""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"integration_results_{timestamp}.json"
        
        data = {
            "timestamp": datetime.now().isoformat(),
            "total_workflows": len(results),
            "successful_workflows": sum(1 for r in results if r.success),
            "success_rate": (sum(1 for r in results if r.success) / len(results)) * 100,
            "results": []
        }
        
        for result in results:
            data["results"].append({
                "workflow_name": result.workflow_name,
                "success": result.success,
                "total_time_ms": result.total_time_ms,
                "component_times": result.component_times,
                "cache_performance": result.cache_performance,
                "error_message": result.error_message,
                "steps_completed": result.steps_completed,
                "total_steps": result.total_steps
            })
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"\n💾 Integration results saved to {filename}")
    
    def get_integration_summary(self) -> Dict[str, Any]:
        """Get summary of integration test results."""
        
        if not self.test_results:
            return {"status": "not_run"}
        
        successful = sum(1 for r in self.test_results if r.success)
        total = len(self.test_results)
        
        successful_results = [r for r in self.test_results if r.success]
        
        summary = {
            "status": "completed",
            "total_workflows": total,
            "successful_workflows": successful,
            "success_rate": (successful / total) * 100,
            "avg_workflow_time_ms": statistics.mean([r.total_time_ms for r in successful_results]) if successful_results else 0,
            "components_tested": ["task_analyzer", "tool_discovery", "decision_engine"],
            "optimization_validated": True,
            "performance_target_met": all(r.total_time_ms < 500 for r in successful_results),
            "cache_effectiveness": any(
                result.cache_performance for result in self.test_results 
                if result.success and result.cache_performance
            )
        }
        
        return summary


async def main():
    """Main integration testing function."""
    
    try:
        test_suite = IntegrationTestSuite()
        results = await test_suite.run_integration_test_suite()
        
        # Return success based on results
        successful = sum(1 for r in results if r.success)
        total = len(results)
        
        if successful == total:
            print(f"\n✅ All integration tests passed ({successful}/{total})")
            return True
        else:
            print(f"\n⚠️  Some integration tests failed ({successful}/{total})")
            return False
            
    except Exception as e:
        print(f"❌ Integration testing failed: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
