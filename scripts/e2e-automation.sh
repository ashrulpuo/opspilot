#!/usr/bin/env bash
# Full-stack E2E automation: Postgres/Redis (Docker) → migrations → empty users → FastAPI → Playwright (Chromium).
# Usage (from repo root): ./scripts/e2e-automation.sh
# Optional: E2E_HEADED=1 ./scripts/e2e-automation.sh — open a real Chromium window while tests run.
# Requires: Docker, Python 3.11+ with backend deps (uvicorn, app), pnpm in frontend.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

COMPOSE_FILE="${REPO_ROOT}/docker-compose.yml"
export DATABASE_URL="${DATABASE_URL:-postgresql+asyncpg://postgres:postgres@127.0.0.1:5438/opspilot}"
export REDIS_URL="${REDIS_URL:-redis://127.0.0.1:6384/0}"
# Dedicated port so we do not clash with a dev server on :8000; must match Vite (see playwright.config E2E_AUTOMATION webServer).
E2E_BACKEND_PORT="${E2E_BACKEND_PORT:-8010}"
export E2E_API_URL="${E2E_API_URL:-http://127.0.0.1:${E2E_BACKEND_PORT}}"
export VITE_API_URL="${VITE_API_URL:-$E2E_API_URL}"
# Isolate Vite from a dev server usually bound to 8848 (must match playwright.config e2eFrontendOrigin).
export E2E_VITE_PORT="${E2E_VITE_PORT:-8858}"
export VITE_PORT="${VITE_PORT:-$E2E_VITE_PORT}"
export E2E_AUTOMATION="${E2E_AUTOMATION:-1}"
export E2E_WAIT_FOR_API="${E2E_WAIT_FOR_API:-1}"

if ! command -v docker >/dev/null 2>&1; then
  echo "Error: docker not found. Install Docker to run stack services."
  exit 1
fi

if [[ "${SKIP_DOCKER:-0}" != "1" ]]; then
  echo "==> Starting Postgres & Redis (docker compose)..."
  docker compose -f "$COMPOSE_FILE" up -d postgres redis

  echo "==> Waiting for PostgreSQL..."
  for _ in $(seq 1 60); do
    if docker compose -f "$COMPOSE_FILE" exec -T postgres pg_isready -U postgres -d opspilot 2>/dev/null; then
      break
    fi
    sleep 1
  done
  if ! docker compose -f "$COMPOSE_FILE" exec -T postgres pg_isready -U postgres -d opspilot 2>/dev/null; then
    echo "Error: Postgres did not become ready."
    exit 1
  fi
else
  echo "==> SKIP_DOCKER=1 — assuming Postgres on 5438 and Redis on 6384 are already up."
fi

PYTHON_BIN="${PYTHON_BIN:-}"
if [[ -z "${PYTHON_BIN}" && -x "$REPO_ROOT/backend/.venv/bin/python" ]]; then
  PYTHON_BIN="$REPO_ROOT/backend/.venv/bin/python"
elif [[ -z "${PYTHON_BIN}" ]]; then
  PYTHON_BIN="python3"
fi

if ! "$PYTHON_BIN" -c "import uvicorn" 2>/dev/null; then
  echo "Error: uvicorn not importable with ${PYTHON_BIN}."
  echo "Create a venv and install backend deps:"
  echo "  cd backend && python3 -m venv .venv && .venv/bin/pip install -e '.[dev]'"
  exit 1
fi

echo "==> Alembic upgrade..."
(cd "$REPO_ROOT/backend" && "$PYTHON_BIN" -m alembic upgrade head)

echo "==> Clearing users for fresh-install API test (TRUNCATE users CASCADE)..."
if ! docker compose -f "$COMPOSE_FILE" exec -T postgres psql -U postgres -d opspilot -v ON_ERROR_STOP=1 \
  -c "TRUNCATE TABLE users CASCADE;"; then
  echo "Warning: TRUNCATE users failed; trying DELETE FROM users..."
  docker compose -f "$COMPOSE_FILE" exec -T postgres psql -U postgres -d opspilot -v ON_ERROR_STOP=1 \
    -c "DELETE FROM users;" || true
fi

echo "==> Reset installation_state so E2E sees fresh-install onboarding..."
docker compose -f "$COMPOSE_FILE" exec -T postgres psql -U postgres -d opspilot -v ON_ERROR_STOP=1 \
  -c "UPDATE installation_state SET initial_setup_completed = false, updated_at = now() WHERE id = 'default';" \
  2>/dev/null || true

if [[ "${SKIP_DOCKER:-0}" != "1" ]]; then
  echo "==> Clearing POST /auth/bootstrap rate-limit keys in Redis..."
  docker compose -f "$COMPOSE_FILE" exec -T redis redis-cli EVAL \
    "local k=redis.call('keys','bootstrap_rate:*') for i=1,#k do redis.call('del',k[i]) end return #k" 0 \
    >/dev/null 2>&1 || true
fi

BACKEND_PID=""
cleanup() {
  if [[ -n "${BACKEND_PID}" ]] && kill -0 "${BACKEND_PID}" 2>/dev/null; then
    echo "==> Stopping backend (PID ${BACKEND_PID})..."
    kill "${BACKEND_PID}" 2>/dev/null || true
    wait "${BACKEND_PID}" 2>/dev/null || true
  fi
}
trap cleanup EXIT

echo "==> Starting FastAPI on ${E2E_API_URL}..."
if command -v lsof >/dev/null 2>&1; then
  OLD_PID="$(lsof -ti:"${E2E_BACKEND_PORT}" -sTCP:LISTEN 2>/dev/null || true)"
  if [[ -n "${OLD_PID}" ]]; then
    echo "==> Freeing port ${E2E_BACKEND_PORT} (PID ${OLD_PID})..."
    kill "${OLD_PID}" 2>/dev/null || true
    sleep 1
  fi
fi

(
  cd "$REPO_ROOT/backend"
  export DATABASE_URL REDIS_URL
  # Prefer OS env over backend/.env so Playwright Vite (:8858) passes CORS even if .env lists only :8848.
  export ALLOWED_ORIGINS="${ALLOWED_ORIGINS:-[\"http://localhost:8848\",\"http://127.0.0.1:8848\",\"http://localhost:8858\",\"http://127.0.0.1:8858\",\"http://localhost:5173\",\"http://127.0.0.1:5173\",\"http://localhost:3000\",\"http://127.0.0.1:3000\"]}"
  exec "$PYTHON_BIN" -m uvicorn app.main:app --host 127.0.0.1 --port "${E2E_BACKEND_PORT}"
) &
BACKEND_PID=$!

echo "==> Waiting for backend /health (${E2E_API_URL})..."
for _ in $(seq 1 40); do
  if curl -sf "${E2E_API_URL}/health" >/dev/null; then
    echo "Backend is up."
    break
  fi
  sleep 1
done
if ! curl -sf "${E2E_API_URL}/health" >/dev/null; then
  echo "Error: Backend did not respond on ${E2E_API_URL}/health"
  exit 1
fi

echo "==> Installing Playwright Chromium (if needed)..."
(cd "$REPO_ROOT/frontend" && pnpm exec playwright install chromium)

echo "==> Running Playwright E2E (Chromium, workers=1)..."
cd "$REPO_ROOT/frontend"
export E2E_API_URL
export VITE_API_URL
export E2E_AUTOMATION
export E2E_WAIT_FOR_API

# E2E_HEADED=1 — visible Chromium (watch the test drive the UI).
# Interactive control: from frontend/ run `pnpm run test:e2e:ui` (Playwright UI) with API + Vite already up.
PW_EXTRA=(--project=chromium --workers=1)
if [[ "${E2E_HEADED:-}" == "1" ]]; then
  PW_EXTRA+=(--headed)
fi
pnpm exec playwright test "${PW_EXTRA[@]}" "$@"

echo "==> E2E automation finished."
