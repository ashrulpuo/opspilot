#!/bin/bash

# OpsPilot Quick Deployment Script
# Automated deployment to production

set -e

echo "🚀 OpsPilot Production Deployment"
echo "==================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
VERSION=${1:-"latest"}
NAMESPACE="production"
REGISTRY="registry.digitalocean.com/opspilot"

# Check if version is provided
if [ "$VERSION" == "latest" ]; then
    echo -e "${YELLOW}No version specified, using 'latest'${NC}"
    echo "Usage: ./deploy.sh <version>"
    echo "Example: ./deploy.sh v1.0.0"
    echo ""
fi

echo "Deploying version: $VERSION"
echo "Namespace: $NAMESPACE"
echo "Registry: $REGISTRY"
echo ""

# ============================================
# Prerequisites Check
# ============================================

echo "🔍 Checking prerequisites..."
if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}❌ kubectl not found. Install kubectl first${NC}"
    exit 1
fi

if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ docker not found. Install docker first${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Prerequisites check passed${NC}"
echo ""

# ============================================
# Build Docker Images
# ============================================

echo "📦 Building Docker images..."
echo "-----------------------------"

# Backend
echo "Building backend image..."
cd backend
docker build -t ${REGISTRY}/opspilot-backend:${VERSION} .
echo -e "${GREEN}✅ Backend image built${NC}"

# Frontend
echo "Building frontend image..."
cd ../frontend
docker build -t ${REGISTRY}/opspilot-frontend:${VERSION} .
echo -e "${GREEN}✅ Frontend image built${NC}"

cd ..

echo ""

# ============================================
# Push Docker Images
# ============================================

echo "📤 Pushing Docker images to registry..."
echo "----------------------------------------"

echo "Pushing backend image..."
docker push ${REGISTRY}/opspilot-backend:${VERSION}
echo -e "${GREEN}✅ Backend image pushed${NC}"

echo "Pushing frontend image..."
docker push ${REGISTRY}/opspilot-frontend:${VERSION}
echo -e "${GREEN}✅ Frontend image pushed${NC}"

echo ""

# ============================================
# Deploy to Kubernetes
# ============================================

echo "🚀 Deploying to Kubernetes..."
echo "----------------------------"

# Create namespace if it doesn't exist
kubectl create namespace ${NAMESPACE} --dry-run=client -o yaml | kubectl apply -f -

# Update backend deployment
echo "Updating backend deployment..."
kubectl set image deployment/opspilot-backend \
    backend=${REGISTRY}/opspilot-backend:${VERSION} \
    -n ${NAMESPACE} \
    --record=true
echo -e "${GREEN}✅ Backend deployment updated${NC}"

# Update frontend deployment
echo "Updating frontend deployment..."
kubectl set image deployment/opspilot-frontend \
    frontend=${REGISTRY}/opspilot-frontend:${VERSION} \
    -n ${NAMESPACE} \
    --record=true
echo -e "${GREEN}✅ Frontend deployment updated${NC}"

echo ""

# ============================================
# Wait for Rollout
# ============================================

echo "⏳ Waiting for rollout to complete..."
echo "--------------------------------------"

echo "Waiting for backend rollout..."
kubectl rollout status deployment/opspilot-backend -n ${NAMESPACE} --timeout=300s
echo -e "${GREEN}✅ Backend rollout complete${NC}"

echo "Waiting for frontend rollout..."
kubectl rollout status deployment/opspilot-frontend -n ${NAMESPACE} --timeout=300s
echo -e "${GREEN}✅ Frontend rollout complete${NC}"

echo ""

# ============================================
# Verify Deployment
# ============================================

echo "✅ Verifying deployment..."
echo "------------------------"

# Get pods
echo "Pods in ${NAMESPACE} namespace:"
kubectl get pods -n ${NAMESPACE}

# Get services
echo "Services in ${NAMESPACE} namespace:"
kubectl get services -n ${NAMESPACE}

# Get ingress
echo "Ingress in ${NAMESPACE} namespace:"
kubectl get ingress -n ${NAMESPACE}

echo ""

# ============================================
# Health Check
# ============================================

echo "🏥 Running health checks..."
echo "--------------------------"

# Wait for backend to be ready
BACKEND_POD=$(kubectl get pod -n ${NAMESPACE} -l app=opspilot-backend -o jsonpath='{.items[0].metadata.name}')
echo "Checking backend pod: ${BACKEND_POD}"

# Get backend pod IP
BACKEND_IP=$(kubectl get pod ${BACKEND_POD} -n ${NAMESPACE} -o jsonpath='{.status.podIP}')
echo "Backend pod IP: ${BACKEND_IP}"

# Execute health check
kubectl exec ${BACKEND_POD} -n ${NAMESPACE} -- curl -f http://localhost:8000/health || {
    echo -e "${RED}❌ Backend health check failed${NC}"
    echo "View logs: kubectl logs ${BACKEND_POD} -n ${NAMESPACE}"
    exit 1
}

echo -e "${GREEN}✅ Backend health check passed${NC}"

# Wait for frontend to be ready
FRONTEND_POD=$(kubectl get pod -n ${NAMESPACE} -l app=opspilot-frontend -o jsonpath='{.items[0].metadata.name}')
echo "Checking frontend pod: ${FRONTEND_POD}"

# Get frontend pod IP
FRONTEND_IP=$(kubectl get pod ${FRONTEND_POD} -n ${NAMESPACE} -o jsonpath='{.status.podIP}')
echo "Frontend pod IP: ${FRONTEND_IP}"

# Execute health check
kubectl exec ${FRONTEND_POD} -n ${NAMESPACE} -- curl -f http://localhost/ || {
    echo -e "${RED}❌ Frontend health check failed${NC}"
    echo "View logs: kubectl logs ${FRONTEND_POD} -n ${NAMESPACE}"
    exit 1
}

echo -e "${GREEN}✅ Frontend health check passed${NC}"

echo ""

# ============================================
# Deployment Summary
# ============================================

echo "======================================"
echo -e "${GREEN}✅ Deployment Complete!${NC}"
echo "======================================"
echo ""
echo "Version deployed: $VERSION"
echo "Namespace: $NAMESPACE"
echo ""
echo "Useful commands:"
echo "  View logs: kubectl logs <pod-name> -n ${NAMESPACE} -f"
echo "  Scale backend: kubectl scale deployment/opspilot-backend --replicas=5 -n ${NAMESPACE}"
echo "  Scale frontend: kubectl scale deployment/opspilot-frontend --replicas=3 -n ${NAMESPACE}"
echo "  Restart deployment: kubectl rollout restart deployment/opspilot-backend -n ${NAMESPACE}"
echo ""
echo "Rollback if needed:"
echo "  kubectl rollout undo deployment/opspilot-backend -n ${NAMESPACE}"
echo "  kubectl rollout undo deployment/opspilot-frontend -n ${NAMESPACE}"
echo ""
echo "Access URLs:"
echo "  Frontend: https://app.yourdomain.com"
echo "  Backend API: https://api.yourdomain.com"
echo "  WebSocket: wss://ws.yourdomain.com"
echo ""
