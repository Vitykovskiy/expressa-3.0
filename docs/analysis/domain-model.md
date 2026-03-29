# Domain Model

## Entities

| Entity | Purpose | Key fields | Rules |
| --- | --- | --- | --- |
| `User` | Единая учетная запись для всех ролей | `id`, `telegram_id`, `display_name`, `is_blocked`, `created_at` | `telegram_id` уникален; blocked user не допускается в customer/backoffice flow |
| `UserRole` | Ролевое назначение пользователя | `user_id`, `role`, `granted_at`, `granted_by` | Один пользователь может иметь `administrator` или `barista`; customer доступ возникает по факту активации customer-бота |
| `MenuCategory` | Категория customer-меню | `id`, `name`, `sort_order`, `is_active` | Скрытая категория не показывается customer |
| `Product` | Товар меню | `id`, `category_id`, `name`, `description`, `base_image`, `is_active` | Товар принадлежит категории и наследует доменные правила доступности |
| `ProductSize` | Размер напитка и цена | `id`, `product_id`, `code`, `label`, `price_rub`, `is_default` | Для напитков выбор размера обязателен; поддерживаются `S`, `M`, `L` |
| `ModifierGroup` | Группа допов/опций | `id`, `name`, `selection_mode`, `min_selected`, `max_selected`, `is_active` | Поддерживаются single/multi-select и взаимоисключающие варианты |
| `ModifierOption` | Отдельный доп | `id`, `group_id`, `name`, `price_delta_rub`, `is_free`, `is_active` | Бесплатный доп имеет `price_delta_rub = 0`; не публикуется как самостоятельный товар |
| `ProductModifierBinding` | Привязка групп допов к товару или группе товаров | `product_id/group_id`, `modifier_group_id`, `sort_order` | Один товар может иметь несколько групп допов |
| `WorkingHoursConfig` | Рабочие часы на день | `day_of_week`, `open_time`, `close_time`, `updated_by` | По умолчанию `09:00–20:00`, изменяется administrator-ом |
| `SlotPolicy` | Правила расчета слотов | `slot_step_minutes`, `slot_capacity`, `updated_by` | По умолчанию `10` минут и `5` активных заказов |
| `PickupSlot` | Вычисленный слот выдачи на дату | `date`, `start_time`, `end_time`, `capacity_total`, `capacity_used` | Доступен только в пределах текущего дня |
| `Order` | Заказ customer на выдачу | `id`, `customer_user_id`, `slot_start`, `slot_end`, `status`, `total_rub`, `created_at` | Статусы: `Created`, `Confirmed`, `Rejected`, `Ready for pickup`, `Closed` |
| `OrderItem` | Позиция заказа | `id`, `order_id`, `product_snapshot`, `size_snapshot`, `qty`, `line_total_rub` | Snapshot обязателен, чтобы история заказа не зависела от текущего меню |
| `OrderItemModifier` | Выбранный доп по позиции | `order_item_id`, `modifier_option_snapshot`, `price_delta_rub` | Хранится как snapshot выбора customer |
| `OrderStatusAudit` | Аудит ключевых переходов заказа | `order_id`, `status_from`, `status_to`, `acted_by_user_id`, `reason`, `acted_at` | При `Rejected` `reason` обязателен; `acted_by_user_id` обязателен для barista-actions |
| `ReminderJob` | Запланированное или отправленное напоминание | `id`, `order_id`, `target_user_id`, `kind`, `scheduled_at`, `sent_at` | Точная периодичность может быть конфигурируема позднее, но канал обязателен |

## Data Formats

| Format | Producer | Consumer | Notes |
| --- | --- | --- | --- |
| `CustomerSessionDto` | `backend-core` | `customer-web-app` | Содержит Telegram identity, block status и базовый профиль |
| `BackofficeSessionDto` | `backend-core` | `backoffice-web-app` | Содержит роль, display name и доступные вкладки |
| `MenuCatalogDto` | `backend-core` | `customer-web-app` | Возвращает категории, товары, размеры и доступность |
| `CartDto` | `backend-core` | `customer-web-app` | Содержит позиции корзины и суммарную стоимость |
| `PickupSlotDto` | `backend-core` | `customer-web-app` | Список доступных слотов текущего дня |
| `OrderSummaryDto` | `backend-core` | customer/backoffice | Унифицированная краткая карточка заказа |
| `OrderDetailDto` | `backend-core` | customer/backoffice | Полный состав заказа, статус, аудит, причина отказа |
| `AvailabilityToggleDto` | `backoffice-web-app` | `backend-core` | Патч на доступность товара/допа/опции |
| `TelegramStatusNotification` | `notification-scheduler` | Telegram API | Уведомляет customer об изменении статуса |
| `TelegramReminderNotification` | `notification-scheduler` | Telegram API | Напоминание barista о заказах без действия |

## Validation Rules

- Заказ не может быть создан без обязательного выбора размера для напитка.
- `Rejected` всегда требует непустую причину отказа.
- Только `administrator` может менять структуру меню, цены, рабочие часы, емкость слотов и роли пользователей.
- Только `barista` и `administrator` могут менять доступность; barista не меняет цены и структуру меню.
- Вместимость слота учитывает только заказы в статусах `Created`, `Confirmed`, `Ready for pickup`.
- История заказа хранит snapshot меню на момент оформления и не пересчитывается по актуальным ценам.
