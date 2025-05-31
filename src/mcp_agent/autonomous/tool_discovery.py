"""
Tool Discovery Agent for autonomous MCP server discovery and capability mapping.

This agent automatically discovers available MCP servers, maps their capabilities,
and maintains a registry for intelligent tool selection.
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Set, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

from ..agents.agent import Agent
from ..workflows.llm.augmented_llm import AugmentedLLM
from ..mcp.mcp_connection_manager import MCPConnectionManager


class ToolCapability(Enum):
    """Categories of tool capabilities."""
    FILE_OPERATIONS = "file_operations"
    WEB_SEARCH = "web_search"
    DATABASE = "database"
    AUTOMATION = "automation"
    DEVELOPMENT = "development"
    COMMUNICATION = "communication"
    ANALYSIS = "analysis"
    REASONING = "reasoning"
    WORKFLOW = "workflow"
    SYSTEM = "system"
    GRAPHICS = "graphics"
    DATA_PROCESSING = "data_processing"


@dataclass
class MCPServerInfo:
    """Information about an MCP server and its capabilities."""
    name: str
    description: str
    capabilities: Set[ToolCapability] = field(default_factory=set)
    tools: List[str] = field(default_factory=list)
    resources: List[str] = field(default_factory=list)
    connection_status: str = "unknown"
    install_command: Optional[str] = None
    config_required: bool = False
    priority_score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class ToolDiscoveryAgent:
    """Agent that discovers and maps MCP server capabilities."""
    
    def __init__(self, connection_manager: MCPConnectionManager):
        self.connection_manager = connection_manager
        self.logger = logging.getLogger(__name__)
        self.discovered_servers: Dict[str, MCPServerInfo] = {}
        self.capability_map: Dict[ToolCapability, List[str]] = {
            cap: [] for cap in ToolCapability
        }
        
    async def discover_available_servers(self) -> Dict[str, MCPServerInfo]:
        """Discover all available MCP servers from various sources."""
        self.logger.info("Starting MCP server discovery...")
        
        # Discover from connected servers
        await self._discover_connected_servers()
        
        # Discover from MCP registries and marketplaces
        await self._discover_from_registries()
        
        # Build capability map
        self._build_capability_map()
        
        self.logger.info(f"Discovered {len(self.discovered_servers)} MCP servers")
        return self.discovered_servers
    
    async def _discover_connected_servers(self) -> None:
        """Discover servers that are currently connected."""
        connected_servers = await self.connection_manager.list_connected_servers()
        
        for server_name in connected_servers:
            try:
                # Get server information
                tools = await self.connection_manager.list_tools(server_name)
                resources = await self.connection_manager.list_resources(server_name)
                
                # Analyze capabilities
                capabilities = self._analyze_server_capabilities(tools, resources)
                
                server_info = MCPServerInfo(
                    name=server_name,
                    description=f"Connected MCP server: {server_name}",
                    capabilities=capabilities,
                    tools=[tool.name for tool in tools],
                    resources=[res.name for res in resources],
                    connection_status="connected",
                    priority_score=1.0  # Higher priority for connected servers
                )
                
                self.discovered_servers[server_name] = server_info
                self.logger.debug(f"Analyzed connected server: {server_name}")
                
            except Exception as e:
                self.logger.warning(f"Failed to analyze server {server_name}: {e}")
    
    async def _discover_from_registries(self) -> None:
        """Discover servers from MCP registries and marketplaces."""
        # Known MCP server patterns and their capabilities
        known_servers = {
            "fetch": {
                "description": "Web fetching and URL operations",
                "capabilities": {ToolCapability.WEB_SEARCH, ToolCapability.DATA_PROCESSING},
                "install_command": "uvx mcp-server-fetch"
            },
            "filesystem": {
                "description": "File system operations",
                "capabilities": {ToolCapability.FILE_OPERATIONS, ToolCapability.SYSTEM},
                "install_command": "npx -y @modelcontextprotocol/server-filesystem"
            },
            "github": {
                "description": "GitHub repository operations",
                "capabilities": {ToolCapability.DEVELOPMENT, ToolCapability.COMMUNICATION},
                "install_command": "uvx mcp-server-github"
            },
            "sqlite": {
                "description": "SQLite database operations",
                "capabilities": {ToolCapability.DATABASE, ToolCapability.DATA_PROCESSING},
                "install_command": "uvx mcp-server-sqlite"
            },
            "puppeteer": {
                "description": "Browser automation",
                "capabilities": {ToolCapability.AUTOMATION, ToolCapability.WEB_SEARCH},
                "install_command": "uvx mcp-server-puppeteer"
            },
            "slack": {
                "description": "Slack communication",
                "capabilities": {ToolCapability.COMMUNICATION, ToolCapability.WORKFLOW},
                "install_command": "uvx mcp-server-slack"
            },
            "google-drive": {
                "description": "Google Drive operations",
                "capabilities": {ToolCapability.FILE_OPERATIONS, ToolCapability.DATA_PROCESSING},
                "install_command": "uvx mcp-server-gdrive"
            },
            "postgres": {
                "description": "PostgreSQL database operations",
                "capabilities": {ToolCapability.DATABASE, ToolCapability.DATA_PROCESSING},
                "install_command": "uvx mcp-server-postgres"
            },
            "git": {
                "description": "Git version control operations",
                "capabilities": {ToolCapability.DEVELOPMENT, ToolCapability.SYSTEM},
                "install_command": "uvx mcp-server-git"
            },
            "sequential-thinking": {
                "description": "Advanced sequential reasoning",
                "capabilities": {ToolCapability.REASONING, ToolCapability.ANALYSIS},
                "install_command": "uvx mcp-server-sequential-thinking"
            },
            "mcp-reasoner": {
                "description": "Advanced reasoning with multiple strategies",
                "capabilities": {ToolCapability.REASONING, ToolCapability.ANALYSIS},
                "install_command": "uvx mcp-reasoner"
            },
            "brave-search": {
                "description": "Web search capabilities",
                "capabilities": {ToolCapability.WEB_SEARCH, ToolCapability.DATA_PROCESSING},
                "install_command": "uvx mcp-server-brave-search"
            }
        }
        
        for server_name, info in known_servers.items():
            if server_name not in self.discovered_servers:
                server_info = MCPServerInfo(
                    name=server_name,
                    description=info["description"],
                    capabilities=info["capabilities"],
                    connection_status="available",
                    install_command=info["install_command"],
                    priority_score=0.5  # Medium priority for known available servers
                )
                self.discovered_servers[server_name] = server_info
    
    def _analyze_server_capabilities(self, tools: List[Any], resources: List[Any]) -> Set[ToolCapability]:
        """Analyze server capabilities based on tools and resources."""
        capabilities = set()
        
        # Analyze tool names for capability hints
        tool_names = [tool.name.lower() if hasattr(tool, 'name') else str(tool).lower() for tool in tools]
        all_names = " ".join(tool_names)
        
        # Pattern matching for capabilities
        capability_patterns = {
            ToolCapability.FILE_OPERATIONS: ["file", "read", "write", "directory", "filesystem"],
            ToolCapability.WEB_SEARCH: ["search", "fetch", "url", "web", "browse"],
            ToolCapability.DATABASE: ["sql", "database", "query", "postgres", "sqlite"],
            ToolCapability.AUTOMATION: ["automate", "script", "execute", "puppeteer"],
            ToolCapability.DEVELOPMENT: ["git", "github", "code", "repository", "build"],
            ToolCapability.COMMUNICATION: ["slack", "email", "message", "send", "notify"],
            ToolCapability.ANALYSIS: ["analyze", "report", "statistics", "metrics"],
            ToolCapability.REASONING: ["reason", "think", "plan", "decide", "logic"],
            ToolCapability.WORKFLOW: ["workflow", "process", "orchestrate", "coordinate"],
            ToolCapability.SYSTEM: ["system", "command", "execute", "shell"],
            ToolCapability.GRAPHICS: ["image", "visual", "render", "draw", "graphics"],
            ToolCapability.DATA_PROCESSING: ["data", "process", "transform", "convert"]
        }
        
        for capability, patterns in capability_patterns.items():
            if any(pattern in all_names for pattern in patterns):
                capabilities.add(capability)
        
        return capabilities
    
    def _build_capability_map(self) -> None:
        """Build a map from capabilities to servers that provide them."""
        self.capability_map = {cap: [] for cap in ToolCapability}
        
        for server_name, server_info in self.discovered_servers.items():
            for capability in server_info.capabilities:
                self.capability_map[capability].append(server_name)
    
    def get_servers_by_capability(self, capability: ToolCapability) -> List[MCPServerInfo]:
        """Get servers that provide a specific capability."""
        server_names = self.capability_map.get(capability, [])
        return [self.discovered_servers[name] for name in server_names 
                if name in self.discovered_servers]
    
    def get_best_servers_for_task(self, task_description: str, max_servers: int = 3) -> List[MCPServerInfo]:
        """Get the best servers for a given task description."""
        # Simple keyword-based matching for now
        # In a full implementation, this could use embedding similarity
        task_lower = task_description.lower()
        
        scored_servers = []
        for server_info in self.discovered_servers.values():
            score = 0.0
            
            # Score based on description match
            if any(word in server_info.description.lower() for word in task_lower.split()):
                score += 1.0
            
            # Score based on tool names
            for tool in server_info.tools:
                if any(word in tool.lower() for word in task_lower.split()):
                    score += 0.5
            
            # Add priority score
            score += server_info.priority_score
            
            # Prefer connected servers
            if server_info.connection_status == "connected":
                score += 2.0
            
            if score > 0:
                scored_servers.append((score, server_info))
        
        # Sort by score and return top servers
        scored_servers.sort(key=lambda x: x[0], reverse=True)
        return [server_info for _, server_info in scored_servers[:max_servers]]
    
    def get_capability_coverage(self) -> Dict[str, float]:
        """Get coverage metrics for each capability."""
        coverage = {}
        total_servers = len(self.discovered_servers)
        
        if total_servers == 0:
            return {cap.value: 0.0 for cap in ToolCapability}
        
        for capability in ToolCapability:
            servers_with_cap = len(self.capability_map[capability])
            coverage[capability.value] = servers_with_cap / total_servers
        
        return coverage
    
    async def validate_server_connectivity(self, server_name: str) -> bool:
        """Validate that a server can be connected to."""
        try:
            # Attempt to connect and get basic info
            await self.connection_manager.connect_server(server_name)
            tools = await self.connection_manager.list_tools(server_name)
            return len(tools) > 0
        except Exception as e:
            self.logger.warning(f"Failed to validate server {server_name}: {e}")
            return False
    
    def export_discovery_results(self) -> Dict[str, Any]:
        """Export discovery results for external use."""
        return {
            "servers": {
                name: {
                    "name": info.name,
                    "description": info.description,
                    "capabilities": [cap.value for cap in info.capabilities],
                    "tools": info.tools,
                    "connection_status": info.connection_status,
                    "install_command": info.install_command,
                    "priority_score": info.priority_score
                }
                for name, info in self.discovered_servers.items()
            },
            "capability_map": {
                cap.value: servers for cap, servers in self.capability_map.items()
            },
            "coverage": self.get_capability_coverage()
        }
