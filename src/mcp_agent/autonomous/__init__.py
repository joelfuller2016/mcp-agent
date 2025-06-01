"""
Autonomous agent capabilities for MCP-Agent.

This module provides advanced autonomous features including:
- AutonomousOrchestrator: Self-managing workflow execution
- DynamicAgentFactory: Runtime agent creation based on requirements  
- TaskAnalyzer: Intelligent task decomposition and planning
- ToolDiscoveryAgent: Automatic capability detection and mapping
- AutonomousDecisionEngine: Strategic decision making for workflows
- MetaCoordinator: High-level orchestration and supervision
"""

# Import the actual implementations
from .autonomous_orchestrator import AutonomousOrchestrator
from .dynamic_agent_factory import DynamicAgentFactory
from .task_analyzer import TaskAnalyzer
from .tool_discovery import ToolDiscoveryAgent, MCPServerInfo, ToolCapability
from .decision_engine import (
    AutonomousDecisionEngine,
    TaskAnalysis,
    StrategyRecommendation, 
    WorkflowPattern,
    TaskComplexity
)
from .meta_coordinator import MetaCoordinator

# For backward compatibility, provide aliases
DecisionEngine = AutonomousDecisionEngine
ToolDiscovery = ToolDiscoveryAgent

# Convenience functions for easy access
async def execute_autonomous_task(task_description: str, context=None):
    """Convenience function to execute a task autonomously."""
    orchestrator = AutonomousOrchestrator()
    await orchestrator.initialize()
    return await orchestrator.execute_autonomous_task(task_description, context)


async def analyze_task_requirements(task_description: str):
    """Convenience function to analyze task requirements."""
    analyzer = TaskAnalyzer()
    return analyzer.analyze_task(task_description)


def create_dynamic_agent(name: str, capabilities: list, **kwargs):
    """Convenience function to create a dynamic agent."""
    factory = DynamicAgentFactory()
    return factory.create_agent(name, capabilities, **kwargs)


async def discover_available_tools(connection_manager=None):
    """Convenience function to discover available MCP tools."""
    if connection_manager is None:
        # Import here to avoid circular imports
        from ..mcp.mcp_connection_manager import MCPConnectionManager
        from ..context import get_current_context
        context = get_current_context()
        connection_manager = MCPConnectionManager(context.server_registry)
    
    discovery_agent = ToolDiscoveryAgent(connection_manager)
    return await discovery_agent.discover_available_servers()


def analyze_and_recommend_strategy(task_description: str, available_servers=None):
    """Convenience function for decision analysis."""
    if available_servers is None:
        available_servers = []
    
    decision_engine = AutonomousDecisionEngine()
    return decision_engine.analyze_and_recommend(task_description, available_servers)


# Export all public classes and functions
__all__ = [
    # Core autonomous classes
    "AutonomousOrchestrator",
    "DynamicAgentFactory", 
    "TaskAnalyzer",
    "ToolDiscoveryAgent",
    "AutonomousDecisionEngine",
    "MetaCoordinator",
    
    # Data classes and enums
    "TaskAnalysis",
    "StrategyRecommendation",
    "WorkflowPattern", 
    "TaskComplexity",
    "MCPServerInfo",
    "ToolCapability",
    
    # Backward compatibility aliases
    "DecisionEngine",
    "ToolDiscovery",
    
    # Convenience functions
    "execute_autonomous_task",
    "analyze_task_requirements", 
    "create_dynamic_agent",
    "discover_available_tools",
    "analyze_and_recommend_strategy",
]
