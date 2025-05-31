"""
Autonomous Orchestrator for MCP-Agent.

This is the main coordinator that brings together all autonomous capabilities:
tool discovery, task analysis, strategy selection, and dynamic agent creation.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Type, Union
from dataclasses import dataclass
import time

from mcp_agent.app import MCPApp
from mcp_agent.config import Settings
from mcp_agent.workflows.llm.augmented_llm import AugmentedLLM
from mcp_agent.workflows.llm.augmented_llm_openai import OpenAIAugmentedLLM
from mcp_agent.workflows.llm.augmented_llm_anthropic import AnthropicAugmentedLLM
from mcp_agent.workflows.parallel.parallel_llm import ParallelLLM
from mcp_agent.workflows.router.router_llm import LLMRouter
from mcp_agent.workflows.orchestrator.orchestrator import Orchestrator
from mcp_agent.workflows.swarm.swarm_anthropic import AnthropicSwarm
from mcp_agent.workflows.swarm.swarm_agent import SwarmAgent
from mcp_agent.workflows.evaluator_optimizer.evaluator_optimizer_llm import EvaluatorOptimizerLLM

from .tool_capability_mapper import ToolCapabilityMapper
from .task_analyzer import TaskAnalyzer, TaskAnalysis, ExecutionPattern
from .strategy_selector import StrategyDecisionEngine, StrategyDecision
from .dynamic_agent_factory import DynamicAgentFactory


@dataclass
class ExecutionResult:
    """Results of autonomous task execution."""
    task_description: str
    execution_pattern: ExecutionPattern
    agents_used: List[str]
    execution_time: float
    result: Any
    success: bool
    error_message: Optional[str] = None
    strategy_confidence: str = ""
    total_steps: int = 0


@dataclass
class AutonomousConfig:
    """Configuration for autonomous execution."""
    max_agents: int = 5
    max_execution_time: int = 300
    prefer_simple_patterns: bool = False
    require_human_approval: bool = False
    default_llm_provider: str = "openai"
    enable_fallbacks: bool = True
    log_decisions: bool = True


class AutonomousOrchestrator:
    """
    Main orchestrator for autonomous MCP-Agent execution.
    
    This class coordinates all autonomous capabilities to automatically:
    1. Discover available tools
    2. Analyze task requirements  
    3. Select optimal execution strategy
    4. Create specialized agents
    5. Execute the task autonomously
    6. Handle errors and fallbacks
    """
    
    def __init__(
        self, 
        app: Optional[MCPApp] = None,
        config: Optional[AutonomousConfig] = None
    ):
        self.app = app or MCPApp(name="autonomous_mcp_agent")
        self.config = config or AutonomousConfig()
        self.logger = logging.getLogger(__name__)
        
        # Initialize autonomous components
        self.tool_mapper: Optional[ToolCapabilityMapper] = None
        self.task_analyzer = TaskAnalyzer()
        self.strategy_engine: Optional[StrategyDecisionEngine] = None
        self.agent_factory: Optional[DynamicAgentFactory] = None
        
        # Execution state
        self.is_initialized = False
        self.execution_history: List[ExecutionResult] = []
        
    async def initialize(self) -> bool:
        """
        Initialize the autonomous orchestrator.
        
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            self.logger.info("Initializing autonomous orchestrator...")
            
            # Initialize tool discovery
            self.tool_mapper = ToolCapabilityMapper(self.app.config)
            await self.tool_mapper.discover_all_capabilities()
            
            # Initialize strategy engine
            self.strategy_engine = StrategyDecisionEngine(self.tool_mapper)
            
            # Initialize agent factory
            self.agent_factory = DynamicAgentFactory(self.tool_mapper)
            
            self.is_initialized = True
            
            # Log capabilities summary
            summary = self.tool_mapper.get_capability_summary()
            self.logger.info(f"Initialized with {summary['available_servers']} available servers")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize autonomous orchestrator: {e}")
            return False
            
    async def execute_autonomous_task(
        self, 
        task_description: str,
        context: Optional[Dict[str, Any]] = None
    ) -> ExecutionResult:
        """
        Execute a task completely autonomously.
        
        Args:
            task_description: Natural language description of the task
            context: Optional context information
            
        Returns:
            ExecutionResult with outcome and details
        """
        start_time = time.time()
        
        if not self.is_initialized:
            if not await self.initialize():
                return ExecutionResult(
                    task_description=task_description,
                    execution_pattern=ExecutionPattern.DIRECT,
                    agents_used=[],
                    execution_time=0,
                    result=None,
                    success=False,
                    error_message="Failed to initialize autonomous orchestrator"
                )
        
        self.logger.info(f"Starting autonomous execution: {task_description}")
        
        try:
            # Step 1: Analyze the task
            task_analysis = self.task_analyzer.analyze_task(task_description)
            
            if self.config.log_decisions:
                self.logger.info(f"Task analysis: {self.task_analyzer.get_analysis_summary(task_analysis)}")
            
            # Step 2: Make strategy decision
            strategy_decision = self.strategy_engine.decide_strategy(task_analysis)
            
            if self.config.log_decisions:
                self.logger.info(f"Strategy decision: {self.strategy_engine.get_decision_summary(strategy_decision)}")
            
            # Step 3: Execute using the chosen strategy
            result = await self._execute_with_strategy(
                task_description, task_analysis, strategy_decision, context
            )
            
            execution_time = time.time() - start_time
            
            execution_result = ExecutionResult(
                task_description=task_description,
                execution_pattern=strategy_decision.recommended_pattern,
                agents_used=strategy_decision.required_servers,
                execution_time=execution_time,
                result=result,
                success=True,
                strategy_confidence=strategy_decision.confidence.value,
                total_steps=task_analysis.estimated_steps
            )
            
            self.execution_history.append(execution_result)
            self.logger.info(f"Task completed successfully in {execution_time:.2f}s")
            
            return execution_result
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_result = ExecutionResult(
                task_description=task_description,
                execution_pattern=ExecutionPattern.DIRECT,
                agents_used=[],
                execution_time=execution_time,
                result=None,
                success=False,
                error_message=str(e)
            )
            
            self.execution_history.append(error_result)
            self.logger.error(f"Task execution failed: {e}")
            
            # Try fallback if enabled
            if self.config.enable_fallbacks:
                return await self._execute_fallback(task_description, context)
            
            return error_result
            
    async def _execute_with_strategy(
        self,
        task_description: str,
        task_analysis: TaskAnalysis,
        strategy_decision: StrategyDecision,
        context: Optional[Dict[str, Any]]
    ) -> Any:
        """Execute task using the selected strategy."""
        pattern = strategy_decision.recommended_pattern
        
        if pattern == ExecutionPattern.DIRECT:
            return await self._execute_direct(task_description, strategy_decision)
        elif pattern == ExecutionPattern.PARALLEL:
            return await self._execute_parallel(task_description, task_analysis, strategy_decision)
        elif pattern == ExecutionPattern.ROUTER:
            return await self._execute_router(task_description, strategy_decision)
        elif pattern == ExecutionPattern.ORCHESTRATOR:
            return await self._execute_orchestrator(task_description, task_analysis, strategy_decision)
        elif pattern == ExecutionPattern.SWARM:
            return await self._execute_swarm(task_description, task_analysis, strategy_decision)
        elif pattern == ExecutionPattern.EVALUATOR_OPTIMIZER:
            return await self._execute_evaluator_optimizer(task_description, strategy_decision)
        else:
            # Default to direct execution
            return await self._execute_direct(task_description, strategy_decision)
            
    async def _execute_direct(
        self, 
        task_description: str, 
        strategy_decision: StrategyDecision
    ) -> Any:
        """Execute task using direct agent approach."""
        # Create a single agent for the task
        agents = self.agent_factory.create_agents_for_task(
            self.task_analyzer.analyze_task(task_description),
            max_agents=1
        )
        
        if not agents:
            raise Exception("No suitable agents could be created")
            
        agent = agents[0]
        
        async with self.app.run() as app_context:
            async with agent:
                llm = await agent.attach_llm(self._get_llm_class())
                result = await llm.generate_str(task_description)
                return result
                
    async def _execute_parallel(
        self,
        task_description: str,
        task_analysis: TaskAnalysis,
        strategy_decision: StrategyDecision
    ) -> Any:
        """Execute task using parallel workflow."""
        # Create multiple specialized agents
        fan_out_agents = self.agent_factory.create_agents_for_task(
            task_analysis, max_agents=min(3, self.config.max_agents - 1)
        )
        
        # Create a coordinator agent
        coordinator = self.agent_factory.create_specialized_agent(
            "coordinator",
            custom_instruction=(
                "You are a coordinator agent responsible for synthesizing "
                "results from multiple specialist agents into a coherent final answer."
            )
        )
        
        if not coordinator:
            coordinator = fan_out_agents[-1]  # Use last agent as coordinator
            fan_out_agents = fan_out_agents[:-1]
            
        async with self.app.run():
            parallel_llm = ParallelLLM(
                fan_in_agent=coordinator,
                fan_out_agents=fan_out_agents,
                llm_factory=self._get_llm_class()
            )
            
            result = await parallel_llm.generate_str(task_description)
            return result
            
    async def _execute_router(
        self, 
        task_description: str, 
        strategy_decision: StrategyDecision
    ) -> Any:
        """Execute task using router pattern."""
        # Create multiple agents for different capabilities
        agents = self.agent_factory.create_agents_for_task(
            self.task_analyzer.analyze_task(task_description),
            max_agents=self.config.max_agents
        )
        
        async with self.app.run():
            # Create router
            router = LLMRouter(
                llm=self._get_llm_class()(),
                agents=agents,
                functions=[]  # Could add utility functions here
            )
            
            # Route to best agent
            results = await router.route(task_description, top_k=1)
            
            if results:
                chosen_agent = results[0].result
                async with chosen_agent:
                    llm = await chosen_agent.attach_llm(self._get_llm_class())
                    result = await llm.generate_str(task_description)
                    return result
            else:
                raise Exception("Router failed to select an appropriate agent")
                
    async def _execute_orchestrator(
        self,
        task_description: str,
        task_analysis: TaskAnalysis,
        strategy_decision: StrategyDecision
    ) -> Any:
        """Execute task using orchestrator pattern."""
        # Create diverse agents for orchestration
        available_agents = self.agent_factory.create_agents_for_task(
            task_analysis, max_agents=self.config.max_agents
        )
        
        async with self.app.run():
            orchestrator = Orchestrator(
                llm_factory=self._get_llm_class(),
                available_agents=available_agents
            )
            
            result = await orchestrator.generate_str(task_description)
            return result
            
    async def _execute_swarm(
        self,
        task_description: str,
        task_analysis: TaskAnalysis,
        strategy_decision: StrategyDecision
    ) -> Any:
        """Execute task using swarm pattern."""
        # Create swarm agents
        base_agents = self.agent_factory.create_agents_for_task(
            task_analysis, max_agents=min(3, self.config.max_agents)
        )
        
        # Convert to swarm agents
        swarm_agents = []
        for agent in base_agents:
            swarm_agent = SwarmAgent(
                name=agent.name,
                instruction=agent.instruction,
                server_names=agent.server_names
            )
            swarm_agents.append(swarm_agent)
            
        if not swarm_agents:
            raise Exception("No agents available for swarm execution")
            
        async with self.app.run():
            # Use first agent as entry point
            swarm = AnthropicSwarm(
                agent=swarm_agents[0],
                context_variables={"task": task_description}
            )
            
            result = await swarm.generate_str(task_description)
            return result
            
    async def _execute_evaluator_optimizer(
        self, 
        task_description: str, 
        strategy_decision: StrategyDecision
    ) -> Any:
        """Execute task using evaluator-optimizer pattern."""
        # Create optimizer and evaluator agents
        optimizer = self.agent_factory.create_specialized_agent(
            "creator",
            custom_instruction=(
                "You are an optimizer agent focused on generating high-quality "
                "responses and iteratively improving them based on feedback."
            )
        )
        
        evaluator = self.agent_factory.create_specialized_agent(
            "analyst",
            custom_instruction=(
                "You are an evaluator agent focused on critically analyzing "
                "responses and providing constructive feedback for improvement."
            )
        )
        
        if not optimizer or not evaluator:
            raise Exception("Could not create evaluator-optimizer agents")
            
        async with self.app.run():
            from mcp_agent.workflows.evaluator_optimizer.types import QualityRating
            
            eo_llm = EvaluatorOptimizerLLM(
                optimizer=optimizer,
                evaluator=evaluator,
                llm_factory=self._get_llm_class(),
                min_rating=QualityRating.GOOD
            )
            
            result = await eo_llm.generate_str(task_description)
            return result
            
    async def _execute_fallback(
        self, 
        task_description: str, 
        context: Optional[Dict[str, Any]]
    ) -> ExecutionResult:
        """Execute fallback strategy when main execution fails."""
        self.logger.info("Executing fallback strategy...")
        
        try:
            # Try simple direct execution as fallback
            task_analysis = self.task_analyzer.analyze_task(task_description)
            agents = self.agent_factory.create_agents_for_task(task_analysis, max_agents=1)
            
            if agents:
                async with self.app.run():
                    agent = agents[0]
                    async with agent:
                        llm = await agent.attach_llm(OpenAIAugmentedLLM)
                        result = await llm.generate_str(task_description)
                        
                        return ExecutionResult(
                            task_description=task_description,
                            execution_pattern=ExecutionPattern.DIRECT,
                            agents_used=[agent.name],
                            execution_time=0,
                            result=result,
                            success=True,
                            strategy_confidence="fallback"
                        )
            
            raise Exception("Fallback execution also failed")
            
        except Exception as e:
            return ExecutionResult(
                task_description=task_description,
                execution_pattern=ExecutionPattern.DIRECT,
                agents_used=[],
                execution_time=0,
                result=None,
                success=False,
                error_message=f"Fallback failed: {e}"
            )
            
    def _get_llm_class(self) -> Type[AugmentedLLM]:
        """Get the appropriate LLM class based on configuration."""
        if self.config.default_llm_provider.lower() == "anthropic":
            return AnthropicAugmentedLLM
        else:
            return OpenAIAugmentedLLM
            
    async def analyze_capabilities(self) -> Dict[str, Any]:
        """Analyze and return current system capabilities."""
        if not self.is_initialized:
            await self.initialize()
            
        return {
            "tool_capabilities": self.tool_mapper.get_capability_summary(),
            "agent_specializations": self.agent_factory.get_available_specializations(),
            "factory_status": self.agent_factory.get_factory_status(),
            "execution_history": len(self.execution_history),
            "success_rate": self._calculate_success_rate()
        }
        
    def _calculate_success_rate(self) -> float:
        """Calculate success rate of past executions."""
        if not self.execution_history:
            return 0.0
            
        successful = sum(1 for result in self.execution_history if result.success)
        return successful / len(self.execution_history)
        
    async def get_execution_suggestions(self, task_description: str) -> Dict[str, Any]:
        """Get suggestions for executing a task without actually executing it."""
        if not self.is_initialized:
            await self.initialize()
            
        task_analysis = self.task_analyzer.analyze_task(task_description)
        strategy_decision = self.strategy_engine.decide_strategy(task_analysis)
        
        return {
            "task_analysis": {
                "type": task_analysis.task_type.value,
                "complexity": task_analysis.complexity.value,
                "estimated_steps": task_analysis.estimated_steps,
                "confidence": task_analysis.confidence
            },
            "strategy": {
                "recommended_pattern": strategy_decision.recommended_pattern.value,
                "confidence": strategy_decision.confidence.value,
                "reasoning": strategy_decision.reasoning,
                "required_servers": strategy_decision.required_servers,
                "estimated_complexity": strategy_decision.estimated_complexity
            },
            "agents": {
                "suggested_count": min(len(strategy_decision.required_servers), self.config.max_agents),
                "specializations_needed": [
                    spec for spec in self.agent_factory.get_available_specializations()
                    if any(cap in task_analysis.required_capabilities 
                          for cap in self.agent_factory.agent_specializations[spec].capabilities)
                ]
            }
        }
        
    def get_execution_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent execution history."""
        recent_history = self.execution_history[-limit:] if limit > 0 else self.execution_history
        
        return [
            {
                "task": result.task_description[:100] + "..." if len(result.task_description) > 100 else result.task_description,
                "pattern": result.execution_pattern.value,
                "success": result.success,
                "execution_time": result.execution_time,
                "agents_used": len(result.agents_used),
                "error": result.error_message if not result.success else None
            }
            for result in recent_history
        ]


# Convenience functions for easy usage
async def execute_autonomous_task(task_description: str) -> ExecutionResult:
    """
    Convenience function to execute a task autonomously.
    
    Args:
        task_description: Natural language description of the task
        
    Returns:
        ExecutionResult with outcome
    """
    orchestrator = AutonomousOrchestrator()
    return await orchestrator.execute_autonomous_task(task_description)


async def analyze_task_requirements(task_description: str) -> Dict[str, Any]:
    """
    Convenience function to analyze task requirements without execution.
    
    Args:
        task_description: Natural language description of the task
        
    Returns:
        Analysis and suggestions
    """
    orchestrator = AutonomousOrchestrator()
    return await orchestrator.get_execution_suggestions(task_description)
