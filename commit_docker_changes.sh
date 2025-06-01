#!/bin/bash

# Script to commit Docker deployment features to the MCP Agent repository

echo "🐳 Committing Docker deployment to MCP Agent repository..."

# Add all Docker-related files
echo "📁 Adding Docker files..."
git add Dockerfile
git add .dockerignore  
git add docker-compose.yml
git add DOCKER.md
git add docker/
git add README.md

# Check what's being committed
echo "📋 Files to be committed:"
git status --porcelain

# Create commit
echo "💾 Creating commit..."
git commit -m "feat: Add comprehensive Docker deployment support

🐳 Docker Features Added:
- Multi-stage Dockerfiles (dev/prod)
- Docker Compose configurations
- Pre-configured MCP servers
- Development environment with live reload
- Production-ready containers with security
- Automated testing in containers
- Comprehensive documentation

📁 Files Added:
- Dockerfile - Main container definition
- docker-compose.yml - Service orchestration
- .dockerignore - Build optimization
- DOCKER.md - Complete deployment guide
- docker/ - Additional Docker configurations
- Updated README.md with Docker section

✅ Ready for containerized deployment and development!

Co-Authored-By: Claude <noreply@anthropic.com>"

# Show commit result
echo "✅ Commit created successfully!"
echo "📤 To push to GitHub, run:"
echo "   git push origin main"

echo "🎉 Docker deployment is now ready in your repository!"
