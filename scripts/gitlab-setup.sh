#!/bin/bash
# GitLab Repository Setup Script for OpsPilot
# Usage: ./gitlab-setup.sh <gitlab_url> <access_token> <project_name>

set -e

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

# Check arguments
if [ $# -lt 3 ]; then
    log_error "Usage: $0 <gitlab_url> <access_token> <project_name>"
    echo ""
    echo "Arguments:"
    echo "  gitlab_url    - GitLab URL (e.g., https://gitlab.com)"
    echo "  access_token   - GitLab personal access token"
    echo "  project_name  - Project name (e.g., opspilot)"
    echo ""
    echo "Example:"
    echo "  $0 https://gitlab.com glpat-xxxxx opspilot"
    exit 1
fi

GITLAB_URL="$1"
ACCESS_TOKEN="$2"
PROJECT_NAME="$3"

# GitLab API helpers
api_request() {
    local endpoint="$1"
    local method="${2:-GET}"
    local data="${3:-}"

    curl -s -X "$method" \
        -H "PRIVATE-TOKEN: $ACCESS_TOKEN" \
        -H "Content-Type: application/json" \
        ${data:+-d "$data"} \
        "$GITLAB_URL/api/v4$endpoint"
}

# Check if git is installed
if ! command -v git &> /dev/null; then
    log_error "git is not installed. Please install it first."
    exit 1
fi

# Check if jq is installed
if ! command -v jq &> /dev/null; then
    log_error "jq is not installed. Please install it first."
    log_info "Install with: brew install jq (macOS) or apt-get install jq (Linux)"
    exit 1
fi

# Get user info
log_info "Getting GitLab user info..."
USER_INFO=$(api_request "/user")
USERNAME=$(echo "$USER_INFO" | jq -r '.username')
USER_ID=$(echo "$USER_INFO" | jq -r '.id')
EMAIL=$(echo "$USER_INFO" | jq -r '.email')

log_info "Logged in as: $USERNAME ($EMAIL)"

# Check if project exists
PROJECT_ID=$(api_request "/projects?search=$PROJECT_NAME" | jq -r ".[] | select(.path == \"$PROJECT_NAME\") | .id")

if [ -n "$PROJECT_ID" ]; then
    log_warn "Project '$PROJECT_NAME' already exists (ID: $PROJECT_ID)"
    read -p "Continue with existing project? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Aborted."
        exit 0
    fi
else
    log_info "Creating project: $PROJECT_NAME"
    PROJECT_DATA=$(cat <<EOF
{
    "name": "$PROJECT_NAME",
    "path": "$PROJECT_NAME",
    "namespace_id": $USER_ID,
    "default_branch": "main",
    "visibility": "private",
    "wiki_enabled": true,
    "issues_enabled": true,
    "merge_requests_enabled": true,
    "builds_enabled": true,
    "container_registry_enabled": true
}
EOF
)

    PROJECT_RESPONSE=$(api_request "/projects" "POST" "$PROJECT_DATA")
    PROJECT_ID=$(echo "$PROJECT_RESPONSE" | jq -r '.id')
    PROJECT_URL=$(echo "$PROJECT_RESPONSE" | jq -r '.web_url')

    log_info "Project created: $PROJECT_URL"
fi

# Initialize git if not already initialized
if [ ! -d ".git" ]; then
    log_info "Initializing git repository..."
    git init
    git add .
    git commit -m "Initial commit: OpsPilot DevOps Automation Platform"
    git branch -M main
fi

# Add GitLab remote if not exists
if ! git remote get-url gitlab &> /dev/null; then
    log_info "Adding GitLab remote..."
    GIT_SSH_URL=$(echo "$PROJECT_RESPONSE" | jq -r '.ssh_url_to_repo')
    git remote add gitlab "$GIT_SSH_URL"
fi

# Push to GitLab
log_info "Pushing to GitLab..."
git push -u gitlab main

# Enable required settings
log_info "Configuring project settings..."

# Enable LFS (Large File Storage)
api_request "/projects/$PROJECT_ID" "PUT" '{"lfs_enabled": true}'

# Enable request access control
api_request "/projects/$PROJECT_ID" "PUT" '{"request_access_enabled": true}'

# Enable squash on merge
api_request "/projects/$PROJECT_ID" "PUT" '{"squash_option": "default_on"}'

# Enable merge request approval
api_request "/projects/$PROJECT_ID" "PUT" '{"merge_requests_author_only": true}'

# Set default merge method to merge commit
api_request "/projects/$PROJECT_ID" "PUT" '{"merge_method": "merge"}'

# Protect main branch
log_info "Protecting main branch..."
BRANCH_PROTECTION_DATA=$(cat <<EOF
{
    "name": "main",
    "push_access_level": 40,
    "merge_access_level": 40,
    "unprotect_access_level": 40,
    "code_owner_approval_required": false,
    "allow_force_push": false,
    "allowed_to_push": [],
    "allowed_to_merge": []
}
EOF
)

api_request "/projects/$PROJECT_ID/protected_branches" "POST" "$BRANCH_PROTECTION_DATA"

# Create protected branches for develop and production
for BRANCH in develop production; do
    log_info "Protecting $BRANCH branch..."
    BRANCH_PROTECTION_DATA=$(cat <<EOF
{
    "name": "$BRANCH",
    "push_access_level": 40,
    "merge_access_level": 30,
    "unprotect_access_level": 40,
    "code_owner_approval_required": false,
    "allow_force_push": false,
    "allowed_to_push": [],
    "allowed_to_merge": []
}
EOF
)

    api_request "/projects/$PROJECT_ID/protected_branches" "POST" "$BRANCH_PROTECTION_DATA"
done

# Create project access token for CI/CD
log_info "Creating CI/CD project access token..."
TOKEN_DATA=$(cat <<EOF
{
    "name": "opspilot-cicd-token",
    "scopes": ["api", "read_repository", "write_repository", "read_registry", "write_registry"],
    "expires_at": null
}
EOF
)

TOKEN_RESPONSE=$(api_request "/projects/$PROJECT_ID/access_tokens" "POST" "$TOKEN_DATA")
PROJECT_TOKEN=$(echo "$TOKEN_RESPONSE" | jq -r '.token')
TOKEN_ID=$(echo "$TOKEN_RESPONSE" | jq -r '.id')

log_warn "CI/CD Token created: $PROJECT_TOKEN"
log_warn "Save this token! It won't be shown again."

# Configure Kubernetes clusters
log_info "Creating Kubernetes cluster configurations..."
read -p "Do you want to configure Kubernetes clusters? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Development cluster
    log_info "Configuring development cluster..."
    read -p "Enter dev cluster name: " DEV_CLUSTER
    read -p "Enter dev cluster API URL: " DEV_API_URL
    read -p "Enter dev cluster CA certificate (optional, press Enter to skip): " DEV_CA_CERT
    
    if [ -n "$DEV_API_URL" ]; then
        K8S_DATA=$(cat <<EOF
{
    "name": "$DEV_CLUSTER",
    "platform_kubernetes_attributes": {
        "api_url": "$DEV_API_URL",
        "ca_cert": "$DEV_CA_CERT",
        "namespace": "opspilot-dev",
        "project_ca_base64": ""
    }
}
EOF
)
        api_request "/projects/$PROJECT_ID/clusters/user/add" "POST" "$K8S_DATA"
        log_info "Dev cluster configured"
    fi
    
    # Staging cluster
    log_info "Configuring staging cluster..."
    read -p "Enter staging cluster name: " STAGING_CLUSTER
    read -p "Enter staging cluster API URL: " STAGING_API_URL
    read -p "Enter staging cluster CA certificate (optional): " STAGING_CA_CERT
    
    if [ -n "$STAGING_API_URL" ]; then
        K8S_DATA=$(cat <<EOF
{
    "name": "$STAGING_CLUSTER",
    "platform_kubernetes_attributes": {
        "api_url": "$STAGING_API_URL",
        "ca_cert": "$STAGING_CA_CERT",
        "namespace": "opspilot-staging",
        "project_ca_base64": ""
    }
}
EOF
)
        api_request "/projects/$PROJECT_ID/clusters/user/add" "POST" "$K8S_DATA"
        log_info "Staging cluster configured"
    fi
    
    # Production cluster
    log_info "Configuring production cluster..."
    read -p "Enter production cluster name: " PROD_CLUSTER
    read -p "Enter production cluster API URL: " PROD_API_URL
    read -p "Enter production cluster CA certificate (optional): " PROD_CA_CERT
    
    if [ -n "$PROD_API_URL" ]; then
        K8S_DATA=$(cat <<EOF
{
    "name": "$PROD_CLUSTER",
    "platform_kubernetes_attributes": {
        "api_url": "$PROD_API_URL",
        "ca_cert": "$PROD_CA_CERT",
        "namespace": "opspilot",
        "project_ca_base64": ""
    }
}
EOF
)
        api_request "/projects/$PROJECT_ID/clusters/user/add" "POST" "$K8S_DATA"
        log_info "Production cluster configured"
    fi
fi

# Create environment variables
log_info "Configuring CI/CD variables..."

# Backend variables
api_request "/projects/$PROJECT_ID/variables/BACKEND_HOST" "PUT" '{"key": "BACKEND_HOST", "value": "0.0.0.0", "protected": false}'
api_request "/projects/$PROJECT_ID/variables/BACKEND_PORT" "PUT" '{"key": "BACKEND_PORT", "value": "8000", "protected": false}'
api_request "/projects/$PROJECT_ID/variables/LOG_LEVEL" "PUT" '{"key": "LOG_LEVEL", "value": "INFO", "protected": false}'

# Frontend variables
api_request "/projects/$PROJECT_ID/variables/FRONTEND_URL" "PUT" '{"key": "FRONTEND_URL", "value": "http://localhost:8848", "protected": false}'
api_request "/project/$PROJECT_ID/variables/API_URL" "PUT" '{"key": "API_URL", "value": "http://localhost:8000", "protected": false}'

# Variables (set in GitLab UI for security)
log_warn "Please set these variables in GitLab CI/CD settings:"
echo "  DATABASE_URL - PostgreSQL connection string"
echo "  DATABASE_PASSWORD - Database password"
echo "  REDIS_URL - Redis connection string"
echo "  REDIS_PASSWORD - Redis password"
echo "  SECRET_KEY - JWT secret key"
echo "  SALT_API_KEY - Salt API key"
echo "  VAULT_TOKEN - Vault token"
echo "  SALT_API_PASSWORD - Salt API password"
echo "  EMAIL_SMTP_USERNAME - SMTP username"
echo "  EMAIL_SMTP_PASSWORD - SMTP password"

# Schedule pipeline
log_info "Setting up scheduled pipelines..."
read -p "Do you want to schedule daily builds? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    read -p "Enter build time in cron format (e.g., '0 2 * * *' for 2 AM daily): " CRON_SCHEDULE
    
    SCHEDULE_DATA=$(cat <<EOF
{
    "description": "Daily build and test",
    "cron": "$CRON_SCHEDULE",
    "cron_timezone": "UTC",
    "active": true,
    "ref": "main"
}
EOF
)
    
    api_request "/projects/$PROJECT_ID/pipeline_schedules" "POST" "$SCHEDULE_DATA")
    log_info "Pipeline schedule created"
fi

# Configure merge request templates
log_info "Configuring merge request templates..."

# Create default MR description
MR_TEMPLATE=$(cat <<'EOF'
## Description
<!-- Describe what this MR does and why it's needed -->

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing completed

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex logic
- [ ] Documentation updated
- [ ] No new warnings generated
- [ ] All tests passing
- [ ] Pipeline is green

## Related Issues
Closes #<issue_number>
EOF
)

echo "$MR_TEMPLATE" > .gitlab/merge_request_templates/default.md
git add .gitlab/merge_request_templates/default.md
git commit -m "Add merge request template" || true
git push gitlab main || true

log_info "Merge request template created"

# Create issue templates
log_info "Configuring issue templates..."

BUG_TEMPLATE=$(cat <<'EOF'
### Description
<!-- Describe the bug clearly and concisely -->

### Steps to Reproduce
1.
2.
3.

### Expected Behavior
<!-- What should happen -->

### Actual Behavior
<!-- What actually happens -->

### Environment
- Version:
- OS:
- Browser (if applicable):

### Additional Context
<!-- Any other relevant information -->
EOF
)

FEATURE_TEMPLATE=$(cat <<'EOF'
### Description
<!-- Describe the feature you would like to see -->

### Problem Statement
<!-- What problem does this feature solve? -->

### Proposed Solution
<!-- How should this feature work? -->

### Alternatives Considered
<!-- What other approaches did you consider? -->

### Additional Context
<!-- Any other relevant information -->
EOF
)

mkdir -p .gitlab/issue_templates
echo "$BUG_TEMPLATE" > .gitlab/issue_templates/Bug.md
echo "$FEATURE_TEMPLATE" > .gitlab/issue_templates/Feature.md
git add .gitlab/issue_templates/
git commit -m "Add issue templates" || true
git push gitlab main || true

log_info "Issue templates created"

# Create README
log_info "Creating project README..."
cat > README.md <<'EOF'
# OpsPilot

[![Pipeline Status](https://gitlab.com/username/opspilot/badges/main/pipeline.svg)](https://gitlab.com/username/opspilot/-/commits/main)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

OpsPilot is a comprehensive DevOps automation platform for managing servers, monitoring, and remote execution.

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Node.js 22+ (for frontend)
- Python 3.11+ (for backend)
- Git

### Development

```bash
# Clone repository
git clone git@gitlab.com:username/opspilot.git
cd opspilot

# Start infrastructure
docker-compose up -d

# Install backend dependencies
cd backend
poetry install

# Install frontend dependencies
cd ../frontend
pnpm install

# Run backend
cd ../backend
poetry run uvicorn app.main:app --reload

# Run frontend
cd frontend
pnpm dev
```

## 📖 Documentation

- [Development Guide](docs/DEVELOPMENT.md)
- [Deployment Guide](docs/DEPLOYMENT.md)
- [API Documentation](docs/API.md)
- [Architecture](docs/ARCHITECTURE.md)

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
EOF

git add README.md
git commit -m "Add project README" || true
git push gitlab main || true

log_info "Project README created"

# Summary
echo ""
log_info "=========================================="
log_info "GitLab Repository Setup Complete!"
log_info "=========================================="
echo ""
echo "Project URL: $PROJECT_URL"
echo "Project ID: $PROJECT_ID"
echo ""
log_info "Next steps:"
echo "  1. Set CI/CD variables in GitLab UI:"
echo "     Settings > CI/CD > Variables"
echo ""
echo "  2. Configure Kubernetes clusters:"
echo "     Infrastructure > Kubernetes"
echo ""
echo "  3. Run first pipeline:"
echo "     CI/CD > Pipelines > Run pipeline"
echo ""
echo "  4. Create feature branch:"
echo "     git checkout -b feature/my-feature"
echo ""
echo "  5. Push and create merge request:"
echo "     git push -u gitlab feature/my-feature"
echo ""
echo "=========================================="
