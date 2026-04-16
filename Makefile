# OpsPilot Makefile
# Common commands for development and testing

.PHONY: help install test test-unit test-integration test-e2e test-e2e-automation coverage lint security-scan clean dev gitlab-setup gitlab-pipeline gitlab-pipeline-dry gitlab-branch gitlab-mr gitlab-status salt-up salt-down salt-keys salt-accept

# Default target
help:
	@echo "OpsPilot - Makefile commands:"
	@echo ""
	@echo "Development:"
	@echo "  make install          - Install dependencies"
	@echo "  make dev              - Start development server"
	@echo "  make dev-frontend     - Start frontend development server"
	@echo "  make dev-backend      - Start backend development server"
	@echo ""
	@echo "Testing:"
	@echo "  make test             - Run all tests"
	@echo "  make test-unit        - Run unit tests"
	@echo "  make test-integration - Run integration tests"
	@echo "  make test-e2e        - Run E2E tests (frontend)"
	@echo "  make test-e2e-automation - Full stack E2E (Docker DB, API, Playwright)"
	@echo ""
	@echo "Quality:"
	@echo "  make coverage         - Run tests with coverage report"
	@echo "  make lint             - Run linter checks"
	@echo "  make security-scan    - Run security scan"
	@echo ""
	@echo "SaltStack:"
	@echo "  make salt-up          - Start Salt Master"
	@echo "  make salt-down        - Stop Salt Master"
	@echo "  make salt-logs        - Show Salt Master logs"
	@echo "  make salt-keys        - List Salt keys"
	@echo "  make salt-accept      - Accept all pending minion keys"
	@echo "  make salt-accept-minion - Accept specific minion"
	@echo "  make salt-test        - Ping all minions"
	@echo "  make salt-grains      - Get grains from all minions"
	@echo "  make salt-install-minion - Install Salt Minion on remote server"
	@echo "  make salt-run-state   - Run state on minion(s)"
	@echo "  make salt-cmd         - Run command on minion(s)"
	@echo ""
	@echo "Maintenance:"
	@echo "  make clean            - Clean build artifacts"
	@echo "  make db-migrate       - Run database migrations"
	@echo "  make db-upgrade       - Upgrade database to latest migration"
	@echo "  make db-downgrade     - Downgrade database by one migration"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-up        - Start all Docker containers"
	@echo "  make docker-down      - Stop all Docker containers"
	@echo "  make docker-logs      - Show Docker logs"
	@echo ""
	@echo "GitLab:"
	@echo "  make gitlab-setup     - Set up GitLab repository"
	@echo "  make gitlab-pipeline  - Trigger GitLab pipeline"
	@echo "  make gitlab-branch    - Create feature branch"
	@echo "  make gitlab-mr        - Create merge request"
	@echo "  make gitlab-status    - Show GitLab status"
	@echo ""
	@echo "Kubernetes:"
	@echo "  make k8s-deploy      - Deploy to Kubernetes"
	@echo "  make k8s-deploy-dev  - Deploy to dev namespace"
	@echo "  make k8s-logs        - Show all K8s logs"
	@echo "  make k8s-logs-backend - Show backend logs"
	@echo "  make k8s-logs-frontend - Show frontend logs"
	@echo "  make k8s-status      - Show cluster status"
	@echo "  make k8s-scale       - Scale deployments"
	@echo "  make k8s-rollback    - Rollback deployment"
	@echo "  make k8s-restart     - Restart deployments"
	@echo ""

# ============================================
# Development
# ============================================

install:
	@echo "Installing dependencies..."
	@cd backend && pip install -e ".[dev]"
	@cd frontend && npm install
	@echo "✅ Dependencies installed"

dev:
	@echo "Starting development servers..."
	@make dev-backend & make dev-frontend

dev-backend:
	@echo "Starting backend server..."
	@cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend:
	@echo "Starting frontend server..."
	@cd frontend && npm run dev

# ============================================
# Testing
# ============================================

test:
	@echo "Running all tests..."
	@cd backend && pytest tests/ -v

test-unit:
	@echo "Running unit tests..."
	@cd backend && pytest tests/unit/ -v -m unit

test-integration:
	@echo "Running integration tests..."
	@cd backend && pytest tests/integration/ -v -m integration

test-e2e:
	@echo "Running E2E tests..."
	@cd frontend && pnpm run test:e2e

test-e2e-automation:
	@echo "Running full-stack E2E automation (see scripts/e2e-automation.sh)..."
	@chmod +x scripts/e2e-automation.sh
	@./scripts/e2e-automation.sh

# ============================================
# Quality
# ============================================

coverage:
	@echo "Running tests with coverage..."
	@cd backend && pytest --cov=app --cov-report=html --cov-report=term tests/
	@echo "Coverage report generated: backend/htmlcov/index.html"

lint:
	@echo "Running linter checks..."
	@cd backend && ruff check .
	@cd frontend && npm run lint
	@echo "✅ Lint checks complete"

security-scan:
	@echo "Running security scan..."
	@bash scripts/security-scan.sh

# ============================================
# Database
# ============================================

db-migrate:
	@echo "Creating new migration..."
	@cd backend && alembic revision --autogenerate -m "$(MSG)"

db-upgrade:
	@echo "Upgrading database..."
	@cd backend && alembic upgrade head

db-downgrade:
	@echo "Downgrading database..."
	@cd backend && alembic downgrade -1

# ============================================
# Maintenance
# ============================================

clean:
	@echo "Cleaning build artifacts..."
	@cd backend && rm -rf __pycache__ .pytest_cache htmlcov .coverage
	@cd frontend && rm -rf dist node_modules/.vite
	@echo "✅ Clean complete"

# ============================================
# Docker
# ============================================

docker-build:
	@echo "Building Docker images..."
	@docker-compose build

docker-up:
	@echo "Starting Docker containers..."
	@docker-compose up -d

docker-down:
	@echo "Stopping Docker containers..."
	@docker-compose down

docker-logs:
	@echo "Showing Docker logs..."
	@docker-compose logs -f

# ============================================
# GitLab
# ============================================

gitlab-setup:
	@echo "Setting up GitLab repository..."
	@bash scripts/gitlab-setup.sh

gitlab-pipeline:
	@echo "Triggering GitLab pipeline..."
	@git push gitlab HEAD

gitlab-pipeline-dry:
	@echo "Running dry-run pipeline..."
	@git push gitlab --dry-run HEAD

gitlab-branch:
	@echo "Creating feature branch..."
	@read -p "Branch name: " BRANCH && \
	git checkout -b feature/$$BRANCH && \
	git push -u gitlab feature/$$BRANCH

gitlab-mr:
	@echo "Creating merge request..."
	@read -p "Target branch (main/develop): " TARGET && \
	TARGET=$${TARGET:-main} && \
	git push -u gitlab HEAD && \
	git request-pull $$TARGET -m "$(git log -1 --pretty=%B)"

gitlab-status:
	@echo "GitLab status:"
	@echo ""
	@echo "  Branches:"
	@git branch -a
	@echo ""
	@echo "  Remotes:"
	@git remote -v

# ============================================
# Kubernetes
# ============================================

k8s-deploy:
	@echo "Deploying to Kubernetes..."
	@bash scripts/k8s-deploy.sh

k8s-deploy-dev:
	@echo "Deploying to dev namespace..."
	@bash scripts/k8s-deploy.sh opspilot-dev development

k8s-logs:
	@echo "Showing Kubernetes logs..."
	@kubectl logs -f -n opspilot -l app=opspilot --all-containers=true

k8s-logs-backend:
	@echo "Showing backend logs..."
	@kubectl logs -f -n opspilot -l app=opspilot,tier=backend

k8s-logs-frontend:
	@echo "Showing frontend logs..."
	@kubectl logs -f -n opspilot -l app=opspilot,tier=frontend

k8s-status:
	@echo "Kubernetes cluster status:"
	@echo ""
	@echo "Pods:"
	@kubectl get pods -n opspilot
	@echo ""
	@echo "Services:"
	@kubectl get services -n opspilot
	@echo ""
	@echo "Ingress:"
	@kubectl get ingress -n opspilot

k8s-scale:
	@echo "Scaling deployments..."
	@read -p "Deployment (backend/frontend): " DEPLOYMENT && \
	read -p "Replicas: " REPLICAS && \
	kubectl scale deployment opspilot-$$DEPLOYMENT -n opspilot --replicas=$$REPLICAS

k8s-rollback:
	@echo "Rolling back deployment..."
	@read -p "Deployment (backend/frontend): " DEPLOYMENT && \
	kubectl rollout undo deployment/opspilot-$$DEPLOYMENT -n opspilot

k8s-restart:
	@echo "Restarting deployments..."
	@kubectl rollout restart deployment/opspilot-backend -n opspilot
	@kubectl rollout restart deployment/opspilot-frontend -n opspilot

# ============================================
# Production
# ============================================

# ============================================
# SaltStack
# ============================================

salt-up:
	@echo "Starting Salt Master..."
	@docker-compose -f docker-compose.salt.yml up -d

salt-down:
	@echo "Stopping Salt Master..."
	@docker-compose -f docker-compose.salt.yml down

salt-logs:
	@echo "Showing Salt Master logs..."
	@docker-compose -f docker-compose.salt.yml logs -f

salt-keys:
	@echo "Listing Salt keys..."
	@docker-compose -f docker-compose.salt.yml exec salt-master salt-key -L

salt-accept:
	@echo "Accepting all pending keys..."
	@docker-compose -f docker-compose.salt.yml exec salt-master salt-key -A

salt-accept-minion:
	@echo "Accepting specific minion..."
	@read -p "Enter minion ID: " MINION_ID && docker-compose -f docker-compose.salt.yml exec salt-master salt-key -a $$MINION_ID

salt-test:
	@echo "Pinging all minions..."
	@docker-compose -f docker-compose.salt.yml exec salt-master salt '*' test.ping

salt-grains:
	@echo "Getting grains from all minions..."
	@docker-compose -f docker-compose.salt.yml exec salt-master salt '*' grains.items

salt-install-minion:
	@echo "Installing Salt Minion on remote server..."
	@read -p "Server IP: " SERVER_IP && \
	read -p "SSH User (root): " SSH_USER && \
	SSH_USER=$${SSH_USER:-root} && \
	read -sp "SSH Password: " SSH_PASSWORD && echo && \
	read -p "Minion ID: " MINION_ID && \
	read -p "Salt Master IP (optional): " MASTER_IP && \
	bash scripts/install-salt-minion.sh "$$SERVER_IP" "$$SSH_USER" "$$SSH_PASSWORD" "$$MINION_ID" "$$MASTER_IP"

salt-run-state:
	@echo "Running state on minion..."
	@read -p "Target minion (* for all): " TARGET && \
	read -p "State to apply: " STATE && \
	docker-compose -f docker-compose.salt.yml exec salt-master salt "$$TARGET" state.apply "$$STATE"

salt-cmd:
	@echo "Running command on minion..."
	@read -p "Target minion (* for all): " TARGET && \
	read -p "Command to run: " CMD && \
	docker-compose -f docker-compose.salt.yml exec salt-master salt "$$TARGET" cmd.run "$$CMD"

# Production
# ============================================

prod-build:
	@echo "Building for production..."
	@cd backend && pip install -e .
	@cd frontend && npm run build

prod-start:
	@echo "Starting production servers..."
	@docker-compose -f docker-compose.prod.yml up -d

prod-deploy:
	@echo "Deploying to production..."
	@kubectl apply -f infrastructure/kubernetes/
	@kubectl rollout restart deployment/opspilot-backend
	@kubectl rollout restart deployment/opspilot-frontend
