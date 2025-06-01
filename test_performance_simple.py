"""
Simplified Performance Test for MCP-Agent Components

This script provides basic performance measurements for TaskAnalyzer
to establish baseline metrics for optimization.
"""

import time
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
        'execution_time_us': execution_time * 1000000,
        'success': success,
        'error': error,
        'result': result
    }

def test_task_analyzer_performance():
    """Test TaskAnalyzer performance"""
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
            "Quick text search and replacement",
            "Build a machine learning model for classification",
            "Orchestrate complex data processing pipeline",
            "Develop comprehensive testing framework",
            "Create automated deployment workflow",
            "Design microservices architecture"
        ]
        
        results = []
        
        print(f"Running {len(test_tasks)} test tasks...")
        
        for i, task in enumerate(test_tasks, 1):
            print(f"  Task {i}: {task[:50]}..." if len(task) > 50 else f"  Task {i}: {task}")
            
            # Test main analyze_task method (this is the most important one)
            result = time_function(analyzer.analyze_task, task)
            result['task'] = task
            result['method'] = 'analyze_task'
            results.append(result)
            
            if result['success']:
                # Test individual component methods for detailed analysis
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
                
                # Test step estimation
                complexity = analyzer._assess_complexity(task)
                result_steps = time_function(analyzer._estimate_steps, task, complexity)
                result_steps['task'] = task
                result_steps['method'] = '_estimate_steps'
                results.append(result_steps)
        
        return analyze_results('TaskAnalyzer', results)
        
    except ImportError as e:
        print(f"Could not import TaskAnalyzer: {e}")
        return None

def test_decision_engine_performance():
    """Test DecisionEngine performance (simplified)"""
    print("\nTesting DecisionEngine Performance...")
    
    try:
        from src.mcp_agent.autonomous.decision_engine import TaskAnalyzer as DecisionTaskAnalyzer
        
        analyzer = DecisionTaskAnalyzer()
        test_tasks = [
            "Simple file operation",
            "Complex workflow orchestration with multiple agents",
            "Data analysis task requiring statistical processing", 
            "Web automation with form filling and scraping",
            "Code development with git integration and testing",
            "Multi-step data processing pipeline",
            "Comprehensive report generation",
            "Automated testing and deployment"
        ]
        
        results = []
        
        for i, task in enumerate(test_tasks, 1):
            print(f"  Task {i}: {task[:50]}..." if len(task) > 50 else f"  Task {i}: {task}")
            
            # Test task analysis
            result = time_function(analyzer.analyze_task, task)
            result['task'] = task
            result['method'] = 'analyze_task'
            results.append(result)
            
            if result['success']:
                # Test component methods
                result_complexity = time_function(analyzer._assess_complexity, task)
                result_complexity['task'] = task
                result_complexity['method'] = '_assess_complexity'
                results.append(result_complexity)
                
                result_capabilities = time_function(analyzer._identify_capabilities, task)
                result_capabilities['task'] = task
                result_capabilities['method'] = '_identify_capabilities'
                results.append(result_capabilities)
        
        return analyze_results('DecisionEngine', results)
        
    except ImportError as e:
        print(f"Could not import DecisionEngine components: {e}")
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
    
    # Identify slowest operations
    slowest_operations = sorted(successful_results, key=lambda x: x['execution_time_ms'], reverse=True)[:3]
    
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
        'slowest_operations': slowest_operations,
        'detailed_results': results
    }
    
    return analysis

def print_performance_summary(results: Dict[str, Dict[str, Any]]):
    """Print performance summary"""
    print("\n" + "=" * 80)
    print("MCP-AGENT PERFORMANCE BASELINE SUMMARY")
    print("=" * 80)
    print(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Target: <500ms response time for autonomous operations")
    print()
    
    total_successful = 0
    total_tests = 0
    
    for component_name, result in results.items():
        if result is None:
            print(f"{component_name}: IMPORT ERROR - Component not available")
            continue
            
        total_tests += result['total_tests']
        total_successful += result['successful_tests']
            
        print(f"{component_name.upper()}:")
        print(f"  Tests Run: {result['successful_tests']}/{result['total_tests']}")
        
        # Show timing with appropriate precision
        if result['avg_time_ms'] < 1:
            print(f"  Average Time: {result['avg_time_us']:.0f}us ({result['avg_time_ms']:.3f}ms)")
        else:
            print(f"  Average Time: {result['avg_time_ms']:.2f}ms")
            
        print(f"  Min/Max Time: {result['min_time_ms']:.3f}ms / {result['max_time_ms']:.3f}ms")
        print(f"  Standard Deviation: {result['std_time_ms']:.3f}ms")
        print(f"  <500ms Compliance: {result['target_compliance']:.1f}%")
        print(f"  Methods Tested: {len(result['methods_tested'])} ({', '.join(result['methods_tested'])})")
        
        # Performance assessment
        if result['avg_time_ms'] > 500:
            print(f"  STATUS: [HIGH PRIORITY] Optimization needed ({result['avg_time_ms']:.0f}ms)")
        elif result['avg_time_ms'] > 100:
            print(f"  STATUS: [MEDIUM PRIORITY] Optimization recommended ({result['avg_time_ms']:.0f}ms)")
        elif result['avg_time_ms'] > 10:
            print(f"  STATUS: [LOW PRIORITY] Minor optimization opportunity ({result['avg_time_ms']:.1f}ms)")
        else:
            print(f"  STATUS: [EXCELLENT] Performance within target ({result['avg_time_ms']:.1f}ms)")
            
        if result['error_rate'] > 0:
            print(f"  WARNING: Error Rate: {result['error_rate']:.1f}%")
        
        # Show slowest operations
        if result['slowest_operations']:
            print(f"  Slowest Operations:")
            for i, op in enumerate(result['slowest_operations'], 1):
                print(f"    {i}. {op['method']}: {op['execution_time_ms']:.3f}ms")
                
        print()
    
    # Overall summary
    overall_success_rate = (total_successful / total_tests) * 100 if total_tests > 0 else 0
    print(f"OVERALL SUCCESS RATE: {overall_success_rate:.1f}% ({total_successful}/{total_tests} tests)")
    print()
    
    # Optimization recommendations
    print("OPTIMIZATION RECOMMENDATIONS:")
    print("-" * 40)
    
    recommendations = []
    
    for component_name, result in results.items():
        if result is None:
            continue
            
        # Check for specific optimization opportunities
        if result['avg_time_ms'] > 1:
            recommendations.append(f"- {component_name}: Consider caching for methods averaging {result['avg_time_ms']:.1f}ms")
        
        if 'analyze' in ' '.join(result['methods_tested']).lower():
            recommendations.append(f"- {component_name}: LRU caching recommended for analysis methods")
        
        if result['std_time_ms'] > result['avg_time_ms'] * 0.5:
            recommendations.append(f"- {component_name}: High variance ({result['std_time_ms']:.2f}ms) suggests optimization opportunities")
        
        # Method-specific recommendations
        analyze_methods = [m for m in result['methods_tested'] if 'analyze' in m.lower()]
        if analyze_methods:
            recommendations.append(f"- {component_name}: Cache results for: {', '.join(analyze_methods)}")
    
    if recommendations:
        for rec in recommendations:
            print(rec)
    else:
        print("- All components are performing optimally")
    
    print()
    print("NEXT STEPS FOR OPTIMIZATION:")
    print("-" * 40)
    print("1. Implement LRU caching for TaskAnalyzer.analyze_task()")
    print("2. Add method-level caching for pattern matching operations")
    print("3. Implement parallel processing for ToolDiscovery operations")
    print("4. Add decision result caching with TTL expiration")
    print("5. Create performance monitoring and alerting")
    
    print("\n" + "=" * 80)

def save_baseline_results(results: Dict[str, Dict[str, Any]]):
    """Save baseline results for future comparison"""
    filename = f"performance_baseline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    # Clean results for JSON serialization
    clean_results = {}
    for component, result in results.items():
        if result is not None:
            clean_result = result.copy()
            # Remove detailed results to keep file manageable
            if 'detailed_results' in clean_result:
                del clean_result['detailed_results']
            if 'slowest_operations' in clean_result:
                # Keep only the timing info, not the full result objects
                clean_result['slowest_operations'] = [
                    {'method': op['method'], 'execution_time_ms': op['execution_time_ms']}
                    for op in clean_result['slowest_operations']
                ]
            clean_results[component] = clean_result
    
    baseline_data = {
        'timestamp': datetime.now().isoformat(),
        'target_time_ms': 500,
        'test_description': 'Baseline performance measurement for MCP-Agent autonomous components',
        'results': clean_results
    }
    
    with open(filename, 'w') as f:
        json.dump(baseline_data, f, indent=2)
    
    print(f"Baseline results saved to: {filename}")
    return filename

def main():
    """Run simplified performance baseline test"""
    print("MCP-Agent Performance Baseline Test (Simplified)")
    print("=" * 60)
    print("Testing core autonomous components for optimization opportunities...")
    print()
    
    results = {}
    
    # Test components
    results['TaskAnalyzer'] = test_task_analyzer_performance()
    results['DecisionEngine'] = test_decision_engine_performance()
    
    # Print summary
    print_performance_summary(results)
    
    # Save baseline
    baseline_file = save_baseline_results(results)
    
    print(f"\nBaseline test complete! Results saved to {baseline_file}")
    print("This baseline will be used to measure optimization improvements.")
    
    return results

if __name__ == "__main__":
    main()
