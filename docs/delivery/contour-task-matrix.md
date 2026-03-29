# Contour Task Matrix

Use this file to decompose approved analysis into contour-specific execution tasks.

## Rules

- one row per task
- one task owns one contour
- one `block_delivery` row represents one integrated deliverable and acts as the parent for child implementation rows
- cross-contour work is split into linked tasks
- dependencies must reference the upstream task names or issue IDs explicitly
- deploy and e2e work are separate rows, not hidden inside implementation rows
- child implementation rows must reference their parent block task explicitly
- rows may depend on a specific bounded `system_analysis` slice and should name that slice explicitly when it is not the only analysis issue for the initiative
- when implementation is blocked by missing specification, record a linked `system_analysis` follow-up row or issue with explicit clarification scope

## Matrix

| Task | Task type | Owner contour | Parent block task | Depends on | Input artifacts | Expected result |
| --- | --- | --- | --- | --- | --- | --- |
| `Expressa v1 — стартовый бизнес-анализ (#2)` | `business_analysis` | `business-analyst` | `n/a` | `#1` | `Expressa — Требования к продукту.txt`, intake docs | Зафиксированы продуктовые рамки и создан downstream analysis issue |
| `Expressa v1 — системный анализ MVP customer/backoffice (#3)` | `system_analysis` | `system-analyst` | `n/a` | `#2` | intake docs, `docs/analysis/*`, Figma Make sources | Готов canonical analysis package и downstream task chain |
| `Expressa v1 — инфраструктура CI/CD, VPS и test environment` | `infrastructure` | `devops` | `n/a` | `#3` | `docs/09-integrations.md`, `docs/analysis/cross-cutting-concerns.md`, `docs/analysis/version-scope-and-acceptance.md` | Поднят Stage 0 prerequisite: VPS, containers, CI/CD, smoke/e2e gates |
| `Expressa v1 — блок customer order flow` | `block_delivery` | `system-analyst` | `n/a` | `#3` | `docs/analysis/user-scenarios.md`, `docs/analysis/ui-specification.md`, `docs/analysis/integration-contracts.md` | Customer flow интегрирован и готов к block-level validation |
| `Expressa v1 — customer web app` | `implementation` | `frontend` | `Expressa v1 — блок customer order flow` | `инфраструктурный prerequisite` | `docs/analysis/ui-specification.md`, `docs/analysis/integration-contracts.md`, `docs/analysis/version-scope-and-acceptance.md` | Telegram customer WebApp с menu/cart/slot/history flow |
| `Expressa v1 — customer/order backend core` | `implementation` | `backend` | `Expressa v1 — блок customer order flow` | `инфраструктурный prerequisite` | `docs/analysis/domain-model.md`, `docs/analysis/integration-contracts.md`, `docs/analysis/cross-cutting-concerns.md` | Menu, cart, slot and order APIs plus customer notifications |
| `Expressa v1 — e2e для customer order flow` | `e2e` | `qa-e2e` | `Expressa v1 — блок customer order flow` | `customer web app`, `customer/order backend core` | `docs/analysis/user-scenarios.md`, `docs/analysis/version-scope-and-acceptance.md`, `docs/analysis/ui-specification.md` | Интегрированная валидация customer потока |
| `Expressa v1 — блок backoffice operations` | `block_delivery` | `system-analyst` | `n/a` | `#3` | `docs/analysis/user-scenarios.md`, `docs/analysis/ui-specification.md`, `docs/analysis/integration-contracts.md` | Backoffice flow интегрирован и готов к block-level validation |
| `Expressa v1 — backoffice web app` | `implementation` | `frontend` | `Expressa v1 — блок backoffice operations` | `инфраструктурный prerequisite` | `docs/analysis/ui-specification.md`, `docs/analysis/integration-contracts.md`, `docs/analysis/version-scope-and-acceptance.md` | Backoffice UI с role-aware tabs и dialogs |
| `Expressa v1 — backoffice/admin backend` | `implementation` | `backend` | `Expressa v1 — блок backoffice operations` | `инфраструктурный prerequisite`, `customer/order backend core` | `docs/analysis/domain-model.md`, `docs/analysis/integration-contracts.md`, `docs/analysis/cross-cutting-concerns.md` | Order actions, availability, menu admin, users, settings, reminders |
| `Expressa v1 — e2e для backoffice operations` | `e2e` | `qa-e2e` | `Expressa v1 — блок backoffice operations` | `backoffice web app`, `backoffice/admin backend` | `docs/analysis/user-scenarios.md`, `docs/analysis/version-scope-and-acceptance.md`, `docs/analysis/ui-specification.md` | Интегрированная валидация backoffice flow |
| `Expressa v1 — deploy MVP slice` | `deploy` | `devops` | `n/a` | `инфраструктурный prerequisite`, `e2e customer order flow`, `e2e backoffice operations` | `docs/09-integrations.md`, `docs/analysis/cross-cutting-concerns.md`, deployment runbook | Rollout test/prod потока для MVP slice |
