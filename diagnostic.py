#!/usr/bin/env python3
"""
MCP-Agent Autonomous Module Diagnostic Script
Systematically tests all autonomous module imports and reports specific issues.
"""

import sys
import os
import traceback
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))


def test_import(module_name, class_name=None):
    """Test import of a specific module/class and report results."""
    try:
        if class_name:
            module = __import__(module_name, fromlist=[class_name])
            getattr(module, class_name)
            print(f"[OK] {module_name}.{class_name}: SUCCESS")
            return True
        else:
            __import__(module_name)
            print(f"[OK] {module_name}: SUCCESS")
            return True
    except ImportError as e:
        print(
            f"[FAIL] {module_name}{('.' + class_name) if class_name else ''}: IMPORT ERROR - {e}"
        )
        return False
    except AttributeError as e:
        print(f"[FAIL] {module_name}.{class_name}: ATTRIBUTE ERROR - {e}")
        return False
    except Exception as e:
        print(
            f"[FAIL] {module_name}{('.' + class_name) if class_name else ''}: UNEXPECTED ERROR - {e}"
        )
        print(f"   Traceback: {traceback.format_exc()}")
        return False


def check_file_exists(file_path):
    """Check if a file exists and report."""
    if Path(file_path).exists():
        print(f"[OK] File exists: {file_path}")
        return True
    else:
        print(f"[FAIL] File missing: {file_path}")
        return False


def main():
    print("=" * 60)
    print("MCP-AGENT AUTONOMOUS MODULE DIAGNOSTIC")
    print("=" * 60)

    # Check project structure
    print("\nPROJECT STRUCTURE CHECK")
    print("-" * 30)

    files_to_check = [
        "src/mcp_agent/__init__.py",
        "src/mcp_agent/autonomous/__init__.py",
        "src/mcp_agent/autonomous/autonomous_orchestrator.py",
        "src/mcp_agent/autonomous/dynamic_agent_factory.py",
        "src/mcp_agent/autonomous/task_analyzer.py",
        "src/mcp_agent/autonomous/tool_discovery.py",
        "src/mcp_agent/autonomous/decision_engine.py",
        "src/mcp_agent/autonomous/meta_coordinator.py",
        "src/mcp_agent/capabilities/capability_mapper.py",
    ]

    structure_ok = True
    for file_path in files_to_check:
        if not check_file_exists(file_path):
            structure_ok = False

    # Check __init__.py contents
    print("\n__INIT__.PY CONTENT CHECK")
    print("-" * 30)

    init_files = [
        "src/mcp_agent/__init__.py",
        "src/mcp_agent/autonomous/__init__.py",
        "src/mcp_agent/capabilities/__init__.py",
    ]

    for init_file in init_files:
        if Path(init_file).exists():
            try:
                with open(init_file, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if content:
                        print(f"[OK] {init_file}: Has content ({len(content)} chars)")
                    else:
                        print(f"[WARN] {init_file}: Empty file")
            except Exception as e:
                print(f"[FAIL] {init_file}: Error reading - {e}")
        else:
            print(f"[FAIL] {init_file}: Missing")

    # Test core framework imports (baseline)
    print("\nCORE FRAMEWORK IMPORTS")
    print("-" * 30)

    core_imports = [
        ("mcp_agent.app", "MCPApp"),
        ("mcp_agent.agents.agent", "Agent"),
        ("mcp_agent.workflows.llm.augmented_llm_openai", "OpenAIAugmentedLLM"),
        ("mcp_agent.config", None),
    ]

    core_success = 0
    for module, class_name in core_imports:
        if test_import(module, class_name):
            core_success += 1

    print(
        f"Core framework success rate: {core_success}/{len(core_imports)} ({core_success / len(core_imports) * 100:.1f}%)"
    )

    # Test autonomous module imports
    print("\nAUTONOMOUS MODULE IMPORTS")
    print("-" * 30)

    autonomous_imports = [
        ("mcp_agent.autonomous.autonomous_orchestrator", "AutonomousOrchestrator"),
        ("mcp_agent.autonomous.dynamic_agent_factory", "DynamicAgentFactory"),
        ("mcp_agent.autonomous.task_analyzer", "TaskAnalyzer"),
        ("mcp_agent.autonomous.tool_discovery", None),
        ("mcp_agent.autonomous.decision_engine", "AutonomousDecisionEngine"),
        ("mcp_agent.autonomous.meta_coordinator", "MetaCoordinator"),
        ("mcp_agent.autonomous.github_project_manager", None),
        ("mcp_agent.autonomous.mcp_installer", None),
    ]

    autonomous_success = 0
    for module, class_name in autonomous_imports:
        if test_import(module, class_name):
            autonomous_success += 1

    print(
        f"Autonomous module success rate: {autonomous_success}/{len(autonomous_imports)} ({autonomous_success / len(autonomous_imports) * 100:.1f}%)"
    )

    # Test capabilities module imports
    print("\nCAPABILITIES MODULE IMPORTS")
    print("-" * 30)

    capabilities_imports = [
        ("mcp_agent.capabilities.capability_mapper", "CapabilityMapper"),
    ]

    capabilities_success = 0
    for module, class_name in capabilities_imports:
        if test_import(module, class_name):
            capabilities_success += 1

    print(
        f"Capabilities module success rate: {capabilities_success}/{len(capabilities_imports)} ({capabilities_success / len(capabilities_imports) * 100:.1f}%)"
    )

    # Summary and recommendations
    print("\nDIAGNOSTIC SUMMARY")
    print("=" * 30)

    total_tests = (
        len(core_imports) + len(autonomous_imports) + len(capabilities_imports)
    )
    total_success = core_success + autonomous_success + capabilities_success
    overall_rate = total_success / total_tests * 100

    print(f"Overall success rate: {total_success}/{total_tests} ({overall_rate:.1f}%)")

    if structure_ok:
        print("[OK] Project structure: OK")
    else:
        print("[FAIL] Project structure: Issues found")

    print("\nRECOMMENDATIONS")
    print("-" * 20)

    if overall_rate < 100:
        print("1. Fix missing imports in __init__.py files")
        print("2. Check for missing dependencies in pyproject.toml")
        print("3. Verify Python path configuration")
        print("4. Review module interdependencies")

    if autonomous_success < len(autonomous_imports):
        print("5. Focus on autonomous module issues first")
        print("6. Check for circular imports in autonomous modules")
        print("7. Validate autonomous module dependencies")

    if not structure_ok:
        print("8. Restore missing files from repository")
        print("9. Check git status for uncommitted changes")

    print(f"\nNext step: Focus on modules with 0% success rate")

    return overall_rate == 100


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
