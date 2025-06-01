#!/usr/bin/env python3
"""
Validation test for autonomous MCP-Agent components.
Tests basic instantiation and simple functionality of autonomous modules.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

async def test_autonomous_components():
    """Test autonomous component instantiation and basic functionality."""
    print("Testing Autonomous Component Validation")
    print("=" * 50)
    
    try:
        # Test 1: Component Instantiation
        print("\n1. Testing Component Instantiation...")
        
        from mcp_agent.autonomous.autonomous_orchestrator import AutonomousOrchestrator
        from mcp_agent.autonomous.dynamic_agent_factory import DynamicAgentFactory
        from mcp_agent.autonomous.task_analyzer import TaskAnalyzer
        from mcp_agent.autonomous.tool_discovery import ToolDiscoveryAgent
        from mcp_agent.autonomous.decision_engine import AutonomousDecisionEngine
        from mcp_agent.autonomous.meta_coordinator import MetaCoordinator
        
        print("   [OK] All autonomous modules imported successfully")
        
        # Test 2: Basic Instantiation
        print("\n2. Testing Basic Component Creation...")
        
        # These should not require complex dependencies for basic instantiation
        try:
            task_analyzer = TaskAnalyzer()
            print("   [OK] TaskAnalyzer created")
        except Exception as e:
            print(f"   [FAIL] TaskAnalyzer failed: {e}")
            return False
            
        try:
            # ToolDiscoveryAgent requires MCPConnectionManager, so skip for basic test
            print("   [SKIP] ToolDiscoveryAgent (requires dependencies)")
        except Exception as e:
            print(f"   [FAIL] ToolDiscoveryAgent failed: {e}")
            return False
            
        try:
            decision_engine = AutonomousDecisionEngine()
            print("   [OK] AutonomousDecisionEngine created")
        except Exception as e:
            print(f"   [FAIL] AutonomousDecisionEngine failed: {e}")
            return False
        
        # Test 3: Task Analysis
        print("\n3. Testing Task Analysis...")
        
        test_task = "Read a file and summarize its contents"
        try:
            analysis = task_analyzer.analyze_task(test_task)
            print(f"   [OK] Task analysis completed: {analysis.complexity.name} complexity")
        except Exception as e:
            print(f"   [FAIL] Task analysis failed: {e}")
            return False
        
        # Test 4: Integration Test (without MCP servers)
        print("\n4. Testing Component Integration...")
        
        try:
            # Test that components can work together conceptually
            test_task = "Create a simple text file"
            task_analysis, strategy_recommendation = decision_engine.analyze_and_recommend(test_task, [])
            print(f"   [OK] Integration test passed: recommended {strategy_recommendation.pattern.name} pattern")
        except Exception as e:
            print(f"   [FAIL] Integration test failed: {e}")
            return False
        
        print("\n[SUCCESS] All autonomous component tests passed!")
        return True
        
    except ImportError as e:
        print(f"\n[ERROR] Import failed: {e}")
        return False
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        return False

if __name__ == "__main__":
    import asyncio
    success = asyncio.run(test_autonomous_components())
    print(f"\n[RESULT] Validation {'PASSED' if success else 'FAILED'}")
    sys.exit(0 if success else 1)
