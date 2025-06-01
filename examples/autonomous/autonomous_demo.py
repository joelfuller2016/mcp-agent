"""
Autonomous MCP-Agent Example Application.

This example demonstrates the autonomous capabilities of mcp-agent:
- Automatic tool discovery
- Task analysis and strategy selection
- Dynamic agent creation
- Intelligent execution pattern selection
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent / "src"))

from mcp_agent.app import MCPApp
from mcp_agent.autonomous.autonomous_orchestrator import (
    AutonomousOrchestrator,
    AutonomousConfig,
)


async def demo_simple_task():
    """Demonstrate autonomous execution of a simple task."""
    print("\n🤖 === AUTONOMOUS MCP-AGENT DEMO ===")
    print("Demonstrating intelligent tool selection and execution...")

    # Create autonomous orchestrator
    config = AutonomousConfig(
        max_agents=3, prefer_simple_patterns=False, log_decisions=True
    )

    orchestrator = AutonomousOrchestrator(config=config)

    # Simple information retrieval task
    print("\n📋 Task 1: Simple Information Retrieval")
    task1 = "Find and read the contents of README.md in the current directory"

    result1 = await orchestrator.execute_autonomous_task(task1)

    print(f"✅ Success: {result1.success}")
    print(f"🎯 Pattern Used: {result1.execution_pattern.value}")
    print(f"🤖 Agents: {', '.join(result1.agents_used)}")
    print(f"⏱️ Time: {result1.execution_time:.2f}s")
    if result1.result:
        print(f"📄 Result: {result1.result[:200]}...")

    return orchestrator


async def demo_complex_task(orchestrator: AutonomousOrchestrator):
    """Demonstrate autonomous execution of a complex task."""
    print("\n📋 Task 2: Complex Analysis Task")
    task2 = (
        "Analyze the mcp-agent project structure, identify the main components, "
        "create a comprehensive report about the project's capabilities, and "
        "suggest improvements for better autonomous functionality"
    )

    # First, get suggestions without executing
    suggestions = await orchestrator.get_execution_suggestions(task2)

    print("🧠 Task Analysis Suggestions:")
    print(f"  Type: {suggestions['task_analysis']['type']}")
    print(f"  Complexity: {suggestions['task_analysis']['complexity']}")
    print(f"  Recommended Pattern: {suggestions['strategy']['recommended_pattern']}")
    print(f"  Reasoning: {suggestions['strategy']['reasoning']}")
    print(f"  Estimated Steps: {suggestions['task_analysis']['estimated_steps']}")

    # Execute the complex task
    result2 = await orchestrator.execute_autonomous_task(task2)

    print(f"\n✅ Success: {result2.success}")
    print(f"🎯 Pattern Used: {result2.execution_pattern.value}")
    print(f"🤖 Agents: {', '.join(result2.agents_used)}")
    print(f"⏱️ Time: {result2.execution_time:.2f}s")
    print(f"🔍 Steps: {result2.total_steps}")

    if result2.result:
        print(f"📊 Result: {result2.result[:300]}...")

    if not result2.success:
        print(f"❌ Error: {result2.error_message}")


async def demo_interactive_mode(orchestrator: AutonomousOrchestrator):
    """Interactive mode for testing autonomous capabilities."""
    print("\n🎮 === INTERACTIVE AUTONOMOUS MODE ===")
    print("Enter tasks for autonomous execution (type 'quit' to exit):")

    while True:
        try:
            task = input("\n🎯 Enter task: ").strip()

            if task.lower() in ["quit", "exit", "q"]:
                break

            if not task:
                continue

            # Get execution suggestions first
            print("\n🧠 Analyzing task...")
            suggestions = await orchestrator.get_execution_suggestions(task)

            print(f"  📊 Analysis: {suggestions['task_analysis']['type']} task")
            print(f"  🎯 Strategy: {suggestions['strategy']['recommended_pattern']}")
            print(f"  🤖 Agents needed: {suggestions['agents']['suggested_count']}")

            # Ask for confirmation
            proceed = input("  ▶️ Execute autonomously? (y/n): ").strip().lower()

            if proceed == "y":
                print("  🚀 Executing...")
                result = await orchestrator.execute_autonomous_task(task)

                if result.success:
                    print(f"  ✅ Completed in {result.execution_time:.2f}s")
                    print(f"  📄 Result: {result.result[:200]}...")
                else:
                    print(f"  ❌ Failed: {result.error_message}")

        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"  ❌ Error: {e}")

    print("\n👋 Exiting interactive mode")


async def demo_capability_analysis(orchestrator: AutonomousOrchestrator):
    """Demonstrate capability analysis."""
    print("\n🔍 === CAPABILITY ANALYSIS ===")

    capabilities = await orchestrator.analyze_capabilities()

    print("🛠️ Tool Capabilities:")
    tool_caps = capabilities["tool_capabilities"]
    print(
        f"  Available Servers: {tool_caps['available_servers']}/{tool_caps['total_servers']}"
    )
    print(f"  Total Capabilities: {tool_caps['total_capabilities']}")
    print(f"  Categories: {', '.join(tool_caps['categories'])}")

    print("\n🤖 Agent Specializations:")
    print(f"  Available: {', '.join(capabilities['agent_specializations'])}")

    factory_status = capabilities["factory_status"]
    print(f"  Most Effective: {factory_status['most_effective_specialization']}")
    print(f"  Average Effectiveness: {factory_status['average_effectiveness']:.2f}")

    print(f"\n📊 Execution History: {capabilities['execution_history']} tasks")
    print(f"  Success Rate: {capabilities['success_rate']:.2%}")


async def demo_specialized_workflows():
    """Demonstrate different specialized workflow patterns."""
    print("\n🎛️ === SPECIALIZED WORKFLOW DEMO ===")

    orchestrator = AutonomousOrchestrator()

    # Test different types of tasks to see different patterns
    test_tasks = [
        ("Simple file read", "Read the pyproject.toml file"),
        (
            "Web research",
            "Search for recent news about Model Context Protocol and summarize findings",
        ),
        ("Code analysis", "Analyze the Python code structure in the src directory"),
        (
            "Complex planning",
            "Create a development roadmap for adding voice capabilities to mcp-agent",
        ),
        (
            "Data processing",
            "If there are any CSV files, analyze their structure and content",
        ),
    ]

    for task_name, task_description in test_tasks:
        print(f"\n📋 {task_name}:")

        suggestions = await orchestrator.get_execution_suggestions(task_description)
        print(
            f"  🎯 Suggested Pattern: {suggestions['strategy']['recommended_pattern']}"
        )
        print(f"  🤖 Agents Needed: {suggestions['agents']['suggested_count']}")
        print(
            f"  🔧 Required Servers: {', '.join(suggestions['strategy']['required_servers'])}"
        )

        # Execute a subset for demonstration
        if task_name in ["Simple file read", "Code analysis"]:
            result = await orchestrator.execute_autonomous_task(task_description)
            print(f"  ✅ Executed: {result.success} in {result.execution_time:.2f}s")


async def main():
    """Main demo function."""
    print("🚀 Starting Autonomous MCP-Agent Demonstration")

    # Set up logging to see decision process
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    try:
        # Demo 1: Simple task
        orchestrator = await demo_simple_task()

        # Demo 2: Complex task
        await demo_complex_task(orchestrator)

        # Demo 3: Capability analysis
        await demo_capability_analysis(orchestrator)

        # Demo 4: Specialized workflows
        await demo_specialized_workflows()

        # Demo 5: Interactive mode (optional)
        interactive = input("\n🎮 Enter interactive mode? (y/n): ").strip().lower()
        if interactive == "y":
            await demo_interactive_mode(orchestrator)

        # Show execution history
        print("\n📊 === EXECUTION HISTORY ===")
        history = orchestrator.get_execution_history()
        for i, execution in enumerate(history[-5:], 1):
            print(
                f"{i}. {execution['task'][:50]}... - {execution['pattern']} - {'✅' if execution['success'] else '❌'}"
            )

        print("\n🎉 Demo completed successfully!")

    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
