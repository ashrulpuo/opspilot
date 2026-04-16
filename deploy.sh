#!/bin/bash

# OpsPilot Deployment Script
# Quick start for local development

echo "🚀 Starting OpsPilot Deployment..."

# Check if Docker is running
if ! docker ps > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Start infrastructure services
echo "📦 Starting infrastructure services (PostgreSQL, Redis, Vault)..."
cd /Volumes/ashrul/Development/Active/opspilot
docker-compose up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check service status
echo "🔍 Checking service status..."
docker ps --filter "name=opspilot" --format "table {{.Names}}\t{{.Status}}"

echo "✅ Infrastructure services started successfully!"
echo ""
echo "📊 Service Endpoints:"
echo "  - PostgreSQL: localhost:5438"
echo "  - Redis: localhost:6384"
echo "  - Vault: localhost:8201"
echo "  - pgAdmin: http://localhost:5051 (admin/admin)"
echo "  - Redis Insight: http://localhost:8002"
echo ""
echo "🚀 Next Steps:"
echo "  1. Start backend: cd backend && poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
echo "  2. Start frontend: cd frontend && pnpm dev"
echo "  3. Open browser: http://localhost:5173"
