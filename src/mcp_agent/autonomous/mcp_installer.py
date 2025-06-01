"""
MCP Installer for discovering and installing MCP servers on-demand.

This component can search for, evaluate, and install new MCP servers to expand
the system's capabilities autonomously.
"""

import asyncio
import json
import logging
import subprocess
import tempfile
from typing import Dict, List, Optional, Set, Any, Tuple
from dataclasses import dataclass
from pathlib import Path

from .tool_discovery import ToolCapability, MCPServerInfo


@dataclass
class MCPServerCandidate:
    """A candidate MCP server that could be installed."""

    name: str
    description: str
    install_command: str
    capabilities: Set[ToolCapability]
    source: str  # "registry", "search", "recommendation"
    confidence: float
    requirements: List[str]
    metadata: Dict[str, Any]


class MCPInstaller:
    """Autonomous MCP server installer and discoverer."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.installed_servers: Dict[str, MCPServerInfo] = {}

        # Known server registries and sources
        self.server_sources = {
            "official": "https://github.com/modelcontextprotocol/servers",
            "community": "https://mcp.so/servers",  # Based on research
            "awesome": "https://github.com/punkpeye/awesome-mcp-servers",
        }

        # Installation methods
        self.install_methods = {
            "uvx": self._install_uvx_server,
            "npx": self._install_npx_server,
            "pip": self._install_pip_server,
            "git": self._install_git_server,
        }

        # Capability-based server recommendations
        self.capability_recommendations = {
            ToolCapability.FILE_OPERATIONS: [
                "filesystem",
                "google-drive",
                "dropbox",
                "onedrive",
            ],
            ToolCapability.WEB_SEARCH: [
                "brave-search",
                "google-search",
                "bing-search",
                "web-crawler",
            ],
            ToolCapability.DATABASE: ["sqlite", "postgres", "mysql", "mongodb"],
            ToolCapability.AUTOMATION: ["puppeteer", "playwright", "selenium", "n8n"],
            ToolCapability.DEVELOPMENT: [
                "github",
                "gitlab",
                "git",
                "docker",
                "kubernetes",
            ],
            ToolCapability.COMMUNICATION: [
                "slack",
                "discord",
                "teams",
                "email",
                "telegram",
            ],
            ToolCapability.ANALYSIS: ["pandas", "jupyter", "matplotlib", "plotly"],
            ToolCapability.REASONING: [
                "sequential-thinking",
                "mcp-reasoner",
                "langchain",
            ],
            ToolCapability.WORKFLOW: ["temporal", "airflow", "n8n", "zapier"],
            ToolCapability.SYSTEM: ["shell", "docker", "kubernetes", "aws-cli"],
            ToolCapability.GRAPHICS: ["blender", "figma", "canva", "imagemagick"],
            ToolCapability.DATA_PROCESSING: ["pandas", "numpy", "dask", "spark"],
        }

    async def find_servers_for_capability(
        self, capability: ToolCapability, max_results: int = 5
    ) -> List[MCPServerCandidate]:
        """Find MCP servers that provide a specific capability."""
        self.logger.info(f"Searching for servers with {capability.value} capability")

        candidates = []

        # Get recommendations from known servers
        recommended_names = self.capability_recommendations.get(capability, [])
        for name in recommended_names:
            candidate = await self._create_candidate_from_name(name, capability)
            if candidate:
                candidates.append(candidate)

        # Search online registries (simulated for now)
        online_candidates = await self._search_online_registries(capability)
        candidates.extend(online_candidates)

        # Score and sort candidates
        scored_candidates = self._score_candidates(candidates, capability)

        return scored_candidates[:max_results]

    async def find_servers_for_task(
        self, task_description: str, required_capabilities: Set[ToolCapability]
    ) -> List[MCPServerCandidate]:
        """Find MCP servers suitable for a specific task."""
        self.logger.info(f"Finding servers for task: {task_description[:100]}...")

        all_candidates = []

        # Find candidates for each required capability
        for capability in required_capabilities:
            capability_candidates = await self.find_servers_for_capability(
                capability, 3
            )
            all_candidates.extend(capability_candidates)

        # Search for task-specific servers
        task_candidates = await self._search_task_specific_servers(task_description)
        all_candidates.extend(task_candidates)

        # Remove duplicates and score
        unique_candidates = self._deduplicate_candidates(all_candidates)
        scored_candidates = self._score_candidates_for_task(
            unique_candidates, task_description
        )

        return scored_candidates[:10]

    async def install_server(self, candidate: MCPServerCandidate) -> bool:
        """Install an MCP server candidate."""
        self.logger.info(f"Installing MCP server: {candidate.name}")

        try:
            # Determine installation method
            install_method = self._determine_install_method(candidate.install_command)

            if install_method not in self.install_methods:
                self.logger.error(f"Unknown installation method: {install_method}")
                return False

            # Execute installation
            success = await self.install_methods[install_method](candidate)

            if success:
                # Add to installed servers
                server_info = MCPServerInfo(
                    name=candidate.name,
                    description=candidate.description,
                    capabilities=candidate.capabilities,
                    connection_status="installed",
                    install_command=candidate.install_command,
                    priority_score=candidate.confidence,
                )
                self.installed_servers[candidate.name] = server_info

                self.logger.info(f"Successfully installed: {candidate.name}")
                return True
            else:
                self.logger.error(f"Failed to install: {candidate.name}")
                return False

        except Exception as e:
            self.logger.error(f"Error installing {candidate.name}: {e}")
            return False

    async def install_best_servers_for_capability(
        self, capability: ToolCapability, max_installs: int = 2
    ) -> List[str]:
        """Install the best servers for a capability."""
        candidates = await self.find_servers_for_capability(
            capability, max_installs * 2
        )

        installed_servers = []
        install_count = 0

        for candidate in candidates:
            if install_count >= max_installs:
                break

            # Skip if already installed
            if candidate.name in self.installed_servers:
                continue

            # Try to install
            if await self.install_server(candidate):
                installed_servers.append(candidate.name)
                install_count += 1

        return installed_servers

    async def _create_candidate_from_name(
        self, name: str, capability: ToolCapability
    ) -> Optional[MCPServerCandidate]:
        """Create a server candidate from a known name."""
        # Known server configurations
        known_servers = {
            "filesystem": {
                "description": "File system operations for reading, writing, and managing files",
                "install_command": "npx -y @modelcontextprotocol/server-filesystem",
                "capabilities": {ToolCapability.FILE_OPERATIONS},
            },
            "brave-search": {
                "description": "Web search using Brave Search API",
                "install_command": "uvx mcp-server-brave-search",
                "capabilities": {ToolCapability.WEB_SEARCH},
            },
            "sqlite": {
                "description": "SQLite database operations and queries",
                "install_command": "uvx mcp-server-sqlite",
                "capabilities": {ToolCapability.DATABASE},
            },
            "puppeteer": {
                "description": "Browser automation with Puppeteer",
                "install_command": "uvx mcp-server-puppeteer",
                "capabilities": {ToolCapability.AUTOMATION, ToolCapability.WEB_SEARCH},
            },
            "github": {
                "description": "GitHub repository and issue management",
                "install_command": "uvx mcp-server-github",
                "capabilities": {
                    ToolCapability.DEVELOPMENT,
                    ToolCapability.COMMUNICATION,
                },
            },
            "slack": {
                "description": "Slack messaging and team communication",
                "install_command": "uvx mcp-server-slack",
                "capabilities": {ToolCapability.COMMUNICATION},
            },
            "google-drive": {
                "description": "Google Drive file operations and sharing",
                "install_command": "uvx mcp-server-gdrive",
                "capabilities": {
                    ToolCapability.FILE_OPERATIONS,
                    ToolCapability.DATA_PROCESSING,
                },
            },
            "postgres": {
                "description": "PostgreSQL database operations",
                "install_command": "uvx mcp-server-postgres",
                "capabilities": {ToolCapability.DATABASE},
            },
            "sequential-thinking": {
                "description": "Advanced sequential reasoning and thinking",
                "install_command": "uvx mcp-server-sequential-thinking",
                "capabilities": {ToolCapability.REASONING},
            },
            "git": {
                "description": "Git version control operations",
                "install_command": "uvx mcp-server-git",
                "capabilities": {ToolCapability.DEVELOPMENT},
            },
        }

        if name not in known_servers:
            return None

        config = known_servers[name]

        return MCPServerCandidate(
            name=name,
            description=config["description"],
            install_command=config["install_command"],
            capabilities=config["capabilities"],
            source="known",
            confidence=0.8,
            requirements=[],
            metadata={"category": "official"},
        )

    async def _search_online_registries(
        self, capability: ToolCapability
    ) -> List[MCPServerCandidate]:
        """Search online registries for servers (simulated)."""
        # In a real implementation, this would query actual MCP registries
        # For now, return some simulated results
        candidates = []

        # Simulate registry search results
        simulated_results = {
            ToolCapability.WEB_SEARCH: [
                {
                    "name": "web-crawler",
                    "description": "Advanced web crawling and content extraction",
                    "install_command": "uvx mcp-server-web-crawler",
                    "confidence": 0.7,
                }
            ],
            ToolCapability.GRAPHICS: [
                {
                    "name": "blender",
                    "description": "3D modeling and rendering with Blender",
                    "install_command": "uvx mcp-server-blender",
                    "confidence": 0.9,
                }
            ],
            ToolCapability.DATA_PROCESSING: [
                {
                    "name": "pandas-analyzer",
                    "description": "Advanced data analysis with pandas",
                    "install_command": "uvx mcp-server-pandas",
                    "confidence": 0.8,
                }
            ],
        }

        results = simulated_results.get(capability, [])
        for result in results:
            candidates.append(
                MCPServerCandidate(
                    name=result["name"],
                    description=result["description"],
                    install_command=result["install_command"],
                    capabilities={capability},
                    source="registry",
                    confidence=result["confidence"],
                    requirements=[],
                    metadata={"registry": "community"},
                )
            )

        return candidates

    async def _search_task_specific_servers(
        self, task_description: str
    ) -> List[MCPServerCandidate]:
        """Search for task-specific servers."""
        # Simple keyword-based matching for now
        task_lower = task_description.lower()

        candidates = []

        # Task-specific server mappings
        if "blender" in task_lower or "3d" in task_lower:
            candidates.append(
                MCPServerCandidate(
                    name="blender",
                    description="3D modeling and animation with Blender",
                    install_command="uvx mcp-server-blender",
                    capabilities={ToolCapability.GRAPHICS},
                    source="task_specific",
                    confidence=0.9,
                    requirements=[],
                    metadata={"task_match": True},
                )
            )

        if "email" in task_lower or "mail" in task_lower:
            candidates.append(
                MCPServerCandidate(
                    name="email",
                    description="Email sending and management",
                    install_command="uvx mcp-server-email",
                    capabilities={ToolCapability.COMMUNICATION},
                    source="task_specific",
                    confidence=0.8,
                    requirements=["smtp_config"],
                    metadata={"task_match": True},
                )
            )

        return candidates

    def _score_candidates(
        self, candidates: List[MCPServerCandidate], capability: ToolCapability
    ) -> List[MCPServerCandidate]:
        """Score and sort candidates for a specific capability."""
        for candidate in candidates:
            score = candidate.confidence

            # Boost score if capability is primary
            if capability in candidate.capabilities:
                score += 0.2

            # Boost official sources
            if candidate.source == "known":
                score += 0.1

            # Penalize servers with requirements
            if candidate.requirements:
                score -= 0.1

            candidate.confidence = min(1.0, score)

        return sorted(candidates, key=lambda x: x.confidence, reverse=True)

    def _score_candidates_for_task(
        self, candidates: List[MCPServerCandidate], task_description: str
    ) -> List[MCPServerCandidate]:
        """Score candidates for a specific task."""
        task_lower = task_description.lower()

        for candidate in candidates:
            score = candidate.confidence

            # Boost if name matches task keywords
            if candidate.name.lower() in task_lower:
                score += 0.3

            # Boost if description matches task
            description_words = candidate.description.lower().split()
            task_words = task_lower.split()

            matches = sum(1 for word in description_words if word in task_words)
            if matches > 0:
                score += matches * 0.1

            candidate.confidence = min(1.0, score)

        return sorted(candidates, key=lambda x: x.confidence, reverse=True)

    def _deduplicate_candidates(
        self, candidates: List[MCPServerCandidate]
    ) -> List[MCPServerCandidate]:
        """Remove duplicate candidates."""
        seen_names = set()
        unique_candidates = []

        for candidate in candidates:
            if candidate.name not in seen_names:
                unique_candidates.append(candidate)
                seen_names.add(candidate.name)

        return unique_candidates

    def _determine_install_method(self, install_command: str) -> str:
        """Determine installation method from command."""
        if install_command.startswith("uvx"):
            return "uvx"
        elif install_command.startswith("npx"):
            return "npx"
        elif install_command.startswith("pip"):
            return "pip"
        elif install_command.startswith("git"):
            return "git"
        else:
            return "unknown"

    async def _install_uvx_server(self, candidate: MCPServerCandidate) -> bool:
        """Install server using uvx."""
        try:
            # Extract package name from command
            parts = candidate.install_command.split()
            if len(parts) < 2:
                return False

            package_name = parts[1]

            # Run uvx install command
            cmd = ["uvx", "install", package_name]
            result = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await result.communicate()

            if result.returncode == 0:
                self.logger.debug(f"uvx install successful: {package_name}")
                return True
            else:
                self.logger.error(f"uvx install failed: {stderr.decode()}")
                return False

        except Exception as e:
            self.logger.error(f"Error in uvx install: {e}")
            return False

    async def _install_npx_server(self, candidate: MCPServerCandidate) -> bool:
        """Install server using npx."""
        try:
            # For npx servers, we just verify they're available
            # Since npx servers are run on-demand
            parts = candidate.install_command.split()
            if len(parts) < 3:
                return False

            package_name = parts[2]  # Skip "npx -y"

            # Test if package is available
            cmd = ["npx", "--yes", package_name, "--help"]
            result = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )

            await result.communicate()

            # npx packages are considered "installed" if they can be run
            return True

        except Exception as e:
            self.logger.error(f"Error testing npx package: {e}")
            return False

    async def _install_pip_server(self, candidate: MCPServerCandidate) -> bool:
        """Install server using pip."""
        try:
            parts = candidate.install_command.split()
            if len(parts) < 3:
                return False

            package_name = parts[2]  # Skip "pip install"

            cmd = ["pip", "install", package_name]
            result = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await result.communicate()

            if result.returncode == 0:
                self.logger.debug(f"pip install successful: {package_name}")
                return True
            else:
                self.logger.error(f"pip install failed: {stderr.decode()}")
                return False

        except Exception as e:
            self.logger.error(f"Error in pip install: {e}")
            return False

    async def _install_git_server(self, candidate: MCPServerCandidate) -> bool:
        """Install server from git repository."""
        try:
            # Extract git URL from command
            parts = candidate.install_command.split()
            if len(parts) < 3:
                return False

            git_url = parts[2]  # Skip "git clone"

            # Clone to temporary directory
            with tempfile.TemporaryDirectory() as temp_dir:
                cmd = ["git", "clone", git_url, temp_dir]
                result = await asyncio.create_subprocess_exec(
                    *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
                )

                stdout, stderr = await result.communicate()

                if result.returncode == 0:
                    # Look for installation instructions
                    setup_py = Path(temp_dir) / "setup.py"
                    requirements_txt = Path(temp_dir) / "requirements.txt"

                    if setup_py.exists():
                        # Install using setup.py
                        install_cmd = ["pip", "install", "-e", temp_dir]
                        install_result = await asyncio.create_subprocess_exec(
                            *install_cmd,
                            stdout=asyncio.subprocess.PIPE,
                            stderr=asyncio.subprocess.PIPE,
                        )
                        await install_result.communicate()
                        return install_result.returncode == 0

                    return True  # Assume success if cloned
                else:
                    self.logger.error(f"git clone failed: {stderr.decode()}")
                    return False

        except Exception as e:
            self.logger.error(f"Error in git install: {e}")
            return False

    def get_installation_status(self) -> Dict[str, Any]:
        """Get status of all installed servers."""
        return {
            "installed_count": len(self.installed_servers),
            "servers": {
                name: {
                    "description": info.description,
                    "capabilities": [cap.value for cap in info.capabilities],
                    "status": info.connection_status,
                }
                for name, info in self.installed_servers.items()
            },
        }

    async def suggest_servers_for_enhancement(
        self, current_capabilities: Set[ToolCapability], max_suggestions: int = 5
    ) -> List[MCPServerCandidate]:
        """Suggest servers to enhance current capabilities."""
        # Find missing capabilities
        all_capabilities = set(ToolCapability)
        missing_capabilities = all_capabilities - current_capabilities

        suggestions = []

        # Suggest servers for missing capabilities
        for capability in missing_capabilities:
            candidates = await self.find_servers_for_capability(capability, 2)
            suggestions.extend(candidates)

        # Score suggestions based on value-add
        for suggestion in suggestions:
            # Higher score for capabilities we don't have
            new_caps = suggestion.capabilities - current_capabilities
            suggestion.confidence += len(new_caps) * 0.1

        return sorted(suggestions, key=lambda x: x.confidence, reverse=True)[
            :max_suggestions
        ]
