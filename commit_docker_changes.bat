@echo off
echo 🐳 Committing Docker deployment to MCP Agent repository...

REM Add all Docker-related files
echo 📁 Adding Docker files...
git add Dockerfile
git add .dockerignore  
git add docker-compose.yml
git add DOCKER.md
git add docker/
git add README.md

REM Check what's being committed
echo 📋 Files to be committed:
git status --porcelain

REM Create commit
echo 💾 Creating commit...
git commit -m "feat: Add comprehensive Docker deployment support" -m "" -m "🐳 Docker Features Added:" -m "- Multi-stage Dockerfiles (dev/prod)" -m "- Docker Compose configurations" -m "- Pre-configured MCP servers" -m "- Development environment with live reload" -m "- Production-ready containers with security" -m "- Automated testing in containers" -m "- Comprehensive documentation" -m "" -m "📁 Files Added:" -m "- Dockerfile - Main container definition" -m "- docker-compose.yml - Service orchestration" -m "- .dockerignore - Build optimization" -m "- DOCKER.md - Complete deployment guide" -m "- docker/ - Additional Docker configurations" -m "- Updated README.md with Docker section" -m "" -m "✅ Ready for containerized deployment and development!" -m "" -m "Co-Authored-By: Claude <noreply@anthropic.com>"

REM Show commit result
echo ✅ Commit created successfully!
echo 📤 To push to GitHub, run:
echo    git push origin main

echo 🎉 Docker deployment is now ready in your repository!
pause
