#!/bin/bash
# =============================================================
# Deployment Script for School Management System
# =============================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "=========================================="
echo "  School Management System - Deployment"
echo "=========================================="

# Check Docker is available
if ! command -v docker &> /dev/null; then
    echo "ERROR: Docker is not installed or not in PATH"
    exit 1
fi

if ! command -v docker compose &> /dev/null && ! command -v docker-compose &> /dev/null; then
    echo "ERROR: Docker Compose is not installed"
    exit 1
fi

cd "$PROJECT_DIR"

echo ""
echo "[1/5] Pulling latest code..."
git pull origin main 2>/dev/null || echo "  (skipped - not a git repo or no remote)"

echo ""
echo "[2/5] Building Docker images..."
docker compose build --no-cache

echo ""
echo "[3/5] Starting services..."
docker compose up -d

echo ""
echo "[4/5] Waiting for services to be healthy..."
sleep 10

echo ""
echo "[5/5] Verifying deployment..."
# Check backend health
HEALTH=$(curl -s http://localhost:8000/api/v1/health 2>/dev/null || echo '{"status":"error"}')
echo "  Backend health: $HEALTH"

# Check frontend
FRONTEND=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5173 2>/dev/null || echo "000")
echo "  Frontend HTTP status: $FRONTEND"

echo ""
echo "=========================================="
echo "  Deployment Complete!"
echo "=========================================="
echo "  Frontend:   http://localhost:5173"
echo "  Backend:    http://localhost:8000"
echo "  API Docs:   http://localhost:8000/docs"
echo "  Prometheus: http://localhost:9090"
echo "  Grafana:    http://localhost:3000 (admin/admin)"
echo "=========================================="
