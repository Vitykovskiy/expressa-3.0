# Tech Stack

## Current Decision Status

Status: `Customer frontend implementation selected on top of the validated Stage 0 substrate`

The deployment substrate from Stage 0 remains fixed. The customer-facing WebApp is now implemented as a dedicated React/Vite application that is built into static assets and served by the existing nginx frontend container.

## Candidate Stack Summary

| Area | Selected | Why | Alternatives | Risks |
| --- | --- | --- | --- | --- |
| Frontend | `React 18 + TypeScript + Vite 6`, built in `node:24-alpine` and served by `nginx:1.27-alpine` | Matches the Telegram WebApp interaction model, keeps the runtime static and simple, and reuses the validated Stage 0 ingress/container contract | SSR, Next.js, pure static placeholder | Until backend issue `#8` lands, the customer app must tolerate missing live endpoints |
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

- React:
  Official docs:
  - https://react.dev/
  Key best practices:
  - keep UI state localized to the customer app boundary;
  - drive view state from API/session contracts instead of ad hoc DOM mutations;
  - cover critical customer flows with automated UI tests.
  Project conventions:
  - `apps/customer-web/` is the customer Telegram WebApp implementation;
  - loading, error, blocked, and empty states are first-class surfaces, not incidental fallbacks.

- Vite:
  Official docs:
  - https://vite.dev/guide/
  Key best practices:
  - keep the app as a static build artifact behind nginx;
  - use the same source tree for local preview, CI build, and staging image build;
  - keep test/build scripts inside the app package for contour-owned validation.
  Project conventions:
  - the frontend image builds from `apps/customer-web/`;
  - `npm run build` is the canonical customer frontend artifact build.

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

- Stage 0 introduced placeholder containers to prove delivery infrastructure; the customer frontend has now replaced the placeholder frontend internals without changing the deployment substrate.
- Local and CI validation use the same compose file with different env files.
- Staging deploys to `/opt/expressa-3.0` on the VPS and exposes the customer frontend on port `8080`.
- Telegram auth is intentionally disabled in staging bootstrap via `DISABLE_TG_AUTH=true` until real Telegram flows are implemented and secrets are replaced.
- Runtime secrets live in GitHub Secrets and in the VPS runtime env file; `.env.example` is the canonical bootstrap contract only.
- The customer frontend must stay compatible with a partially implemented backend by providing deterministic blocked/error/mock behavior for QA and staging verification.

## Risks

- The backend is still ahead-of-contract for customer APIs until issue `#8` lands, so the customer frontend currently needs an explicit live-to-mock fallback path for staging and QA.
- Port `80` is already occupied on the VPS by an unrelated Caddy process, so Expressa staging publishes on `:8080` during the MVP cycle unless deploy issue `#13` deliberately changes ingress.
- Telegram bot tokens and admin IDs are placeholder staging values during Stage 0 and must be rotated to real credentials before production-like rollout.

## Review Trigger

Update this file whenever the selected stack, runtime constraints, or critical practices change.
