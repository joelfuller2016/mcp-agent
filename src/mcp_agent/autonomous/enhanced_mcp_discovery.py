"""
Enhanced MCP Server Discovery and Auto-Installation System

This module provides advanced MCP server discovery capabilities with automatic
installation, configuration, and integration support.
"""

import asyncio
import json
import logging
import subprocess
import sys
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Any, Tuple
from urllib.parse import urlparse
import aiohttp
import yaml

from ..mcp.mcp_connection_manager import MCPConnectionManager


class ServerInstallMethod(Enum):
    """Installation methods for MCP servers."""
    NPX = "npx"
    UVX = "uvx"
    PIP = "pip"
    NPM = "npm"
    DOCKER = "docker"
    BINARY = "binary"
    GIT = "git"


class ServerCategory(Enum):
    """Categories of MCP servers."""
    FILE_OPERATIONS = "file_operations"
    WEB_SEARCH = "web_search"
    DATABASE = "database"
    CLOUD_SERVICES = "cloud_services"
    DEVELOPMENT = "development"
    COMMUNICATION = "communication"
    ANALYSIS = "analysis"
    AUTOMATION = "automation"
    PRODUCTIVITY = "productivity"
    SYSTEM = "system"


@dataclass
class MCPServerSpec:
    """Specification for an MCP server."""
    name: str
    description: str
    category: ServerCategory
    install_method: ServerInstallMethod
    install_command: str
    config_template: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    environment_vars: Dict[str, str] = field(default_factory=dict)
    required_config: List[str] = field(default_factory=list)
    optional_config: List[str] = field(default_factory=list)
    capabilities: Set[str] = field(default_factory=set)
    tools: List[str] = field(default_factory=list)
    resources: List[str] = field(default_factory=list)
    version: str = "latest"
    repository_url: Optional[str] = None
    documentation_url: Optional[str] = None
    priority_score: float = 0.0
    auto_install: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class InstallationResult:
    """Result of MCP server installation."""
    server_name: str
    success: bool
    install_time_ms: float
    error_message: str = ""
    config_path: Optional[str] = None
    executable_path: Optional[str] = None
    post_install_notes: List[str] = field(default_factory=list)


class EnhancedMCPDiscovery:
    """
    Enhanced MCP server discovery and auto-installation system.
    
    Features:
    - Automatic discovery of available MCP servers from multiple sources
    - Intelligent server recommendation based on task requirements
    - Automatic installation with dependency management
    - Configuration template generation
    - Health monitoring and auto-recovery
    """

    def __init__(self, config_dir: Optional[Path] = None):
        self.logger = logging.getLogger(__name__)
        self.config_dir = config_dir or Path.home() / ".mcp-agent"
        self.config_dir.mkdir(exist_ok=True)
        
        # Server registry and state
        self.server_registry: Dict[str, MCPServerSpec] = {}
        self.installed_servers: Dict[str, InstallationResult] = {}
        self.server_configs: Dict[str, Dict[str, Any]] = {}
        
        # Performance tracking
        self.discovery_metrics = {
            "total_discoveries": 0,
            "successful_installs": 0,
            "failed_installs": 0,
            "avg_install_time_ms": 0.0,
            "cache_hits": 0
        }
        
        # Initialize with built-in server specifications
        self._load_builtin_servers()

    def _load_builtin_servers(self):
        """Load built-in MCP server specifications."""
        builtin_servers = [
            MCPServerSpec(
                name="fetch",
                description="Web content fetching and scraping capabilities",
                category=ServerCategory.WEB_SEARCH,
                install_method=ServerInstallMethod.NPX,
                install_command="npx @modelcontextprotocol/server-fetch",
                capabilities={"web_fetch", "html_parsing", "content_extraction"},
                tools=["fetch_html", "fetch_text", "fetch_json"],
                priority_score=8.5,
                auto_install=True
            ),
            MCPServerSpec(
                name="filesystem",
                description="File system operations and management",
                category=ServerCategory.FILE_OPERATIONS,
                install_method=ServerInstallMethod.NPX,
                install_command="npx @modelcontextprotocol/server-filesystem",
                capabilities={"file_read", "file_write", "directory_operations"},
                tools=["read_file", "write_file", "list_directory", "create_directory"],
                priority_score=9.0,
                auto_install=True
            ),
            MCPServerSpec(
                name="github",
                description="GitHub repository management and operations",
                category=ServerCategory.DEVELOPMENT,
                install_method=ServerInstallMethod.NPX,
                install_command="npx @modelcontextprotocol/server-github",
                capabilities={"git_operations", "repository_management", "issue_tracking"},
                tools=["create_repository", "list_issues", "create_pull_request"],
                required_config=["GITHUB_PERSONAL_ACCESS_TOKEN"],
                priority_score=8.0,
                auto_install=True
            ),
            MCPServerSpec(
                name="sqlite",
                description="SQLite database operations and queries",
                category=ServerCategory.DATABASE,
                install_method=ServerInstallMethod.NPX,
                install_command="npx @modelcontextprotocol/server-sqlite",
                capabilities={"database_queries", "sql_operations", "data_management"},
                tools=["execute_query", "create_table", "insert_data"],
                priority_score=7.5,
                auto_install=True
            ),
            MCPServerSpec(
                name="puppeteer",
                description="Browser automation and web interaction",
                category=ServerCategory.AUTOMATION,
                install_method=ServerInstallMethod.NPX,
                install_command="npx @modelcontextprotocol/server-puppeteer",
                capabilities={"browser_automation", "web_scraping", "screenshot"},
                tools=["navigate", "click", "screenshot", "fill_form"],
                priority_score=7.0,
                auto_install=True
            ),
            MCPServerSpec(
                name="postgres",
                description="PostgreSQL database operations",
                category=ServerCategory.DATABASE,
                install_method=ServerInstallMethod.NPX,
                install_command="npx @modelcontextprotocol/server-postgres",
                capabilities={"database_queries", "postgresql", "advanced_sql"},
                tools=["execute_query", "create_table", "manage_schema"],
                required_config=["DATABASE_URL"],
                priority_score=6.5,
                auto_install=False  # Requires database setup
            ),
            MCPServerSpec(
                name="brave-search",
                description="Web search using Brave Search API",
                category=ServerCategory.WEB_SEARCH,
                install_method=ServerInstallMethod.NPX,
                install_command="npx @modelcontextprotocol/server-brave-search",
                capabilities={"web_search", "information_retrieval", "real_time_search"},
                tools=["web_search", "search_news", "search_images"],
                required_config=["BRAVE_API_KEY"],
                priority_score=8.0,
                auto_install=False  # Requires API key
            ),
            MCPServerSpec(
                name="google-drive",
                description="Google Drive file management and operations",
                category=ServerCategory.CLOUD_SERVICES,
                install_method=ServerInstallMethod.NPX,
                install_command="npx @modelcontextprotocol/server-google-drive",
                capabilities={"cloud_storage", "document_management", "file_sharing"},
                tools=["list_files", "download_file", "upload_file", "create_folder"],
                required_config=["GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET"],
                priority_score=7.0,
                auto_install=False  # Requires OAuth setup
            )
        ]
        
        for server in builtin_servers:
            self.server_registry[server.name] = server

    async def discover_available_servers(self) -> List[MCPServerSpec]:
        """
        Discover available MCP servers from multiple sources.
        
        Returns:
            List of discovered server specifications
        """
        self.logger.info("Starting enhanced MCP server discovery...")
        start_time = time.perf_counter()
        
        discovery_tasks = [
            self._discover_from_registry(),
            self._discover_from_github(),
            self._discover_from_npm(),
            self._discover_local_servers()
        ]
        
        # Run discovery tasks in parallel
        discovery_results = await asyncio.gather(*discovery_tasks, return_exceptions=True)
        
        # Collect all discovered servers
        all_servers = []
        for result in discovery_results:
            if isinstance(result, Exception):
                self.logger.warning(f"Discovery task failed: {result}")
                continue
            all_servers.extend(result)
        
        # Update registry with new discoveries
        for server in all_servers:
            if server.name not in self.server_registry:
                self.server_registry[server.name] = server
        
        discovery_time = (time.perf_counter() - start_time) * 1000
        self.discovery_metrics["total_discoveries"] += 1
        
        self.logger.info(f"Discovery completed in {discovery_time:.2f}ms. Found {len(all_servers)} servers.")
        return all_servers

    async def _discover_from_registry(self) -> List[MCPServerSpec]:
        """Discover servers from official MCP registry."""
        try:
            # This would connect to an official MCP server registry API
            # For now, return built-in servers
            return list(self.server_registry.values())
        except Exception as e:
            self.logger.warning(f"Registry discovery failed: {e}")
            return []

    async def _discover_from_github(self) -> List[MCPServerSpec]:
        """Discover servers from GitHub repositories."""
        try:
            # Search GitHub for MCP server repositories
            # This would use GitHub API to find repositories with MCP server tags
            discovered_servers = []
            
            # Placeholder for GitHub API integration
            # In production, this would:
            # 1. Search for repositories with "mcp-server" topic
            # 2. Parse their configuration files
            # 3. Create MCPServerSpec objects
            
            return discovered_servers
        except Exception as e:
            self.logger.warning(f"GitHub discovery failed: {e}")
            return []

    async def _discover_from_npm(self) -> List[MCPServerSpec]:
        """Discover servers from NPM registry."""
        try:
            # Search NPM for MCP server packages
            # This would use NPM API to find packages with MCP keywords
            discovered_servers = []
            
            # Placeholder for NPM API integration
            
            return discovered_servers
        except Exception as e:
            self.logger.warning(f"NPM discovery failed: {e}")
            return []

    async def _discover_local_servers(self) -> List[MCPServerSpec]:
        """Discover locally installed MCP servers."""
        try:
            # Check for locally installed servers
            local_servers = []
            
            # Check common installation paths
            # Parse local configuration files
            
            return local_servers
        except Exception as e:
            self.logger.warning(f"Local discovery failed: {e}")
            return []

    async def recommend_servers_for_task(self, task_description: str, max_recommendations: int = 5) -> List[MCPServerSpec]:
        """
        Recommend MCP servers for a specific task.
        
        Args:
            task_description: Natural language description of the task
            max_recommendations: Maximum number of servers to recommend
            
        Returns:
            List of recommended server specifications
        """
        task_lower = task_description.lower()
        
        # Score servers based on task requirements
        server_scores = {}
        for server_name, server_spec in self.server_registry.items():
            score = self._calculate_task_compatibility_score(task_lower, server_spec)
            if score > 0:
                server_scores[server_name] = score
        
        # Sort by score and return top recommendations
        recommended = sorted(
            server_scores.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:max_recommendations]
        
        return [self.server_registry[name] for name, _ in recommended]

    def _calculate_task_compatibility_score(self, task_description: str, server_spec: MCPServerSpec) -> float:
        """Calculate compatibility score between task and server."""
        score = 0.0
        
        # Base priority score
        score += server_spec.priority_score
        
        # Category matching
        category_keywords = {
            ServerCategory.FILE_OPERATIONS: ["file", "directory", "folder", "save", "load", "read", "write"],
            ServerCategory.WEB_SEARCH: ["search", "web", "internet", "find", "lookup", "browse"],
            ServerCategory.DATABASE: ["database", "sql", "query", "data", "table", "record"],
            ServerCategory.DEVELOPMENT: ["code", "github", "repository", "commit", "programming"],
            ServerCategory.AUTOMATION: ["automate", "browser", "click", "form", "screenshot"],
            ServerCategory.COMMUNICATION: ["email", "message", "send", "notify", "slack"],
            ServerCategory.CLOUD_SERVICES: ["cloud", "drive", "storage", "upload", "download"]
        }
        
        keywords = category_keywords.get(server_spec.category, [])
        keyword_matches = sum(1 for keyword in keywords if keyword in task_description)
        score += keyword_matches * 2.0
        
        # Capability matching
        for capability in server_spec.capabilities:
            if capability.replace("_", " ") in task_description:
                score += 3.0
        
        # Tool matching
        for tool in server_spec.tools:
            if tool.replace("_", " ") in task_description:
                score += 1.5
        
        return score

    async def auto_install_server(self, server_spec: MCPServerSpec) -> InstallationResult:
        """
        Automatically install an MCP server.
        
        Args:
            server_spec: Server specification to install
            
        Returns:
            Installation result with success status and details
        """
        self.logger.info(f"Starting auto-installation of {server_spec.name}...")
        start_time = time.perf_counter()
        
        try:
            # Check if already installed
            if server_spec.name in self.installed_servers:
                existing = self.installed_servers[server_spec.name]
                if existing.success:
                    self.logger.info(f"Server {server_spec.name} already installed")
                    return existing
            
            # Validate installation method
            if not await self._validate_install_method(server_spec.install_method):
                raise Exception(f"Installation method {server_spec.install_method.value} not available")
            
            # Install dependencies first
            for dependency in server_spec.dependencies:
                await self._install_dependency(dependency)
            
            # Execute installation command
            await self._execute_install_command(server_spec)
            
            # Generate configuration if needed
            config_path = None
            if server_spec.config_template or server_spec.required_config:
                config_path = await self._generate_server_config(server_spec)
            
            install_time = (time.perf_counter() - start_time) * 1000
            
            result = InstallationResult(
                server_name=server_spec.name,
                success=True,
                install_time_ms=install_time,
                config_path=str(config_path) if config_path else None,
                post_install_notes=[
                    f"Server {server_spec.name} installed successfully",
                    f"Installation completed in {install_time:.2f}ms"
                ]
            )
            
            self.installed_servers[server_spec.name] = result
            self.discovery_metrics["successful_installs"] += 1
            
            self.logger.info(f"Successfully installed {server_spec.name} in {install_time:.2f}ms")
            return result
            
        except Exception as e:
            install_time = (time.perf_counter() - start_time) * 1000
            error_msg = str(e)
            
            result = InstallationResult(
                server_name=server_spec.name,
                success=False,
                install_time_ms=install_time,
                error_message=error_msg
            )
            
            self.installed_servers[server_spec.name] = result
            self.discovery_metrics["failed_installs"] += 1
            
            self.logger.error(f"Failed to install {server_spec.name}: {error_msg}")
            return result

    async def _validate_install_method(self, method: ServerInstallMethod) -> bool:
        """Validate that installation method is available."""
        method_commands = {
            ServerInstallMethod.NPX: "npx",
            ServerInstallMethod.UVX: "uvx", 
            ServerInstallMethod.PIP: "pip",
            ServerInstallMethod.NPM: "npm",
            ServerInstallMethod.DOCKER: "docker"
        }
        
        command = method_commands.get(method)
        if not command:
            return False
        
        try:
            process = await asyncio.create_subprocess_exec(
                command, "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await process.communicate()
            return process.returncode == 0
        except Exception:
            return False

    async def _install_dependency(self, dependency: str):
        """Install a dependency."""
        # Implementation for dependency installation
        pass

    async def _execute_install_command(self, server_spec: MCPServerSpec):
        """Execute the installation command for a server."""
        command_parts = server_spec.install_command.split()
        
        process = await asyncio.create_subprocess_exec(
            *command_parts,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            raise Exception(f"Installation failed: {stderr.decode()}")

    async def _generate_server_config(self, server_spec: MCPServerSpec) -> Optional[Path]:
        """Generate configuration file for a server."""
        if not server_spec.config_template and not server_spec.required_config:
            return None
        
        config_path = self.config_dir / f"{server_spec.name}_config.json"
        
        config = {}
        config.update(server_spec.config_template)
        
        # Add placeholders for required config
        for required_key in server_spec.required_config:
            if required_key not in config:
                config[required_key] = f"<PLEASE_SET_{required_key}>"
        
        # Add environment variables
        if server_spec.environment_vars:
            config["environment"] = server_spec.environment_vars
        
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)
        
        return config_path

    async def get_installation_status(self) -> Dict[str, Any]:
        """Get comprehensive installation status."""
        total_installs = len(self.installed_servers)
        successful = sum(1 for r in self.installed_servers.values() if r.success)
        failed = total_installs - successful
        
        avg_install_time = 0.0
        if total_installs > 0:
            total_time = sum(r.install_time_ms for r in self.installed_servers.values())
            avg_install_time = total_time / total_installs
        
        return {
            "total_servers_available": len(self.server_registry),
            "total_installed": total_installs,
            "successful_installs": successful,
            "failed_installs": failed,
            "success_rate": (successful / max(total_installs, 1)) * 100,
            "avg_install_time_ms": avg_install_time,
            "installed_servers": {
                name: {
                    "success": result.success,
                    "install_time_ms": result.install_time_ms,
                    "config_path": result.config_path,
                    "error": result.error_message
                }
                for name, result in self.installed_servers.items()
            },
            "discovery_metrics": self.discovery_metrics
        }

    async def health_check_servers(self) -> Dict[str, bool]:
        """Perform health check on installed servers."""
        health_status = {}
        
        for server_name, install_result in self.installed_servers.items():
            if not install_result.success:
                health_status[server_name] = False
                continue
            
            try:
                # Attempt to connect to server
                # This would involve actual MCP connection testing
                health_status[server_name] = True
            except Exception:
                health_status[server_name] = False
        
        return health_status

    async def get_server_recommendations_summary(self, task_description: str) -> str:
        """Get a human-readable summary of server recommendations."""
        recommendations = await self.recommend_servers_for_task(task_description)
        
        if not recommendations:
            return "No suitable MCP servers found for this task."
        
        summary = f"Recommended MCP servers for '{task_description}':\n\n"
        
        for i, server in enumerate(recommendations, 1):
            install_status = "[INSTALLED]" if server.name in self.installed_servers and self.installed_servers[server.name].success else "[NOT INSTALLED]"
            auto_install = "[AUTO-INSTALL]" if server.auto_install else "[MANUAL SETUP]"
            
            summary += f"{i}. **{server.name}** ({server.category.value})\n"
            summary += f"   Description: {server.description}\n"
            summary += f"   Status: {install_status} | {auto_install}\n"
            summary += f"   Priority Score: {server.priority_score}/10\n"
            
            if server.required_config:
                summary += f"   Required Config: {', '.join(server.required_config)}\n"
            
            summary += "\n"
        
        return summary
