"""
Dynamic MCP Tool Installer for Autonomous MCP Agent

This module provides the capability to automatically install MCP servers on-demand
based on task requirements. It supports multiple installation methods and maintains
a registry of available tools.
"""

import asyncio
import subprocess
import logging
import os
import json
from typing import Dict, List, Optional, Set, Any, Tuple
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from .tool_discovery import ToolDiscovery, ToolCapability


class InstallationMethod(Enum):
    UVX = "uvx"
    NPM = "npm"
    PIP = "pip"
    CONDA = "conda"
    MANUAL = "manual"


@dataclass
class InstallationResult:
    """Result of MCP tool installation"""
    tool_name: str
    success: bool
    method: InstallationMethod
    command_used: str
    output: str
    error: str = ""
    installation_time: float = 0.0


class DynamicInstaller:
    """Dynamically installs MCP tools based on requirements"""
    
    def __init__(self, tool_discovery: ToolDiscovery):
        self.tool_discovery = tool_discovery
        self.logger = logging.getLogger(__name__)
        
        # Track installation status
        self.installation_cache: Dict[str, InstallationResult] = {}
        self.failed_installations: Set[str] = set()
        
        # Load installation database
        self._load_installation_database()
    
    def _load_installation_database(self):
        """Load database of known MCP tools and their installation methods"""
        self.installation_db = {
            # Official MCP servers
            "fetch": {
                "package": "mcp-server-fetch",
                "methods": [InstallationMethod.UVX],
                "commands": {
                    InstallationMethod.UVX: "uvx install mcp-server-fetch"
                },
                "description": "Fetch content from URLs and web endpoints"
            },
            "filesystem": {
                "package": "@modelcontextprotocol/server-filesystem",
                "methods": [InstallationMethod.NPM],
                "commands": {
                    InstallationMethod.NPM: "npm install -g @modelcontextprotocol/server-filesystem"
                },
                "description": "File system operations and content management"
            },
            "git": {
                "package": "mcp-server-git",
                "methods": [InstallationMethod.UVX],
                "commands": {
                    InstallationMethod.UVX: "uvx install mcp-server-git"
                },
                "description": "Git repository operations and version control"
            },
            "github": {
                "package": "mcp-server-github",
                "methods": [InstallationMethod.UVX],
                "commands": {
                    InstallationMethod.UVX: "uvx install mcp-server-github"
                },
                "description": "GitHub API integration"
            },
            "brave_search": {
                "package": "mcp-server-brave-search",
                "methods": [InstallationMethod.UVX],
                "commands": {
                    InstallationMethod.UVX: "uvx install mcp-server-brave-search"
                },
                "description": "Web search using Brave Search API"
            },
            "puppeteer": {
                "package": "mcp-server-puppeteer",
                "methods": [InstallationMethod.UVX],
                "commands": {
                    InstallationMethod.UVX: "uvx install mcp-server-puppeteer"
                },
                "description": "Browser automation and web scraping"
            },
            "sqlite": {
                "package": "mcp-server-sqlite",
                "methods": [InstallationMethod.UVX],
                "commands": {
                    InstallationMethod.UVX: "uvx install mcp-server-sqlite"
                },
                "description": "SQLite database operations"
            },
            "postgres": {
                "package": "mcp-server-postgres",
                "methods": [InstallationMethod.UVX],
                "commands": {
                    InstallationMethod.UVX: "uvx install mcp-server-postgres"
                },
                "description": "PostgreSQL database operations"
            },
            "slack": {
                "package": "mcp-server-slack",
                "methods": [InstallationMethod.UVX],
                "commands": {
                    InstallationMethod.UVX: "uvx install mcp-server-slack"
                },
                "description": "Slack messaging and communication"
            },
            "gdrive": {
                "package": "mcp-server-gdrive",
                "methods": [InstallationMethod.UVX],
                "commands": {
                    InstallationMethod.UVX: "uvx install mcp-server-gdrive"
                },
                "description": "Google Drive integration"
            },
            "time": {
                "package": "mcp-server-time",
                "methods": [InstallationMethod.UVX],
                "commands": {
                    InstallationMethod.UVX: "uvx install mcp-server-time"
                },
                "description": "Time and scheduling operations"
            },
            "memory": {
                "package": "mcp-server-memory",
                "methods": [InstallationMethod.UVX],
                "commands": {
                    InstallationMethod.UVX: "uvx install mcp-server-memory"
                },
                "description": "Memory and knowledge management"
            },
            "sequential_thinking": {
                "package": "mcp-server-sequential-thinking",
                "methods": [InstallationMethod.UVX],
                "commands": {
                    InstallationMethod.UVX: "uvx install mcp-server-sequential-thinking"
                },
                "description": "Sequential reasoning and problem solving"
            },
            "youtube": {
                "package": "mcp-server-youtube",
                "methods": [InstallationMethod.UVX],
                "commands": {
                    InstallationMethod.UVX: "uvx install mcp-server-youtube"
                },
                "description": "YouTube video search and analysis"
            },
            "todo": {
                "package": "mcp-server-todo",
                "methods": [InstallationMethod.UVX],
                "commands": {
                    InstallationMethod.UVX: "uvx install mcp-server-todo"
                },
                "description": "Task management and productivity"
            },
            "everart": {
                "package": "mcp-server-everart",
                "methods": [InstallationMethod.UVX],
                "commands": {
                    InstallationMethod.UVX: "uvx install mcp-server-everart"
                },
                "description": "AI image generation"
            },
            # Community servers
            "obsidian": {
                "package": "mcp-server-obsidian",
                "methods": [InstallationMethod.UVX],
                "commands": {
                    InstallationMethod.UVX: "uvx install mcp-server-obsidian"
                },
                "description": "Obsidian note-taking integration"
            },
            "notion": {
                "package": "mcp-server-notion",
                "methods": [InstallationMethod.UVX],
                "commands": {
                    InstallationMethod.UVX: "uvx install mcp-server-notion"
                },
                "description": "Notion workspace integration"
            },
            "jira": {
                "package": "mcp-server-jira",
                "methods": [InstallationMethod.UVX],
                "commands": {
                    InstallationMethod.UVX: "uvx install mcp-server-jira"
                },
                "description": "Jira issue tracking integration"
            }
        }
    
    async def ensure_tools_available(self, required_capabilities: List[str]) -> List[str]:
        """Ensure tools for required capabilities are available, installing if needed"""
        self.logger.info(f"Ensuring tools for capabilities: {required_capabilities}")
        
        # Find tools that match capabilities
        available_tools = self.tool_discovery.get_tools_for_capabilities(required_capabilities)
        
        if available_tools:
            self.logger.info(f"Found available tools: {available_tools}")
            return available_tools
        
        # No available tools, try to install some
        candidate_tools = self._find_installable_tools(required_capabilities)
        
        if not candidate_tools:
            self.logger.warning(f"No installable tools found for capabilities: {required_capabilities}")
            return []
        
        # Install the most promising tools
        installed_tools = []
        for tool_name in candidate_tools[:3]:  # Try up to 3 tools
            if await self.install_tool(tool_name):
                installed_tools.append(tool_name)
        
        # Refresh tool discovery after installation
        if installed_tools:
            await self.tool_discovery.discover_available_tools()
            return self.tool_discovery.get_tools_for_capabilities(required_capabilities)
        
        return []
    
    def _find_installable_tools(self, required_capabilities: List[str]) -> List[str]:
        """Find tools that can be installed to provide required capabilities"""
        candidate_tools = []
        
        for tool_name, tool_info in self.installation_db.items():
            # Skip if already failed to install
            if tool_name in self.failed_installations:
                continue
            
            # Check if tool provides any required capabilities
            if tool_name in self.tool_discovery.capability_registry:
                tool_capabilities = self.tool_discovery.capability_registry[tool_name].capabilities
                if any(cap in tool_capabilities for cap in required_capabilities):
                    candidate_tools.append(tool_name)
        
        # Sort by relevance (more matching capabilities = higher priority)
        def relevance_score(tool_name):
            if tool_name not in self.tool_discovery.capability_registry:
                return 0
            tool_capabilities = self.tool_discovery.capability_registry[tool_name].capabilities
            return sum(1 for cap in required_capabilities if cap in tool_capabilities)
        
        candidate_tools.sort(key=relevance_score, reverse=True)
        return candidate_tools
    
    async def install_tool(self, tool_name: str) -> bool:
        """Install a specific MCP tool"""
        if tool_name in self.installation_cache:
            result = self.installation_cache[tool_name]
            if result.success:
                self.logger.info(f"Tool {tool_name} already installed successfully")
                return True
            else:
                self.logger.warning(f"Tool {tool_name} previously failed to install")
                return False
        
        if tool_name not in self.installation_db:
            self.logger.error(f"Tool {tool_name} not found in installation database")
            return False
        
        tool_info = self.installation_db[tool_name]
        self.logger.info(f"Installing MCP tool: {tool_name}")
        
        # Try installation methods in order of preference
        for method in tool_info["methods"]:
            if await self._check_installation_method_available(method):
                result = await self._install_with_method(tool_name, method, tool_info)
                self.installation_cache[tool_name] = result
                
                if result.success:
                    self.logger.info(f"Successfully installed {tool_name} using {method.value}")
                    return True
                else:
                    self.logger.warning(f"Failed to install {tool_name} using {method.value}: {result.error}")
        
        # Mark as failed if all methods failed
        self.failed_installations.add(tool_name)
        self.logger.error(f"Failed to install {tool_name} with any method")
        return False
    
    async def _check_installation_method_available(self, method: InstallationMethod) -> bool:
        """Check if an installation method is available on the system"""
        try:
            if method == InstallationMethod.UVX:
                result = subprocess.run(["uvx", "--version"], capture_output=True, text=True, timeout=5)
                return result.returncode == 0
            
            elif method == InstallationMethod.NPM:
                result = subprocess.run(["npm", "--version"], capture_output=True, text=True, timeout=5)
                return result.returncode == 0
            
            elif method == InstallationMethod.PIP:
                result = subprocess.run(["pip", "--version"], capture_output=True, text=True, timeout=5)
                return result.returncode == 0
            
            elif method == InstallationMethod.CONDA:
                result = subprocess.run(["conda", "--version"], capture_output=True, text=True, timeout=5)
                return result.returncode == 0
            
            return False
        
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
            self.logger.debug(f"Installation method {method.value} not available: {e}")
            return False
    
    async def _install_with_method(self, tool_name: str, method: InstallationMethod,
                                 tool_info: Dict[str, Any]) -> InstallationResult:
        """Install tool using specific method"""
        import time
        start_time = time.time()
        
        command = tool_info["commands"][method]
        self.logger.debug(f"Running installation command: {command}")
        
        try:
            # Run installation command
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=os.environ.copy()
            )
            
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=300)  # 5 min timeout
            
            success = process.returncode == 0
            output = stdout.decode() if stdout else ""
            error = stderr.decode() if stderr else ""
            
            installation_time = time.time() - start_time
            
            return InstallationResult(
                tool_name=tool_name,
                success=success,
                method=method,
                command_used=command,
                output=output,
                error=error,
                installation_time=installation_time
            )
        
        except asyncio.TimeoutError:
            installation_time = time.time() - start_time
            return InstallationResult(
                tool_name=tool_name,
                success=False,
                method=method,
                command_used=command,
                output="",
                error="Installation timeout after 5 minutes",
                installation_time=installation_time
            )
        
        except Exception as e:
            installation_time = time.time() - start_time
            return InstallationResult(
                tool_name=tool_name,
                success=False,
                method=method,
                command_used=command,
                output="",
                error=f"Installation error: {str(e)}",
                installation_time=installation_time
            )
    
    async def install_tools_for_pattern(self, suggested_tools: List[str]) -> List[str]:
        """Install multiple tools needed for a pattern"""
        self.logger.info(f"Installing tools for pattern: {suggested_tools}")
        
        installed_tools = []
        
        # Install tools in parallel (but limit concurrency)
        semaphore = asyncio.Semaphore(3)  # Max 3 concurrent installations
        
        async def install_with_semaphore(tool_name: str) -> Optional[str]:
            async with semaphore:
                if await self.install_tool(tool_name):
                    return tool_name
                return None
        
        # Create installation tasks
        tasks = [install_with_semaphore(tool) for tool in suggested_tools]
        
        # Wait for all installations to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Collect successfully installed tools
        for result in results:
            if isinstance(result, str):  # Successfully installed tool name
                installed_tools.append(result)
            elif isinstance(result, Exception):
                self.logger.error(f"Installation task failed: {result}")
        
        self.logger.info(f"Successfully installed {len(installed_tools)} tools: {installed_tools}")
        return installed_tools
    
    async def suggest_additional_tools(self, current_capabilities: List[str]) -> List[str]:
        """Suggest additional tools that would complement current capabilities"""
        # Get complementary tools from tool discovery
        current_tools = self.tool_discovery.get_tools_for_capabilities(current_capabilities)
        suggestions = self.tool_discovery.suggest_complementary_tools(current_tools)
        
        # Filter to only installable tools
        installable_suggestions = [
            tool for tool in suggestions 
            if tool in self.installation_db and tool not in self.failed_installations
        ]
        
        return installable_suggestions[:3]  # Return top 3 suggestions
    
    def get_installation_status(self, tool_name: str) -> Optional[InstallationResult]:
        """Get installation status for a tool"""
        return self.installation_cache.get(tool_name)
    
    def get_installation_summary(self) -> Dict[str, Any]:
        """Get summary of all installation attempts"""
        successful = [name for name, result in self.installation_cache.items() if result.success]
        failed = [name for name, result in self.installation_cache.items() if not result.success]
        
        total_time = sum(result.installation_time for result in self.installation_cache.values())
        
        return {
            "total_attempts": len(self.installation_cache),
            "successful": len(successful),
            "failed": len(failed),
            "successful_tools": successful,
            "failed_tools": failed,
            "total_installation_time": total_time,
            "failed_permanently": list(self.failed_installations)
        }
    
    async def verify_installation(self, tool_name: str) -> bool:
        """Verify that a tool was installed correctly and is functional"""
        try:
            # Try to connect to the tool using tool discovery
            async with asyncio.timeout(10):
                server_info = await self.tool_discovery.get_server_info(tool_name)
                if server_info and server_info.get("connected", False):
                    self.logger.info(f"Verified {tool_name} is installed and functional")
                    return True
                else:
                    self.logger.warning(f"Tool {tool_name} installed but not functional")
                    return False
        
        except Exception as e:
            self.logger.error(f"Error verifying {tool_name}: {e}")
            return False
    
    async def uninstall_tool(self, tool_name: str) -> bool:
        """Uninstall a tool (if supported by the installation method)"""
        if tool_name not in self.installation_cache:
            self.logger.warning(f"Tool {tool_name} not found in installation cache")
            return False
        
        result = self.installation_cache[tool_name]
        if not result.success:
            self.logger.warning(f"Tool {tool_name} was not successfully installed")
            return False
        
        try:
            # Attempt uninstallation based on method used
            if result.method == InstallationMethod.UVX:
                uninstall_cmd = f"uvx uninstall {self.installation_db[tool_name]['package']}"
            elif result.method == InstallationMethod.NPM:
                uninstall_cmd = f"npm uninstall -g {self.installation_db[tool_name]['package']}"
            elif result.method == InstallationMethod.PIP:
                uninstall_cmd = f"pip uninstall -y {self.installation_db[tool_name]['package']}"
            else:
                self.logger.warning(f"Uninstallation not supported for method {result.method.value}")
                return False
            
            process = await asyncio.create_subprocess_shell(
                uninstall_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=60)
            
            if process.returncode == 0:
                self.logger.info(f"Successfully uninstalled {tool_name}")
                # Remove from cache
                del self.installation_cache[tool_name]
                self.failed_installations.discard(tool_name)
                return True
            else:
                error_msg = stderr.decode() if stderr else "Unknown error"
                self.logger.error(f"Failed to uninstall {tool_name}: {error_msg}")
                return False
        
        except Exception as e:
            self.logger.error(f"Error uninstalling {tool_name}: {e}")
            return False
    
    def clear_installation_cache(self):
        """Clear the installation cache (useful for testing)"""
        self.installation_cache.clear()
        self.failed_installations.clear()
        self.logger.info("Installation cache cleared")
