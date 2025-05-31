"""
Autonomous Coordinator

This module provides the main coordination system for autonomous MCP-agent
workflows, integrating discovery, strategy selection, and execution management.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
import json
import time

from ..app import MCPApp
from ..agents.agent import Agent
from ..workflows.llm.augmented_llm import AugmentedLLM
from ..workflows.llm.augmented_llm_openai import OpenAIAugmentedLLM
from ..workflows.llm.augmented_llm_anthropic import AnthropicAugmentedLLM
from ..workflows.parallel.parallel_llm import ParallelLLM
from ..workflows.router.router_llm import LLMRouter
from ..workflows.orchestrator.orchestrator import Orchestrator
from ..workflows.swarm.swarm_anthropic import AnthropicSwarm
from ..workflows.evaluator_optimizer.evaluator_optimizer_llm import EvaluatorOptimizerLLM

from .discovery import AutonomousDiscovery, MCPToolInfo
from .strategy_selector import AutonomousStrategySelector, ExecutionStrategy, TaskAnalysis, StrategyRecommendation
from .agent_factory import DynamicAgentFactory


class CoordinationStatus(Enum):
    """Status of autonomous coordination"""
    INITIALIZING = "initializing"
    ANALYZING = "analyzing"
    PLANNING = "planning"
    EXECUTING = "executing"
    COORDINATING = "coordinating"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class ExecutionContext:
    """Context for autonomous execution"""
    task_id: str
    original_request: str
    task_analysis: TaskAnalysis
    strategy_recommendation: StrategyRecommendation
    selected_tools: List[MCPToolInfo]
    created_agents: List[Agent]
    execution_workflow: Optional[AugmentedLLM]
    status: CoordinationStatus
    start_time: float
    end_time: Optional[float] = None
    result: Optional[str] = None
    error: Optional[str] = None
    performance_metrics: Dict[str, Any] = None


class AutonomousCoordinator:
    """
    Main coordinator for autonomous MCP-agent workflows
    
    Provides the primary interface for autonomous task execution by:
    1. Discovering and analyzing available tools
    2. Analyzing task requirements and complexity
    3. Selecting optimal execution strategies
    4. Creating specialized agents dynamically
    5. Coordinating multi-agent workflows
    6. Monitoring and adapting execution
    """
    
    def __init__(self, app: MCPApp):
        self.app = app
        self.logger = logging.getLogger(__name__)
        
        # Core autonomous components
        self.discovery = AutonomousDiscovery(app.config)
        self.strategy_selector = AutonomousStrategySelector(self.discovery)
        self.agent_factory = DynamicAgentFactory(self.discovery)
        
        # Execution tracking
        self.active_executions: Dict[str, ExecutionContext] = {}
        self.execution_history: List[ExecutionContext] = []
        
        # Performance metrics
        self.performance_metrics = {
            "total_tasks": 0,
            "successful_tasks": 0,
            "avg_execution_time": 0.0,
            "strategy_usage": {},
            "tool_usage": {}
        }
        
        # Configuration
        self.max_concurrent_executions = 5
        self.default_llm_factory = OpenAIAugmentedLLM
        self.adaptive_strategy_enabled = True
        
    async def initialize(self):
        """Initialize the autonomous coordinator"""
        self.logger.info("Initializing autonomous coordinator...")
        
        # Start tool discovery
        await self.discovery.discover_available_tools()
        
        # Start continuous discovery if enabled
        await self.discovery.start_continuous_discovery()
        
        self.logger.info("Autonomous coordinator initialized successfully")
    
    async def execute_autonomous_task(self, 
                                    task_description: str,
                                    context: Optional[Dict[str, Any]] = None,
                                    constraints: Optional[Dict[str, Any]] = None) -> str:
        """
        Execute a task autonomously with full coordination
        
        Args:
            task_description: Natural language description of the task
            context: Optional context information
            constraints: Optional constraints (time, quality, resources)
            
        Returns:
            Task execution result
        """
        
        task_id = f"task_{int(time.time())}_{len(self.active_executions)}"
        
        self.logger.info(f"Starting autonomous execution of task {task_id}: {task_description[:100]}...")
        
        try:
            # Create execution context
            execution_context = ExecutionContext(
                task_id=task_id,
                original_request=task_description,
                task_analysis=None,
                strategy_recommendation=None,
                selected_tools=[],
                created_agents=[],
                execution_workflow=None,
                status=CoordinationStatus.INITIALIZING,
                start_time=time.time()
            )
            
            self.active_executions[task_id] = execution_context
            
            # Phase 1: Analyze the task
            execution_context.status = CoordinationStatus.ANALYZING
            task_analysis = await self.strategy_selector.analyze_task(task_description, context)
            execution_context.task_analysis = task_analysis
            
            self.logger.info(f"Task analysis complete. Complexity: {task_analysis.complexity_score}")
            
            # Phase 2: Select optimal strategy
            execution_context.status = CoordinationStatus.PLANNING
            available_tools = list((await self.discovery.discover_available_tools()).values())
            strategy_recommendation = await self.strategy_selector.recommend_strategy(
                task_analysis, available_tools
            )
            execution_context.strategy_recommendation = strategy_recommendation
            
            self.logger.info(f"Strategy selected: {strategy_recommendation.strategy.value} "
                           f"(confidence: {strategy_recommendation.confidence:.2f})")
            
            # Phase 3: Prepare tools and agents
            selected_tools = await self._select_and_prepare_tools(
                strategy_recommendation.required_tools, available_tools
            )
            execution_context.selected_tools = selected_tools
            
            # Phase 4: Create execution workflow
            execution_context.status = CoordinationStatus.EXECUTING
            workflow = await self._create_execution_workflow(
                strategy_recommendation, task_analysis, selected_tools
            )
            execution_context.execution_workflow = workflow
            
            # Phase 5: Execute the task
            result = await self._execute_workflow(workflow, task_description, execution_context)
            
            # Phase 6: Complete and cleanup
            execution_context.status = CoordinationStatus.COMPLETED
            execution_context.result = result
            execution_context.end_time = time.time()
            
            # Update performance metrics
            await self._update_performance_metrics(execution_context, success=True)
            
            # Move to history
            self.execution_history.append(execution_context)
            del self.active_executions[task_id]
            
            self.logger.info(f"Task {task_id} completed successfully")
            return result
            
        except Exception as e:
            self.logger.error(f"Error executing task {task_id}: {e}")
            
            # Update execution context with error
            if task_id in self.active_executions:
                execution_context = self.active_executions[task_id]
                execution_context.status = CoordinationStatus.ERROR
                execution_context.error = str(e)
                execution_context.end_time = time.time()
                
                await self._update_performance_metrics(execution_context, success=False)
                
                self.execution_history.append(execution_context)
                del self.active_executions[task_id]
            
            raise e
    
    async def _select_and_prepare_tools(self, 
                                      required_tool_names: List[str],
                                      available_tools: List[MCPToolInfo]) -> List[MCPToolInfo]:
        """Select and prepare required tools for execution"""
        
        selected_tools = []
        
        for tool_name in required_tool_names:
            # Find the tool in available tools
            tool = next((t for t in available_tools if t.name == tool_name), None)
            
            if tool:
                # Install if needed
                if tool.status.value != "installed":
                    success = await self.discovery.install_tool(tool_name)
                    if not success:
                        self.logger.warning(f"Failed to install tool {tool_name}")
                        continue
                
                selected_tools.append(tool)
                self.logger.info(f"Selected tool: {tool_name}")
            else:
                self.logger.warning(f"Required tool {tool_name} not found")
        
        return selected_tools
    
    async def _create_execution_workflow(self, 
                                       strategy_recommendation: StrategyRecommendation,
                                       task_analysis: TaskAnalysis,
                                       selected_tools: List[MCPToolInfo]) -> AugmentedLLM:
        """Create the appropriate execution workflow based on strategy"""
        
        strategy = strategy_recommendation.strategy
        
        if strategy == ExecutionStrategy.DIRECT:
            return await self._create_direct_workflow(selected_tools)
            
        elif strategy == ExecutionStrategy.PARALLEL:
            return await self._create_parallel_workflow(task_analysis, selected_tools)
            
        elif strategy == ExecutionStrategy.ROUTER:
            return await self._create_router_workflow(selected_tools)
            
        elif strategy == ExecutionStrategy.ORCHESTRATOR:
            return await self._create_orchestrator_workflow(task_analysis, selected_tools)
            
        elif strategy == ExecutionStrategy.SWARM:
            return await self._create_swarm_workflow(task_analysis, selected_tools)
            
        elif strategy == ExecutionStrategy.EVALUATOR_OPTIMIZER:
            return await self._create_evaluator_optimizer_workflow(task_analysis, selected_tools)
            
        elif strategy == ExecutionStrategy.ADAPTIVE_HYBRID:
            return await self._create_adaptive_hybrid_workflow(task_analysis, selected_tools)
        
        else:
            # Fallback to direct
            return await self._create_direct_workflow(selected_tools)
    
    async def _create_direct_workflow(self, selected_tools: List[MCPToolInfo]) -> AugmentedLLM:
        """Create a direct execution workflow with a single agent"""
        
        # Create a single agent with all selected tools
        tool_names = [tool.name for tool in selected_tools]
        
        agent = await self.agent_factory.create_agent(
            name="autonomous_agent",
            instruction="You are an autonomous agent capable of using multiple tools to complete tasks efficiently.",
            server_names=tool_names
        )
        
        async with agent:
            llm = await agent.attach_llm(self.default_llm_factory)
            return llm
    
    async def _create_parallel_workflow(self, 
                                      task_analysis: TaskAnalysis,
                                      selected_tools: List[MCPToolInfo]) -> ParallelLLM:
        """Create a parallel execution workflow"""
        
        # Create specialized agents for different capabilities
        capability_groups = self._group_tools_by_capability(selected_tools)
        
        fan_out_agents = []
        for capability, tools in capability_groups.items():
            tool_names = [tool.name for tool in tools]
            agent = await self.agent_factory.create_agent(
                name=f"{capability}_specialist",
                instruction=f"You specialize in {capability} tasks and operations.",
                server_names=tool_names
            )
            fan_out_agents.append(agent)
        
        # Create aggregator agent
        aggregator = await self.agent_factory.create_agent(
            name="aggregator",
            instruction="You combine and synthesize results from multiple specialists into coherent final output.",
            server_names=[]
        )
        
        return ParallelLLM(
            fan_in_agent=aggregator,
            fan_out_agents=fan_out_agents,
            llm_factory=self.default_llm_factory
        )
    
    async def _create_router_workflow(self, selected_tools: List[MCPToolInfo]) -> LLMRouter:
        """Create a router workflow"""
        
        # Create specialized agents for different tool categories
        agents = []
        capability_groups = self._group_tools_by_capability(selected_tools)
        
        for capability, tools in capability_groups.items():
            tool_names = [tool.name for tool in tools]
            agent = await self.agent_factory.create_agent(
                name=f"{capability}_agent",
                instruction=f"You are an expert in {capability} operations.",
                server_names=tool_names
            )
            agents.append(agent)
        
        # Create router LLM
        router_llm = await self.default_llm_factory().initialize()
        
        return LLMRouter(
            llm=router_llm,
            agents=agents,
            functions=[]
        )
    
    async def _create_orchestrator_workflow(self, 
                                          task_analysis: TaskAnalysis,
                                          selected_tools: List[MCPToolInfo]) -> Orchestrator:
        """Create an orchestrator workflow"""
        
        # Create agents for different capabilities
        agents = []
        capability_groups = self._group_tools_by_capability(selected_tools)
        
        for capability, tools in capability_groups.items():
            tool_names = [tool.name for tool in tools]
            agent = await self.agent_factory.create_agent(
                name=f"{capability}_worker",
                instruction=f"You are a specialized worker for {capability} tasks.",
                server_names=tool_names
            )
            agents.append(agent)
        
        return Orchestrator(
            llm_factory=self.default_llm_factory,
            available_agents=agents
        )
    
    async def _create_swarm_workflow(self, 
                                   task_analysis: TaskAnalysis,
                                   selected_tools: List[MCPToolInfo]) -> AnthropicSwarm:
        """Create a swarm workflow"""
        
        # Create a primary agent for swarm coordination
        primary_agent = await self.agent_factory.create_swarm_agent(
            name="swarm_coordinator",
            instruction="You coordinate with other agents to complete complex tasks efficiently.",
            server_names=[tool.name for tool in selected_tools]
        )
        
        return AnthropicSwarm(
            agent=primary_agent,
            context_variables={"task_complexity": task_analysis.complexity_score}
        )
    
    async def _create_evaluator_optimizer_workflow(self, 
                                                 task_analysis: TaskAnalysis,
                                                 selected_tools: List[MCPToolInfo]) -> EvaluatorOptimizerLLM:
        """Create an evaluator-optimizer workflow"""
        
        # Create optimizer agent
        optimizer = await self.agent_factory.create_agent(
            name="optimizer",
            instruction="You create and refine high-quality responses to meet exact requirements.",
            server_names=[tool.name for tool in selected_tools]
        )
        
        # Create evaluator agent
        evaluator = await self.agent_factory.create_agent(
            name="evaluator",
            instruction="You critically evaluate responses for quality, accuracy, and completeness.",
            server_names=[]
        )
        
        return EvaluatorOptimizerLLM(
            optimizer=optimizer,
            evaluator=evaluator,
            llm_factory=self.default_llm_factory,
            min_rating="EXCELLENT" if task_analysis.quality_requirements == "critical" else "GOOD"
        )
    
    async def _create_adaptive_hybrid_workflow(self, 
                                             task_analysis: TaskAnalysis,
                                             selected_tools: List[MCPToolInfo]) -> AugmentedLLM:
        """Create an adaptive hybrid workflow that can switch strategies"""
        
        # For now, start with orchestrator and allow adaptation
        # This could be enhanced to truly switch strategies mid-execution
        return await self._create_orchestrator_workflow(task_analysis, selected_tools)
    
    def _group_tools_by_capability(self, tools: List[MCPToolInfo]) -> Dict[str, List[MCPToolInfo]]:
        """Group tools by their primary capability category"""
        
        groups = {}
        
        for tool in tools:
            if tool.capabilities:
                # Use the first capability's category as primary
                primary_category = tool.capabilities[0].category.value
                
                if primary_category not in groups:
                    groups[primary_category] = []
                
                groups[primary_category].append(tool)
        
        return groups
    
    async def _execute_workflow(self, 
                              workflow: AugmentedLLM,
                              task_description: str,
                              execution_context: ExecutionContext) -> str:
        """Execute the workflow with monitoring and coordination"""
        
        execution_context.status = CoordinationStatus.COORDINATING
        
        try:
            # Execute the workflow
            result = await workflow.generate_str(message=task_description)
            
            # Update tool performance metrics
            for tool in execution_context.selected_tools:
                await self.discovery.update_performance_metrics(
                    tool.name, 
                    response_time=time.time() - execution_context.start_time,
                    success=True
                )
            
            return result
            
        except Exception as e:
            # Update tool performance metrics for failure
            for tool in execution_context.selected_tools:
                await self.discovery.update_performance_metrics(
                    tool.name,
                    response_time=time.time() - execution_context.start_time,
                    success=False
                )
            
            raise e
    
    async def _update_performance_metrics(self, 
                                        execution_context: ExecutionContext,
                                        success: bool):
        """Update performance metrics after task execution"""
        
        self.performance_metrics["total_tasks"] += 1
        
        if success:
            self.performance_metrics["successful_tasks"] += 1
        
        # Update execution time
        if execution_context.end_time:
            duration = execution_context.end_time - execution_context.start_time
            current_avg = self.performance_metrics["avg_execution_time"]
            total_tasks = self.performance_metrics["total_tasks"]
            
            # Update rolling average
            self.performance_metrics["avg_execution_time"] = (
                (current_avg * (total_tasks - 1) + duration) / total_tasks
            )
        
        # Update strategy usage
        if execution_context.strategy_recommendation:
            strategy = execution_context.strategy_recommendation.strategy.value
            if strategy not in self.performance_metrics["strategy_usage"]:
                self.performance_metrics["strategy_usage"][strategy] = 0
            self.performance_metrics["strategy_usage"][strategy] += 1
            
            # Update strategy performance in selector
            quality_score = 0.8 if success else 0.2  # Simple quality scoring
            duration = execution_context.end_time - execution_context.start_time if execution_context.end_time else 0
            
            await self.strategy_selector.update_strategy_performance(
                execution_context.strategy_recommendation.strategy,
                success,
                duration,
                quality_score
            )
        
        # Update tool usage
        for tool in execution_context.selected_tools:
            tool_name = tool.name
            if tool_name not in self.performance_metrics["tool_usage"]:
                self.performance_metrics["tool_usage"][tool_name] = 0
            self.performance_metrics["tool_usage"][tool_name] += 1
    
    async def get_execution_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a running or completed execution"""
        
        # Check active executions
        if task_id in self.active_executions:
            context = self.active_executions[task_id]
            return self._format_execution_status(context)
        
        # Check execution history
        for context in self.execution_history:
            if context.task_id == task_id:
                return self._format_execution_status(context)
        
        return None
    
    def _format_execution_status(self, context: ExecutionContext) -> Dict[str, Any]:
        """Format execution context for status reporting"""
        
        status = {
            "task_id": context.task_id,
            "status": context.status.value,
            "original_request": context.original_request,
            "start_time": context.start_time,
            "end_time": context.end_time,
            "duration": context.end_time - context.start_time if context.end_time else None,
        }
        
        if context.task_analysis:
            status["complexity_score"] = context.task_analysis.complexity_score
            status["tool_requirements"] = context.task_analysis.tool_requirements
        
        if context.strategy_recommendation:
            status["selected_strategy"] = context.strategy_recommendation.strategy.value
            status["strategy_confidence"] = context.strategy_recommendation.confidence
        
        if context.selected_tools:
            status["selected_tools"] = [tool.name for tool in context.selected_tools]
        
        if context.result:
            status["result"] = context.result
        
        if context.error:
            status["error"] = context.error
        
        return status
    
    async def list_active_executions(self) -> List[Dict[str, Any]]:
        """List all currently active executions"""
        
        return [self._format_execution_status(context) 
                for context in self.active_executions.values()]
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary for the autonomous coordinator"""
        
        summary = {
            "total_tasks": self.performance_metrics["total_tasks"],
            "success_rate": (self.performance_metrics["successful_tasks"] / 
                           max(1, self.performance_metrics["total_tasks"])),
            "avg_execution_time": self.performance_metrics["avg_execution_time"],
            "active_executions": len(self.active_executions),
            "strategy_usage": self.performance_metrics["strategy_usage"],
            "tool_usage": self.performance_metrics["tool_usage"],
            "strategy_performance": self.strategy_selector.get_strategy_performance_summary(),
            "tool_registry": await self.discovery.get_tool_registry()
        }
        
        return summary
    
    async def shutdown(self):
        """Shutdown the autonomous coordinator"""
        
        self.logger.info("Shutting down autonomous coordinator...")
        
        # Stop continuous discovery
        await self.discovery.stop_continuous_discovery()
        
        # Wait for active executions to complete (with timeout)
        if self.active_executions:
            self.logger.info(f"Waiting for {len(self.active_executions)} active executions to complete...")
            
            timeout = 30  # 30 seconds timeout
            start_time = time.time()
            
            while self.active_executions and (time.time() - start_time) < timeout:
                await asyncio.sleep(1)
            
            if self.active_executions:
                self.logger.warning(f"Forcibly terminating {len(self.active_executions)} executions")
        
        self.logger.info("Autonomous coordinator shutdown complete")
