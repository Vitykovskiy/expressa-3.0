import { useEffect, useState } from 'react';
import { BackofficeApi } from './backofficeApi';
import type {
  AvailabilityEntity,
  MenuDialogState,
  MenuPayload,
  OrderRecord,
  OrderStatus,
  OrdersPayload,
  RejectDialogState,
  Session,
  SessionState,
  SettingsPayload,
  TabId,
  UserDialogState,
  UsersPayload,
} from './types';

function rub(value: number) {
  return `${value.toLocaleString('ru-RU')} ₽`;
}

function formatDate(dateString: string) {
  return new Date(dateString).toLocaleString('ru-RU', {
    day: '2-digit',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function humanStatus(status: OrderStatus) {
  switch (status) {
    case 'Created':
      return 'Новый';
    case 'Confirmed':
      return 'Подтвержден';
    case 'Rejected':
      return 'Отклонен';
    case 'Ready for pickup':
      return 'Готов к выдаче';
    case 'Closed':
      return 'Закрыт';
    default:
      return status;
  }
}

function slug(value: string) {
  return value.toLowerCase().replaceAll(' ', '-');
}

function defaultMenuDialog(type: MenuDialogState['type']): MenuDialogState {
  return {
    type,
    mode: 'create',
    categoryId: '',
    name: '',
    description: '',
    sizeLabels: '',
  };
}

interface AppProps {
  api?: BackofficeApi;
}

export default function App({ api = new BackofficeApi() }: AppProps) {
  const [sessionState, setSessionState] = useState<SessionState>('loading');
  const [session, setSession] = useState<Session | null>(null);
  const [activeTab, setActiveTab] = useState<TabId>('orders');
  const [orders, setOrders] = useState<OrderRecord[]>([]);
  const [orderCounters, setOrderCounters] = useState<OrdersPayload['counters']>({});
  const [statusFilter, setStatusFilter] = useState<OrderStatus | 'all'>('all');
  const [availability, setAvailability] = useState<AvailabilityEntity[]>([]);
  const [availabilitySearch, setAvailabilitySearch] = useState('');
  const [menu, setMenu] = useState<MenuPayload>({ categories: [], products: [], modifierGroups: [] });
  const [users, setUsers] = useState<UsersPayload['users']>([]);
  const [userSearch, setUserSearch] = useState('');
  const [settings, setSettings] = useState<SettingsPayload>({
    workingHours: { openTime: '08:00', closeTime: '21:00' },
    slotStepMinutes: 10,
    slotCapacity: 8,
  });
  const [toast, setToast] = useState('');
  const [isBusy, setIsBusy] = useState(false);
  const [rejectDialog, setRejectDialog] = useState<RejectDialogState | null>(null);
  const [rejectError, setRejectError] = useState('');
  const [menuDialog, setMenuDialog] = useState<MenuDialogState | null>(null);
  const [userDialog, setUserDialog] = useState<UserDialogState | null>(null);
  const [settingsError, setSettingsError] = useState('');

  useEffect(() => {
    let cancelled = false;

    async function bootstrap() {
      try {
        const nextSession = await api.getSession();

        if (cancelled) {
          return;
        }

        if (nextSession.isBlocked) {
          setSession(nextSession);
          setSessionState('blocked');
          return;
        }

        if (!nextSession.allowedTabs.length) {
          setSession(nextSession);
          setSessionState('forbidden');
          return;
        }

        const [ordersPayload, availabilityPayload, menuPayload, usersPayload, settingsPayload] = await Promise.all([
          api.getOrders(),
          api.getAvailability(),
          nextSession.allowedTabs.includes('menu') ? api.getMenu() : Promise.resolve({ categories: [], products: [], modifierGroups: [] }),
          nextSession.allowedTabs.includes('users') ? api.getUsers() : Promise.resolve({ users: [] }),
          nextSession.allowedTabs.includes('settings')
            ? api.getSettings()
            : Promise.resolve({ workingHours: { openTime: '08:00', closeTime: '21:00' }, slotStepMinutes: 10, slotCapacity: 8 }),
        ]);

        if (cancelled) {
          return;
        }

        setSession(nextSession);
        setActiveTab(nextSession.allowedTabs[0]);
        setOrders(ordersPayload.orders);
        setOrderCounters(ordersPayload.counters);
        setAvailability(availabilityPayload.entities);
        setMenu(menuPayload);
        setUsers(usersPayload.users);
        setSettings(settingsPayload);
        setSessionState('ready');
      } catch {
        if (!cancelled) {
          setSessionState('error');
        }
      }
    }

    bootstrap();

    return () => {
      cancelled = true;
    };
  }, [api]);

  async function refreshOrders(nextStatus?: OrderStatus | 'all') {
    const payload = await api.getOrders(nextStatus && nextStatus !== 'all' ? nextStatus : undefined);
    setOrders(payload.orders);
    setOrderCounters(payload.counters);
  }

  async function applyOrderAction(orderId: string, action: 'confirm' | 'ready' | 'close') {
    setIsBusy(true);
    setToast('');

    try {
      const payload = await api.updateOrderStatus(orderId, action);
      setOrders(payload.orders);
      setOrderCounters(payload.counters);
      setToast('Статус заказа обновлен.');
    } catch (error) {
      setToast(`Не удалось обновить заказ: ${String(error)}`);
    } finally {
      setIsBusy(false);
    }
  }

  async function submitReject() {
    if (!rejectDialog) {
      return;
    }

    if (!rejectDialog.reason.trim()) {
      setRejectError('Укажите причину отказа, чтобы закрыть диалог.');
      return;
    }

    setIsBusy(true);
    setRejectError('');

    try {
      const payload = await api.updateOrderStatus(rejectDialog.orderId, 'reject', rejectDialog.reason.trim());
      setOrders(payload.orders);
      setOrderCounters(payload.counters);
      setRejectDialog(null);
      setToast('Заказ отклонен с указанием причины.');
    } catch (error) {
      setRejectError(String(error));
    } finally {
      setIsBusy(false);
    }
  }

  async function toggleEntity(entity: AvailabilityEntity) {
    setToast('');
    try {
      const payload = await api.toggleAvailability(entity.entityType, entity.entityId, !entity.isActive);
      setAvailability(payload.entities);
      setToast('Доступность обновлена.');
    } catch (error) {
      setToast(`Не удалось изменить доступность: ${String(error)}`);
    }
  }

  async function saveMenuDialog() {
    if (!menuDialog || !menuDialog.name.trim()) {
      return;
    }

    try {
      const payload = await api.saveMenuDialog(menuDialog);
      setMenu(payload);
      setMenuDialog(null);
      setToast('Изменения меню сохранены.');
    } catch (error) {
      setToast(`Не удалось сохранить меню: ${String(error)}`);
    }
  }

  async function saveUserDialog() {
    if (!userDialog) {
      return;
    }

    try {
      const payload = await api.saveUserDialog(userDialog);
      setUsers(payload.users);
      setUserDialog(null);
      setToast('Роль и блокировка обновлены.');
    } catch (error) {
      setToast(`Не удалось обновить пользователя: ${String(error)}`);
    }
  }

  async function saveSettings() {
    if (settings.workingHours.openTime >= settings.workingHours.closeTime) {
      setSettingsError('Время открытия должно быть раньше времени закрытия.');
      return;
    }

    setSettingsError('');

    try {
      const payload = await api.saveSettings({
        workingHours: settings.workingHours,
        slotCapacity: settings.slotCapacity,
      });
      setSettings(payload);
      setToast('Настройки сохранены.');
    } catch (error) {
      setSettingsError(String(error));
    }
  }

  async function applyAvailabilitySearch() {
    const payload = await api.getAvailability(availabilitySearch);
    setAvailability(payload.entities);
  }

  async function applyUserSearch() {
    const payload = await api.getUsers(userSearch);
    setUsers(payload.users);
  }

  if (sessionState === 'loading') {
    return <LoadingState />;
  }

  if (sessionState === 'blocked') {
    return (
      <StateShell eyebrow="Backoffice Auth Gate" title="Доступ сотрудника заблокирован">
        Профиль {session?.displayName ?? 'сотрудника'} больше не может работать в backoffice. Обратитесь к администратору
        Expressa для восстановления доступа.
      </StateShell>
    );
  }

  if (sessionState === 'forbidden') {
    return (
      <StateShell eyebrow="Forbidden" title="Нет доступа к backoffice">
        Сессия не вернула ни одной разрешенной вкладки. Это ожидаемо только для пользователей без роли `barista` или
        `administrator`.
      </StateShell>
    );
  }

  if (sessionState === 'error') {
    return (
      <StateShell eyebrow="Auth Error" title="Не удалось инициализировать backoffice">
        Live `/api/backoffice/*` endpoints еще могут быть недоступны. Откройте интерфейс в preview-режиме или дождитесь
        готовности backend sibling.
      </StateShell>
    );
  }

  const availableTabs = session?.allowedTabs ?? [];

  return (
    <div className="backoffice-shell">
      <div className="backoffice-app">
        <aside className="sidebar card">
          <div className="brand">
            <p className="eyebrow">Expressa Backoffice</p>
            <h1>Операционный пульт смены</h1>
            <p className="sidebar-copy">
              Видимые вкладки зависят от роли. Barista работает с очередью и доступностью, administrator управляет меню,
              пользователями и настройками.
            </p>
          </div>

          <div className="session-card">
            <span className="role-badge">{session?.role === 'administrator' ? 'Administrator' : 'Barista'}</span>
            <strong>{session?.displayName}</strong>
            <span className="muted">{api.getMode() === 'mock' ? 'Preview-проверка' : 'Live API'}</span>
          </div>

          <nav className="sidebar-nav">
            {availableTabs.map((tab) => (
              <button
                key={tab}
                className={activeTab === tab ? 'tab-link active' : 'tab-link'}
                onClick={() => setActiveTab(tab)}
              >
                {tabLabels[tab]}
              </button>
            ))}
          </nav>
        </aside>

        <main className="workspace">
          <header className="workspace-header card">
            <div>
              <p className="eyebrow">Role-aware workspace</p>
              <h2>{tabLabels[activeTab]}</h2>
            </div>
            <div className="header-meta">
              <span className="meta-pill">Visible tabs: {availableTabs.length}</span>
              <span className="meta-pill">Slot step: {settings.slotStepMinutes} мин</span>
            </div>
          </header>

          {toast ? <div className="toast">{toast}</div> : null}

          <div className="mobile-tabs">
            {availableTabs.map((tab) => (
              <button
                key={tab}
                className={activeTab === tab ? 'mobile-tab active' : 'mobile-tab'}
                onClick={() => setActiveTab(tab)}
              >
                {tabLabels[tab]}
              </button>
            ))}
          </div>

          {activeTab === 'orders' ? (
            <section className="card workspace-card">
              <div className="section-head">
                <div>
                  <p className="eyebrow">Orders</p>
                  <h3>Очередь заказов</h3>
                </div>
                <div className="counter-row">
                  <Counter label="Новые" value={orderCounters.Created ?? 0} />
                  <Counter label="Подтверждены" value={orderCounters.Confirmed ?? 0} />
                  <Counter label="Готовы" value={orderCounters['Ready for pickup'] ?? 0} />
                </div>
              </div>

              <div className="filter-row">
                {(['all', 'Created', 'Confirmed', 'Ready for pickup', 'Rejected', 'Closed'] as const).map((filter) => (
                  <button
                    key={filter}
                    className={statusFilter === filter ? 'filter-chip active' : 'filter-chip'}
                    onClick={() => {
                      setStatusFilter(filter);
                      void refreshOrders(filter);
                    }}
                  >
                    {filter === 'all' ? 'Все' : humanStatus(filter)}
                  </button>
                ))}
              </div>

              {!orders.length ? (
                <EmptyState
                  title="Очередь сейчас пуста"
                  text="Как только появятся новые заказы, карточки со слотами, суммой и составом появятся здесь."
                />
              ) : (
                <div className="orders-grid">
                  {orders.map((order) => (
                    <article key={order.orderId} className="order-card">
                      <div className="order-top">
                        <div>
                          <p className="eyebrow">{formatDate(order.updatedAt)}</p>
                          <h4>{order.orderId}</h4>
                        </div>
                        <span className={`status-chip status-${slug(order.status)}`}>{humanStatus(order.status)}</span>
                      </div>
                      <p className="order-subline">
                        {order.customerName} · {formatDate(order.slotStart)} · {rub(order.totalRub)}
                      </p>
                      <div className="order-items">
                        {order.items.map((item) => (
                          <div key={`${order.orderId}-${item.name}`} className="order-item">
                            <span>
                              {item.name} · {item.qty} шт.
                            </span>
                            <span>{item.sizeLabel}</span>
                          </div>
                        ))}
                      </div>
                      {order.rejectReason ? <p className="warning-box">Причина отказа: {order.rejectReason}</p> : null}
                      <div className="action-row">
                        {order.status === 'Created' ? (
                          <>
                            <button
                              disabled={isBusy}
                              className="primary-button"
                              onClick={() => void applyOrderAction(order.orderId, 'confirm')}
                            >
                              Подтвердить
                            </button>
                            <button
                              disabled={isBusy}
                              className="secondary-button"
                              onClick={() => {
                                setRejectError('');
                                setRejectDialog({ orderId: order.orderId, reason: '' });
                              }}
                            >
                              Отклонить
                            </button>
                          </>
                        ) : null}
                        {order.status === 'Confirmed' ? (
                          <button
                            disabled={isBusy}
                            className="primary-button"
                            onClick={() => void applyOrderAction(order.orderId, 'ready')}
                          >
                            Отметить готовым
                          </button>
                        ) : null}
                        {order.status === 'Ready for pickup' ? (
                          <button
                            disabled={isBusy}
                            className="primary-button"
                            onClick={() => void applyOrderAction(order.orderId, 'close')}
                          >
                            Закрыть заказ
                          </button>
                        ) : null}
                      </div>
                    </article>
                  ))}
                </div>
              )}
            </section>
          ) : null}

          {activeTab === 'availability' ? (
            <section className="card workspace-card">
              <div className="section-head">
                <div>
                  <p className="eyebrow">Availability</p>
                  <h3>Оперативная доступность</h3>
                </div>
                <div className="search-row">
                  <input
                    value={availabilitySearch}
                    onChange={(event) => setAvailabilitySearch(event.target.value)}
                    placeholder="Поиск товара или модификатора"
                  />
                  <button className="secondary-button" onClick={() => void applyAvailabilitySearch()}>
                    Найти
                  </button>
                </div>
              </div>

              {!availability.length ? (
                <EmptyState
                  title="Ничего не найдено"
                  text="Проверьте фильтр или дождитесь наполнения availability backend-контрактом."
                />
              ) : (
                <div className="availability-list">
                  {availability.map((entity) => (
                    <article key={entity.entityId} className="inline-card">
                      <div>
                        <strong>{entity.name}</strong>
                        <p>
                          {entity.category} · {entity.entityType}
                        </p>
                      </div>
                      <button
                        className={entity.isActive ? 'secondary-button' : 'primary-button'}
                        onClick={() => void toggleEntity(entity)}
                      >
                        {entity.isActive ? 'Выключить' : 'Включить'}
                      </button>
                    </article>
                  ))}
                </div>
              )}
            </section>
          ) : null}

          {activeTab === 'menu' ? (
            <section className="card workspace-card">
              <div className="section-head">
                <div>
                  <p className="eyebrow">Menu</p>
                  <h3>Категории и продукты</h3>
                </div>
                <div className="action-row">
                  <button className="secondary-button" onClick={() => setMenuDialog(defaultMenuDialog('category'))}>
                    Категория
                  </button>
                  <button
                    className="primary-button"
                    onClick={() =>
                      setMenuDialog({
                        ...defaultMenuDialog('product'),
                        categoryId: menu.categories[0]?.id ?? '',
                        sizeLabels: 'Standard',
                      })
                    }
                  >
                    Продукт
                  </button>
                </div>
              </div>

              <div className="split-grid">
                <div className="stack">
                  <h4>Категории</h4>
                  {menu.categories.length ? (
                    menu.categories.map((category) => (
                      <article key={category.id} className="inline-card">
                        <div>
                          <strong>{category.name}</strong>
                          <p>Порядок: {category.sortOrder}</p>
                        </div>
                        <button
                          className="secondary-button"
                          onClick={() =>
                            setMenuDialog({
                              type: 'category',
                              mode: 'edit',
                              id: category.id,
                              categoryId: category.id,
                              name: category.name,
                              description: '',
                              sizeLabels: '',
                            })
                          }
                        >
                          Изменить
                        </button>
                      </article>
                    ))
                  ) : (
                    <EmptyState title="Категорий пока нет" text="Создайте первую категорию, чтобы наполнить меню." />
                  )}
                </div>

                <div className="stack">
                  <h4>Продукты</h4>
                  {menu.products.length ? (
                    menu.products.map((product) => (
                      <article key={product.id} className="inline-card product-inline">
                        <div>
                          <strong>{product.name}</strong>
                          <p>{product.description}</p>
                          <p>{product.sizeLabels.join(', ')}</p>
                        </div>
                        <button
                          className="secondary-button"
                          onClick={() =>
                            setMenuDialog({
                              type: 'product',
                              mode: 'edit',
                              id: product.id,
                              categoryId: product.categoryId,
                              name: product.name,
                              description: product.description,
                              sizeLabels: product.sizeLabels.join(', '),
                            })
                          }
                        >
                          Изменить
                        </button>
                      </article>
                    ))
                  ) : (
                    <EmptyState title="Продуктов пока нет" text="Добавьте товар, чтобы customer-каталог получил контент." />
                  )}
                </div>
              </div>
            </section>
          ) : null}

          {activeTab === 'users' ? (
            <section className="card workspace-card">
              <div className="section-head">
                <div>
                  <p className="eyebrow">Users</p>
                  <h3>Роли и блокировки</h3>
                </div>
                <div className="search-row">
                  <input
                    value={userSearch}
                    onChange={(event) => setUserSearch(event.target.value)}
                    placeholder="Поиск по имени или Telegram ID"
                  />
                  <button className="secondary-button" onClick={() => void applyUserSearch()}>
                    Найти
                  </button>
                </div>
              </div>

              {!users.length ? (
                <EmptyState title="Пользователи не найдены" text="Смените фильтр или дождитесь синхронизации user-списка." />
              ) : (
                <div className="availability-list">
                  {users.map((user) => (
                    <article key={user.id} className="inline-card">
                      <div>
                        <strong>{user.displayName}</strong>
                        <p>
                          @{user.telegramId} · {user.role} · {user.isBlocked ? 'заблокирован' : 'активен'}
                        </p>
                      </div>
                      <button
                        className="secondary-button"
                        onClick={() =>
                          setUserDialog({
                            id: user.id,
                            role: user.role,
                            isBlocked: user.isBlocked,
                          })
                        }
                      >
                        Изменить
                      </button>
                    </article>
                  ))}
                </div>
              )}
            </section>
          ) : null}

          {activeTab === 'settings' ? (
            <section className="card workspace-card">
              <div className="section-head">
                <div>
                  <p className="eyebrow">Settings</p>
                  <h3>Часы работы и емкость слотов</h3>
                </div>
                <span className="meta-pill">Шаг слота: {settings.slotStepMinutes} мин</span>
              </div>

              <div className="settings-grid">
                <label>
                  <span>Открытие</span>
                  <input
                    aria-label="Открытие"
                    type="time"
                    value={settings.workingHours.openTime}
                    onChange={(event) =>
                      setSettings((current) => ({
                        ...current,
                        workingHours: { ...current.workingHours, openTime: event.target.value },
                      }))
                    }
                  />
                </label>
                <label>
                  <span>Закрытие</span>
                  <input
                    aria-label="Закрытие"
                    type="time"
                    value={settings.workingHours.closeTime}
                    onChange={(event) =>
                      setSettings((current) => ({
                        ...current,
                        workingHours: { ...current.workingHours, closeTime: event.target.value },
                      }))
                    }
                  />
                </label>
                <label>
                  <span>Емкость слота</span>
                  <input
                    aria-label="Емкость слота"
                    type="number"
                    min={1}
                    value={settings.slotCapacity}
                    onChange={(event) =>
                      setSettings((current) => ({
                        ...current,
                        slotCapacity: Number(event.target.value),
                      }))
                    }
                  />
                </label>
              </div>

              {settingsError ? <p className="validation-box">{settingsError}</p> : null}

              <div className="action-row">
                <button className="primary-button" onClick={() => void saveSettings()}>
                  Сохранить
                </button>
              </div>
            </section>
          ) : null}
        </main>
      </div>

      {rejectDialog ? (
        <Dialog
          title="Reject Dialog"
          subtitle="Причина отказа обязательна и уходит в audit trail и customer notification."
          onClose={() => setRejectDialog(null)}
        >
          <label className="stack">
            <span>Причина отказа</span>
            <textarea
              value={rejectDialog.reason}
              onChange={(event) =>
                setRejectDialog((current) => (current ? { ...current, reason: event.target.value } : current))
              }
              rows={4}
              placeholder="Например: закончился сироп или нет миндального молока"
            />
          </label>
          {rejectError ? <p className="validation-box">{rejectError}</p> : null}
          <div className="action-row">
            <button className="primary-button" onClick={() => void submitReject()}>
              Подтвердить отказ
            </button>
            <button className="secondary-button" onClick={() => setRejectDialog(null)}>
              Отмена
            </button>
          </div>
        </Dialog>
      ) : null}

      {menuDialog ? (
        <Dialog
          title={menuDialog.type === 'category' ? 'Редактирование категории' : 'Редактирование продукта'}
          subtitle={
            menuDialog.type === 'category'
              ? 'Только administrator может менять структуру меню.'
              : 'Размеры указываются списком через запятую.'
          }
          onClose={() => setMenuDialog(null)}
        >
          <div className="settings-grid compact">
            {menuDialog.type === 'product' ? (
              <label>
                <span>Категория</span>
                <select
                  value={menuDialog.categoryId}
                  onChange={(event) =>
                    setMenuDialog((current) => (current ? { ...current, categoryId: event.target.value } : current))
                  }
                >
                  {menu.categories.map((category) => (
                    <option key={category.id} value={category.id}>
                      {category.name}
                    </option>
                  ))}
                </select>
              </label>
            ) : null}
            <label>
              <span>Название</span>
              <input
                value={menuDialog.name}
                onChange={(event) => setMenuDialog((current) => (current ? { ...current, name: event.target.value } : current))}
              />
            </label>
            {menuDialog.type === 'product' ? (
              <>
                <label>
                  <span>Описание</span>
                  <textarea
                    value={menuDialog.description}
                    onChange={(event) =>
                      setMenuDialog((current) => (current ? { ...current, description: event.target.value } : current))
                    }
                    rows={3}
                  />
                </label>
                <label>
                  <span>Размеры</span>
                  <input
                    value={menuDialog.sizeLabels}
                    onChange={(event) =>
                      setMenuDialog((current) => (current ? { ...current, sizeLabels: event.target.value } : current))
                    }
                  />
                </label>
              </>
            ) : null}
          </div>
          <div className="action-row">
            <button className="primary-button" onClick={() => void saveMenuDialog()}>
              Сохранить
            </button>
            <button className="secondary-button" onClick={() => setMenuDialog(null)}>
              Отмена
            </button>
          </div>
        </Dialog>
      ) : null}

      {userDialog ? (
        <Dialog
          title="Редактирование пользователя"
          subtitle="Назначение ролей и блокировка доступны только administrator."
          onClose={() => setUserDialog(null)}
        >
          <div className="settings-grid compact">
            <label>
              <span>Роль</span>
              <select
                value={userDialog.role}
                onChange={(event) =>
                  setUserDialog((current) =>
                    current
                      ? {
                          ...current,
                          role: event.target.value as UserDialogState['role'],
                        }
                      : current,
                  )
                }
              >
                <option value="customer">customer</option>
                <option value="barista">barista</option>
                <option value="administrator">administrator</option>
              </select>
            </label>
            <label className="toggle-row">
              <span>Заблокирован</span>
              <input
                type="checkbox"
                checked={userDialog.isBlocked}
                onChange={(event) =>
                  setUserDialog((current) => (current ? { ...current, isBlocked: event.target.checked } : current))
                }
              />
            </label>
          </div>
          <div className="action-row">
            <button className="primary-button" onClick={() => void saveUserDialog()}>
              Сохранить
            </button>
            <button className="secondary-button" onClick={() => setUserDialog(null)}>
              Отмена
            </button>
          </div>
        </Dialog>
      ) : null}
    </div>
  );
}

const tabLabels: Record<TabId, string> = {
  orders: 'Заказы',
  availability: 'Доступность',
  menu: 'Меню',
  users: 'Пользователи',
  settings: 'Настройки',
};

function Counter({ label, value }: { label: string; value: number }) {
  return (
    <div className="counter-card">
      <strong>{value}</strong>
      <span>{label}</span>
    </div>
  );
}

function EmptyState({ title, text }: { title: string; text: string }) {
  return (
    <div className="empty-state">
      <h4>{title}</h4>
      <p>{text}</p>
    </div>
  );
}

function LoadingState() {
  return (
    <div className="backoffice-shell">
      <div className="backoffice-app loading-layout">
        <aside className="sidebar card skeleton" />
        <main className="workspace">
          <header className="workspace-header card skeleton" />
          <section className="workspace-card card skeleton large" />
        </main>
      </div>
    </div>
  );
}

function StateShell({
  eyebrow,
  title,
  children,
}: {
  eyebrow: string;
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="backoffice-shell">
      <section className="state-card card">
        <p className="eyebrow">{eyebrow}</p>
        <h1>{title}</h1>
        <p>{children}</p>
      </section>
    </div>
  );
}

function Dialog({
  title,
  subtitle,
  children,
  onClose,
}: {
  title: string;
  subtitle: string;
  children: React.ReactNode;
  onClose: () => void;
}) {
  return (
    <div className="dialog-shell">
      <div className="dialog card">
        <div className="section-head">
          <div>
            <p className="eyebrow">{title}</p>
            <p className="dialog-copy">{subtitle}</p>
          </div>
          <button className="secondary-button" onClick={onClose}>
            Закрыть
          </button>
        </div>
        {children}
      </div>
    </div>
  );
}
