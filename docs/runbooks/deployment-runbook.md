# Deployment Runbook

## Environment

- Environment name: `staging`
- Environment URL: `http://216.57.105.133:8080`
- Deployment entrypoint: `.github/workflows/deploy-staging.yml` -> `scripts/infra/deploy-staging.sh`
- Owners: `devops`

## Prerequisites

- Required approvals: `none` while `pull_requests.enabled = false`; direct push to `main` is the configured delivery path
- Required completed tasks: `#4` for Stage 0 bootstrap, later `#13` for rollout beyond infrastructure baseline
- Required secrets or variables: `VPS_HOST`, `VPS_USER`, `VPS_PORT`, `VPS_SSH_PRIVATE_KEY`, `STAGING_*`, `TARGET_URL`
- Required database or infrastructure state: Docker Engine and Docker Compose installed on the VPS, SSH key added to `authorized_keys`, target port `8080` reachable

## Rollout Steps

1. GitHub Actions runs `Stage 0 CI` and proves that the compose stack builds and passes smoke/e2e checks.
2. On successful push to `main`, `deploy-staging.yml` connects to the VPS over SSH, updates `/opt/expressa-3.0`, writes `infra/staging/.env.runtime`, and runs `bash scripts/infra/deploy-staging.sh`.
3. Remote deploy rebuilds the compose stack and starts `postgres`, `backend`, and `frontend` containers.
4. The workflow verifies local VPS health endpoints and then runs the public `scripts/infra/e2e.sh` check against `TARGET_URL`.

## Verification

- Health checks:
  - `curl -fsS http://127.0.0.1:8080/health`
  - `curl -fsS http://127.0.0.1:8080/api/health`
  - `docker compose -f infra/staging/docker-compose.yml --env-file infra/staging/.env.runtime ps`
- Smoke checks:
  - `bash scripts/infra/smoke.sh http://127.0.0.1:8080 http://127.0.0.1:8081`
  - `bash scripts/infra/e2e.sh http://216.57.105.133:8080`
- Monitoring evidence location: GitHub Actions run logs and `docker compose logs` on the VPS

## Rollback

- Rollback trigger: public e2e check fails after deploy, or compose services fail to reach healthy state
- Rollback steps:
  1. SSH to the VPS.
  2. `cd /opt/expressa-3.0`
  3. `git log --oneline -n 5` to select the last known good commit.
  4. `git checkout <good-commit>`
  5. `docker compose -f infra/staging/docker-compose.yml --env-file infra/staging/.env.runtime up -d --build`
- Data recovery notes: PostgreSQL data lives in the `postgres-data` named volume; Stage 0 placeholder services do not apply schema migrations yet

## Evidence

- Deployment result location: GitHub Actions `Deploy Staging` workflow run and live target URL `http://216.57.105.133:8080`
- Change record: issue `#4`, telemetry `.agent-work/telemetry/20260329-225342.jsonl`, git history on `main`
- Follow-up issues: `#7`, `#8`, `#10`, `#11`, `#13`
