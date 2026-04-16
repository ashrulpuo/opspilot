# OpsPilot Infrastructure

Infrastructure as Code for OpsPilot DevOps Automation Platform.

## Overview

This repository contains Terraform configurations and Helm charts for deploying OpsPilot to Kubernetes.

## Structure

```
opspilot-infrastructure/
├── terraform/              # Terraform configurations
│   ├── environments/       # Environment-specific configs (dev, staging, prod)
│   ├── modules/            # Reusable Terraform modules
│   └── main.tf             # Main Terraform entry point
├── helm/                   # Helm charts
│   ├── opspilot-backend/   # Backend service chart
│   ├── opspilot-frontend/  # Frontend service chart
│   └── postgresql/         # PostgreSQL + TimescaleDB chart
└── docker/                 # Dockerfiles for services
```

## Prerequisites

- Terraform 1.6+
- kubectl configured with cluster access
- Helm 3+
- Docker (for building images)

## Quick Start

### Terraform

```bash
cd terraform/environments/dev

# Initialize Terraform
terraform init

# Plan infrastructure changes
terraform plan

# Apply changes
terraform apply

# Destroy infrastructure
terraform destroy
```

### Helm

```bash
# Add required Helm repositories
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo add hashicorp https://helm.releases.hashicorp.com
helm repo update

# Install OpsPilot charts
helm install opspilot-backend ./helm/opspilot-backend
helm install opspilot-frontend ./helm/opspilot-frontend
helm install postgresql ./helm/postgresql
helm install redis ./helm/redis
helm install vault ./helm/vault
```

## Modules

### PostgreSQL with TimescaleDB
- PostgreSQL 15+
- TimescaleDB extension
- Automated backups
- High availability (optional)

### Redis
- Redis 7+
- Persistence enabled
- Cluster support (optional)

### Vault
- HashiCorp Vault
- Auto-unseal (AWS KMS or GCP KMS)
- Kubernetes authentication

### SaltStack
- Salt Master deployment
- Minion auto-configuration
- Salt API exposure

## Security Notes

- All secrets stored in Vault
- Network policies for service-to-service communication
- PodSecurityPolicy/SecurityContext hardening
- TLS for all external communications

## Environment Variables

See `.env.example` for required environment variables.

## License

MIT
