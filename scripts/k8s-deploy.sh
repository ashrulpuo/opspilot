#!/bin/bash
# Kubernetes Deployment Script for OpsPilot
# Usage: ./k8s-deploy.sh [namespace] [environment]

set -e

# Default values
NAMESPACE="${1:-opspilot}"
ENVIRONMENT="${2:-production}"
BACKEND_IMAGE="${3:-opspilot-backend:latest}"
FRONTEND_IMAGE="${4:-opspilot-frontend:latest}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check kubectl
if ! command -v kubectl &> /dev/null; then
    log_error "kubectl is not installed. Please install it first."
    exit 1
fi

# Check cluster connection
log_info "Checking Kubernetes cluster connection..."
if ! kubectl cluster-info &> /dev/null; then
    log_error "Cannot connect to Kubernetes cluster. Please check your kubeconfig."
    exit 1
fi

log_info "Connected to cluster: $(kubectl config current-context)"

# Create namespace
log_info "Creating namespace: $NAMESPACE"
kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -

# Apply ConfigMap
log_info "Applying ConfigMap..."
kubectl apply -f infrastructure/kubernetes/01-configmap.yaml -n $NAMESPACE

# Apply Secrets
log_warn "Make sure to update secrets in 02-secret.yaml before continuing!"
read -p "Continue? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    log_info "Applying Secrets..."
    kubectl apply -f infrastructure/kubernetes/02-secret.yaml -n $NAMESPACE
else
    log_error "Aborted. Please update secrets first."
    exit 1
fi

# Build images (if needed)
log_info "Building Docker images..."
docker build -t $BACKEND_IMAGE -f infrastructure/docker/Dockerfile.backend ./backend
docker build -t $FRONTEND_IMAGE -f infrastructure/docker/Dockerfile.frontend ./frontend

# Tag and push images (if using a registry)
read -p "Push images to registry? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    read -p "Enter registry URL (e.g., registry.example.com): " REGISTRY_URL
    docker tag $BACKEND_IMAGE $REGISTRY_URL/$BACKEND_IMAGE
    docker tag $FRONTEND_IMAGE $REGISTRY_URL/$FRONTEND_IMAGE
    docker push $REGISTRY_URL/$BACKEND_IMAGE
    docker push $REGISTRY_URL/$FRONTEND_IMAGE
    
    # Update image names in deployment files
    sed -i.bak "s|image: opspilot-backend:latest|image: $REGISTRY_URL/$BACKEND_IMAGE|g" infrastructure/kubernetes/50-backend.yaml
    sed -i.bak "s|image: opspilot-frontend:latest|image: $REGISTRY_URL/$FRONTEND_IMAGE|g" infrastructure/kubernetes/60-frontend.yaml
fi

# Deploy in order
log_info "Deploying PostgreSQL + TimescaleDB..."
kubectl apply -f infrastructure/kubernetes/10-postgres.yaml -n $NAMESPACE

log_info "Waiting for PostgreSQL to be ready..."
kubectl wait --for=condition=ready pod -l app=opspilot,tier=database -n $NAMESPACE --timeout=300s

log_info "Deploying Redis..."
kubectl apply -f infrastructure/kubernetes/20-redis.yaml -n $NAMESPACE

log_info "Waiting for Redis to be ready..."
kubectl wait --for=condition=ready pod -l app=opspilot,tier=cache -n $NAMESPACE --timeout=120s

log_info "Deploying Vault..."
kubectl apply -f infrastructure/kubernetes/30-vault.yaml -n $NAMESPACE

log_info "Waiting for Vault to be ready..."
kubectl wait --for=condition=ready pod -l app=opspilot,tier=secrets -n $NAMESPACE --timeout=120s

log_info "Deploying Salt Master..."
kubectl apply -f infrastructure/kubernetes/40-salt-master.yaml -n $NAMESPACE

log_info "Waiting for Salt Master to be ready..."
kubectl wait --for=condition=ready pod -l app=opspilot,tier=automation -n $NAMESPACE --timeout=120s

# Enable TimescaleDB extension
log_info "Enabling TimescaleDB extension..."
kubectl exec -it $(kubectl get pods -n $NAMESPACE -l app=opspilot,tier=database -o jsonpath='{.items[0].metadata.name}') -n $NAMESPACE -- \
    psql -U $(kubectl get configmap opspilot-config -n $NAMESPACE -o jsonpath='{.data.DATABASE_USER}') -d opspilot -c "CREATE EXTENSION IF NOT EXISTS timescaledb;"

# Create hypertable for metrics
log_info "Creating TimescaleDB hypertable for metrics..."
kubectl exec -it $(kubectl get pods -n $NAMESPACE -l app=opspilot,tier=database -o jsonpath='{.items[0].metadata.name}') -n $NAMESPACE -- \
    psql -U $(kubectl get configmap opspilot-config -n $NAMESPACE -o jsonpath='{.data.DATABASE_USER}') -d opspilot -c "SELECT create_hypertable('metrics', 'timestamp', if_not_exists => TRUE);"

# Set retention policy
log_info "Setting TimescaleDB retention policy (90 days)..."
kubectl exec -it $(kubectl get pods -n $NAMESPACE -l app=opspilot,tier=database -o jsonpath='{.items[0].metadata.name}') -n $NAMESPACE -- \
    psql -U $(kubectl get configmap opspilot-config -n $NAMESPACE -o jsonpath='{.data.DATABASE_USER}') -d opspilot -c "SELECT add_retention_policy('metrics', INTERVAL '90 days');"

log_info "Deploying Backend..."
kubectl apply -f infrastructure/kubernetes/50-backend.yaml -n $NAMESPACE

log_info "Waiting for Backend to be ready..."
kubectl wait --for=condition=ready pod -l app=opspilot,tier=backend -n $NAMESPACE --timeout=300s

log_info "Deploying Frontend..."
kubectl apply -f infrastructure/kubernetes/60-frontend.yaml -n $NAMESPACE

log_info "Waiting for Frontend to be ready..."
kubectl wait --for=condition=ready pod -l app=opspilot,tier=frontend -n $NAMESPACE --timeout=300s

log_info "Deploying Ingress..."
kubectl apply -f infrastructure/kubernetes/70-ingress.yaml -n $NAMESPACE

# Verify deployment
log_info "Verifying deployment..."
echo ""
log_info "Pods in namespace $NAMESPACE:"
kubectl get pods -n $NAMESPACE

echo ""
log_info "Services in namespace $NAMESPACE:"
kubectl get services -n $NAMESPACE

echo ""
log_info "Ingress in namespace $NAMESPACE:"
kubectl get ingress -n $NAMESPACE

# Run database migrations
log_info "Running database migrations..."
BACKEND_POD=$(kubectl get pods -n $NAMESPACE -l app=opspilot,tier=backend -o jsonpath='{.items[0].metadata.name}')
kubectl exec -it $BACKEND_POD -n $NAMESPACE -- alembic upgrade head

# Summary
echo ""
log_info "=========================================="
log_info "Deployment Complete!"
log_info "=========================================="
echo ""
log_info "Application URL: https://app.opspilot.com"
log_info "API URL: https://api.opspilot.com"
echo ""
log_info "To check logs:"
echo "  kubectl logs -f -n $NAMESPACE -l app=opspilot,tier=backend"
echo ""
log_info "To scale deployments:"
echo "  kubectl scale deployment opspilot-backend -n $NAMESPACE --replicas=3"
echo "  kubectl scale deployment opspilot-frontend -n $NAMESPACE --replicas=3"
echo ""
log_info "To rollback:"
echo "  kubectl rollout undo deployment opspilot-backend -n $NAMESPACE"
echo "  kubectl rollout undo deployment opspilot-frontend -n $NAMESPACE"
echo ""
log_info "=========================================="
