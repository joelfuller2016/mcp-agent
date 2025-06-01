# Docker commands for MCP Agent

.PHONY: docker-build docker-run docker-dev docker-test docker-clean docker-shell

# Build the main Docker image
docker-build:
	docker build -t mcp-agent:latest .

# Build development image
docker-build-dev:
	docker build -f docker/Dockerfile.dev -t mcp-agent:dev .

# Build production image
docker-build-prod:
	docker build -f docker/Dockerfile.prod -t mcp-agent:prod .

# Run the basic test
docker-run:
	docker run --rm mcp-agent:latest

# Run in development mode with volume mounts
docker-dev:
	docker run -it --rm \
		-v $(PWD):/app \
		-v $(PWD)/logs:/app/logs \
		-p 8000:8000 \
		mcp-agent:dev

# Run tests in Docker
docker-test:
	docker run --rm \
		-v $(PWD):/app \
		mcp-agent:dev \
		uv run python -m pytest tests/ -v

# Interactive shell in container
docker-shell:
	docker run -it --rm \
		-v $(PWD):/app \
		--entrypoint bash \
		mcp-agent:dev

# Run with Docker Compose (development)
docker-compose-dev:
	docker-compose -f docker/docker-compose.dev.yml up --build

# Run specific service with Docker Compose
docker-compose-test:
	docker-compose -f docker/docker-compose.dev.yml run --rm mcp-agent-test

# Clean up Docker resources
docker-clean:
	docker system prune -f
	docker volume prune -f

# Remove all MCP agent images
docker-clean-images:
	docker rmi -f $(shell docker images mcp-agent* -q) 2>/dev/null || true

# Full rebuild (clean + build)
docker-rebuild: docker-clean-images docker-build

# Quick test run (build + test)
docker-quick-test: docker-build docker-test

# Development setup (build dev image and start interactive session)
docker-setup: docker-build-dev docker-dev

# Show Docker system information
docker-info:
	@echo "=== Docker Images ==="
	@docker images mcp-agent*
	@echo "\n=== Docker Containers ==="
	@docker ps -a --filter "ancestor=mcp-agent"
	@echo "\n=== Docker System Usage ==="
	@docker system df

# Help
docker-help:
	@echo "Available Docker commands:"
	@echo "  docker-build          Build main Docker image"
	@echo "  docker-build-dev      Build development image"
	@echo "  docker-build-prod     Build production image"
	@echo "  docker-run            Run basic test in container"
	@echo "  docker-dev            Start development container"
	@echo "  docker-test           Run tests in container"
	@echo "  docker-shell          Interactive shell in container"
	@echo "  docker-compose-dev    Start with Docker Compose"
	@echo "  docker-compose-test   Run tests with Docker Compose"
	@echo "  docker-clean          Clean up Docker resources"
	@echo "  docker-clean-images   Remove MCP agent images"
	@echo "  docker-rebuild        Full rebuild"
	@echo "  docker-quick-test     Build and test"
	@echo "  docker-setup          Development setup"
	@echo "  docker-info           Show Docker status"
	@echo "  docker-help           Show this help"
