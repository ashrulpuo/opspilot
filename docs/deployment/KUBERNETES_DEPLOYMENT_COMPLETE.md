# Kubernetes Deployment - Complete Guide

## Overview

OpsPilot now has complete Kubernetes deployment with:

1. ✅ Namespace isolation
2. ✅ ConfigMap for configuration
3. ✅ Secret management
4. ✅ PostgreSQL + TimescaleDB
5. ✅ Redis
6. ✅ Vault
7. ✅ Salt Master
8. ✅ Backend (FastAPI)
9. ✅ Frontend (Vue 3)
10. ✅ Ingress with TLS
11. ✅ Horizontal Pod Autoscaling
12. ✅ Health checks
13. ✅ Resource limits
14. ✅ Automated deployment script

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Kubernetes Cluster                     │
│                                                            │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              Ingress (nginx)                     │    │
│  │  app.opspilot.com → Frontend                   │    │
│  │  api.opspilot.com → Backend                    │    │
│  └─────────────────────────────────────────────────────┘    │
│                           │                                 │
│         ┌─────────────────┼─────────────────┐               │
│         │                 │                 │               │
│  ┌──────▼──────┐  ┌────▼─────┐  ┌─────▼──────┐       │
│  │  Frontend   │  │  Backend │  │ Salt Master │       │
│  │   (Vue 3)   │  │ (FastAPI) │  │ (SaltStack) │       │
│  │   2 pods    │  │   2 pods  │  │    1 pod    │       │
│  └──────┬──────┘  └────┬─────┘  └─────┬──────┘       │
│         │               │                │               │
│         │               └────────┬───────┘               │
│         │                        │                      │
│  ┌──────▼────────────────────────▼───────┐             │
│  │       Services (ClusterIP)             │             │
│  └────────────────────────────────────────┘             │
│                                                        │
│  ┌─────────────────────────────────────────────┐          │
│  │         Data Layer                        │          │
│  │  ┌─────┐  ┌─────┐  ┌─────┐        │          │
│  │  │Post │  │Redis│  │Vault│        │          │
│  │  │greSQL│  │     │  │     │        │          │
│  │  │Times│  │     │  │     │        │          │
│  │  │cale │  │     │  │     │        │          │
│  │  └─────┘  └─────┘  └─────┘        │          │
│  └─────────────────────────────────────────┘          │
│                                                        │
└─────────────────────────────────────────────────────────────┘
```

---

## Quick Start

### Prerequisites

1. **Kubernetes cluster** (v1.25+)
   - Local: Minikube, Kind, Docker Desktop
   - Cloud: GKE, EKS, AKS, DigitalOcean K8s

2. **kubectl** installed
   ```bash
   # Check version
   kubectl version --client
   ```

3. **Docker** installed (for building images)

4. **Ingress controller** (nginx-ingress)
5. **cert-manager** (for TLS certificates)

### 1. Deploy to Kubernetes

```bash
cd /Volumes/ashrul/Development/Active/opspilot

# Interactive deployment
bash scripts/k8s-deploy.sh

# Or specify namespace and environment
bash scripts/k8s-deploy.sh opspilot production

# With custom images
bash scripts/k8s-deploy.sh opspilot production \
  registry.example.com/opspilot-backend:v1.0.0 \
  registry.example.com/opspilot-frontend:v1.0.0
```

### 2. Update Secrets

**IMPORTANT:** Update secrets before deploying!

```bash
# Edit secret file
vim infrastructure/kubernetes/02-secret.yaml

# Update values:
# - DATABASE_PASSWORD
# - SECRET_KEY
# - SALT_API_KEY
# - REDIS_PASSWORD
# - VAULT_TOKEN
# - SALT_API_PASSWORD
# - EMAIL_SMTP_USERNAME
# - EMAIL_SMTP_PASSWORD
```

### 3. Configure Ingress

Update domain names in:

1. `infrastructure/kubernetes/01-configmap.yaml`
   - `APP_URL`
   - `FRONTEND_URL`
   - `API_URL`

2. `infrastructure/kubernetes/70-ingress.yaml`
   - `host: app.opspilot.com` → your domain
   - `host: api.opspilot.com` → your domain

### 4. Verify Deployment

```bash
# Check all pods
kubectl get pods -n opspilot

# Check services
kubectl get services -n opspilot

# Check ingress
kubectl get ingress -n opspilot

# Check backend logs
kubectl logs -f -n opspilot -l app=opspilot,tier=backend

# Check frontend logs
kubectl logs -f -n opspilot -l app=opspilot,tier=frontend
```

---

## Deployment Files

### File Structure

```
infrastructure/kubernetes/
├── 00-namespace.yaml          # Namespace definition
├── 01-configmap.yaml         # Application configuration
├── 02-secret.yaml            # Sensitive data (update this!)
├── 10-postgres.yaml          # PostgreSQL + TimescaleDB
├── 20-redis.yaml            # Redis cache
├── 30-vault.yaml            # HashiCorp Vault
├── 40-salt-master.yaml       # SaltStack master
├── 50-backend.yaml          # FastAPI backend
├── 60-frontend.yaml         # Vue 3 frontend
└── 70-ingress.yaml          # Ingress routing + TLS
```

---

## Components

### 1. Namespace

- **Name:** `opspilot`
- **Purpose:** Resource isolation
- **Labels:** `app=opspilot`

### 2. ConfigMap

**Environment variables:**
- Application settings (APP_NAME, APP_ENV, etc.)
- Database configuration (host, port)
- Redis configuration
- Vault configuration
- Salt API configuration
- Email settings
- URLs

**Sensitive values are in Secrets!**

### 3. Secret

**Sensitive data:**
- Database password
- JWT secret key
- Salt API key
- Redis password
- Vault token
- Salt API credentials
- Email credentials

**⚠️ NEVER COMMIT SECRETS TO GIT!**

### 4. PostgreSQL + TimescaleDB

**Deployment:** StatefulSet
**Replicas:** 1
**Storage:** 50Gi PVC
**Resources:**
  - Requests: 2Gi RAM, 1 CPU
  - Limits: 4Gi RAM, 2 CPU

**Features:**
- TimescaleDB extension enabled
- Hypertable for metrics
- 90-day retention policy
- Health checks (liveness, readiness)

### 5. Redis

**Deployment:** Deployment
**Replicas:** 1
**Storage:** 10Gi PVC
**Resources:**
  - Requests: 512Mi RAM, 250m CPU
  - Limits: 1Gi RAM, 500m CPU

**Features:**
- AOF persistence
- Password authentication
- Health checks

### 6. Vault

**Deployment:** Deployment
**Replicas:** 1
**Storage:** 5Gi PVC
**Resources:**
  - Requests: 256Mi RAM, 100m CPU
  - Limits: 512Mi RAM, 250m CPU

**Features:**
- Dev mode (auto-unseal)
- IPC_LOCK capability
- Health checks

### 7. Salt Master

**Deployment:** Deployment
**Replicas:** 1
**Storage:** 5Gi PVC (for states/pillars)
**Ports:** 4505, 4506, 8000
**Resources:**
  - Requests: 512Mi RAM, 250m CPU
  - Limits: 1Gi RAM, 500m CPU

**Features:**
- PAM authentication
- Salt API on port 8000
- Custom state files
- Health checks

### 8. Backend (FastAPI)

**Deployment:** Deployment
**Replicas:** 2 (HPA: 2-10)
**Resources:**
  - Requests: 512Mi RAM, 250m CPU
  - Limits: 1Gi RAM, 500m CPU

**Features:**
- Rolling updates
- Health checks (liveness, readiness, startup)
- Horizontal Pod Autoscaling
- Environment variables from ConfigMap + Secret

### 9. Frontend (Vue 3)

**Deployment:** Deployment
**Replicas:** 2 (HPA: 2-5)
**Resources:**
  - Requests: 128Mi RAM, 50m CPU
  - Limits: 256Mi RAM, 100m CPU

**Features:**
- Rolling updates
- Health checks
- Horizontal Pod Autoscaling
- Nginx container

### 10. Ingress

**Controller:** nginx
**TLS:** cert-manager + Let's Encrypt
**Routes:**
- `app.opspilot.com` → Frontend (port 80)
- `api.opspilot.com` → Backend (port 8000)
- `app.opspilot.com/api` → Backend (port 8000)

**Features:**
- SSL redirect
- Large proxy body size (100MB)
- WebSocket support
- Long timeout (600s)

---

## Scaling

### Horizontal Pod Autoscaling (HPA)

**Backend:**
- Min: 2 replicas
- Max: 10 replicas
- CPU: Scale at 70% utilization
- Memory: Scale at 80% utilization

**Frontend:**
- Min: 2 replicas
- Max: 5 replicas
- CPU: Scale at 70% utilization
- Memory: Scale at 80% utilization

### Manual Scaling

```bash
# Scale backend
kubectl scale deployment opspilot-backend -n opspilot --replicas=5

# Scale frontend
kubectl scale deployment opspilot-frontend -n opspilot --replicas=3

# Scale Redis (if needed)
kubectl scale deployment opspilot-redis -n opspilot --replicas=2
```

---

## Updates & Rollbacks

### Rolling Update

```bash
# Update backend image
kubectl set image deployment/opspilot-backend \
  backend=opspilot-backend:v1.0.1 \
  -n opspilot

# Update frontend image
kubectl set image deployment/opspilot-frontend \
  frontend=opspilot-frontend:v1.0.1 \
  -n opspilot

# Watch rollout
kubectl rollout status deployment/opspilot-backend -n opspilot
```

### Rollback

```bash
# Rollback to previous version
kubectl rollout undo deployment/opspilot-backend -n opspilot
kubectl rollout undo deployment/opspilot-frontend -n opspilot

# Rollback to specific revision
kubectl rollout undo deployment/opspilot-backend \
  --to-revision=2 \
  -n opspilot

# Check rollout history
kubectl rollout history deployment/opspilot-backend -n opspilot
```

---

## Monitoring

### View Logs

```bash
# Backend logs
kubectl logs -f -n opspilot -l app=opspilot,tier=backend

# Frontend logs
kubectl logs -f -n opspilot -l app=opspilot,tier=frontend

# All logs
kubectl logs -f -n opspilot -l app=opspilot --all-containers=true

# Previous pod logs (if crashed)
kubectl logs -n opspilot <pod-name> --previous
```

### Pod Status

```bash
# All pods
kubectl get pods -n opspilot

# Wide format (with nodes)
kubectl get pods -n opspilot -o wide

# Describe pod (for troubleshooting)
kubectl describe pod <pod-name> -n opspilot
```

### Resource Usage

```bash
# Resource usage by pod
kubectl top pods -n opspilot

# Resource usage by node
kubectl top nodes

# Resource requests and limits
kubectl get pods -n opspilot -o jsonpath='{.items[*].spec.containers[*].resources}'
```

---

## Troubleshooting

### Pod Not Starting

```bash
# Check pod status
kubectl describe pod <pod-name> -n opspilot

# Check pod logs
kubectl logs <pod-name> -n opspilot

# Check events
kubectl get events -n opspilot --sort-by=.metadata.creationTimestamp
```

### Service Not Working

```bash
# Check service
kubectl describe service opspilot-backend -n opspilot

# Test service from inside cluster
kubectl run test-pod --image=busybox --rm -it \
  --restart=Never -- sh
wget -O- http://opspilot-backend.opspilot.svc.cluster.local:8000/health
```

### Ingress Not Working

```bash
# Check ingress
kubectl describe ingress opspilot-ingress -n opspilot

# Check nginx-ingress controller
kubectl get pods -n ingress-nginx

# Check nginx-ingress logs
kubectl logs -f -n ingress-nginx <pod-name>
```

### Database Connection Issues

```bash
# Check postgres pod
kubectl get pods -n opspilot -l app=opspilot,tier=database

# Test connection
kubectl exec -it <postgres-pod> -n opspilot -- \
  psql -U opspilot -d opspilot -c "SELECT version();"

# Check postgres logs
kubectl logs -f -n opspilot -l app=opspilot,tier=database
```

### Certificate Issues

```bash
# Check certificate
kubectl describe certificate opspilot-tls -n opspilot

# Check certificate status
kubectl get certificate -n opspilot

# Force certificate renewal
kubectl delete certificate opspilot-tls -n opspilot
```

---

## Production Checklist

### Before Deploying to Production

- [ ] Update all secrets with strong values
- [ ] Configure correct domain names in ConfigMap
- [ ] Configure correct domain names in Ingress
- [ ] Ensure ingress controller is installed
- [ ] Ensure cert-manager is installed
- [ ] Configure Let's Encrypt ClusterIssuer
- [ ] Set up backup for PVCs
- [ ] Configure monitoring (Prometheus + Grafana)
- [ ] Configure logging (Loki + Promtail)
- [ ] Set up alerts (PagerDuty, Slack, etc.)
- [ ] Review resource limits
- [ ] Configure HPA thresholds
- [ ] Test rollback procedure
- [ ] Set up CI/CD pipeline

### After Deployment

- [ ] Verify all pods are running
- [ ] Verify services are accessible
- [ ] Verify ingress is working
- [ ] Verify TLS certificates are valid
- [ ] Test application endpoints
- [ ] Test database migrations
- [ ] Test Salt API connection
- [ ] Verify Vault is accessible
- [ ] Check logs for errors
- [ ] Monitor resource usage
- [ ] Test scaling behavior
- [ ] Document deployment

---

## Maintenance

### Backup PVCs

```bash
# Backup PostgreSQL data
kubectl exec <postgres-pod> -n opspilot -- \
  pg_dump -U opspilot opspilot > backup.sql

# Backup Redis data
kubectl cp <redis-pod>:/data redis-backup -n opspilot

# Backup Vault data
kubectl cp <vault-pod>:/vault/data vault-backup -n opspilot
```

### Restore PVCs

```bash
# Restore PostgreSQL
kubectl exec <postgres-pod> -n opspilot -i -- \
  psql -U opspilot opspilot < backup.sql

# Restore Redis
kubectl cp redis-backup <redis-pod>:/data -n opspilot

# Restore Vault
kubectl cp vault-backup <vault-pod>:/vault/data -n opspilot
```

### Clean Up

```bash
# Delete all resources in namespace
kubectl delete namespace opspilot

# Delete specific deployment
kubectl delete deployment opspilot-backend -n opspilot

# Delete old completed pods
kubectl delete pods -n opspilot --field-selector=status.phase=Succeeded
```

---

## Advanced Topics

### Blue-Green Deployment

```bash
# Deploy blue (current version)
kubectl apply -f infrastructure/kubernetes/50-backend.yaml -n opspilot-blue

# Deploy green (new version)
kubectl apply -f infrastructure/kubernetes/50-backend.yaml -n opspilot-green

# Switch ingress to green
kubectl patch ingress opspilot-ingress -n opspilot -p '...'
```

### Canary Deployment

```bash
# Create canary deployment (10% traffic)
kubectl scale deployment opspilot-backend -n opspilot --replicas=2

# Gradually increase canary
kubectl scale deployment opspilot-backend -n opspilot --replicas=3  # 30% traffic
kubectl scale deployment opspilot-backend -n opspilot --replicas=4  # 50% traffic
```

### ConfigMap Updates

```bash
# Update ConfigMap
kubectl edit configmap opspilot-config -n opspilot

# Force pod restart to pick up changes
kubectl rollout restart deployment opspilot-backend -n opspilot
kubectl rollout restart deployment opspilot-frontend -n opspilot
```

---

## Documentation

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Ingress NGINX](https://kubernetes.github.io/ingress-nginx/)
- [Cert Manager](https://cert-manager.io/docs/)
- [TimescaleDB](https://docs.timescale.com/)
- [OpsPilot PRD](/Volumes/ashrul/Development/Active/prds/current/2026-Q2/)

---

## Support

For issues or questions:
1. Check pod logs: `kubectl logs -n opspilot`
2. Describe pod: `kubectl describe pod <pod> -n opspilot`
3. Check events: `kubectl get events -n opspilot`
4. Review this documentation

---

**Kubernetes Deployment Complete!** ☸️✅
