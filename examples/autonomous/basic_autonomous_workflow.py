#!/usr/bin/env python3
"""
Basic Autonomous Workflow Example

This example demonstrates how to use the autonomous orchestrator
to execute tasks without manual agent configuration.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from mcp_agent.app import MCPApp
from mcp_agent.autonomous.autonomous_orchestrator import AutonomousOrchestrator

async def demonstrate_basic_autonomous_execution():
    """Demonstrate basic autonomous task execution."""
    
    print("🤖 Basic Autonomous Workflow Demonstration")
    print("=" * 50)
    
    # Create MCP app
    app = MCPApp(name="autonomous_basic_demo")
    
    # Create autonomous orchestrator
    orchestrator = AutonomousOrchestrator(app=app)
    
    print("1️⃣ Initializing autonomous orchestrator...")
    
    # Initialize (discovers tools, sets up components)
    success = await orchestrator.initialize()
    if not success:
        print("❌ Failed to initialize orchestrator")
        return
    
    print("✅ Orchestrator initialized successfully!")
    
    # Example tasks to demonstrate different patterns
    tasks = [
        "List the files in the current directory",
        "Analyze the project structure and identify key files",
        "Create a summary of the project's autonomous capabilities"
    ]
    
    for i, task in enumerate(tasks, 1):
        print(f"\n{i}️⃣ Executing Task: {task}")
        print("-" * 40)
        
        # Get execution suggestions first (optional)
        suggestions = await orchestrator.get_execution_suggestions(task)
        print(f"📋 Strategy: {suggestions['strategy']['recommended_pattern']}")
        print(f"🧠 Complexity: {suggestions['task_analysis']['complexity']}")
        print(f"👥 Suggested agents: {suggestions['agents']['suggested_count']}")
        
        # Execute the task autonomously
        print("🚀 Executing...")
        result = await orchestrator.execute_autonomous_task(task)
        
        if result.success:
            print(f"✅ Task completed successfully!")
            print(f"📊 Pattern used: {result.execution_pattern.value}")
            print(f"⏱️ Execution time: {result.execution_time:.2f}s")
            print(f"🛠️ Agents used: {len(result.agents_used)}")
            print(f"📝 Result: {str(result.result)[:200]}...")
        else:
            print(f"❌ Task failed: {result.error_message}")
    
    # Show execution history
    print(f"\n📈 Execution History:")
    history = orchestrator.get_execution_history()
    for i, execution in enumerate(history, 1):
        status = "✅" if execution["success"] else "❌"
        print(f"   {i}. {status} {execution['task'][:50]}... ({execution['execution_time']:.1f}s)")
    
    print(f"\n🎯 Performance Summary:")
    capabilities = await orchestrator.analyze_capabilities()
    print(f"   • Success rate: {capabilities.get('success_rate', 0)*100:.1f}%")
    print(f"   • Total executions: {capabilities.get('execution_history', 0)}")

if __name__ == "__main__":
    asyncio.run(demonstrate_basic_autonomous_execution())
