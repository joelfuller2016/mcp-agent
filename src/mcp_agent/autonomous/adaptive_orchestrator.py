"""
Adaptive Orchestrator for Autonomous MCP Agent

This module provides the main autonomous orchestration system that combines
tool discovery, decision making, and dynamic agent creation to execute tasks
automatically without manual configuration.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Union, Type
from dataclasses import dataclass

from ..app import MCPApp
from ..agents.agent import Agent
from ..workflows.llm.augmented_llm import AugmentedLLM
from ..workflows.llm.augmented_llm_openai import OpenAIAugmentedLLM
from ..workflows.llm.augmented_llm_anthropic import AnthropicAugmentedLLM
from ..workflows.parallel.parallel_llm import ParallelLLM
from ..workflows.router.router_llm import LLMRouter
from ..workflows.orchestrator.orchestrator import Orchestrator
from ..workflows.evaluator_optimizer.evaluator_optimizer import EvaluatorOptimizerLLM
from ..workflows.swarm.swarm_anthropic import AnthropicSwarm
from ..workflows.swarm.swarm_openai import OpenAISwarm

from .discovery import AutoDiscoverySystem, MCPServerProfile
from .decision_engine import AutonomousDecisionEngine, TaskAnalysis, StrategyRecommendation, WorkflowPattern
from .agent_factory import DynamicAgentFactory


@dataclass
class ExecutionResult:
    """Result of autonomous task execution"""
    task_description: str
    result: str
    pattern_used: WorkflowPattern
    agents_created: List[str]
    execution_time: float
    success: bool
    error_message: Optional[str] = None
    confidence: float = 0.0


class AdaptiveOrchestrator:
    """
    Main autonomous orchestrator that automatically:
    1. Discovers available tools
    2. Analyzes tasks
    3. Selects optimal workflow patterns
    4. Creates specialized agents
    5. Executes tasks autonomously
    """
    
    def __init__(self, app: Optional[MCPApp] = None, llm_provider: str = "openai"):
        self.logger = logging.getLogger(__name__)
        self.app = app or MCPApp(name="autonomous_mcp_agent")
        self.llm_provider = llm_provider
        
        # Core autonomous components
        self.discovery_system = AutoDiscoverySystem()
        self.decision_engine = AutonomousDecisionEngine()
        self.agent_factory = DynamicAgentFactory()
        
        # State tracking
        self.available_servers: Dict[str, MCPServerProfile] = {}
        self.created_agents: Dict[str, Agent] = {}
        self.execution_history: List[ExecutionResult] = []
        
        # LLM providers
        self._llm_providers = {
            "openai": OpenAIAugmentedLLM,
            "anthropic": AnthropicAugmentedLLM
        }
        
        self.logger.info("Adaptive Orchestrator initialized")
    
    async def initialize(self):
        """Initialize the autonomous system"""
        self.logger.info("Initializing autonomous MCP agent...")
        
        # Discover available tools
        self.available_servers = await self.discovery_system.discover_available_tools()
        
        if not self.available_servers:
            self.logger.warning("No MCP servers discovered - some functionality may be limited")
        else:
            self.logger.info(f"Discovered {len(self.available_servers)} MCP servers")
        
        self.logger.info("Autonomous system ready")
    
    async def execute_autonomous_task(self, task_description: str, 
                                    preferences: Optional[Dict[str, Any]] = None) -> ExecutionResult:
        """
        Execute a task autonomously with full auto-discovery and decision making
        
        Args:
            task_description: Natural language description of the task
            preferences: Optional preferences for execution (e.g., preferred LLM, timeout)
        
        Returns:
            ExecutionResult with details of execution
        """
        start_time = asyncio.get_event_loop().time()
        self.logger.info(f"Executing autonomous task: {task_description}")
        
        try:
            # Ensure we have the necessary tools
            await self._ensure_tools_for_task(task_description)
            
            # Analyze task and get strategy recommendation
            task_analysis, strategy_recommendation = self.decision_engine.analyze_and_recommend(
                task_description, list(self.available_servers.values())
            )
            
            # Log decision reasoning
            self.logger.info(f"Task analysis complete:")
            self.logger.info(f"  Complexity: {task_analysis.complexity.name}")
            self.logger.info(f"  Pattern: {strategy_recommendation.pattern.value}")
            self.logger.info(f"  Confidence: {strategy_recommendation.confidence:.2f}")
            
            # Create agents for the selected pattern
            agents = self.agent_factory.create_agents_for_task(
                task_analysis, strategy_recommendation.pattern, list(self.available_servers.values())
            )
            
            # Execute using the selected pattern
            result = await self._execute_with_pattern(
                task_description, strategy_recommendation.pattern, agents, preferences
            )
            
            execution_time = asyncio.get_event_loop().time() - start_time
            
            # Create execution result
            execution_result = ExecutionResult(
                task_description=task_description,
                result=result,
                pattern_used=strategy_recommendation.pattern,
                agents_created=[agent.name for agent in agents],
                execution_time=execution_time,
                success=True,
                confidence=strategy_recommendation.confidence
            )
            
            self.execution_history.append(execution_result)
            
            self.logger.info(f"Task completed successfully in {execution_time:.2f}s "
                           f"using {strategy_recommendation.pattern.value} pattern")
            
            return execution_result
            
        except Exception as e:
            execution_time = asyncio.get_event_loop().time() - start_time
            error_msg = f"Task execution failed: {str(e)}"
            self.logger.error(error_msg)
            
            execution_result = ExecutionResult(
                task_description=task_description,
                result="",
                pattern_used=WorkflowPattern.DIRECT,  # Default for error cases
                agents_created=[],
                execution_time=execution_time,
                success=False,
                error_message=error_msg
            )
            
            self.execution_history.append(execution_result)
            return execution_result
    
    async def _ensure_tools_for_task(self, task_description: str):
        """Ensure required tools are available, installing if needed"""
        required_tools = await self.discovery_system.ensure_tools_for_task(task_description)
        
        # Update available servers with any newly installed tools
        for tool in required_tools:
            if tool.name not in self.available_servers:
                self.available_servers[tool.name] = tool
                self.logger.info(f"Added newly available tool: {tool.name}")
    
    async def _execute_with_pattern(self, task_description: str, pattern: WorkflowPattern,
                                  agents: List[Agent], preferences: Optional[Dict[str, Any]]) -> str:
        """Execute task using the specified workflow pattern"""
        
        # Get LLM factory
        llm_factory = self._llm_providers.get(self.llm_provider, OpenAIAugmentedLLM)
        
        async with self.app.run() as mcp_app:
            
            if pattern == WorkflowPattern.DIRECT:
                return await self._execute_direct(task_description, agents[0], llm_factory)
            
            elif pattern == WorkflowPattern.PARALLEL:
                return await self._execute_parallel(task_description, agents, llm_factory)
            
            elif pattern == WorkflowPattern.ROUTER:
                return await self._execute_router(task_description, agents, llm_factory)
            
            elif pattern == WorkflowPattern.SWARM:
                return await self._execute_swarm(task_description, agents, llm_factory)
            
            elif pattern == WorkflowPattern.ORCHESTRATOR:
                return await self._execute_orchestrator(task_description, agents, llm_factory)
            
            elif pattern == WorkflowPattern.EVALUATOR_OPTIMIZER:
                return await self._execute_evaluator_optimizer(task_description, agents, llm_factory)
            
            else:
                # Fallback to direct execution
                return await self._execute_direct(task_description, agents[0], llm_factory)
    
    async def _execute_direct(self, task_description: str, agent: Agent, 
                            llm_factory: Type[AugmentedLLM]) -> str:
        """Execute task with direct agent pattern"""
        async with agent:
            llm = await agent.attach_llm(llm_factory)
            result = await llm.generate_str(task_description)
            return result
    
    async def _execute_parallel(self, task_description: str, agents: List[Agent],
                              llm_factory: Type[AugmentedLLM]) -> str:
        """Execute task with parallel pattern"""
        if len(agents) < 2:
            # Fallback to direct if we don't have enough agents
            return await self._execute_direct(task_description, agents[0], llm_factory)
        
        # Last agent is typically the coordinator
        coordinator = agents[-1]
        specialist_agents = agents[:-1]
        
        parallel_llm = ParallelLLM(
            fan_in_agent=coordinator,
            fan_out_agents=specialist_agents,
            llm_factory=llm_factory
        )
        
        result = await parallel_llm.generate_str(task_description)
        return result
    
    async def _execute_router(self, task_description: str, agents: List[Agent],
                            llm_factory: Type[AugmentedLLM]) -> str:
        """Execute task with router pattern"""
        if not agents:
            raise ValueError("No agents available for router pattern")
        
        # Create router with available agents
        router = LLMRouter(
            llm=llm_factory(),
            agents=agents
        )
        
        # Route to best agent
        results = await router.route(task_description, top_k=1)
        
        if results:
            chosen_agent = results[0].result
            async with chosen_agent:
                llm = await chosen_agent.attach_llm(llm_factory)
                result = await llm.generate_str(task_description)
                return result
        else:
            # Fallback to first agent
            return await self._execute_direct(task_description, agents[0], llm_factory)
    
    async def _execute_swarm(self, task_description: str, agents: List[Agent],
                           llm_factory: Type[AugmentedLLM]) -> str:
        """Execute task with swarm pattern"""
        if not agents:
            raise ValueError("No agents available for swarm pattern")
        
        # First agent is typically the triage agent
        triage_agent = agents[0]
        
        # Convert agents to swarm agents (simplified for this implementation)
        if self.llm_provider == "anthropic":
            swarm = AnthropicSwarm(agent=triage_agent)
        else:
            swarm = OpenAISwarm(agent=triage_agent)
        
        result = await swarm.generate_str(task_description)
        return result
    
    async def _execute_orchestrator(self, task_description: str, agents: List[Agent],
                                  llm_factory: Type[AugmentedLLM]) -> str:
        """Execute task with orchestrator pattern"""
        if len(agents) < 2:
            return await self._execute_direct(task_description, agents[0], llm_factory)
        
        # First agent is typically the planner, rest are workers
        worker_agents = agents[1:] if len(agents) > 1 else agents
        
        orchestrator = Orchestrator(
            llm_factory=llm_factory,
            available_agents=worker_agents
        )
        
        result = await orchestrator.generate_str(task_description)
        return result
    
    async def _execute_evaluator_optimizer(self, task_description: str, agents: List[Agent],
                                         llm_factory: Type[AugmentedLLM]) -> str:
        """Execute task with evaluator-optimizer pattern"""
        if len(agents) < 2:
            return await self._execute_direct(task_description, agents[0], llm_factory)
        
        optimizer_agent = agents[0]  # First agent is optimizer
        evaluator_agent = agents[1]  # Second agent is evaluator
        
        eo_llm = EvaluatorOptimizerLLM(
            optimizer=optimizer_agent,
            evaluator=evaluator_agent,
            llm_factory=llm_factory
        )
        
        result = await eo_llm.generate_str(task_description)
        return result
    
    async def explain_approach(self, task_description: str) -> str:
        """Explain how the system would approach a task without executing it"""
        # Analyze task
        task_analysis, strategy_recommendation = self.decision_engine.analyze_and_recommend(
            task_description, list(self.available_servers.values())
        )
        
        # Generate detailed explanation
        explanation = self.decision_engine.explain_decision(task_analysis, strategy_recommendation)
        
        # Add agent creation details
        agents = self.agent_factory.create_agents_for_task(
            task_analysis, strategy_recommendation.pattern, list(self.available_servers.values())
        )
        
        agent_details = f\"\\nAgent Creation:\\n\"
        for agent in agents:
            agent_details += f\"- {agent.name}: {agent.instruction[:100]}...\\n\"
        
        return explanation + agent_details
    
    def get_execution_history(self) -> List[ExecutionResult]:
        \"\"\"Get history of executed tasks\"\"\"
        return self.execution_history.copy()
    
    def get_available_capabilities(self) -> Dict[str, List[str]]:
        \"\"\"Get summary of available capabilities\"\"\"
        return self.discovery_system.list_available_capabilities()
    
    def get_system_status(self) -> Dict[str, Any]:
        \"\"\"Get current system status\"\"\"
        return {
            \"available_servers\": len(self.available_servers),
            \"server_names\": list(self.available_servers.keys()),
            \"execution_history_count\": len(self.execution_history),
            \"successful_executions\": sum(1 for r in self.execution_history if r.success),
            \"llm_provider\": self.llm_provider,
            \"specializations_available\": self.agent_factory.get_available_specializations()
        }
    
    async def interactive_mode(self):
        \"\"\"Run in interactive mode for testing and demonstration\"\"\"
        print(\"🤖 Autonomous MCP Agent - Interactive Mode\")
        print(\"Type 'help' for commands, 'quit' to exit\\n\")
        
        await self.initialize()
        
        while True:
            try:
                user_input = input(\"📝 Task: \").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    break
                elif user_input.lower() == 'help':
                    self._show_help()
                    continue
                elif user_input.lower() == 'status':
                    self._show_status()
                    continue
                elif user_input.lower().startswith('explain '):
                    task = user_input[8:]
                    explanation = await self.explain_approach(task)
                    print(f\"\\n📊 Approach Analysis:\\n{explanation}\\n\")
                    continue
                elif not user_input:
                    continue
                
                print(f\"\\n🔄 Processing: {user_input}\")
                
                result = await self.execute_autonomous_task(user_input)
                
                if result.success:
                    print(f\"\\n✅ Result ({result.pattern_used.value} pattern, {result.execution_time:.1f}s):\")
                    print(f\"{result.result}\\n\")
                else:
                    print(f\"\\n❌ Error: {result.error_message}\\n\")
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f\"\\n❌ Unexpected error: {str(e)}\\n\")
        
        print(\"\\n👋 Goodbye!\")
    
    def _show_help(self):
        \"\"\"Show help information\"\"\"
        print(\"\\n🤖 Available Commands:\")
        print(\"  help - Show this help message\")
        print(\"  status - Show system status\")
        print(\"  explain <task> - Explain approach without executing\")
        print(\"  quit/exit/q - Exit interactive mode\")
        print(\"  Or just type any task description to execute it autonomously\\n\")
    
    def _show_status(self):
        \"\"\"Show current system status\"\"\"
        status = self.get_system_status()
        print(f\"\\n📊 System Status:\")
        print(f\"  Available MCP servers: {status['available_servers']}\")
        print(f\"  Server names: {', '.join(status['server_names'][:5])}{'...' if len(status['server_names']) > 5 else ''}\")
        print(f\"  Tasks executed: {status['execution_history_count']}\")
        print(f\"  Success rate: {status['successful_executions']}/{status['execution_history_count']}\")
        print(f\"  LLM provider: {status['llm_provider']}\")
        print(f\"  Available specializations: {len(status['specializations_available'])}\\n\")


# Convenience functions for easy usage
async def execute_task(task_description: str, llm_provider: str = \"openai\") -> str:
    \"\"\"
    Convenience function to execute a single task autonomously
    
    Args:
        task_description: Natural language description of the task
        llm_provider: LLM provider to use ('openai' or 'anthropic')
    
    Returns:
        Task result as string
    \"\"\"
    orchestrator = AdaptiveOrchestrator(llm_provider=llm_provider)
    await orchestrator.initialize()
    
    result = await orchestrator.execute_autonomous_task(task_description)
    
    if result.success:
        return result.result
    else:
        raise Exception(f\"Task execution failed: {result.error_message}\")


async def explain_task_approach(task_description: str) -> str:
    \"\"\"
    Convenience function to explain how a task would be approached
    
    Args:
        task_description: Natural language description of the task
    
    Returns:
        Detailed explanation of the approach
    \"\"\"
    orchestrator = AdaptiveOrchestrator()
    await orchestrator.initialize()
    
    return await orchestrator.explain_approach(task_description)


async def run_demo():
    \"\"\"Run a demonstration of autonomous capabilities\"\"\"
    orchestrator = AdaptiveOrchestrator()
    
    print(\"🚀 Autonomous MCP Agent Demo\")
    print(\"=\" * 40)
    
    await orchestrator.initialize()
    
    demo_tasks = [
        \"Read the README.md file and tell me what this project does\",
        \"Search for information about Model Context Protocol and summarize it\",
        \"Create a simple task list for organizing my projects\",
        \"Help me understand the complexity of building an autonomous agent system\"
    ]
    
    for i, task in enumerate(demo_tasks, 1):
        print(f\"\\n📋 Demo Task {i}: {task}\")
        print(\"-\" * 50)
        
        # First explain the approach
        explanation = await orchestrator.explain_approach(task)
        print(f\"\\n🧠 Approach: {explanation.split('Strategy Recommendation:')[1].split('Selected pattern:')[1].split('Reasoning:')[1][:100]}...\")
        
        # Then execute
        result = await orchestrator.execute_autonomous_task(task)
        
        if result.success:
            print(f\"\\n✅ Result ({result.pattern_used.value}, {result.execution_time:.1f}s):\")
            print(f\"{result.result[:200]}{'...' if len(result.result) > 200 else ''}\")
        else:
            print(f\"\\n❌ Failed: {result.error_message}\")
    
    # Show final status
    print(f\"\\n📊 Demo Complete!\")
    status = orchestrator.get_system_status()
    print(f\"Executed {status['execution_history_count']} tasks with {status['successful_executions']} successes\")


if __name__ == \"__main__\":
    # Run interactive mode when called directly
    async def main():
        orchestrator = AdaptiveOrchestrator()
        await orchestrator.interactive_mode()
    
    asyncio.run(main())
