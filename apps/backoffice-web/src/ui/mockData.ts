import type {
  AvailabilityEntity,
  AvailabilityPayload,
  MenuCategory,
  MenuDialogState,
  MenuPayload,
  MenuProduct,
  OrderRecord,
  OrderStatus,
  OrdersPayload,
  Role,
  Session,
  SettingsPayload,
  UserDialogState,
  UserRecord,
  UsersPayload,
} from './types';

function nowIso() {
  return new Date().toISOString();
}

function countersFromOrders(orders: OrderRecord[]) {
  return orders.reduce<Partial<Record<OrderStatus, number>>>((acc, order) => {
    acc[order.status] = (acc[order.status] ?? 0) + 1;
    return acc;
  }, {});
}

export class MockBackofficeStore {
  private readonly searchParams: URLSearchParams;
  private orders: OrderRecord[];
  private availability: AvailabilityEntity[];
  private categories: MenuCategory[];
  private products: MenuProduct[];
  private users: UserRecord[];
  private settings: SettingsPayload;

  constructor(searchParams: URLSearchParams) {
    this.searchParams = searchParams;
    this.orders = [
      {
        orderId: 'ORD-24031',
        customerName: 'Алина',
        slotStart: new Date(new Date().setHours(10, 10, 0, 0)).toISOString(),
        totalRub: 760,
        status: 'Created',
        itemCount: 2,
        items: [
          { name: 'Капучино', qty: 1, sizeLabel: 'M / 350 мл' },
          { name: 'Круассан миндальный', qty: 1, sizeLabel: 'Standard' },
        ],
        updatedAt: nowIso(),
      },
      {
        orderId: 'ORD-24022',
        customerName: 'Игорь',
        slotStart: new Date(new Date().setHours(10, 30, 0, 0)).toISOString(),
        totalRub: 490,
        status: 'Confirmed',
        itemCount: 1,
        items: [{ name: 'Флэт уайт', qty: 1, sizeLabel: 'S / 250 мл' }],
        updatedAt: nowIso(),
      },
      {
        orderId: 'ORD-24018',
        customerName: 'Мария',
        slotStart: new Date(new Date().setHours(9, 50, 0, 0)).toISOString(),
        totalRub: 890,
        status: 'Ready for pickup',
        itemCount: 3,
        items: [
          { name: 'Раф ванильный', qty: 2, sizeLabel: 'M / 350 мл' },
          { name: 'Чизкейк баскский', qty: 1, sizeLabel: 'Standard' },
        ],
        updatedAt: nowIso(),
      },
      {
        orderId: 'ORD-24004',
        customerName: 'Никита',
        slotStart: new Date(new Date().setHours(9, 20, 0, 0)).toISOString(),
        totalRub: 430,
        status: 'Rejected',
        rejectReason: 'Не хватает миндального молока',
        itemCount: 1,
        items: [{ name: 'Латте', qty: 1, sizeLabel: 'M / 350 мл' }],
        updatedAt: nowIso(),
      },
    ];
    this.availability = [
      { entityId: 'prod-1', entityType: 'product', name: 'Капучино', category: 'Напитки', isActive: true },
      { entityId: 'prod-2', entityType: 'product', name: 'Матча латте', category: 'Напитки', isActive: false },
      { entityId: 'mod-1', entityType: 'modifier-option', name: 'Овсяное молоко', category: 'Модификаторы', isActive: true },
      { entityId: 'mod-2', entityType: 'modifier-option', name: 'Карамельный сироп', category: 'Модификаторы', isActive: true },
    ];
    this.categories = [
      { id: 'cat-drinks', name: 'Напитки', sortOrder: 1, isActive: true },
      { id: 'cat-desserts', name: 'Десерты', sortOrder: 2, isActive: true },
    ];
    this.products = [
      {
        id: 'prod-1',
        categoryId: 'cat-drinks',
        name: 'Капучино',
        description: 'Эспрессо, молоко и шелковистая пена.',
        sizeLabels: ['S / 250 мл', 'M / 350 мл'],
        modifierGroupIds: ['milk', 'syrup'],
        isActive: true,
      },
      {
        id: 'prod-3',
        categoryId: 'cat-desserts',
        name: 'Тарталетка с лимоном',
        description: 'Песочная основа, лимонный курд, меренга.',
        sizeLabels: ['Standard'],
        modifierGroupIds: [],
        isActive: true,
      },
    ];
    this.users = [
      { id: 'u-1', displayName: 'Старший администратор', telegramId: '2000001', role: 'administrator', isBlocked: false },
      { id: 'u-2', displayName: 'Артём', telegramId: '2000002', role: 'barista', isBlocked: false },
      { id: 'u-3', displayName: 'Елена', telegramId: '2000003', role: 'customer', isBlocked: true },
    ];
    this.settings = {
      workingHours: {
        openTime: '08:00',
        closeTime: '21:00',
      },
      slotStepMinutes: 10,
      slotCapacity: 8,
    };
  }

  getSession(): Session {
    const state = this.searchParams.get('state');
    const role = (this.searchParams.get('role') as Role | null) ?? 'administrator';

    if (state === 'blocked') {
      return {
        userId: 'blocked',
        displayName: role === 'barista' ? 'Бариста' : 'Администратор',
        role,
        allowedTabs: [],
        isBlocked: true,
      };
    }

    if (state === 'forbidden') {
      return {
        userId: 'forbidden',
        displayName: 'Нет доступа',
        role: 'barista',
        allowedTabs: [],
      };
    }

    return {
      userId: role === 'barista' ? 'barista-1' : 'admin-1',
      displayName: role === 'barista' ? 'Артём' : 'Старший администратор',
      role,
      allowedTabs: role === 'barista' ? ['orders', 'availability'] : ['orders', 'availability', 'menu', 'users', 'settings'],
    };
  }

  listOrders(status?: OrderStatus) {
    const orders = status ? this.orders.filter((order) => order.status === status) : this.orders;
    return {
      orders,
      counters: countersFromOrders(this.orders),
    } satisfies OrdersPayload;
  }

  updateOrderStatus(orderId: string, nextStatus: OrderStatus, reason?: string) {
    this.orders = this.orders.map((order) => {
      if (order.orderId !== orderId) {
        return order;
      }

      return {
        ...order,
        status: nextStatus,
        rejectReason: nextStatus === 'Rejected' ? reason : undefined,
        updatedAt: nowIso(),
      };
    });

    return this.listOrders();
  }

  getAvailability(search = '') {
    const normalized = search.trim().toLowerCase();
    const entities = normalized
      ? this.availability.filter((entity) => `${entity.name} ${entity.category}`.toLowerCase().includes(normalized))
      : this.availability;
    return { entities } satisfies AvailabilityPayload;
  }

  toggleAvailability(entityId: string, isActive: boolean) {
    this.availability = this.availability.map((entity) =>
      entity.entityId === entityId ? { ...entity, isActive } : entity,
    );
    return this.getAvailability();
  }

  getMenu() {
    return {
      categories: this.categories,
      products: this.products,
      modifierGroups: [
        { id: 'milk', name: 'Молоко' },
        { id: 'syrup', name: 'Сиропы' },
      ],
    } satisfies MenuPayload;
  }

  saveMenuDialog(dialog: MenuDialogState) {
    if (dialog.type === 'category') {
      if (dialog.mode === 'create') {
        this.categories = [
          ...this.categories,
          {
            id: `cat-${Date.now()}`,
            name: dialog.name,
            sortOrder: this.categories.length + 1,
            isActive: true,
          },
        ];
      } else {
        this.categories = this.categories.map((category) =>
          category.id === dialog.id ? { ...category, name: dialog.name } : category,
        );
      }
    } else {
      const sizeLabels = dialog.sizeLabels
        .split(',')
        .map((entry) => entry.trim())
        .filter(Boolean);

      if (dialog.mode === 'create') {
        this.products = [
          ...this.products,
          {
            id: `prod-${Date.now()}`,
            categoryId: dialog.categoryId,
            name: dialog.name,
            description: dialog.description,
            sizeLabels: sizeLabels.length ? sizeLabels : ['Standard'],
            modifierGroupIds: [],
            isActive: true,
          },
        ];
      } else {
        this.products = this.products.map((product) =>
          product.id === dialog.id
            ? {
                ...product,
                categoryId: dialog.categoryId,
                name: dialog.name,
                description: dialog.description,
                sizeLabels: sizeLabels.length ? sizeLabels : ['Standard'],
              }
            : product,
        );
      }
    }

    return this.getMenu();
  }

  listUsers(search = '') {
    const normalized = search.trim().toLowerCase();
    const users = normalized
      ? this.users.filter((user) => `${user.displayName} ${user.telegramId}`.toLowerCase().includes(normalized))
      : this.users;
    return { users } satisfies UsersPayload;
  }

  saveUserDialog(dialog: UserDialogState) {
    this.users = this.users.map((user) =>
      user.id === dialog.id ? { ...user, role: dialog.role, isBlocked: dialog.isBlocked } : user,
    );
    return this.listUsers();
  }

  getSettings() {
    return this.settings;
  }

  saveSettings(payload: Pick<SettingsPayload, 'workingHours' | 'slotCapacity'>) {
    this.settings = {
      ...this.settings,
      workingHours: payload.workingHours,
      slotCapacity: payload.slotCapacity,
    };
    return this.getSettings();
  }
}
