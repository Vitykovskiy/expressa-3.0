# System Modules

## Module List

| Module | Responsibility | Owned contour | Depends on |
| --- | --- | --- | --- |
| `customer-telegram-bot` | Точка входа customer в WebApp и канал customer-уведомлений | `backend` | `backend-core`, Telegram Bot API |
| `customer-web-app` | Отрисовка customer flow: меню, товар, корзина, слот, история | `frontend` | `backend-core`, Telegram WebApp context |
| `backoffice-telegram-bot` | Точка входа backoffice-пользователей и канал напоминаний | `backend` | `backend-core`, Telegram Bot API |
| `backoffice-web-app` | Операционные экраны для `barista` и `administrator` | `frontend` | `backend-core`, Telegram WebApp context |
| `backend-core` | API и бизнес-логика меню, модификаторов, слотов, заказов, ролей и блокировок | `backend` | `postgres`, Telegram identity input |
| `notification-scheduler` | Формирование и отправка reminders/status notifications через Telegram | `backend` | `backend-core`, Telegram Bot API |
| `postgres` | Хранение доменных сущностей, статусов заказа, аудита и конфигурации | `backend` | none |
| `delivery-platform` | CI/CD, контейнеризация, test environment на VPS, merge gates, rollout | `devops` | VPS access, repository secrets |

## Relationships

| From module | To module | Relationship | Notes |
| --- | --- | --- | --- |
| `customer-web-app` | `backend-core` | HTTP API | Читает меню, корзину, слоты и историю, создает заказ |
| `backoffice-web-app` | `backend-core` | HTTP API | Работает с заказами, доступностью, меню, пользователями и настройками |
| `customer-telegram-bot` | `customer-web-app` | Telegram deep link / WebApp launch | Customer не должен заходить в flow минуя Telegram |
| `backoffice-telegram-bot` | `backoffice-web-app` | Telegram deep link / WebApp launch | Backoffice доступен через отдельный бот |
| `backend-core` | `postgres` | Persistent storage | Хранит меню, пользователей, заказы, аудит, настройки |
| `notification-scheduler` | `backend-core` | Internal service boundary | Забирает состояния заказов и правила напоминаний |
| `notification-scheduler` | `customer-telegram-bot` | Outbound Telegram message | Уведомляет customer о смене статуса |
| `notification-scheduler` | `backoffice-telegram-bot` | Outbound Telegram message | Отправляет reminder barista |
| `delivery-platform` | `customer-web-app` | Build/deploy pipeline | Собирает и публикует контейнеры в test/prod потоки |
| `delivery-platform` | `backoffice-web-app` | Build/deploy pipeline | То же для backoffice |
| `delivery-platform` | `backend-core` | Build/deploy pipeline | То же для backend и БД миграций |

## Design Notes

- Customer и backoffice split по UI-поверхностям, но используют единое backend-ядро, чтобы не дублировать доменные правила.
- Telegram identity остается внешним источником идентификатора пользователя; test environment может отключать обязательную Telegram validation через `DISABLE_TG_AUTH=true`.
- Напоминания barista не являются отдельным UI surface, но являются обязательной частью backend behavior и acceptance.
