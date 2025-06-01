#!/usr/bin/env python3
"""
Performance Report Generator for CI/CD Pipeline

Generates comprehensive HTML reports and summary data for performance test results.
"""

import os
import json
import glob
from datetime import datetime
from typing import Dict, List, Any, Optional


class PerformanceReportGenerator:
    """Generate comprehensive performance reports."""
    
    def __init__(self, artifacts_dir: str = "performance-artifacts"):
        self.artifacts_dir = artifacts_dir
        self.report_template = self._get_html_template()
    
    def _get_html_template(self) -> str:
        """Get HTML template for performance report."""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MCP-Agent Performance Report</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
            color: #333;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        .header h1 {
            margin: 0;
            font-size: 2.5em;
        }
        .header p {
            margin: 10px 0 0 0;
            opacity: 0.9;
        }
        .summary {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            padding: 30px;
            background: #f8f9fa;
        }
        .summary-card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            text-align: center;
        }
        .summary-card h3 {
            margin: 0 0 10px 0;
            color: #495057;
        }
        .summary-card .value {
            font-size: 2em;
            font-weight: bold;
            margin: 10px 0;
        }
        .value.success { color: #28a745; }
        .value.warning { color: #ffc107; }
        .value.danger { color: #dc3545; }
        .content {
            padding: 30px;
        }
        .test-section {
            margin-bottom: 40px;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            overflow: hidden;
        }
        .test-header {
            background: #e9ecef;
            padding: 15px 20px;
            border-bottom: 1px solid #dee2e6;
        }
        .test-header h2 {
            margin: 0;
            color: #495057;
        }
        .test-content {
            padding: 20px;
        }
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }
        .metric {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 6px;
            border-left: 4px solid #007bff;
        }
        .metric.success { border-left-color: #28a745; }
        .metric.warning { border-left-color: #ffc107; }
        .metric.danger { border-left-color: #dc3545; }
        .metric-label {
            font-size: 0.9em;
            color: #6c757d;
            margin-bottom: 5px;
        }
        .metric-value {
            font-size: 1.4em;
            font-weight: bold;
            color: #495057;
        }
        .regression-list {
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 6px;
            padding: 15px;
            margin: 15px 0;
        }
        .regression-item {
            background: white;
            padding: 10px;
            margin: 8px 0;
            border-radius: 4px;
            border-left: 4px solid #ffc107;
        }
        .regression-item.high {
            border-left-color: #dc3545;
            background: #f8d7da;
        }
        .status-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.8em;
            font-weight: bold;
            text-transform: uppercase;
        }
        .status-badge.passing {
            background: #d4edda;
            color: #155724;
        }
        .status-badge.warning {
            background: #fff3cd;
            color: #856404;
        }
        .status-badge.failing {
            background: #f8d7da;
            color: #721c24;
        }
        .status-badge.critical {
            background: #f5c6cb;
            color: #721c24;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }
        th, td {
            text-align: left;
            padding: 12px;
            border-bottom: 1px solid #dee2e6;
        }
        th {
            background: #f8f9fa;
            font-weight: 600;
            color: #495057;
        }
        .footer {
            background: #e9ecef;
            padding: 20px;
            text-align: center;
            color: #6c757d;
        }
        .chart-container {
            margin: 20px 0;
            height: 300px;
            background: #f8f9fa;
            border-radius: 6px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #6c757d;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 MCP-Agent Performance Report</h1>
            <p>Generated on {timestamp}</p>
        </div>
        
        <div class="summary">
            <div class="summary-card">
                <h3>Overall Status</h3>
                <div class="value {overall_status_class}">{overall_status}</div>
                <span class="status-badge {overall_status}">{overall_status}</span>
            </div>
            <div class="summary-card">
                <h3>Regression Detected</h3>
                <div class="value {regression_class}">{regression_status}</div>
                <p>{regression_count} issues found</p>
            </div>
            <div class="summary-card">
                <h3>Targets Met</h3>
                <div class="value {targets_class}">{targets_status}</div>
                <p>{target_compliance}% compliance</p>
            </div>
            <div class="summary-card">
                <h3>Tests Run</h3>
                <div class="value">{total_tests}</div>
                <p>{successful_tests} successful</p>
            </div>
        </div>
        
        <div class="content">
            {test_sections}
        </div>
        
        <div class="footer">
            <p>Report generated by MCP-Agent CI/CD Performance Monitoring System</p>
            <p>For more information, see the <a href="PERFORMANCE_OPTIMIZATION_GUIDE.md">Performance Optimization Guide</a></p>
        </div>
    </div>
</body>
</html>
        """
    
    def load_results(self) -> Dict[str, Any]:
        """Load all performance results and analysis."""
        results = {
            'test_results': {},
            'analysis': None,
            'timestamp': datetime.now().isoformat()
        }
        
        # Load individual test results
        for test_type in ['baseline', 'load', 'integration']:
            pattern = os.path.join(self.artifacts_dir, f"*{test_type}*", f"performance_{test_type}_*.json")
            files = glob.glob(pattern)
            
            if files:
                # Get most recent result
                latest_file = max(files, key=os.path.getctime)
                try:
                    with open(latest_file, 'r') as f:
                        results['test_results'][test_type] = json.load(f)
                except Exception as e:
                    print(f"Warning: Could not load {latest_file}: {e}")
        
        # Load regression analysis
        analysis_files = glob.glob("performance_regression_analysis.json")
        if analysis_files:
            try:
                with open(analysis_files[0], 'r') as f:
                    results['analysis'] = json.load(f)
            except Exception as e:
                print(f"Warning: Could not load analysis: {e}")
        
        return results
    
    def generate_test_section(self, test_type: str, test_data: Dict[str, Any], 
                             analysis_data: Optional[Dict[str, Any]] = None) -> str:
        """Generate HTML section for a specific test type."""
        
        # Extract metrics
        metrics_html = ""
        if 'overall' in test_data:
            overall = test_data['overall']
            
            if 'avg_response_time_ms' in overall:
                response_time = overall['avg_response_time_ms']
                time_class = 'success' if response_time < 50 else ('warning' if response_time < 500 else 'danger')
                metrics_html += f"""
                <div class="metric {time_class}">
                    <div class="metric-label">Average Response Time</div>
                    <div class="metric-value">{response_time:.2f}ms</div>
                </div>
                """
            
            if 'success_rate' in overall:
                success_rate = overall['success_rate']
                rate_class = 'success' if success_rate >= 95 else ('warning' if success_rate >= 90 else 'danger')
                metrics_html += f"""
                <div class="metric {rate_class}">
                    <div class="metric-label">Success Rate</div>
                    <div class="metric-value">{success_rate:.1f}%</div>
                </div>
                """
            
            if 'max_throughput_rps' in overall:
                throughput = overall['max_throughput_rps']
                throughput_class = 'success' if throughput >= 100 else 'warning'
                metrics_html += f"""
                <div class="metric {throughput_class}">
                    <div class="metric-label">Peak Throughput</div>
                    <div class="metric-value">{throughput:.1f} RPS</div>
                </div>
                """
        
        # Generate regression analysis
        regression_html = ""
        if analysis_data and 'regression_analysis' in analysis_data:
            regression = analysis_data['regression_analysis']
            regressions = regression.get('regressions', [])
            
            if regressions:
                regression_html = '<div class="regression-list"><h4>⚠️ Regressions Detected</h4>'
                for reg in regressions:
                    severity_class = 'high' if reg['severity'] == 'high' else ''
                    regression_html += f"""
                    <div class="regression-item {severity_class}">
                        <strong>{reg['type'].replace('_', ' ').title()}:</strong> {reg['message']}
                    </div>
                    """
                regression_html += '</div>'
            else:
                regression_html = '<div class="metric success"><div class="metric-label">Regression Status</div><div class="metric-value">✅ No Regressions</div></div>'
        
        # Generate detailed results table
        table_html = ""
        if test_type == 'load' and 'tests' in test_data:
            table_html = """
            <h4>Load Test Results</h4>
            <table>
                <thead>
                    <tr>
                        <th>Test Configuration</th>
                        <th>Users</th>
                        <th>Success Rate</th>
                        <th>Avg Time</th>
                        <th>P95 Time</th>
                        <th>RPS</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
            """
            
            for test in test_data['tests']:
                status = '✅ Pass' if test['target_met'] else '❌ Fail'
                table_html += f"""
                <tr>
                    <td>{test['name']}</td>
                    <td>{test['concurrent_users']}</td>
                    <td>{test['success_rate']:.1f}%</td>
                    <td>{test['avg_response_time_ms']:.2f}ms</td>
                    <td>{test['p95_response_time_ms']:.2f}ms</td>
                    <td>{test['requests_per_second']:.1f}</td>
                    <td>{status}</td>
                </tr>
                """
            
            table_html += "</tbody></table>"
        
        elif test_type == 'integration' and 'workflows' in test_data:
            table_html = """
            <h4>Integration Test Results</h4>
            <table>
                <thead>
                    <tr>
                        <th>Workflow</th>
                        <th>Status</th>
                        <th>Response Time</th>
                        <th>Target Met</th>
                    </tr>
                </thead>
                <tbody>
            """
            
            for workflow in test_data['workflows']:
                status_icon = '✅' if workflow['success'] else '❌'
                target_icon = '✅' if workflow['target_met'] else '❌'
                table_html += f"""
                <tr>
                    <td>{workflow['name']}</td>
                    <td>{status_icon} {workflow['status'].title()}</td>
                    <td>{workflow['response_time_ms']:.2f}ms</td>
                    <td>{target_icon}</td>
                </tr>
                """
            
            table_html += "</tbody></table>"
        
        return f"""
        <div class="test-section">
            <div class="test-header">
                <h2>{test_type.title()} Performance Test</h2>
            </div>
            <div class="test-content">
                <div class="metrics-grid">
                    {metrics_html}
                </div>
                {regression_html}
                {table_html}
            </div>
        </div>
        """
    
    def generate_html_report(self, results: Dict[str, Any]) -> str:
        """Generate complete HTML performance report."""
        
        # Calculate summary statistics
        analysis = results.get('analysis', {})
        overall_status = analysis.get('overall_status', 'unknown')
        regression_detected = analysis.get('regression_detected', False)
        targets_met = analysis.get('targets_met', True)
        
        # Count statistics
        total_tests = 0
        successful_tests = 0
        regression_count = 0
        
        for test_type, test_data in results['test_results'].items():
            if 'overall' in test_data:
                total_tests += test_data['overall'].get('total_tests', 1)
                successful_tests += test_data['overall'].get('successful_tests', 1)
        
        if analysis and 'test_results' in analysis:
            for test_result in analysis['test_results'].values():
                regressions = test_result.get('regression_analysis', {}).get('regressions', [])
                regression_count += len(regressions)
        
        target_compliance = (successful_tests / max(total_tests, 1)) * 100
        
        # Generate test sections
        test_sections = ""
        for test_type, test_data in results['test_results'].items():
            analysis_data = None
            if analysis and 'test_results' in analysis and test_type in analysis['test_results']:
                analysis_data = analysis['test_results'][test_type]
            
            test_sections += self.generate_test_section(test_type, test_data, analysis_data)
        
        # Determine CSS classes for styling
        overall_status_class = {
            'passing': 'success',
            'warning': 'warning', 
            'failing': 'danger',
            'critical': 'danger'
        }.get(overall_status, 'warning')
        
        regression_class = 'danger' if regression_detected else 'success'
        targets_class = 'success' if targets_met else 'danger'
        
        # Fill template
        return self.report_template.format(
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC'),
            overall_status=overall_status.upper(),
            overall_status_class=overall_status_class,
            regression_status='YES' if regression_detected else 'NO',
            regression_class=regression_class,
            regression_count=regression_count,
            targets_status='YES' if targets_met else 'NO',
            targets_class=targets_class,
            target_compliance=f"{target_compliance:.1f}",
            total_tests=total_tests,
            successful_tests=successful_tests,
            test_sections=test_sections
        )
    
    def generate_summary_json(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate JSON summary for CI/CD pipeline."""
        analysis = results.get('analysis', {})
        
        summary = {
            'timestamp': results['timestamp'],
            'overall_status': analysis.get('overall_status', 'unknown'),
            'regression_detected': analysis.get('regression_detected', False),
            'targets_met': analysis.get('targets_met', True),
            'baseline': {'status': 'not_run', 'avg_time': 0},
            'load': {'status': 'not_run', 'avg_time': 0},
            'integration': {'status': 'not_run', 'avg_time': 0}
        }
        
        # Extract test-specific data
        for test_type, test_data in results['test_results'].items():
            if 'overall' in test_data and 'avg_response_time_ms' in test_data['overall']:
                avg_time = test_data['overall']['avg_response_time_ms']
                status = 'pass' if avg_time < 500 else 'fail'
                
                summary[test_type] = {
                    'status': status,
                    'avg_time': f"{avg_time:.2f}",
                    'success_rate': test_data['overall'].get('success_rate', 0)
                }
        
        return summary
    
    def generate_reports(self, output_dir: str = "."):
        """Generate all performance reports."""
        results = self.load_results()
        
        # Generate HTML report
        html_report = self.generate_html_report(results)
        html_path = os.path.join(output_dir, "performance_report.html")
        
        with open(html_path, 'w') as f:
            f.write(html_report)
        print(f"HTML report generated: {html_path}")
        
        # Generate JSON summary
        summary = self.generate_summary_json(results)
        summary_path = os.path.join(output_dir, "performance_summary.json")
        
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
        print(f"Summary JSON generated: {summary_path}")
        
        return {
            'html_report': html_path,
            'summary_json': summary_path,
            'results': results
        }


def main():
    """Main function for CLI usage."""
    generator = PerformanceReportGenerator()
    reports = generator.generate_reports()
    
    print("Performance report generation completed!")
    print(f"HTML Report: {reports['html_report']}")
    print(f"Summary JSON: {reports['summary_json']}")


if __name__ == "__main__":
    main()
