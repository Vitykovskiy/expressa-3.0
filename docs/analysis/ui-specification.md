# UI Specification

## UI/UX Source Traceability

Основной source set для UI/UX контракта:

1. `Expressa — Требования к продукту.txt`
2. Figma Make `Expressa Customer` (`8AVVTDwJgQ2vFG8ZbQ6RV0`)
   - screen inventory из resource links: `MenuRoot`, `MenuGroup`, `ProductDetail`, `Cart`, `SlotPicker`, `OrdersHistory`, `Auth`
   - визуальный preview подтверждает mobile-first customer menu shell
3. Figma Make `Expressa Admin` (`pRTdx3oouQIEwmXDTtM0zT`)
   - screen inventory из resource links: `OrdersScreen`, `AvailabilityScreen`, `MenuScreen`, `UsersScreen`, `SettingsScreen`
   - component inventory: `TopBar`, `TabBar`, `SideNav`, `OrderCard`, `StatusBadge`, CRUD dialogs

Если состояние ниже отмечено как `synthesized`, оно выведено из требований и считается обязательным для реализации, даже если в Figma Make не найден отдельный финальный экран.

## Customer UI/UX Contract

| Screen / interface | User | Goal | States | Notes |
| --- | --- | --- | --- | --- |
| `Customer Auth Gate` | `customer` | Проверить доступ и инициализировать session | `loading`, `ready`, `blocked (synthesized)`, `auth error (synthesized)` | В prod вход только через Telegram WebApp context |
| `Menu Home` | `customer` | Войти в каталог и выбрать категорию/товар | `loading`, `populated`, `empty category`, `product unavailable` | Mobile-first vertical feed; sticky header допустим |
| `Menu Category` | `customer` | Просмотреть товары выбранной категории | `loading`, `populated`, `no products` | Отдельный экран или route state поверх menu shell |
| `Product Detail` | `customer` | Настроить товар перед добавлением | `default`, `size required`, `modifier selected`, `validation error` | Обязательный выбор размера для напитков; показывать итоговую цену до add-to-cart |
| `Cart` | `customer` | Проверить и отредактировать состав заказа | `empty`, `populated`, `item update`, `unavailable item conflict (synthesized)` | Позволяет менять количество и состав до order creation |
| `Slot Picker` | `customer` | Выбрать доступный слот текущего дня | `loading`, `slots available`, `no slots available`, `slot just filled (synthesized)` | Доступны только интервалы текущего дня |
| `Order Confirmation Result` | `customer` | Получить подтверждение, что заказ создан | `success`, `conflict retry (synthesized)` | Успешный результат должен показать номер заказа, слот и статус `Created` |
| `Orders History` | `customer` | Видеть прошлые и текущие заказы | `loading`, `empty`, `list`, `rejected with reason` | Заказ должен показывать статус, состав, сумму и слот |

## Backoffice UI/UX Contract

| Screen / interface | User | Goal | States | Notes |
| --- | --- | --- | --- | --- |
| `Backoffice Auth Gate` | `barista` / `administrator` | Инициализировать роль и набор вкладок | `loading`, `ready`, `forbidden`, `blocked` | Роль определяет видимые вкладки |
| `Orders` | `barista` / `administrator` | Работать с очередью заказов | `loading`, `empty`, `list`, `detail expanded`, `action pending` | Карточка заказа обязана показывать slot, сумму, состав, статус |
| `Reject Dialog` | `barista` / `administrator` | Указать причину отказа | `closed`, `open`, `validation error` | Причина обязательна и уходит в audit + customer notification |
| `Availability` | `barista` / `administrator` | Временно включать и выключать доступность | `loading`, `list`, `toggle success`, `toggle failed` | Меняет только `isActive`, не структуру и не цену |
| `Menu` | `administrator` | Управлять категориями, товарами, размерами, допами | `loading`, `empty`, `list`, `create/edit dialog`, `save error` | Доступна только administrator |
| `Users` | `administrator` | Назначать роль `barista` и блокировать пользователей | `loading`, `empty`, `list`, `add/edit dialog` | Нужно отображать текущую роль и block status |
| `Settings` | `administrator` | Настраивать рабочие часы и емкость слотов | `loading`, `form`, `save success`, `validation error` | В v1 изменяются часы и емкость; шаг слота зафиксирован 10 минут |

## Navigation Model

- Customer surface:
  1. `Auth Gate` -> `Menu Home`
  2. `Menu Home` -> `Menu Category` or `Product Detail`
  3. `Product Detail` -> `Cart`
  4. `Cart` -> `Slot Picker`
  5. `Slot Picker` -> `Order Confirmation Result`
  6. `Menu Home` or primary nav -> `Orders History`
- Backoffice surface:
  1. `Auth Gate` -> default tab `Orders`
  2. `barista` sees tabs: `Orders`, `Availability`
  3. `administrator` sees tabs: `Orders`, `Availability`, `Menu`, `Users`, `Settings`
  4. Mobile navigation может быть bottom tab bar; desktop/tablet inside Telegram может использовать side nav

## Interaction Rules

- Customer не может добавить напиток в корзину без выбранного размера.
- Недоступные товары и модификаторы должны либо скрываться, либо явно маркироваться как недоступные до add-to-cart.
- Из корзины можно вернуться к изменению позиции без потери остального состава корзины.
- Выбранный слот должен валидироваться сервером повторно при создании заказа.
- Barista-actions должны быть быстрыми: confirm, reject, ready, close доступны прямо из карточки заказа или детального drawer.
- Причина отказа обязательна до закрытия reject dialog.
- Вкладки, недоступные текущей роли, не должны рендериться как интерактивные элементы.

## Validation And Error States

| Surface | Condition | Expected behavior |
| --- | --- | --- |
| `Customer Auth Gate` | Пользователь заблокирован | Показать явный blocked state с текстом о недоступности сервиса |
| `Product Detail` | Не выбран обязательный размер | Кнопка добавления disabled, показать inline hint |
| `Cart` | Позиция стала недоступной | Показать conflict state и предложить обновить корзину |
| `Slot Picker` | Нет доступных слотов | Показать empty state без возможности оформить заказ |
| `Orders` | Reject без причины | Не отправлять запрос, показать inline validation |
| `Availability` | Ошибка переключения | Вернуть toggle в предыдущее состояние и показать toast/error |
| `Settings` | `open_time >= close_time` | Не сохранять форму, показать validation error |

## Accessibility / UX Notes

- Customer UI mobile-first: крупные tappable cards, вертикальный scroll, без горизонтального скролла на основных экранах.
- Все критичные действия должны иметь понятный текстовый label, а не только icon affordance.
- Статусы заказа должны дублироваться текстом, а не только цветом.
- Empty/loading/error states обязательны на обоих surface, чтобы QA не угадывал поведение.
