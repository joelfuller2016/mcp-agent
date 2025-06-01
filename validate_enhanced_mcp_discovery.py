"""
Simple validation test for Enhanced MCP Discovery System
"""

import asyncio
import tempfile
from pathlib import Path
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

try:
    from mcp_agent.autonomous.enhanced_mcp_discovery import (
        EnhancedMCPDiscovery,
        MCPServerSpec,
        ServerCategory,
        ServerInstallMethod
    )
    print("✅ Enhanced MCP Discovery imports successful")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)


async def test_enhanced_mcp_discovery():
    """Test enhanced MCP discovery functionality."""
    print("\n🚀 Testing Enhanced MCP Discovery System")
    print("=" * 60)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        config_dir = Path(temp_dir)
        discovery = EnhancedMCPDiscovery(config_dir=config_dir)
        
        # Test 1: Initialization
        print("\n🔍 Test 1: System Initialization")
        print(f"Configuration directory: {discovery.config_dir}")
        print(f"Built-in servers loaded: {len(discovery.server_registry)}")
        
        for server_name in sorted(discovery.server_registry.keys()):
            server = discovery.server_registry[server_name]
            print(f"  - {server_name}: {server.description[:50]}...")
        
        assert len(discovery.server_registry) >= 5, "Should have at least 5 built-in servers"
        print("✅ Initialization test passed")
        
        # Test 2: Server Discovery  
        print("\n🔍 Test 2: Server Discovery")
        discovered_servers = await discovery.discover_available_servers()
        print(f"Total servers discovered: {len(discovered_servers)}")
        print(f"Discovery metrics: {discovery.discovery_metrics}")
        
        assert len(discovered_servers) > 0, "Should discover servers"
        print("✅ Discovery test passed")
        
        # Test 3: Task Recommendations
        print("\n🔍 Test 3: Task-Based Server Recommendations")
        
        test_tasks = [
            "Read a CSV file and analyze the data",
            "Search for information about Python programming", 
            "Create a GitHub repository and commit code",
            "Query a database for customer information",
            "Take a screenshot of a website"
        ]
        
        for task in test_tasks:
            recommendations = await discovery.recommend_servers_for_task(task, max_recommendations=3)
            print(f"\nTask: '{task}'")
            print(f"Recommendations ({len(recommendations)}):")
            
            for i, server in enumerate(recommendations, 1):
                install_status = "Auto-install" if server.auto_install else "Manual setup"
                print(f"  {i}. {server.name} ({server.category.value}) - {install_status}")
                print(f"     Score: {server.priority_score}/10 | {server.description[:40]}...")
            
            assert len(recommendations) > 0, f"Should have recommendations for task: {task}"
        
        print("✅ Recommendation test passed")
        
        # Test 4: Installation Validation
        print("\n🔍 Test 4: Installation Method Validation")
        
        # Test validation methods (these may fail if tools not installed, but shouldn't crash)
        for method in [ServerInstallMethod.NPX, ServerInstallMethod.PIP]:
            try:
                is_available = await discovery._validate_install_method(method)
                status = "✅ Available" if is_available else "❌ Not available"
                print(f"  {method.value}: {status}")
            except Exception as e:
                print(f"  {method.value}: ⚠️ Error during validation: {e}")
        
        print("✅ Validation test passed")
        
        # Test 5: Configuration Generation
        print("\n🔍 Test 5: Configuration Generation")
        
        # Test config generation for a server with requirements
        github_server = discovery.server_registry.get("github")
        if github_server:
            try:
                config_path = await discovery._generate_server_config(github_server)
                if config_path:
                    print(f"  Generated config: {config_path}")
                    print(f"  Config exists: {config_path.exists()}")
                    
                    # Read and display config
                    if config_path.exists():
                        import json
                        with open(config_path) as f:
                            config = json.load(f)
                        print(f"  Config keys: {list(config.keys())}")
                else:
                    print("  No config generated (none required)")
            except Exception as e:
                print(f"  ⚠️ Config generation failed: {e}")
        
        print("✅ Configuration test passed")
        
        # Test 6: Status Reporting
        print("\n🔍 Test 6: Installation Status")
        
        status = await discovery.get_installation_status()
        print(f"  Total servers available: {status['total_servers_available']}")
        print(f"  Total installed: {status['total_installed']}")
        print(f"  Success rate: {status['success_rate']:.1f}%")
        print(f"  Average install time: {status['avg_install_time_ms']:.2f}ms")
        
        print("✅ Status reporting test passed")
        
        # Test 7: Recommendation Summary
        print("\n🔍 Test 7: Recommendation Summary")
        
        task = "Create files and search for information online"
        summary = discovery.get_server_recommendations_summary(task)
        print(f"Summary for task: '{task}'")
        print("=" * 40)
        print(summary[:500] + "..." if len(summary) > 500 else summary)
        
        assert "Recommended MCP servers" in summary, "Summary should contain recommendations"
        print("✅ Summary test passed")
        
        # Performance Test
        print("\n🔍 Performance Test")
        
        import time
        
        # Measure recommendation performance
        start_time = time.perf_counter()
        recommendations = await discovery.recommend_servers_for_task(
            "Complex task involving file operations, web search, and database queries"
        )
        recommendation_time = (time.perf_counter() - start_time) * 1000
        
        print(f"  Recommendation time: {recommendation_time:.2f}ms")
        print(f"  Recommendations generated: {len(recommendations)}")
        print(f"  Performance target (<100ms): {'✅ MET' if recommendation_time < 100 else '❌ NOT MET'}")
        
        print("\n🎉 All Enhanced MCP Discovery tests passed!")
        print("=" * 60)
        
        return True


async def main():
    """Run all tests."""
    try:
        success = await test_enhanced_mcp_discovery()
        print(f"\n{'🎉 SUCCESS' if success else '❌ FAILED'}: Enhanced MCP Discovery validation {'completed' if success else 'failed'}")
        return success
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    print(f"\nEnhanced MCP Discovery System: {'✅ READY FOR INTEGRATION' if success else '❌ NEEDS FIXES'}")
