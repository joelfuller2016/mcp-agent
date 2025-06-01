#!/usr/bin/env python3
"""
Performance Regression Analysis for CI/CD Pipeline

Analyzes performance test results to detect regressions and trends.
"""

import os
import json
import glob
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import statistics


class PerformanceRegressionAnalyzer:
    """Analyze performance test results for regressions."""
    
    def __init__(self, artifacts_dir: str = "performance-artifacts"):
        self.artifacts_dir = artifacts_dir
        self.regression_thresholds = {
            'response_time_increase': 20.0,  # 20% increase triggers regression
            'success_rate_decrease': 5.0,    # 5% decrease triggers regression
            'throughput_decrease': 15.0,     # 15% decrease triggers regression
            'cache_hit_rate_decrease': 10.0  # 10% decrease triggers regression
        }
        
        # Performance targets
        self.performance_targets = {
            'baseline': {
                'avg_response_time_ms': 50.0,
                'success_rate': 95.0
            },
            'load': {
                'avg_response_time_ms': 500.0,
                'success_rate': 90.0,
                'min_throughput_rps': 100.0
            },
            'integration': {
                'avg_response_time_ms': 500.0,
                'success_rate': 95.0
            }
        }
    
    def load_performance_results(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load all performance results from artifacts."""
        results = {'baseline': [], 'load': [], 'integration': []}
        
        # Search for result files in artifacts directory
        for test_type in results.keys():
            pattern = os.path.join(self.artifacts_dir, f"*{test_type}*", f"performance_{test_type}_*.json")
            files = glob.glob(pattern)
            
            for file_path in files:
                try:
                    with open(file_path, 'r') as f:
                        result = json.load(f)
                        results[test_type].append(result)
                except Exception as e:
                    print(f"Warning: Could not load {file_path}: {e}")
        
        # Sort by timestamp
        for test_type in results:
            results[test_type].sort(key=lambda x: x.get('timestamp', ''))
        
        return results
    
    def calculate_regression_metrics(self, current: Dict[str, Any], 
                                     historical: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate regression metrics comparing current to historical results."""
        
        if not historical:
            return {'has_baseline': False, 'metrics': {}}
        
        # Get recent historical data (last 10 runs or 30 days)
        recent_cutoff = datetime.now() - timedelta(days=30)
        recent_historical = []
        
        for result in historical[-10:]:  # Last 10 runs
            try:
                result_date = datetime.fromisoformat(result.get('timestamp', ''))
                if result_date >= recent_cutoff:
                    recent_historical.append(result)
            except:
                recent_historical.append(result)  # Include if timestamp parsing fails
        
        if not recent_historical:
            return {'has_baseline': False, 'metrics': {}}
        
        metrics = {'has_baseline': True, 'regressions': []}
        
        # Analyze response time regression
        if 'overall' in current and 'avg_response_time_ms' in current['overall']:
            current_time = current['overall']['avg_response_time_ms']
            historical_times = []
            
            for result in recent_historical:
                if 'overall' in result and 'avg_response_time_ms' in result['overall']:
                    historical_times.append(result['overall']['avg_response_time_ms'])
            
            if historical_times:
                baseline_time = statistics.mean(historical_times)
                time_increase = ((current_time - baseline_time) / baseline_time) * 100
                
                metrics['response_time'] = {
                    'current': current_time,
                    'baseline': baseline_time,
                    'change_percent': time_increase,
                    'regression': time_increase > self.regression_thresholds['response_time_increase']
                }
                
                if metrics['response_time']['regression']:
                    metrics['regressions'].append({
                        'type': 'response_time',
                        'message': f"Response time increased by {time_increase:.1f}% ({baseline_time:.2f}ms → {current_time:.2f}ms)",
                        'severity': 'high' if time_increase > 50 else 'medium'
                    })
        
        # Analyze success rate regression
        if 'overall' in current and 'success_rate' in current['overall']:
            current_rate = current['overall']['success_rate']
            historical_rates = []
            
            for result in recent_historical:
                if 'overall' in result and 'success_rate' in result['overall']:
                    historical_rates.append(result['overall']['success_rate'])
            
            if historical_rates:
                baseline_rate = statistics.mean(historical_rates)
                rate_decrease = baseline_rate - current_rate
                
                metrics['success_rate'] = {
                    'current': current_rate,
                    'baseline': baseline_rate,
                    'change_percent': -rate_decrease,
                    'regression': rate_decrease > self.regression_thresholds['success_rate_decrease']
                }
                
                if metrics['success_rate']['regression']:
                    metrics['regressions'].append({
                        'type': 'success_rate',
                        'message': f"Success rate decreased by {rate_decrease:.1f}% ({baseline_rate:.1f}% → {current_rate:.1f}%)",
                        'severity': 'high' if rate_decrease > 10 else 'medium'
                    })
        
        # Analyze throughput regression (for load tests)
        if (current.get('test_type') == 'load' and 'overall' in current and 
            'avg_throughput_rps' in current['overall']):
            
            current_throughput = current['overall']['avg_throughput_rps']
            historical_throughputs = []
            
            for result in recent_historical:
                if ('overall' in result and 'avg_throughput_rps' in result['overall']):
                    historical_throughputs.append(result['overall']['avg_throughput_rps'])
            
            if historical_throughputs:
                baseline_throughput = statistics.mean(historical_throughputs)
                throughput_decrease = ((baseline_throughput - current_throughput) / baseline_throughput) * 100
                
                metrics['throughput'] = {
                    'current': current_throughput,
                    'baseline': baseline_throughput,
                    'change_percent': -throughput_decrease,
                    'regression': throughput_decrease > self.regression_thresholds['throughput_decrease']
                }
                
                if metrics['throughput']['regression']:
                    metrics['regressions'].append({
                        'type': 'throughput',
                        'message': f"Throughput decreased by {throughput_decrease:.1f}% ({baseline_throughput:.1f} → {current_throughput:.1f} RPS)",
                        'severity': 'medium'
                    })
        
        return metrics
    
    def check_performance_targets(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Check if current results meet performance targets."""
        test_type = results.get('test_type', 'unknown')
        targets = self.performance_targets.get(test_type, {})
        
        target_results = {
            'targets_met': True,
            'failed_targets': [],
            'checks': {}
        }
        
        if not targets:
            return target_results
        
        # Check response time target
        if ('avg_response_time_ms' in targets and 'overall' in results and 
            'avg_response_time_ms' in results['overall']):
            
            current_time = results['overall']['avg_response_time_ms']
            target_time = targets['avg_response_time_ms']
            
            target_met = current_time <= target_time
            target_results['checks']['response_time'] = {
                'current': current_time,
                'target': target_time,
                'met': target_met
            }
            
            if not target_met:
                target_results['targets_met'] = False
                target_results['failed_targets'].append({
                    'type': 'response_time',
                    'message': f"Response time {current_time:.2f}ms exceeds target {target_time:.2f}ms",
                    'severity': 'high'
                })
        
        # Check success rate target
        if ('success_rate' in targets and 'overall' in results and 
            'success_rate' in results['overall']):
            
            current_rate = results['overall']['success_rate']
            target_rate = targets['success_rate']
            
            target_met = current_rate >= target_rate
            target_results['checks']['success_rate'] = {
                'current': current_rate,
                'target': target_rate,
                'met': target_met
            }
            
            if not target_met:
                target_results['targets_met'] = False
                target_results['failed_targets'].append({
                    'type': 'success_rate',
                    'message': f"Success rate {current_rate:.1f}% below target {target_rate:.1f}%",
                    'severity': 'high'
                })
        
        # Check throughput target (for load tests)
        if ('min_throughput_rps' in targets and 'overall' in results and 
            'avg_throughput_rps' in results['overall']):
            
            current_throughput = results['overall']['avg_throughput_rps']
            target_throughput = targets['min_throughput_rps']
            
            target_met = current_throughput >= target_throughput
            target_results['checks']['throughput'] = {
                'current': current_throughput,
                'target': target_throughput,
                'met': target_met
            }
            
            if not target_met:
                target_results['targets_met'] = False
                target_results['failed_targets'].append({
                    'type': 'throughput',
                    'message': f"Throughput {current_throughput:.1f} RPS below target {target_throughput:.1f} RPS",
                    'severity': 'medium'
                })
        
        return target_results
    
    def analyze_all_results(self) -> Dict[str, Any]:
        """Analyze all performance results for regressions."""
        all_results = self.load_performance_results()
        analysis = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': 'unknown',
            'regression_detected': False,
            'targets_met': True,
            'test_results': {}
        }
        
        for test_type, results in all_results.items():
            if not results:
                continue
            
            current_result = results[-1]  # Most recent result
            historical_results = results[:-1]  # All previous results
            
            # Calculate regression metrics
            regression_metrics = self.calculate_regression_metrics(current_result, historical_results)
            
            # Check performance targets
            target_results = self.check_performance_targets(current_result)
            
            test_analysis = {
                'test_type': test_type,
                'current_result': current_result,
                'regression_analysis': regression_metrics,
                'target_analysis': target_results,
                'has_regressions': len(regression_metrics.get('regressions', [])) > 0,
                'meets_targets': target_results['targets_met']
            }
            
            analysis['test_results'][test_type] = test_analysis
            
            # Update overall status
            if test_analysis['has_regressions']:
                analysis['regression_detected'] = True
            
            if not test_analysis['meets_targets']:
                analysis['targets_met'] = False
        
        # Determine overall status
        if analysis['regression_detected'] and not analysis['targets_met']:
            analysis['overall_status'] = 'critical'
        elif analysis['regression_detected']:
            analysis['overall_status'] = 'warning'
        elif not analysis['targets_met']:
            analysis['overall_status'] = 'failing'
        else:
            analysis['overall_status'] = 'passing'
        
        return analysis
    
    def save_analysis(self, analysis: Dict[str, Any], output_file: str = "performance_regression_analysis.json"):
        """Save regression analysis to file."""
        try:
            with open(output_file, 'w') as f:
                json.dump(analysis, f, indent=2)
            print(f"Regression analysis saved to {output_file}")
        except Exception as e:
            print(f"Failed to save analysis: {e}")
    
    def print_summary(self, analysis: Dict[str, Any]):
        """Print analysis summary."""
        print("="*60)
        print("PERFORMANCE REGRESSION ANALYSIS")
        print("="*60)
        
        print(f"Overall Status: {analysis['overall_status'].upper()}")
        print(f"Regression Detected: {'Yes' if analysis['regression_detected'] else 'No'}")
        print(f"Targets Met: {'Yes' if analysis['targets_met'] else 'No'}")
        
        for test_type, test_result in analysis['test_results'].items():
            print(f"\n{test_type.upper()} Test Analysis:")
            print("-" * 30)
            
            # Current performance
            current = test_result['current_result']
            if 'overall' in current and 'avg_response_time_ms' in current['overall']:
                print(f"Current Response Time: {current['overall']['avg_response_time_ms']:.2f}ms")
            
            if 'overall' in current and 'success_rate' in current['overall']:
                print(f"Current Success Rate: {current['overall']['success_rate']:.1f}%")
            
            # Regression analysis
            regression = test_result['regression_analysis']
            if regression.get('has_baseline'):
                print("Regression Analysis:")
                for reg in regression.get('regressions', []):
                    print(f"  - {reg['type']}: {reg['message']} [{reg['severity']}]")
                
                if not regression.get('regressions'):
                    print("  - No regressions detected")
            else:
                print("  - No baseline data for comparison")
            
            # Target analysis
            target = test_result['target_analysis']
            print("Target Compliance:")
            if target['targets_met']:
                print("  - All performance targets met")
            else:
                for failed in target['failed_targets']:
                    print(f"  - {failed['type']}: {failed['message']} [{failed['severity']}]")


def main():
    """Main function for CLI usage."""
    analyzer = PerformanceRegressionAnalyzer()
    analysis = analyzer.analyze_all_results()
    
    # Save analysis
    analyzer.save_analysis(analysis)
    
    # Print summary
    analyzer.print_summary(analysis)
    
    # Exit with appropriate code
    if analysis['overall_status'] in ['critical', 'failing']:
        print("\nPerformance issues detected!")
        exit(1)
    elif analysis['overall_status'] == 'warning':
        print("\nPerformance warnings detected!")
        exit(0)  # Warning but not failure
    else:
        print("\nAll performance checks passed!")
        exit(0)


if __name__ == "__main__":
    main()
