#!/usr/bin/env python3
"""
Quick Fix Script for MCP-Agent Import Issues
Automatically fixes common import problems in autonomous modules.
"""

import os
import sys
from pathlib import Path


def ensure_init_file(directory_path, content=None):
    """Ensure __init__.py exists in a directory with proper content."""
    init_path = Path(directory_path) / "__init__.py"

    if not init_path.exists():
        print(f"Creating missing {init_path}")
        with open(init_path, "w") as f:
            if content:
                f.write(content)
            else:
                f.write('"""Module initialization."""\n')
        return True
    else:
        print(f"✅ {init_path} already exists")
        return False


def fix_autonomous_init():
    """Fix the autonomous module __init__.py with proper imports."""
    autonomous_init_content = '''"""
Autonomous agent capabilities for MCP-Agent.

This module provides advanced autonomous features including:
- AutonomousOrchestrator: Self-managing workflow execution
- DynamicAgentFactory: Runtime agent creation
- TaskAnalyzer: Intelligent task decomposition
- ToolDiscovery: Automatic capability detection
- DecisionEngine: Strategic decision making
- MetaCoordinator: High-level orchestration
"""

# Core autonomous components
try:
    from .autonomous_orchestrator import AutonomousOrchestrator
except ImportError as e:
    print(f"Warning: Could not import AutonomousOrchestrator: {e}")
    AutonomousOrchestrator = None

try:
    from .dynamic_agent_factory import DynamicAgentFactory
except ImportError as e:
    print(f"Warning: Could not import DynamicAgentFactory: {e}")
    DynamicAgentFactory = None

try:
    from .task_analyzer import TaskAnalyzer
except ImportError as e:
    print(f"Warning: Could not import TaskAnalyzer: {e}")
    TaskAnalyzer = None

try:
    from .decision_engine import DecisionEngine
except ImportError as e:
    print(f"Warning: Could not import DecisionEngine: {e}")
    DecisionEngine = None

try:
    from .meta_coordinator import MetaCoordinator
except ImportError as e:
    print(f"Warning: Could not import MetaCoordinator: {e}")
    MetaCoordinator = None

# Optional components
try:
    from .tool_discovery import discover_tools, map_capabilities
except ImportError as e:
    print(f"Warning: Could not import tool discovery functions: {e}")
    discover_tools = None
    map_capabilities = None

__all__ = [
    "AutonomousOrchestrator",
    "DynamicAgentFactory", 
    "TaskAnalyzer",
    "DecisionEngine",
    "MetaCoordinator",
    "discover_tools",
    "map_capabilities",
]
'''

    autonomous_init_path = Path("src/mcp_agent/autonomous/__init__.py")
    print(f"Updating {autonomous_init_path} with proper imports...")

    with open(autonomous_init_path, "w") as f:
        f.write(autonomous_init_content)

    print("✅ Updated autonomous/__init__.py")


def fix_capabilities_init():
    """Fix the capabilities module __init__.py."""
    capabilities_init_content = '''"""
Capability mapping and analysis for MCP-Agent.

This module provides tools for mapping and analyzing agent capabilities.
"""

try:
    from .capability_mapper import CapabilityMapper
except ImportError as e:
    print(f"Warning: Could not import CapabilityMapper: {e}")
    CapabilityMapper = None

__all__ = ["CapabilityMapper"]
'''

    capabilities_init_path = Path("src/mcp_agent/capabilities/__init__.py")
    print(f"Updating {capabilities_init_path} with proper imports...")

    with open(capabilities_init_path, "w") as f:
        f.write(capabilities_init_content)

    print("✅ Updated capabilities/__init__.py")


def check_and_fix_dependencies():
    """Check if all required dependencies are installed."""
    required_packages = [
        "fastapi",
        "instructor",
        "pydantic",
        "pyyaml",
        "rich",
        "typer",
        "numpy",
        "scikit-learn",
        "aiohttp",
        "websockets",
        "mcp",
        "temporalio",
        "anthropic",
        "openai",
    ]

    missing_packages = []

    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            print(f"✅ {package}: Available")
        except ImportError:
            print(f"❌ {package}: Missing")
            missing_packages.append(package)

    if missing_packages:
        print(f"\n🔧 To install missing packages:")
        print(f"uv add {' '.join(missing_packages)}")
        return False

    return True


def main():
    print("=" * 50)
    print("MCP-AGENT QUICK FIX SCRIPT")
    print("=" * 50)

    # Change to project root
    project_root = Path(__file__).parent
    os.chdir(project_root)

    print(f"Working directory: {project_root}")

    # Ensure all __init__.py files exist
    print("\n🔧 FIXING __INIT__.PY FILES")
    print("-" * 25)

    directories = [
        "src/mcp_agent",
        "src/mcp_agent/agents",
        "src/mcp_agent/autonomous",
        "src/mcp_agent/capabilities",
        "src/mcp_agent/cli",
        "src/mcp_agent/core",
        "src/mcp_agent/workflows",
        "src/mcp_agent/workflows/llm",
        "src/mcp_agent/mcp",
    ]

    for directory in directories:
        ensure_init_file(directory)

    # Fix specific module imports
    print("\n🔧 FIXING MODULE IMPORTS")
    print("-" * 25)

    fix_autonomous_init()
    fix_capabilities_init()

    # Check dependencies
    print("\n🔧 CHECKING DEPENDENCIES")
    print("-" * 25)

    deps_ok = check_and_fix_dependencies()

    # Final recommendations
    print("\n📋 NEXT STEPS")
    print("-" * 15)

    print("1. Run: python diagnostic.py")
    print("2. If still failing, run: uv install --all-extras")
    print(
        "3. Test autonomous imports: python -c 'from mcp_agent.autonomous import AutonomousOrchestrator'"
    )
    print("4. Run full tests: python test_autonomous.py")

    if not deps_ok:
        print("5. Install missing dependencies first!")

    print("\n✨ Quick fix complete!")


if __name__ == "__main__":
    main()
