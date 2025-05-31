"""
Autonomous MCP Agent Example

This example demonstrates the autonomous capabilities of mcp-agent, including:
- Automatic tool discovery and selection
- Intelligent workflow pattern selection  
- Dynamic agent creation
- Autonomous task execution

Run this example to see the autonomous system in action!
"""

import asyncio
import logging

from mcp_agent.autonomous import AdaptiveOrchestrator, execute_task, explain_task_approach, run_demo


async def basic_autonomous_example():
    """Basic example of autonomous task execution"""
    print("🤖 Basic Autonomous Task Execution")
    print("=" * 50)
    
    # Simple usage - the system handles everything automatically
    tasks = [
        "List the files in the current directory",
        "Create a simple project plan for building a web application", 
        "Search for the latest news about AI and summarize the top 3 articles",
        "Analyze the complexity of implementing autonomous agent systems"
    ]
    
    for task in tasks:
        print(f"\n📝 Task: {task}")
        print("-" * 30)
        
        try:
            # Explain approach first
            explanation = await explain_task_approach(task)
            pattern = explanation.split("Selected pattern: ")[1].split("\n")[0] if "Selected pattern:" in explanation else "unknown"
            print(f"🧠 Approach: Using {pattern} pattern")
            
            # Execute autonomously  
            result = await execute_task(task)
            print(f"✅ Result: {result[:200]}{'...' if len(result) > 200 else ''}")
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")


async def detailed_autonomous_example():
    """Detailed example showing full autonomous system capabilities"""
    print("\n🔧 Detailed Autonomous System Demo")
    print("=" * 50)
    
    # Create orchestrator instance for detailed control
    orchestrator = AdaptiveOrchestrator(llm_provider="openai")
    
    # Initialize the system
    print("\n🚀 Initializing autonomous system...")
    await orchestrator.initialize()
    
    # Show system status
    status = orchestrator.get_system_status()
    print(f"\n📊 System Status:")
    print(f"  Available MCP servers: {status['available_servers']}")
    print(f"  Detected capabilities: {list(orchestrator.get_available_capabilities().keys())}")
    
    # Complex multi-step task
    complex_task = """
    I need you to help me analyze my development workflow. First, read any README 
    files to understand current projects. Then search for best practices in 
    software project management. Finally, create a comprehensive improvement 
    plan that combines the current state with industry best practices.
    """
    
    print(f"\n📋 Complex Task: {complex_task.strip()}")
    print("-" * 50)
    
    # Get detailed explanation
    explanation = await orchestrator.explain_approach(complex_task)
    print(f"\n🧠 Detailed Analysis:\n{explanation}")
    
    # Execute the task
    print(f"\n⚡ Executing autonomous task...")
    result = await orchestrator.execute_autonomous_task(complex_task)
    
    if result.success:
        print(f"\n✅ Task completed successfully!")
        print(f"   Pattern used: {result.pattern_used.value}")
        print(f"   Agents created: {', '.join(result.agents_created)}")
        print(f"   Execution time: {result.execution_time:.2f}s")
        print(f"   Confidence: {result.confidence:.2f}")
        print(f"\n📄 Result:\n{result.result}")
    else:
        print(f"\n❌ Task failed: {result.error_message}")
    
    # Show execution history
    history = orchestrator.get_execution_history()
    print(f"\n📊 Execution Summary:")
    print(f"   Total tasks: {len(history)}")
    print(f"   Successful: {sum(1 for r in history if r.success)}")
    print(f"   Average execution time: {sum(r.execution_time for r in history) / len(history):.2f}s")


async def workflow_pattern_demo():
    """Demonstrate different workflow patterns being selected automatically"""
    print("\n🔄 Workflow Pattern Selection Demo")
    print("=" * 50)
    
    # Tasks designed to trigger different patterns
    pattern_tasks = [
        ("Simple file read", "Read the contents of README.md"),
        ("Parallel analysis", "Analyze this project from both technical and business perspectives"),
        ("Complex orchestration", "Create a comprehensive development roadmap that includes research, planning, implementation, and testing phases"),
        ("Iterative refinement", "Write a professional project description and keep improving it until it's excellent"),
        ("Multi-agent coordination", "Help me organize a complex software project with multiple team members and different skill requirements")
    ]
    
    orchestrator = AdaptiveOrchestrator()
    await orchestrator.initialize()
    
    for pattern_name, task in pattern_tasks:
        print(f"\n📝 {pattern_name}: {task}")
        print("-" * 40)
        
        # Show what pattern would be selected
        explanation = await orchestrator.explain_approach(task)
        lines = explanation.split('\n')
        pattern_line = next((line for line in lines if 'Selected pattern:' in line), "Pattern: unknown")
        reasoning_line = next((line for line in lines if 'Reasoning:' in line), "")
        
        print(f"🧠 {pattern_line}")
        print(f"💭 {reasoning_line}")
        
        # Execute the task
        result = await orchestrator.execute_autonomous_task(task)
        
        if result.success:
            print(f"✅ Success using {result.pattern_used.value} pattern ({result.execution_time:.1f}s)")
            print(f"   Created agents: {', '.join(result.agents_created)}")
        else:
            print(f"❌ Failed: {result.error_message}")


async def interactive_demo():
    """Run interactive demo mode"""
    print("\n💬 Interactive Demo Mode")
    print("=" * 50)
    print("This will start an interactive session where you can try the autonomous system.")
    print("Type any task and watch the system automatically select tools and patterns!\n")
    
    orchestrator = AdaptiveOrchestrator()
    await orchestrator.interactive_mode()


async def capability_showcase():
    """Showcase specific autonomous capabilities"""
    print("\n🎯 Autonomous Capabilities Showcase")
    print("=" * 50)
    
    orchestrator = AdaptiveOrchestrator()
    await orchestrator.initialize()
    
    # Showcase tool discovery
    print("\n🔍 Tool Discovery Capabilities:")
    capabilities = orchestrator.get_available_capabilities()
    for category, tools in capabilities.items():
        print(f"  {category}: {len(tools)} tools available")
    
    # Showcase intelligent task analysis
    analysis_tasks = [
        "Simple task: read a file",
        "Moderate task: search and analyze information",
        "Complex task: coordinate multiple systems and generate comprehensive reports",
        "Advanced task: create an intelligent autonomous system that can adapt and learn"
    ]
    
    print("\n🧠 Task Analysis Capabilities:")
    for task in analysis_tasks:
        task_analysis, strategy = orchestrator.decision_engine.analyze_and_recommend(
            task, list(orchestrator.available_servers.values())
        )
        print(f"  '{task}' -> {task_analysis.complexity.name} complexity, {strategy.pattern.value} pattern")
    
    # Showcase agent specializations
    print("\n👥 Agent Specialization Capabilities:")
    specializations = orchestrator.agent_factory.get_available_specializations()
    for spec in specializations:
        info = orchestrator.agent_factory.get_specialization_info(spec)
        print(f"  {spec}: {info['capability_categories']}")


async def main():
    """Main demo function"""
    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    print("🤖 Autonomous MCP Agent - Complete Demo")
    print("=" * 60)
    print("This demo showcases the autonomous capabilities of mcp-agent.")
    print("The system will automatically discover tools, select patterns,")
    print("create specialized agents, and execute tasks without manual setup.\n")
    
    demos = [
        ("1. Basic Autonomous Examples", basic_autonomous_example),
        ("2. Detailed System Demo", detailed_autonomous_example), 
        ("3. Workflow Pattern Demo", workflow_pattern_demo),
        ("4. Capabilities Showcase", capability_showcase),
        ("5. Pre-built Demo", run_demo),
        ("6. Interactive Mode", interactive_demo)
    ]
    
    print("Available demos:")
    for title, _ in demos:
        print(f"  {title}")
    
    try:
        choice = input("\nSelect demo (1-6, or 'all' for everything): ").strip()
        
        if choice.lower() == 'all':
            # Run all demos except interactive
            for i, (title, demo_func) in enumerate(demos[:-1], 1):
                print(f"\n{'='*60}")
                print(f"Running Demo {i}: {title}")
                print('='*60)
                await demo_func()
                
                if i < len(demos) - 1:
                    input("\nPress Enter to continue to next demo...")
        
        elif choice in ['1', '2', '3', '4', '5', '6']:
            demo_index = int(choice) - 1
            title, demo_func = demos[demo_index]
            print(f"\n{'='*60}")
            print(f"Running: {title}")
            print('='*60)
            await demo_func()
        
        else:
            print("Invalid choice. Running basic demo...")
            await basic_autonomous_example()
    
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user.")
    except Exception as e:
        print(f"\nDemo error: {str(e)}")
    
    print("\n🎉 Demo complete! The autonomous MCP agent is ready for production use.")
    print("\nKey features demonstrated:")
    print("  ✅ Automatic tool discovery and installation")
    print("  ✅ Intelligent workflow pattern selection")  
    print("  ✅ Dynamic agent specialization")
    print("  ✅ Autonomous task execution")
    print("  ✅ Multi-pattern coordination")
    print("\nTo use in your own projects:")
    print("  from mcp_agent.autonomous import execute_task")
    print("  result = await execute_task('your task description here')")


if __name__ == "__main__":
    asyncio.run(main())
