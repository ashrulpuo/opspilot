# GitLab + CI/CD - Complete Guide

## Overview

OpsPilot now has complete GitLab integration with:

1. ✅ GitLab repository setup automation
2. ✅ GitLab CI/CD pipelines for backend and frontend
3. ✅ Docker multi-stage builds
4. ✅ Automated testing (unit, integration)
5. ✅ Security scanning (SAST, SCA, container scanning)
6. ✅ Automated deployments to dev/staging/production
7. ✅ Container registry integration
8. ✅ Merge request templates
9. ✅ Issue templates
10. ✅ Branch protection
11. ✅ Scheduled pipelines
12. ✅ Rollback support

---

## Quick Start

### 1. Set Up GitLab Repository

```bash
cd /Volumes/ashrul/Development/Active/opspilot

# Interactive setup
make gitlab-setup

# Or directly
bash scripts/gitlab-setup.sh \
  https://gitlab.com \
  glpat-xxxxxxxxxxxxxxxxxxxx \
  opspilot
```

**What the script does:**
- Creates GitLab project
- Initializes git repository
- Pushes code to GitLab
- Configures protected branches (main, develop, production)
- Creates CI/CD project access token
- Configures Kubernetes clusters (optional)
- Sets up CI/CD variables
- Creates merge request templates
- Creates issue templates
- Creates project README

---

### 2. Configure CI/CD Variables

**Critical:** Set these variables in GitLab UI:

**Path:** Settings > CI/CD > Variables

**Backend Variables:**
```
DATABASE_URL = postgresql+asyncpg://user:password@host:5432/opspilot
DATABASE_PASSWORD = secure_password
REDIS_URL = redis://host:6379/0
REDIS_PASSWORD = secure_password
SECRET_KEY = secure_32_char_jwt_secret
SALT_API_KEY = secure_api_key
VAULT_TOKEN = vault_token
SALT_API_PASSWORD = secure_password
EMAIL_SMTP_USERNAME = your-email@gmail.com
EMAIL_SMTP_PASSWORD = your-app-password
```

**Frontend Variables:**
```
FRONTEND_URL = https://app.opspilot.com
API_URL = https://api.opspilot.com
```

**Kubernetes Variables:**
```
KUBE_CONTEXT_DEV = dev-cluster-context
KUBE_CONTEXT_STAGING = staging-cluster-context
KUBE_CONTEXT_PROD = prod-cluster-context
```

**⚠️ Mark all password/token variables as "Protected" and "Masked"!**

---

### 3. Configure Kubernetes Clusters

**Path:** Infrastructure > Kubernetes

**Required Clusters:**
1. **Development** (namespace: `opspilot-dev`)
2. **Staging** (namespace: `opspilot-staging`)
3. **Production** (namespace: `opspilot`)

**For each cluster:**
1. Click "Connect cluster"
2. Enter cluster API URL
3. Paste CA certificate (if using self-signed cert)
4. Install GitLab Runner (if needed)
5. Set default namespace

---

### 4. First Pipeline Run

```bash
# Trigger pipeline
make gitlab-pipeline

# Or manually in GitLab UI
# CI/CD > Pipelines > Run pipeline
```

**Expected Pipeline Stages:**
1. Test (unit, integration)
2. Security (SAST, SCA, container)
3. Build (Docker)
4. Deploy (dev/staging/production)

---

## Architecture

### GitLab CI/CD Pipeline Structure

```
┌─────────────────────────────────────────────────────────────┐
│                 GitLab CI/CD Pipeline                     │
│                                                            │
│  ┌─────────────────────────────────────────────┐    │
│  │           Backend Pipeline                 │    │
│  │                                            │        │
│  │  ┌─────────────────────────────────┐         │        │
│  │  │     Test Stage                │         │        │
│  │  │  - Unit tests                │         │        │
│  │  │  - Integration tests         │         │        │
│  │  └─────────────────────────────────┘         │        │
│  │           │                                    │        │
│  │  ▼                                    │        │
│  │  ┌─────────────────────────────────┐         │        │
│  │  │    Security Stage            │         │        │
│  │  │  - SAST                      │         │        │
│  │  │  - SCA                       │         │        │
│  │  │  - Container scanning        │         │        │
│  │  └─────────────────────────────────┘         │        │
│  │           │                                    │        │
│  │  ▼                                    │        │
│  │  ┌─────────────────────────────────┐         │        │
│  │  │    Build Stage               │         │        │
│  │  │  - Build Docker image         │         │        │
│  │  │  - Push to registry         │         │        │
│  │  └─────────────────────────────────┘         │        │
│  │           │                                    │        │
│  │  ▼                                    │        │
│  │  ┌─────────────────────────────────┐         │        │
│  │  │   Deploy Stages             │         │        │
│  │  │  - Deploy to dev            │         │        │
│  │  │  - Deploy to staging         │         │        │
│  │  │  - Deploy to production      │         │        │
│  │  └─────────────────────────────────┘         │        │
│  └─────────────────────────────────────────────┘    │
│                                                           │
│  ┌─────────────────────────────────────────────┐    │
│  │           Frontend Pipeline                │    │
│  │                                            │        │
│  │  [Similar stages as backend]                │        │
│  └─────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

---

## CI/CD Pipelines

### Backend Pipeline (`.gitlab-ci.backend.yml`)

**Stages:**
1. **test**
   - `unit-tests` - Run pytest with coverage
   - `integration-tests` - Run integration tests with test DB

2. **security**
   - `security-scan` - Safety and Bandit scanning
   - `sast` - Static application security testing
   - `dependency-scanning` - Dependency vulnerability scan
   - `container-scanning` - Container image scanning

3. **build**
   - `build-backend` - Build Docker image, push to registry

4. **deploy**
   - `deploy-dev` - Deploy to dev cluster (auto on develop branch)
   - `deploy-staging` - Deploy to staging cluster (manual on main)
   - `deploy-production` - Deploy to production (manual on production)
   - `rollback-backend` - Rollback to previous version (manual)

**Triggers:**
- Automatic on push to `develop`, `main`, `production`
- Manual deployment to staging/production
- Scheduled pipelines (optional)

### Frontend Pipeline (`.gitlab-ci.frontend.yml`)

**Stages:**
1. **test**
   - `unit-tests` - Run vitest with coverage
   - `type-check` - TypeScript type checking
   - `lint` - ESLint checking

2. **security**
   - `security-scan` - npm audit
   - `sast` - Static application security testing
   - `dependency-scanning` - Dependency vulnerability scan
   - `container-scanning` - Container image scanning

3. **build**
   - `build-frontend` - Build Docker image, push to registry

4. **deploy**
   - `deploy-dev` - Deploy to dev cluster
   - `deploy-staging` - Deploy to staging cluster
   - `deploy-production` - Deploy to production cluster
   - `rollback-frontend` - Rollback to previous version

---

## Dockerfiles

### Backend Dockerfile (`Dockerfile.backend`)

**Multi-stage:**
1. Build stage - Install Python dependencies
2. Production stage - Minimal runtime

**Features:**
- Python 3.11-slim base image
- Non-root user (security)
- Health check endpoint
- Optimized layer caching
- Copy local dependencies first

**Build:**
```bash
docker build -f Dockerfile.backend -t opspilot-backend:latest .
```

### Frontend Dockerfile (`Dockerfile.frontend`)

**Multi-stage:**
1. Builder stage - Build Vue 3 app
2. Production stage - Nginx serving static files

**Features:**
- Node 22-alpine base for builder
- Nginx 1.25-alpine for production
- Non-root user
- Health check endpoint
- Optimized static asset serving
- Custom nginx config

**Build:**
```bash
docker build -f Dockerfile.frontend -t opspilot-frontend:latest .
```

---

## Container Registry

GitLab Container Registry automatically integrated:

**Registry URL:**
```
registry.gitlab.com/username/opspilot/opspilot-backend
registry.gitlab.com/username/opspilot/opspilot-frontend
```

**Images:**
- `opspilot-backend:latest` - Latest stable version
- `opspilot-backend:<commit-sha>` - Specific commit version
- `opspilot-frontend:latest` - Latest stable version
- `opspilot-frontend:<commit-sha>` - Specific commit version

**Usage:**
```bash
# Pull image
docker pull registry.gitlab.com/username/opspilot/opspilot-backend:latest

# Use in Kubernetes
image: registry.gitlab.com/username/opspilot/opspilot-backend:latest
```

---

## Branch Strategy

### Protected Branches

**Main Branches:**
1. **`main`** - Production-ready code
   - Push: Protected (maintainers only)
   - Merge: Protected (maintainers only)
   - Requirements: Passing pipeline, approvals

2. **`develop`** - Development integration branch
   - Push: Protected (maintainers only)
   - Merge: Protected (developers)
   - Requirements: Passing pipeline

3. **`production`** - Production releases
   - Push: Protected (maintainers only)
   - Merge: Protected (maintainers only)
   - Requirements: Passing pipeline, approvals

### Branch Naming

**Feature Branches:**
```
feature/<feature-name>
example: feature/user-authentication
```

**Bugfix Branches:**
```
bugfix/<bug-name>
example: bugfix/login-redirect-issue
```

**Hotfix Branches:**
```
hotfix/<hotfix-name>
example: hotfix/security-patch
```

### Workflow

1. **Develop** → `develop` branch
2. **Test** → Automated tests
3. **Review** → Create merge request
4. **Merge** → Merge to `develop`
5. **Release** → Merge `develop` → `main`
6. **Deploy** → Automated deploy to staging
7. **Approve** → Manual approve for production
8. **Deploy** → Manual deploy to production

---

## Merge Requests

### Merge Request Template

Created automatically at `.gitlab/merge_request_templates/default.md`

**Sections:**
- Description
- Type of Change (Bug fix, New feature, Breaking change, Documentation)
- Testing checklist
- Code review checklist
- Related issues

### Merge Request Settings

**Configured by setup script:**
- **Squash on merge:** Enabled
- **Merge method:** Merge commit
- **Remove source branch:** After merge
- **Only allow merge if pipeline succeeds:** Enabled
- **Approvals required:** For production branch

### Best Practices

1. **Write clear commit messages:**
   ```
   feat(auth): add JWT authentication
   fix(db): resolve connection pool issue
   docs(readme): update installation instructions
   ```

2. **Keep MRs focused:**
   - One feature or bugfix per MR
   - Small, reviewable chunks

3. **Update documentation:**
   - README.md
   - API docs
   - Changelog

4. **Include tests:**
   - Unit tests for new code
   - Integration tests for API changes

5. **Address review comments:**
   - Respond to all feedback
   - Update code as needed
   - Re-request review when done

---

## Issues

### Issue Templates

Created automatically at `.gitlab/issue_templates/`:

**Bug Report (`Bug.md`)**
- Description
- Steps to reproduce
- Expected vs actual behavior
- Environment details

**Feature Request (`Feature.md`)**
- Description
- Problem statement
- Proposed solution
- Alternatives considered

### Issue Labels

**Recommended labels:**
- `bug` - Bug reports
- `enhancement` - Feature requests
- `documentation` - Documentation issues
- `security` - Security issues
- `critical` - High priority bugs
- `good first issue` - Easy fixes for newcomers

---

## Troubleshooting

### Pipeline Fails - Test Stage

**Check:**
```bash
# View test logs
# GitLab UI: CI/CD > Pipelines > Click pipeline > Click job

# Run tests locally
cd backend
poetry install --with dev
poetry run pytest tests/ -v
```

**Common issues:**
- Missing dependencies → Update `pyproject.toml`
- Test DB connection failed → Check test DB configuration
- Timeout → Increase test timeout

### Pipeline Fails - Build Stage

**Check:**
```bash
# View build logs
# GitLab UI: CI/CD > Pipelines > Click pipeline > Click job

# Build locally
docker build -f Dockerfile.backend -t test .
docker run test
```

**Common issues:**
- Docker build timeout → Increase `DOCKER_BUILDKIT` timeout
- Out of memory → Increase runner memory limit
- Registry authentication failed → Check CI_REGISTRY_PASSWORD

### Pipeline Fails - Deploy Stage

**Check:**
```bash
# View deploy logs
# GitLab UI: CI/CD > Pipelines > Click pipeline > Click job

# Check kubectl connection
kubectl config current-context
kubectl get pods -n opspilot
```

**Common issues:**
- kubectl not configured → Check KUBE_CONTEXT variables
- Image pull failed → Check registry credentials
- Deployment fails → Check Kubernetes resources

### Container Scanning Fails

**Check:**
```bash
# View scanning results
# GitLab UI: Security & Compliance > Container Scanning
```

**Common issues:**
- High severity vulnerabilities → Update dependencies
- Base image vulnerabilities → Update base image version

---

## Security

### CI/CD Security Best Practices

1. **Never commit secrets:**
   - Use GitLab CI/CD variables
   - Mask sensitive variables
   - Use protected variables for production

2. **Use protected branches:**
   - Protect `main`, `develop`, `production`
   - Require approvals for production
   - Require passing pipelines

3. **Limit runner access:**
   - Use protected runners for production
   - Separate runners for dev/staging/prod
   - Configure runner permissions

4. **Security scanning:**
   - SAST on every MR
   - SCA on every MR
   - Container scanning on every build
   - Review security reports

5. **Access control:**
   - Use project access tokens (not personal)
   - Rotate tokens regularly
   - Audit token usage

---

## Monitoring

### Pipeline Status

**View in GitLab UI:**
- CI/CD > Pipelines
- View all pipelines, their status, duration
- Click on pipeline to view jobs

### Pipeline Analytics

**View in GitLab UI:**
- CI/CD > Pipelines > Analytics
- Pipeline duration trends
- Success/failure rates
- Job performance

### Job Artifacts

**View in GitLab UI:**
- CI/CD > Pipelines > Click pipeline > Click job
- Download artifacts (test coverage, reports)
- View job logs

---

## Advanced Topics

### Custom GitLab Runners

**Create runners for:**
- Specific environments (dev, staging, prod)
- Performance requirements (more RAM/CPU)
- Custom dependencies (specific tools)

**Setup:**
```bash
# Install GitLab Runner
curl -L https://packages.gitlab.com/install/repositories/runner/gitlab-runner/script.deb.sh | sudo bash

# Register runner
sudo gitlab-runner register \
  --url https://gitlab.com \
  --registration-token $RUNNER_TOKEN \
  --executor docker \
  --docker-image docker:24
```

### Pipeline Schedules

**Create scheduled pipelines:**
```bash
# In GitLab UI
# CI/CD > Pipelines > Schedules

# Or via API
curl -X POST \
  -H "PRIVATE-TOKEN: $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Daily build and test",
    "cron": "0 2 * * *",
    "ref": "main"
  }' \
  https://gitlab.com/api/v4/projects/$PROJECT_ID/pipeline_schedules
```

### Pipeline Variables

**Scoped variables:**
- Dev environment: `DATABASE_URL_DEV`
- Staging environment: `DATABASE_URL_STAGING`
- Production environment: `DATABASE_URL_PROD`

**Use in `.gitlab-ci.yml`:**
```yaml
variables:
  DATABASE_URL: $DATABASE_URL_${CI_ENVIRONMENT_NAME}
```

---

## Documentation

- [GitLab CI/CD Documentation](https://docs.gitlab.com/ee/ci/)
- [GitLab Runner Documentation](https://docs.gitlab.com/runner/)
- [Docker Documentation](https://docs.docker.com/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [OpsPilot PRD](/Volumes/ashrul/Development/Active/prds/current/2026-Q2/)

---

## Support

For issues or questions:
1. Check GitLab CI/CD logs
2. Review pipeline status in GitLab UI
3. Check runner logs
4. Review this documentation

---

**GitLab + CI/CD Complete!** 🦊✅
