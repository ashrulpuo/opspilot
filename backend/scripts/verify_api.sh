#!/usr/bin/env bash
# Quick check that port :8000 (or $API_PORT) is OpsPilot FastAPI, not another process (e.g. Salt API also uses 8000).
set -euo pipefail
HOST="${1:-127.0.0.1}"
PORT="${2:-8000}"
BASE="http://${HOST}:${PORT}"

echo "==> GET ${BASE}/"
curl -sf "${BASE}/" | head -c 400 || { echo "FAIL: nothing on ${BASE}"; exit 1; }
echo ""
echo ""

if ! curl -sf "${BASE}/" | grep -q opspilot-api; then
  echo "WARNING: ${BASE}/ does not look like OpsPilot (expected JSON with service=opspilot-api)."
  echo "Another app may be bound to this port (e.g. Salt CherryPy from docker-compose.salt.yml)."
  exit 1
fi

API_PREFIX="/api/v1"
echo "==> GET ${BASE}${API_PREFIX}/health"
curl -sf "${BASE}${API_PREFIX}/health" || { echo "FAIL: ${BASE}${API_PREFIX}/health"; exit 1; }
echo ""

echo "==> OK: OpsPilot API responds. Bootstrap: POST ${BASE}${API_PREFIX}/auth/bootstrap"
exit 0
