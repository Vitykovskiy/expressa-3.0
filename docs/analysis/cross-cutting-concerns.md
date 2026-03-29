# Cross-Cutting Concerns

## Concerns

| Concern | Requirement | Affected contours | Notes |
| --- | --- | --- | --- |
| `Telegram identity` | Prod flow требует Telegram-based вход для customer и backoffice | `frontend`, `backend`, `qa-e2e` | В test env допускается `DISABLE_TG_AUTH=true` |
| `Role-based access` | Вкладки и API действия должны фильтроваться по роли | `frontend`, `backend`, `qa-e2e` | `barista` не меняет цены, роли и рабочие часы |
| `Blocked users` | Заблокированный пользователь не может пользоваться продуктом | `frontend`, `backend`, `qa-e2e` | Требуется явный blocked state |
| `Auditability` | Система хранит исполнителя подтверждения, готовности и отказа | `backend`, `qa-e2e` | Причина отказа обязательна |
| `Slot consistency` | Расчет свободных слотов должен быть серверным и идемпотентным | `backend`, `frontend`, `qa-e2e` | Повторная валидация на order creation обязательна |
| `Currency and totals` | Все суммы в рублях, округление до целых | `backend`, `frontend`, `qa-e2e` | Snapshot totals в заказе не пересчитываются задним числом |
| `Operational notifications` | Customer получает status notifications, barista получает reminders | `backend`, `qa-e2e` | Telegram Bot API считается обязательной интеграцией |
| `Environment parity` | Каждый push поднимает/обновляет test environment на VPS | `devops`, `qa-e2e` | Контейнеры БД, frontend и backend обязательны |
| `Merge gates` | Build, smoke и e2e обязательны для merge | `devops` | Stage 0 prerequisite перед implementation start |
| `Documentation as source of truth` | Delivery опирается на docs, а не на устные договоренности | `all` | Любой specification gap возвращается в `system_analysis` |

## Shared Rules

- Telegram WebApp context обязателен в prod и может быть отключен только для test environment через `DISABLE_TG_AUTH=true`.
- Backend является источником истины для ролей, доступности, слотов и статусов заказа.
- Frontend не должен хардкодить ролевые права сверх того, что пришло из session contract.
- Все статусные переходы заказа логируются и должны быть воспроизводимы для QA.
- Любой отказ в критической операции должен возвращать machine-readable причину и user-facing сообщение.

## Operational Notes

- Инфраструктурный prerequisite должен подготовить VPS, контейнеры, pipeline и test secrets до старта implementation issues.
- Smoke test обязан покрыть startup на пустой БД, seeding, customer order flow и базовую barista-обработку заказа.
- Deployment поток должен разделять test environment и production-mode rollout.
