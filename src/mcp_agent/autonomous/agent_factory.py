"""
Dynamic Agent Factory

This module provides dynamic creation of specialized agents based on task
requirements and available MCP tools for autonomous coordination.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
import json

from ..agents.agent import Agent
from ..workflows.swarm.swarm_agent import SwarmAgent
from .discovery import AutonomousDiscovery, MCPToolInfo, DiscoveryStatus


@dataclass
class AgentTemplate:
    """Template for creating specialized agents"""

    name: str
    instruction: str
    server_names: List[str]
    agent_type: str = "standard"  # "standard", "swarm", "specialist"
    capabilities_focus: List[str] = None
    personality_traits: List[str] = None


class DynamicAgentFactory:
    """
    Factory for creating specialized agents dynamically based on requirements

    Creates agents optimized for specific capabilities, tools, and task types
    with appropriate instructions and configurations.
    """

    def __init__(self, discovery: AutonomousDiscovery):
        self.discovery = discovery
        self.logger = logging.getLogger(__name__)

        # Agent templates for different specializations
        self.agent_templates = self._initialize_agent_templates()

        # Created agents cache
        self.created_agents: Dict[str, Agent] = {}

        # Agent performance tracking
        self.agent_performance: Dict[str, Dict[str, float]] = {}

    def _initialize_agent_templates(self) -> Dict[str, AgentTemplate]:
        """Initialize templates for different types of agents"""

        templates = {
            # Development specialists
            "git_specialist": AgentTemplate(
                name="git_specialist",
                instruction="You are a Git version control specialist. You excel at repository operations, branching strategies, merge conflict resolution, and maintaining clean commit histories.",
                server_names=["mcp-server-git"],
                capabilities_focus=[
                    "development:version_control",
                    "development:code_history",
                ],
                personality_traits=["methodical", "detail-oriented", "systematic"],
            ),
            "github_specialist": AgentTemplate(
                name="github_specialist",
                instruction="You are a GitHub collaboration expert. You specialize in repository management, issue tracking, pull request workflows, and team collaboration features.",
                server_names=["mcp-server-github"],
                capabilities_focus=[
                    "development:repository_management",
                    "communication:collaboration",
                ],
                personality_traits=["collaborative", "organized", "communicative"],
            ),
            "code_analyst": AgentTemplate(
                name="code_analyst",
                instruction="You are a code analysis specialist. You excel at examining codebases, identifying patterns, analyzing dependencies, and providing insights about code quality and structure.",
                server_names=["filesystem", "mcp-server-git", "mcp-server-github"],
                capabilities_focus=["development:analysis", "filesystem:search"],
                personality_traits=["analytical", "thorough", "insightful"],
            ),
            # Search and research specialists
            "web_researcher": AgentTemplate(
                name="web_researcher",
                instruction="You are a web research specialist. You excel at finding information online, evaluating source credibility, and synthesizing research from multiple sources.",
                server_names=["brave-search", "mcp-server-fetch"],
                capabilities_focus=["search:web", "network:web_fetch"],
                personality_traits=["curious", "thorough", "discerning"],
            ),
            "information_gatherer": AgentTemplate(
                name="information_gatherer",
                instruction="You are an information gathering expert. You specialize in collecting, organizing, and presenting information from various sources in a structured manner.",
                server_names=["brave-search", "mcp-server-fetch", "filesystem"],
                capabilities_focus=["search:web", "filesystem:operations"],
                personality_traits=["organized", "comprehensive", "systematic"],
            ),
            # Data specialists
            "data_analyst": AgentTemplate(
                name="data_analyst",
                instruction="You are a data analysis specialist. You excel at working with databases, analyzing data patterns, and extracting meaningful insights from structured information.",
                server_names=["mcp-server-sqlite", "memory"],
                capabilities_focus=["data:database", "data:knowledge_graph"],
                personality_traits=["analytical", "precise", "logical"],
            ),
            "knowledge_manager": AgentTemplate(
                name="knowledge_manager",
                instruction="You are a knowledge management expert. You specialize in organizing information, maintaining knowledge graphs, and facilitating information retrieval and connections.",
                server_names=["memory", "filesystem"],
                capabilities_focus=["data:knowledge_graph", "filesystem:operations"],
                personality_traits=["organized", "systematic", "connective"],
            ),
            # Automation specialists
            "workflow_architect": AgentTemplate(
                name="workflow_architect",
                instruction="You are a workflow automation architect. You excel at designing efficient processes, creating automation workflows, and optimizing task sequences.",
                server_names=["n8n-workflow-builder", "taskmanager"],
                capabilities_focus=[
                    "automation:workflow_automation",
                    "automation:task_management",
                ],
                personality_traits=["systematic", "efficient", "forward-thinking"],
            ),
            "browser_automator": AgentTemplate(
                name="browser_automator",
                instruction="You are a browser automation specialist. You excel at web scraping, automated testing, and programmatic web interactions.",
                server_names=["browsermcp", "puppeteer"],
                capabilities_focus=[
                    "automation:browser_automation",
                    "automation:web_automation",
                ],
                personality_traits=["precise", "methodical", "adaptive"],
            ),
            "task_coordinator": AgentTemplate(
                name="task_coordinator",
                instruction="You are a task coordination specialist. You excel at organizing work, managing dependencies, and ensuring smooth execution of complex multi-step processes.",
                server_names=["taskmanager", "github-project-manager"],
                capabilities_focus=[
                    "automation:task_management",
                    "development:project_management",
                ],
                personality_traits=["organized", "coordinated", "reliable"],
            ),
            # Cognitive specialists
            "reasoning_expert": AgentTemplate(
                name="reasoning_expert",
                instruction="You are an advanced reasoning specialist. You excel at complex problem solving, logical analysis, and strategic thinking using sophisticated reasoning methods.",
                server_names=["mcp-reasoner", "sequential-thinking"],
                capabilities_focus=[
                    "cognitive:reasoning",
                    "cognitive:advanced_reasoning",
                ],
                personality_traits=["logical", "strategic", "thorough"],
            ),
            "analytical_thinker": AgentTemplate(
                name="analytical_thinker",
                instruction="You are an analytical thinking expert. You specialize in breaking down complex problems, systematic analysis, and step-by-step reasoning approaches.",
                server_names=["sequential-thinking"],
                capabilities_focus=["cognitive:reasoning"],
                personality_traits=["systematic", "methodical", "clear-thinking"],
            ),
            # File and system specialists
            "file_manager": AgentTemplate(
                name="file_manager",
                instruction="You are a file system specialist. You excel at file operations, directory management, and organizing digital assets efficiently.",
                server_names=["filesystem"],
                capabilities_focus=[
                    "filesystem:file_operations",
                    "filesystem:file_search",
                ],
                personality_traits=["organized", "systematic", "careful"],
            ),
            # Generalist agents
            "versatile_assistant": AgentTemplate(
                name="versatile_assistant",
                instruction="You are a versatile AI assistant capable of handling diverse tasks. You adapt your approach based on the specific requirements and available tools.",
                server_names=[],  # Will be populated dynamically
                capabilities_focus=[],
                personality_traits=["adaptable", "helpful", "resourceful"],
            ),
            "coordinator": AgentTemplate(
                name="coordinator",
                instruction="You are a coordination specialist. You excel at managing complex workflows, synthesizing inputs from multiple sources, and ensuring coherent final outcomes.",
                server_names=[],
                capabilities_focus=[],
                personality_traits=["coordinated", "synthesizing", "holistic"],
            ),
        }

        return templates

    async def create_agent(
        self,
        name: str,
        instruction: str,
        server_names: List[str],
        capabilities: Optional[List[str]] = None,
    ) -> Agent:
        """
        Create a new agent with specified configuration

        Args:
            name: Agent name
            instruction: Agent instruction/purpose
            server_names: List of MCP server names to use
            capabilities: Optional list of capability focuses

        Returns:
            Configured Agent instance
        """

        self.logger.info(f"Creating agent '{name}' with servers: {server_names}")

        # Ensure all required servers are available
        available_servers = await self._ensure_servers_available(server_names)

        # Create the agent
        agent = Agent(
            name=name, instruction=instruction, server_names=available_servers
        )

        # Cache the agent
        agent_key = f"{name}_{hash(instruction)}_{hash(tuple(available_servers))}"
        self.created_agents[agent_key] = agent

        # Initialize performance tracking
        self.agent_performance[agent_key] = {
            "success_rate": 0.0,
            "avg_response_time": 0.0,
            "total_tasks": 0,
            "successful_tasks": 0,
        }

        self.logger.info(
            f"Created agent '{name}' with {len(available_servers)} servers"
        )
        return agent

    async def create_swarm_agent(
        self,
        name: str,
        instruction: str,
        server_names: List[str],
        handoff_functions: Optional[List] = None,
    ) -> SwarmAgent:
        """
        Create a SwarmAgent for multi-agent coordination

        Args:
            name: Agent name
            instruction: Agent instruction
            server_names: List of MCP server names
            handoff_functions: Optional handoff functions for swarm coordination

        Returns:
            Configured SwarmAgent instance
        """

        self.logger.info(f"Creating swarm agent '{name}' with servers: {server_names}")

        # Ensure servers are available
        available_servers = await self._ensure_servers_available(server_names)

        # Create swarm agent
        swarm_agent = SwarmAgent(
            name=name, instruction=instruction, server_names=available_servers
        )

        if handoff_functions:
            swarm_agent.functions.extend(handoff_functions)

        return swarm_agent

    async def create_specialized_agent(
        self,
        capability_requirements: List[str],
        available_tools: Optional[List[MCPToolInfo]] = None,
    ) -> Agent:
        """
        Create a specialized agent based on capability requirements

        Args:
            capability_requirements: List of required capabilities
            available_tools: Available MCP tools (auto-discovered if not provided)

        Returns:
            Specialized Agent optimized for the required capabilities
        """

        if available_tools is None:
            discovered_tools = await self.discovery.discover_available_tools()
            available_tools = list(discovered_tools.values())

        # Find the best template match
        best_template = await self._find_best_template(
            capability_requirements, available_tools
        )

        # Find required tools for capabilities
        required_tools = await self._find_tools_for_capabilities(
            capability_requirements, available_tools
        )

        # Customize the template
        customized_template = await self._customize_template(
            best_template, capability_requirements, required_tools
        )

        # Create the agent
        agent = await self.create_agent(
            name=customized_template.name,
            instruction=customized_template.instruction,
            server_names=customized_template.server_names,
            capabilities=capability_requirements,
        )

        return agent

    async def create_agent_team(
        self, capability_requirements: List[str], team_size: Optional[int] = None
    ) -> List[Agent]:
        """
        Create a team of specialized agents for complex tasks

        Args:
            capability_requirements: Required capabilities across the team
            team_size: Optional team size (auto-determined if not specified)

        Returns:
            List of specialized agents forming a team
        """

        # Group capabilities by category
        capability_groups = self._group_capabilities_by_category(
            capability_requirements
        )

        # Determine team size if not specified
        if team_size is None:
            team_size = min(len(capability_groups), 4)  # Max 4 agents per team

        team = []
        available_tools = list(
            (await self.discovery.discover_available_tools()).values()
        )

        # Create agents for each capability group
        for i, (category, capabilities) in enumerate(capability_groups.items()):
            if i >= team_size:
                break

            agent = await self.create_specialized_agent(capabilities, available_tools)
            team.append(agent)

        self.logger.info(f"Created agent team of {len(team)} specialists")
        return team

    async def _ensure_servers_available(self, server_names: List[str]) -> List[str]:
        """Ensure all required servers are available, installing if necessary"""

        available_servers = []

        for server_name in server_names:
            # Check if server is in discovery registry
            if server_name in self.discovery.discovered_tools:
                tool_info = self.discovery.discovered_tools[server_name]

                # Install if not already installed
                if tool_info.status != DiscoveryStatus.INSTALLED:
                    success = await self.discovery.install_tool(server_name)
                    if success:
                        available_servers.append(server_name)
                    else:
                        self.logger.warning(f"Failed to install server {server_name}")
                else:
                    available_servers.append(server_name)
            else:
                self.logger.warning(
                    f"Server {server_name} not found in discovery registry"
                )

        return available_servers

    async def _find_best_template(
        self, capability_requirements: List[str], available_tools: List[MCPToolInfo]
    ) -> AgentTemplate:
        """Find the best agent template for the given requirements"""

        best_template = None
        best_score = 0.0

        for template_name, template in self.agent_templates.items():
            score = self._score_template_match(template, capability_requirements)

            if score > best_score:
                best_score = score
                best_template = template

        # If no good match found, use versatile assistant
        if best_template is None or best_score < 0.3:
            best_template = self.agent_templates["versatile_assistant"]

        return best_template

    def _score_template_match(
        self, template: AgentTemplate, capability_requirements: List[str]
    ) -> float:
        """Score how well a template matches capability requirements"""

        if not template.capabilities_focus:
            return 0.1  # Low score for generic templates

        # Calculate overlap between template capabilities and requirements
        template_caps = set(template.capabilities_focus)
        required_caps = set(capability_requirements)

        intersection = template_caps.intersection(required_caps)
        union = template_caps.union(required_caps)

        if not union:
            return 0.0

        # Jaccard similarity with bonus for exact matches
        jaccard_score = len(intersection) / len(union)
        exact_match_bonus = (
            len(intersection) / len(required_caps) if required_caps else 0
        )

        return (jaccard_score * 0.7) + (exact_match_bonus * 0.3)

    async def _find_tools_for_capabilities(
        self, capabilities: List[str], available_tools: List[MCPToolInfo]
    ) -> List[str]:
        """Find tools that provide the required capabilities"""

        required_tools = set()

        for capability in capabilities:
            # Find tools that provide this capability
            matching_tools = await self.discovery.get_tools_for_capability(capability)

            # Add available tools
            for tool in matching_tools:
                if any(t.name == tool.name for t in available_tools):
                    required_tools.add(tool.name)

        return list(required_tools)

    async def _customize_template(
        self,
        template: AgentTemplate,
        capability_requirements: List[str],
        required_tools: List[str],
    ) -> AgentTemplate:
        """Customize a template for specific requirements"""

        # Create a copy of the template
        customized = AgentTemplate(
            name=template.name,
            instruction=template.instruction,
            server_names=template.server_names.copy(),
            agent_type=template.agent_type,
            capabilities_focus=template.capabilities_focus.copy()
            if template.capabilities_focus
            else [],
            personality_traits=template.personality_traits.copy()
            if template.personality_traits
            else [],
        )

        # Add required tools not already in template
        for tool in required_tools:
            if tool not in customized.server_names:
                customized.server_names.append(tool)

        # Enhance instruction with specific capabilities
        if capability_requirements:
            cap_descriptions = []
            for cap in capability_requirements:
                desc = self.discovery.capability_mapper.get_capability_description(cap)
                cap_descriptions.append(desc)

            if cap_descriptions:
                customized.instruction += (
                    f" You specialize in: {', '.join(cap_descriptions)}."
                )

        # Add personality context if traits exist
        if customized.personality_traits:
            traits_text = ", ".join(customized.personality_traits)
            customized.instruction += f" Your approach is {traits_text}."

        return customized

    def _group_capabilities_by_category(
        self, capabilities: List[str]
    ) -> Dict[str, List[str]]:
        """Group capabilities by their main category"""

        groups = {}

        for capability in capabilities:
            category = capability.split(":")[0]

            if category not in groups:
                groups[category] = []

            groups[category].append(capability)

        return groups

    async def update_agent_performance(
        self, agent_key: str, success: bool, response_time: float
    ):
        """Update performance metrics for an agent"""

        if agent_key not in self.agent_performance:
            return

        metrics = self.agent_performance[agent_key]
        metrics["total_tasks"] += 1

        if success:
            metrics["successful_tasks"] += 1

        # Update success rate
        metrics["success_rate"] = metrics["successful_tasks"] / metrics["total_tasks"]

        # Update average response time (exponential moving average)
        alpha = 0.1
        metrics["avg_response_time"] = (
            alpha * response_time + (1 - alpha) * metrics["avg_response_time"]
        )

        self.logger.debug(
            f"Updated performance for agent {agent_key}: "
            f"success_rate={metrics['success_rate']:.2f}"
        )

    def get_agent_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary for all created agents"""

        return {
            "total_agents_created": len(self.created_agents),
            "agent_performance": self.agent_performance,
            "available_templates": list(self.agent_templates.keys()),
        }

    async def cleanup_unused_agents(self, max_idle_time: float = 3600):
        """Clean up agents that haven't been used recently"""

        # This is a placeholder for future implementation
        # Would track agent usage and clean up idle agents
        pass
