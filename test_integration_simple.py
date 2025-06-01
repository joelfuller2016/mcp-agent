#!/usr/bin/env python3
"""
Integration Testing Suite for Optimized MCP-Agent Components (Simplified)

This script validates that all optimized autonomous components work together 
seamlessly in real autonomous workflows.
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
    # Try to import optimized components
    from mcp_agent.autonomous.task_analyzer_cached import CachedTaskAnalyzer
    from mcp_agent.autonomous.tool_discovery_optimized import ParallelToolDiscoveryAgent  
    from mcp_agent.autonomous.decision_engine_optimized import CachedAutonomousDecisionEngine
    print("[OK] Optimized component imports: SUCCESS")
    USING_OPTIMIZED = True
except ImportError as e:
    # Fallback to original components
    from mcp_agent.autonomous.task_analyzer import TaskAnalyzer as CachedTaskAnalyzer
    from mcp_agent.autonomous.tool_discovery import ToolDiscoveryAgent as ParallelToolDiscoveryAgent
    from mcp_agent.autonomous.decision_engine import AutonomousDecisionEngine as CachedAutonomousDecisionEngine
    print("[OK] Fallback to original components: SUCCESS")
    USING_OPTIMIZED = False


@dataclass
class IntegrationTestResult:
    """Results from an integration test workflow."""
    
    workflow_name: str
    success: bool
    total_time_ms: float
    component_times: Dict[str, float]
    error_message: str = ""
    steps_completed: int = 0


class MockConnectionManager:
    """Mock connection manager for testing without real MCP servers."""
    
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
        
        self.server_resources = {
            server: [f"{server}_config", f"{server}_logs"]
            for server in self.connected_servers
        }
    
    async def list_connected_servers(self):
        await asyncio.sleep(0.001)
        return self.connected_servers
    
    async def list_tools(self, server_name):
        await asyncio.sleep(0.002)
        tools = []
        for tool_name in self.server_tools.get(server_name, []):
            tools.append(type('Tool', (), {'name': tool_name})())
        return tools
    
    async def list_resources(self, server_name):
        await asyncio.sleep(0.001)
        resources = []
        for resource_name in self.server_resources.get(server_name, []):
            resources.append(type('Resource', (), {'name': resource_name})())
        return resources
    
    async def connect_server(self, server_name):
        await asyncio.sleep(0.005)
        return server_name in self.connected_servers


class IntegrationTestSuite:
    """Simplified integration testing for optimized components."""
    
    def __init__(self):
        self.mock_connection_manager = MockConnectionManager()
        self.test_results = []
        
        # Initialize components with proper parameters
        if USING_OPTIMIZED:
            self.task_analyzer = CachedTaskAnalyzer()
            self.tool_discovery = ParallelToolDiscoveryAgent(
                self.mock_connection_manager, 
                max_concurrent_operations=5
            )
            self.decision_engine = CachedAutonomousDecisionEngine()
        else:
            self.task_analyzer = CachedTaskAnalyzer()
            self.tool_discovery = ParallelToolDiscoveryAgent(self.mock_connection_manager)
            self.decision_engine = CachedAutonomousDecisionEngine()
        
        # Define test workflows
        self.workflow_tests = [
            {
                "name": "Simple Web Research",
                "description": "Search for information about MCP protocol and save findings to a file",
                "expected_complexity": "MODERATE",
            },
            {
                "name": "Data Analysis Task", 
                "description": "Analyze CSV data and generate statistical report with visualizations",
                "expected_complexity": "COMPLEX",
            },
            {
                "name": "Quick File Operation",
                "description": "Read a file and display basic information",
                "expected_complexity": "SIMPLE",
            }
        ]
    
    async def test_workflow_integration(self, workflow) -> IntegrationTestResult:
        """Test a complete workflow through all components."""
        
        print(f"\nTesting Workflow: {workflow['name']}")
        print(f"Description: {workflow['description']}")
        
        start_time = time.perf_counter()
        component_times = {}
        steps_completed = 0
        
        try:
            # Step 1: Task Analysis
            print("  Step 1/5: Task Analysis...")
            step_start = time.perf_counter()
            task_analysis = self.task_analyzer.analyze_task(workflow['description'])
            component_times["task_analysis"] = (time.perf_counter() - step_start) * 1000
            steps_completed += 1
            
            print(f"    Complexity: {task_analysis.complexity.name}")
            print(f"    Estimated Steps: {task_analysis.estimated_steps}")
            
            # Step 2: Tool Discovery
            print("  Step 2/5: Tool Discovery...")
            step_start = time.perf_counter()
            discovered_servers = await self.tool_discovery.discover_available_servers()
            component_times["tool_discovery"] = (time.perf_counter() - step_start) * 1000
            steps_completed += 1
            
            print(f"    Discovered {len(discovered_servers)} servers")
            
            # Step 3: Server Selection
            print("  Step 3/5: Server Selection...")
            step_start = time.perf_counter()
            relevant_servers = self.tool_discovery.get_best_servers_for_task(
                workflow['description'], max_servers=3
            )
            component_times["server_selection"] = (time.perf_counter() - step_start) * 1000
            steps_completed += 1
            
            print(f"    Selected {len(relevant_servers)} relevant servers")
            
            # Step 4: Decision Making
            print("  Step 4/5: Decision Analysis...")
            step_start = time.perf_counter()
            
            # Create mock server profiles for decision engine
            mock_server_profiles = []
            for server_info in relevant_servers:
                mock_profile = type('MockProfile', (), {
                    'name': server_info.name,
                    'capabilities': []
                })()
                mock_server_profiles.append(mock_profile)
            
            task_analysis_result, strategy_recommendation = self.decision_engine.analyze_and_recommend(
                workflow['description'], mock_server_profiles
            )
            component_times["decision_analysis"] = (time.perf_counter() - step_start) * 1000
            steps_completed += 1
            
            print(f"    Recommended Pattern: {strategy_recommendation.pattern.value}")
            print(f"    Confidence: {strategy_recommendation.confidence:.2f}")
            
            # Step 5: Integration Validation
            print("  Step 5/5: Integration Validation...")
            step_start = time.perf_counter()
            
            # Validate consistency between components
            assert task_analysis.complexity.name in ['SIMPLE', 'MODERATE', 'COMPLEX', 'ADVANCED', 'EXPERT']
            assert len(discovered_servers) > 0
            assert strategy_recommendation.confidence > 0
            
            component_times["integration_validation"] = (time.perf_counter() - step_start) * 1000
            steps_completed += 1
            
            total_time = (time.perf_counter() - start_time) * 1000
            
            result = IntegrationTestResult(
                workflow_name=workflow['name'],
                success=True,
                total_time_ms=total_time,
                component_times=component_times,
                steps_completed=steps_completed
            )
            
            print(f"  SUCCESS: Completed in {total_time:.2f}ms")
            return result
            
        except Exception as e:
            total_time = (time.perf_counter() - start_time) * 1000
            
            result = IntegrationTestResult(
                workflow_name=workflow['name'],
                success=False,
                total_time_ms=total_time,
                component_times=component_times,
                error_message=str(e),
                steps_completed=steps_completed
            )
            
            print(f"  FAILED: {str(e)}")
            return result
    
    async def run_integration_tests(self):
        """Run all integration tests."""
        
        print("=" * 60)
        print("MCP-Agent Optimized Components Integration Testing")
        print("=" * 60)
        print(f"Using Optimized Components: {USING_OPTIMIZED}")
        print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Test Workflows: {len(self.workflow_tests)}")
        
        # Run all tests
        all_results = []
        successful = 0
        
        for i, workflow in enumerate(self.workflow_tests, 1):
            print(f"\nRunning Test {i}/{len(self.workflow_tests)}")
            result = await self.test_workflow_integration(workflow)
            all_results.append(result)
            
            if result.success:
                successful += 1
        
        # Print summary
        print("\n" + "=" * 60)
        print("INTEGRATION TEST RESULTS")
        print("=" * 60)
        
        total_tests = len(all_results)
        success_rate = (successful / total_tests) * 100
        
        print(f"Total Tests: {total_tests}")
        print(f"Successful: {successful}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if successful > 0:
            successful_results = [r for r in all_results if r.success]
            avg_time = statistics.mean([r.total_time_ms for r in successful_results])
            min_time = min([r.total_time_ms for r in successful_results])
            max_time = max([r.total_time_ms for r in successful_results])
            
            print(f"Average Time: {avg_time:.2f}ms")
            print(f"Fastest: {min_time:.2f}ms")
            print(f"Slowest: {max_time:.2f}ms")
        
        print("\nDetailed Results:")
        for result in all_results:
            status = "PASS" if result.success else "FAIL"
            print(f"  {status}: {result.workflow_name} ({result.total_time_ms:.2f}ms)")
            if not result.success:
                print(f"    Error: {result.error_message}")
        
        # Assessment
        print("\n" + "=" * 40)
        print("ASSESSMENT")
        print("=" * 40)
        
        if success_rate == 100:
            print("EXCELLENT: All integration tests passed!")
            if successful > 0:
                avg_time = statistics.mean([r.total_time_ms for r in successful_results])
                if avg_time < 100:
                    print("PERFORMANCE: Excellent response times (<100ms)")
                elif avg_time < 500:
                    print("PERFORMANCE: Good response times (<500ms)")
        elif success_rate >= 80:
            print("GOOD: Most integration tests passed")
        else:
            print("NEEDS ATTENTION: Some integration issues detected")
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"integration_test_results_{timestamp}.json"
        
        data = {
            "timestamp": datetime.now().isoformat(),
            "using_optimized_components": USING_OPTIMIZED,
            "total_tests": total_tests,
            "successful_tests": successful,
            "success_rate": success_rate,
            "results": [
                {
                    "workflow_name": r.workflow_name,
                    "success": r.success,
                    "total_time_ms": r.total_time_ms,
                    "component_times": r.component_times,
                    "error_message": r.error_message,
                    "steps_completed": r.steps_completed
                }
                for r in all_results
            ]
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"\nResults saved to: {filename}")
        
        return success_rate == 100


async def main():
    """Main testing function."""
    
    try:
        test_suite = IntegrationTestSuite()
        success = await test_suite.run_integration_tests()
        
        if success:
            print("\nALL INTEGRATION TESTS PASSED!")
            return True
        else:
            print("\nSOME INTEGRATION TESTS FAILED!")
            return False
            
    except Exception as e:
        print(f"Integration testing failed: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
