"""
Quick Performance Test for MCP-Agent Components

This script provides a simplified performance test that can be run immediately
to establish baseline metrics for optimization targets.
"""

import time
import asyncio
import statistics
import json
from datetime import datetime
from typing import Dict, List, Any
import sys
import os

# Add the project path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(project_root, 'src'))

def time_function(func, *args, **kwargs):
    """Time a function execution"""
    start_time = time.perf_counter()
    try:
        if asyncio.iscoroutinefunction(func):
            result = asyncio.run(func(*args, **kwargs))
        else:
            result = func(*args, **kwargs)
        success = True
        error = ""
    except Exception as e:
        result = None
        success = False
        error = str(e)
    
    end_time = time.perf_counter()
    execution_time = end_time - start_time
    
    return {
        'execution_time': execution_time,
        'execution_time_ms': execution_time * 1000,
        'success': success,
        'error': error,
        'result': result
    }

def test_task_analyzer_performance():
    """Test TaskAnalyzer performance with direct imports"""
    print("Testing TaskAnalyzer Performance...")
    
    try:
        from src.mcp_agent.autonomous.task_analyzer import TaskAnalyzer
        
        analyzer = TaskAnalyzer()
        test_tasks = [
            "Find information about Python programming",
            "Create a simple web scraper",
            "Analyze data from CSV file",
            "Simple file read operation",
            "Search GitHub repositories",
            "Write REST API code",
            "Plan multi-step workflow",
            "Get weather information",
            "Database query optimization",
            "Quick text search"
        ]
        
        results = []
        print(f"Running {len(test_tasks)} test tasks...")
        
        for i, task in enumerate(test_tasks, 1):
            print(f"  Task {i}: {task[:30]}..." if len(task) > 30 else f"  Task {i}: {task}")
            
            # Test main analyze_task method
            result = time_function(analyzer.analyze_task, task)
            result['task'] = task
            result['method'] = 'analyze_task'
            results.append(result)
            
            if result['success']:
                # Test component methods
                result_detect = time_function(analyzer._detect_task_type, task)
                result_detect['task'] = task
                result_detect['method'] = '_detect_task_type'
                results.append(result_detect)
                
                result_complexity = time_function(analyzer._assess_complexity, task)
                result_complexity['task'] = task  
                result_complexity['method'] = '_assess_complexity'
                results.append(result_complexity)
        
        return analyze_results('TaskAnalyzer', results)
        
    except ImportError as e:
        print(f"Could not import TaskAnalyzer: {e}")
        return None

def test_tool_discovery_performance():
    """Test ToolDiscovery performance"""
    print("\nTesting ToolDiscovery Performance...")
    
    try:
        from src.mcp_agent.autonomous.tool_discovery import ToolDiscoveryAgent
        
        # Mock connection manager
        class MockConnectionManager:
            async def list_connected_servers(self):
                return []
            async def list_tools(self, server_name):
                return []
            async def list_resources(self, server_name):
                return []
        
        discovery = ToolDiscoveryAgent(MockConnectionManager())
        results = []
        
        # Test registry discovery (doesn't need real connections)
        print("  Testing registry discovery...")
        result = time_function(discovery._discover_from_registries)
        result['method'] = '_discover_from_registries'
        results.append(result)
        
        # Test capability analysis
        print("  Testing capability analysis...")
        mock_tools = [
            type('Tool', (), {'name': 'file_read'})(),
            type('Tool', (), {'name': 'web_search'})(),
            type('Tool', (), {'name': 'database_query'})(),
        ]
        
        result = time_function(discovery._analyze_server_capabilities, mock_tools, [])
        result['method'] = '_analyze_server_capabilities'
        results.append(result)
        
        # Test build capability map
        print("  Testing capability map building...")
        result = time_function(discovery._build_capability_map)
        result['method'] = '_build_capability_map'
        results.append(result)
        
        return analyze_results('ToolDiscovery', results)
        
    except ImportError as e:
        print(f"Could not import ToolDiscovery: {e}")
        return None

def test_decision_engine_performance():
    """Test DecisionEngine performance"""
    print("\nTesting DecisionEngine Performance...")
    
    try:
        from src.mcp_agent.autonomous.decision_engine import AutonomousDecisionEngine
        
        engine = AutonomousDecisionEngine()
        test_tasks = [
            "Simple file operation",
            "Complex workflow orchestration",
            "Data analysis task",
            "Web automation",
            "Code development"
        ]
        
        results = []
        
        for task in test_tasks:
            print(f"  Testing: {task}")
            
            # Test task analysis
            result = time_function(engine.task_analyzer.analyze_task, task)
            result['task'] = task
            result['method'] = 'task_analyzer.analyze_task'
            results.append(result)
        
        return analyze_results('DecisionEngine', results)
        
    except ImportError as e:
        print(f"Could not import DecisionEngine: {e}")
        return None

def analyze_results(component_name: str, results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze performance results"""
    successful_results = [r for r in results if r['success']]
    failed_results = [r for r in results if not r['success']]
    
    if not successful_results:
        return {
            'component': component_name,
            'total_tests': len(results),
            'successful_tests': 0,
            'failed_tests': len(failed_results),
            'error_rate': 100.0,
            'avg_time_ms': 0,
            'min_time_ms': 0,
            'max_time_ms': 0,
            'std_time_ms': 0,
            'target_compliance': 0.0
        }
    
    execution_times_ms = [r['execution_time_ms'] for r in successful_results]
    
    # Calculate target compliance (<500ms)
    fast_results = [r for r in successful_results if r['execution_time_ms'] < 500]
    target_compliance = (len(fast_results) / len(successful_results)) * 100
    
    analysis = {
        'component': component_name,
        'total_tests': len(results),
        'successful_tests': len(successful_results),
        'failed_tests': len(failed_results),
        'error_rate': (len(failed_results) / len(results)) * 100,
        'avg_time_ms': statistics.mean(execution_times_ms),
        'min_time_ms': min(execution_times_ms),
        'max_time_ms': max(execution_times_ms),
        'std_time_ms': statistics.stdev(execution_times_ms) if len(execution_times_ms) > 1 else 0,
        'target_compliance': target_compliance,
        'detailed_results': results
    }
    
    return analysis

def print_performance_summary(results: Dict[str, Dict[str, Any]]):
    """Print performance summary"""
    print("\n" + "=" * 80)
    print("MCP-AGENT PERFORMANCE BASELINE SUMMARY")
    print("=" * 80)
    print(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Target: <500ms response time")
    print()
    
    for component_name, result in results.items():
        if result is None:
            print(f"{component_name}: IMPORT ERROR - Component not available")
            continue
            
        print(f"{component_name.upper()}:")
        print(f"  Tests Run: {result['successful_tests']}/{result['total_tests']}")
        print(f"  Average Time: {result['avg_time_ms']:.1f}ms")
        print(f"  Min/Max Time: {result['min_time_ms']:.1f}ms / {result['max_time_ms']:.1f}ms")
        print(f"  <500ms Compliance: {result['target_compliance']:.1f}%")
        
        if result['avg_time_ms'] > 500:
            print(f"  🔴 OPTIMIZATION NEEDED (Average: {result['avg_time_ms']:.0f}ms)")
        elif result['avg_time_ms'] > 100:
            print(f"  🟡 OPTIMIZATION RECOMMENDED (Average: {result['avg_time_ms']:.0f}ms)")
        else:
            print(f"  🟢 PERFORMANCE GOOD (Average: {result['avg_time_ms']:.0f}ms)")
            
        if result['error_rate'] > 0:
            print(f"  ⚠️  Error Rate: {result['error_rate']:.1f}%")
            
        print()
    
    # Overall recommendations
    print("OPTIMIZATION PRIORITIES:")
    print("-" * 40)
    
    priorities = []
    for component_name, result in results.items():
        if result is None:
            continue
            
        if result['avg_time_ms'] > 500:
            priorities.append((component_name, result['avg_time_ms'], 'HIGH'))
        elif result['avg_time_ms'] > 100:
            priorities.append((component_name, result['avg_time_ms'], 'MEDIUM'))
    
    priorities.sort(key=lambda x: x[1], reverse=True)
    
    for component, avg_time, priority in priorities:
        print(f"{priority} PRIORITY: {component} ({avg_time:.0f}ms average)")
    
    if not priorities:
        print("All components performing within acceptable ranges!")
    
    print("\n" + "=" * 80)

def save_baseline_results(results: Dict[str, Dict[str, Any]]):
    """Save baseline results for future comparison"""
    filename = f"performance_baseline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    # Clean results for JSON serialization
    clean_results = {}
    for component, result in results.items():
        if result is not None:
            clean_result = result.copy()
            # Remove detailed results for cleaner baseline file
            if 'detailed_results' in clean_result:
                del clean_result['detailed_results']
            clean_results[component] = clean_result
    
    with open(filename, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'target_time_ms': 500,
            'results': clean_results
        }, f, indent=2)
    
    print(f"Baseline results saved to: {filename}")

def main():
    """Run quick performance baseline test"""
    print("MCP-Agent Performance Baseline Test")
    print("=" * 50)
    print("Testing core autonomous components for optimization opportunities...")
    print()
    
    results = {}
    
    # Test each component
    results['TaskAnalyzer'] = test_task_analyzer_performance()
    results['ToolDiscovery'] = test_tool_discovery_performance() 
    results['DecisionEngine'] = test_decision_engine_performance()
    
    # Print summary
    print_performance_summary(results)
    
    # Save baseline
    save_baseline_results(results)
    
    return results

if __name__ == "__main__":
    main()
