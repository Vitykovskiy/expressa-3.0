# Integration Contracts

## API Contracts

| Contract | Producer | Consumer | Request | Response / Event | Notes |
| --- | --- | --- | --- | --- | --- |
| `GET /api/customer/session` | `backend-core` | `customer-web-app` | Header/context from Telegram WebApp; no body | `200 { userId, displayName, isBlocked, telegramId }` | При `isBlocked=true` UI должен уйти в blocked state |
| `GET /api/customer/menu` | `backend-core` | `customer-web-app` | Query: optional `categoryId` | `200 { categories[], products[] }` | Возвращает только активные и доступные позиции |
| `GET /api/customer/products/{productId}` | `backend-core` | `customer-web-app` | Path `productId` | `200 { product, sizes[], modifierGroups[] }` | Используется экраном настройки товара |
| `GET /api/customer/cart` | `backend-core` | `customer-web-app` | Session user | `200 { items[], subtotalRub, totalRub }` | Корзина привязана к customer session |
| `POST /api/customer/cart/items` | `customer-web-app` | `backend-core` | `{ productId, sizeCode, qty, modifierOptionIds[] }` | `201 { cartItemId, cart }` | Сервер валидирует обязательный размер и допустимость модификаторов |
| `PATCH /api/customer/cart/items/{cartItemId}` | `customer-web-app` | `backend-core` | `{ qty?, sizeCode?, modifierOptionIds? }` | `200 { cart }` | Недоступный товар возвращает ошибку доменной валидации |
| `DELETE /api/customer/cart/items/{cartItemId}` | `customer-web-app` | `backend-core` | Path `cartItemId` | `204` | После удаления UI пересчитывает totals |
| `GET /api/customer/slots` | `backend-core` | `customer-web-app` | Query `{ date=today }` | `200 { slots[{ start, end, capacityLeft, isAvailable }] }` | Для v1 разрешен только текущий день |
| `POST /api/customer/orders` | `customer-web-app` | `backend-core` | `{ slotStart, cartVersion }` | `201 { orderId, status, slotStart, totalRub }` | Успешный заказ получает статус `Created` |
| `GET /api/customer/orders` | `backend-core` | `customer-web-app` | Session user | `200 { orders[] }` | Список истории заказов |
| `GET /api/customer/orders/{orderId}` | `backend-core` | `customer-web-app` | Path `orderId` | `200 { order, items[], statusHistory[] }` | При `Rejected` возвращает `rejectReason` |
| `GET /api/backoffice/session` | `backend-core` | `backoffice-web-app` | Telegram context | `200 { userId, displayName, role, allowedTabs[] }` | Определяет ролевую навигацию |
| `GET /api/backoffice/orders` | `backend-core` | `backoffice-web-app` | Query `{ status?, slotStartFrom?, page? }` | `200 { orders[], counters }` | Вкладка заказов и фильтры |
| `POST /api/backoffice/orders/{orderId}/confirm` | `backoffice-web-app` | `backend-core` | `{ actedAt? }` | `200 { orderId, status='Confirmed' }` | Только `barista` или `administrator` |
| `POST /api/backoffice/orders/{orderId}/reject` | `backoffice-web-app` | `backend-core` | `{ reason }` | `200 { orderId, status='Rejected', reason }` | `reason` обязателен |
| `POST /api/backoffice/orders/{orderId}/ready` | `backoffice-web-app` | `backend-core` | `{ actedAt? }` | `200 { orderId, status='Ready for pickup' }` | Переход возможен только из `Confirmed` |
| `POST /api/backoffice/orders/{orderId}/close` | `backoffice-web-app` | `backend-core` | `{ actedAt? }` | `200 { orderId, status='Closed' }` | Переход возможен только из `Ready for pickup` |
| `GET /api/backoffice/availability` | `backend-core` | `backoffice-web-app` | Query `{ type?, search? }` | `200 { entities[] }` | Возвращает товары, группы, опции и допы |
| `PATCH /api/backoffice/availability/{entityType}/{entityId}` | `backoffice-web-app` | `backend-core` | `{ isActive }` | `200 { entityId, isActive }` | Barista не меняет цену и структуру |
| `GET /api/backoffice/menu` | `backend-core` | `backoffice-web-app` | none | `200 { categories[], products[], modifierGroups[] }` | Только для `administrator` |
| `POST /api/backoffice/menu/categories` | `backoffice-web-app` | `backend-core` | `{ name, sortOrder }` | `201 { category }` | Только `administrator` |
| `PATCH /api/backoffice/menu/categories/{id}` | `backoffice-web-app` | `backend-core` | `{ name?, sortOrder?, isActive? }` | `200 { category }` | Только `administrator` |
| `POST /api/backoffice/menu/products` | `backoffice-web-app` | `backend-core` | `{ categoryId, name, description, sizes[], modifierGroupIds[] }` | `201 { product }` | Размеры и цены передаются явно |
| `PATCH /api/backoffice/menu/products/{id}` | `backoffice-web-app` | `backend-core` | `{ name?, description?, sizes?, modifierGroupIds?, isActive? }` | `200 { product }` | Только `administrator` |
| `GET /api/backoffice/users` | `backend-core` | `backoffice-web-app` | Query `{ search? }` | `200 { users[] }` | Отображает роли и блокировку |
| `PATCH /api/backoffice/users/{id}/role` | `backoffice-web-app` | `backend-core` | `{ role: 'barista' | 'customer' | 'administrator' }` | `200 { user }` | Назначение ролей только administrator-ом |
| `PATCH /api/backoffice/users/{id}/block` | `backoffice-web-app` | `backend-core` | `{ isBlocked }` | `200 { user }` | Blocked user не проходит в интерфейс |
| `GET /api/backoffice/settings` | `backend-core` | `backoffice-web-app` | none | `200 { workingHours, slotStepMinutes, slotCapacity }` | Только `administrator` |
| `PATCH /api/backoffice/settings` | `backoffice-web-app` | `backend-core` | `{ openTime?, closeTime?, slotCapacity? }` | `200 { settings }` | В v1 изменяются часы и емкость; шаг слота зафиксирован 10 минут |

## Event Contracts

| Event | Producer | Consumer | Payload | Notes |
| --- | --- | --- | --- | --- |
| `order.status.changed` | `backend-core` | `notification-scheduler` | `{ orderId, customerTelegramId, status, rejectReason?, changedByUserId }` | Триггерит customer notification |
| `order.requires.barista-action` | `backend-core` | `notification-scheduler` | `{ orderId, status, slotStart, assigneeRole='barista' }` | Используется для reminder logic |
| `telegram.customer.notification` | `notification-scheduler` | Telegram Bot API | `{ telegramId, message, deepLink? }` | Текст зависит от нового статуса заказа |
| `telegram.barista.reminder` | `notification-scheduler` | Telegram Bot API | `{ telegramId, message, orderIds[] }` | Частота напоминаний может быть конфигурируема позднее, но отправка обязательна |

## External Integrations

| Integration | Purpose | Contract reference | Failure handling |
| --- | --- | --- | --- |
| `Telegram WebApp` | Identity context и запуск UI | `GET /api/customer/session`, `GET /api/backoffice/session` | Если context отсутствует в prod, доступ отклоняется; в test env допускается `DISABLE_TG_AUTH=true` |
| `Telegram Bot API` | Customer notifications и barista reminders | Event contracts above | Ошибки отправки логируются и подлежат retry |
| `PostgreSQL` | Primary system storage | Domain model entities | Ошибка миграции или соединения блокирует startup |
| `VPS container runtime` | Test/prod окружение | Delivery-platform pipeline contract | Ошибки deploy блокируют merge/release gates |

## Rule

Implementation contours must consume or produce contracts from this file. If a required contract is missing, return to `analysis`.
