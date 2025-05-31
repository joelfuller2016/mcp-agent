"""
Dynamic Agent Factory for autonomous MCP-Agent.

This module creates specialized agents dynamically based on task requirements
and available MCP tools.
"""

import logging
from typing import Dict, List, Optional, Set, Any, Type
from dataclasses import dataclass

from mcp_agent.agents.agent import Agent
from mcp_agent.workflows.llm.augmented_llm import AugmentedLLM
from mcp_agent.workflows.llm.augmented_llm_openai import OpenAIAugmentedLLM
from mcp_agent.workflows.llm.augmented_llm_anthropic import AnthropicAugmentedLLM

from .tool_capability_mapper import ToolCapabilityMapper, ToolCategory, MCPServerProfile
from .task_analyzer import TaskAnalysis, TaskType


@dataclass
class AgentSpecialization:
    """Defines an agent's specialization."""
    name: str
    role: str
    instruction: str
    capabilities: Set[ToolCategory]
    server_names: List[str]
    priority: int  # 1-5, higher is more important
    
    
@dataclass
class AgentBlueprint:
    """Blueprint for creating an agent."""
    specialization: AgentSpecialization
    preferred_llm: Type[AugmentedLLM]
    configuration: Dict[str, Any]


class DynamicAgentFactory:
    """
    Creates specialized agents dynamically based on task requirements.
    
    This factory analyzes task requirements and available tools to create
    the most appropriate agents for the job, including specialized roles
    like researchers, analyzers, creators, and coordinators.
    """
    
    def __init__(self, tool_mapper: ToolCapabilityMapper):
        self.tool_mapper = tool_mapper
        self.logger = logging.getLogger(__name__)
        
        # Predefined agent specializations
        self.agent_specializations = {
            "researcher": AgentSpecialization(
                name="researcher",
                role="Information Research Specialist",
                instruction=(
                    "You are a research specialist focused on gathering comprehensive "
                    "information from multiple sources. You excel at finding relevant "
                    "data, analyzing search results, and synthesizing information from "
                    "web sources and documents."
                ),
                capabilities={ToolCategory.SEARCH, ToolCategory.WEB, ToolCategory.ANALYSIS},
                server_names=["fetch", "brave-search", "filesystem"],
                priority=4
            ),
            "analyst": AgentSpecialization(
                name="analyst",
                role="Data Analysis Specialist", 
                instruction=(
                    "You are a data analysis specialist who excels at examining data, "
                    "identifying patterns, calculating metrics, and generating insights. "
                    "You can work with databases, spreadsheets, and perform statistical analysis."
                ),
                capabilities={ToolCategory.DATA, ToolCategory.ANALYSIS, ToolCategory.REASONING},
                server_names=["mcp-server-sqlite", "filesystem"],
                priority=5
            ),
            "creator": AgentSpecialization(
                name="creator",
                role="Content Creation Specialist",
                instruction=(
                    "You are a content creation specialist who excels at generating "
                    "high-quality written content, documents, reports, and creative materials. "
                    "You focus on clarity, structure, and engaging presentation."
                ),
                capabilities={ToolCategory.CREATION, ToolCategory.FILE_SYSTEM},
                server_names=["filesystem"],
                priority=4
            ),
            "developer": AgentSpecialization(
                name="developer",
                role="Software Development Specialist",
                instruction=(
                    "You are a software development specialist skilled in coding, "
                    "version control, project management, and technical implementation. "
                    "You excel at creating, modifying, and managing code projects."
                ),
                capabilities={ToolCategory.DEVELOPMENT, ToolCategory.FILE_SYSTEM},
                server_names=["mcp-server-git", "github", "filesystem"],
                priority=5
            ),
            "automator": AgentSpecialization(
                name="automator",
                role="Workflow Automation Specialist",
                instruction=(
                    "You are a workflow automation specialist who excels at creating "
                    "automated processes, managing tasks, and orchestrating complex workflows. "
                    "You focus on efficiency and process optimization."
                ),
                capabilities={ToolCategory.AUTOMATION, ToolCategory.DATA},
                server_names=["n8n-workflow-builder", "taskmanager"],
                priority=4
            ),
            "web_specialist": AgentSpecialization(
                name="web_specialist",
                role="Web Automation Specialist",
                instruction=(
                    "You are a web automation specialist skilled in browser automation, "
                    "web scraping, form filling, and website interaction. You excel at "
                    "navigating websites and extracting information."
                ),
                capabilities={ToolCategory.WEB, ToolCategory.AUTOMATION},
                server_names=["puppeteer", "browsermcp", "fetch"],
                priority=3
            ),
            "reasoner": AgentSpecialization(
                name="reasoner",
                role="Cognitive Reasoning Specialist",
                instruction=(
                    "You are a cognitive reasoning specialist who excels at complex "
                    "problem-solving, logical analysis, and strategic thinking. You "
                    "use advanced reasoning tools to solve difficult problems."
                ),
                capabilities={ToolCategory.COGNITIVE, ToolCategory.REASONING},
                server_names=["mcp-reasoner", "sequential-thinking"],
                priority=5
            ),
            "coordinator": AgentSpecialization(
                name="coordinator",
                role="Multi-Agent Coordinator",
                instruction=(
                    "You are a coordination specialist who excels at orchestrating "
                    "multiple agents, managing workflows, and ensuring smooth "
                    "collaboration between different specialists."
                ),
                capabilities={ToolCategory.AUTOMATION, ToolCategory.REASONING},
                server_names=["taskmanager", "github-project-manager"],
                priority=3
            ),
            "communicator": AgentSpecialization(
                name="communicator",
                role="Communication Specialist",
                instruction=(
                    "You are a communication specialist who excels at managing "
                    "external communications, notifications, and messaging across "
                    "different platforms and channels."
                ),
                capabilities={ToolCategory.COMMUNICATION},
                server_names=["email", "slack"],  # These might not be available
                priority=2
            )
        }
        
        # Task type to preferred agent mapping
        self.task_agent_preferences = {
            TaskType.INFORMATION_RETRIEVAL: ["researcher", "web_specialist"],
            TaskType.CONTENT_CREATION: ["creator", "researcher"],
            TaskType.DATA_ANALYSIS: ["analyst", "researcher"],
            TaskType.FILE_OPERATIONS: ["developer", "automator"],
            TaskType.WEB_AUTOMATION: ["web_specialist", "automator"],
            TaskType.CODE_DEVELOPMENT: ["developer", "analyst"],
            TaskType.PROJECT_MANAGEMENT: ["coordinator", "automator"],
            TaskType.RESEARCH: ["researcher", "analyst", "reasoner"],
            TaskType.COMMUNICATION: ["communicator", "coordinator"],
            TaskType.REASONING: ["reasoner", "analyst"]
        }
        
    def create_agents_for_task(
        self, 
        task_analysis: TaskAnalysis,
        max_agents: int = 5
    ) -> List[Agent]:
        """
        Create specialized agents for a specific task.
        
        Args:
            task_analysis: Analysis of the task requirements
            max_agents: Maximum number of agents to create
            
        Returns:
            List of specialized agents ready for the task
        """
        self.logger.debug(f"Creating agents for {task_analysis.task_type.value} task")
        
        # Get relevant agent specializations
        blueprints = self._select_agent_blueprints(task_analysis, max_agents)
        
        # Create agents from blueprints
        agents = []
        for blueprint in blueprints:
            try:
                agent = self._create_agent_from_blueprint(blueprint)
                agents.append(agent)
                self.logger.info(f"Created {blueprint.specialization.role}")
            except Exception as e:
                self.logger.warning(
                    f"Failed to create {blueprint.specialization.name}: {e}"
                )
                
        if not agents:
            # Fallback: create a general-purpose agent
            agents = [self._create_fallback_agent(task_analysis)]
            
        self.logger.info(f"Created {len(agents)} agents for task execution")
        return agents
        
    def create_specialized_agent(
        self,
        specialization_name: str,
        custom_instruction: Optional[str] = None
    ) -> Optional[Agent]:
        """
        Create a specific specialized agent.
        
        Args:
            specialization_name: Name of the specialization
            custom_instruction: Override default instruction
            
        Returns:
            Specialized agent or None if creation fails
        """
        if specialization_name not in self.agent_specializations:
            self.logger.error(f"Unknown specialization: {specialization_name}")
            return None
            
        specialization = self.agent_specializations[specialization_name]
        
        # Override instruction if provided
        if custom_instruction:
            specialization = AgentSpecialization(
                name=specialization.name,
                role=specialization.role,
                instruction=custom_instruction,
                capabilities=specialization.capabilities,
                server_names=specialization.server_names,
                priority=specialization.priority
            )
            
        blueprint = self._create_blueprint(specialization)
        return self._create_agent_from_blueprint(blueprint)
        
    def _select_agent_blueprints(
        self, 
        task_analysis: TaskAnalysis,
        max_agents: int
    ) -> List[AgentBlueprint]:
        """Select the best agent blueprints for the task."""
        blueprints = []
        
        # Get preferred agents for this task type
        preferred_agents = self.task_agent_preferences.get(
            task_analysis.task_type, ["researcher"]
        )
        
        # Score all specializations
        specialization_scores = {}
        for spec_name, specialization in self.agent_specializations.items():
            score = self._score_specialization(specialization, task_analysis)
            if score > 0:
                specialization_scores[spec_name] = score
                
        # Sort by score and preference
        scored_specs = []
        for spec_name, score in specialization_scores.items():
            preference_bonus = 0.5 if spec_name in preferred_agents else 0
            final_score = score + preference_bonus
            scored_specs.append((spec_name, final_score))
            
        # Sort by score descending
        scored_specs.sort(key=lambda x: x[1], reverse=True)
        
        # Create blueprints for top agents
        for spec_name, score in scored_specs[:max_agents]:
            specialization = self.agent_specializations[spec_name]
            blueprint = self._create_blueprint(specialization)
            blueprints.append(blueprint)
            
        return blueprints
        
    def _score_specialization(
        self, 
        specialization: AgentSpecialization,
        task_analysis: TaskAnalysis
    ) -> float:
        """Score how well a specialization matches the task."""
        score = 0.0
        
        # Capability overlap score
        required_caps = task_analysis.required_capabilities
        overlap = specialization.capabilities.intersection(required_caps)
        
        if required_caps:
            capability_score = len(overlap) / len(required_caps)
            score += capability_score * 0.6
            
        # Server availability score
        available_servers = set(self.tool_mapper.server_profiles.keys())
        spec_servers = set(specialization.server_names)
        server_overlap = spec_servers.intersection(available_servers)
        
        if spec_servers:
            server_score = len(server_overlap) / len(spec_servers)
            score += server_score * 0.3
            
        # Priority score
        priority_score = specialization.priority / 5.0
        score += priority_score * 0.1
        
        return score
        
    def _create_blueprint(self, specialization: AgentSpecialization) -> AgentBlueprint:
        """Create an agent blueprint from a specialization."""
        # Select LLM provider based on specialization
        if specialization.name in ["reasoner", "analyst"]:
            preferred_llm = AnthropicAugmentedLLM  # Better for reasoning
        else:
            preferred_llm = OpenAIAugmentedLLM  # Good general purpose
            
        # Filter server names to only available ones
        available_servers = set(self.tool_mapper.server_profiles.keys())
        available_spec_servers = [
            server for server in specialization.server_names
            if server in available_servers
        ]
        
        configuration = {
            "server_names": available_spec_servers,
            "timeout": 300,
            "retry_attempts": 2
        }
        
        return AgentBlueprint(
            specialization=specialization,
            preferred_llm=preferred_llm,
            configuration=configuration
        )
        
    def _create_agent_from_blueprint(self, blueprint: AgentBlueprint) -> Agent:
        """Create an actual agent from a blueprint."""
        spec = blueprint.specialization
        
        agent = Agent(
            name=spec.name,
            instruction=spec.instruction,
            server_names=blueprint.configuration["server_names"]
        )
        
        return agent
        
    def _create_fallback_agent(self, task_analysis: TaskAnalysis) -> Agent:
        """Create a general-purpose fallback agent."""
        # Get any available servers
        available_servers = [
            name for name, profile in self.tool_mapper.server_profiles.items()
            if profile.is_available
        ]
        
        # Limit to reasonable number
        server_names = available_servers[:3]
        
        instruction = (
            f"You are a general-purpose agent capable of handling "
            f"{task_analysis.task_type.value} tasks. Use the available tools "
            f"to complete the requested task efficiently."
        )
        
        return Agent(
            name="general_agent",
            instruction=instruction,
            server_names=server_names
        )
        
    def get_available_specializations(self) -> List[str]:
        """Get list of available agent specializations."""
        return list(self.agent_specializations.keys())
        
    def get_specialization_info(self, name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specialization."""
        if name not in self.agent_specializations:
            return None
            
        spec = self.agent_specializations[name]
        available_servers = set(self.tool_mapper.server_profiles.keys())
        spec_servers = set(spec.server_names)
        
        return {
            "name": spec.name,
            "role": spec.role,
            "instruction": spec.instruction,
            "capabilities": [cap.value for cap in spec.capabilities],
            "required_servers": spec.server_names,
            "available_servers": list(spec_servers.intersection(available_servers)),
            "missing_servers": list(spec_servers - available_servers),
            "priority": spec.priority,
            "effectiveness": len(spec_servers.intersection(available_servers)) / len(spec_servers)
        }
        
    def create_custom_agent(
        self,
        name: str,
        role: str,
        instruction: str,
        capabilities: List[str],
        max_servers: int = 3
    ) -> Agent:
        """
        Create a custom agent with specific capabilities.
        
        Args:
            name: Agent name
            role: Agent role description
            instruction: Custom instruction
            capabilities: List of required capability names
            max_servers: Maximum servers to assign
            
        Returns:
            Custom agent
        """
        # Convert capability names to categories
        capability_categories = set()
        for cap_name in capabilities:
            try:
                category = ToolCategory(cap_name.lower())
                capability_categories.add(category)
            except ValueError:
                self.logger.warning(f"Unknown capability: {cap_name}")
                
        # Find servers that provide these capabilities
        suitable_servers = []
        for server_name, profile in self.tool_mapper.server_profiles.items():
            if not profile.is_available:
                continue
                
            # Check if server provides any required capabilities
            if profile.categories.intersection(capability_categories):
                suitable_servers.append(server_name)
                
        # Limit to max_servers
        server_names = suitable_servers[:max_servers]
        
        if not server_names:
            self.logger.warning("No suitable servers found for custom agent")
            # Use any available server as fallback
            server_names = [
                name for name, profile in self.tool_mapper.server_profiles.items()
                if profile.is_available
            ][:1]
            
        return Agent(
            name=name,
            instruction=instruction,
            server_names=server_names
        )
        
    def get_factory_status(self) -> Dict[str, Any]:
        """Get status information about the factory."""
        total_specs = len(self.agent_specializations)
        available_servers = sum(
            1 for profile in self.tool_mapper.server_profiles.values()
            if profile.is_available
        )
        
        # Calculate effectiveness for each specialization
        spec_effectiveness = {}
        for name, spec in self.agent_specializations.items():
            info = self.get_specialization_info(name)
            spec_effectiveness[name] = info["effectiveness"] if info else 0.0
            
        return {
            "total_specializations": total_specs,
            "available_servers": available_servers,
            "total_servers": len(self.tool_mapper.server_profiles),
            "average_effectiveness": sum(spec_effectiveness.values()) / total_specs,
            "most_effective_specialization": max(
                spec_effectiveness, key=spec_effectiveness.get
            ),
            "least_effective_specialization": min(
                spec_effectiveness, key=spec_effectiveness.get
            ),
            "specialization_effectiveness": spec_effectiveness
        }
