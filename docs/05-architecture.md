# Architecture

## Purpose

This file is the structural navigation map for implementation, deployment, and testing work.

It complements the analysis package:

- `docs/analysis/` defines the target system and contracts;
- this file maps those decisions onto the actual repository structure and runtime boundaries.

## Repository Structure Map

This repository does not use FSD (`architecture.use_fsd = false`). Frontend structure is documented by application boundary and local module ownership instead.

| Area | Path | Responsibility | Owned Contour |
| --- | --- | --- | --- |
| Customer web app | `apps/customer-web/` | Telegram customer WebApp source, build scripts, UI state, contour-owned tests | `frontend` |
| Customer UI modules | `apps/customer-web/src/ui/` | Session gate, menu, product detail, cart, slot picker, order result, order history, API adapter | `frontend` |
| Customer test harness | `apps/customer-web/src/test/` | Vitest setup for frontend contour verification | `frontend` |
| Staging frontend image | `infra/staging/frontend/Dockerfile` | Builds the customer web app and serves compiled assets through nginx | `devops` |
| Staging compose stack | `infra/staging/docker-compose.yml` | Runtime wiring for postgres, backend, and customer frontend on staging | `devops` |

## Runtime Modules

Map implemented runtime modules back to the canonical analysis artifacts.

| Runtime module | Repository path | Canonical source | Notes |
| --- | --- | --- | --- |
| Customer auth gate | `apps/customer-web/src/ui/App.tsx` | `docs/analysis/ui-specification.md` | Handles loading, blocked, and auth error entry states |
| Customer menu and product detail flow | `apps/customer-web/src/ui/App.tsx` | `docs/analysis/ui-specification.md` | Covers category switch, product detail drawer, size/modifier selection |
| Customer cart and slot booking flow | `apps/customer-web/src/ui/App.tsx` | `docs/analysis/ui-specification.md`, `docs/analysis/integration-contracts.md` | Covers cart updates, slot selection, and order confirmation result |
| Customer order history | `apps/customer-web/src/ui/App.tsx` | `docs/analysis/ui-specification.md`, `docs/analysis/version-scope-and-acceptance.md` | Covers history list, detail drawer, and empty state |
| Customer API adapter | `apps/customer-web/src/ui/customerApi.ts` | `docs/analysis/integration-contracts.md` | Uses live `/api/customer/*` routes when available and falls back to a deterministic local mock store when unavailable |
| Customer mock store | `apps/customer-web/src/ui/mockData.ts` | `docs/analysis/ui-specification.md`, `docs/analysis/version-scope-and-acceptance.md` | Supports staging/QA verification before backend contour is complete |

## Contour Boundaries

- Frontend: owns only the customer WebApp in `apps/customer-web/`, including its UI state, customer API adapter, local mock fallback, and contour-owned tests. It consumes the customer contracts from `docs/analysis/ui-specification.md`, `docs/analysis/integration-contracts.md`, and `docs/analysis/version-scope-and-acceptance.md`.
- Backend: owns the `/api/customer/*` contract implementation and order/menu business logic. No backend service implementation lives under the customer frontend path.
- DevOps: owns the staging compose topology and frontend image build path that now package `apps/customer-web/` into nginx without changing the overall Stage 0 substrate.
- QA E2E: owns integrated block-level validation on staging, including Telegram-auth-disabled flows, customer ordering happy path, and required error/empty-state coverage.

## Cross-Contour Dependencies

| From contour | To contour | Dependency | Canonical contract |
| --- | --- | --- | --- |
| `frontend` | `backend` | Customer session, menu, product detail, cart, slot, and order endpoints under `/api/customer/*` | `docs/analysis/integration-contracts.md` |
| `frontend` | `devops` | Static build packaging and staging nginx serving path for `apps/customer-web/` | `docs/04-tech-stack.md` |
| `qa-e2e` | `frontend` | Customer WebApp selectors, UI states, and deterministic mock/live fallback behavior | `docs/analysis/ui-specification.md` |

## Deployment Topology

- Environments: local frontend preview, local compose stack, and the shared staging VPS environment.
- Delivery units: static customer frontend bundle from `apps/customer-web/`, placeholder/backend service container, postgres service.
- External integrations: Telegram WebApp host context, backend HTTP API under `/api`, and staging nginx reverse proxy boundaries.

## Update Rule

Update this file whenever repository structure, contour ownership, runtime module placement, or deployment topology changes.

Do not use this file to invent missing product behavior. Missing behavior belongs in `docs/analysis/`.
