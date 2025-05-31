"""
Tool Capability Mapper for autonomous MCP-Agent.

This module discovers and maps the capabilities of available MCP servers,
creating a knowledge base that the autonomous agent can use to select
the best tools for any given task.
"""

import asyncio
import logging
from typing import Dict, List, Set, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

from mcp_agent.mcp.gen_client import gen_client
from mcp_agent.config import Settings


class ToolCategory(Enum):
    """Categories of tool capabilities."""
    DEVELOPMENT = "development"
    INFORMATION = "information" 
    COGNITIVE = "cognitive"
    AUTOMATION = "automation"
    DATA = "data"
    COMMUNICATION = "communication"
    ANALYSIS = "analysis"
    CREATION = "creation"
    FILE_SYSTEM = "file_system"
    WEB = "web"
    SEARCH = "search"
    REASONING = "reasoning"


@dataclass
class ToolCapability:
    """Represents a capability of an MCP tool."""
    name: str
    description: str
    category: ToolCategory
    complexity: int  # 1-5 scale
    input_types: List[str]
    output_types: List[str]
    dependencies: List[str]
    
    
@dataclass
class MCPServerProfile:
    """Complete profile of an MCP server's capabilities."""
    server_name: str
    description: str
    tools: List[Dict[str, Any]]
    capabilities: List[ToolCapability]
    categories: Set[ToolCategory]
    is_available: bool
    connection_config: Dict[str, Any]


class ToolCapabilityMapper:
    """
    Discovers and maps capabilities of available MCP servers.
    
    This class automatically scans configured MCP servers, analyzes their
    tools and functions, and creates capability profiles that can be used
    for intelligent tool selection.
    """
    
    def __init__(self, config: Optional[Settings] = None):
        self.config = config or Settings()
        self.logger = logging.getLogger(__name__)
        self.server_profiles: Dict[str, MCPServerProfile] = {}
        self.capability_map: Dict[ToolCategory, List[str]] = {}
        
    async def discover_all_capabilities(self) -> Dict[str, MCPServerProfile]:
        """
        Discover capabilities of all configured MCP servers.
        
        Returns:
            Dictionary mapping server names to their capability profiles.
        """
        self.logger.info("Starting MCP server capability discovery...")
        
        # Get server configurations
        server_configs = self._get_server_configurations()
        
        # Discover capabilities for each server
        discovery_tasks = []
        for server_name, server_config in server_configs.items():
            task = self._discover_server_capabilities(server_name, server_config)
            discovery_tasks.append(task)
            
        # Execute discovery in parallel
        results = await asyncio.gather(*discovery_tasks, return_exceptions=True)
        
        # Process results
        for i, result in enumerate(results):
            server_name = list(server_configs.keys())[i]
            if isinstance(result, Exception):
                self.logger.warning(f"Failed to discover capabilities for {server_name}: {result}")
            else:
                self.server_profiles[server_name] = result
                
        self._build_capability_map()
        
        self.logger.info(f"Discovered capabilities for {len(self.server_profiles)} servers")
        return self.server_profiles
        
    async def _discover_server_capabilities(
        self, 
        server_name: str, 
        server_config: Dict[str, Any]
    ) -> MCPServerProfile:
        """Discover capabilities for a specific MCP server."""
        try:
            async with gen_client(server_name) as client:
                # Get available tools
                tools_response = await client.list_tools()
                tools = tools_response.tools if hasattr(tools_response, 'tools') else []
                
                # Analyze tools and extract capabilities
                capabilities = self._analyze_tools(tools)
                categories = {cap.category for cap in capabilities}
                
                profile = MCPServerProfile(
                    server_name=server_name,
                    description=self._infer_server_description(server_name, tools),
                    tools=[tool.model_dump() if hasattr(tool, 'model_dump') else tool for tool in tools],
                    capabilities=capabilities,
                    categories=categories,
                    is_available=True,
                    connection_config=server_config
                )
                
                self.logger.debug(f"Discovered {len(capabilities)} capabilities for {server_name}")
                return profile
                
        except Exception as e:
            self.logger.warning(f"Could not connect to server {server_name}: {e}")
            return MCPServerProfile(
                server_name=server_name,
                description=f"Server {server_name} (unavailable)",
                tools=[],
                capabilities=[],
                categories=set(),
                is_available=False,
                connection_config=server_config
            )
            
    def _analyze_tools(self, tools: List[Any]) -> List[ToolCapability]:
        """Analyze MCP tools and extract their capabilities."""
        capabilities = []
        
        for tool in tools:
            # Extract tool information
            tool_name = getattr(tool, 'name', str(tool))
            tool_description = getattr(tool, 'description', '')
            
            # Determine category based on tool name and description
            category = self._categorize_tool(tool_name, tool_description)
            
            # Determine complexity (simple heuristic)
            complexity = self._assess_complexity(tool_name, tool_description)
            
            # Extract input/output types (simplified)
            input_types, output_types = self._extract_io_types(tool)
            
            capability = ToolCapability(
                name=tool_name,
                description=tool_description,
                category=category,
                complexity=complexity,
                input_types=input_types,
                output_types=output_types,
                dependencies=[]
            )
            
            capabilities.append(capability)
            
        return capabilities
        
    def _categorize_tool(self, tool_name: str, description: str) -> ToolCategory:
        """Categorize a tool based on its name and description."""
        name_lower = tool_name.lower()
        desc_lower = description.lower()
        
        # Development tools
        if any(keyword in name_lower for keyword in ['git', 'github', 'code', 'build', 'deploy']):
            return ToolCategory.DEVELOPMENT
            
        # File system tools
        if any(keyword in name_lower for keyword in ['file', 'read', 'write', 'directory', 'path']):
            return ToolCategory.FILE_SYSTEM
            
        # Web and search tools
        if any(keyword in name_lower for keyword in ['web', 'fetch', 'url', 'http', 'browser']):
            return ToolCategory.WEB
        if any(keyword in name_lower for keyword in ['search', 'find', 'query']):
            return ToolCategory.SEARCH
            
        # Cognitive tools
        if any(keyword in name_lower for keyword in ['reason', 'think', 'analyze', 'cognitive']):
            return ToolCategory.COGNITIVE
            
        # Data tools
        if any(keyword in name_lower for keyword in ['sql', 'database', 'data', 'csv']):
            return ToolCategory.DATA
            
        # Automation tools
        if any(keyword in name_lower for keyword in ['workflow', 'automate', 'task', 'schedule']):
            return ToolCategory.AUTOMATION
            
        # Analysis tools
        if any(keyword in name_lower for keyword in ['analyze', 'evaluate', 'assess', 'report']):
            return ToolCategory.ANALYSIS
            
        # Creation tools
        if any(keyword in name_lower for keyword in ['create', 'generate', 'build', 'make']):
            return ToolCategory.CREATION
            
        # Default to information
        return ToolCategory.INFORMATION
        
    def _assess_complexity(self, tool_name: str, description: str) -> int:
        """Assess tool complexity on a 1-5 scale."""
        complexity_indicators = {
            'simple': 1,
            'basic': 1,
            'read': 1,
            'get': 1,
            'list': 1,
            'search': 2,
            'analyze': 3,
            'process': 3,
            'generate': 3,
            'workflow': 4,
            'orchestrate': 4,
            'reason': 4,
            'complex': 5,
            'advanced': 5
        }
        
        text = f"{tool_name} {description}".lower()
        
        for indicator, level in complexity_indicators.items():
            if indicator in text:
                return level
                
        return 2  # Default complexity
        
    def _extract_io_types(self, tool: Any) -> Tuple[List[str], List[str]]:
        """Extract input and output types from tool definition."""
        # This is a simplified implementation
        # In practice, you'd parse the tool schema more thoroughly
        
        input_types = ["text"]  # Default
        output_types = ["text"]  # Default
        
        if hasattr(tool, 'inputSchema'):
            # Parse input schema for more specific types
            pass
            
        return input_types, output_types
        
    def _get_server_configurations(self) -> Dict[str, Dict[str, Any]]:
        """Get MCP server configurations from config."""
        if not self.config or not hasattr(self.config, 'mcp') or not self.config.mcp:
            return {}
            
        servers = getattr(self.config.mcp, 'servers', {})
        return dict(servers) if servers else {}
        
    def _infer_server_description(self, server_name: str, tools: List[Any]) -> str:
        """Infer a description for the MCP server based on its tools."""
        tool_count = len(tools)
        
        if server_name == 'fetch':
            return f"Web fetching server with {tool_count} tools for HTTP requests and content retrieval"
        elif server_name == 'filesystem':
            return f"File system server with {tool_count} tools for file and directory operations"
        elif server_name == 'github':
            return f"GitHub integration server with {tool_count} tools for repository management"
        elif 'database' in server_name or 'sql' in server_name:
            return f"Database server with {tool_count} tools for data storage and querying"
        else:
            return f"MCP server '{server_name}' with {tool_count} available tools"
            
    def _build_capability_map(self):
        """Build a map of capabilities by category."""
        self.capability_map = {}
        
        for profile in self.server_profiles.values():
            for capability in profile.capabilities:
                category = capability.category
                if category not in self.capability_map:
                    self.capability_map[category] = []
                self.capability_map[category].append(profile.server_name)
                
    def get_servers_by_capability(self, category: ToolCategory) -> List[str]:
        """Get servers that provide a specific capability category."""
        return self.capability_map.get(category, [])
        
    def get_best_servers_for_task(self, task_description: str) -> List[Tuple[str, float]]:
        """
        Get the best servers for a given task, ranked by relevance.
        
        Returns:
            List of (server_name, relevance_score) tuples, sorted by score.
        """
        scores = []
        task_lower = task_description.lower()
        
        for server_name, profile in self.server_profiles.items():
            if not profile.is_available:
                continue
                
            score = 0.0
            
            # Score based on tool relevance
            for capability in profile.capabilities:
                # Simple keyword matching (could be improved with embeddings)
                if any(keyword in task_lower for keyword in [
                    capability.name.lower(),
                    capability.description.lower()
                ]):
                    score += 1.0 / capability.complexity  # Prefer simpler tools
                    
            # Normalize by number of capabilities
            if profile.capabilities:
                score /= len(profile.capabilities)
                
            if score > 0:
                scores.append((server_name, score))
                
        return sorted(scores, key=lambda x: x[1], reverse=True)
        
    def get_capability_summary(self) -> Dict[str, Any]:
        """Get a summary of all discovered capabilities."""
        return {
            'total_servers': len(self.server_profiles),
            'available_servers': len([p for p in self.server_profiles.values() if p.is_available]),
            'total_capabilities': sum(len(p.capabilities) for p in self.server_profiles.values()),
            'categories': list(self.capability_map.keys()),
            'servers_by_category': {
                cat.value: servers for cat, servers in self.capability_map.items()
            }
        }
