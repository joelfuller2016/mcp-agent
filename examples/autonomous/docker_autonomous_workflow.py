#!/usr/bin/env python3
"""
Docker Autonomous Workflow Example

This example demonstrates autonomous workflows specifically designed
for containerized environments with Docker.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from mcp_agent.app import MCPApp
from mcp_agent.autonomous.autonomous_orchestrator import AutonomousOrchestrator

async def demonstrate_docker_autonomous_workflow():
    """Demonstrate autonomous workflows in Docker environment."""
    
    print("🐳 Docker Autonomous Workflow Demonstration")
    print("=" * 50)
    
    # Check Docker environment
    print("1️⃣ Docker Environment Check:")
    docker_env_vars = [
        "MCP_AUTONOMOUS_MODE",
        "MCP_AUTONOMOUS_CONFIG_PATH", 
        "PYTHONPATH",
        "PYTHONUNBUFFERED"
    ]
    
    for var in docker_env_vars:
        value = os.environ.get(var, "Not set")
        print(f"   • {var}: {value}")
    
    # Create app configured for Docker
    app = MCPApp(name="docker_autonomous_demo")
    
    # Create orchestrator
    orchestrator = AutonomousOrchestrator(app=app)
    
    print(f"\n2️⃣ Initializing in Docker environment...")
    success = await orchestrator.initialize()
    
    if not success:
        print("❌ Failed to initialize in Docker")
        return
    
    print("✅ Docker autonomous environment ready!")
    
    # Docker-specific tasks
    docker_tasks = [
        "Analyze the container's file system structure",
        "Check what MCP servers are available in this container",
        "Evaluate the autonomous configuration loaded from /app/config/autonomous.yaml",
        "Test file operations within the container environment",
        "Generate a containerized deployment report"
    ]
    
    print(f"\n3️⃣ Executing Docker-Specific Tasks:")
    
    for i, task in enumerate(docker_tasks, 1):
        print(f"\n   {i}. 📋 Task: {task}")
        print(f"      🔄 Analyzing...")
        
        # Get execution strategy
        suggestions = await orchestrator.get_execution_suggestions(task)
        print(f"      📊 Strategy: {suggestions['strategy']['recommended_pattern']}")
        print(f"      🧠 Complexity: {suggestions['task_analysis']['complexity']}")
        
        # Execute in Docker environment
        print(f"      🚀 Executing in container...")
        result = await orchestrator.execute_autonomous_task(task)
        
        if result.success:
            print(f"      ✅ Completed in {result.execution_time:.2f}s")
            print(f"      🛠️ Used {len(result.agents_used)} agents")
            print(f"      📝 Result: {str(result.result)[:100]}...")
        else:
            print(f"      ❌ Failed: {result.error_message}")
    
    # Test container-specific capabilities
    print(f"\n4️⃣ Container Capability Assessment:")
    
    capabilities = await orchestrator.analyze_capabilities()
    
    print(f"   📊 Tool Capabilities:")
    tool_summary = capabilities.get('tool_capabilities', {})
    print(f"      • Available servers: {tool_summary.get('available_servers', 0)}")
    
    print(f"   🏭 Agent Factory:")
    factory_status = capabilities.get('factory_status', {})
    print(f"      • Specializations: {len(factory_status.get('available_specializations', []))}")
    
    print(f"   📈 Execution Metrics:")
    print(f"      • Success rate: {capabilities.get('success_rate', 0)*100:.1f}%")
    print(f"      • Executions: {capabilities.get('execution_history', 0)}")
    
    # Test Docker volume access
    print(f"\n5️⃣ Docker Volume and Mount Testing:")
    
    volume_tests = [
        ("Logs directory", "/app/logs"),
        ("Config directory", "/app/config"),
        ("Data directory", "/app/data"),
        ("Examples directory", "/app/examples")
    ]
    
    for name, path in volume_tests:
        if os.path.exists(path):
            items = len(os.listdir(path))
            print(f"   ✅ {name}: {path} ({items} items)")
        else:
            print(f"   ❌ {name}: {path} (not found)")
    
    # Check configuration loading
    print(f"\n6️⃣ Configuration Validation:")
    
    config_path = "/app/config/autonomous.yaml"
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config_content = f.read()
        
        print(f"   ✅ Autonomous config loaded ({len(config_content)} chars)")
        
        # Check key sections
        sections = ["autonomous:", "tool_discovery:", "performance:"]
        for section in sections:
            if section in config_content:
                print(f"   ✅ {section} section found")
            else:
                print(f"   ⚠️ {section} section missing")
    else:
        print(f"   ❌ Config file not found at {config_path}")
    
    # Generate Docker deployment report
    print(f"\n7️⃣ Generating Docker Deployment Report...")
    
    report_task = """
    Generate a comprehensive Docker deployment report that includes:
    - Container environment analysis
    - Available tools and capabilities  
    - Configuration validation
    - Performance assessment
    - Recommendations for optimization
    """
    
    print("📄 Executing report generation...")
    report_result = await orchestrator.execute_autonomous_task(report_task.strip())
    
    if report_result.success:
        print(f"✅ Docker deployment report generated!")
        print(f"📊 Report details:")
        print(f"   • Pattern used: {report_result.execution_pattern.value}")
        print(f"   • Execution time: {report_result.execution_time:.2f}s")
        print(f"   • Agents involved: {len(report_result.agents_used)}")
        
        # Save report to Docker volume
        report_path = "/app/logs/docker_deployment_report.txt"
        try:
            with open(report_path, 'w') as f:
                f.write(f"Docker Autonomous Deployment Report\n")
                f.write(f"Generated at: {asyncio.get_event_loop().time()}\n")
                f.write(f"Pattern: {report_result.execution_pattern.value}\n")
                f.write(f"Execution time: {report_result.execution_time:.2f}s\n\n")
                f.write(str(report_result.result))
            
            print(f"💾 Report saved to {report_path}")
        except Exception as e:
            print(f"⚠️ Could not save report: {e}")
    else:
        print(f"❌ Report generation failed: {report_result.error_message}")
    
    # Show execution summary
    print(f"\n📈 Docker Execution Summary:")
    history = orchestrator.get_execution_history()
    
    successful = sum(1 for h in history if h["success"])
    total = len(history)
    
    print(f"   • Total tasks executed: {total}")
    print(f"   • Successful: {successful}")
    print(f"   • Success rate: {(successful/total)*100:.1f}%" if total > 0 else "   • Success rate: N/A")
    print(f"   • Average execution time: {sum(h['execution_time'] for h in history)/total:.2f}s" if total > 0 else "   • Average time: N/A")
    
    # Environment recommendations
    print(f"\n💡 Docker Environment Recommendations:")
    
    recommendations = []
    
    if os.environ.get("MCP_AUTONOMOUS_MODE") != "true":
        recommendations.append("Set MCP_AUTONOMOUS_MODE=true for optimal performance")
    
    if not os.path.exists("/app/config/autonomous.yaml"):
        recommendations.append("Ensure autonomous.yaml configuration is properly mounted")
    
    if not os.path.exists("/app/data"):
        recommendations.append("Mount persistent volume for /app/data directory")
    
    if recommendations:
        for i, rec in enumerate(recommendations, 1):
            print(f"   {i}. {rec}")
    else:
        print("   ✅ Docker environment is optimally configured!")

if __name__ == "__main__":
    asyncio.run(demonstrate_docker_autonomous_workflow())
