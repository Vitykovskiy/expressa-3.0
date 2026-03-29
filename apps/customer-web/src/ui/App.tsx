import { useEffect, useState } from 'react';
import { CustomerApi } from './customerApi';
import type {
  CartItem,
  CartPayload,
  MenuPayload,
  OrderDetail,
  OrderSummary,
  ProductConfiguratorState,
  ProductDetailPayload,
  Screen,
  Session,
  SessionState,
  Slot,
} from './types';

function rub(value: number) {
  return `${value.toLocaleString('ru-RU')} ₽`;
}

function formatSlot(dateString: string) {
  const date = new Date(dateString);
  return date.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' });
}

function formatDate(dateString: string) {
  return new Date(dateString).toLocaleString('ru-RU', {
    day: '2-digit',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function emptyConfigurator(): ProductConfiguratorState {
  return {
    sizeCode: '',
    modifierOptionIds: [],
    qty: 1,
  };
}

interface AppProps {
  api?: CustomerApi;
}

export default function App({ api = new CustomerApi() }: AppProps) {
  const [sessionState, setSessionState] = useState<SessionState>('loading');
  const [session, setSession] = useState<Session | null>(null);
  const [menu, setMenu] = useState<MenuPayload>({ categories: [], products: [] });
  const [selectedCategory, setSelectedCategory] = useState('');
  const [detail, setDetail] = useState<ProductDetailPayload | null>(null);
  const [config, setConfig] = useState<ProductConfiguratorState>(emptyConfigurator);
  const [cart, setCart] = useState<CartPayload>({ items: [], subtotalRub: 0, totalRub: 0, version: 1 });
  const [slots, setSlots] = useState<Slot[]>([]);
  const [orders, setOrders] = useState<OrderSummary[]>([]);
  const [orderDetail, setOrderDetail] = useState<OrderDetail | null>(null);
  const [screen, setScreen] = useState<Screen>('menu');
  const [resultMessage, setResultMessage] = useState('');
  const [selectedSlot, setSelectedSlot] = useState('');
  const [isBusy, setIsBusy] = useState(false);
  const [alert, setAlert] = useState('');

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

        const [nextMenu, nextCart, nextOrders] = await Promise.all([
          api.getMenu(),
          api.getCart(),
          api.listOrders(),
        ]);

        if (cancelled) {
          return;
        }

        setSession(nextSession);
        setMenu(nextMenu);
        setSelectedCategory(nextMenu.categories[0]?.id ?? '');
        setCart(nextCart);
        setOrders(nextOrders.orders);
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

  const filteredProducts = selectedCategory
    ? menu.products.filter((product) => product.categoryId === selectedCategory)
    : menu.products;

  async function openProduct(productId: string) {
    setAlert('');
    setIsBusy(true);

    try {
      const payload = await api.getProduct(productId);
      setDetail(payload);
      setConfig(emptyConfigurator());
    } catch (error) {
      setAlert(`Не удалось открыть товар: ${String(error)}`);
    } finally {
      setIsBusy(false);
    }
  }

  async function addToCart() {
    if (!detail) {
      return;
    }

    setIsBusy(true);
    setAlert('');

    try {
      const nextCart = await api.addCartItem(detail.product.id, config);
      setCart(nextCart);
      setDetail(null);
      setConfig(emptyConfigurator());
      setAlert('Позиция добавлена в корзину.');
    } catch (error) {
      setAlert(String(error));
    } finally {
      setIsBusy(false);
    }
  }

  async function updateQty(item: CartItem, qty: number) {
    if (qty <= 0) {
      setCart(await api.removeCartItem(item.cartItemId));
      return;
    }

    setCart(await api.updateCartItem(item.cartItemId, { qty }));
  }

  async function loadSlots() {
    setIsBusy(true);
    setAlert('');

    try {
      const payload = await api.getSlots();
      setSlots(payload.slots);
      setSelectedSlot(payload.slots.find((slot) => slot.isAvailable)?.start ?? '');
      setScreen('slots');
    } catch (error) {
      setAlert(`Не удалось получить слоты: ${String(error)}`);
    } finally {
      setIsBusy(false);
    }
  }

  async function confirmOrder() {
    if (!selectedSlot) {
      setAlert('Выберите слот перед оформлением заказа.');
      return;
    }

    setIsBusy(true);
    setAlert('');

    try {
      const result = await api.createOrder(selectedSlot, cart.version);
      setResultMessage(`Заказ ${result.orderId} создан. Слот ${formatSlot(result.slotStart)} зарезервирован.`);
      setCart(await api.getCart());
      setOrders((await api.listOrders()).orders);
      setScreen('result');
    } catch (error) {
      setAlert(`Не удалось оформить заказ: ${String(error)}`);
    } finally {
      setIsBusy(false);
    }
  }

  async function openOrder(orderId: string) {
    setIsBusy(true);
    try {
      setOrderDetail(await api.getOrder(orderId));
    } finally {
      setIsBusy(false);
    }
  }

  if (sessionState === 'loading') {
    return <LoadingState />;
  }

  if (sessionState === 'blocked') {
    return (
      <div className="shell">
        <section className="blocked-card">
          <p className="eyebrow">Customer Auth Gate</p>
          <h1>Доступ временно недоступен</h1>
          <p>
            Профиль {session?.displayName ?? 'пользователя'} заблокирован. Если это ошибка, обратитесь в Expressa support
            через Telegram.
          </p>
        </section>
      </div>
    );
  }

  if (sessionState === 'error') {
    return (
      <div className="shell">
        <section className="blocked-card">
          <p className="eyebrow">Auth Error</p>
          <h1>Не удалось инициализировать сессию</h1>
          <p>
            Stage 0 backend ещё может не публиковать customer endpoints. Откройте customer WebApp из Telegram-бота
            или включите preview-проверку для UI-обхода без backend sibling.
          </p>
          <div className="result-actions">
            <a className="secondary-button inline-link" href="?preview=1">
              Открыть preview-проверку
            </a>
          </div>
        </section>
      </div>
    );
  }

  return (
    <div className="shell">
      <div className="app">
        <header className="hero">
          <div>
            <p className="eyebrow">Expressa Customer</p>
            <h1>Кофе к выдаче без очереди</h1>
            <p className="hero-copy">
              Выберите напиток, настройте размер и добавки, забронируйте слот на сегодня и следите за статусом заказа.
            </p>
          </div>
          <div className="hero-meta">
            <span className="pill">{session?.displayName}</span>
            <span className="pill pill-soft">{api.getMode() === 'mock' ? 'Preview-проверка' : 'Live API'}</span>
          </div>
        </header>

        <nav className="bottom-nav">
          <button className={screen === 'menu' ? 'nav-link active' : 'nav-link'} onClick={() => setScreen('menu')}>
            Меню
          </button>
          <button
            className={screen === 'history' ? 'nav-link active' : 'nav-link'}
            onClick={() => setScreen('history')}
          >
            История
          </button>
          <button className="cart-link" onClick={() => void loadSlots()} disabled={!cart.items.length}>
            Корзина · {cart.items.length}
          </button>
        </nav>

        {alert ? <div className="toast">{alert}</div> : null}

        {screen === 'menu' ? (
          <main className="content">
            <section className="card panel">
              <div className="section-head">
                <div>
                  <p className="eyebrow">Menu Home</p>
                  <h2>Сегодня в меню</h2>
                </div>
                <button className="link-button" onClick={() => setScreen('history')}>
                  Мои заказы
                </button>
              </div>

              <div className="chip-row">
                {menu.categories.map((category) => (
                  <button
                    key={category.id}
                    className={selectedCategory === category.id ? 'chip active' : 'chip'}
                    onClick={() => setSelectedCategory(category.id)}
                  >
                    {category.name}
                  </button>
                ))}
              </div>

              {!menu.categories.length ? (
                <EmptyState
                  title="Каталог пуст"
                  text="Сегодня нет доступных категорий. Вернитесь позже или проверьте availability в backoffice."
                />
              ) : filteredProducts.length ? (
                <div className="product-grid">
                  {filteredProducts.map((product) => (
                    <article key={product.id} className={product.isAvailable ? 'product-card' : 'product-card muted'}>
                      <div className="product-top">
                        <p className="eyebrow">{product.badge ?? 'Expressa picks'}</p>
                        <span>{rub(product.priceFromRub)}</span>
                      </div>
                      <h3>{product.name}</h3>
                      <p>{product.description}</p>
                      <button disabled={!product.isAvailable || isBusy} onClick={() => void openProduct(product.id)}>
                        {product.isAvailable ? 'Настроить' : 'Недоступно'}
                      </button>
                    </article>
                  ))}
                </div>
              ) : (
                <EmptyState
                  title="В этой категории пока пусто"
                  text="Попробуйте соседнюю категорию или дождитесь обновления меню."
                />
              )}
            </section>

            <section className="card panel cart-panel">
              <div className="section-head">
                <div>
                  <p className="eyebrow">Cart</p>
                  <h2>Корзина</h2>
                </div>
                <span className="pill">{rub(cart.totalRub)}</span>
              </div>

              {!cart.items.length ? (
                <EmptyState title="Корзина пуста" text="Добавьте напиток или десерт, чтобы перейти к выбору слота." />
              ) : (
                <>
                  <div className="cart-list">
                    {cart.items.map((item) => (
                      <article key={item.cartItemId} className="cart-item">
                        <div>
                          <h3>{item.productName}</h3>
                          <p>
                            {item.sizeLabel}
                            {item.modifierLabels.length ? ` · ${item.modifierLabels.join(', ')}` : ''}
                          </p>
                          {item.availabilityConflict ? (
                            <p className="warning-text">Позиция изменилась. Обновите корзину перед оформлением заказа.</p>
                          ) : null}
                        </div>
                        <div className="cart-controls">
                          <button onClick={() => void updateQty(item, item.qty - 1)}>-</button>
                          <span>{item.qty}</span>
                          <button onClick={() => void updateQty(item, item.qty + 1)}>+</button>
                        </div>
                        <strong>{rub(item.totalPriceRub)}</strong>
                      </article>
                    ))}
                  </div>
                  <div className="summary-row">
                    <span>Итого</span>
                    <strong>{rub(cart.totalRub)}</strong>
                  </div>
                  <button className="primary-button" onClick={() => void loadSlots()}>
                    Выбрать слот
                  </button>
                </>
              )}
            </section>
          </main>
        ) : null}

        {screen === 'slots' ? (
          <main className="content single-column">
            <section className="card panel">
              <div className="section-head">
                <div>
                  <p className="eyebrow">Slot Picker</p>
                  <h2>Выберите слот на сегодня</h2>
                </div>
                <button className="link-button" onClick={() => setScreen('menu')}>
                  Назад к меню
                </button>
              </div>

              {!slots.length ? (
                <EmptyState
                  title="Свободных слотов на сегодня нет"
                  text="Выберите другой момент позже. Заказ нельзя оформить без доступного интервала."
                />
              ) : (
                <div className="slot-grid">
                  {slots.map((slot) => (
                    <button
                      key={slot.start}
                      className={selectedSlot === slot.start ? 'slot-card active' : 'slot-card'}
                      disabled={!slot.isAvailable}
                      onClick={() => setSelectedSlot(slot.start)}
                    >
                      <strong>
                        {formatSlot(slot.start)} - {formatSlot(slot.end)}
                      </strong>
                      <span>{slot.isAvailable ? `Осталось ${slot.capacityLeft}` : 'Нет мест'}</span>
                    </button>
                  ))}
                </div>
              )}

              <div className="summary-block">
                <p>Сервер повторно валидирует slot capacity при создании заказа.</p>
                <button
                  className="primary-button"
                  disabled={!selectedSlot || isBusy || !slots.length}
                  onClick={() => void confirmOrder()}
                >
                  Подтвердить заказ
                </button>
              </div>
            </section>
          </main>
        ) : null}

        {screen === 'result' ? (
          <main className="content single-column">
            <section className="card panel result-card">
              <p className="eyebrow">Order Confirmation Result</p>
              <h2>Заказ оформлен</h2>
              <p>{resultMessage}</p>
              <p>
                Статус стартует с <strong>Created</strong>. Дальнейшие изменения придут в интерфейс и в Telegram-уведомлении.
              </p>
              <div className="result-actions">
                <button className="primary-button" onClick={() => setScreen('history')}>
                  Открыть историю
                </button>
                <button className="secondary-button" onClick={() => setScreen('menu')}>
                  Вернуться в меню
                </button>
              </div>
            </section>
          </main>
        ) : null}

        {screen === 'history' ? (
          <main className="content single-column">
            <section className="card panel">
              <div className="section-head">
                <div>
                  <p className="eyebrow">Orders History</p>
                  <h2>Мои заказы</h2>
                </div>
                <button className="link-button" onClick={() => setScreen('menu')}>
                  К меню
                </button>
              </div>

              {!orders.length ? (
                <EmptyState title="История пока пустая" text="Как только вы оформите первый заказ, он появится здесь." />
              ) : (
                <div className="history-list">
                  {orders.map((order) => (
                    <article key={order.orderId} className="history-card">
                      <div>
                        <p className="eyebrow">{formatDate(order.createdAt)}</p>
                        <h3>{order.orderId}</h3>
                        <p>
                          {order.itemCount} поз. · {rub(order.totalRub)}
                        </p>
                        <span className="status-pill">{order.status}</span>
                        {order.rejectReason ? <p className="warning-text">Причина отказа: {order.rejectReason}</p> : null}
                      </div>
                      <button className="secondary-button" onClick={() => void openOrder(order.orderId)}>
                        Детали
                      </button>
                    </article>
                  ))}
                </div>
              )}
            </section>
          </main>
        ) : null}
      </div>

      {detail ? (
        <aside className="drawer">
          <div className="drawer-sheet">
            <div className="section-head">
              <div>
                <p className="eyebrow">Product Detail</p>
                <h2>{detail.product.name}</h2>
              </div>
              <button className="link-button" onClick={() => setDetail(null)}>
                Закрыть
              </button>
            </div>

            <p className="drawer-copy">{detail.product.description}</p>

            <div className="field-group">
              <label>Размер</label>
              <div className="choice-grid">
                {detail.sizes.map((size) => (
                  <button
                    key={size.code}
                    className={config.sizeCode === size.code ? 'choice active' : 'choice'}
                    onClick={() => setConfig((current) => ({ ...current, sizeCode: size.code }))}
                  >
                    <strong>{size.label}</strong>
                    <span>{rub(size.priceRub)}</span>
                  </button>
                ))}
              </div>
              {!config.sizeCode ? <p className="validation-text">Выберите обязательный размер, чтобы добавить напиток.</p> : null}
            </div>

            {detail.modifierGroups.map((group) => (
              <div key={group.id} className="field-group">
                <label>{group.name}</label>
                <div className="choice-grid">
                  {group.options.map((option) => {
                    const selected = config.modifierOptionIds.includes(option.id);
                    return (
                      <button
                        key={option.id}
                        className={selected ? 'choice active' : 'choice'}
                        disabled={!option.isAvailable}
                        onClick={() =>
                          setConfig((current) => {
                            const exists = current.modifierOptionIds.includes(option.id);
                            const nextIds = exists
                              ? current.modifierOptionIds.filter((entry) => entry !== option.id)
                              : [...current.modifierOptionIds, option.id].slice(-group.maxSelect);

                            return {
                              ...current,
                              modifierOptionIds: nextIds,
                            };
                          })
                        }
                      >
                        <strong>{option.label}</strong>
                        <span>{option.priceDeltaRub ? `+${rub(option.priceDeltaRub)}` : 'Включено'}</span>
                      </button>
                    );
                  })}
                </div>
              </div>
            ))}

            <div className="qty-row">
              <label>Количество</label>
              <div className="stepper">
                <button onClick={() => setConfig((current) => ({ ...current, qty: Math.max(1, current.qty - 1) }))}>-</button>
                <span>{config.qty}</span>
                <button onClick={() => setConfig((current) => ({ ...current, qty: current.qty + 1 }))}>+</button>
              </div>
            </div>

            <button className="primary-button" disabled={!config.sizeCode || isBusy} onClick={() => void addToCart()}>
              Добавить в корзину
            </button>
          </div>
        </aside>
      ) : null}

      {orderDetail ? (
        <aside className="drawer">
          <div className="drawer-sheet">
            <div className="section-head">
              <div>
                <p className="eyebrow">Order Detail</p>
                <h2>{orderDetail.order.orderId}</h2>
              </div>
              <button className="link-button" onClick={() => setOrderDetail(null)}>
                Закрыть
              </button>
            </div>
            <div className="detail-stack">
              <div className="detail-row">
                <span>Статус</span>
                <strong>{orderDetail.order.status}</strong>
              </div>
              <div className="detail-row">
                <span>Слот</span>
                <strong>{formatSlot(orderDetail.order.slotStart)}</strong>
              </div>
              <div className="detail-row">
                <span>Итого</span>
                <strong>{rub(orderDetail.order.totalRub)}</strong>
              </div>
              {orderDetail.order.rejectReason ? (
                <div className="detail-row warning-box">
                  <span>Причина отказа</span>
                  <strong>{orderDetail.order.rejectReason}</strong>
                </div>
              ) : null}
            </div>
            <div className="history-entries">
              {orderDetail.items.map((item) => (
                <div key={item.cartItemId} className="history-entry">
                  <div>
                    <strong>{item.productName}</strong>
                    <p>
                      {item.sizeLabel} · {item.qty} шт.
                    </p>
                  </div>
                  <span>{rub(item.totalPriceRub)}</span>
                </div>
              ))}
            </div>
            <div className="timeline">
              {orderDetail.statusHistory.map((entry) => (
                <div key={entry.changedAt} className="timeline-item">
                  <strong>{entry.status}</strong>
                  <span>{formatDate(entry.changedAt)}</span>
                </div>
              ))}
            </div>
          </div>
        </aside>
      ) : null}
    </div>
  );
}

function LoadingState() {
  return (
    <div className="shell">
      <div className="app">
        <header className="hero skeleton" />
        <main className="content">
          <section className="card panel skeleton large" />
          <section className="card panel skeleton medium" />
        </main>
      </div>
    </div>
  );
}

function EmptyState({ title, text }: { title: string; text: string }) {
  return (
    <div className="empty-state">
      <h3>{title}</h3>
      <p>{text}</p>
    </div>
  );
}
