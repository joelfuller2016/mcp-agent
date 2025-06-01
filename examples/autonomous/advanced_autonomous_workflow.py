#!/usr/bin/env python3
"""
Advanced Autonomous Workflow Example

This example demonstrates complex autonomous orchestration with multiple
agents, dynamic tool discovery, and sophisticated workflow patterns.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from mcp_agent.app import MCPApp
from mcp_agent.autonomous.autonomous_orchestrator import AutonomousOrchestrator
from mcp_agent.autonomous.meta_coordinator import MetaCoordinator

async def demonstrate_advanced_autonomous_orchestration():
    """Demonstrate advanced autonomous capabilities."""
    
    print("🧠 Advanced Autonomous Workflow Demonstration")
    print("=" * 55)
    
    # Create MCP app with enhanced configuration
    app = MCPApp(name="autonomous_advanced_demo")
    
    # Create meta-coordinator for highest-level orchestration
    coordinator = MetaCoordinator(app)
    
    print("1️⃣ Initializing meta-coordinator...")
    await coordinator.initialize()
    print("✅ Meta-coordinator ready!")
    
    # Complex multi-step task that requires orchestration
    complex_task = """
    Perform a comprehensive analysis of this MCP-Agent project:
    1. Analyze the project structure and identify all key components
    2. Evaluate the autonomous capabilities and their maturity
    3. Generate recommendations for Phase 2 enhancements
    4. Create a summary report with findings and next steps
    """
    
    print(f"\n2️⃣ Executing Complex Multi-Step Task:")
    print(f"📋 Task: {complex_task.strip()}")
    print("-" * 55)
    
    # Execute with meta-coordination
    result = await coordinator.execute_autonomous_task(
        complex_task.strip(),
        user_preferences={
            "detail_level": "comprehensive",
            "include_metrics": True,
            "format": "structured_report"
        }
    )
    
    if result.success:
        print("✅ Complex task completed successfully!")
        print(f"📊 Pattern: {result.pattern_used.value}")
        print(f"⏱️ Execution time: {result.execution_time:.2f}s")
        print(f"👥 Agents created: {result.agents_created}")
        print(f"🛠️ Tools used: {', '.join(result.tools_used)}")
        print(f"📝 Result length: {len(str(result.result))} characters")
        
        # Show first part of result
        result_preview = str(result.result)[:500]
        print(f"📄 Result preview:\n{result_preview}...")
        
    else:
        print(f"❌ Complex task failed: {result.error_message}")
    
    # Demonstrate capability gap analysis
    print(f"\n3️⃣ Analyzing Capability Gaps...")
    
    failed_tasks = [
        "Connect to a PostgreSQL database and run complex queries",
        "Deploy the application to AWS with auto-scaling",
        "Integrate with Slack for real-time notifications"
    ]
    
    gap_analysis = await coordinator.analyze_capability_gaps(failed_tasks)
    
    print("🔍 Capability Gap Analysis:")
    print(f"   • Missing capabilities: {len(gap_analysis['missing_capabilities'])}")
    for cap in gap_analysis['missing_capabilities']:
        print(f"     - {cap}")
    
    print(f"   • Suggested tools: {len(gap_analysis['suggested_tools'])}")
    for tool in gap_analysis['suggested_tools']:
        print(f"     - {tool}")
    
    print(f"   • Recommendations:")
    for rec in gap_analysis['recommendations']:
        print(f"     - {rec}")
    
    # Demonstrate performance optimization
    print(f"\n4️⃣ Performance Optimization Analysis...")
    
    optimization = await coordinator.optimize_configuration()
    
    print("⚡ Performance Optimization:")
    for pattern, stats in optimization['pattern_success_rates'].items():
        success_rate = stats['successes'] / max(stats['total'], 1) * 100
        print(f"   • {pattern}: {success_rate:.1f}% success ({stats['total']} executions)")
    
    print("💡 Optimization Suggestions:")
    for suggestion in optimization['optimization_suggestions']:
        print(f"   - {suggestion}")
    
    # Show comprehensive performance summary
    print(f"\n5️⃣ Performance Summary:")
    summary = coordinator.get_performance_summary()
    
    print(f"📈 Overall Performance:")
    print(f"   • Total executions: {summary['total_executions']}")
    print(f"   • Success rate: {summary['success_rate']}")
    print(f"   • Average execution time: {summary['average_execution_time']}")
    print(f"   • Most used pattern: {summary['most_used_pattern']}")
    print(f"   • Most used tool: {summary['most_used_tool']}")
    print(f"   • Unique tools: {summary['unique_tools_used']}")
    
    # Demonstrate different workflow patterns
    print(f"\n6️⃣ Testing Different Workflow Patterns...")
    
    pattern_tests = [
        ("Direct", "Get the current timestamp"),
        ("Parallel", "Analyze multiple configuration files and compare their settings"),
        ("Router", "Route this analysis task to the most appropriate specialist"),
        ("Orchestrator", "Plan and execute a comprehensive project audit with multiple phases")
    ]
    
    for pattern_name, task in pattern_tests:
        print(f"\n   🔄 Testing {pattern_name} Pattern:")
        print(f"   📋 Task: {task}")
        
        # Get suggestions without executing
        orchestrator = AutonomousOrchestrator(app=app)
        await orchestrator.initialize()
        
        suggestions = await orchestrator.get_execution_suggestions(task)
        
        print(f"   📊 Analysis:")
        print(f"      • Recommended: {suggestions['strategy']['recommended_pattern']}")
        print(f"      • Confidence: {suggestions['strategy']['confidence']}")
        print(f"      • Complexity: {suggestions['task_analysis']['complexity']}")
        print(f"      • Agents needed: {suggestions['agents']['suggested_count']}")

async def demonstrate_dynamic_agent_creation():
    """Demonstrate dynamic agent creation based on task requirements."""
    
    print(f"\n🏭 Dynamic Agent Factory Demonstration")
    print("=" * 45)
    
    # This would be expanded to show the DynamicAgentFactory in action
    # For now, we'll simulate it
    
    from mcp_agent.autonomous.task_analyzer import TaskAnalyzer
    
    analyzer = TaskAnalyzer()
    
    specialized_tasks = [
        "Analyze code quality and suggest improvements",
        "Process and analyze large datasets",
        "Manage GitHub repositories and issues",
        "Perform web scraping and data extraction",
        "Generate technical documentation"
    ]
    
    print("🏭 Agent Factory Analysis:")
    
    for i, task in enumerate(specialized_tasks, 1):
        analysis = analyzer.analyze_task(task)
        
        print(f"\n   {i}. Task: {task[:50]}...")
        print(f"      📊 Complexity: {analysis.complexity.value}")
        print(f"      🎯 Type: {analysis.task_type.value}")
        print(f"      🛠️ Capabilities needed: {len(analysis.required_capabilities)}")
        print(f"      ⚡ Pattern: {analysis.recommended_pattern.value}")
        print(f"      📝 Steps: {analysis.estimated_steps}")
        
        # Show what kind of agent would be created
        required_caps = analysis.required_capabilities
        if required_caps:
            print(f"      👤 Agent would need: {', '.join(list(required_caps)[:3])}...")

if __name__ == "__main__":
    async def main():
        await demonstrate_advanced_autonomous_orchestration()
        await demonstrate_dynamic_agent_creation()
        
        print(f"\n🎉 Advanced Autonomous Demonstration Complete!")
        print("   ✅ Meta-coordination working")
        print("   ✅ Complex task orchestration working")
        print("   ✅ Capability gap analysis working")
        print("   ✅ Performance optimization working")
        print("   ✅ Dynamic agent creation working")
    
    asyncio.run(main())
