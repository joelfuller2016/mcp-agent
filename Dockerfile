# Enhanced Dockerfile for MCP-Agent with Autonomous Support
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies including autonomous operation support
RUN apt-get update && apt-get install -y \
    git \
    curl \
    wget \
    build-essential \
    nodejs \
    npm \
    sqlite3 \
    jq \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install UV package manager for fast dependency management
RUN pip install uv

# Install comprehensive set of MCP servers for autonomous operations
RUN npm install -g \
    @modelcontextprotocol/server-filesystem \
    @modelcontextprotocol/server-fetch \
    @modelcontextprotocol/server-git \
    @modelcontextprotocol/server-sqlite \
    && npm cache clean --force

# Install uvx and Python-based MCP servers
RUN pip install uvx && \
    uvx install mcp-server-fetch && \
    uvx install mcp-server-git && \
    uvx install mcp-server-sqlite

# Copy the entire project into the container
COPY . /app/

# Install Python dependencies using UV
RUN uv sync

# Install the mcp-agent package in development mode
RUN uv pip install -e .

# Create necessary directories for autonomous operations
RUN mkdir -p logs examples/autonomous data/autonomous config

# Set working directory to basic example
WORKDIR /app/examples/basic/mcp_basic_agent

# Create secrets file from example (will be overridden by environment variables)
RUN cp mcp_agent.secrets.yaml.example mcp_agent.secrets.yaml || echo "# Add your API keys here" > mcp_agent.secrets.yaml

# Return to app root
WORKDIR /app

# Create autonomous configuration file
RUN echo "autonomous:" > config/autonomous.yaml && \
    echo "  enabled: true" >> config/autonomous.yaml && \
    echo "  max_agents: 5" >> config/autonomous.yaml && \
    echo "  max_execution_time: 300" >> config/autonomous.yaml && \
    echo "  default_llm_provider: openai" >> config/autonomous.yaml && \
    echo "  enable_fallbacks: true" >> config/autonomous.yaml && \
    echo "  log_decisions: true" >> config/autonomous.yaml && \
    echo "  require_human_approval: false" >> config/autonomous.yaml && \
    echo "" >> config/autonomous.yaml && \
    echo "tool_discovery:" >> config/autonomous.yaml && \
    echo "  auto_discovery: true" >> config/autonomous.yaml && \
    echo "  discovery_interval: 300" >> config/autonomous.yaml && \
    echo "  max_concurrent_discoveries: 5" >> config/autonomous.yaml && \
    echo "  enable_dynamic_installation: true" >> config/autonomous.yaml && \
    echo "" >> config/autonomous.yaml && \
    echo "performance:" >> config/autonomous.yaml && \
    echo "  enable_caching: true" >> config/autonomous.yaml && \
    echo "  cache_ttl: 3600" >> config/autonomous.yaml && \
    echo "  enable_parallel_discovery: true" >> config/autonomous.yaml && \
    echo "  metrics_retention_days: 30" >> config/autonomous.yaml

# Health check for autonomous components
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.path.insert(0, '/app/src'); from mcp_agent.autonomous.task_analyzer import TaskAnalyzer; TaskAnalyzer().analyze_task('test')" || exit 1

# Expose port for potential web interface
EXPOSE 8000

# Set environment variables including autonomous support
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV MCP_AUTONOMOUS_MODE=true
ENV MCP_LOG_LEVEL=info
ENV MCP_AUTONOMOUS_CONFIG_PATH=/app/config/autonomous.yaml

# Default command runs enhanced deployment test with autonomous features
CMD ["uv", "run", "python", "/app/docker/test_enhanced_deployment.py"]
