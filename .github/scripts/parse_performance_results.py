#!/usr/bin/env python3
"""
Performance Results Parser for CI/CD Pipeline

Parses performance test logs and extracts key metrics for regression analysis.
"""

import sys
import json
import re
from datetime import datetime
from typing import Dict, List, Any, Optional


class PerformanceResultParser:
    """Parse performance test results from log files."""
    
    def __init__(self):
        self.patterns = {
            'baseline': {
                'component_time': r'(\w+):\s*(\d+\.?\d*)us \((\d+\.?\d*)ms\)',
                'success_rate': r'OVERALL SUCCESS RATE: (\d+\.?\d*)%',
                'test_count': r'Tests Run: (\d+)/(\d+)',
                'status': r'STATUS: \[(\w+)\]',
                'average_time': r'Average Time: (\d+\.?\d*)us'
            },
            'load': {
                'test_result': r'(\w+_\w+_\w+)\s+(\d+)\s+(\d+\.?\d*)%\s+(\d+\.?\d*)\s+(\d+\.?\d*)\s+(\d+\.?\d*)',
                'success_rate': r'Overall Success Rate: (\d+\.?\d*)%',
                'response_range': r'Response Time Range: (\d+\.?\d*)ms - (\d+\.?\d*)ms',
                'max_throughput': r'Maximum Throughput: (\d+\.?\d*) requests/sec',
                'assessment': r'\[(\w+)\] (.*)',
                'scalability': r'Performance Degradation: (\d+\.?\d*)%'
            },
            'integration': {
                'workflow_result': r'(PASS|FAIL): ([^(]+) \((\d+\.?\d*)ms\)',
                'success_rate': r'Success Rate: (\d+\.?\d*)%',
                'test_status': r'(EXCELLENT|GOOD|FAIR|POOR): (.*)',
                'total_tests': r'Total Tests: (\d+)',
                'successful_tests': r'Successful: (\d+)'
            }
        }
    
    def parse_baseline_results(self, log_content: str) -> Dict[str, Any]:
        """Parse baseline performance test results."""
        results = {
            'test_type': 'baseline',
            'timestamp': datetime.now().isoformat(),
            'components': {},
            'overall': {},
            'status': 'unknown',
            'success': False
        }
        
        # Extract component performance
        for match in re.finditer(self.patterns['baseline']['component_time'], log_content):
            component = match.group(1)
            time_us = float(match.group(2))
            time_ms = float(match.group(3))
            
            results['components'][component] = {
                'time_us': time_us,
                'time_ms': time_ms,
                'target_met': time_ms < 500
            }
        
        # Extract overall metrics
        success_match = re.search(self.patterns['baseline']['success_rate'], log_content)
        if success_match:
            results['overall']['success_rate'] = float(success_match.group(1))
        
        test_count_match = re.search(self.patterns['baseline']['test_count'], log_content)
        if test_count_match:
            results['overall']['tests_run'] = int(test_count_match.group(1))
            results['overall']['total_tests'] = int(test_count_match.group(2))
        
        # Extract status
        status_match = re.search(self.patterns['baseline']['status'], log_content)
        if status_match:
            results['status'] = status_match.group(1).lower()
            results['success'] = results['status'] == 'excellent'
        
        # Calculate average response time
        if results['components']:
            avg_time = sum(comp['time_ms'] for comp in results['components'].values()) / len(results['components'])
            results['overall']['avg_response_time_ms'] = avg_time
            results['overall']['target_met'] = avg_time < 500
        
        return results
    
    def parse_load_results(self, log_content: str) -> Dict[str, Any]:
        """Parse load test results."""
        results = {
            'test_type': 'load',
            'timestamp': datetime.now().isoformat(),
            'tests': [],
            'overall': {},
            'status': 'unknown',
            'success': False
        }
        
        # Extract individual test results
        for match in re.finditer(self.patterns['load']['test_result'], log_content):
            test_name = match.group(1)
            users = int(match.group(2))
            success_rate = float(match.group(3))
            avg_time = float(match.group(4))
            p95_time = float(match.group(5))
            rps = float(match.group(6))
            
            results['tests'].append({
                'name': test_name,
                'concurrent_users': users,
                'success_rate': success_rate,
                'avg_response_time_ms': avg_time,
                'p95_response_time_ms': p95_time,
                'requests_per_second': rps,
                'target_met': avg_time < 500
            })
        
        # Extract overall metrics
        success_match = re.search(self.patterns['load']['success_rate'], log_content)
        if success_match:
            results['overall']['success_rate'] = float(success_match.group(1))
        
        range_match = re.search(self.patterns['load']['response_range'], log_content)
        if range_match:
            results['overall']['min_response_time_ms'] = float(range_match.group(1))
            results['overall']['max_response_time_ms'] = float(range_match.group(2))
        
        throughput_match = re.search(self.patterns['load']['max_throughput'], log_content)
        if throughput_match:
            results['overall']['max_throughput_rps'] = float(throughput_match.group(1))
        
        # Extract assessment
        assessment_match = re.search(self.patterns['load']['assessment'], log_content)
        if assessment_match:
            results['status'] = assessment_match.group(1).lower()
            results['assessment'] = assessment_match.group(2)
            results['success'] = results['status'] == 'excellent'
        
        # Extract scalability info
        scalability_match = re.search(self.patterns['load']['scalability'], log_content)
        if scalability_match:
            results['overall']['scalability_degradation_percent'] = float(scalability_match.group(1))
        
        # Calculate overall averages
        if results['tests']:
            successful_tests = [t for t in results['tests'] if t['success_rate'] > 0]
            if successful_tests:
                results['overall']['avg_response_time_ms'] = sum(t['avg_response_time_ms'] for t in successful_tests) / len(successful_tests)
                results['overall']['avg_throughput_rps'] = sum(t['requests_per_second'] for t in successful_tests) / len(successful_tests)
                results['overall']['target_met'] = all(t['target_met'] for t in successful_tests)
        
        return results
    
    def parse_integration_results(self, log_content: str) -> Dict[str, Any]:
        """Parse integration test results."""
        results = {
            'test_type': 'integration',
            'timestamp': datetime.now().isoformat(),
            'workflows': [],
            'overall': {},
            'status': 'unknown',
            'success': False
        }
        
        # Extract workflow results
        for match in re.finditer(self.patterns['integration']['workflow_result'], log_content):
            status = match.group(1)
            workflow_name = match.group(2).strip()
            response_time = float(match.group(3))
            
            results['workflows'].append({
                'name': workflow_name,
                'status': status.lower(),
                'response_time_ms': response_time,
                'success': status == 'PASS',
                'target_met': response_time < 500
            })
        
        # Extract overall metrics
        success_match = re.search(self.patterns['integration']['success_rate'], log_content)
        if success_match:
            results['overall']['success_rate'] = float(success_match.group(1))
        
        total_match = re.search(self.patterns['integration']['total_tests'], log_content)
        if total_match:
            results['overall']['total_tests'] = int(total_match.group(1))
        
        successful_match = re.search(self.patterns['integration']['successful_tests'], log_content)
        if successful_match:
            results['overall']['successful_tests'] = int(successful_match.group(1))
        
        # Extract test status
        status_match = re.search(self.patterns['integration']['test_status'], log_content)
        if status_match:
            results['status'] = status_match.group(1).lower()
            results['assessment'] = status_match.group(2)
            results['success'] = results['status'] == 'excellent'
        
        # Calculate averages
        if results['workflows']:
            successful_workflows = [w for w in results['workflows'] if w['success']]
            if successful_workflows:
                results['overall']['avg_response_time_ms'] = sum(w['response_time_ms'] for w in successful_workflows) / len(successful_workflows)
                results['overall']['target_met'] = all(w['target_met'] for w in successful_workflows)
        
        return results
    
    def parse_log_file(self, log_file: str, test_type: str) -> Dict[str, Any]:
        """Parse a log file and extract performance results."""
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            return {
                'test_type': test_type,
                'timestamp': datetime.now().isoformat(),
                'error': f"Failed to read log file: {str(e)}",
                'success': False
            }
        
        if test_type == 'baseline':
            return self.parse_baseline_results(content)
        elif test_type == 'load':
            return self.parse_load_results(content)
        elif test_type == 'integration':
            return self.parse_integration_results(content)
        else:
            return {
                'test_type': test_type,
                'timestamp': datetime.now().isoformat(),
                'error': f"Unknown test type: {test_type}",
                'success': False
            }
    
    def save_results(self, results: Dict[str, Any], output_file: str):
        """Save parsed results to JSON file."""
        try:
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"Results saved to {output_file}")
        except Exception as e:
            print(f"Failed to save results: {e}")


def main():
    """Main function for CLI usage."""
    if len(sys.argv) != 3:
        print("Usage: python parse_performance_results.py <log_file> <test_type>")
        print("Test types: baseline, load, integration")
        sys.exit(1)
    
    log_file = sys.argv[1]
    test_type = sys.argv[2]
    
    parser = PerformanceResultParser()
    results = parser.parse_log_file(log_file, test_type)
    
    # Generate output filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"performance_{test_type}_{timestamp}.json"
    
    parser.save_results(results, output_file)
    
    # Print summary
    print(f"\nPerformance Test Summary ({test_type}):")
    print(f"Status: {results.get('status', 'unknown')}")
    print(f"Success: {results.get('success', False)}")
    
    if 'overall' in results and 'avg_response_time_ms' in results['overall']:
        avg_time = results['overall']['avg_response_time_ms']
        print(f"Average Response Time: {avg_time:.2f}ms")
        print(f"Target Met: {results['overall'].get('target_met', False)}")
    
    if results.get('error'):
        print(f"Error: {results['error']}")
        sys.exit(1)
    
    # Exit with non-zero code if performance targets not met
    if not results.get('success', False):
        print("Performance targets not met!")
        sys.exit(1)
    
    print("Performance targets met!")


if __name__ == "__main__":
    main()
