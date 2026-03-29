# Architecture

## Purpose

This file is the structural navigation map for implementation, deployment, and testing work.

It complements the analysis package:

- `docs/analysis/` defines the target system and contracts;
- this file maps those decisions onto the actual repository structure and runtime boundaries.

## Repository Structure Map

Record the main applications, packages, services, and infrastructure areas before delivery starts.

If `.ai-dev-template.config.json` sets `architecture.use_fsd` to `true`, describe frontend areas in terms of FSD layers and record the intended boundaries in this file. If it is `false`, document the alternative frontend structure explicitly for later sessions.

| Area | Path | Responsibility | Owned Contour |
| --- | --- | --- | --- |
| `<app/package/service>` | `<path>` | `<responsibility>` | `<frontend/backend/devops/etc.>` |

## Runtime Modules

Map implemented runtime modules back to the canonical analysis artifacts.

| Runtime module | Repository path | Canonical source | Notes |
| --- | --- | --- | --- |
| `<module>` | `<path>` | `docs/analysis/<file>.md` | `<notes>` |

## Contour Boundaries

- Frontend: `<owned modules, UI surfaces, consumed contracts>`
- Backend: `<owned modules, domain services, produced contracts>`
- DevOps: `<owned environments, pipelines, runtime infrastructure>`
- QA E2E: `<owned suites, test environments, validation surfaces>`

## Cross-Contour Dependencies

| From contour | To contour | Dependency | Canonical contract |
| --- | --- | --- | --- |
| `<frontend>` | `<backend>` | `<dependency>` | `docs/analysis/integration-contracts.md` |

## Deployment Topology

- Environments: `<local/staging/prod/etc.>`
- Delivery units: `<apps/services/jobs>`
- External integrations: `<systems and boundaries>`

## Update Rule

Update this file whenever repository structure, contour ownership, runtime module placement, or deployment topology changes.

Do not use this file to invent missing product behavior. Missing behavior belongs in `docs/analysis/`.
