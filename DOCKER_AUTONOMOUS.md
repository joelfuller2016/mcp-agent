# Enhanced Docker Guide for Autonomous MCP-Agent

This guide covers Docker deployment and usage specifically for the autonomous capabilities of MCP-Agent.

## 🤖 Autonomous Features in Docker

The enhanced Docker setup provides full support for:
- **Autonomous task orchestration**
- **Dynamic tool discovery and installation**
- **Self-configuring agent creation**
- **Performance optimization and caching**
- **Multi-pattern workflow execution**

## 🏗️ Docker Architecture

### Enhanced Multi-Stage Build

```dockerfile
# Base stage - common dependencies
FROM python:3.11-slim as base

# Development stage - includes dev tools
FROM base as development

# Production stage - minimal runtime
FROM base as production
```

### Container Features

✅ **Comprehensive MCP servers** (filesystem, fetch, git, sqlite)  
✅ **Autonomous configuration** pre-loaded  
✅ **Performance monitoring** and health checks  
✅ **Multi-environment** support (dev/test/prod)  
✅ **Volume persistence** for data and logs  
✅ **Security hardening** with non-root user  

## 🚀 Quick Start

### 1. Basic Autonomous Container

```bash
# Build enhanced image
docker build -t mcp-agent-autonomous .

# Run with autonomous features
docker run --rm \
  -e OPENAI_API_KEY="your-key" \
  -e MCP_AUTONOMOUS_MODE=true \
  mcp-agent-autonomous
```

### 2. Production Deployment

```bash
# Build production image
docker build -f Dockerfile.autonomous --target production -t mcp-agent-prod .

# Run production container
docker run -d \
  --name mcp-agent-production \
  -p 8001:8000 \
  -v mcp-data:/app/data \
  -v mcp-logs:/app/logs \
  -e OPENAI_API_KEY="your-key" \
  -e ANTHROPIC_API_KEY="your-key" \
  --restart unless-stopped \
  mcp-agent-prod
```

### 3. Development Environment

```bash
# Build development image
docker build -f Dockerfile.autonomous --target development -t mcp-agent-dev .

# Run with live reload
docker run -it \
  -v $(pwd)/src:/app/src \
  -v $(pwd)/examples:/app/examples \
  -v $(pwd)/config:/app/config \
  -e OPENAI_API_KEY="your-key" \
  -e MCP_LOG_LEVEL=debug \
  mcp-agent-dev
```

## 🔧 Docker Compose Configurations

### Standard Deployment

```bash
# Start main service
docker-compose up mcp-agent

# Run tests
docker-compose run mcp-agent-test

# View logs
docker-compose logs -f mcp-agent
```

### Production Profile

```bash
# Start production services
docker-compose --profile production up

# Scale production service
docker-compose --profile production up --scale mcp-agent-production=3
```

### Development Profile

```bash
# Start development environment
docker-compose --profile development up mcp-agent-dev

# Run with live reload
docker-compose --profile development run mcp-agent-dev bash
```

### Database Profile

```bash
# Start with database support
docker-compose --profile database up
```

## 📋 Environment Variables

### Autonomous Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_AUTONOMOUS_MODE` | `true` | Enables autonomous features |
| `MCP_LOG_LEVEL` | `info` | Logging level (debug/info/warn/error) |
| `MCP_AUTONOMOUS_CONFIG_PATH` | `/app/config/autonomous.yaml` | Config file path |
| `MCP_TEST_MODE` | `false` | Enables test mode |
| `MCP_DEV_MODE` | `false` | Enables development mode |

### API Keys

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Yes | OpenAI API key for GPT models |
| `ANTHROPIC_API_KEY` | Optional | Anthropic API key for Claude models |

### Performance Tuning

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_MAX_AGENTS` | `5` | Maximum concurrent agents |
| `MCP_EXECUTION_TIMEOUT` | `300` | Task execution timeout (seconds) |
| `MCP_CACHE_TTL` | `3600` | Cache time-to-live (seconds) |

## 🧪 Testing Autonomous Features

### Comprehensive Test Suite

```bash
# Run autonomous deployment test
docker run --rm mcp-agent uv run python /app/docker/test_autonomous_deployment.py

# Run specific autonomous tests
docker-compose run mcp-agent-test
```

### Test Output Example

```
🤖 Starting Comprehensive Autonomous Docker Test

1️⃣ Testing Basic MCP Functionality...
✅ Connected to 4 MCP tools
✅ File system operations working (15 items found)

2️⃣ Testing Autonomous Imports...
✅ All autonomous module imports successful

3️⃣ Testing Task Analysis...
   1. Read a file and summarize its contents...
      → Complexity: moderate
      → Pattern: direct
      → Steps: 3
      → Confidence: 0.85
✅ Task analysis working correctly

🎉 All autonomous Docker deployment tests passed!
   ✅ Autonomous capabilities: FULLY FUNCTIONAL
   ✅ Docker environment: OPTIMAL
   ✅ Ready for production deployment
```

## 📊 Health Monitoring

### Health Check Configuration

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.path.insert(0, '/app/src'); from mcp_agent.autonomous.task_analyzer import TaskAnalyzer; TaskAnalyzer().analyze_task('test')" || exit 1
```

### Monitoring Commands

```bash
# Check container health
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# View health check logs
docker inspect mcp-agent-autonomous | jq '.[0].State.Health'

# Monitor resource usage
docker stats mcp-agent-autonomous
```

## 💾 Volume Management

### Persistent Volumes

```yaml
volumes:
  mcp-logs:        # Application logs
  mcp-data:        # Autonomous agent data
  mcp-config:      # Configuration files
```

### Volume Usage

```bash
# Backup volumes
docker run --rm -v mcp-data:/data -v $(pwd):/backup alpine tar czf /backup/mcp-data-backup.tar.gz -C /data .

# Restore volumes
docker run --rm -v mcp-data:/data -v $(pwd):/backup alpine tar xzf /backup/mcp-data-backup.tar.gz -C /data

# Inspect volume contents
docker run --rm -it -v mcp-data:/data alpine ls -la /data
```

## 🔐 Security Configuration

### Non-Root User

```dockerfile
# Create non-root user
RUN groupadd -r mcpagent && useradd -r -g mcpagent mcpagent
RUN chown -R mcpagent:mcpagent /app
USER mcpagent
```

### API Key Security

```bash
# Use Docker secrets (Docker Swarm)
echo "your-openai-key" | docker secret create openai_api_key -

# Use environment file
echo "OPENAI_API_KEY=your-key" > .env
docker-compose --env-file .env up
```

### Network Security

```yaml
networks:
  mcp-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
```

## 🚀 Production Deployment

### Docker Swarm

```yaml
# docker-stack.yml
version: '3.8'
services:
  mcp-agent:
    image: mcp-agent-prod:latest
    deploy:
      replicas: 3
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
    secrets:
      - openai_api_key
    environment:
      - OPENAI_API_KEY_FILE=/run/secrets/openai_api_key
```

Deploy:
```bash
docker stack deploy -c docker-stack.yml mcp-stack
```

### Kubernetes

```yaml
# k8s-deployment.yml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mcp-agent-autonomous
spec:
  replicas: 3
  selector:
    matchLabels:
      app: mcp-agent
  template:
    metadata:
      labels:
        app: mcp-agent
    spec:
      containers:
      - name: mcp-agent
        image: mcp-agent-prod:latest
        ports:
        - containerPort: 8000
        env:
        - name: MCP_AUTONOMOUS_MODE
          value: "true"
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: mcp-secrets
              key: openai-key
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
```

## 📈 Performance Optimization

### Resource Limits

```yaml
services:
  mcp-agent:
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '2'
        reservations:
          memory: 512M
          cpus: '1'
```

### Caching Strategy

```yaml
environment:
  - MCP_CACHE_TTL=3600
  - MCP_ENABLE_PARALLEL_DISCOVERY=true
  - MCP_METRICS_RETENTION_DAYS=30
```

### Scaling Considerations

- **Horizontal scaling**: Multiple container instances
- **Vertical scaling**: Increased CPU/memory per container
- **Load balancing**: Distribute tasks across instances
- **Database**: Shared state for multi-instance deployments

## 🔍 Troubleshooting

### Common Issues

#### 1. Autonomous Components Not Loading
```bash
# Check Python path
docker exec mcp-agent-autonomous python -c "import sys; print(sys.path)"

# Verify autonomous imports
docker exec mcp-agent-autonomous python -c "from mcp_agent.autonomous.task_analyzer import TaskAnalyzer"
```

#### 2. Configuration Not Found
```bash
# Check config file
docker exec mcp-agent-autonomous ls -la /app/config/

# Verify environment variables
docker exec mcp-agent-autonomous env | grep MCP_
```

#### 3. API Key Issues
```bash
# Check environment variables
docker exec mcp-agent-autonomous env | grep API_KEY

# Test API connectivity (without exposing keys)
docker exec mcp-agent-autonomous python -c "import os; print('OpenAI key set:', bool(os.getenv('OPENAI_API_KEY')))"
```

#### 4. Volume Permission Issues
```bash
# Fix permissions
docker exec --user root mcp-agent-autonomous chown -R mcpagent:mcpagent /app/logs /app/data
```

### Debug Mode

Enable comprehensive debugging:

```bash
docker run --rm \
  -e MCP_LOG_LEVEL=debug \
  -e MCP_DEV_MODE=true \
  -v $(pwd)/logs:/app/logs \
  mcp-agent-autonomous
```

### Performance Monitoring

```bash
# Monitor container metrics
docker exec mcp-agent-autonomous python -c "
from mcp_agent.autonomous.autonomous_orchestrator import AutonomousOrchestrator
import asyncio
async def check():
    o = AutonomousOrchestrator()
    await o.initialize()
    caps = await o.analyze_capabilities()
    print(f'Success rate: {caps.get(\"success_rate\", 0)*100:.1f}%')
asyncio.run(check())
"
```

## 📚 Advanced Usage

### Custom Autonomous Configuration

```yaml
# custom-autonomous.yaml
autonomous:
  enabled: true
  max_agents: 10
  max_execution_time: 600
  default_llm_provider: anthropic
  enable_fallbacks: true
  log_decisions: true
  require_human_approval: false

tool_discovery:
  auto_discovery: true
  discovery_interval: 180
  enable_dynamic_installation: true
  preferred_servers:
    - mcp-server-fetch
    - mcp-server-git
    - mcp-server-sqlite

performance:
  enable_caching: true
  cache_ttl: 7200
  enable_parallel_discovery: true
  max_concurrent_discoveries: 10
  metrics_retention_days: 90
```

Mount custom config:
```bash
docker run --rm \
  -v $(pwd)/custom-autonomous.yaml:/app/config/autonomous.yaml \
  -e MCP_AUTONOMOUS_CONFIG_PATH=/app/config/autonomous.yaml \
  mcp-agent-autonomous
```

### Multi-Container Autonomous Setup

```yaml
# docker-compose.autonomous.yml
version: '3.8'
services:
  mcp-orchestrator:
    image: mcp-agent-autonomous
    environment:
      - MCP_ROLE=orchestrator
    command: ["python", "/app/examples/autonomous/advanced_autonomous_workflow.py"]
  
  mcp-worker-1:
    image: mcp-agent-autonomous
    environment:
      - MCP_ROLE=worker
      - MCP_WORKER_ID=1
  
  mcp-worker-2:
    image: mcp-agent-autonomous
    environment:
      - MCP_ROLE=worker
      - MCP_WORKER_ID=2
```

This enhanced Docker setup provides a robust, scalable foundation for deploying autonomous MCP-Agent capabilities in any environment.
