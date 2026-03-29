import type {
  CartItem,
  CartPayload,
  Category,
  MenuPayload,
  ModifierGroup,
  OrderDetail,
  OrderSummary,
  ProductCard,
  ProductConfiguratorState,
  ProductDetailPayload,
  ProductSize,
  Session,
  Slot,
} from './types';

interface StoreState {
  session: Session;
  categories: Category[];
  products: ProductCard[];
  details: Record<string, ProductDetailPayload>;
  cart: CartPayload;
  slots: Slot[];
  orders: OrderDetail[];
}

const STORAGE_KEY = 'expressa.customer.mock-store';

function todayAt(hours: number, minutes: number) {
  const date = new Date();
  date.setHours(hours, minutes, 0, 0);
  return date.toISOString();
}

const baseCategories: Category[] = [
  { id: 'coffee', name: 'Кофе', description: 'Эспрессо, фильтр, авторские напитки' },
  { id: 'tea', name: 'Чай', description: 'Черный, зеленый и фруктовые бленды' },
  { id: 'pastry', name: 'Пекарня', description: 'Круассаны, печенье и десерты' },
];

const baseProducts: ProductCard[] = [
  {
    id: 'flat-white',
    categoryId: 'coffee',
    name: 'Flat White',
    description: 'Двойной эспрессо и молоко с бархатной текстурой',
    priceFromRub: 260,
    badge: 'Хит дня',
    isAvailable: true,
  },
  {
    id: 'filter-citrus',
    categoryId: 'coffee',
    name: 'Filter Citrus',
    description: 'Легкий фильтр с цитрусовым профилем',
    priceFromRub: 220,
    isAvailable: true,
  },
  {
    id: 'matcha-latte',
    categoryId: 'tea',
    name: 'Matcha Latte',
    description: 'Японская матча с молоком',
    priceFromRub: 280,
    badge: 'Новинка',
    isAvailable: true,
  },
  {
    id: 'almond-croissant',
    categoryId: 'pastry',
    name: 'Круассан с миндалем',
    description: 'Свежая слоеная выпечка с кремом',
    priceFromRub: 190,
    isAvailable: false,
  },
];

const sizes: ProductSize[] = [
  { code: 'small', label: 'S / 250 мл', priceRub: 260 },
  { code: 'medium', label: 'M / 350 мл', priceRub: 290 },
  { code: 'large', label: 'L / 450 мл', priceRub: 330 },
];

const modifierGroups: ModifierGroup[] = [
  {
    id: 'milk',
    name: 'Молоко',
    minSelect: 0,
    maxSelect: 1,
    options: [
      { id: 'whole', label: 'Обычное', priceDeltaRub: 0, isAvailable: true },
      { id: 'oat', label: 'Овсяное', priceDeltaRub: 40, isAvailable: true },
      { id: 'lactose-free', label: 'Безлактозное', priceDeltaRub: 30, isAvailable: true },
    ],
  },
  {
    id: 'extras',
    name: 'Допы',
    minSelect: 0,
    maxSelect: 2,
    options: [
      { id: 'vanilla', label: 'Ванильный сироп', priceDeltaRub: 20, isAvailable: true },
      { id: 'shot', label: 'Доп. эспрессо', priceDeltaRub: 50, isAvailable: true },
      { id: 'cinnamon', label: 'Корица', priceDeltaRub: 0, isAvailable: true },
    ],
  },
];

function createDetails(): Record<string, ProductDetailPayload> {
  return Object.fromEntries(
    baseProducts.map((product) => [
      product.id,
      {
        product,
        sizes: product.categoryId === 'pastry' ? [{ code: 'piece', label: '1 шт.', priceRub: 190 }] : sizes,
        modifierGroups: product.categoryId === 'pastry' ? [] : modifierGroups,
      },
    ]),
  );
}

function createSlots(): Slot[] {
  return [
    { start: todayAt(10, 0), end: todayAt(10, 10), capacityLeft: 3, isAvailable: true },
    { start: todayAt(10, 10), end: todayAt(10, 20), capacityLeft: 2, isAvailable: true },
    { start: todayAt(10, 20), end: todayAt(10, 30), capacityLeft: 0, isAvailable: false },
    { start: todayAt(10, 30), end: todayAt(10, 40), capacityLeft: 4, isAvailable: true },
    { start: todayAt(10, 40), end: todayAt(10, 50), capacityLeft: 1, isAvailable: true },
  ];
}

function emptyCart(): CartPayload {
  return { items: [], subtotalRub: 0, totalRub: 0, version: 1 };
}

function buildInitialStore(search: URLSearchParams): StoreState {
  const blocked = search.get('state') === 'blocked';

  return {
    session: {
      userId: 'customer-1',
      displayName: 'Мария',
      isBlocked: blocked,
      telegramId: '987654321',
      isTelegramContext: false,
    },
    categories: search.get('menu') === 'empty' ? [] : baseCategories,
    products: search.get('menu') === 'empty' ? [] : baseProducts,
    details: createDetails(),
    cart: emptyCart(),
    slots: search.get('slots') === 'empty' ? [] : createSlots(),
    orders: [],
  };
}

function computeTotals(items: CartItem[]) {
  const subtotalRub = items.reduce((total, item) => total + item.totalPriceRub, 0);
  return {
    subtotalRub,
    totalRub: subtotalRub,
  };
}

function loadStoredState(search: URLSearchParams) {
  const raw = window.localStorage.getItem(STORAGE_KEY);

  if (!raw) {
    return buildInitialStore(search);
  }

  try {
    const parsed = JSON.parse(raw) as StoreState;
    return {
      ...buildInitialStore(search),
      ...parsed,
    };
  } catch {
    return buildInitialStore(search);
  }
}

function persist(state: StoreState) {
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
}

function humanModifierLabels(product: ProductDetailPayload, ids: string[]) {
  return product.modifierGroups
    .flatMap((group) => group.options)
    .filter((option) => ids.includes(option.id))
    .map((option) => option.label);
}

export class MockCustomerStore {
  private state: StoreState;
  private readonly search: URLSearchParams;

  constructor(search: URLSearchParams) {
    this.search = search;
    this.state = loadStoredState(search);
  }

  getSession() {
    if (this.search.get('auth') === 'error') {
      throw new Error('AUTH_CONTEXT_MISSING');
    }

    return this.state.session;
  }

  getMenu(categoryId?: string): MenuPayload {
    const products = categoryId
      ? this.state.products.filter((product) => product.categoryId === categoryId)
      : this.state.products;

    return {
      categories: this.state.categories,
      products,
    };
  }

  getProduct(productId: string) {
    const detail = this.state.details[productId];

    if (!detail) {
      throw new Error('PRODUCT_NOT_FOUND');
    }

    return detail;
  }

  getCart(): CartPayload {
    const items =
      this.search.get('cartConflict') === '1'
        ? this.state.cart.items.map((item, index) => ({
            ...item,
            availabilityConflict: index === 0,
          }))
        : this.state.cart.items;

    return {
      ...this.state.cart,
      items,
    };
  }

  addToCart(productId: string, config: ProductConfiguratorState) {
    const detail = this.getProduct(productId);
    const size = detail.sizes.find((entry) => entry.code === config.sizeCode);

    if (!size) {
      throw new Error('SIZE_REQUIRED');
    }

    const modifierOptions = detail.modifierGroups.flatMap((group) => group.options);
    const modifierDelta = modifierOptions
      .filter((option) => config.modifierOptionIds.includes(option.id))
      .reduce((total, option) => total + option.priceDeltaRub, 0);

    const unitPriceRub = size.priceRub + modifierDelta;
    const nextItem: CartItem = {
      cartItemId: crypto.randomUUID(),
      productId,
      productName: detail.product.name,
      sizeCode: config.sizeCode,
      sizeLabel: size.label,
      qty: config.qty,
      modifierOptionIds: config.modifierOptionIds,
      modifierLabels: humanModifierLabels(detail, config.modifierOptionIds),
      unitPriceRub,
      totalPriceRub: unitPriceRub * config.qty,
    };

    const items = [...this.state.cart.items, nextItem];
    const totals = computeTotals(items);

    this.state = {
      ...this.state,
      cart: {
        ...this.state.cart,
        ...totals,
        items,
        version: this.state.cart.version + 1,
      },
    };
    persist(this.state);

    return this.getCart();
  }

  updateCartItem(cartItemId: string, patch: Partial<Pick<CartItem, 'qty' | 'sizeCode' | 'modifierOptionIds'>>) {
    const items = this.state.cart.items.map((item) => {
      if (item.cartItemId !== cartItemId) {
        return item;
      }

      const detail = this.getProduct(item.productId);
      const nextSizeCode = patch.sizeCode ?? item.sizeCode;
      const nextQty = patch.qty ?? item.qty;
      const nextModifierIds = patch.modifierOptionIds ?? item.modifierOptionIds;
      const size = detail.sizes.find((entry) => entry.code === nextSizeCode);

      if (!size) {
        throw new Error('SIZE_REQUIRED');
      }

      const optionDelta = detail.modifierGroups
        .flatMap((group) => group.options)
        .filter((option) => nextModifierIds.includes(option.id))
        .reduce((total, option) => total + option.priceDeltaRub, 0);

      const unitPriceRub = size.priceRub + optionDelta;

      return {
        ...item,
        sizeCode: nextSizeCode,
        sizeLabel: size.label,
        qty: nextQty,
        modifierOptionIds: nextModifierIds,
        modifierLabels: humanModifierLabels(detail, nextModifierIds),
        unitPriceRub,
        totalPriceRub: unitPriceRub * nextQty,
      };
    });

    const totals = computeTotals(items);
    this.state = {
      ...this.state,
      cart: {
        ...this.state.cart,
        ...totals,
        items,
        version: this.state.cart.version + 1,
      },
    };
    persist(this.state);

    return this.getCart();
  }

  removeCartItem(cartItemId: string) {
    const items = this.state.cart.items.filter((item) => item.cartItemId !== cartItemId);
    const totals = computeTotals(items);

    this.state = {
      ...this.state,
      cart: {
        ...this.state.cart,
        ...totals,
        items,
        version: this.state.cart.version + 1,
      },
    };
    persist(this.state);
  }

  getSlots() {
    return {
      slots: this.state.slots,
    };
  }

  createOrder(slotStart: string, cartVersion: number) {
    if (!this.state.cart.items.length) {
      throw new Error('CART_EMPTY');
    }

    if (cartVersion !== this.state.cart.version) {
      throw new Error('CART_VERSION_CONFLICT');
    }

    const slot = this.state.slots.find((entry) => entry.start === slotStart && entry.isAvailable);

    if (!slot) {
      throw new Error('SLOT_UNAVAILABLE');
    }

    const orderId = `ord-${String(this.state.orders.length + 1).padStart(3, '0')}`;
    const order: OrderSummary = {
      orderId,
      status: 'Created',
      slotStart,
      totalRub: this.state.cart.totalRub,
      createdAt: new Date().toISOString(),
      itemCount: this.state.cart.items.length,
    };
    const detail: OrderDetail = {
      order,
      items: this.state.cart.items,
      statusHistory: [
        {
          status: 'Created',
          changedAt: new Date().toISOString(),
          changedBy: 'system',
        },
      ],
    };

    this.state = {
      ...this.state,
      cart: emptyCart(),
      orders: [detail, ...this.state.orders],
      slots: this.state.slots.map((entry) =>
        entry.start === slotStart
          ? { ...entry, capacityLeft: Math.max(0, entry.capacityLeft - 1), isAvailable: entry.capacityLeft - 1 > 0 }
          : entry,
      ),
    };
    persist(this.state);

    return {
      orderId,
      status: 'Created',
      slotStart,
      totalRub: detail.order.totalRub,
    };
  }

  listOrders() {
    return {
      orders: this.state.orders.map((entry) => entry.order),
    };
  }

  getOrder(orderId: string) {
    const order = this.state.orders.find((entry) => entry.order.orderId === orderId);

    if (!order) {
      throw new Error('ORDER_NOT_FOUND');
    }

    return order;
  }
}
