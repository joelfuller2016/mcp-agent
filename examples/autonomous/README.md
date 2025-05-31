# Autonomous MCP-Agent Example

This example demonstrates the autonomous capabilities of mcp-agent, where the system can automatically:

- **Discover and map available MCP tools**
- **Analyze task complexity and requirements** 
- **Select optimal execution strategies**
- **Create specialized agents dynamically**
- **Execute tasks with minimal human intervention**

## Features Demonstrated

### 🤖 Autonomous Decision Making
- **Tool Discovery**: Automatically scans and maps available MCP servers
- **Task Analysis**: Understands task requirements and complexity 
- **Strategy Selection**: Chooses the best execution pattern (direct, parallel, orchestrator, swarm, etc.)
- **Agent Creation**: Dynamically creates specialized agents based on task needs

### 🎯 Execution Patterns
The autonomous system can choose from multiple execution patterns:

- **Direct**: Single agent, straightforward execution
- **Parallel**: Multiple agents working in parallel 
- **Router**: Intelligent routing to the best agent
- **Orchestrator**: Complex planning and coordination
- **Swarm**: Multi-agent collaboration with handoffs
- **Evaluator-Optimizer**: Iterative refinement

### 🛠️ Agent Specializations
Creates specialized agents automatically:

- **Researcher**: Information gathering and web research
- **Analyst**: Data analysis and pattern recognition  
- **Creator**: Content generation and writing
- **Developer**: Code development and Git operations
- **Automator**: Workflow automation and task management
- **Web Specialist**: Browser automation and web scraping
- **Reasoner**: Complex problem solving and logic
- **Coordinator**: Multi-agent orchestration

## Quick Start

1. **Install Dependencies**:
   ```bash
   cd examples/autonomous
   uv install
   ```

2. **Configure API Keys**:
   ```bash
   cp mcp_agent.secrets.yaml.example mcp_agent.secrets.yaml
   # Edit mcp_agent.secrets.yaml with your API keys
   ```

3. **Run the Demo**:
   ```bash
   uv run autonomous_demo.py
   ```

## Usage Examples

### Simple Autonomous Execution
```python
from mcp_agent.autonomous import execute_autonomous_task

# The system will automatically analyze the task and choose the best approach
result = await execute_autonomous_task(
    "Find and analyze all Python files in the src directory"
)

print(f"Success: {result.success}")
print(f"Pattern used: {result.execution_pattern}")
print(f"Result: {result.result}")
```

### Advanced Configuration
```python
from mcp_agent.autonomous import AutonomousOrchestrator, AutonomousConfig

config = AutonomousConfig(
    max_agents=5,
    prefer_simple_patterns=False,
    require_human_approval=False,
    default_llm_provider="anthropic"
)

orchestrator = AutonomousOrchestrator(config=config)
result = await orchestrator.execute_autonomous_task(
    "Create a comprehensive analysis of this codebase and suggest improvements"
)
```

### Task Analysis Without Execution
```python
# Get suggestions for how a task would be executed
suggestions = await orchestrator.get_execution_suggestions(
    "Research recent developments in Model Context Protocol"
)

print(f"Recommended pattern: {suggestions['strategy']['recommended_pattern']}")
print(f"Reasoning: {suggestions['strategy']['reasoning']}")
print(f"Agents needed: {suggestions['agents']['suggested_count']}")
```

## How It Works

### 1. Tool Discovery
The system scans your MCP configuration to understand available capabilities:

```python
tool_mapper = ToolCapabilityMapper()
await tool_mapper.discover_all_capabilities()

# Maps tools by category: development, analysis, web, file_system, etc.
capabilities = tool_mapper.get_capability_summary()
```

### 2. Task Analysis  
Analyzes natural language tasks to understand requirements:

```python
analyzer = TaskAnalyzer()
analysis = analyzer.analyze_task("Analyze my GitHub repositories")

# Results: task_type, complexity, required_capabilities, estimated_steps
```

### 3. Strategy Selection
Chooses optimal execution pattern based on task analysis:

```python
strategy_engine = StrategyDecisionEngine(tool_mapper)
decision = strategy_engine.decide_strategy(task_analysis)

# Results: recommended_pattern, confidence, reasoning, required_servers
```

### 4. Dynamic Agent Creation
Creates specialized agents based on requirements:

```python
agent_factory = DynamicAgentFactory(tool_mapper)
agents = agent_factory.create_agents_for_task(task_analysis)

# Creates: researcher, analyst, developer agents as needed
```

### 5. Autonomous Execution
Orchestrates the complete execution:

```python
orchestrator = AutonomousOrchestrator()
result = await orchestrator.execute_autonomous_task(task_description)

# Handles: initialization, execution, error handling, fallbacks
```

## Configuration Options

### MCP Servers
The autonomous system works with any MCP servers you have configured:

```yaml
mcp:
  servers:
    filesystem:
      command: "npx"
      args: ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/files"]
    
    fetch:
      command: "uvx" 
      args: ["mcp-server-fetch"]
    
    github:
      command: "uvx"
      args: ["mcp-server-github"]
```

### Autonomous Settings
```yaml
autonomous:
  max_agents: 5                    # Maximum agents to create
  max_execution_time: 300          # Timeout in seconds
  prefer_simple_patterns: false    # Prefer simple over complex patterns
  require_human_approval: false    # Require approval for complex tasks
  default_llm_provider: "openai"   # Default LLM provider
  enable_fallbacks: true           # Enable fallback strategies
  log_decisions: true              # Log decision-making process
```

## Advanced Features

### Execution History
```python
# View recent execution history
history = orchestrator.get_execution_history(limit=10)
for execution in history:
    print(f"{execution['task']} - {execution['pattern']} - {'✅' if execution['success'] else '❌'}")
```

### Capability Analysis
```python
# Analyze current system capabilities
capabilities = await orchestrator.analyze_capabilities()
print(f"Available servers: {capabilities['tool_capabilities']['available_servers']}")
print(f"Success rate: {capabilities['success_rate']:.2%}")
```

### Custom Agent Specializations
```python
# Create custom agent specialization
custom_agent = agent_factory.create_custom_agent(
    name="data_scientist",
    role="Data Science Specialist", 
    instruction="You excel at statistical analysis and machine learning tasks",
    capabilities=["data", "analysis", "reasoning"]
)
```

## Example Tasks

The autonomous system can handle various types of tasks:

### Information Retrieval
- "Find and summarize the main features of this project"
- "Search for recent news about AI agents and create a brief report"
- "Read all documentation files and identify missing sections"

### Code Analysis
- "Analyze the code structure and identify potential improvements"
- "Find all TODO comments and prioritize them"  
- "Review the test coverage and suggest additional tests"

### Project Management
- "Create a development roadmap for the next quarter"
- "Analyze GitHub issues and categorize them by priority"
- "Generate a project status report with key metrics"

### Research and Analysis
- "Research best practices for MCP server development"
- "Compare different AI agent frameworks and their features"
- "Analyze user feedback and identify common themes"

## Troubleshooting

### Common Issues

1. **No agents created**: Check that MCP servers are properly configured and accessible
2. **Execution timeouts**: Increase `max_execution_time` in configuration
3. **Pattern selection**: Set `prefer_simple_patterns: true` for simpler tasks
4. **API errors**: Verify API keys in `mcp_agent.secrets.yaml`

### Debug Mode
Enable detailed logging to see decision-making process:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

config = AutonomousConfig(log_decisions=True)
orchestrator = AutonomousOrchestrator(config=config)
```

### Manual Override
Override automatic decisions when needed:

```python
# Force specific execution pattern
from mcp_agent.workflows.parallel import ParallelLLM

agents = agent_factory.create_agents_for_task(task_analysis, max_agents=3)
parallel_llm = ParallelLLM(
    fan_in_agent=agents[0],
    fan_out_agents=agents[1:],
    llm_factory=OpenAIAugmentedLLM
)
result = await parallel_llm.generate_str(task_description)
```

## Contributing

The autonomous system is designed to be extensible:

- **Add new agent specializations** in `dynamic_agent_factory.py`
- **Implement new execution patterns** following existing pattern interfaces
- **Enhance task analysis** with better natural language understanding
- **Improve strategy selection** with more sophisticated scoring algorithms

See the main [CONTRIBUTING.md](../../CONTRIBUTING.md) for general contribution guidelines.
