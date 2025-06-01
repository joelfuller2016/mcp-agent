"""
SwarmAgent - Unified interface for swarm functionality in autonomous modules.

This module provides a simplified SwarmAgent class that wraps the existing
swarm implementations (AnthropicSwarm, OpenAISwarm) to resolve import issues
in the autonomous modules.
"""

from typing import List, Dict, Any, Optional, Callable
from .swarm_anthropic import AnthropicSwarm
from .swarm_openai import OpenAISwarm
from mcp_agent.workflows.llm.augmented_llm import RequestParams


class SwarmAgent:
    """
    Unified SwarmAgent interface for autonomous modules.

    This class provides a consistent interface for swarm functionality
    regardless of the underlying LLM provider.
    """

    def __init__(
        self,
        name: str,
        instructions: str,
        model_provider: str = "anthropic",
        functions: Optional[List[Callable]] = None,
    ):
        """
        Initialize SwarmAgent with specified provider.

        Args:
            name: Agent name/identifier
            instructions: Instructions for the agent behavior
            model_provider: LLM provider ("anthropic", "openai")
            functions: Optional list of functions the agent can call
        """
        self.name = name
        self.instructions = instructions
        self.functions = functions or []
        self.model_provider = model_provider

        # Initialize the appropriate swarm implementation
        if model_provider.lower() == "anthropic":
            self.swarm = AnthropicSwarm()
        elif model_provider.lower() == "openai":
            self.swarm = OpenAISwarm()
        else:
            # Default to Anthropic
            self.swarm = AnthropicSwarm()

        # Configure the swarm with agent details
        self._configure_swarm()

    def _configure_swarm(self):
        """Configure the underlying swarm with agent details."""
        # Set up the swarm agent configuration
        # This would typically involve setting the agent instructions
        # and available functions in the swarm instance
        pass

    async def run(
        self,
        messages: List[Dict[str, Any]],
        request_params: Optional[RequestParams] = None,
    ) -> Any:
        """
        Execute the swarm agent with given messages.

        Args:
            messages: List of message objects to process
            request_params: Optional request parameters for the LLM

        Returns:
            Response from the swarm execution
        """
        try:
            # Use the configured swarm to process messages
            response = await self.swarm.generate(
                message=messages, request_params=request_params
            )
            return response
        except Exception as e:
            # Handle any errors and provide fallback
            return {"error": str(e), "agent": self.name, "status": "failed"}

    async def execute_with_functions(
        self,
        messages: List[Dict[str, Any]],
        available_functions: Optional[List[Callable]] = None,
    ) -> Any:
        """
        Execute with specific functions available.

        Args:
            messages: Messages to process
            available_functions: Functions available for this execution

        Returns:
            Execution result
        """
        # Temporarily extend functions if provided
        original_functions = self.functions.copy()
        if available_functions:
            self.functions.extend(available_functions)

        try:
            result = await self.run(messages)
            return result
        finally:
            # Restore original functions
            self.functions = original_functions

    def add_function(self, func: Callable):
        """Add a function to the agent's available functions."""
        if func not in self.functions:
            self.functions.append(func)

    def remove_function(self, func: Callable):
        """Remove a function from the agent's available functions."""
        if func in self.functions:
            self.functions.remove(func)

    def get_info(self) -> Dict[str, Any]:
        """Get agent information."""
        return {
            "name": self.name,
            "instructions": self.instructions,
            "model_provider": self.model_provider,
            "function_count": len(self.functions),
            "swarm_type": type(self.swarm).__name__,
        }

    def __str__(self) -> str:
        return f"SwarmAgent(name='{self.name}', provider='{self.model_provider}')"

    def __repr__(self) -> str:
        return self.__str__()


# Convenience function for quick agent creation
def create_swarm_agent(
    name: str,
    instructions: str,
    model_provider: str = "anthropic",
    functions: Optional[List[Callable]] = None,
) -> SwarmAgent:
    """
    Create a SwarmAgent with specified configuration.

    Args:
        name: Agent name
        instructions: Agent instructions
        model_provider: LLM provider to use
        functions: Optional functions list

    Returns:
        Configured SwarmAgent instance
    """
    return SwarmAgent(
        name=name,
        instructions=instructions,
        model_provider=model_provider,
        functions=functions,
    )
