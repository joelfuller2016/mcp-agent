"""
Resource-Optimized Meta-Coordinator for Autonomous MCP Agent

This module provides an enhanced MetaCoordinator with resource management optimizations,
memory efficiency improvements, and performance monitoring capabilities.
"""

import asyncio
import logging
import time
import weakref
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict, deque
import json
import gc
from functools import lru_cache
import psutil

from ..app import MCPApp
from ..agents.agent import Agent
from ..workflows.llm.augmented_llm import AugmentedLLM
from ..workflows.llm.augmented_llm_openai import OpenAIAugmentedLLM
from ..workflows.llm.augmented_llm_anthropic import AnthropicAugmentedLLM
from ..workflows.parallel.parallel_llm import ParallelLLM
from ..workflows.orchestrator.orchestrator import Orchestrator
from ..workflows.router.router_llm import LLMRouter
from ..workflows.swarm.swarm import Swarm

from .tool_discovery_optimized import ParallelToolDiscoveryAgent
from .tool_capability_mapper import ToolCategory
from .task_analyzer_optimized import TaskLevelCachedAnalyzer, TaskAnalysis, ExecutionPattern
from .strategy_selector import AutonomousStrategySelector, StrategyRecommendation
from .dynamic_installer import DynamicInstaller


@dataclass
class ExecutionContext:
    """Optimized context for autonomous task execution with resource tracking."""

    task_description: str
    task_analysis: TaskAnalysis
    strategy_recommendation: StrategyRecommendation
    available_tools: List[str]
    execution_start_time: datetime
    user_preferences: Dict[str, Any] = None
    session_id: str = None
    
    # Resource tracking
    memory_at_start: float = 0.0
    cpu_at_start: float = 0.0
    
    def __post_init__(self):
        """Initialize resource tracking."""
        self.memory_at_start = psutil.virtual_memory().used / 1024 / 1024  # MB
        self.cpu_at_start = psutil.cpu_percent(interval=None)


@dataclass
class ExecutionResult:
    """Enhanced result of autonomous task execution with resource metrics."""

    success: bool
    result: str
    execution_time: float
    pattern_used: ExecutionPattern
    tools_used: List[str]
    agents_created: int
    error_message: str = ""
    performance_metrics: Dict[str, Any] = None
    
    # Resource usage metrics
    memory_used_mb: float = 0.0
    memory_peak_mb: float = 0.0
    cpu_usage_percent: float = 0.0
    cache_performance: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ResourcePool:
    """Resource pool for efficient agent and LLM management."""
    
    available_agents: deque = field(default_factory=deque)
    active_agents: Dict[str, Agent] = field(default_factory=dict)
    llm_instances: Dict[str, Any] = field(default_factory=dict)
    max_pool_size: int = 10
    
    def get_agent(self, agent_config: Dict[str, Any]) -> Agent:
        """Get an agent from the pool or create a new one."""
        agent_key = f"{agent_config['name']}:{hash(str(agent_config))}"
        
        if agent_key in self.active_agents:
            return self.active_agents[agent_key]
        
        if self.available_agents and len(self.active_agents) < self.max_pool_size:
            agent = self.available_agents.popleft()
            # Reconfigure agent
            agent.name = agent_config["name"]
            agent.instruction = agent_config["instruction"]
            agent.server_names = agent_config["server_names"]
        else:
            agent = Agent(
                name=agent_config["name"],
                instruction=agent_config["instruction"],
                server_names=agent_config["server_names"],
            )
        
        self.active_agents[agent_key] = agent
        return agent
    
    def return_agent(self, agent: Agent):
        """Return an agent to the pool."""
        agent_key = next((k for k, v in self.active_agents.items() if v is agent), None)
        if agent_key:
            del self.active_agents[agent_key]
            if len(self.available_agents) < self.max_pool_size:
                self.available_agents.append(agent)
    
    def cleanup(self):
        """Clean up the resource pool."""
        self.available_agents.clear()
        self.active_agents.clear()
        self.llm_instances.clear()


class ResourceOptimizedMetaCoordinator:
    """
    Resource-optimized coordinator for autonomous task execution.
    
    Optimizations:
    - Resource pooling for agents and LLMs
    - Memory-efficient execution tracking
    - Optimized performance metrics collection  
    - Intelligent garbage collection management
    - Configurable resource limits and monitoring
    """

    def __init__(self, mcp_app: MCPApp, default_llm_factory=None, max_concurrent_executions: int = 5):
        self.mcp_app = mcp_app
        self.logger = logging.getLogger(__name__)

        # Default LLM factory
        self.default_llm_factory = default_llm_factory or OpenAIAugmentedLLM
        
        # Resource management
        self.max_concurrent_executions = max_concurrent_executions
        self.resource_pool = ResourcePool(max_pool_size=max_concurrent_executions * 2)
        self.active_executions = 0
        self.execution_semaphore = asyncio.Semaphore(max_concurrent_executions)

        # Initialize optimized autonomous components
        self.tool_discovery = ParallelToolDiscoveryAgent(
            connection_manager=None,  # Will be set during initialization
            max_concurrent_operations=min(max_concurrent_executions * 2, 10)
        )
        self.dynamic_installer = DynamicInstaller(self.tool_discovery)
        self.task_analyzer = TaskLevelCachedAnalyzer(cache_size=256)
        self.strategy_selector = AutonomousStrategySelector(self.tool_discovery)

        # Execution history with memory optimization (limited size)
        self.execution_history: deque = deque(maxlen=1000)  # Limit memory usage
        
        # Performance tracking with memory efficiency
        self.performance_metrics = {
            "total_executions": 0,
            "successful_executions": 0,
            "average_execution_time": 0.0,
            "pattern_usage": {pattern.value: 0 for pattern in ExecutionPattern},
            "tool_usage": defaultdict(int),
            "error_patterns": defaultdict(int),
            "resource_usage": {
                "avg_memory_mb": 0.0,
                "peak_memory_mb": 0.0,
                "avg_cpu_percent": 0.0,
            }
        }
        
        # Cache for frequently used configurations
        self._agent_config_cache = {}
        
        # Memory monitoring
        self.memory_threshold_mb = 1024  # 1GB threshold for cleanup
        self.last_gc_time = time.time()
        self.gc_interval = 60  # Run GC every 60 seconds if needed

    async def initialize(self):
        """Initialize the meta-coordinator with optimized discovery."""
        self.logger.info("Initializing Resource-Optimized Meta-Coordinator...")
        
        start_time = time.perf_counter()
        
        # Initialize tool discovery with performance monitoring
        await self.tool_discovery.discover_available_servers()
        
        initialization_time = (time.perf_counter() - start_time) * 1000
        
        self.logger.info(
            f"Meta-Coordinator initialized successfully in {initialization_time:.2f}ms"
        )

    async def execute_autonomous_task(
        self,
        task_description: str,
        user_preferences: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
    ) -> ExecutionResult:
        """Execute a task autonomously with resource optimization."""
        
        # Control concurrent executions
        async with self.execution_semaphore:
            self.active_executions += 1
            
            try:
                return await self._execute_task_with_monitoring(
                    task_description, user_preferences, session_id
                )
            finally:
                self.active_executions -= 1
                # Trigger cleanup if needed
                await self._maybe_cleanup_resources()

    async def _execute_task_with_monitoring(
        self,
        task_description: str,
        user_preferences: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
    ) -> ExecutionResult:
        """Execute task with comprehensive resource monitoring."""
        
        execution_start = datetime.now()
        start_memory = psutil.virtual_memory().used / 1024 / 1024
        start_cpu = psutil.cpu_percent(interval=None)

        try:
            self.logger.info(f"Starting optimized autonomous execution: {task_description}")

            # Phase 1: Analyze the task (cached)
            task_analysis = self.task_analyzer.analyze_task(task_description)
            self.logger.info(
                f"Task analysis complete: {task_analysis.complexity.value} - "
                f"{task_analysis.recommended_pattern.value} "
                f"(cached: {getattr(task_analysis, 'cache_hit', False)})"
            )

            # Phase 2: Ensure required tools are available (parallel)
            available_tools = await self._ensure_tools_available_optimized(task_analysis)

            if not available_tools:
                return self._create_error_result(
                    "No suitable tools available for this task",
                    ExecutionPattern.DIRECT,
                    execution_start,
                    start_memory,
                    start_cpu
                )

            # Phase 3: Select execution strategy (cached)
            strategy = await self.strategy_selector.select_strategy(task_analysis)
            self.logger.info(
                f"Selected strategy: {strategy.pattern.value} "
                f"(confidence: {strategy.confidence_score:.2f})"
            )

            # Phase 4: Create optimized execution context
            context = ExecutionContext(
                task_description=task_description,
                task_analysis=task_analysis,
                strategy_recommendation=strategy,
                available_tools=available_tools,
                execution_start_time=execution_start,
                user_preferences=user_preferences,
                session_id=session_id,
            )

            # Phase 5: Execute using optimized pattern execution
            result = await self._execute_with_pattern_optimized(context)

            # Phase 6: Calculate resource usage
            end_memory = psutil.virtual_memory().used / 1024 / 1024
            end_cpu = psutil.cpu_percent(interval=None)
            
            result.memory_used_mb = end_memory - start_memory
            result.memory_peak_mb = max(end_memory, start_memory)
            result.cpu_usage_percent = end_cpu - start_cpu

            # Phase 7: Update performance metrics efficiently
            self._update_performance_metrics_optimized(result)

            # Phase 8: Add to execution history (with memory limit)
            self.execution_history.append(result)

            return result

        except Exception as e:
            execution_time = (datetime.now() - execution_start).total_seconds()
            error_result = self._create_error_result(
                str(e), ExecutionPattern.DIRECT, execution_start, start_memory, start_cpu
            )
            error_result.execution_time = execution_time

            self.logger.error(f"Optimized autonomous execution failed: {e}")
            self._update_performance_metrics_optimized(error_result)
            self.execution_history.append(error_result)

            return error_result

    async def _ensure_tools_available_optimized(self, task_analysis: TaskAnalysis) -> List[str]:
        """Optimized tool availability checking with parallel operations."""
        
        # Use parallel tool discovery capabilities
        if hasattr(self.tool_discovery, 'get_tools_for_capabilities'):
            available_tools = self.tool_discovery.get_tools_for_capabilities(
                task_analysis.required_capabilities
            )
        else:
            # Fallback for compatibility
            available_tools = []

        if available_tools:
            self.logger.info(
                f"Found {len(available_tools)} existing tools: {available_tools}"
            )
            return available_tools

        # If no tools available, try dynamic installation with parallel processing
        self.logger.info("No suitable tools found, attempting optimized installation...")

        installed_tools = await self.dynamic_installer.ensure_tools_available(
            task_analysis.required_capabilities
        )

        if installed_tools:
            self.logger.info(
                f"Successfully installed {len(installed_tools)} tools: {installed_tools}"
            )
            # Refresh tool discovery after installation
            await self.tool_discovery.discover_available_servers()
            
            if hasattr(self.tool_discovery, 'get_tools_for_capabilities'):
                return self.tool_discovery.get_tools_for_capabilities(
                    task_analysis.required_capabilities
                )

        return []

    async def _execute_with_pattern_optimized(self, context: ExecutionContext) -> ExecutionResult:
        """Execute task using optimized pattern execution with resource pooling."""

        pattern = context.strategy_recommendation.pattern
        execution_start = datetime.now()

        try:
            if pattern == ExecutionPattern.DIRECT:
                result = await self._execute_direct_optimized(context)
            elif pattern == ExecutionPattern.PARALLEL:
                result = await self._execute_parallel_optimized(context)
            elif pattern == ExecutionPattern.SWARM:
                result = await self._execute_swarm_optimized(context)
            elif pattern == ExecutionPattern.ORCHESTRATOR:
                result = await self._execute_orchestrator_optimized(context)
            elif pattern == ExecutionPattern.ROUTER:
                result = await self._execute_router_optimized(context)
            elif pattern == ExecutionPattern.EVALUATOR_OPTIMIZER:
                result = await self._execute_evaluator_optimizer_optimized(context)
            else:
                raise ValueError(f"Unsupported execution pattern: {pattern}")

            execution_time = (datetime.now() - execution_start).total_seconds()

            return ExecutionResult(
                success=True,
                result=result,
                execution_time=execution_time,
                pattern_used=pattern,
                tools_used=context.available_tools,
                agents_created=len(
                    context.strategy_recommendation.agent_configuration.get("agents", [])
                ),
                performance_metrics=self._calculate_performance_metrics_optimized(
                    context, execution_time
                ),
            )

        except Exception as e:
            execution_time = (datetime.now() - execution_start).total_seconds()

            return ExecutionResult(
                success=False,
                result="",
                execution_time=execution_time,
                pattern_used=pattern,
                tools_used=context.available_tools,
                agents_created=len(
                    context.strategy_recommendation.agent_configuration.get("agents", [])
                ),
                error_message=str(e),
            )

    async def _execute_direct_optimized(self, context: ExecutionContext) -> str:
        """Execute using direct pattern with resource pooling."""

        agent_config = context.strategy_recommendation.agent_configuration["agents"][0]
        
        # Get agent from resource pool
        agent = self.resource_pool.get_agent(agent_config)

        try:
            async with agent:
                llm = await agent.attach_llm(self.default_llm_factory)
                result = await llm.generate_str(context.task_description)
                return result
        finally:
            # Return agent to pool
            self.resource_pool.return_agent(agent)

    async def _execute_parallel_optimized(self, context: ExecutionContext) -> str:
        """Execute using parallel pattern with optimized resource management."""

        agent_configs = context.strategy_recommendation.agent_configuration["agents"]

        # Create agents using resource pool
        fan_out_agents = []
        agents_to_return = []
        
        try:
            # Get fan-out agents from pool
            for config in agent_configs[:-1]:
                agent = self.resource_pool.get_agent(config)
                fan_out_agents.append(agent)
                agents_to_return.append(agent)

            # Create fan-in agent
            if len(agent_configs) > 1:
                fan_in_config = agent_configs[-1]
            else:
                fan_in_config = {
                    "name": "coordinator",
                    "instruction": "Synthesize and combine results from multiple agents into a coherent response.",
                    "server_names": context.available_tools[:2],
                }

            fan_in_agent = self.resource_pool.get_agent(fan_in_config)
            agents_to_return.append(fan_in_agent)

            # Execute parallel LLM
            parallel_llm = ParallelLLM(
                fan_in_agent=fan_in_agent,
                fan_out_agents=fan_out_agents,
                llm_factory=self.default_llm_factory,
            )

            result = await parallel_llm.generate_str(context.task_description)
            return result
            
        finally:
            # Return all agents to pool
            for agent in agents_to_return:
                self.resource_pool.return_agent(agent)

    async def _execute_swarm_optimized(self, context: ExecutionContext) -> str:
        """Execute using swarm pattern with resource optimization."""
        # Simplified swarm implementation using orchestrator
        return await self._execute_orchestrator_optimized(context)

    async def _execute_orchestrator_optimized(self, context: ExecutionContext) -> str:
        """Execute using orchestrator pattern with resource pooling."""

        agent_configs = context.strategy_recommendation.agent_configuration["agents"]
        
        # Create available agents using resource pool
        available_agents = []
        agents_to_return = []
        
        try:
            for config in agent_configs:
                agent = self.resource_pool.get_agent(config)
                available_agents.append(agent)
                agents_to_return.append(agent)

            orchestrator = Orchestrator(
                llm_factory=self.default_llm_factory, 
                available_agents=available_agents
            )

            result = await orchestrator.generate_str(context.task_description)
            return result
            
        finally:
            # Return agents to pool
            for agent in agents_to_return:
                self.resource_pool.return_agent(agent)

    async def _execute_router_optimized(self, context: ExecutionContext) -> str:
        """Execute using router pattern with resource optimization."""

        agent_configs = context.strategy_recommendation.agent_configuration["agents"]
        
        # Create agents for routing using resource pool
        agents = []
        agents_to_return = []
        
        try:
            for config in agent_configs:
                agent = self.resource_pool.get_agent(config)
                agents.append(agent)
                agents_to_return.append(agent)

            router = LLMRouter(llm=self.default_llm_factory(), agents=agents)

            # Route to best agent
            results = await router.route(context.task_description, top_k=1)
            if results:
                chosen_agent = results[0].result
                async with chosen_agent:
                    llm = await chosen_agent.attach_llm(self.default_llm_factory)
                    result = await llm.generate_str(context.task_description)
                    return result

            return "No suitable agent found for routing"
            
        finally:
            # Return agents to pool
            for agent in agents_to_return:
                self.resource_pool.return_agent(agent)

    async def _execute_evaluator_optimizer_optimized(self, context: ExecutionContext) -> str:
        """Execute using evaluator-optimizer pattern with resource pooling."""

        agent_configs = context.strategy_recommendation.agent_configuration["agents"]

        if len(agent_configs) < 2:
            return await self._execute_direct_optimized(context)

        # Create optimizer and evaluator agents using resource pool
        optimizer_config = agent_configs[0]
        evaluator_config = agent_configs[1]

        optimizer_agent = self.resource_pool.get_agent(optimizer_config)
        evaluator_agent = self.resource_pool.get_agent(evaluator_config)
        
        try:
            # Execute optimizer
            async with optimizer_agent:
                optimizer_llm = await optimizer_agent.attach_llm(self.default_llm_factory)
                initial_result = await optimizer_llm.generate_str(context.task_description)

            # Execute evaluator
            async with evaluator_agent:
                evaluator_llm = await evaluator_agent.attach_llm(self.default_llm_factory)
                evaluation = await evaluator_llm.generate_str(
                    f"Evaluate this response to the task '{context.task_description}': {initial_result}"
                )

            return f"{initial_result}\n\nEvaluation: {evaluation}"
            
        finally:
            # Return agents to pool
            self.resource_pool.return_agent(optimizer_agent)
            self.resource_pool.return_agent(evaluator_agent)

    def _calculate_performance_metrics_optimized(
        self, context: ExecutionContext, execution_time: float
    ) -> Dict[str, Any]:
        """Calculate performance metrics with minimal overhead."""

        return {
            "execution_time": execution_time,
            "pattern_used": context.strategy_recommendation.pattern.value,
            "confidence_score": context.strategy_recommendation.confidence_score,
            "tools_count": len(context.available_tools),
            "agents_count": len(
                context.strategy_recommendation.agent_configuration.get("agents", [])
            ),
            "task_complexity": context.task_analysis.complexity.value,
            "cache_performance": {
                "task_analysis_cached": getattr(context.task_analysis, 'cache_hit', False),
                "strategy_selection_cached": getattr(context.strategy_recommendation, 'cache_hit', False),
            }
        }

    def _update_performance_metrics_optimized(self, result: ExecutionResult):
        """Update performance metrics with memory efficiency."""

        self.performance_metrics["total_executions"] += 1

        if result.success:
            self.performance_metrics["successful_executions"] += 1

        # Update average execution time efficiently
        current_avg = self.performance_metrics["average_execution_time"]
        total_executions = self.performance_metrics["total_executions"]
        
        self.performance_metrics["average_execution_time"] = (
            (current_avg * (total_executions - 1) + result.execution_time) / total_executions
        )

        # Update pattern usage
        self.performance_metrics["pattern_usage"][result.pattern_used.value] += 1

        # Update tool usage efficiently
        for tool in result.tools_used:
            self.performance_metrics["tool_usage"][tool] += 1

        # Update resource usage metrics
        if result.memory_used_mb > 0:
            resource_metrics = self.performance_metrics["resource_usage"]
            
            # Update average memory usage
            current_mem_avg = resource_metrics["avg_memory_mb"]
            resource_metrics["avg_memory_mb"] = (
                (current_mem_avg * (total_executions - 1) + result.memory_used_mb) / total_executions
            )
            
            # Update peak memory
            resource_metrics["peak_memory_mb"] = max(
                resource_metrics["peak_memory_mb"], result.memory_peak_mb
            )
            
            # Update average CPU usage
            current_cpu_avg = resource_metrics["avg_cpu_percent"]
            resource_metrics["avg_cpu_percent"] = (
                (current_cpu_avg * (total_executions - 1) + result.cpu_usage_percent) / total_executions
            )

        # Track errors efficiently
        if not result.success and result.error_message:
            error_type = type(result.error_message).__name__ if hasattr(result.error_message, "__name__") else "General"
            self.performance_metrics["error_patterns"][error_type] += 1

    async def _maybe_cleanup_resources(self):
        """Perform resource cleanup if needed."""
        current_time = time.time()
        current_memory = psutil.virtual_memory().used / 1024 / 1024

        # Check if cleanup is needed
        should_cleanup = (
            current_memory > self.memory_threshold_mb or
            (current_time - self.last_gc_time) > self.gc_interval
        )

        if should_cleanup:
            # Clean up resource pool if it's getting large
            if len(self.resource_pool.available_agents) > self.resource_pool.max_pool_size:
                excess_agents = len(self.resource_pool.available_agents) - self.resource_pool.max_pool_size
                for _ in range(excess_agents):
                    if self.resource_pool.available_agents:
                        self.resource_pool.available_agents.popleft()

            # Clear old cache entries if memory is high
            if current_memory > self.memory_threshold_mb:
                self.task_analyzer.clear_cache()
                if hasattr(self.tool_discovery, 'clear_cache'):
                    self.tool_discovery.clear_cache()

            # Run garbage collection
            gc.collect()
            self.last_gc_time = current_time
            
            self.logger.debug(f"Resource cleanup performed. Memory: {current_memory:.1f}MB")

    def _create_error_result(
        self, 
        error_message: str, 
        pattern: ExecutionPattern, 
        start_time: datetime,
        start_memory: float,
        start_cpu: float
    ) -> ExecutionResult:
        """Create a standardized error result."""
        
        execution_time = (datetime.now() - start_time).total_seconds()
        end_memory = psutil.virtual_memory().used / 1024 / 1024
        end_cpu = psutil.cpu_percent(interval=None)
        
        return ExecutionResult(
            success=False,
            result="",
            execution_time=execution_time,
            pattern_used=pattern,
            tools_used=[],
            agents_created=0,
            error_message=error_message,
            memory_used_mb=end_memory - start_memory,
            memory_peak_mb=max(end_memory, start_memory),
            cpu_usage_percent=end_cpu - start_cpu,
        )

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get optimized performance summary with resource metrics."""

        success_rate = (
            self.performance_metrics["successful_executions"]
            / max(self.performance_metrics["total_executions"], 1)
        ) * 100

        most_used_pattern = max(
            self.performance_metrics["pattern_usage"].items(),
            key=lambda x: x[1],
            default=("none", 0),
        )

        most_used_tool = max(
            self.performance_metrics["tool_usage"].items(),
            key=lambda x: x[1],
            default=("none", 0),
        )

        # Get cache performance summary
        cache_summary = {}
        if hasattr(self.task_analyzer, 'get_cache_info'):
            cache_info = self.task_analyzer.get_cache_info()
            if cache_info and 'hit_rate' in cache_info:
                cache_summary["task_analyzer_hit_rate"] = cache_info['hit_rate']

        if hasattr(self.tool_discovery, 'get_performance_summary'):
            tool_discovery_perf = self.tool_discovery.get_performance_summary()
            cache_summary.update(tool_discovery_perf)

        return {
            "total_executions": self.performance_metrics["total_executions"],
            "success_rate": f"{success_rate:.1f}%",
            "average_execution_time": f"{self.performance_metrics['average_execution_time']:.3f}s",
            "most_used_pattern": f"{most_used_pattern[0]} ({most_used_pattern[1]} times)",
            "most_used_tool": f"{most_used_tool[0]} ({most_used_tool[1]} times)",
            "unique_tools_used": len(self.performance_metrics["tool_usage"]),
            "error_types": len(self.performance_metrics["error_patterns"]),
            "resource_usage": self.performance_metrics["resource_usage"],
            "cache_performance": cache_summary,
            "active_executions": self.active_executions,
            "resource_pool_status": {
                "available_agents": len(self.resource_pool.available_agents),
                "active_agents": len(self.resource_pool.active_agents),
                "max_pool_size": self.resource_pool.max_pool_size,
            },
            "installation_summary": self.dynamic_installer.get_installation_summary() if hasattr(self.dynamic_installer, 'get_installation_summary') else {},
        }

    async def optimize_configuration(self) -> Dict[str, Any]:
        """Optimize configuration based on usage patterns and resource metrics."""

        optimization_suggestions = []

        # Analyze pattern effectiveness with resource consideration
        pattern_success_rates = {}
        pattern_resource_usage = {}
        
        for result in list(self.execution_history):  # Convert deque to list for iteration
            pattern = result.pattern_used.value
            
            if pattern not in pattern_success_rates:
                pattern_success_rates[pattern] = {"successes": 0, "total": 0}
                pattern_resource_usage[pattern] = {"memory": 0.0, "cpu": 0.0, "count": 0}

            pattern_success_rates[pattern]["total"] += 1
            if result.success:
                pattern_success_rates[pattern]["successes"] += 1

            # Track resource usage per pattern
            if result.memory_used_mb > 0:
                pattern_resource_usage[pattern]["memory"] += result.memory_used_mb
                pattern_resource_usage[pattern]["cpu"] += result.cpu_usage_percent
                pattern_resource_usage[pattern]["count"] += 1

        # Find underperforming patterns
        for pattern, stats in pattern_success_rates.items():
            success_rate = stats["successes"] / max(stats["total"], 1)
            if success_rate < 0.7 and stats["total"] > 3:
                optimization_suggestions.append(
                    f"Pattern {pattern} has low success rate ({success_rate:.1%}), consider configuration review"
                )

        # Analyze resource usage patterns
        for pattern, usage in pattern_resource_usage.items():
            if usage["count"] > 0:
                avg_memory = usage["memory"] / usage["count"]
                avg_cpu = usage["cpu"] / usage["count"]
                
                if avg_memory > 500:  # High memory usage
                    optimization_suggestions.append(
                        f"Pattern {pattern} uses high memory ({avg_memory:.1f}MB avg), consider optimization"
                    )

        # Memory optimization suggestions
        current_memory = psutil.virtual_memory().used / 1024 / 1024
        if current_memory > self.memory_threshold_mb:
            optimization_suggestions.append(
                f"Current memory usage ({current_memory:.1f}MB) exceeds threshold, consider clearing caches"
            )

        # Resource pool optimization
        pool_efficiency = len(self.resource_pool.active_agents) / max(len(self.resource_pool.available_agents) + len(self.resource_pool.active_agents), 1)
        if pool_efficiency < 0.3:
            optimization_suggestions.append(
                "Resource pool has low utilization, consider reducing pool size"
            )

        return {
            "pattern_success_rates": pattern_success_rates,
            "pattern_resource_usage": pattern_resource_usage,
            "optimization_suggestions": optimization_suggestions,
            "current_performance": self.get_performance_summary(),
            "memory_status": {
                "current_usage_mb": current_memory,
                "threshold_mb": self.memory_threshold_mb,
                "last_cleanup": self.last_gc_time,
            }
        }

    def cleanup(self):
        """Clean up all resources."""
        self.resource_pool.cleanup()
        self.execution_history.clear()
        if hasattr(self.task_analyzer, 'clear_cache'):
            self.task_analyzer.clear_cache()
        if hasattr(self.tool_discovery, 'clear_cache'):
            self.tool_discovery.clear_cache()
        gc.collect()
        self.logger.info("Meta-coordinator cleanup completed")

    def __del__(self):
        """Cleanup on destruction."""
        try:
            self.cleanup()
        except:
            pass  # Ignore cleanup errors during destruction


# Backward compatibility alias
MetaCoordinator = ResourceOptimizedMetaCoordinator
