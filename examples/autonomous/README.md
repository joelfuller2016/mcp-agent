# Autonomous Workflow Examples

This directory contains comprehensive examples demonstrating the autonomous capabilities of MCP-Agent.

## 🤖 What is Autonomous MCP-Agent?

The autonomous capabilities enable MCP-Agent to:
- **Automatically analyze tasks** and determine optimal execution strategies
- **Dynamically discover and install** required MCP servers
- **Create specialized agents** on-demand based on task requirements
- **Select workflow patterns** (Direct, Parallel, Router, Orchestrator, Swarm, etc.)
- **Self-optimize performance** based on execution history
- **Handle complex multi-step tasks** without manual configuration

## 📁 Examples Overview

### 1. `basic_autonomous_workflow.py`
**Difficulty:** Beginner  
**Purpose:** Introduction to autonomous execution

Demonstrates:
- Basic autonomous task execution
- Task analysis and strategy selection
- Execution pattern selection
- Performance tracking

```bash
# Run in container
docker run --rm mcp-agent uv run python /app/examples/autonomous/basic_autonomous_workflow.py

# Run locally
cd examples/autonomous
python basic_autonomous_workflow.py
```

### 2. `advanced_autonomous_workflow.py`
**Difficulty:** Intermediate  
**Purpose:** Complex orchestration and meta-coordination

Demonstrates:
- Meta-coordinator usage
- Complex multi-step task execution
- Capability gap analysis
- Performance optimization
- Multiple workflow patterns

```bash
# Run in container
docker run --rm mcp-agent uv run python /app/examples/autonomous/advanced_autonomous_workflow.py

# Run locally  
cd examples/autonomous
python advanced_autonomous_workflow.py
```

### 3. `docker_autonomous_workflow.py`
**Difficulty:** Intermediate  
**Purpose:** Containerized autonomous execution

Demonstrates:
- Docker environment analysis
- Container-specific task execution
- Volume and configuration validation
- Docker deployment reporting

```bash
# Run in container (recommended)
docker run --rm mcp-agent uv run python /app/examples/autonomous/docker_autonomous_workflow.py

# Run with Docker Compose
docker-compose run mcp-agent uv run python /app/examples/autonomous/docker_autonomous_workflow.py
```

## 🚀 Quick Start

### Prerequisites

1. **API Keys**: Set up your LLM provider API keys
   ```bash
   export OPENAI_API_KEY="your-key-here"
   export ANTHROPIC_API_KEY="your-key-here"
   ```

2. **Docker** (for containerized examples):
   ```bash
   docker build -t mcp-agent .
   ```

### Running Examples

#### Option 1: Docker (Recommended)
```bash
# Basic example
docker run --rm \
  -e OPENAI_API_KEY="$OPENAI_API_KEY" \
  mcp-agent \
  uv run python /app/examples/autonomous/basic_autonomous_workflow.py

# Advanced example with volume mounting
docker run --rm \
  -v $(pwd)/logs:/app/logs \
  -e OPENAI_API_KEY="$OPENAI_API_KEY" \
  mcp-agent \
  uv run python /app/examples/autonomous/advanced_autonomous_workflow.py
```

#### Option 2: Docker Compose
```bash
# Set up environment
cp .env.example .env
# Edit .env with your API keys

# Run basic example
docker-compose run mcp-agent uv run python /app/examples/autonomous/basic_autonomous_workflow.py

# Run all examples
docker-compose run mcp-agent bash -c "
  python /app/examples/autonomous/basic_autonomous_workflow.py &&
  python /app/examples/autonomous/advanced_autonomous_workflow.py &&
  python /app/examples/autonomous/docker_autonomous_workflow.py
"
```

#### Option 3: Local Development
```bash
# Set up environment
uv sync
export PYTHONPATH=$(pwd)/src

# Run examples
cd examples/autonomous
python basic_autonomous_workflow.py
python advanced_autonomous_workflow.py
```

## 🔧 Configuration

### Autonomous Configuration

The examples use configuration from `/app/config/autonomous.yaml`:

```yaml
autonomous:
  enabled: true
  max_agents: 5
  max_execution_time: 300
  default_llm_provider: openai
  enable_fallbacks: true
  log_decisions: true
  require_human_approval: false

tool_discovery:
  auto_discovery: true
  discovery_interval: 300
  max_concurrent_discoveries: 5
  enable_dynamic_installation: true

performance:
  enable_caching: true
  cache_ttl: 3600
  enable_parallel_discovery: true
  metrics_retention_days: 30
```

### Environment Variables

Key environment variables for autonomous operation:

- `MCP_AUTONOMOUS_MODE=true` - Enables autonomous features
- `MCP_LOG_LEVEL=info` - Controls logging verbosity
- `MCP_AUTONOMOUS_CONFIG_PATH` - Path to autonomous config file
- `OPENAI_API_KEY` - OpenAI API key for LLM operations
- `ANTHROPIC_API_KEY` - Anthropic API key for Claude models

## 📊 Understanding the Output

### Task Analysis
```
📋 Strategy: orchestrator
🧠 Complexity: complex
👥 Suggested agents: 3
```

### Execution Results
```
✅ Task completed successfully!
📊 Pattern used: parallel
⏱️ Execution time: 2.34s
🛠️ Agents used: 2
📝 Result: Generated comprehensive analysis...
```

### Performance Metrics
```
📈 Overall Performance:
   • Total executions: 5
   • Success rate: 100.0%
   • Average execution time: 1.8s
   • Most used pattern: orchestrator (3 times)
```

## 🎯 Example Use Cases

### Business Intelligence
```python
# Autonomous data analysis
task = "Analyze sales data from Q4 and generate insights report"
result = await orchestrator.execute_autonomous_task(task)
```

### DevOps Automation
```python
# Autonomous infrastructure assessment
task = "Analyze server logs, identify issues, and suggest optimizations"
result = await orchestrator.execute_autonomous_task(task)
```

### Content Generation
```python
# Autonomous content creation
task = "Research AI trends and write a technical blog post"
result = await orchestrator.execute_autonomous_task(task)
```

### Project Management
```python
# Autonomous project analysis
task = "Analyze project status, identify risks, and create action plan"
result = await orchestrator.execute_autonomous_task(task)
```

## 🧠 Key Concepts

### Autonomous Orchestrator
The main entry point that coordinates all autonomous capabilities:
- Task analysis
- Tool discovery
- Agent creation
- Workflow execution
- Performance tracking

### Meta-Coordinator
Higher-level orchestration for complex multi-step tasks:
- Advanced planning
- Resource optimization
- Capability gap analysis
- Performance tuning

### Dynamic Agent Factory
Creates specialized agents based on task requirements:
- Capability mapping
- Agent specialization
- Resource allocation
- Performance optimization

### Workflow Patterns
Autonomous selection from multiple execution patterns:
- **Direct**: Single agent execution
- **Parallel**: Fan-out/fan-in with multiple agents
- **Router**: Route to best-suited agent
- **Orchestrator**: Complex planning and coordination
- **Swarm**: Multi-agent collaboration
- **Evaluator-Optimizer**: Iterative refinement

## 🔍 Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   # Ensure PYTHONPATH is set
   export PYTHONPATH=/app/src
   ```

2. **API Key Issues**
   ```bash
   # Check environment variables
   echo $OPENAI_API_KEY
   echo $ANTHROPIC_API_KEY
   ```

3. **Docker Permission Issues**
   ```bash
   # Use proper volume mounting
   docker run --rm -v $(pwd)/logs:/app/logs mcp-agent
   ```

4. **Configuration Loading**
   ```bash
   # Verify config file exists
   ls -la /app/config/autonomous.yaml
   ```

### Debug Mode

Enable debug logging for detailed output:
```bash
export MCP_LOG_LEVEL=debug
```

## 📚 Next Steps

1. **Explore the code**: Review the autonomous components in `src/mcp_agent/autonomous/`
2. **Customize configuration**: Modify `config/autonomous.yaml` for your needs
3. **Create custom examples**: Build your own autonomous workflows
4. **Contribute**: Add new workflow patterns or capabilities

## 🤝 Contributing

To contribute new autonomous examples:

1. Create your example in this directory
2. Follow the naming convention: `{purpose}_autonomous_workflow.py`
3. Include comprehensive documentation
4. Add proper error handling and logging
5. Test in both Docker and local environments

For more information, see the main [CONTRIBUTING.md](../../CONTRIBUTING.md) file.
