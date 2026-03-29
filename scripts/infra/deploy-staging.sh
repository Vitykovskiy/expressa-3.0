#!/usr/bin/env bash
set -euo pipefail

DEPLOY_PATH="${DEPLOY_PATH:-/opt/expressa-3.0}"
REPO_URL="${REPO_URL:-https://github.com/Vitykovskiy/expressa-3.0.git}"
BRANCH="${BRANCH:-main}"
COMPOSE_FILE="${COMPOSE_FILE:-infra/staging/docker-compose.yml}"
ENV_FILE="${ENV_FILE:-infra/staging/.env.runtime}"

mkdir -p "$(dirname "$DEPLOY_PATH")"

if [ ! -d "${DEPLOY_PATH}/.git" ]; then
  git clone --branch "$BRANCH" "$REPO_URL" "$DEPLOY_PATH"
fi

cd "$DEPLOY_PATH"
git fetch origin "$BRANCH"
git checkout "$BRANCH"
git pull --ff-only origin "$BRANCH"

test -f "$ENV_FILE"

docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d --build
docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" ps
