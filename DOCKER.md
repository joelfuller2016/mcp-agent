# Docker Deployment Guide for MCP Agent

This directory contains Docker configuration for deploying and developing the MCP Agent framework.

## 🐳 Quick Start

### Build and Run

```bash
# Build the Docker image
docker build -t mcp-agent .

# Run the basic example
docker run --rm mcp-agent

# Run interactively for development
docker run -it --rm -v $(pwd):/app mcp-agent bash
```

### Using Docker Compose

```bash
# Start the development environment
docker-compose up mcp-agent

# Run tests in Docker
docker-compose run mcp-agent-test

# Build and start services
docker-compose up --build
```

## 📋 What's Included

### Docker Files

- **`Dockerfile`** - Main container definition
- **`docker-compose.yml`** - Multi-service orchestration
- **`.dockerignore`** - Build context exclusions

### Container Features

- ✅ **Python 3.11** environment
- ✅ **UV package manager** for fast dependency management
- ✅ **Node.js & npm** for MCP servers
- ✅ **Pre-installed MCP servers**: filesystem, fetch
- ✅ **Development tools** included
- ✅ **Optimized layers** for faster builds

## 🏗️ Container Architecture

```
mcp-agent:latest
├── Python 3.11 + UV
├── Node.js + MCP servers
├── MCP Agent framework
├── Example configurations
└── Development tools
```

## 🔧 Configuration

### Environment Variables

```bash
# API Keys (mount secrets file or use env vars)
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here

# Python settings
PYTHONPATH=/app
PYTHONUNBUFFERED=1
```

### Volume Mounts

```bash
# Development with live reload
docker run -v $(pwd):/app mcp-agent

# Persistent logs
docker run -v ./logs:/app/logs mcp-agent

# Custom examples
docker run -v ./my-examples:/app/examples mcp-agent
```

## 🧪 Testing

```bash
# Run all tests
docker-compose run mcp-agent-test

# Run specific tests
docker run --rm mcp-agent uv run python -m pytest tests/test_agents.py -v

# Interactive testing
docker run -it --rm mcp-agent bash
```

## 📦 Production Deployment

### Multi-stage Build (Optimized)

```dockerfile
# Production Dockerfile.prod
FROM mcp-agent:latest as production
WORKDIR /app
CMD ["uv", "run", "python", "your_production_script.py"]
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mcp-agent
spec:
  replicas: 3
  selector:
    matchLabels:
      app: mcp-agent
  template:
    spec:
      containers:
      - name: mcp-agent
        image: mcp-agent:latest
        ports:
        - containerPort: 8000
        env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: mcp-secrets
              key: openai-key
```

## 🔍 Troubleshooting

### Common Issues

1. **Build fails with dependencies**
   ```bash
   # Clear cache and rebuild
   docker build --no-cache -t mcp-agent .
   ```

2. **Permission errors**
   ```bash
   # Use correct user
   docker run --user $(id -u):$(id -g) mcp-agent
   ```

3. **API key issues**
   ```bash
   # Mount secrets file
   docker run -v ./secrets.yaml:/app/mcp_agent.secrets.yaml mcp-agent
   ```

### Debug Mode

```bash
# Run with debug logging
docker run -e LOG_LEVEL=debug mcp-agent

# Interactive debugging
docker run -it --rm --entrypoint bash mcp-agent
```

## 🚀 Advanced Usage

### Custom MCP Servers

```dockerfile
# Add custom MCP server
RUN npm install -g @your-org/custom-mcp-server
```

### Multi-Agent Deployment

```yaml
# docker-compose.yml
services:
  agent-1:
    build: .
    environment:
      - AGENT_ROLE=analyzer
  agent-2:
    build: .
    environment:
      - AGENT_ROLE=processor
  agent-3:
    build: .
    environment:
      - AGENT_ROLE=synthesizer
```

### Monitoring & Observability

```bash
# With logging driver
docker run --log-driver=fluentd mcp-agent

# With health checks
docker run --health-cmd="curl -f http://localhost:8000/health" mcp-agent
```

## 📊 Performance

- **Image Size**: ~580MB (optimized)
- **Startup Time**: <3 seconds
- **Memory Usage**: ~100MB base
- **Build Time**: ~2 minutes

## 🛡️ Security

- ✅ **Non-root user** execution
- ✅ **Minimal base image** (python:3.11-slim)
- ✅ **Secrets management** via environment/files
- ✅ **Network isolation** in Docker Compose
- ✅ **Read-only filesystem** option available

## 🤝 Contributing

When adding new Docker features:

1. Update this documentation
2. Test with `docker-compose up --build`
3. Verify multi-platform builds
4. Update example configurations

---

## 📚 Related Documentation

- [Main README](../README.md) - Project overview
- [Contributing Guide](../CONTRIBUTING.md) - Development setup
- [Examples](../examples/) - Usage examples

For issues or questions about Docker deployment, please open an issue with the `docker` label.
