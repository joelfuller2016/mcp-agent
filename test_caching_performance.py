"""
Performance Comparison Test for Cached TaskAnalyzer

This script compares the performance of the original TaskAnalyzer
with the new CachedTaskAnalyzer to validate optimization improvements.
"""

import time
import statistics
import sys
import os
from typing import List, Dict, Any
from datetime import datetime

# Add the project path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(project_root, 'src'))

def time_multiple_calls(analyzer, tasks: List[str], iterations: int = 3) -> Dict[str, Any]:
    """Test analyzer performance with multiple calls to the same tasks."""
    all_times = []
    results = []
    
    # Run multiple iterations
    for iteration in range(iterations):
        iteration_times = []
        
        for task in tasks:
            start_time = time.perf_counter()
            try:
                result = analyzer.analyze_task(task)
                success = True
                cache_hit = getattr(result, 'cache_hit', False)
            except Exception as e:
                success = False
                cache_hit = False
                result = None
                
            end_time = time.perf_counter()
            execution_time = (end_time - start_time) * 1000  # ms
            
            iteration_times.append(execution_time)
            results.append({
                'iteration': iteration + 1,
                'task': task,
                'time_ms': execution_time,
                'success': success,
                'cache_hit': cache_hit
            })
            
        all_times.extend(iteration_times)
    
    return {
        'all_times_ms': all_times,
        'avg_time_ms': statistics.mean(all_times),
        'min_time_ms': min(all_times),
        'max_time_ms': max(all_times),
        'std_time_ms': statistics.stdev(all_times) if len(all_times) > 1 else 0,
        'total_calls': len(all_times),
        'detailed_results': results
    }

def test_original_analyzer():
    """Test the original TaskAnalyzer performance."""
    print("Testing Original TaskAnalyzer...")
    
    try:
        from src.mcp_agent.autonomous.task_analyzer import TaskAnalyzer as OriginalTaskAnalyzer
        
        analyzer = OriginalTaskAnalyzer()
        
        test_tasks = [
            "Find information about Python programming",
            "Create a simple web scraper for news",
            "Analyze data from CSV file",
            "Simple file read operation",
            "Search GitHub repositories",
        ]
        
        return time_multiple_calls(analyzer, test_tasks, iterations=3)
        
    except ImportError as e:
        print(f"Could not import original TaskAnalyzer: {e}")
        return None

def test_cached_analyzer():
    """Test the cached TaskAnalyzer performance."""
    print("Testing Cached TaskAnalyzer...")
    
    try:
        from src.mcp_agent.autonomous.task_analyzer_cached import CachedTaskAnalyzer
        
        # Create analyzer with cache statistics enabled
        analyzer = CachedTaskAnalyzer(
            cache_config={
                'analyze_task': 64,
                'detect_task_type': 32,
                'assess_complexity': 32,
                'extract_requirements': 16,
                'estimate_steps': 16
            },
            enable_cache_stats=True
        )
        
        test_tasks = [
            "Find information about Python programming",
            "Create a simple web scraper for news",
            "Analyze data from CSV file", 
            "Simple file read operation",
            "Search GitHub repositories",
        ]
        
        result = time_multiple_calls(analyzer, test_tasks, iterations=3)
        
        # Add cache statistics
        result['cache_stats'] = analyzer.get_cache_statistics()
        result['cache_info'] = analyzer.get_cache_info()
        
        return result
        
    except ImportError as e:
        print(f"Could not import cached TaskAnalyzer: {e}")
        return None

def test_cache_effectiveness():
    """Test cache effectiveness with repeated similar tasks."""
    print("\nTesting Cache Effectiveness with Similar Tasks...")
    
    try:
        from src.mcp_agent.autonomous.task_analyzer_cached import CachedTaskAnalyzer
        
        analyzer = CachedTaskAnalyzer(enable_cache_stats=True)
        
        # Test with very similar tasks that should benefit from caching
        similar_tasks = [
            "create a file",
            "create a new file", 
            "create file",
            "create a simple file",
            "file creation",
            "create a text file",
            "create a file on disk"
        ]
        
        times = []
        cache_hits = []
        
        print("  Analyzing similar tasks...")
        for i, task in enumerate(similar_tasks):
            start_time = time.perf_counter()
            result = analyzer.analyze_task(task)
            end_time = time.perf_counter()
            
            execution_time = (end_time - start_time) * 1000
            cache_hit = getattr(result, 'cache_hit', False)
            
            times.append(execution_time)
            cache_hits.append(cache_hit)
            
            print(f"    Task {i+1}: {execution_time:.3f}ms {'(cached)' if cache_hit else '(computed)'}")
        
        cache_stats = analyzer.get_cache_statistics()
        
        return {
            'times_ms': times,
            'cache_hits': cache_hits,
            'cache_hit_rate': sum(cache_hits) / len(cache_hits) * 100,
            'avg_time_ms': statistics.mean(times),
            'cache_stats': cache_stats
        }
        
    except ImportError as e:
        print(f"Could not test cache effectiveness: {e}")
        return None

def compare_performance_variance():
    """Compare performance variance between original and cached versions."""
    print("\nTesting Performance Variance...")
    
    try:
        from src.mcp_agent.autonomous.task_analyzer import TaskAnalyzer as OriginalTaskAnalyzer
        from src.mcp_agent.autonomous.task_analyzer_cached import CachedTaskAnalyzer
        
        # Same task repeated many times
        task = "Create a complex data processing pipeline with multiple steps"
        
        # Test original analyzer
        print("  Testing original analyzer variance...")
        original_analyzer = OriginalTaskAnalyzer()
        original_times = []
        
        for _ in range(20):
            start_time = time.perf_counter()
            original_analyzer.analyze_task(task)
            end_time = time.perf_counter()
            original_times.append((end_time - start_time) * 1000)
        
        # Test cached analyzer
        print("  Testing cached analyzer variance...")
        cached_analyzer = CachedTaskAnalyzer(enable_cache_stats=True)
        cached_times = []
        
        for _ in range(20):
            start_time = time.perf_counter()
            cached_analyzer.analyze_task(task)
            end_time = time.perf_counter()
            cached_times.append((end_time - start_time) * 1000)
        
        return {
            'original': {
                'times_ms': original_times,
                'avg_ms': statistics.mean(original_times),
                'std_ms': statistics.stdev(original_times),
                'min_ms': min(original_times),
                'max_ms': max(original_times)
            },
            'cached': {
                'times_ms': cached_times,
                'avg_ms': statistics.mean(cached_times),
                'std_ms': statistics.stdev(cached_times),
                'min_ms': min(cached_times),
                'max_ms': max(cached_times)
            }
        }
        
    except ImportError as e:
        print(f"Could not compare variance: {e}")
        return None

def print_comparison_results(original_result, cached_result):
    """Print detailed comparison results."""
    print("\n" + "=" * 80)
    print("TASKANALYZER CACHING PERFORMANCE COMPARISON")
    print("=" * 80)
    print(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    if original_result is None or cached_result is None:
        print("Could not complete comparison - missing results")
        return
    
    # Basic performance comparison
    print("BASIC PERFORMANCE COMPARISON:")
    print("-" * 40)
    print(f"Original TaskAnalyzer:")
    print(f"  Average Time: {original_result['avg_time_ms']:.3f}ms")
    print(f"  Min/Max: {original_result['min_time_ms']:.3f}ms / {original_result['max_time_ms']:.3f}ms")
    print(f"  Standard Deviation: {original_result['std_time_ms']:.3f}ms")
    print(f"  Total Calls: {original_result['total_calls']}")
    print()
    
    print(f"Cached TaskAnalyzer:")
    print(f"  Average Time: {cached_result['avg_time_ms']:.3f}ms")
    print(f"  Min/Max: {cached_result['min_time_ms']:.3f}ms / {cached_result['max_time_ms']:.3f}ms")
    print(f"  Standard Deviation: {cached_result['std_time_ms']:.3f}ms")
    print(f"  Total Calls: {cached_result['total_calls']}")
    print()
    
    # Performance improvements
    avg_improvement = ((original_result['avg_time_ms'] - cached_result['avg_time_ms']) / original_result['avg_time_ms']) * 100
    variance_improvement = ((original_result['std_time_ms'] - cached_result['std_time_ms']) / original_result['std_time_ms']) * 100
    
    print("PERFORMANCE IMPROVEMENTS:")
    print("-" * 40)
    print(f"Average Time Improvement: {avg_improvement:+.1f}%")
    print(f"Variance Reduction: {variance_improvement:+.1f}%")
    print(f"Min Time Improvement: {((original_result['min_time_ms'] - cached_result['min_time_ms']) / original_result['min_time_ms']) * 100:+.1f}%")
    print()
    
    # Cache statistics
    if 'cache_stats' in cached_result:
        print("CACHE PERFORMANCE:")
        print("-" * 40)
        
        for method, stats in cached_result['cache_stats'].items():
            if stats.total_requests > 0:
                print(f"{method}:")
                print(f"  Hit Rate: {stats.hit_rate:.1f}%")
                print(f"  Total Requests: {stats.total_requests}")
                print(f"  Average Hit Time: {stats.avg_hit_time_ms:.3f}ms")
                print(f"  Average Miss Time: {stats.avg_miss_time_ms:.3f}ms")
        print()
    
    # Cache info
    if 'cache_info' in cached_result:
        print("CACHE UTILIZATION:")
        print("-" * 40)
        
        for method, info in cached_result['cache_info'].items():
            print(f"{method}: {info.hits} hits, {info.misses} misses, {info.currsize}/{info.maxsize} cached")
        print()
    
    print("OPTIMIZATION ASSESSMENT:")
    print("-" * 40)
    
    if avg_improvement > 0:
        print(f"✅ Average performance improved by {avg_improvement:.1f}%")
    else:
        print(f"⚠️  Average performance decreased by {abs(avg_improvement):.1f}%")
        
    if variance_improvement > 0:
        print(f"✅ Performance variance reduced by {variance_improvement:.1f}%")
    else:
        print(f"⚠️  Performance variance increased by {abs(variance_improvement):.1f}%")
    
    if cached_result.get('cache_stats'):
        total_hit_rate = sum(s.hit_rate for s in cached_result['cache_stats'].values()) / len(cached_result['cache_stats'])
        print(f"✅ Average cache hit rate: {total_hit_rate:.1f}%")
        
        if total_hit_rate > 50:
            print("✅ Cache is effectively reducing computational overhead")
        else:
            print("⚠️  Cache hit rate could be improved")

def main():
    """Run the performance comparison test."""
    print("TaskAnalyzer Caching Performance Comparison")
    print("=" * 60)
    print("Testing performance improvements from intelligent caching...")
    print()
    
    # Test basic performance
    original_result = test_original_analyzer()
    cached_result = test_cached_analyzer()
    
    # Print comparison
    print_comparison_results(original_result, cached_result)
    
    # Test cache effectiveness
    cache_effectiveness = test_cache_effectiveness()
    if cache_effectiveness:
        print("\nCACHE EFFECTIVENESS TEST:")
        print("-" * 40)
        print(f"Cache Hit Rate: {cache_effectiveness['cache_hit_rate']:.1f}%")
        print(f"Average Time: {cache_effectiveness['avg_time_ms']:.3f}ms")
        
        if cache_effectiveness['cache_hit_rate'] > 0:
            print("✅ Cache is working for similar tasks")
        else:
            print("⚠️  Cache not hitting for similar tasks")
    
    # Test variance improvement
    variance_result = compare_performance_variance()
    if variance_result:
        print("\nVARIANCE COMPARISON:")
        print("-" * 40)
        print(f"Original Std Dev: {variance_result['original']['std_ms']:.3f}ms")
        print(f"Cached Std Dev: {variance_result['cached']['std_ms']:.3f}ms")
        
        variance_improvement = ((variance_result['original']['std_ms'] - variance_result['cached']['std_ms']) / variance_result['original']['std_ms']) * 100
        print(f"Variance Improvement: {variance_improvement:+.1f}%")
        
        if variance_improvement > 0:
            print("✅ Caching significantly improves consistency")
        else:
            print("⚠️  Caching may not be improving consistency")
    
    print("\n" + "=" * 80)
    print("Caching implementation test complete!")
    
    return {
        'original': original_result,
        'cached': cached_result,
        'cache_effectiveness': cache_effectiveness,
        'variance_comparison': variance_result
    }

if __name__ == "__main__":
    main()
