"""
Quick Performance Test for MCP-Agent Components (Fixed)

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
    """Time a function execution with high precision"""
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
        'execution_time_us': execution_time * 1000000,  # microseconds for precision
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
            "Create a simple web scraper for news articles",
            "Analyze data from CSV file and generate insights",
            "Simple file read operation",
            "Search GitHub repositories for machine learning",
            "Write REST API code with authentication",
            "Plan multi-step workflow automation",
            "Get weather information for travel planning",
            "Database query optimization for performance",
            "Quick text search and replacement"
        ]
        
        results = []
        print(f"Running {len(test_tasks)} test tasks...")
        
        for i, task in enumerate(test_tasks, 1):
            print(f"  Task {i}: {task[:40]}..." if len(task) > 40 else f"  Task {i}: {task}")
            
            # Test main analyze_task method
            result = time_function(analyzer.analyze_task, task)
            result['task'] = task
            result['method'] = 'analyze_task'
            results.append(result)
            
            if result['success']:
                # Test component methods for detailed analysis
                result_detect = time_function(analyzer._detect_task_type, task)
                result_detect['task'] = task
                result_detect['method'] = '_detect_task_type'
                results.append(result_detect)
                
                result_complexity = time_function(analyzer._assess_complexity, task)
                result_complexity['task'] = task  
                result_complexity['method'] = '_assess_complexity'
                results.append(result_complexity)
                
                # Test requirement extraction
                task_type = analyzer._detect_task_type(task)
                result_req = time_function(analyzer._extract_requirements, task, task_type)
                result_req['task'] = task
                result_req['method'] = '_extract_requirements'
                results.append(result_req)
        
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
        
        # Test capability analysis with various tool sets
        print("  Testing capability analysis...")
        tool_sets = [
            [type('Tool', (), {'name': 'file_read'})(), type('Tool', (), {'name': 'file_write'})()],
            [type('Tool', (), {'name': 'web_search'})(), type('Tool', (), {'name': 'web_fetch'})()],
            [type('Tool', (), {'name': 'database_query'})(), type('Tool', (), {'name': 'sql_execute'})()],
            [type('Tool', (), {'name': 'git_commit'})(), type('Tool', (), {'name': 'github_create_pr'})()],
        ]
        
        for tools in tool_sets:
            result = time_function(discovery._analyze_server_capabilities, tools, [])
            result['method'] = '_analyze_server_capabilities'
            results.append(result)
        
        # Test build capability map
        print("  Testing capability map building...")
        result = time_function(discovery._build_capability_map)
        result['method'] = '_build_capability_map'
        results.append(result)
        
        # Test server recommendations
        # Populate servers first with sync call
        asyncio.run(discovery._discover_from_registries())
        test_tasks = ["file operations", "web scraping", "database work"]
        
        for task in test_tasks:
            result = time_function(discovery.get_best_servers_for_task, task)
            result['method'] = 'get_best_servers_for_task'
            result['task'] = task
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
            "Complex workflow orchestration with multiple agents",
            "Data analysis task requiring statistical processing",
            "Web automation with form filling and scraping",
            "Code development with git integration and testing"
        ]
        
        results = []
        
        for task in test_tasks:
            print(f"  Testing: {task[:50]}..." if len(task) > 50 else f"  Testing: {task}")
            
            # Test task analysis
            result = time_function(engine.task_analyzer.analyze_task, task)
            result['task'] = task
            result['method'] = 'task_analyzer.analyze_task'
            results.append(result)
            
            # Test strategy selection with mock servers
            if result['success']:
                try:
                    task_analysis = result['result']
                    result_strategy = time_function(engine.strategy_selector.select_strategy, task_analysis, [])
                    result_strategy['task'] = task
                    result_strategy['method'] = 'strategy_selector.select_strategy'
                    results.append(result_strategy)
                except Exception as e:
                    # Strategy selection might fail without proper server profiles
                    pass
        
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
            'avg_time_us': 0,
            'min_time_ms': 0,
            'max_time_ms': 0,
            'std_time_ms': 0,
            'target_compliance': 0.0,
            'methods_tested': []
        }
    
    execution_times_ms = [r['execution_time_ms'] for r in successful_results]
    execution_times_us = [r['execution_time_us'] for r in successful_results]
    
    # Calculate target compliance (<500ms)
    fast_results = [r for r in successful_results if r['execution_time_ms'] < 500]
    target_compliance = (len(fast_results) / len(successful_results)) * 100
    
    # Get unique methods tested
    methods_tested = list(set(r['method'] for r in results))
    
    analysis = {
        'component': component_name,
        'total_tests': len(results),
        'successful_tests': len(successful_results),
        'failed_tests': len(failed_results),
        'error_rate': (len(failed_results) / len(results)) * 100,
        'avg_time_ms': statistics.mean(execution_times_ms),
        'avg_time_us': statistics.mean(execution_times_us),
        'min_time_ms': min(execution_times_ms),
        'max_time_ms': max(execution_times_ms),
        'std_time_ms': statistics.stdev(execution_times_ms) if len(execution_times_ms) > 1 else 0,
        'target_compliance': target_compliance,
        'methods_tested': methods_tested,
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
        
        # Show both ms and microseconds for precision
        if result['avg_time_ms'] < 1:
            print(f"  Average Time: {result['avg_time_us']:.1f}μs ({result['avg_time_ms']:.3f}ms)")
        else:
            print(f"  Average Time: {result['avg_time_ms']:.1f}ms")
            
        print(f"  Min/Max Time: {result['min_time_ms']:.3f}ms / {result['max_time_ms']:.3f}ms")
        print(f"  <500ms Compliance: {result['target_compliance']:.1f}%")
        print(f"  Methods Tested: {', '.join(result['methods_tested'])}")
        
        if result['avg_time_ms'] > 500:
            print(f"  [HIGH PRIORITY] OPTIMIZATION NEEDED (Average: {result['avg_time_ms']:.0f}ms)")
        elif result['avg_time_ms'] > 100:
            print(f"  [MEDIUM PRIORITY] OPTIMIZATION RECOMMENDED (Average: {result['avg_time_ms']:.0f}ms)")
        else:
            print(f"  [GOOD] PERFORMANCE ACCEPTABLE (Average: {result['avg_time_ms']:.1f}ms)")
            
        if result['error_rate'] > 0:
            print(f"  [WARNING] Error Rate: {result['error_rate']:.1f}%")
            
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
        elif result['avg_time_ms'] > 10:
            priorities.append((component_name, result['avg_time_ms'], 'LOW'))
    
    priorities.sort(key=lambda x: x[1], reverse=True)
    
    for component, avg_time, priority in priorities:
        print(f"{priority} PRIORITY: {component} ({avg_time:.1f}ms average)")
    
    if not priorities:
        print("All components performing within excellent ranges!")
    
    # Specific optimization recommendations
    print("\nOPTIMIZATION RECOMMENDATIONS:")
    print("-" * 40)
    
    recommendations = []
    
    for component_name, result in results.items():
        if result is None:
            continue
            
        # Check for caching opportunities
        if 'analyze' in ' '.join(result['methods_tested']).lower():
            recommendations.append(f"- {component_name}: Consider LRU caching for analysis methods")
        
        # Check for parallel processing opportunities
        if component_name == 'ToolDiscovery':
            recommendations.append(f"- {component_name}: Implement parallel server discovery and analysis")
        
        # Check for high variance (optimization opportunity)
        if result['std_time_ms'] > result['avg_time_ms'] * 0.5:
            recommendations.append(f"- {component_name}: High variance detected, investigate inconsistent performance")
    
    for rec in recommendations:
        print(rec)
    
    if not recommendations:
        print("- Performance is consistent across all components")
    
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

async def main():
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
    asyncio.run(main())
