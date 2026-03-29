# Tech Stack

## Current Decision Status

Status: `Stage 0 baseline selected and validated for infrastructure bootstrap`

The infrastructure stack is now explicit enough to unblock implementation. Product-facing frontend and backend implementation details may evolve in later contour tasks, but the deployment substrate is fixed.

## Candidate Stack Summary

| Area | Selected | Why | Alternatives | Risks |
| --- | --- | --- | --- | --- |
| Frontend | `nginx:1.27-alpine` static placeholder for Stage 0, later replaced by product WebApps | Lets CI/CD and VPS routing prove end-to-end delivery before feature implementation exists | Caddy, Node-based SSR placeholder | Placeholder runtime is not the final product frontend |
| Backend | `python:3.12-alpine` stdlib HTTP service for Stage 0, later replaced by product backend | Zero-dependency health/meta service keeps the bootstrap deterministic and fast | Node/Express, Go | Placeholder runtime proves delivery, not business logic |
| Data | `postgres:16-alpine` | Matches analysis requirement for primary relational storage and gives the environment a real database service from day one | PostgreSQL Debian image | Placeholder app does not yet exercise schema migrations |
| Infra | Docker Compose on Ubuntu 24.04 VPS, GitHub Actions, SSH key-based deploy | Simple, repeatable, and compatible with the provided raw VPS access | Kubernetes, Nomad, systemd-only deploy | Single-host staging is enough for MVP but not HA |

## Official Documentation And Best Practices

Record only official or primary sources for selected technologies.

Example format:

- Docker Engine / Docker Compose:
  Official docs:
  - https://docs.docker.com/engine/
  - https://docs.docker.com/compose/
  Key best practices:
  - keep services disposable and environment-driven;
  - use health checks so automation waits for real readiness instead of container start;
  - keep runtime secrets outside git and inject them via environment or secret store.
  Project conventions:
  - `infra/staging/docker-compose.yml` is the canonical Stage 0 stack;
  - runtime env file on VPS is `infra/staging/.env.runtime` and stays untracked.

- GitHub Actions:
  Official docs:
  - https://docs.github.com/actions
  Key best practices:
  - separate CI validation from deploy execution;
  - fail fast on smoke checks before attempting deployment;
  - keep deploy authentication in GitHub Secrets and avoid committing host credentials.
  Project conventions:
  - `stage0-ci.yml` owns build/smoke/e2e gates;
  - `deploy-staging.yml` owns push-to-staging autodeploy.

- PostgreSQL:
  Official docs:
  - https://www.postgresql.org/docs/
  Key best practices:
  - use dedicated runtime credentials;
  - keep persistent data in a named volume;
  - gate dependent services on health checks.
  Project conventions:
  - Stage 0 provisions PostgreSQL even before feature schema exists, so later backend tasks inherit a stable service boundary.

## Project Conventions

- Stage 0 may introduce placeholder frontend/backend containers strictly to prove delivery infrastructure; later contour implementation replaces their internals, not the deployment substrate.
- Local and CI validation use the same compose file with different env files.
- Staging deploys to `/opt/expressa-3.0` on the VPS and exposes the placeholder frontend on port `8080`.
- Telegram auth is intentionally disabled in staging bootstrap via `DISABLE_TG_AUTH=true` until real Telegram flows are implemented and secrets are replaced.
- Runtime secrets live in GitHub Secrets and in the VPS runtime env file; `.env.example` is the canonical bootstrap contract only.

## Risks

- The Stage 0 placeholder services prove delivery, not product behavior; later contour tasks must preserve the same health and deploy contract while replacing the placeholder code.
- Port `80` is already occupied on the VPS by an unrelated Caddy process, so Expressa staging publishes on `:8080` during the MVP cycle unless deploy issue `#13` deliberately changes ingress.
- Telegram bot tokens and admin IDs are placeholder staging values during Stage 0 and must be rotated to real credentials before production-like rollout.

## Review Trigger

Update this file whenever the selected stack, runtime constraints, or critical practices change.
