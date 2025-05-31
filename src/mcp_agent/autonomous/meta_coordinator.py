"""
Meta-Coordinator for Autonomous MCP Agent

This module coordinates all autonomous capabilities to provide intelligent
task execution. It brings together tool discovery, task analysis, strategy
selection, and dynamic installation to create a fully autonomous agent system.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from datetime import datetime
import json

from ..app import MCPApp
from ..agents.agent import Agent
from ..workflows.llm.augmented_llm import AugmentedLLM
from ..workflows.llm.augmented_llm_openai import OpenAIAugmentedLLM
from ..workflows.llm.augmented_llm_anthropic import AnthropicAugmentedLLM
from ..workflows.parallel.parallel_llm import ParallelLLM
from ..workflows.orchestrator.orchestrator import Orchestrator
from ..workflows.router.router_llm import LLMRouter
from ..workflows.swarm.swarm import Swarm

from .tool_discovery import ToolDiscovery, ToolCategory
from .task_analyzer import TaskAnalyzer, TaskAnalysis, ExecutionPattern
from .strategy_selector import StrategySelector, StrategyRecommendation
from .dynamic_installer import DynamicInstaller


@dataclass
class ExecutionContext:
    """Context for autonomous task execution"""
    task_description: str
    task_analysis: TaskAnalysis
    strategy_recommendation: StrategyRecommendation
    available_tools: List[str]
    execution_start_time: datetime
    user_preferences: Dict[str, Any] = None
    session_id: str = None


@dataclass
class ExecutionResult:
    """Result of autonomous task execution"""
    success: bool
    result: str
    execution_time: float
    pattern_used: ExecutionPattern
    tools_used: List[str]
    agents_created: int
    error_message: str = ""
    performance_metrics: Dict[str, Any] = None


class MetaCoordinator:
    """Coordinates autonomous task execution across all components"""
    
    def __init__(self, mcp_app: MCPApp, default_llm_factory=None):
        self.mcp_app = mcp_app
        self.logger = logging.getLogger(__name__)
        
        # Default LLM factory
        self.default_llm_factory = default_llm_factory or OpenAIAugmentedLLM
        
        # Initialize autonomous components
        self.tool_discovery = ToolDiscovery()
        self.dynamic_installer = DynamicInstaller(self.tool_discovery)
        self.task_analyzer = TaskAnalyzer(self.tool_discovery)
        self.strategy_selector = StrategySelector(self.tool_discovery)
        
        # Execution history
        self.execution_history: List[ExecutionResult] = []
        
        # Performance tracking
        self.performance_metrics = {
            "total_executions": 0,
            "successful_executions": 0,
            "average_execution_time": 0.0,
            "pattern_usage": {pattern.value: 0 for pattern in ExecutionPattern},
            "tool_usage": {},
            "error_patterns": {}
        }
    
    async def initialize(self):
        """Initialize the meta-coordinator and discover available tools"""
        self.logger.info("Initializing Meta-Coordinator...")
        
        # Discover available tools
        await self.tool_discovery.discover_available_tools()
        
        self.logger.info("Meta-Coordinator initialized successfully")
    
    async def execute_autonomous_task(self, task_description: str,
                                    user_preferences: Optional[Dict[str, Any]] = None,
                                    session_id: Optional[str] = None) -> ExecutionResult:
        """Execute a task autonomously using intelligent tool selection and coordination"""
        
        execution_start = datetime.now()
        
        try:
            self.logger.info(f"Starting autonomous execution: {task_description}")
            
            # Phase 1: Analyze the task
            task_analysis = await self.task_analyzer.analyze_task(task_description)
            self.logger.info(f"Task analysis complete: {task_analysis.complexity.value} - {task_analysis.suggested_pattern.value}")
            
            # Phase 2: Ensure required tools are available
            available_tools = await self._ensure_tools_available(task_analysis)
            
            if not available_tools:
                return ExecutionResult(
                    success=False,
                    result="No suitable tools available for this task",
                    execution_time=0.0,
                    pattern_used=ExecutionPattern.DIRECT,
                    tools_used=[],
                    agents_created=0,
                    error_message="Tool discovery/installation failed"
                )
            
            # Phase 3: Select execution strategy
            strategy = await self.strategy_selector.select_strategy(task_analysis)
            self.logger.info(f"Selected strategy: {strategy.pattern.value} (confidence: {strategy.confidence_score:.2f})")
            
            # Phase 4: Create execution context
            context = ExecutionContext(
                task_description=task_description,
                task_analysis=task_analysis,
                strategy_recommendation=strategy,
                available_tools=available_tools,
                execution_start_time=execution_start,
                user_preferences=user_preferences,
                session_id=session_id
            )
            
            # Phase 5: Execute using selected pattern
            result = await self._execute_with_pattern(context)
            
            # Phase 6: Update performance metrics
            self._update_performance_metrics(result)
            
            # Phase 7: Log execution
            self.execution_history.append(result)
            
            return result
        
        except Exception as e:
            execution_time = (datetime.now() - execution_start).total_seconds()
            error_result = ExecutionResult(
                success=False,
                result="",
                execution_time=execution_time,
                pattern_used=ExecutionPattern.DIRECT,
                tools_used=[],
                agents_created=0,
                error_message=str(e)
            )
            
            self.logger.error(f"Autonomous execution failed: {e}")
            self._update_performance_metrics(error_result)
            self.execution_history.append(error_result)
            
            return error_result
    
    async def _ensure_tools_available(self, task_analysis: TaskAnalysis) -> List[str]:
        """Ensure required tools are available, installing if necessary"""
        
        # First, try to find existing tools
        available_tools = self.tool_discovery.get_tools_for_capabilities(
            task_analysis.required_capabilities
        )
        
        if available_tools:
            self.logger.info(f"Found {len(available_tools)} existing tools: {available_tools}")
            return available_tools
        
        # If no tools available, try dynamic installation
        self.logger.info("No suitable tools found, attempting dynamic installation...")
        
        installed_tools = await self.dynamic_installer.ensure_tools_available(
            task_analysis.required_capabilities
        )
        
        if installed_tools:
            self.logger.info(f"Successfully installed {len(installed_tools)} tools: {installed_tools}")
            # Refresh tool discovery after installation
            await self.tool_discovery.discover_available_tools()
            return self.tool_discovery.get_tools_for_capabilities(task_analysis.required_capabilities)
        
        # Last resort: suggest manual installation
        self.logger.warning("Could not automatically install required tools")
        suggested_tools = await self.dynamic_installer.suggest_additional_tools(
            task_analysis.required_capabilities
        )
        
        if suggested_tools:
            self.logger.info(f"Suggested tools for manual installation: {suggested_tools}")
        
        return []
    
    async def _execute_with_pattern(self, context: ExecutionContext) -> ExecutionResult:
        """Execute task using the selected pattern"""
        
        pattern = context.strategy_recommendation.pattern
        execution_start = datetime.now()
        
        try:
            if pattern == ExecutionPattern.DIRECT:
                result = await self._execute_direct(context)
            elif pattern == ExecutionPattern.PARALLEL:
                result = await self._execute_parallel(context)
            elif pattern == ExecutionPattern.SWARM:
                result = await self._execute_swarm(context)
            elif pattern == ExecutionPattern.ORCHESTRATOR:
                result = await self._execute_orchestrator(context)
            elif pattern == ExecutionPattern.ROUTER:
                result = await self._execute_router(context)
            elif pattern == ExecutionPattern.EVALUATOR_OPTIMIZER:
                result = await self._execute_evaluator_optimizer(context)
            else:
                raise ValueError(f"Unsupported execution pattern: {pattern}")
            
            execution_time = (datetime.now() - execution_start).total_seconds()
            
            return ExecutionResult(
                success=True,
                result=result,
                execution_time=execution_time,
                pattern_used=pattern,
                tools_used=context.available_tools,
                agents_created=len(context.strategy_recommendation.agent_configuration.get("agents", [])),
                performance_metrics=self._calculate_performance_metrics(context, execution_time)
            )
        
        except Exception as e:
            execution_time = (datetime.now() - execution_start).total_seconds()
            
            return ExecutionResult(
                success=False,
                result="",
                execution_time=execution_time,
                pattern_used=pattern,
                tools_used=context.available_tools,
                agents_created=len(context.strategy_recommendation.agent_configuration.get("agents", [])),
                error_message=str(e)
            )
    
    async def _execute_direct(self, context: ExecutionContext) -> str:
        """Execute using direct pattern (single agent)"""
        
        agent_config = context.strategy_recommendation.agent_configuration["agents"][0]
        
        agent = Agent(
            name=agent_config["name"],
            instruction=agent_config["instruction"],
            server_names=agent_config["server_names"]
        )
        
        async with agent:
            llm = await agent.attach_llm(self.default_llm_factory)
            result = await llm.generate_str(context.task_description)
            return result
    
    async def _execute_parallel(self, context: ExecutionContext) -> str:
        """Execute using parallel pattern (fan-out/fan-in)"""
        
        agent_configs = context.strategy_recommendation.agent_configuration["agents"]
        
        # Create agents
        fan_out_agents = []
        fan_in_agent = None
        
        for config in agent_configs[:-1]:  # All but last for fan-out
            agent = Agent(
                name=config["name"],
                instruction=config["instruction"],
                server_names=config["server_names"]
            )
            fan_out_agents.append(agent)
        
        # Last agent for fan-in (or create a coordinator)
        if len(agent_configs) > 1:
            fan_in_config = agent_configs[-1]
        else:
            # Create a coordinator agent
            fan_in_config = {
                "name": "coordinator",
                "instruction": "Synthesize and combine results from multiple agents into a coherent response.",
                "server_names": context.available_tools[:2]  # Give basic tools
            }
        
        fan_in_agent = Agent(
            name=fan_in_config["name"],
            instruction=fan_in_config["instruction"],
            server_names=fan_in_config["server_names"]
        )
        
        parallel_llm = ParallelLLM(
            fan_in_agent=fan_in_agent,
            fan_out_agents=fan_out_agents,
            llm_factory=self.default_llm_factory
        )
        
        result = await parallel_llm.generate_str(context.task_description)
        return result
    
    async def _execute_swarm(self, context: ExecutionContext) -> str:
        """Execute using swarm pattern (multi-agent collaboration)"""
        
        # Note: This is a simplified implementation
        # In a full implementation, you'd use the actual Swarm class
        # For now, we'll use the orchestrator as a proxy
        
        return await self._execute_orchestrator(context)
    
    async def _execute_orchestrator(self, context: ExecutionContext) -> str:
        """Execute using orchestrator pattern (complex planning)"""
        
        agent_configs = context.strategy_recommendation.agent_configuration["agents"]
        
        # Create available agents
        available_agents = []
        for config in agent_configs:
            agent = Agent(
                name=config["name"],
                instruction=config["instruction"],
                server_names=config["server_names"]
            )
            available_agents.append(agent)
        
        orchestrator = Orchestrator(
            llm_factory=self.default_llm_factory,
            available_agents=available_agents
        )
        
        result = await orchestrator.generate_str(context.task_description)
        return result
    
    async def _execute_router(self, context: ExecutionContext) -> str:
        """Execute using router pattern (dynamic routing)"""
        
        agent_configs = context.strategy_recommendation.agent_configuration["agents"]
        
        # Create agents for routing
        agents = []
        for config in agent_configs:
            agent = Agent(
                name=config["name"],
                instruction=config["instruction"],
                server_names=config["server_names"]
            )
            agents.append(agent)
        
        router = LLMRouter(
            llm=self.default_llm_factory(),
            agents=agents
        )
        
        # Route to best agent
        results = await router.route(context.task_description, top_k=1)
        if results:
            chosen_agent = results[0].result
            async with chosen_agent:
                llm = await chosen_agent.attach_llm(self.default_llm_factory)
                result = await llm.generate_str(context.task_description)
                return result
        
        return "No suitable agent found for routing"
    
    async def _execute_evaluator_optimizer(self, context: ExecutionContext) -> str:
        """Execute using evaluator-optimizer pattern (iterative improvement)"""
        
        agent_configs = context.strategy_recommendation.agent_configuration["agents"]
        
        if len(agent_configs) < 2:
            # Fall back to direct execution
            return await self._execute_direct(context)
        
        # Create optimizer and evaluator agents
        optimizer_config = agent_configs[0]
        evaluator_config = agent_configs[1]
        
        optimizer_agent = Agent(
            name=optimizer_config["name"],
            instruction=optimizer_config["instruction"],
            server_names=optimizer_config["server_names"]
        )
        
        evaluator_agent = Agent(
            name=evaluator_config["name"],
            instruction=evaluator_config["instruction"],
            server_names=evaluator_config["server_names"]
        )
        
        # Simplified evaluator-optimizer implementation
        async with optimizer_agent:
            optimizer_llm = await optimizer_agent.attach_llm(self.default_llm_factory)
            initial_result = await optimizer_llm.generate_str(context.task_description)
        
        async with evaluator_agent:
            evaluator_llm = await evaluator_agent.attach_llm(self.default_llm_factory)
            evaluation = await evaluator_llm.generate_str(
                f"Evaluate this response to the task '{context.task_description}': {initial_result}"
            )
        
        # For simplicity, return the initial result
        # In a full implementation, this would iterate based on evaluation
        return f"{initial_result}\n\nEvaluation: {evaluation}"
    
    def _calculate_performance_metrics(self, context: ExecutionContext, execution_time: float) -> Dict[str, Any]:
        """Calculate performance metrics for the execution"""
        
        return {
            "execution_time": execution_time,
            "pattern_used": context.strategy_recommendation.pattern.value,
            "confidence_score": context.strategy_recommendation.confidence_score,
            "tools_count": len(context.available_tools),
            "agents_count": len(context.strategy_recommendation.agent_configuration.get("agents", [])),
            "task_complexity": context.task_analysis.complexity.value,
            "estimated_vs_actual_time": {
                "estimated": context.strategy_recommendation.estimated_resources.get("estimated_duration_minutes", 0) * 60,
                "actual": execution_time,
                "ratio": execution_time / max(context.strategy_recommendation.estimated_resources.get("estimated_duration_minutes", 1) * 60, 1)
            }
        }
    
    def _update_performance_metrics(self, result: ExecutionResult):
        """Update global performance metrics"""
        
        self.performance_metrics["total_executions"] += 1
        
        if result.success:
            self.performance_metrics["successful_executions"] += 1
        
        # Update average execution time
        total_time = (self.performance_metrics["average_execution_time"] * 
                     (self.performance_metrics["total_executions"] - 1) + result.execution_time)
        self.performance_metrics["average_execution_time"] = total_time / self.performance_metrics["total_executions"]
        
        # Update pattern usage
        self.performance_metrics["pattern_usage"][result.pattern_used.value] += 1
        
        # Update tool usage
        for tool in result.tools_used:
            self.performance_metrics["tool_usage"][tool] = self.performance_metrics["tool_usage"].get(tool, 0) + 1
        
        # Track errors
        if not result.success and result.error_message:
            error_type = type(result.error_message).__name__ if hasattr(result.error_message, '__name__') else "General"
            self.performance_metrics["error_patterns"][error_type] = self.performance_metrics["error_patterns"].get(error_type, 0) + 1
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get summary of performance metrics"""
        
        success_rate = (self.performance_metrics["successful_executions"] / 
                       max(self.performance_metrics["total_executions"], 1)) * 100
        
        most_used_pattern = max(self.performance_metrics["pattern_usage"].items(), 
                               key=lambda x: x[1], default=("none", 0))
        
        most_used_tool = max(self.performance_metrics["tool_usage"].items(),
                            key=lambda x: x[1], default=("none", 0))
        
        return {
            "total_executions": self.performance_metrics["total_executions"],
            "success_rate": f"{success_rate:.1f}%",
            "average_execution_time": f"{self.performance_metrics['average_execution_time']:.2f}s",
            "most_used_pattern": f"{most_used_pattern[0]} ({most_used_pattern[1]} times)",
            "most_used_tool": f"{most_used_tool[0]} ({most_used_tool[1]} times)",
            "unique_tools_used": len(self.performance_metrics["tool_usage"]),
            "error_types": len(self.performance_metrics["error_patterns"]),
            "installation_summary": self.dynamic_installer.get_installation_summary()
        }
    
    async def analyze_capability_gaps(self, failed_tasks: List[str]) -> Dict[str, Any]:
        """Analyze capability gaps based on failed tasks"""
        
        gap_analysis = {
            "missing_capabilities": set(),
            "suggested_tools": set(),
            "pattern_limitations": {},
            "recommendations": []
        }
        
        for task in failed_tasks:
            task_analysis = await self.task_analyzer.analyze_task(task)
            
            # Check if we have tools for the required capabilities
            available_tools = self.tool_discovery.get_tools_for_capabilities(
                task_analysis.required_capabilities
            )
            
            if not available_tools:
                gap_analysis["missing_capabilities"].update(task_analysis.required_capabilities)
                
                # Find installable tools for these capabilities
                suggested = await self.dynamic_installer.suggest_additional_tools(
                    task_analysis.required_capabilities
                )
                gap_analysis["suggested_tools"].update(suggested)
        
        # Generate recommendations
        if gap_analysis["missing_capabilities"]:
            gap_analysis["recommendations"].append(
                f"Install tools for capabilities: {', '.join(gap_analysis['missing_capabilities'])}"
            )
        
        if gap_analysis["suggested_tools"]:
            gap_analysis["recommendations"].append(
                f"Consider installing: {', '.join(gap_analysis['suggested_tools'])}"
            )
        
        return {
            "missing_capabilities": list(gap_analysis["missing_capabilities"]),
            "suggested_tools": list(gap_analysis["suggested_tools"]),
            "recommendations": gap_analysis["recommendations"]
        }
    
    async def optimize_configuration(self) -> Dict[str, Any]:
        """Optimize configuration based on usage patterns"""
        
        optimization_suggestions = []
        
        # Analyze pattern effectiveness
        pattern_success_rates = {}
        for result in self.execution_history:
            pattern = result.pattern_used.value
            if pattern not in pattern_success_rates:
                pattern_success_rates[pattern] = {"successes": 0, "total": 0}
            
            pattern_success_rates[pattern]["total"] += 1
            if result.success:
                pattern_success_rates[pattern]["successes"] += 1
        
        # Find underperforming patterns
        for pattern, stats in pattern_success_rates.items():
            success_rate = stats["successes"] / max(stats["total"], 1)
            if success_rate < 0.7 and stats["total"] > 3:
                optimization_suggestions.append(
                    f"Pattern {pattern} has low success rate ({success_rate:.1%}), consider configuration review"
                )
        
        # Analyze tool usage efficiency
        tool_usage = self.performance_metrics["tool_usage"]
        if tool_usage:
            # Find unused tools
            available_tools = set(self.tool_discovery.available_servers)
            used_tools = set(tool_usage.keys())
            unused_tools = available_tools - used_tools
            
            if unused_tools:
                optimization_suggestions.append(
                    f"Unused tools detected: {', '.join(list(unused_tools)[:5])}. Consider removal if not needed."
                )
        
        return {
            "pattern_success_rates": pattern_success_rates,
            "optimization_suggestions": optimization_suggestions,
            "current_performance": self.get_performance_summary()
        }
