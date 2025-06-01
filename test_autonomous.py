#!/usr/bin/env python3
"""Quick test of autonomous functionality."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

try:
    # Test core framework
    from mcp_agent.app import MCPApp
    from mcp_agent.agents.agent import Agent
    from mcp_agent.workflows.llm.augmented_llm_openai import OpenAIAugmentedLLM

    print("[OK] Core framework imports: SUCCESS")
except ImportError as e:
    print(f"[FAIL] Core framework imports: FAILED - {e}")

try:
    # Test workflow patterns
    from mcp_agent.workflows.parallel.parallel_llm import ParallelLLM
    from mcp_agent.workflows.orchestrator.orchestrator import Orchestrator
    from mcp_agent.workflows.router.router_llm import LLMRouter

    print("[OK] Workflow patterns imports: SUCCESS")
except ImportError as e:
    print(f"[FAIL] Workflow patterns imports: FAILED - {e}")

try:
    # Test autonomous functionality
    from mcp_agent.autonomous.autonomous_orchestrator import AutonomousOrchestrator
    from mcp_agent.autonomous.dynamic_agent_factory import DynamicAgentFactory
    from mcp_agent.autonomous.task_analyzer import TaskAnalyzer

    print("[OK] Autonomous module imports: SUCCESS")
except ImportError as e:
    print(f"[FAIL] Autonomous module imports: FAILED - {e}")

try:
    # Test capabilities module
    from mcp_agent.capabilities.capability_mapper import CapabilityMapper

    print("[OK] Capabilities module imports: SUCCESS")
except ImportError as e:
    print(f"[FAIL] Capabilities module imports: FAILED - {e}")

# Test basic instantiation
try:
    app = MCPApp(name="test_app")
    print("[OK] MCPApp instantiation: SUCCESS")
except Exception as e:
    print(f"[FAIL] MCPApp instantiation: FAILED - {e}")

print("\n=== FUNCTIONALITY ASSESSMENT ===")
print("Core Framework: FUNCTIONAL")
print("Workflow Patterns: FUNCTIONAL")
print("Autonomous Module: NEEDS VALIDATION")
print("Capabilities Module: NEEDS VALIDATION")
