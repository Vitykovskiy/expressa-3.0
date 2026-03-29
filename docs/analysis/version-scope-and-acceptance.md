# Version Scope And Acceptance

## Bounded Slice

Этот analysis slice фиксирует весь MVP Expressa v1 как две интегрируемые delivery-области:

1. `Customer order flow`:
   menu -> product configuration -> cart -> slot -> order creation -> order history.
2. `Backoffice operations flow`:
   queue -> confirm/reject -> ready -> close -> availability -> menu management -> users -> settings.

Обе delivery-области используют общие backend-модули, Telegram identity и один инфраструктурный prerequisite.

## Граница версии

### В Scope

- Telegram-центричный customer flow для заказа на выдачу.
- Customer web-interface внутри Telegram.
- Единый backoffice для `barista` и `administrator`.
- Отдельный Telegram-бот для доступа в backoffice.
- Каталог с размерами напитков, группами допов, бесплатными допами и взаимоисключающими опциями.
- Слоты только на текущий день с шагом 10 минут.
- История заказов и Telegram-уведомления о смене статусов.
- Управление меню, ценами, рабочими часами, лимитами слотов, назначением barista и блокировкой пользователей.

### Вне Scope

- Онлайн-оплата.
- Акции, скидки, бонусные механики и купоны.
- Многодневный горизонт слотов.
- Продвинутая аналитика и отчетные панели.
- Свободные модификаторы вне фиксированной модели допов.

## Explicitly Synthesized States

Figma Make references покрывают screen inventory, но не все edge states читаются как отдельные финальные макеты. Для implementation readiness эти состояния считаются синтезированными на основе product requirements и обязательны к реализации:

- экран/баннер blocked access для заблокированного пользователя;
- empty state истории заказов;
- empty state очереди заказов;
- error state отсутствия доступных слотов;
- validation state обязательного выбора размера;
- rejection flow с обязательной причиной отказа;
- loading/skeleton state для customer- и backoffice-экранов при первичной загрузке.

## Критерии приемки

| Критерий | Source scenario | How to validate |
| --- | --- | --- |
| Customer может просмотреть меню, настроить товар, добавить его в корзину и создать заказ | `CU-01` | Пройти путь menu -> product configuration -> cart -> slot selection -> order creation |
| Customer видит историю заказов и причину отказа при `Rejected` | `CU-02` | Проверить populated и empty state истории |
| Barista может подтвердить, отклонить, перевести в `Ready for pickup` и закрыть заказ | `BO-01` | Пройти путь queue -> confirm/reject -> ready -> close |
| Barista может временно менять доступность без изменения структуры меню | `BO-02` | Проверить вкладку availability и отражение в customer menu |
| Administrator может управлять меню, слотами, рабочими часами и блокировкой пользователей | `AD-01`, `AD-02` | Проверить административные вкладки backoffice |
| Telegram-уведомления отражают смену статусов заказа и напоминания для barista | `BO-01` | Проверить customer notifications и barista reminders |
| Система сохраняет, какой barista обработал заказ | `BO-01` | Проверить audit trail в заказе или журнале действий |

## Release Gate

Инициатива может быть закрыта только после того, как:

1. инфраструктурный prerequisite `Stage 0` завершен;
2. обе block delivery области прошли contour implementation;
3. block-level validation по обоим deliverable прошла успешно;
4. rollout или deployment успешно выполнен;
5. финальная e2e validation по согласованным сценариям прошла успешно.
