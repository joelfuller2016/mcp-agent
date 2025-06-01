"""
Autonomous MCP Tool Discovery System

This module provides intelligent discovery and mapping of available MCP servers,
their capabilities, and optimal usage patterns for autonomous agent coordination.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, field
from enum import Enum
import json
from pathlib import Path

from ..mcp.mcp_connection_manager import MCPConnectionManager
from ..config import Settings
from .tool_capability_mapper import ToolCapabilityMapper, ToolCategory, ToolCapability


class DiscoveryStatus(Enum):
    """Status of MCP tool discovery"""

    PENDING = "pending"
    DISCOVERING = "discovering"
    AVAILABLE = "available"
    ERROR = "error"
    INSTALLED = "installed"


@dataclass
class MCPToolInfo:
    """Information about an discovered MCP tool/server"""

    name: str
    server_type: str
    capabilities: List[ToolCapability]
    status: DiscoveryStatus
    connection_info: Dict[str, Any]
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    last_updated: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    security_level: str = "standard"
    description: Optional[str] = None
    version: Optional[str] = None


class AutonomousDiscovery:
    """
    Autonomous MCP Tool Discovery System

    Automatically discovers, analyzes, and manages MCP servers for optimal
    autonomous agent operation. Maintains a dynamic registry of capabilities
    and provides intelligent tool selection recommendations.
    """

    def __init__(self, config: Settings):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.capability_mapper = ToolCapabilityMapper()
        self.connection_manager = MCPConnectionManager(config)

        # Dynamic registry of discovered tools
        self.discovered_tools: Dict[str, MCPToolInfo] = {}
        self.capability_index: Dict[str, Set[str]] = {}

        # Performance tracking
        self.tool_performance: Dict[str, Dict[str, float]] = {}

        # Discovery settings
        self.auto_discovery_enabled = True
        self.discovery_interval = 300  # 5 minutes
        self.max_concurrent_discoveries = 5

    async def discover_available_tools(self) -> Dict[str, MCPToolInfo]:
        """
        Discover all available MCP tools in the environment

        Returns:
            Dictionary mapping tool names to their information
        """
        self.logger.info("Starting autonomous MCP tool discovery...")

        discovered = {}

        # Discover from configuration
        config_tools = await self._discover_from_config()
        discovered.update(config_tools)

        # Discover from environment
        env_tools = await self._discover_from_environment()
        discovered.update(env_tools)

        # Discover from common locations
        common_tools = await self._discover_from_common_locations()
        discovered.update(common_tools)

        # Update internal registry
        self.discovered_tools.update(discovered)

        # Build capability index
        await self._build_capability_index()

        self.logger.info(f"Discovery complete. Found {len(discovered)} MCP tools.")
        return discovered

    async def _discover_from_config(self) -> Dict[str, MCPToolInfo]:
        """Discover tools from existing configuration"""
        tools = {}

        if hasattr(self.config, "mcp") and hasattr(self.config.mcp, "servers"):
            for server_name, server_config in self.config.mcp.servers.items():
                try:
                    # Analyze server configuration
                    capabilities = await self.capability_mapper.analyze_server_config(
                        server_name, server_config
                    )

                    tool_info = MCPToolInfo(
                        name=server_name,
                        server_type="configured",
                        capabilities=capabilities,
                        status=DiscoveryStatus.AVAILABLE,
                        connection_info=server_config,
                        description=f"Configured MCP server: {server_name}",
                    )

                    tools[server_name] = tool_info

                except Exception as e:
                    self.logger.warning(
                        f"Error analyzing configured server {server_name}: {e}"
                    )

        return tools

    async def _discover_from_environment(self) -> Dict[str, MCPToolInfo]:
        """Discover tools from environment variables and system"""
        tools = {}

        # Check for common MCP environment patterns
        common_patterns = ["MCP_*_SERVER", "*_MCP_*", "MCP_SERVER_*"]

        # This would be expanded to actually scan environment
        # For now, return empty as it requires system-specific implementation

        return tools

    async def _discover_from_common_locations(self) -> Dict[str, MCPToolInfo]:
        """Discover tools from common installation locations"""
        tools = {}

        # Common MCP server locations
        common_locations = [
            "uvx",  # Python packages
            "npx",  # Node packages
            "~/.local/bin",  # Local installs
            "/usr/local/bin",  # System installs
        ]

        # Common MCP server names to look for
        common_servers = [
            "mcp-server-fetch",
            "mcp-server-filesystem",
            "mcp-server-git",
            "mcp-server-github",
            "mcp-server-sqlite",
            "mcp-server-postgres",
            "mcp-server-brave-search",
            "mcp-server-puppeteer",
        ]

        for server_name in common_servers:
            try:
                # Try to get info about the server
                capabilities = await self.capability_mapper.get_default_capabilities(
                    server_name
                )

                if capabilities:
                    tool_info = MCPToolInfo(
                        name=server_name,
                        server_type="discoverable",
                        capabilities=capabilities,
                        status=DiscoveryStatus.PENDING,
                        connection_info={"command": "uvx", "args": [server_name]},
                        description=f"Discoverable MCP server: {server_name}",
                    )

                    tools[server_name] = tool_info

            except Exception as e:
                self.logger.debug(f"Could not discover {server_name}: {e}")

        return tools

    async def _build_capability_index(self):
        """Build index of capabilities to tools for fast lookup"""
        self.capability_index.clear()

        for tool_name, tool_info in self.discovered_tools.items():
            for capability in tool_info.capabilities:
                capability_key = f"{capability.category}:{capability.subcategory}"

                if capability_key not in self.capability_index:
                    self.capability_index[capability_key] = set()

                self.capability_index[capability_key].add(tool_name)

    async def get_tools_for_capability(self, capability: str) -> List[MCPToolInfo]:
        """
        Get tools that provide a specific capability

        Args:
            capability: Capability string (e.g., "development:git", "search:web")

        Returns:
            List of tools that provide the capability
        """
        if capability not in self.capability_index:
            return []

        tool_names = self.capability_index[capability]
        return [
            self.discovered_tools[name]
            for name in tool_names
            if name in self.discovered_tools
        ]

    async def recommend_tools_for_task(
        self, task_description: str
    ) -> List[MCPToolInfo]:
        """
        Recommend optimal tools for a given task description

        Args:
            task_description: Natural language description of the task

        Returns:
            Ranked list of recommended tools
        """
        # Analyze task to extract required capabilities
        required_capabilities = await self.capability_mapper.analyze_task_requirements(
            task_description
        )

        # Find tools for each capability
        recommended_tools = {}

        for capability in required_capabilities:
            tools = await self.get_tools_for_capability(capability)

            for tool in tools:
                if tool.name not in recommended_tools:
                    recommended_tools[tool.name] = {
                        "tool": tool,
                        "capability_matches": 0,
                        "performance_score": self._get_performance_score(tool.name),
                    }

                recommended_tools[tool.name]["capability_matches"] += 1

        # Rank tools by capability matches and performance
        ranked_tools = sorted(
            recommended_tools.values(),
            key=lambda x: (x["capability_matches"], x["performance_score"]),
            reverse=True,
        )

        return [item["tool"] for item in ranked_tools]

    def _get_performance_score(self, tool_name: str) -> float:
        """Get performance score for a tool (0.0 to 1.0)"""
        if tool_name not in self.tool_performance:
            return 0.5  # Default neutral score

        metrics = self.tool_performance[tool_name]

        # Combine various performance metrics
        success_rate = metrics.get("success_rate", 0.5)
        avg_response_time = metrics.get("avg_response_time", 1.0)
        reliability = metrics.get("reliability", 0.5)

        # Normalize response time (lower is better)
        time_score = max(0.0, 1.0 - (avg_response_time / 10.0))

        # Weighted combination
        score = success_rate * 0.4 + time_score * 0.3 + reliability * 0.3
        return max(0.0, min(1.0, score))

    async def install_tool(self, tool_name: str) -> bool:
        """
        Install an MCP tool on demand

        Args:
            tool_name: Name of the tool to install

        Returns:
            True if installation successful
        """
        if tool_name not in self.discovered_tools:
            self.logger.warning(f"Tool {tool_name} not found in discovery registry")
            return False

        tool_info = self.discovered_tools[tool_name]

        if tool_info.status == DiscoveryStatus.INSTALLED:
            self.logger.info(f"Tool {tool_name} already installed")
            return True

        try:
            self.logger.info(f"Installing MCP tool: {tool_name}")

            # Update status
            tool_info.status = DiscoveryStatus.DISCOVERING

            # Attempt installation based on connection info
            if await self._perform_installation(tool_info):
                tool_info.status = DiscoveryStatus.INSTALLED
                self.logger.info(f"Successfully installed {tool_name}")
                return True
            else:
                tool_info.status = DiscoveryStatus.ERROR
                self.logger.error(f"Failed to install {tool_name}")
                return False

        except Exception as e:
            tool_info.status = DiscoveryStatus.ERROR
            self.logger.error(f"Error installing {tool_name}: {e}")
            return False

    async def _perform_installation(self, tool_info: MCPToolInfo) -> bool:
        """Perform the actual installation of an MCP tool"""

        # For now, this is a placeholder that would integrate with
        # package managers like uvx, npm, etc.

        connection_info = tool_info.connection_info

        if connection_info.get("command") == "uvx":
            # Would run: uvx install {tool_name}
            self.logger.info(f"Would install via uvx: {tool_info.name}")
            return True
        elif connection_info.get("command") == "npx":
            # Would run: npm install -g {tool_name}
            self.logger.info(f"Would install via npm: {tool_info.name}")
            return True

        return False

    async def update_performance_metrics(
        self, tool_name: str, response_time: float, success: bool
    ):
        """Update performance metrics for a tool"""

        if tool_name not in self.tool_performance:
            self.tool_performance[tool_name] = {
                "success_rate": 0.0,
                "avg_response_time": 0.0,
                "total_calls": 0,
                "successful_calls": 0,
                "reliability": 0.5,
            }

        metrics = self.tool_performance[tool_name]
        metrics["total_calls"] += 1

        if success:
            metrics["successful_calls"] += 1

        # Update success rate
        metrics["success_rate"] = metrics["successful_calls"] / metrics["total_calls"]

        # Update average response time (exponential moving average)
        alpha = 0.1  # Smoothing factor
        metrics["avg_response_time"] = (
            alpha * response_time + (1 - alpha) * metrics["avg_response_time"]
        )

        # Update reliability based on recent performance
        metrics["reliability"] = min(
            1.0, metrics["success_rate"] + (0.1 if response_time < 2.0 else -0.1)
        )

    async def get_tool_registry(self) -> Dict[str, Any]:
        """Get the complete tool registry for external access"""

        registry = {
            "tools": {},
            "capabilities": self.capability_index,
            "last_discovery": asyncio.get_event_loop().time(),
            "total_tools": len(self.discovered_tools),
        }

        for name, tool_info in self.discovered_tools.items():
            registry["tools"][name] = {
                "name": tool_info.name,
                "type": tool_info.server_type,
                "status": tool_info.status.value,
                "capabilities": [cap.to_dict() for cap in tool_info.capabilities],
                "performance": self.tool_performance.get(name, {}),
                "description": tool_info.description,
            }

        return registry

    async def start_continuous_discovery(self):
        """Start continuous discovery process"""
        self.auto_discovery_enabled = True

        async def discovery_loop():
            while self.auto_discovery_enabled:
                try:
                    await self.discover_available_tools()
                    await asyncio.sleep(self.discovery_interval)
                except Exception as e:
                    self.logger.error(f"Error in discovery loop: {e}")
                    await asyncio.sleep(60)  # Wait 1 minute on error

        # Start discovery loop in background
        asyncio.create_task(discovery_loop())
        self.logger.info("Started continuous MCP tool discovery")

    async def stop_continuous_discovery(self):
        """Stop continuous discovery process"""
        self.auto_discovery_enabled = False
        self.logger.info("Stopped continuous MCP tool discovery")
