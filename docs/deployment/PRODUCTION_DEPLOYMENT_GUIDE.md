# OpsPilot Production Deployment Guide

**Last Updated:** 2026-04-13
**Version:** 1.0.0

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Infrastructure Setup](#infrastructure-setup)
3. [Database Setup](#database-setup)
4. [Application Deployment](#application-deployment)
5. [SaltStack Setup](#saltstack-setup)
6. [Monitoring & Logging](#monitoring--logging)
7. [Security Configuration](#security-configuration)
8. [Rollback Procedure](#rollback-procedure)
9. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Tools Required

```bash
# Check tools are installed
kubectl version --client
helm version
docker version
terraform version
aws --version  # Or gcloud for GCP
```

### Cloud Provider Setup

#### DigitalOcean (Recommended)
- DigitalOcean account with API key
- VPC configured
- Load balancer configured
- Managed PostgreSQL cluster (TimescaleDB extension)
- Managed Redis cluster
- Object storage for backups (Spaces)

#### AWS Alternative
- AWS account with IAM user
- VPC configured
- RDS PostgreSQL (TimescaleDB)
- ElastiCache Redis
- S3 for backups

### DNS Configuration

```
A Record: app.yourdomain.com → Load Balancer IP
CNAME Record: api.yourdomain.com → Load Balancer IP
CNAME Record: ws.yourdomain.com → Load Balancer IP
```

---

## Infrastructure Setup

### 1. Terraform Configuration

**File:** `infrastructure/terraform/main.tf`

```hcl
# DigitalOcean Provider
provider "digitalocean" {
  token = var.do_token
}

# VPC
resource "digitalocean_vpc" "main" {
  name        = "opspilot-vpc"
  region      = var.region
  ip_range    = "10.0.0.0/16"
}

# PostgreSQL Cluster
resource "digitalocean_database_cluster" "postgres" {
  name       = "opspilot-db"
  engine     = "pg"
  version    = "15"
  size       = "db-s-2vcpu-8gb"
  region     = var.region
  node_count = 2
  vpc_id     = digitalocean_vpc.main.id

  # Enable TimescaleDB extension
  maintenance_window {
    day  = "sunday"
    hour = "03:00:00"
  }
}

# Redis Cluster
resource "digitalocean_database_cluster" "redis" {
  name       = "opspilot-redis"
  engine     = "redis"
  version    = "7"
  size       = "db-s-1vcpu-2gb"
  region     = var.region
  node_count = 1
  vpc_id     = digitalocean_vpc.main.id
}

# Load Balancer
resource "digitalocean_loadbalancer" "app" {
  name   = "opspilot-lb"
  region = var.region
  vpc_id = digitalocean_vpc.main.id

  forwarding_rule {
    entry_port     = 80
    entry_protocol = "http"
    target_port     = 80
    target_protocol = "http"

    forwarding_rule {
      port_range = "443"
      tls        = true
    }
  }

  healthcheck {
    protocol     = "http"
    port         = 80
    path         = "/health"
    check_interval = 10
    response_timeout = 5
    unhealthy_threshold = 3
    healthy_threshold = 2
  }
}
```

### 2. Apply Infrastructure

```bash
cd infrastructure/terraform

# Initialize Terraform
terraform init

# Review changes
terraform plan

# Apply infrastructure (30-60 minutes)
terraform apply

# Get outputs
terraform output -json > ../config/terraform-outputs.json
```

---

## Database Setup

### 1. TimescaleDB Extension

```bash
# Connect to PostgreSQL
PGPASSWORD=$(cat .env.db) psql -h $DB_HOST -U $DB_USER -d opspilot

# Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

# Verify installation
SELECT * FROM pg_extension WHERE extname = 'timescaledb';
```

### 2. Run Migrations

```bash
cd backend

# Install dependencies
pip install -e ".[dev]"

# Set database URL
export DATABASE_URL="postgresql+asyncpg://$DB_USER:$DB_PASS@$DB_HOST:5432/opspilot"

# Run migrations
alembic upgrade head

# Verify migrations
alembic current
alembic history
```

### 3. Create Hypertable for Metrics

```bash
# Connect to PostgreSQL
PGPASSWORD=$(cat .env.db) psql -h $DB_HOST -U $DB_USER -d opspilot

# Convert metrics table to hypertable
SELECT create_hypertable('metrics', 'timestamp', chunk_time_interval => INTERVAL '1 day');

# Set retention policy (90 days)
SELECT add_retention_policy('metrics', INTERVAL '90 days');

# Verify
SELECT * FROM timescaledb_information.hypertables;
```

---

## Application Deployment

### 1. Build Docker Images

```bash
# Backend
cd backend
docker build -t registry.digitalocean.com/opspilot/opspilot-backend:v1.0.0 .
docker push registry.digitalocean.com/opspilot/opspilot-backend:v1.0.0

# Frontend
cd ../frontend
docker build -t registry.digitalocean.com/opspilot/opspilot-frontend:v1.0.0 .
docker push registry.digitalocean.com/opspilot/opspilot-frontend:v1.0.0
```

### 2. Deploy to Kubernetes

**File:** `infrastructure/kubernetes/deployments/backend.yaml`

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: opspilot-backend
  namespace: production
spec:
  replicas: 3
  selector:
    matchLabels:
      app: opspilot-backend
  template:
    metadata:
      labels:
        app: opspilot-backend
    spec:
      containers:
      - name: backend
        image: registry.digitalocean.com/opspilot/opspilot-backend:v1.0.0
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: opspilot-secrets
              key: database-url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: opspilot-secrets
              key: redis-url
        - name: JWT_SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: opspilot-secrets
              key: jwt-secret
        - name: ENCRYPTION_KEY
          valueFrom:
            secretKeyRef:
              name: opspilot-secrets
              key: encryption-key
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5

---
apiVersion: v1
kind: Service
metadata:
  name: opspilot-backend
  namespace: production
spec:
  selector:
    app: opspilot-backend
  ports:
  - port: 80
    targetPort: 8000
  type: ClusterIP

---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: opspilot-backend-hpa
  namespace: production
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: opspilot-backend
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

**File:** `infrastructure/kubernetes/deployments/frontend.yaml`

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: opspilot-frontend
  namespace: production
spec:
  replicas: 2
  selector:
    matchLabels:
      app: opspilot-frontend
  template:
    metadata:
      labels:
        app: opspilot-frontend
    spec:
      containers:
      - name: frontend
        image: registry.digitalocean.com/opspilot/opspilot-frontend:v1.0.0
        ports:
        - containerPort: 80
        env:
        - name: VITE_API_BASE_URL
          value: "https://api.yourdomain.com"
        resources:
          requests:
            memory: "64Mi"
            cpu: "50m"
          limits:
            memory: "128Mi"
            cpu: "100m"
        livenessProbe:
          httpGet:
            path: /
            port: 80
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /
            port: 80
          initialDelaySeconds: 5
          periodSeconds: 5

---
apiVersion: v1
kind: Service
metadata:
  name: opspilot-frontend
  namespace: production
spec:
  selector:
    app: opspilot-frontend
  ports:
  - port: 80
    targetPort: 80
  type: ClusterIP
```

### 3. Create Kubernetes Secrets

```bash
# Generate secure secrets
export JWT_SECRET_KEY=$(openssl rand -base64 32)
export ENCRYPTION_KEY=$(openssl rand -base64 32)

# Create secret
kubectl create secret generic opspilot-secrets \
  --from-literal=jwt-secret=$JWT_SECRET_KEY \
  --from-literal=encryption-key=$ENCRYPTION_KEY \
  --from-literal=database-url=$DATABASE_URL \
  --from-literal=redis-url=$REDIS_URL \
  --namespace=production
```

### 4. Apply Kubernetes Manifests

```bash
cd infrastructure/kubernetes

# Create namespace
kubectl create namespace production

# Apply deployments
kubectl apply -f deployments/backend.yaml
kubectl apply -f deployments/frontend.yaml

# Apply ingress
kubectl apply -f ingress.yaml

# Verify
kubectl get pods -n production
kubectl get services -n production
```

### 5. Configure Ingress

**File:** `infrastructure/kubernetes/ingress.yaml`

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: opspilot-ingress
  namespace: production
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - app.yourdomain.com
    - api.yourdomain.com
    - ws.yourdomain.com
    secretName: opspilot-tls
  rules:
  - host: app.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: opspilot-frontend
            port:
              number: 80
  - host: api.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: opspilot-backend
            port:
              number: 80
  - host: ws.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: opspilot-backend
            port:
              number: 80
```

### 6. Deploy Application

```bash
# Apply ingress
kubectl apply -f ingress.yaml

# Wait for pods to be ready
kubectl wait --for=condition=ready pod -l app=opspilot-backend -n production --timeout=300s
kubectl wait --for=condition=ready pod -l app=opspilot-frontend -n production --timeout=300s

# Get Load Balancer IP
kubectl get ingress -n production

# Update DNS A records to point to Load Balancer IP
```

---

## SaltStack Setup

### 1. Install Salt Master

```bash
# On a dedicated server or use Kubernetes
kubectl apply -f infrastructure/kubernetes/salt/master.yaml
```

### 2. Install Salt Minions on Servers

```bash
# Install Salt minion on each server
curl -L https://bootstrap.saltproject.io | sudo sh -s -- -P -x python3

# Configure minion
sudo cat > /etc/salt/minion <<EOF
master: salt.yourdomain.com
id: $(hostname)
EOF

# Start minion
sudo systemctl start salt-minion
sudo systemctl enable salt-minion

# Accept key on master
sudo salt-key -A
```

### 3. Deploy Salt States

```bash
# Copy Salt states to master
kubectl cp salt/salt/ salt-master-0:/srv/salt/
kubectl cp salt/pillar/ salt-master-0:/srv/pillar/

# Apply states to all minions
sudo salt '*' state.apply
```

---

## Monitoring & Logging

### 1. Prometheus Monitoring

```bash
# Install Prometheus Operator
kubectl apply -f https://raw.githubusercontent.com/prometheus-operator/prometheus-operator/main/bundle.yaml

# Deploy Prometheus
kubectl apply -f infrastructure/kubernetes/monitoring/prometheus.yaml

# Configure ServiceMonitors for application
kubectl apply -f infrastructure/kubernetes/monitoring/servicemonitors.yaml
```

### 2. Grafana Dashboards

```bash
# Deploy Grafana
kubectl apply -f infrastructure/kubernetes/monitoring/grafana.yaml

# Import dashboards
kubectl apply -f infrastructure/kubernetes/monitoring/dashboards/
```

### 3. Centralized Logging (Loki)

```bash
# Install Loki
kubectl apply -f infrastructure/kubernetes/logging/loki.yaml

# Install Promtail on all nodes
kubectl apply -f infrastructure/kubernetes/logging/promtail-daemonset.yaml

# Configure application logging
# Application logs automatically shipped to Loki
```

---

## Security Configuration

### 1. TLS Certificates (Let's Encrypt)

```bash
# Install cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Create ClusterIssuer for production
kubectl apply -f infrastructure/kubernetes/cert-manager/cluster-issuer.yaml
```

### 2. Network Policies

```bash
# Apply network policies
kubectl apply -f infrastructure/kubernetes/networkpolicies.yaml
```

### 3. Vault for Secrets

```bash
# Install Vault
kubectl apply -f infrastructure/kubernetes/vault/

# Unseal Vault
kubectl exec -it vault-0 -n vault -- vault operator init
kubectl exec -it vault-0 -n vault -- vault operator unseal <unseal-key-1>
# Repeat for all keys

# Enable secrets engine
kubectl exec -it vault-0 -n vault -- vault secrets enable -path=opspilot kv-v2
```

---

## Rollback Procedure

### 1. Database Rollback

```bash
cd backend

# Rollback to previous migration
alembic downgrade -1

# Verify
alembic current
```

### 2. Application Rollback

```bash
# Rollback to previous image
kubectl set image deployment/opspilot-backend \
  backend=registry.digitalocean.com/opspilot/opspilot-backend:v0.9.0 \
  -n production

kubectl set image deployment/opspilot-frontend \
  frontend=registry.digitalocean.com/opspilot/opspilot-frontend:v0.9.0 \
  -n production

# Wait for rollout
kubectl rollout status deployment/opspilot-backend -n production
kubectl rollout status deployment/opspilot-frontend -n production
```

### 3. Full System Rollback

```bash
# Rollback everything to previous state
cd infrastructure/terraform
terraform apply -backup=-backup-<timestamp>
```

---

## Troubleshooting

### Check Pod Status

```bash
# List all pods
kubectl get pods -n production

# Describe pod
kubectl describe pod <pod-name> -n production

# View logs
kubectl logs <pod-name> -n production -f
```

### Database Issues

```bash
# Check database connection
PGPASSWORD=$(cat .env.db) psql -h $DB_HOST -U $DB_USER -d opspilot -c "SELECT 1;"

# Check TimescaleDB
PGPASSWORD=$(cat .env.db) psql -h $DB_HOST -U $DB_USER -d opspilot -c "SELECT * FROM timescaledb_information.hypertables;"
```

### Salt Issues

```bash
# Check Salt master status
sudo salt-run manage.status

# Check minion connectivity
sudo salt '*' test.ping

# Apply state on specific minion
sudo salt 'minion-id' state.apply
```

### Performance Issues

```bash
# Check resource usage
kubectl top pods -n production
kubectl top nodes

# Check HPA status
kubectl get hpa -n production

# Scale manually if needed
kubectl scale deployment opspilot-backend --replicas=5 -n production
```

---

## Post-Deployment Checklist

- [ ] Infrastructure deployed (Terraform)
- [ ] Database configured with TimescaleDB
- [ ] Migrations applied successfully
- [ ] Kubernetes secrets created
- [ ] Deployments rolled out
- [ ] Ingress configured with TLS
- [ ] DNS A records updated
- [ ] Load balancer working
- [ ] SSL certificates valid
- [ ] Salt master and minions connected
- [ ] Monitoring and logging configured
- [ ] Alerts configured in Prometheus/Grafana
- [ ] Backup schedules configured
- [ ] Security policies applied
- [ ] E2E tests passing
- [ ] Performance benchmarks met

---

## Maintenance

### Daily
- Check application logs
- Verify alerts are firing correctly
- Monitor resource usage

### Weekly
- Review deployment logs
- Check for security updates
- Backup database (automated but verify)

### Monthly
- Review performance metrics
- Optimize queries if needed
- Update dependencies
- Disaster recovery drill

### Quarterly
- Security audit
- Performance review
- Cost optimization
- Capacity planning

---

## Support

For issues or questions:
- GitHub Issues: https://github.com/yourcompany/opspilot/issues
- Documentation: https://docs.opspilot.dev
- Email: support@opspilot.dev
