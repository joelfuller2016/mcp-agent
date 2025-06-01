"""
Test suite for Enhanced MCP Discovery and Auto-Installation System
"""

import asyncio
import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from mcp_agent.autonomous.enhanced_mcp_discovery import (
    EnhancedMCPDiscovery,
    MCPServerSpec,
    ServerCategory,
    ServerInstallMethod,
    InstallationResult
)


class TestEnhancedMCPDiscovery:
    """Test cases for Enhanced MCP Discovery system."""

    @pytest.fixture
    async def discovery_system(self):
        """Create a test discovery system."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir)
            discovery = EnhancedMCPDiscovery(config_dir=config_dir)
            yield discovery

    @pytest.mark.asyncio
    async def test_initialization(self, discovery_system):
        """Test system initialization."""
        discovery = discovery_system
        
        # Check that built-in servers are loaded
        assert len(discovery.server_registry) > 0
        assert "fetch" in discovery.server_registry
        assert "filesystem" in discovery.server_registry
        assert "github" in discovery.server_registry
        
        # Check configuration directory creation
        assert discovery.config_dir.exists()

    @pytest.mark.asyncio
    async def test_server_discovery(self, discovery_system):
        """Test server discovery functionality."""
        discovery = discovery_system
        
        # Mock discovery methods
        with patch.object(discovery, '_discover_from_registry') as mock_registry, \
             patch.object(discovery, '_discover_from_github') as mock_github, \
             patch.object(discovery, '_discover_from_npm') as mock_npm, \
             patch.object(discovery, '_discover_local_servers') as mock_local:
            
            # Set up mock returns
            mock_registry.return_value = list(discovery.server_registry.values())
            mock_github.return_value = []
            mock_npm.return_value = []
            mock_local.return_value = []
            
            discovered_servers = await discovery.discover_available_servers()
            
            # Verify all discovery methods were called
            mock_registry.assert_called_once()
            mock_github.assert_called_once()
            mock_npm.assert_called_once()
            mock_local.assert_called_once()
            
            # Check results
            assert len(discovered_servers) >= 5  # At least our built-in servers
            assert discovery.discovery_metrics["total_discoveries"] == 1

    @pytest.mark.asyncio
    async def test_task_recommendation(self, discovery_system):
        """Test server recommendation for tasks."""
        discovery = discovery_system
        
        # Test file operation task
        file_task = "Read a CSV file and analyze the data"
        recommendations = await discovery.recommend_servers_for_task(file_task, max_recommendations=3)
        
        assert len(recommendations) > 0
        # Should recommend filesystem server for file operations
        server_names = [server.name for server in recommendations]
        assert "filesystem" in server_names
        
        # Test web search task
        search_task = "Search for information about Python programming"
        recommendations = await discovery.recommend_servers_for_task(search_task, max_recommendations=3)
        
        assert len(recommendations) > 0
        # Should recommend web search servers
        categories = [server.category for server in recommendations]
        assert ServerCategory.WEB_SEARCH in categories

    @pytest.mark.asyncio
    async def test_compatibility_scoring(self, discovery_system):
        """Test task-server compatibility scoring."""
        discovery = discovery_system
        
        # Create test server spec
        test_server = MCPServerSpec(
            name="test_server",
            description="Test server for file operations",
            category=ServerCategory.FILE_OPERATIONS,
            install_method=ServerInstallMethod.NPX,
            install_command="npx test-server",
            capabilities={"file_read", "file_write"},
            tools=["read_file", "write_file"],
            priority_score=5.0
        )
        
        # Test scoring for matching task
        matching_task = "read file contents and write to another file"
        score = discovery._calculate_task_compatibility_score(matching_task, test_server)
        assert score > 5.0  # Should be higher than base priority
        
        # Test scoring for non-matching task
        non_matching_task = "search the web for information"
        score = discovery._calculate_task_compatibility_score(non_matching_task, test_server)
        assert score <= 5.0  # Should be base priority or lower

    @pytest.mark.asyncio
    async def test_installation_validation(self, discovery_system):
        """Test installation method validation."""
        discovery = discovery_system
        
        # Mock subprocess calls
        with patch('asyncio.create_subprocess_exec') as mock_subprocess:
            # Mock successful validation
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (b"v1.0.0", b"")
            mock_process.returncode = 0
            mock_subprocess.return_value = mock_process
            
            # Test NPX validation
            result = await discovery._validate_install_method(ServerInstallMethod.NPX)
            assert result is True
            
            # Mock failed validation
            mock_process.returncode = 1
            result = await discovery._validate_install_method(ServerInstallMethod.NPX)
            assert result is False

    @pytest.mark.asyncio
    async def test_auto_installation(self, discovery_system):
        """Test automatic server installation."""
        discovery = discovery_system
        
        # Create test server spec
        test_server = MCPServerSpec(
            name="test_install_server",
            description="Test server for installation",
            category=ServerCategory.FILE_OPERATIONS,
            install_method=ServerInstallMethod.NPX,
            install_command="npx test-install-server",
            auto_install=True
        )
        
        # Mock installation methods
        with patch.object(discovery, '_validate_install_method') as mock_validate, \
             patch.object(discovery, '_execute_install_command') as mock_install, \
             patch.object(discovery, '_generate_server_config') as mock_config:
            
            mock_validate.return_value = True
            mock_install.return_value = None
            mock_config.return_value = None
            
            # Test successful installation
            result = await discovery.auto_install_server(test_server)
            
            assert result.success is True
            assert result.server_name == "test_install_server"
            assert result.install_time_ms > 0
            assert discovery.discovery_metrics["successful_installs"] == 1
            
            # Verify server is marked as installed
            assert test_server.name in discovery.installed_servers

    @pytest.mark.asyncio
    async def test_installation_failure(self, discovery_system):
        """Test installation failure handling."""
        discovery = discovery_system
        
        # Create test server spec
        test_server = MCPServerSpec(
            name="failing_server",
            description="Server that fails to install",
            category=ServerCategory.FILE_OPERATIONS,
            install_method=ServerInstallMethod.NPX,
            install_command="npx failing-server"
        )
        
        # Mock installation failure
        with patch.object(discovery, '_validate_install_method') as mock_validate, \
             patch.object(discovery, '_execute_install_command') as mock_install:
            
            mock_validate.return_value = True
            mock_install.side_effect = Exception("Installation failed")
            
            # Test failed installation
            result = await discovery.auto_install_server(test_server)
            
            assert result.success is False
            assert result.error_message == "Installation failed"
            assert discovery.discovery_metrics["failed_installs"] == 1

    @pytest.mark.asyncio
    async def test_config_generation(self, discovery_system):
        """Test configuration file generation."""
        discovery = discovery_system
        
        # Create server spec with config requirements
        test_server = MCPServerSpec(
            name="config_server",
            description="Server requiring configuration",
            category=ServerCategory.CLOUD_SERVICES,
            install_method=ServerInstallMethod.NPX,
            install_command="npx config-server",
            config_template={"port": 3000, "host": "localhost"},
            required_config=["API_KEY", "SECRET_TOKEN"],
            environment_vars={"NODE_ENV": "production"}
        )
        
        # Test config generation
        config_path = await discovery._generate_server_config(test_server)
        
        assert config_path is not None
        assert config_path.exists()
        
        # Verify config content
        with open(config_path) as f:
            config = json.load(f)
        
        assert config["port"] == 3000
        assert config["host"] == "localhost"
        assert "API_KEY" in config
        assert "SECRET_TOKEN" in config
        assert config["environment"]["NODE_ENV"] == "production"

    @pytest.mark.asyncio
    async def test_installation_status(self, discovery_system):
        """Test installation status reporting."""
        discovery = discovery_system
        
        # Add some mock installation results
        discovery.installed_servers["server1"] = InstallationResult(
            server_name="server1",
            success=True,
            install_time_ms=150.0
        )
        discovery.installed_servers["server2"] = InstallationResult(
            server_name="server2",
            success=False,
            install_time_ms=75.0,
            error_message="Installation failed"
        )
        
        # Update metrics
        discovery.discovery_metrics["successful_installs"] = 1
        discovery.discovery_metrics["failed_installs"] = 1
        
        # Get status
        status = await discovery.get_installation_status()
        
        assert status["total_installed"] == 2
        assert status["successful_installs"] == 1
        assert status["failed_installs"] == 1
        assert status["success_rate"] == 50.0
        assert status["avg_install_time_ms"] == 112.5
        assert "server1" in status["installed_servers"]
        assert "server2" in status["installed_servers"]

    @pytest.mark.asyncio
    async def test_health_check(self, discovery_system):
        """Test server health checking."""
        discovery = discovery_system
        
        # Add mock installations
        discovery.installed_servers["healthy_server"] = InstallationResult(
            server_name="healthy_server",
            success=True,
            install_time_ms=100.0
        )
        discovery.installed_servers["unhealthy_server"] = InstallationResult(
            server_name="unhealthy_server",
            success=False,
            install_time_ms=50.0,
            error_message="Failed"
        )
        
        # Test health check
        health_status = await discovery.health_check_servers()
        
        assert "healthy_server" in health_status
        assert "unhealthy_server" in health_status
        assert health_status["unhealthy_server"] is False

    def test_recommendation_summary(self, discovery_system):
        """Test recommendation summary generation."""
        discovery = discovery_system
        
        # Test summary generation
        task = "Read files and search the web"
        summary = discovery.get_server_recommendations_summary(task)
        
        assert isinstance(summary, str)
        assert len(summary) > 0
        assert "Recommended MCP servers" in summary
        assert "filesystem" in summary or "fetch" in summary


# Performance benchmark test
@pytest.mark.asyncio
async def test_discovery_performance():
    """Test discovery system performance."""
    with tempfile.TemporaryDirectory() as temp_dir:
        config_dir = Path(temp_dir)
        discovery = EnhancedMCPDiscovery(config_dir=config_dir)
        
        # Mock discovery to avoid network calls
        with patch.object(discovery, '_discover_from_github') as mock_github, \
             patch.object(discovery, '_discover_from_npm') as mock_npm, \
             patch.object(discovery, '_discover_local_servers') as mock_local:
            
            mock_github.return_value = []
            mock_npm.return_value = []
            mock_local.return_value = []
            
            # Measure discovery performance
            import time
            start_time = time.perf_counter()
            
            await discovery.discover_available_servers()
            
            discovery_time = (time.perf_counter() - start_time) * 1000
            
            # Should complete discovery quickly
            assert discovery_time < 1000  # Less than 1 second
            
            # Test recommendation performance
            start_time = time.perf_counter()
            
            recommendations = await discovery.recommend_servers_for_task(
                "Create files and search for information online"
            )
            
            recommendation_time = (time.perf_counter() - start_time) * 1000
            
            # Should complete recommendations quickly
            assert recommendation_time < 100  # Less than 100ms
            assert len(recommendations) > 0


if __name__ == "__main__":
    # Run basic tests
    async def run_basic_tests():
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir)
            discovery = EnhancedMCPDiscovery(config_dir=config_dir)
            
            print("Testing Enhanced MCP Discovery System...")
            
            # Test initialization
            print(f"✅ Initialized with {len(discovery.server_registry)} built-in servers")
            
            # Test discovery
            discovered = await discovery.discover_available_servers()
            print(f"✅ Discovered {len(discovered)} servers")
            
            # Test recommendations
            task = "Read a CSV file and create a summary report"
            recommendations = await discovery.recommend_servers_for_task(task)
            print(f"✅ Generated {len(recommendations)} recommendations for: '{task}'")
            
            # Test status
            status = await discovery.get_installation_status()
            print(f"✅ Status: {status['total_servers_available']} servers available")
            
            print("\n🎉 All basic tests passed!")
    
    asyncio.run(run_basic_tests())
