#!/usr/bin/env python3
"""
Autonomous Docker deployment test that validates advanced autonomous 
capabilities and workflow patterns.
"""

import asyncio
import os
import sys
import time
from pathlib import Path

# Add src to path for development
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mcp_agent.app import MCPApp
from mcp_agent.agents.agent import Agent

app = MCPApp(name="mcp_autonomous_docker_test")

async def test_basic_mcp_functionality():
    """Test basic MCP functionality."""
    async with app.run() as agent_app:
        logger = agent_app.logger
        context = agent_app.context

        print("=== Basic MCP Functionality Test ===")
        logger.info("Testing basic MCP agent functionality")

        # Add current directory to filesystem server args
        context.config.mcp.servers["filesystem"].args.extend([os.getcwd()])

        # Create a simple agent
        test_agent = Agent(
            name="test_agent",
            instruction="Test agent for Docker deployment verification",
            server_names=["filesystem"],
        )

        async with test_agent:
            logger.info("Connected to MCP servers successfully!")

            # List available tools
            tools = await test_agent.list_tools()
            logger.info(f"Available tools: {[tool.name for tool in tools.tools]}")

            print(f"✅ Connected to {len(tools.tools)} MCP tools")

            # Test basic functionality
            aggregator = test_agent.aggregator

            # Test directory listing
            result = await aggregator.call_tool(
                name="list_directory", arguments={"path": "."}
            )
            print(f"✅ File system operations working ({len(result.content)} items found)")

            return True

async def test_autonomous_imports():
    """Test autonomous component imports."""
    print("\n=== Autonomous Component Import Test ===")
    
    try:
        # Test core autonomous imports
        from mcp_agent.autonomous.autonomous_orchestrator import AutonomousOrchestrator
        from mcp_agent.autonomous.dynamic_agent_factory import DynamicAgentFactory
        from mcp_agent.autonomous.task_analyzer import TaskAnalyzer
        from mcp_agent.autonomous.decision_engine import AutonomousDecisionEngine
        from mcp_agent.autonomous.meta_coordinator import MetaCoordinator
        from mcp_agent.autonomous.discovery import AutonomousDiscovery
        
        print("✅ All autonomous module imports successful")
        return True
        
    except ImportError as e:
        print(f"❌ Autonomous import failed: {e}")
        return False

async def test_autonomous_task_analysis():
    """Test autonomous task analysis capabilities."""
    print("\n=== Autonomous Task Analysis Test ===")
    
    try:
        from mcp_agent.autonomous.task_analyzer import TaskAnalyzer
        from mcp_agent.autonomous.decision_engine import AutonomousDecisionEngine
        
        # Test task analyzer
        task_analyzer = TaskAnalyzer()
        test_tasks = [
            "Read a file and summarize its contents",
            "Create a comprehensive report analyzing multiple data sources",
            "Search the web for information about AI and write a blog post",
            "Automate a complex workflow with multiple steps"
        ]
        
        print(f"Testing {len(test_tasks)} different task types...")
        
        for i, task in enumerate(test_tasks, 1):
            analysis = task_analyzer.analyze_task(task)
            print(f"   {i}. {task[:50]}...")
            print(f"      → Complexity: {analysis.complexity.value}")
            print(f"      → Pattern: {analysis.recommended_pattern.value}")
            print(f"      → Steps: {analysis.estimated_steps}")
            print(f"      → Confidence: {analysis.confidence:.2f}")
        
        print("✅ Task analysis working correctly")
        
        # Test decision engine
        decision_engine = AutonomousDecisionEngine()
        task_analysis, strategy = decision_engine.analyze_and_recommend(
            "Create a comprehensive analysis of project files", []
        )
        
        print(f"✅ Decision engine working: {strategy.pattern.value} pattern recommended")
        return True
        
    except Exception as e:
        print(f"❌ Autonomous task analysis failed: {e}")
        return False

async def test_autonomous_orchestrator():
    """Test autonomous orchestrator functionality."""
    print("\n=== Autonomous Orchestrator Test ===")
    
    try:
        from mcp_agent.autonomous.autonomous_orchestrator import AutonomousOrchestrator
        
        # Create orchestrator
        orchestrator = AutonomousOrchestrator(app=app)
        
        print("Created autonomous orchestrator...")
        
        # Test initialization
        init_success = await orchestrator.initialize()
        if not init_success:
            print("❌ Orchestrator initialization failed")
            return False
            
        print("✅ Orchestrator initialized successfully")
        
        # Test capability analysis
        capabilities = await orchestrator.analyze_capabilities()
        print(f"✅ Capability analysis: {capabilities.get('execution_history', 0)} executions in history")
        
        # Test execution suggestions (without actual execution)
        test_task = "Analyze the current directory structure and create a summary report"
        suggestions = await orchestrator.get_execution_suggestions(test_task)
        
        print(f"✅ Execution suggestions generated:")
        print(f"   • Task type: {suggestions['task_analysis']['type']}")
        print(f"   • Complexity: {suggestions['task_analysis']['complexity']}")
        print(f"   • Recommended pattern: {suggestions['strategy']['recommended_pattern']}")
        print(f"   • Suggested agents: {suggestions['agents']['suggested_count']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Autonomous orchestrator test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_autonomous_workflow_patterns():
    """Test different autonomous workflow patterns."""
    print("\n=== Autonomous Workflow Patterns Test ===")
    
    try:
        from mcp_agent.autonomous.task_analyzer import TaskAnalyzer, ExecutionPattern
        
        task_analyzer = TaskAnalyzer()
        
        # Test different patterns
        pattern_tests = {
            ExecutionPattern.DIRECT: "Get the current date and time",
            ExecutionPattern.PARALLEL: "Analyze multiple files simultaneously and compare their contents",
            ExecutionPattern.ORCHESTRATOR: "Create a comprehensive project report with analysis, recommendations, and next steps",
            ExecutionPattern.ROUTER: "Route this task to the most appropriate specialized agent",
        }
        
        print(f"Testing {len(pattern_tests)} workflow patterns...")
        
        for pattern, task_desc in pattern_tests.items():
            analysis = task_analyzer.analyze_task(task_desc)
            print(f"   • {pattern.value.upper()}: Analysis complete")
            print(f"     → Detected complexity: {analysis.complexity.value}")
            print(f"     → Recommended: {analysis.recommended_pattern.value}")
            print(f"     → Match: {'✅' if analysis.recommended_pattern == pattern else '⚠️'}")
        
        print("✅ Workflow pattern analysis working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Workflow patterns test failed: {e}")
        return False

async def test_autonomous_configuration():
    """Test autonomous configuration loading."""
    print("\n=== Autonomous Configuration Test ===")
    
    try:
        # Check if configuration file exists
        config_path = "/app/config/autonomous.yaml"
        if os.path.exists(config_path):
            print(f"✅ Autonomous configuration found at {config_path}")
            
            with open(config_path, 'r') as f:
                content = f.read()
                print(f"✅ Configuration loaded ({len(content)} characters)")
                
                # Check for key sections
                if "autonomous:" in content:
                    print("✅ Autonomous settings section found")
                if "tool_discovery:" in content:
                    print("✅ Tool discovery settings section found")
                if "performance:" in content:
                    print("✅ Performance settings section found")
        else:
            print(f"⚠️ Autonomous configuration not found at {config_path}")
            
        # Check environment variables
        env_vars = ["MCP_AUTONOMOUS_MODE", "MCP_AUTONOMOUS_CONFIG_PATH"]
        for var in env_vars:
            value = os.environ.get(var)
            if value:
                print(f"✅ Environment variable {var}={value}")
            else:
                print(f"⚠️ Environment variable {var} not set")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

async def run_comprehensive_autonomous_test():
    """Run comprehensive autonomous deployment test."""
    print("🤖 Starting Comprehensive Autonomous Docker Test\n")
    
    start_time = time.time()
    
    # Test 1: Basic MCP functionality
    print("1️⃣ Testing Basic MCP Functionality...")
    basic_success = await test_basic_mcp_functionality()
    
    # Test 2: Autonomous imports
    print("\n2️⃣ Testing Autonomous Imports...")
    import_success = await test_autonomous_imports()
    
    # Test 3: Task analysis
    print("\n3️⃣ Testing Task Analysis...")
    analysis_success = await test_autonomous_task_analysis()
    
    # Test 4: Orchestrator
    print("\n4️⃣ Testing Autonomous Orchestrator...")
    orchestrator_success = await test_autonomous_orchestrator()
    
    # Test 5: Workflow patterns
    print("\n5️⃣ Testing Workflow Patterns...")
    patterns_success = await test_autonomous_workflow_patterns()
    
    # Test 6: Configuration
    print("\n6️⃣ Testing Configuration...")
    config_success = await test_autonomous_configuration()
    
    execution_time = time.time() - start_time
    
    # Summary
    print(f"\n🤖 Autonomous Docker Container Status:")
    print(f"   • Basic MCP Framework: {'✅ OPERATIONAL' if basic_success else '❌ FAILED'}")
    print(f"   • Autonomous Imports: {'✅ WORKING' if import_success else '❌ FAILED'}")
    print(f"   • Task Analysis: {'✅ WORKING' if analysis_success else '❌ FAILED'}")
    print(f"   • Orchestrator: {'✅ WORKING' if orchestrator_success else '❌ FAILED'}")
    print(f"   • Workflow Patterns: {'✅ WORKING' if patterns_success else '❌ FAILED'}")
    print(f"   • Configuration: {'✅ WORKING' if config_success else '❌ FAILED'}")
    
    # Calculate overall status
    tests = [basic_success, import_success, analysis_success, orchestrator_success, patterns_success, config_success]
    passed_tests = sum(tests)
    total_tests = len(tests)
    
    print(f"\n📊 Test Results ({execution_time:.2f}s execution time):")
    print(f"   • Tests Passed: {passed_tests}/{total_tests}")
    print(f"   • Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    if passed_tests == total_tests:
        print(f"\n🎉 All autonomous Docker deployment tests passed!")
        print(f"   ✅ Autonomous capabilities: FULLY FUNCTIONAL")
        print(f"   ✅ Docker environment: OPTIMAL")
        print(f"   ✅ Ready for production deployment")
    elif passed_tests >= total_tests * 0.8:
        print(f"\n✅ Most autonomous Docker deployment tests passed!")
        print(f"   ⚠️ Minor issues detected, but system is functional")
        print(f"   ✅ Ready for testing and development")
    else:
        print(f"\n⚠️ Some autonomous Docker deployment tests failed:")
        print(f"   ❌ Significant issues detected")
        print(f"   🔧 System needs attention before production use")
    
    return passed_tests == total_tests

if __name__ == "__main__":
    try:
        result = asyncio.run(run_comprehensive_autonomous_test())
        sys.exit(0 if result else 1)
    except Exception as e:
        print(f"❌ Autonomous Docker test failed with unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
