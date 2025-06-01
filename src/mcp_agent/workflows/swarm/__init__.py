"""
MCP-Agent Swarm Workflow Pattern Module.

This module provides swarm-based collaborative agent patterns for complex problem solving.
Includes implementations for different LLM providers and a unified SwarmAgent interface.
"""

from .swarm import Swarm
from .swarm_anthropic import AnthropicSwarm
from .swarm_openai import OpenAISwarm
from .swarm_agent import SwarmAgent, create_swarm_agent

__all__ = ["Swarm", "AnthropicSwarm", "OpenAISwarm", "SwarmAgent", "create_swarm_agent"]
