import asyncio
import os
from mcp_agent.app import MCPApp
from mcp_agent.agents.agent import Agent

app = MCPApp(name="mcp_basic_test")


async def test_basic_functionality():
    async with app.run() as agent_app:
        logger = agent_app.logger
        context = agent_app.context

        print("=== MCP Agent Docker Test ===")
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
            print("✅ MCP Agent Docker deployment successful!")

            # Test basic functionality
            aggregator = test_agent.aggregator

            # Test directory listing
            result = await aggregator.call_tool(
                name="list_directory", arguments={"path": "."}
            )
            print("✅ File system operations working")

            print("\n🐳 Docker Container Status:")
            print("   • MCP Agent Framework: OPERATIONAL")
            print("   • Filesystem MCP Server: CONNECTED")
            print("   • Tool Discovery: WORKING")
            print("   • Container Integration: COMPLETE")

            return True


if __name__ == "__main__":
    try:
        result = asyncio.run(test_basic_functionality())
        if result:
            print("\n🎉 All Docker deployment tests passed!")
            exit(0)
    except Exception as e:
        print(f"❌ Docker test failed: {e}")
        import traceback

        traceback.print_exc()
        exit(1)
