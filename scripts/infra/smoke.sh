#!/usr/bin/env bash
set -euo pipefail

FRONTEND_URL="${1:-http://127.0.0.1:8080}"
BACKEND_URL="${2:-http://127.0.0.1:8081}"

wait_for_url() {
  local url="$1"
  local name="$2"
  for _ in $(seq 1 30); do
    if curl -fsS "$url" >/dev/null; then
      return 0
    fi
    sleep 2
  done
  echo "Timed out waiting for ${name} at ${url}" >&2
  return 1
}

wait_for_url "${FRONTEND_URL}/health" "frontend health"
wait_for_url "${BACKEND_URL}/health" "backend health"

echo "Smoke: frontend health"
curl -fsS "${FRONTEND_URL}/health" >/dev/null

echo "Smoke: backend health"
curl -fsS "${BACKEND_URL}/health" >/dev/null

echo "Smoke: backend metadata through frontend proxy"
curl -fsS "${FRONTEND_URL}/api/meta" | grep -q '"project": "expressa-stage0"'

echo "Smoke checks passed."
