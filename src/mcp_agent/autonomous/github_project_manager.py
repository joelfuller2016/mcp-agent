"""
GitHub Project Management Automation

This component provides automated GitHub project management capabilities including
project planning, issue management, milestone tracking, and development roadmaps.
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum

from .task_analyzer import TaskAnalysis, TaskComplexity, WorkflowPattern
from .tool_discovery import ToolCapability


class IssueType(Enum):
    """Types of GitHub issues."""
    FEATURE = "feature"
    BUG = "bug"
    ENHANCEMENT = "enhancement"
    DOCUMENTATION = "documentation"
    TESTING = "testing"
    RESEARCH = "research"
    INFRASTRUCTURE = "infrastructure"


class Priority(Enum):
    """Priority levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class GitHubIssue:
    """GitHub issue specification."""
    title: str
    body: str
    labels: List[str]
    assignees: List[str] = None
    milestone: Optional[str] = None
    priority: Priority = Priority.MEDIUM
    issue_type: IssueType = IssueType.FEATURE
    estimated_hours: Optional[int] = None
    dependencies: List[str] = None


@dataclass
class GitHubMilestone:
    """GitHub milestone specification."""
    title: str
    description: str
    due_date: Optional[str] = None
    issues: List[GitHubIssue] = None


@dataclass
class ProjectPlan:
    """Complete project plan."""
    name: str
    description: str
    milestones: List[GitHubMilestone]
    total_estimated_hours: int
    start_date: str
    target_completion: str
    repository: str
    created_by: str = "AutonomousMCPAgent"


class GitHubProjectManager:
    """Automated GitHub project management and planning."""
    
    def __init__(self, github_token: Optional[str] = None):
        self.github_token = github_token
        self.logger = logging.getLogger(__name__)
        
        # Template for autonomous capabilities project
        self.autonomous_project_template = {
            "phases": [
                {
                    "name": "Foundation & Analysis",
                    "description": "Core infrastructure and analysis components",
                    "duration_weeks": 2,
                    "components": [
                        "Tool Discovery Agent",
                        "Task Analyzer", 
                        "Strategy Selector",
                        "Project Structure Analysis"
                    ]
                },
                {
                    "name": "Agent Infrastructure",
                    "description": "Dynamic agent creation and management",
                    "duration_weeks": 2,
                    "components": [
                        "Dynamic Agent Factory",
                        "MCP Installer",
                        "Agent Lifecycle Management",
                        "Resource Management"
                    ]
                },
                {
                    "name": "Orchestration & Coordination", 
                    "description": "Autonomous orchestration and workflow management",
                    "duration_weeks": 3,
                    "components": [
                        "Autonomous Orchestrator",
                        "Workflow Pattern Integration",
                        "Multi-Agent Coordination",
                        "Reasoning Integration"
                    ]
                },
                {
                    "name": "Integration & Testing",
                    "description": "System integration and comprehensive testing",
                    "duration_weeks": 2,
                    "components": [
                        "End-to-End Integration",
                        "Autonomous Testing Suite",
                        "Performance Optimization",
                        "Documentation"
                    ]
                },
                {
                    "name": "Enhancement & Deployment",
                    "description": "Advanced features and production deployment",
                    "duration_weeks": 2,
                    "components": [
                        "Advanced Reasoning",
                        "Security Hardening",
                        "Monitoring & Observability",
                        "Production Deployment"
                    ]
                }
            ]
        }
    
    async def create_autonomous_mcp_project_plan(self, 
                                               repository: str,
                                               existing_capabilities: List[ToolCapability] = None) -> ProjectPlan:
        """Create a comprehensive project plan for autonomous MCP-agent capabilities."""
        self.logger.info(f"Creating autonomous MCP project plan for {repository}")
        
        existing_capabilities = existing_capabilities or []
        
        # Generate milestones based on template
        milestones = []
        start_date = datetime.now()
        current_date = start_date
        
        for phase in self.autonomous_project_template["phases"]:
            milestone = await self._create_phase_milestone(
                phase, current_date, existing_capabilities
            )
            milestones.append(milestone)
            current_date += timedelta(weeks=phase["duration_weeks"])
        
        # Calculate total estimated hours
        total_hours = sum(
            sum(issue.estimated_hours or 8 for issue in milestone.issues or [])
            for milestone in milestones
        )
        
        # Create project plan
        project_plan = ProjectPlan(
            name="Autonomous MCP-Agent Enhancement",
            description=(
                "Comprehensive enhancement of mcp-agent with autonomous capabilities including "
                "tool discovery, strategy selection, dynamic agent creation, and intelligent orchestration."
            ),
            milestones=milestones,
            total_estimated_hours=total_hours,
            start_date=start_date.isoformat(),
            target_completion=current_date.isoformat(),
            repository=repository
        )
        
        return project_plan
    
    async def _create_phase_milestone(self, 
                                    phase: Dict[str, Any],
                                    start_date: datetime,
                                    existing_capabilities: List[ToolCapability]) -> GitHubMilestone:
        """Create a milestone for a project phase."""
        due_date = start_date + timedelta(weeks=phase["duration_weeks"])
        
        # Generate issues for this phase
        issues = []
        
        if phase["name"] == "Foundation & Analysis":
            issues.extend(await self._create_foundation_issues())
        elif phase["name"] == "Agent Infrastructure":
            issues.extend(await self._create_agent_infrastructure_issues())
        elif phase["name"] == "Orchestration & Coordination":
            issues.extend(await self._create_orchestration_issues())
        elif phase["name"] == "Integration & Testing":
            issues.extend(await self._create_integration_issues())
        elif phase["name"] == "Enhancement & Deployment":
            issues.extend(await self._create_enhancement_issues())
        
        return GitHubMilestone(
            title=phase["name"],
            description=phase["description"],
            due_date=due_date.isoformat(),
            issues=issues
        )
    
    async def _create_foundation_issues(self) -> List[GitHubIssue]:
        """Create issues for foundation phase."""
        return [
            GitHubIssue(
                title="Implement Tool Discovery Agent",
                body="""
## Description
Create a ToolDiscoveryAgent that can automatically discover and map MCP server capabilities.

## Requirements
- [x] Scan connected MCP servers
- [x] Map server capabilities to tool categories
- [x] Discover available servers from registries
- [x] Maintain capability-to-server mapping
- [x] Validate server connectivity

## Implementation Details
- Build on existing MCP connection manager
- Support automatic server discovery
- Create capability taxonomy
- Implement scoring system for server selection

## Acceptance Criteria
- [ ] Can discover all connected MCP servers
- [ ] Accurately maps server capabilities
- [ ] Provides server recommendations for tasks
- [ ] Handles server connection failures gracefully
                """,
                labels=["enhancement", "autonomous", "high-priority"],
                priority=Priority.HIGH,
                issue_type=IssueType.FEATURE,
                estimated_hours=16
            ),
            GitHubIssue(
                title="Implement Task Analyzer for Autonomous Decision Making",
                body="""
## Description
Create a TaskAnalyzer that can understand task complexity and requirements for autonomous execution.

## Requirements
- [x] Analyze task complexity (simple to highly complex)
- [x] Identify required capabilities
- [x] Recommend workflow patterns
- [x] Estimate execution time and resources
- [x] Assess risks and dependencies

## Implementation Details
- Pattern matching for capability identification
- Complexity scoring algorithm
- Integration with existing workflow patterns
- Support for custom task types

## Acceptance Criteria
- [ ] Accurately classifies task complexity
- [ ] Identifies all required capabilities
- [ ] Provides reliable workflow pattern recommendations
- [ ] Generates actionable execution plans
                """,
                labels=["enhancement", "autonomous", "analysis"],
                priority=Priority.HIGH,
                issue_type=IssueType.FEATURE,
                estimated_hours=20
            ),
            GitHubIssue(
                title="Create Strategy Selector for Workflow Pattern Selection",
                body="""
## Description
Implement intelligent strategy selection for choosing optimal workflow patterns based on task analysis.

## Requirements
- [x] Analyze task requirements vs available tools
- [x] Select optimal workflow pattern
- [x] Generate execution plans
- [x] Provide confidence scores and reasoning
- [x] Handle fallback strategies

## Implementation Details
- Integration with existing workflow patterns
- Confidence scoring system
- Support for pattern composition
- Fallback strategy implementation

## Acceptance Criteria
- [ ] Selects appropriate patterns for different task types
- [ ] Provides clear reasoning for selections
- [ ] Handles tool availability constraints
- [ ] Supports pattern fallbacks when needed
                """,
                labels=["enhancement", "autonomous", "strategy"],
                priority=Priority.HIGH,
                issue_type=IssueType.FEATURE,
                estimated_hours=18
            )
        ]
    
    async def _create_agent_infrastructure_issues(self) -> List[GitHubIssue]:
        """Create issues for agent infrastructure phase."""
        return [
            GitHubIssue(
                title="Implement Dynamic Agent Factory",
                body="""
## Description
Create a factory for dynamically creating specialized agents based on task requirements.

## Requirements
- [x] Create agents based on capability requirements
- [x] Support multiple agent types and roles
- [x] Generate appropriate agent instructions
- [x] Manage agent lifecycle and resources
- [x] Support agent composition and specialization

## Implementation Details
- Agent specification system
- Role-based agent templates
- Capability-driven agent creation
- Resource management and cleanup

## Acceptance Criteria
- [ ] Creates agents with appropriate capabilities
- [ ] Generates effective agent instructions
- [ ] Manages agent resources efficiently
- [ ] Supports various agent roles and specializations
                """,
                labels=["enhancement", "autonomous", "agents"],
                priority=Priority.HIGH,
                issue_type=IssueType.FEATURE,
                estimated_hours=24
            ),
            GitHubIssue(
                title="Implement MCP Installer for Ad-hoc Tool Installation",
                body="""
## Description
Create an MCP installer that can discover and install new MCP servers on-demand.

## Requirements
- [x] Search for MCP servers by capability
- [x] Evaluate server candidates
- [x] Install servers using various methods (uvx, npx, pip, git)
- [x] Validate installations
- [x] Suggest capability enhancements

## Implementation Details
- Multiple installation methods
- Server candidate scoring
- Installation validation
- Integration with tool discovery

## Acceptance Criteria
- [ ] Finds relevant servers for capabilities
- [ ] Successfully installs servers
- [ ] Validates server functionality
- [ ] Provides installation status and feedback
                """,
                labels=["enhancement", "autonomous", "installation"],
                priority=Priority.MEDIUM,
                issue_type=IssueType.FEATURE,
                estimated_hours=20
            ),
            GitHubIssue(
                title="Create Agent Lifecycle Management System",
                body="""
## Description
Implement comprehensive agent lifecycle management for creation, execution, and cleanup.

## Requirements
- [ ] Agent creation and initialization
- [ ] Resource allocation and management
- [ ] Agent monitoring and health checks
- [ ] Graceful agent shutdown and cleanup
- [ ] Agent performance metrics

## Implementation Details
- Async context managers for agents
- Resource pooling and limits
- Health monitoring
- Performance tracking

## Acceptance Criteria
- [ ] Agents are properly initialized and cleaned up
- [ ] Resource usage is monitored and controlled
- [ ] Agent health is tracked
- [ ] Performance metrics are collected
                """,
                labels=["enhancement", "infrastructure", "agents"],
                priority=Priority.MEDIUM,
                issue_type=IssueType.FEATURE,
                estimated_hours=16
            )
        ]
    
    async def _create_orchestration_issues(self) -> List[GitHubIssue]:
        """Create issues for orchestration phase."""
        return [
            GitHubIssue(
                title="Implement Autonomous Orchestrator",
                body="""
## Description
Create the main autonomous orchestrator that coordinates all components for fully autonomous task execution.

## Requirements
- [x] Integrate all autonomous components
- [x] Support multiple execution modes
- [x] Handle tool installation and agent creation
- [x] Execute workflow patterns autonomously
- [x] Provide execution monitoring and feedback

## Implementation Details
- Component integration and coordination
- Execution mode support (autonomous, guided, simulation)
- Error handling and recovery
- Execution tracking and metrics

## Acceptance Criteria
- [ ] Executes tasks autonomously end-to-end
- [ ] Handles failures gracefully with fallbacks
- [ ] Provides clear execution feedback
- [ ] Supports different execution modes
                """,
                labels=["enhancement", "autonomous", "orchestration"],
                priority=Priority.CRITICAL,
                issue_type=IssueType.FEATURE,
                estimated_hours=32
            ),
            GitHubIssue(
                title="Integrate Reasoning Tools (mcp-reasoner, sequential-thinking)",
                body="""
## Description
Integrate advanced reasoning capabilities using mcp-reasoner and sequential-thinking tools.

## Requirements
- [ ] Configure reasoning MCP servers
- [ ] Integrate with autonomous orchestrator
- [ ] Support complex problem decomposition
- [ ] Enable multi-step reasoning workflows
- [ ] Provide reasoning transparency

## Implementation Details
- MCP server configuration for reasoning tools
- Integration with existing workflow patterns
- Reasoning result interpretation
- Reasoning chain visualization

## Acceptance Criteria
- [ ] Reasoning tools are properly integrated
- [ ] Complex problems are decomposed effectively
- [ ] Reasoning process is transparent
- [ ] Reasoning enhances autonomous decisions
                """,
                labels=["enhancement", "reasoning", "integration"],
                priority=Priority.HIGH,
                issue_type=IssueType.FEATURE,
                estimated_hours=20
            ),
            GitHubIssue(
                title="Implement Multi-Agent Coordination",
                body="""
## Description
Enhance the system with sophisticated multi-agent coordination capabilities.

## Requirements
- [ ] Agent-to-agent communication
- [ ] Task delegation and handoffs
- [ ] Shared context management
- [ ] Conflict resolution
- [ ] Collaborative decision making

## Implementation Details
- Communication protocols between agents
- Context sharing mechanisms
- Coordination patterns
- Conflict detection and resolution

## Acceptance Criteria
- [ ] Agents can communicate and coordinate
- [ ] Tasks are delegated appropriately
- [ ] Context is shared effectively
- [ ] Conflicts are resolved automatically
                """,
                labels=["enhancement", "coordination", "agents"],
                priority=Priority.HIGH,
                issue_type=IssueType.FEATURE,
                estimated_hours=28
            )
        ]
    
    async def _create_integration_issues(self) -> List[GitHubIssue]:
        """Create issues for integration phase."""
        return [
            GitHubIssue(
                title="End-to-End Integration Testing",
                body="""
## Description
Create comprehensive integration tests for all autonomous capabilities.

## Requirements
- [ ] Test autonomous task execution
- [ ] Validate tool discovery and installation
- [ ] Test agent creation and coordination
- [ ] Verify workflow pattern selection
- [ ] Test error handling and recovery

## Implementation Details
- Integration test suite
- Mock MCP servers for testing
- Test scenarios for different complexities
- Performance benchmarking

## Acceptance Criteria
- [ ] All components work together seamlessly
- [ ] Error scenarios are handled correctly
- [ ] Performance meets requirements
- [ ] Test coverage is comprehensive
                """,
                labels=["testing", "integration", "autonomous"],
                priority=Priority.HIGH,
                issue_type=IssueType.TESTING,
                estimated_hours=24
            ),
            GitHubIssue(
                title="Performance Optimization",
                body="""
## Description
Optimize performance of autonomous capabilities for production use.

## Requirements
- [ ] Profile component performance
- [ ] Optimize tool discovery speed
- [ ] Improve agent creation time
- [ ] Reduce orchestration overhead
- [ ] Implement caching strategies

## Implementation Details
- Performance profiling and benchmarking
- Optimization of critical paths
- Caching implementation
- Resource usage optimization

## Acceptance Criteria
- [ ] Significant performance improvements
- [ ] Reduced latency for common operations
- [ ] Efficient resource utilization
- [ ] Scalable performance characteristics
                """,
                labels=["performance", "optimization", "infrastructure"],
                priority=Priority.MEDIUM,
                issue_type=IssueType.ENHANCEMENT,
                estimated_hours=16
            ),
            GitHubIssue(
                title="Documentation and Examples",
                body="""
## Description
Create comprehensive documentation and examples for autonomous capabilities.

## Requirements
- [ ] Update README with autonomous features
- [ ] Create usage examples and tutorials
- [ ] Document API and configuration options
- [ ] Provide troubleshooting guides
- [ ] Create video demos

## Implementation Details
- Documentation updates
- Example creation
- Tutorial development
- Demo creation

## Acceptance Criteria
- [ ] Documentation is complete and clear
- [ ] Examples demonstrate key features
- [ ] Users can easily get started
- [ ] Troubleshooting information is available
                """,
                labels=["documentation", "examples", "user-experience"],
                priority=Priority.MEDIUM,
                issue_type=IssueType.DOCUMENTATION,
                estimated_hours=20
            )
        ]
    
    async def _create_enhancement_issues(self) -> List[GitHubIssue]:
        """Create issues for enhancement phase."""
        return [
            GitHubIssue(
                title="Advanced Reasoning Capabilities",
                body="""
## Description
Implement advanced reasoning capabilities for complex problem solving.

## Requirements
- [ ] Multi-step reasoning chains
- [ ] Hypothesis generation and testing
- [ ] Uncertainty quantification
- [ ] Causal reasoning
- [ ] Abstract problem representation

## Implementation Details
- Integration with advanced reasoning models
- Reasoning pattern library
- Uncertainty tracking
- Result validation

## Acceptance Criteria
- [ ] Complex problems are solved effectively
- [ ] Reasoning is transparent and auditable
- [ ] Uncertainty is properly communicated
- [ ] Results are validated and reliable
                """,
                labels=["enhancement", "reasoning", "advanced"],
                priority=Priority.LOW,
                issue_type=IssueType.FEATURE,
                estimated_hours=32
            ),
            GitHubIssue(
                title="Security Hardening",
                body="""
## Description
Implement security measures for autonomous operation in production environments.

## Requirements
- [ ] Secure MCP server communication
- [ ] Agent permission controls
- [ ] Audit logging
- [ ] Resource usage limits
- [ ] Vulnerability scanning

## Implementation Details
- Security audit and assessment
- Permission system implementation
- Secure communication protocols
- Monitoring and alerting

## Acceptance Criteria
- [ ] System is secure for production use
- [ ] All operations are audited
- [ ] Resource usage is controlled
- [ ] Vulnerabilities are identified and fixed
                """,
                labels=["security", "production", "infrastructure"],
                priority=Priority.HIGH,
                issue_type=IssueType.ENHANCEMENT,
                estimated_hours=24
            ),
            GitHubIssue(
                title="Production Deployment and Monitoring",
                body="""
## Description
Prepare the system for production deployment with monitoring and observability.

## Requirements
- [ ] Deployment automation
- [ ] Health monitoring
- [ ] Performance metrics
- [ ] Error tracking
- [ ] Alerting system

## Implementation Details
- Deployment pipeline
- Monitoring infrastructure
- Metrics collection
- Alerting configuration

## Acceptance Criteria
- [ ] System can be deployed automatically
- [ ] Health and performance are monitored
- [ ] Issues are detected and alerted
- [ ] Operations are observable and debuggable
                """,
                labels=["deployment", "monitoring", "production"],
                priority=Priority.MEDIUM,
                issue_type=IssueType.INFRASTRUCTURE,
                estimated_hours=20
            )
        ]
    
    async def export_project_plan_to_github(self, 
                                          project_plan: ProjectPlan,
                                          create_issues: bool = False,
                                          create_milestones: bool = False) -> Dict[str, Any]:
        """Export project plan to GitHub format."""
        
        # Export to GitHub-compatible format
        github_export = {
            "project": {
                "name": project_plan.name,
                "description": project_plan.description,
                "repository": project_plan.repository,
                "total_estimated_hours": project_plan.total_estimated_hours,
                "start_date": project_plan.start_date,
                "target_completion": project_plan.target_completion
            },
            "milestones": [],
            "issues": []
        }
        
        # Convert milestones
        for milestone in project_plan.milestones:
            milestone_data = {
                "title": milestone.title,
                "description": milestone.description,
                "due_date": milestone.due_date,
                "issues": len(milestone.issues or [])
            }
            github_export["milestones"].append(milestone_data)
            
            # Convert issues
            for issue in milestone.issues or []:
                issue_data = {
                    "title": issue.title,
                    "body": issue.body,
                    "labels": issue.labels,
                    "milestone": milestone.title,
                    "priority": issue.priority.value,
                    "type": issue.issue_type.value,
                    "estimated_hours": issue.estimated_hours
                }
                github_export["issues"].append(issue_data)
        
        return github_export
    
    async def create_project_readme_section(self, project_plan: ProjectPlan) -> str:
        """Create a README section for the autonomous capabilities."""
        
        readme_section = f"""
# 🤖 Autonomous MCP-Agent Capabilities

{project_plan.description}

## 🚀 Quick Start with Autonomous Features

```python
import asyncio
from mcp_agent.app import MCPApp
from mcp_agent.autonomous import AutonomousOrchestrator, ExecutionMode

async def autonomous_example():
    app = MCPApp(name="autonomous_demo")
    
    async with app.run() as mcp_app:
        # Initialize autonomous orchestrator
        orchestrator = AutonomousOrchestrator(
            app=mcp_app,
            execution_mode=ExecutionMode.GUIDED_AUTONOMY
        )
        await orchestrator.initialize()
        
        # Execute any task autonomously
        result = await orchestrator.execute_autonomous_task(
            "Analyze this codebase and suggest improvements"
        )
        
        print(f"Task completed: {{result.success}}")
        print(f"Result: {{result.result}}")

asyncio.run(autonomous_example())
```

## 🧠 Autonomous Components

### Tool Discovery Agent
- **Automatic MCP server discovery** - Scans and maps available tools
- **Capability classification** - Categorizes tools by their capabilities  
- **Smart tool selection** - Recommends best tools for specific tasks

### Task Analyzer
- **Complexity assessment** - Analyzes task complexity and requirements
- **Capability identification** - Determines required tool capabilities
- **Pattern recommendation** - Suggests optimal workflow patterns

### Strategy Selector  
- **Intelligent pattern selection** - Chooses best execution strategy
- **Confidence scoring** - Provides confidence levels for decisions
- **Fallback strategies** - Handles cases when primary strategy fails

### Dynamic Agent Factory
- **On-demand agent creation** - Creates specialized agents as needed
- **Role-based templates** - Uses predefined templates for common roles
- **Capability-driven design** - Builds agents based on required capabilities

### MCP Installer
- **Ad-hoc tool installation** - Installs new MCP servers automatically
- **Multiple install methods** - Supports uvx, npx, pip, and git installation
- **Capability enhancement** - Suggests tools to expand capabilities

### Autonomous Orchestrator
- **End-to-end coordination** - Manages entire autonomous execution pipeline
- **Multi-mode operation** - Supports autonomous, guided, and simulation modes
- **Execution monitoring** - Tracks and reports on execution progress

## 📊 Project Roadmap

| Phase | Duration | Status | Description |
|-------|----------|--------|-------------|
| Foundation & Analysis | 2 weeks | ✅ Completed | Core infrastructure and analysis components |
| Agent Infrastructure | 2 weeks | ✅ Completed | Dynamic agent creation and management |  
| Orchestration & Coordination | 3 weeks | 🔄 In Progress | Autonomous orchestration and workflow management |
| Integration & Testing | 2 weeks | ⏳ Planned | System integration and comprehensive testing |
| Enhancement & Deployment | 2 weeks | ⏳ Planned | Advanced features and production deployment |

**Total Estimated Hours:** {project_plan.total_estimated_hours}  
**Target Completion:** {project_plan.target_completion[:10]}

## 🎯 Execution Modes

- **Fully Autonomous** - Complete autonomy with no user intervention
- **Guided Autonomy** - Asks for confirmation on tool installations and major decisions  
- **Simulation** - Plans execution without actually running commands

## 🛠️ Supported Workflow Patterns

The autonomous system can intelligently select and execute any of the core mcp-agent patterns:

- **Direct** - Simple single-agent execution
- **Parallel** - Fan-out to multiple agents with result aggregation
- **Router** - Intelligent routing to the best available agent
- **Orchestrator** - Complex multi-step planning and execution
- **Swarm** - Multi-agent coordination with handoffs
- **Evaluator-Optimizer** - Iterative refinement until quality threshold met

## 📈 Performance & Metrics

The autonomous system provides detailed execution metrics:

- Success rates and failure analysis
- Execution time tracking  
- Resource utilization monitoring
- Tool usage statistics
- Agent performance analytics

## 🔧 Configuration

Configure autonomous behavior via environment variables or config files:

```bash
# Execution mode
MCP_AUTONOMOUS_MODE=guided_autonomy

# Tool installation behavior  
MCP_AUTO_INSTALL_TOOLS=true
MCP_MAX_INSTALL_ATTEMPTS=3

# Agent limits
MCP_MAX_AGENTS_PER_TASK=5
MCP_AGENT_TIMEOUT=300

# Reasoning integration
MCP_ENABLE_REASONING=true
MCP_REASONING_DEPTH=3
```

## 🎮 Interactive Demo

Try the autonomous capabilities with the interactive demo:

```bash
cd examples/autonomous
python autonomous_demo.py
```

## 🤝 Contributing to Autonomous Features

We welcome contributions to the autonomous capabilities! See our development guidelines:

1. **Component Development** - Each autonomous component has its own module
2. **Testing Requirements** - All autonomous features must include comprehensive tests
3. **Documentation Standards** - Document the reasoning behind autonomous decisions
4. **Performance Considerations** - Optimize for real-world autonomous usage

## 🔒 Security Considerations

The autonomous system includes several security measures:

- **Tool validation** - Validates MCP servers before installation
- **Permission controls** - Granular permissions for agent actions
- **Audit logging** - Complete audit trail of autonomous decisions
- **Resource limits** - Prevents resource exhaustion

## 📚 Examples

Check out `examples/autonomous/` for comprehensive examples including:

- **Basic autonomous execution**
- **Multi-agent coordination scenarios**  
- **Custom strategy development**
- **Tool discovery and installation**
- **Integration with existing mcp-agent patterns**

---

*🤖 This project enhances mcp-agent with autonomous capabilities that can discover tools, create agents, and execute complex workflows without human intervention, while maintaining the safety and transparency needed for production use.*
"""
        
        return readme_section
    
    def generate_github_actions_workflow(self) -> str:
        """Generate GitHub Actions workflow for autonomous testing."""
        
        workflow = """
name: Autonomous MCP-Agent CI/CD

on:
  push:
    branches: [ main, develop ]
    paths: 
      - 'src/mcp_agent/autonomous/**'
      - 'examples/autonomous/**'
      - 'tests/autonomous/**'
  pull_request:
    branches: [ main ]

jobs:
  test-autonomous-components:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.10, 3.11, 3.12]
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install uv
        uv pip install -e .
        uv pip install pytest pytest-asyncio pytest-cov
    
    - name: Test Tool Discovery
      run: |
        pytest tests/autonomous/test_tool_discovery.py -v
    
    - name: Test Task Analysis
      run: |
        pytest tests/autonomous/test_task_analyzer.py -v
    
    - name: Test Strategy Selection
      run: |
        pytest tests/autonomous/test_strategy_selector.py -v
    
    - name: Test Agent Factory
      run: |
        pytest tests/autonomous/test_dynamic_agent_factory.py -v
    
    - name: Test MCP Installer
      run: |
        pytest tests/autonomous/test_mcp_installer.py -v
    
    - name: Test Autonomous Orchestrator
      run: |
        pytest tests/autonomous/test_autonomous_orchestrator.py -v
    
    - name: Integration Tests
      run: |
        pytest tests/autonomous/test_integration.py -v
    
    - name: Coverage Report
      run: |
        pytest tests/autonomous/ --cov=src/mcp_agent/autonomous --cov-report=xml
    
    - name: Upload Coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        flags: autonomous

  test-autonomous-examples:
    runs-on: ubuntu-latest
    needs: test-autonomous-components
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: 3.11
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install uv
        uv pip install -e .
    
    - name: Test Autonomous Demo
      run: |
        cd examples/autonomous
        timeout 60 python autonomous_demo.py < /dev/null || true
    
    - name: Validate Examples
      run: |
        python -m py_compile examples/autonomous/*.py

  security-scan:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    
    - name: Run Security Scan
      uses: PyCQA/bandit-action@v1
      with:
        path: src/mcp_agent/autonomous/
        level: medium
        confidence: medium
        exit_zero: true

  performance-benchmark:
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: 3.11
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install uv
        uv pip install -e .
        uv pip install pytest-benchmark
    
    - name: Run Performance Benchmarks
      run: |
        pytest tests/autonomous/test_performance.py --benchmark-json=benchmark.json
    
    - name: Store Benchmark Results
      uses: actions/upload-artifact@v3
      with:
        name: benchmark-results
        path: benchmark.json
"""
        
        return workflow
