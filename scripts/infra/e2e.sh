#!/usr/bin/env bash
set -euo pipefail

TARGET_URL="${1:-http://127.0.0.1:8080}"

wait_for_url() {
  local url="$1"
  for _ in $(seq 1 30); do
    if curl -fsS "$url" >/dev/null; then
      return 0
    fi
    sleep 2
  done
  echo "Timed out waiting for ${url}" >&2
  return 1
}

wait_for_url "${TARGET_URL}/health"

echo "E2E: customer surface"
curl -fsS "${TARGET_URL}/" | grep -q "Expressa Customer"

echo "E2E: backoffice surface"
curl -fsS "${TARGET_URL}/backoffice/" | grep -q "Expressa Backoffice"

echo "E2E: proxied API health"
curl -fsS "${TARGET_URL}/api/health" | grep -q '"status": "ok"'

echo "E2E: metadata contract"
curl -fsS "${TARGET_URL}/api/meta" | grep -q '"telegramAuthDisabled": true'

echo "E2E: customer session contract"
curl -fsS "${TARGET_URL}/api/customer/session" | grep -q '"userId":'

echo "E2E: backoffice session contract"
curl -fsS "${TARGET_URL}/api/backoffice/session" | grep -q '"allowedTabs":'

echo "Staging e2e checks passed."
