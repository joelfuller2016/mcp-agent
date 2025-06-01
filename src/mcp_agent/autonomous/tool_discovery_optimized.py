"""
Optimized Tool Discovery Agent with Parallel Processing

This module provides an enhanced ToolDiscoveryAgent with parallel processing
capabilities to improve discovery performance and reduce response times.
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Optional, Set, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache

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
    discovery_time_ms: float = 0.0  # Track discovery performance


@dataclass
class DiscoveryPerformanceMetrics:
    """Performance metrics for discovery operations."""
    
    total_servers_discovered: int = 0
    connected_servers_found: int = 0
    registry_servers_found: int = 0
    total_discovery_time_ms: float = 0.0
    parallel_operations_count: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    failed_discoveries: int = 0


class ParallelToolDiscoveryAgent:
    """
    Enhanced ToolDiscoveryAgent with parallel processing capabilities.
    
    Optimizations:
    - Parallel server discovery using asyncio.gather()
    - Concurrent server validation
    - Cached capability analysis
    - Connection pooling for server communications
    - Performance monitoring and metrics
    """

    def __init__(self, connection_manager: MCPConnectionManager, max_concurrent_operations: int = 10):
        self.connection_manager = connection_manager
        self.logger = logging.getLogger(__name__)
        self.discovered_servers: Dict[str, MCPServerInfo] = {}
        self.capability_map: Dict[ToolCapability, List[str]] = {
            cap: [] for cap in ToolCapability
        }
        
        # Performance optimization settings
        self.max_concurrent_operations = max_concurrent_operations
        self.connection_pool_size = min(max_concurrent_operations, 5)
        
        # Performance tracking
        self.performance_metrics = DiscoveryPerformanceMetrics()
        
        # Create thread pool for CPU-bound operations
        self.thread_pool = ThreadPoolExecutor(max_workers=max_concurrent_operations // 2)
        
        # Cache for capability analysis results
        self._capability_cache: Dict[str, Set[ToolCapability]] = {}

    async def discover_available_servers(self) -> Dict[str, MCPServerInfo]:
        """Discover all available MCP servers using parallel processing."""
        start_time = time.perf_counter()
        self.logger.info("Starting parallel MCP server discovery...")
        
        try:
            # Reset metrics for this discovery session
            self.performance_metrics = DiscoveryPerformanceMetrics()
            
            # Run discovery operations in parallel
            discovery_tasks = [
                self._discover_connected_servers_parallel(),
                self._discover_from_registries_parallel()
            ]
            
            # Execute discovery tasks concurrently
            await asyncio.gather(*discovery_tasks, return_exceptions=True)
            
            # Build capability map
            self._build_capability_map()
            
            # Update performance metrics
            end_time = time.perf_counter()
            self.performance_metrics.total_discovery_time_ms = (end_time - start_time) * 1000
            self.performance_metrics.total_servers_discovered = len(self.discovered_servers)
            
            self.logger.info(
                f"Parallel discovery complete: {len(self.discovered_servers)} servers "
                f"in {self.performance_metrics.total_discovery_time_ms:.2f}ms"
            )
            
            return self.discovered_servers
            
        except Exception as e:
            self.logger.error(f"Error during parallel discovery: {e}")
            self.performance_metrics.failed_discoveries += 1
            return self.discovered_servers

    async def _discover_connected_servers_parallel(self) -> None:
        """Discover connected servers using parallel processing."""
        try:
            connected_servers = await self.connection_manager.list_connected_servers()
            
            if not connected_servers:
                return
            
            # Create semaphore to limit concurrent operations
            semaphore = asyncio.Semaphore(self.max_concurrent_operations)
            
            # Create discovery tasks for each server
            discovery_tasks = [
                self._analyze_single_server(server_name, semaphore)
                for server_name in connected_servers
            ]
            
            # Execute server analysis in parallel
            results = await asyncio.gather(*discovery_tasks, return_exceptions=True)
            
            # Process results and count successes
            successful_discoveries = 0
            for i, result in enumerate(results):
                if not isinstance(result, Exception):
                    successful_discoveries += 1
                else:
                    self.logger.warning(f"Failed to analyze server {connected_servers[i]}: {result}")
                    self.performance_metrics.failed_discoveries += 1
            
            self.performance_metrics.connected_servers_found = successful_discoveries
            self.performance_metrics.parallel_operations_count += len(discovery_tasks)
            
        except Exception as e:
            self.logger.error(f"Error in parallel connected server discovery: {e}")
            self.performance_metrics.failed_discoveries += 1

    async def _analyze_single_server(self, server_name: str, semaphore: asyncio.Semaphore) -> MCPServerInfo:
        """Analyze a single server with concurrency control."""
        async with semaphore:
            start_time = time.perf_counter()
            
            try:
                # Gather server information in parallel
                tools_task = self.connection_manager.list_tools(server_name)
                resources_task = self.connection_manager.list_resources(server_name)
                
                tools, resources = await asyncio.gather(tools_task, resources_task)
                
                # Analyze capabilities (potentially cached)
                capabilities = await self._analyze_server_capabilities_cached(
                    server_name, tools, resources
                )
                
                # Calculate discovery time
                discovery_time = (time.perf_counter() - start_time) * 1000
                
                server_info = MCPServerInfo(
                    name=server_name,
                    description=f"Connected MCP server: {server_name}",
                    capabilities=capabilities,
                    tools=[tool.name for tool in tools],
                    resources=[res.name for res in resources],
                    connection_status="connected",
                    priority_score=1.0,
                    discovery_time_ms=discovery_time
                )
                
                self.discovered_servers[server_name] = server_info
                self.logger.debug(f"Analyzed server {server_name} in {discovery_time:.2f}ms")
                
                return server_info
                
            except Exception as e:
                self.logger.warning(f"Failed to analyze server {server_name}: {e}")
                raise e

    async def _analyze_server_capabilities_cached(
        self, server_name: str, tools: List[Any], resources: List[Any]
    ) -> Set[ToolCapability]:
        """Analyze server capabilities with caching."""
        
        # Create cache key based on tools and resources
        tool_names = [tool.name if hasattr(tool, 'name') else str(tool) for tool in tools]
        resource_names = [res.name if hasattr(res, 'name') else str(res) for res in resources]
        cache_key = f"{server_name}:{hash(tuple(sorted(tool_names + resource_names)))}"
        
        # Check cache first
        if cache_key in self._capability_cache:
            self.performance_metrics.cache_hits += 1
            return self._capability_cache[cache_key]
        
        # Analyze capabilities in thread pool (CPU-bound operation)
        loop = asyncio.get_event_loop()
        capabilities = await loop.run_in_executor(
            self.thread_pool,
            self._analyze_server_capabilities_sync,
            tools,
            resources
        )
        
        # Cache the result
        self._capability_cache[cache_key] = capabilities
        self.performance_metrics.cache_misses += 1
        
        return capabilities

    def _analyze_server_capabilities_sync(
        self, tools: List[Any], resources: List[Any]
    ) -> Set[ToolCapability]:
        """Synchronous capability analysis for thread pool execution."""
        capabilities = set()
        
        # Analyze tool names for capability hints
        tool_names = [
            tool.name.lower() if hasattr(tool, "name") else str(tool).lower()
            for tool in tools
        ]
        all_names = " ".join(tool_names)
        
        # Pattern matching for capabilities
        capability_patterns = {
            ToolCapability.FILE_OPERATIONS: [
                "file", "read", "write", "directory", "filesystem",
            ],
            ToolCapability.WEB_SEARCH: ["search", "fetch", "url", "web", "browse"],
            ToolCapability.DATABASE: ["sql", "database", "query", "postgres", "sqlite"],
            ToolCapability.AUTOMATION: ["automate", "script", "execute", "puppeteer"],
            ToolCapability.DEVELOPMENT: [
                "git", "github", "code", "repository", "build",
            ],
            ToolCapability.COMMUNICATION: [
                "slack", "email", "message", "send", "notify",
            ],
            ToolCapability.ANALYSIS: ["analyze", "report", "statistics", "metrics"],
            ToolCapability.REASONING: ["reason", "think", "plan", "decide", "logic"],
            ToolCapability.WORKFLOW: [
                "workflow", "process", "orchestrate", "coordinate",
            ],
            ToolCapability.SYSTEM: ["system", "command", "execute", "shell"],
            ToolCapability.GRAPHICS: ["image", "visual", "render", "draw", "graphics"],
            ToolCapability.DATA_PROCESSING: ["data", "process", "transform", "convert"],
        }
        
        for capability, patterns in capability_patterns.items():
            if any(pattern in all_names for pattern in patterns):
                capabilities.add(capability)
        
        return capabilities

    async def _discover_from_registries_parallel(self) -> None:
        """Discover servers from registries using parallel processing."""
        try:
            # Known MCP server patterns and their capabilities
            known_servers = {
                "fetch": {
                    "description": "Web fetching and URL operations",
                    "capabilities": {
                        ToolCapability.WEB_SEARCH,
                        ToolCapability.DATA_PROCESSING,
                    },
                    "install_command": "uvx mcp-server-fetch",
                },
                "filesystem": {
                    "description": "File system operations",
                    "capabilities": {ToolCapability.FILE_OPERATIONS, ToolCapability.SYSTEM},
                    "install_command": "npx -y @modelcontextprotocol/server-filesystem",
                },
                "github": {
                    "description": "GitHub repository operations",
                    "capabilities": {
                        ToolCapability.DEVELOPMENT,
                        ToolCapability.COMMUNICATION,
                    },
                    "install_command": "uvx mcp-server-github",
                },
                "sqlite": {
                    "description": "SQLite database operations",
                    "capabilities": {
                        ToolCapability.DATABASE,
                        ToolCapability.DATA_PROCESSING,
                    },
                    "install_command": "uvx mcp-server-sqlite",
                },
                "puppeteer": {
                    "description": "Browser automation",
                    "capabilities": {ToolCapability.AUTOMATION, ToolCapability.WEB_SEARCH},
                    "install_command": "uvx mcp-server-puppeteer",
                },
                "slack": {
                    "description": "Slack communication",
                    "capabilities": {ToolCapability.COMMUNICATION, ToolCapability.WORKFLOW},
                    "install_command": "uvx mcp-server-slack",
                },
                "google-drive": {
                    "description": "Google Drive operations",
                    "capabilities": {
                        ToolCapability.FILE_OPERATIONS,
                        ToolCapability.DATA_PROCESSING,
                    },
                    "install_command": "uvx mcp-server-gdrive",
                },
                "postgres": {
                    "description": "PostgreSQL database operations",
                    "capabilities": {
                        ToolCapability.DATABASE,
                        ToolCapability.DATA_PROCESSING,
                    },
                    "install_command": "uvx mcp-server-postgres",
                },
                "git": {
                    "description": "Git version control operations",
                    "capabilities": {ToolCapability.DEVELOPMENT, ToolCapability.SYSTEM},
                    "install_command": "uvx mcp-server-git",
                },
                "sequential-thinking": {
                    "description": "Advanced sequential reasoning",
                    "capabilities": {ToolCapability.REASONING, ToolCapability.ANALYSIS},
                    "install_command": "uvx mcp-server-sequential-thinking",
                },
                "mcp-reasoner": {
                    "description": "Advanced reasoning with multiple strategies",
                    "capabilities": {ToolCapability.REASONING, ToolCapability.ANALYSIS},
                    "install_command": "uvx mcp-reasoner",
                },
                "brave-search": {
                    "description": "Web search capabilities",
                    "capabilities": {
                        ToolCapability.WEB_SEARCH,
                        ToolCapability.DATA_PROCESSING,
                    },
                    "install_command": "uvx mcp-server-brave-search",
                },
            }
            
            # Process registry servers in parallel batches
            server_items = list(known_servers.items())
            batch_size = self.max_concurrent_operations
            
            for i in range(0, len(server_items), batch_size):
                batch = server_items[i:i + batch_size]
                
                # Create tasks for this batch
                batch_tasks = [
                    self._process_registry_server(server_name, info)
                    for server_name, info in batch
                ]
                
                # Execute batch in parallel
                await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            self.performance_metrics.registry_servers_found = len([
                s for s in self.discovered_servers.values()
                if s.connection_status == "available"
            ])
            
        except Exception as e:
            self.logger.error(f"Error in parallel registry discovery: {e}")
            self.performance_metrics.failed_discoveries += 1

    async def _process_registry_server(self, server_name: str, info: Dict[str, Any]) -> None:
        """Process a single registry server asynchronously."""
        try:
            if server_name not in self.discovered_servers:
                start_time = time.perf_counter()
                
                server_info = MCPServerInfo(
                    name=server_name,
                    description=info["description"],
                    capabilities=info["capabilities"],
                    connection_status="available",
                    install_command=info["install_command"],
                    priority_score=0.5,
                    discovery_time_ms=(time.perf_counter() - start_time) * 1000
                )
                
                self.discovered_servers[server_name] = server_info
                
        except Exception as e:
            self.logger.warning(f"Failed to process registry server {server_name}: {e}")

    async def validate_servers_connectivity_parallel(
        self, server_names: List[str]
    ) -> Dict[str, bool]:
        """Validate connectivity for multiple servers in parallel."""
        
        semaphore = asyncio.Semaphore(self.max_concurrent_operations)
        
        async def validate_single_server(server_name: str) -> Tuple[str, bool]:
            async with semaphore:
                try:
                    await self.connection_manager.connect_server(server_name)
                    tools = await self.connection_manager.list_tools(server_name)
                    return server_name, len(tools) > 0
                except Exception as e:
                    self.logger.warning(f"Failed to validate server {server_name}: {e}")
                    return server_name, False
        
        # Create validation tasks
        validation_tasks = [
            validate_single_server(server_name)
            for server_name in server_names
        ]
        
        # Execute validations in parallel
        results = await asyncio.gather(*validation_tasks, return_exceptions=True)
        
        # Process results
        connectivity_results = {}
        for result in results:
            if isinstance(result, tuple):
                server_name, is_connected = result
                connectivity_results[server_name] = is_connected
            else:
                self.logger.error(f"Validation error: {result}")
        
        return connectivity_results

    def _build_capability_map(self) -> None:
        """Build a map from capabilities to servers that provide them."""
        self.capability_map = {cap: [] for cap in ToolCapability}
        
        for server_name, server_info in self.discovered_servers.items():
            for capability in server_info.capabilities:
                self.capability_map[capability].append(server_name)

    def get_servers_by_capability(
        self, capability: ToolCapability
    ) -> List[MCPServerInfo]:
        """Get servers that provide a specific capability."""
        server_names = self.capability_map.get(capability, [])
        return [
            self.discovered_servers[name]
            for name in server_names
            if name in self.discovered_servers
        ]

    def get_best_servers_for_task(
        self, task_description: str, max_servers: int = 3
    ) -> List[MCPServerInfo]:
        """Get the best servers for a given task description."""
        task_lower = task_description.lower()
        
        scored_servers = []
        for server_info in self.discovered_servers.values():
            score = 0.0
            
            # Score based on description match
            if any(
                word in server_info.description.lower() for word in task_lower.split()
            ):
                score += 1.0
            
            # Score based on tool names
            for tool in server_info.tools:
                if any(word in tool.lower() for word in task_lower.split()):
                    score += 0.5
            
            # Add priority score and discovery performance bonus
            score += server_info.priority_score
            
            # Bonus for faster discovery (better performance)
            if server_info.discovery_time_ms > 0:
                performance_bonus = max(0, 1.0 - (server_info.discovery_time_ms / 1000))
                score += performance_bonus * 0.1
            
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

    def get_performance_metrics(self) -> DiscoveryPerformanceMetrics:
        """Get discovery performance metrics."""
        return self.performance_metrics

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get a summary of discovery performance."""
        metrics = self.performance_metrics
        
        cache_hit_rate = 0.0
        if (metrics.cache_hits + metrics.cache_misses) > 0:
            cache_hit_rate = metrics.cache_hits / (metrics.cache_hits + metrics.cache_misses) * 100
        
        return {
            "total_servers_discovered": metrics.total_servers_discovered,
            "connected_servers_found": metrics.connected_servers_found,
            "registry_servers_found": metrics.registry_servers_found,
            "total_discovery_time_ms": round(metrics.total_discovery_time_ms, 2),
            "parallel_operations_count": metrics.parallel_operations_count,
            "cache_hit_rate": round(cache_hit_rate, 1),
            "failed_discoveries": metrics.failed_discoveries,
            "avg_discovery_time_per_server": round(
                metrics.total_discovery_time_ms / max(metrics.total_servers_discovered, 1), 2
            ),
        }

    def clear_cache(self) -> None:
        """Clear the capability analysis cache."""
        self._capability_cache.clear()
        self.logger.info("Capability analysis cache cleared")

    def export_discovery_results(self) -> Dict[str, Any]:
        """Export discovery results with performance data."""
        return {
            "servers": {
                name: {
                    "name": info.name,
                    "description": info.description,
                    "capabilities": [cap.value for cap in info.capabilities],
                    "tools": info.tools,
                    "connection_status": info.connection_status,
                    "install_command": info.install_command,
                    "priority_score": info.priority_score,
                    "discovery_time_ms": info.discovery_time_ms,
                }
                for name, info in self.discovered_servers.items()
            },
            "capability_map": {
                cap.value: servers for cap, servers in self.capability_map.items()
            },
            "coverage": self.get_capability_coverage(),
            "performance_metrics": self.get_performance_summary(),
        }

    def __del__(self):
        """Cleanup thread pool on object destruction."""
        if hasattr(self, 'thread_pool'):
            self.thread_pool.shutdown(wait=False)


# Backward compatibility alias
ToolDiscoveryAgent = ParallelToolDiscoveryAgent
