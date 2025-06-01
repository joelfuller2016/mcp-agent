"""
MCP Tool Capability Mapping System

This module provides intelligent capability mapping for MCP tools, categorizing
their functions and analyzing task requirements for optimal tool selection.
"""

import re
import asyncio
from typing import Dict, List, Set, Optional, Any
from dataclasses import dataclass
from enum import Enum
import json


class CapabilityCategory(Enum):
    """Main categories of MCP tool capabilities"""

    DEVELOPMENT = "development"
    SEARCH = "search"
    COGNITIVE = "cognitive"
    DATA = "data"
    AUTOMATION = "automation"
    COMMUNICATION = "communication"
    FILESYSTEM = "filesystem"
    NETWORK = "network"
    SECURITY = "security"
    MONITORING = "monitoring"


@dataclass
class ToolCapability:
    """Represents a specific capability of an MCP tool"""

    category: CapabilityCategory
    subcategory: str
    description: str
    keywords: List[str]
    complexity_level: int  # 1-5, where 5 is most complex
    reliability_score: float = 0.8  # 0.0-1.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category.value,
            "subcategory": self.subcategory,
            "description": self.description,
            "keywords": self.keywords,
            "complexity_level": self.complexity_level,
            "reliability_score": self.reliability_score,
        }


class CapabilityMapper:
    """
    Maps MCP tools to their capabilities and analyzes task requirements
    """

    def __init__(self):
        self.capability_definitions = self._initialize_capability_definitions()
        self.tool_patterns = self._initialize_tool_patterns()
        self.task_keywords = self._initialize_task_keywords()

    def _initialize_capability_definitions(self) -> Dict[str, List[ToolCapability]]:
        """Initialize known capability definitions for common MCP tools"""

        capabilities = {
            # Development tools
            "mcp-server-git": [
                ToolCapability(
                    CapabilityCategory.DEVELOPMENT,
                    "version_control",
                    "Git repository operations and version control",
                    ["git", "commit", "branch", "merge", "repository", "version"],
                    3,
                ),
                ToolCapability(
                    CapabilityCategory.DEVELOPMENT,
                    "code_history",
                    "Access code history and changes",
                    ["history", "diff", "changes", "log", "blame"],
                    2,
                ),
            ],
            "mcp-server-github": [
                ToolCapability(
                    CapabilityCategory.DEVELOPMENT,
                    "repository_management",
                    "GitHub repository operations",
                    ["github", "repo", "issues", "pull", "release"],
                    3,
                ),
                ToolCapability(
                    CapabilityCategory.COMMUNICATION,
                    "collaboration",
                    "Code collaboration and review",
                    ["review", "comments", "collaboration", "team"],
                    2,
                ),
            ],
            "filesystem": [
                ToolCapability(
                    CapabilityCategory.FILESYSTEM,
                    "file_operations",
                    "File and directory operations",
                    ["file", "directory", "read", "write", "create", "delete"],
                    1,
                ),
                ToolCapability(
                    CapabilityCategory.FILESYSTEM,
                    "file_search",
                    "Search and find files",
                    ["search", "find", "locate", "glob", "pattern"],
                    2,
                ),
            ],
            # Search tools
            "mcp-server-fetch": [
                ToolCapability(
                    CapabilityCategory.NETWORK,
                    "web_fetch",
                    "Fetch content from web URLs",
                    ["fetch", "url", "http", "web", "download", "content"],
                    2,
                )
            ],
            "brave-search": [
                ToolCapability(
                    CapabilityCategory.SEARCH,
                    "web_search",
                    "Web search capabilities",
                    ["search", "web", "internet", "query", "find", "lookup"],
                    2,
                )
            ],
            "browsermcp": [
                ToolCapability(
                    CapabilityCategory.AUTOMATION,
                    "browser_automation",
                    "Browser automation and control",
                    ["browser", "automation", "navigate", "click", "interact"],
                    4,
                )
            ],
            "puppeteer": [
                ToolCapability(
                    CapabilityCategory.AUTOMATION,
                    "web_automation",
                    "Advanced web automation and scraping",
                    ["scraping", "automation", "headless", "screenshot"],
                    4,
                )
            ],
            # Data tools
            "mcp-server-sqlite": [
                ToolCapability(
                    CapabilityCategory.DATA,
                    "database_sqlite",
                    "SQLite database operations",
                    ["sqlite", "database", "sql", "query", "store", "retrieve"],
                    3,
                )
            ],
            "mcp-server-postgres": [
                ToolCapability(
                    CapabilityCategory.DATA,
                    "database_postgres",
                    "PostgreSQL database operations",
                    ["postgres", "postgresql", "database", "sql", "query"],
                    4,
                )
            ],
            # Cognitive tools
            "sequential-thinking": [
                ToolCapability(
                    CapabilityCategory.COGNITIVE,
                    "reasoning",
                    "Sequential reasoning and problem solving",
                    ["reasoning", "thinking", "analysis", "problem", "solve"],
                    5,
                )
            ],
            "mcp-reasoner": [
                ToolCapability(
                    CapabilityCategory.COGNITIVE,
                    "advanced_reasoning",
                    "Advanced reasoning with multiple strategies",
                    ["reasoning", "analysis", "strategy", "decision", "logic"],
                    5,
                )
            ],
            "memory": [
                ToolCapability(
                    CapabilityCategory.DATA,
                    "knowledge_graph",
                    "Knowledge graph and memory operations",
                    ["memory", "knowledge", "graph", "relationships", "store"],
                    4,
                )
            ],
            # Project management tools
            "taskmanager": [
                ToolCapability(
                    CapabilityCategory.AUTOMATION,
                    "task_management",
                    "Task creation and management",
                    ["task", "todo", "manage", "organize", "plan"],
                    2,
                )
            ],
            "github-project-manager": [
                ToolCapability(
                    CapabilityCategory.DEVELOPMENT,
                    "project_management",
                    "GitHub project and milestone management",
                    ["project", "milestone", "roadmap", "planning", "github"],
                    3,
                )
            ],
            "n8n-workflow-builder": [
                ToolCapability(
                    CapabilityCategory.AUTOMATION,
                    "workflow_automation",
                    "Workflow creation and automation",
                    ["workflow", "automation", "trigger", "integration"],
                    4,
                )
            ],
        }

        return capabilities

    def _initialize_tool_patterns(self) -> Dict[str, CapabilityCategory]:
        """Initialize patterns to identify tool categories"""

        return {
            # Development patterns
            r".*git.*": CapabilityCategory.DEVELOPMENT,
            r".*github.*": CapabilityCategory.DEVELOPMENT,
            r".*code.*": CapabilityCategory.DEVELOPMENT,
            r".*repo.*": CapabilityCategory.DEVELOPMENT,
            # Search patterns
            r".*search.*": CapabilityCategory.SEARCH,
            r".*find.*": CapabilityCategory.SEARCH,
            r".*lookup.*": CapabilityCategory.SEARCH,
            # Data patterns
            r".*sql.*": CapabilityCategory.DATA,
            r".*database.*": CapabilityCategory.DATA,
            r".*db.*": CapabilityCategory.DATA,
            r".*memory.*": CapabilityCategory.DATA,
            # Automation patterns
            r".*automat.*": CapabilityCategory.AUTOMATION,
            r".*workflow.*": CapabilityCategory.AUTOMATION,
            r".*browser.*": CapabilityCategory.AUTOMATION,
            r".*puppeteer.*": CapabilityCategory.AUTOMATION,
            # Filesystem patterns
            r".*file.*": CapabilityCategory.FILESYSTEM,
            r".*filesystem.*": CapabilityCategory.FILESYSTEM,
            # Network patterns
            r".*fetch.*": CapabilityCategory.NETWORK,
            r".*http.*": CapabilityCategory.NETWORK,
            r".*url.*": CapabilityCategory.NETWORK,
            # Cognitive patterns
            r".*reasoning.*": CapabilityCategory.COGNITIVE,
            r".*think.*": CapabilityCategory.COGNITIVE,
            r".*analysis.*": CapabilityCategory.COGNITIVE,
        }

    def _initialize_task_keywords(self) -> Dict[str, List[str]]:
        """Initialize task keyword mappings to capabilities"""

        return {
            # Development keywords
            "development:git": [
                "git",
                "commit",
                "push",
                "pull",
                "branch",
                "merge",
                "repository",
                "version control",
                "code history",
                "diff",
                "checkout",
            ],
            "development:github": [
                "github",
                "issues",
                "pull request",
                "repository",
                "release",
                "collaboration",
                "code review",
                "fork",
                "clone",
            ],
            "development:project_management": [
                "project",
                "milestone",
                "roadmap",
                "planning",
                "tracking",
                "kanban",
                "sprint",
                "backlog",
            ],
            # Search keywords
            "search:web": [
                "search",
                "find",
                "lookup",
                "google",
                "web",
                "internet",
                "query",
                "research",
                "information",
            ],
            # Data keywords
            "data:database": [
                "database",
                "sql",
                "query",
                "store",
                "retrieve",
                "persist",
                "table",
                "record",
                "data",
            ],
            "data:knowledge_graph": [
                "memory",
                "knowledge",
                "graph",
                "relationships",
                "entities",
                "connections",
                "recall",
                "remember",
            ],
            # Filesystem keywords
            "filesystem:operations": [
                "file",
                "directory",
                "folder",
                "read",
                "write",
                "create",
                "delete",
                "copy",
                "move",
                "exists",
            ],
            "filesystem:search": [
                "find file",
                "search file",
                "locate",
                "glob",
                "pattern match",
            ],
            # Automation keywords
            "automation:browser": [
                "browser",
                "navigate",
                "click",
                "interact",
                "automate",
                "screenshot",
                "scrape",
                "web automation",
            ],
            "automation:workflow": [
                "workflow",
                "automation",
                "trigger",
                "integration",
                "n8n",
                "process",
                "pipeline",
            ],
            "automation:task": [
                "task",
                "todo",
                "manage",
                "organize",
                "plan",
                "schedule",
            ],
            # Network keywords
            "network:fetch": ["fetch", "download", "url", "http", "web content", "get"],
            # Cognitive keywords
            "cognitive:reasoning": [
                "analyze",
                "reason",
                "think",
                "problem solve",
                "decision",
                "logic",
                "strategy",
                "complex reasoning",
            ],
        }

    async def analyze_server_config(
        self, server_name: str, server_config: Dict[str, Any]
    ) -> List[ToolCapability]:
        """
        Analyze a server configuration to determine its capabilities

        Args:
            server_name: Name of the MCP server
            server_config: Configuration dictionary

        Returns:
            List of capabilities for this server
        """

        # Check if we have predefined capabilities
        if server_name in self.capability_definitions:
            return self.capability_definitions[server_name]

        # Try to infer capabilities from name and config
        capabilities = []

        # Analyze server name patterns
        for pattern, category in self.tool_patterns.items():
            if re.match(pattern, server_name, re.IGNORECASE):
                # Create a generic capability for this category
                capability = ToolCapability(
                    category=category,
                    subcategory="general",
                    description=f"General {category.value} capabilities",
                    keywords=[server_name, category.value],
                    complexity_level=2,
                )
                capabilities.append(capability)
                break

        # If no patterns matched, create a generic capability
        if not capabilities:
            capability = ToolCapability(
                category=CapabilityCategory.AUTOMATION,
                subcategory="custom",
                description=f"Custom MCP server: {server_name}",
                keywords=[server_name, "custom"],
                complexity_level=3,
            )
            capabilities.append(capability)

        return capabilities

    async def get_default_capabilities(self, server_name: str) -> List[ToolCapability]:
        """Get default capabilities for a known server name"""

        if server_name in self.capability_definitions:
            return self.capability_definitions[server_name]

        # Try pattern matching
        for pattern, category in self.tool_patterns.items():
            if re.match(pattern, server_name, re.IGNORECASE):
                capability = ToolCapability(
                    category=category,
                    subcategory="general",
                    description=f"General {category.value} capabilities",
                    keywords=[server_name, category.value],
                    complexity_level=2,
                )
                return [capability]

        return []

    async def analyze_task_requirements(self, task_description: str) -> List[str]:
        """
        Analyze a task description to extract required capabilities

        Args:
            task_description: Natural language task description

        Returns:
            List of capability strings (e.g., ["development:git", "search:web"])
        """

        task_lower = task_description.lower()
        required_capabilities = []

        # Analyze task text against keyword mappings
        for capability, keywords in self.task_keywords.items():
            # Check if any of the capability keywords appear in the task
            matches = sum(1 for keyword in keywords if keyword.lower() in task_lower)

            # If enough keywords match, include this capability
            if matches > 0:
                # Calculate confidence based on keyword matches
                confidence = min(1.0, matches / len(keywords) * 3)

                if confidence > 0.1:  # Threshold for inclusion
                    required_capabilities.append(capability)

        # Additional analysis for complex patterns
        additional_caps = await self._analyze_complex_patterns(task_description)
        required_capabilities.extend(additional_caps)

        # Remove duplicates while preserving order
        seen = set()
        unique_caps = []
        for cap in required_capabilities:
            if cap not in seen:
                seen.add(cap)
                unique_caps.append(cap)

        return unique_caps

    async def _analyze_complex_patterns(self, task_description: str) -> List[str]:
        """Analyze complex patterns in task descriptions"""

        additional_capabilities = []
        task_lower = task_description.lower()

        # Pattern: Creating/building something
        if any(word in task_lower for word in ["create", "build", "make", "generate"]):
            if any(word in task_lower for word in ["file", "document", "code"]):
                additional_capabilities.append("filesystem:operations")

        # Pattern: Research/analysis tasks
        if any(
            word in task_lower
            for word in ["research", "analyze", "study", "investigate"]
        ):
            additional_capabilities.append("search:web")
            additional_capabilities.append("cognitive:reasoning")

        # Pattern: Data processing
        if any(word in task_lower for word in ["data", "database", "store", "save"]):
            additional_capabilities.append("data:database")

        # Pattern: Web interaction
        if any(
            word in task_lower
            for word in ["website", "web page", "browser", "navigate"]
        ):
            additional_capabilities.append("automation:browser")

        # Pattern: Planning/organizing
        if any(
            word in task_lower for word in ["plan", "organize", "schedule", "manage"]
        ):
            additional_capabilities.append("automation:task")

        return additional_capabilities

    def get_capability_complexity(self, capability_string: str) -> int:
        """Get the complexity level of a capability (1-5)"""

        # Find the first tool that provides this capability
        for tool_capabilities in self.capability_definitions.values():
            for cap in tool_capabilities:
                cap_string = f"{cap.category.value}:{cap.subcategory}"
                if cap_string == capability_string:
                    return cap.complexity_level

        # Default complexity for unknown capabilities
        return 3

    def get_capability_description(self, capability_string: str) -> str:
        """Get human-readable description of a capability"""

        for tool_capabilities in self.capability_definitions.values():
            for cap in tool_capabilities:
                cap_string = f"{cap.category.value}:{cap.subcategory}"
                if cap_string == capability_string:
                    return cap.description

        # Generate description from capability string
        category, subcategory = capability_string.split(":", 1)
        return f"{subcategory.replace('_', ' ').title()} capabilities in {category}"

    async def suggest_tool_combinations(
        self, required_capabilities: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Suggest optimal tool combinations for required capabilities

        Args:
            required_capabilities: List of required capability strings

        Returns:
            List of tool combination suggestions with scores
        """

        suggestions = []

        # Calculate total complexity
        total_complexity = sum(
            self.get_capability_complexity(cap) for cap in required_capabilities
        )

        # Determine execution strategy based on complexity
        if total_complexity <= 3:
            strategy = "direct"
        elif total_complexity <= 8:
            strategy = "parallel"
        elif total_complexity <= 15:
            strategy = "orchestrated"
        else:
            strategy = "swarm"

        suggestion = {
            "capabilities": required_capabilities,
            "total_complexity": total_complexity,
            "recommended_strategy": strategy,
            "reasoning": self._get_strategy_reasoning(strategy, total_complexity),
            "tools_needed": len(
                set(cap.split(":")[0] for cap in required_capabilities)
            ),
        }

        suggestions.append(suggestion)

        return suggestions

    def _get_strategy_reasoning(self, strategy: str, complexity: int) -> str:
        """Get reasoning for strategy selection"""

        reasoning_map = {
            "direct": f"Simple task (complexity {complexity}) can be handled by a single agent",
            "parallel": f"Moderate complexity ({complexity}) benefits from parallel execution",
            "orchestrated": f"High complexity ({complexity}) requires orchestrated coordination",
            "swarm": f"Very high complexity ({complexity}) needs dynamic multi-agent coordination",
        }

        return reasoning_map.get(
            strategy, f"Strategy selected based on complexity {complexity}"
        )
