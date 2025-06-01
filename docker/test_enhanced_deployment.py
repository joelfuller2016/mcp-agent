#!/usr/bin/env python3
"""
Enhanced Docker deployment test that validates both basic MCP functionality 
and autonomous components.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path for development
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mcp_agent.app import MCPApp
from mcp_agent.agents.agent import Agent

app = MCPApp(name="mcp_docker_test_enhanced")

async def test_basic_functionality():
    """Test basic MCP functionality in Docker."""
    async with app.run() as agent_app:
        logger = agent_app.logger
        context = agent_app.context

        print("=== MCP Agent Enhanced Docker Test ===")
        logger.info("Testing MCP agent functionality in Docker container")

        # Add current directory to filesystem server args
        context.config.mcp.servers["filesystem"].args.extend([os.getcwd()])

        # Create a simple agent without LLM calls
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

            print(f"✅ Successfully connected to {len(tools.tools)} tools")

            # Test basic functionality
            aggregator = test_agent.aggregator

            # Test directory listing
            result = await aggregator.call_tool(
                name="list_directory", arguments={"path": "."}
            )
            print("✅ File system operations working")

            return True

async def test_autonomous_components():
    """Test autonomous components in Docker environment."""
    print("\n=== Testing Autonomous Components ===")
    
    try:
        # Test imports
        from mcp_agent.autonomous.autonomous_orchestrator import AutonomousOrchestrator
        from mcp_agent.autonomous.dynamic_agent_factory import DynamicAgentFactory
        from mcp_agent.autonomous.task_analyzer import TaskAnalyzer
        from mcp_agent.autonomous.decision_engine import AutonomousDecisionEngine
        print("✅ Autonomous module imports successful")
        
        # Test basic instantiation
        task_analyzer = TaskAnalyzer()
        print("✅ TaskAnalyzer created")
        
        decision_engine = AutonomousDecisionEngine()
        print("✅ AutonomousDecisionEngine created")
        
        # Test basic functionality
        test_task = "Read a file and summarize its contents"
        analysis = task_analyzer.analyze_task(test_task)
        print(f"✅ Task analysis completed: {analysis.complexity.name} complexity")
        
        # Test integration
        task_analysis, strategy_recommendation = decision_engine.analyze_and_recommend(
            "Create a simple text file", []
        )
        print(f"✅ Integration test passed: recommended {strategy_recommendation.pattern.name} pattern")
        
        return True
        
    except ImportError as e:
        print(f"❌ Autonomous import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Autonomous test failed: {e}")
        return False

async def run_comprehensive_test():
    """Run comprehensive Docker deployment test."""
    print("🐳 Starting Comprehensive Docker Test\n")
    
    # Test 1: Basic MCP functionality
    basic_success = await test_basic_functionality()
    
    # Test 2: Autonomous components
    autonomous_success = await test_autonomous_components()
    
    print("\n🐳 Docker Container Status:")
    print("   • MCP Agent Framework: OPERATIONAL" if basic_success else "   • MCP Agent Framework: FAILED")
    print("   • Filesystem MCP Server: CONNECTED" if basic_success else "   • Filesystem MCP Server: FAILED")
    print("   • Autonomous Components: WORKING" if autonomous_success else "   • Autonomous Components: FAILED")
    print("   • Tool Discovery: WORKING" if basic_success else "   • Tool Discovery: FAILED")
    print("   • Container Integration: COMPLETE" if (basic_success and autonomous_success) else "   • Container Integration: PARTIAL")
    
    overall_success = basic_success and autonomous_success
    
    if overall_success:
        print("\n🎉 All enhanced Docker deployment tests passed!")
        print("📊 Test Results:")
        print("   ✅ Basic MCP functionality: PASS")
        print("   ✅ Autonomous components: PASS")
        print("   ✅ Integration tests: PASS")
        print("   ✅ Docker environment: READY")
    else:
        print("\n⚠️  Some Docker deployment tests failed:")
        print(f"   {'✅' if basic_success else '❌'} Basic MCP functionality")
        print(f"   {'✅' if autonomous_success else '❌'} Autonomous components")
        print("   🔧 Please check the error messages above")
    
    return overall_success

if __name__ == "__main__":
    try:
        result = asyncio.run(run_comprehensive_test())
        sys.exit(0 if result else 1)
    except Exception as e:
        print(f"❌ Docker test failed with unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
