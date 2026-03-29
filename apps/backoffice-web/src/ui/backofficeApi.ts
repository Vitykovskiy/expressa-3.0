import { MockBackofficeStore } from './mockData';
import type {
  ApiMode,
  AvailabilityPayload,
  MenuDialogState,
  MenuPayload,
  OrderStatus,
  OrdersPayload,
  Session,
  SettingsPayload,
  UserDialogState,
  UsersPayload,
} from './types';

declare global {
  interface Window {
    __EXPRESSA_CONFIG__?: {
      apiBaseUrl?: string;
    };
  }
}

interface ApiConfig {
  apiBaseUrl: string;
  mode: ApiMode;
}

async function parseJson<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    throw new Error(payload?.reason ?? payload?.status ?? `HTTP_${response.status}`);
  }

  return response.json() as Promise<T>;
}

export class BackofficeApi {
  private readonly config: ApiConfig;
  private readonly mockStore: MockBackofficeStore;
  private resolvedMode: Exclude<ApiMode, 'auto'> | null;

  constructor(config?: Partial<ApiConfig>) {
    const searchParams = new URLSearchParams(window.location.search);
    this.config = {
      apiBaseUrl: window.__EXPRESSA_CONFIG__?.apiBaseUrl ?? '/api',
      mode:
        searchParams.get('preview') === '1'
          ? 'mock'
          : searchParams.get('api') === 'live'
            ? 'live'
            : searchParams.get('api') === 'mock'
              ? 'mock'
              : 'auto',
      ...config,
    };
    this.mockStore = new MockBackofficeStore(searchParams);
    this.resolvedMode = this.config.mode === 'auto' ? null : this.config.mode;
  }

  getMode() {
    return this.resolvedMode ?? 'live';
  }

  private async runLive<T>(path: string, init?: RequestInit) {
    const response = await fetch(`${this.config.apiBaseUrl}${path}`, {
      headers: {
        'Content-Type': 'application/json',
      },
      ...init,
    });

    return parseJson<T>(response);
  }

  private async withFallback<T>(operation: () => Promise<T>, fallback: () => T | Promise<T>) {
    if (this.resolvedMode === 'mock') {
      return fallback();
    }

    try {
      const result = await operation();
      this.resolvedMode = 'live';
      return result;
    } catch (error) {
      if (this.config.mode === 'live') {
        throw error;
      }

      this.resolvedMode = 'mock';
      return fallback();
    }
  }

  getSession(): Promise<Session> {
    return this.withFallback(
      () => this.runLive<Session>('/backoffice/session'),
      () => this.mockStore.getSession(),
    );
  }

  getOrders(status?: OrderStatus) {
    const query = status ? `?status=${encodeURIComponent(status)}` : '';
    return this.withFallback(
      () => this.runLive<OrdersPayload>(`/backoffice/orders${query}`),
      () => this.mockStore.listOrders(status),
    );
  }

  updateOrderStatus(orderId: string, action: 'confirm' | 'reject' | 'ready' | 'close', reason?: string) {
    const actionToStatus = {
      confirm: 'Confirmed',
      reject: 'Rejected',
      ready: 'Ready for pickup',
      close: 'Closed',
    } satisfies Record<typeof action, OrderStatus>;

    return this.withFallback(
      () =>
        this.runLive<OrdersPayload>(`/backoffice/orders/${orderId}/${action}`, {
          method: 'POST',
          body: JSON.stringify(reason ? { reason } : {}),
        }),
      () => this.mockStore.updateOrderStatus(orderId, actionToStatus[action], reason),
    );
  }

  getAvailability(search = '') {
    const query = search ? `?search=${encodeURIComponent(search)}` : '';
    return this.withFallback(
      () => this.runLive<AvailabilityPayload>(`/backoffice/availability${query}`),
      () => this.mockStore.getAvailability(search),
    );
  }

  toggleAvailability(entityType: string, entityId: string, isActive: boolean) {
    return this.withFallback(
      async () => {
        await this.runLive(`/backoffice/availability/${entityType}/${entityId}`, {
          method: 'PATCH',
          body: JSON.stringify({ isActive }),
        });
        return this.getAvailability();
      },
      () => this.mockStore.toggleAvailability(entityId, isActive),
    );
  }

  getMenu() {
    return this.withFallback(
      () => this.runLive<MenuPayload>('/backoffice/menu'),
      () => this.mockStore.getMenu(),
    );
  }

  saveMenuDialog(dialog: MenuDialogState) {
    const isCategory = dialog.type === 'category';
    const isCreate = dialog.mode === 'create';
    const path = isCategory
      ? isCreate
        ? '/backoffice/menu/categories'
        : `/backoffice/menu/categories/${dialog.id}`
      : isCreate
        ? '/backoffice/menu/products'
        : `/backoffice/menu/products/${dialog.id}`;

    return this.withFallback(
      async () => {
        await this.runLive(path, {
          method: isCreate ? 'POST' : 'PATCH',
          body: JSON.stringify(
            isCategory
              ? { name: dialog.name, sortOrder: 0 }
              : {
                  categoryId: dialog.categoryId,
                  name: dialog.name,
                  description: dialog.description,
                  sizes: dialog.sizeLabels
                    .split(',')
                    .map((entry) => entry.trim())
                    .filter(Boolean),
                  modifierGroupIds: [],
                },
          ),
        });
        return this.getMenu();
      },
      () => this.mockStore.saveMenuDialog(dialog),
    );
  }

  getUsers(search = '') {
    const query = search ? `?search=${encodeURIComponent(search)}` : '';
    return this.withFallback(
      () => this.runLive<UsersPayload>(`/backoffice/users${query}`),
      () => this.mockStore.listUsers(search),
    );
  }

  saveUserDialog(dialog: UserDialogState) {
    return this.withFallback(
      async () => {
        await this.runLive(`/backoffice/users/${dialog.id}/role`, {
          method: 'PATCH',
          body: JSON.stringify({ role: dialog.role }),
        });
        await this.runLive(`/backoffice/users/${dialog.id}/block`, {
          method: 'PATCH',
          body: JSON.stringify({ isBlocked: dialog.isBlocked }),
        });
        return this.getUsers();
      },
      () => this.mockStore.saveUserDialog(dialog),
    );
  }

  getSettings() {
    return this.withFallback(
      () => this.runLive<SettingsPayload>('/backoffice/settings'),
      () => this.mockStore.getSettings(),
    );
  }

  saveSettings(settings: Pick<SettingsPayload, 'workingHours' | 'slotCapacity'>) {
    return this.withFallback(
      () =>
        this.runLive<SettingsPayload>('/backoffice/settings', {
          method: 'PATCH',
          body: JSON.stringify({
            openTime: settings.workingHours.openTime,
            closeTime: settings.workingHours.closeTime,
            slotCapacity: settings.slotCapacity,
          }),
        }),
      () => this.mockStore.saveSettings(settings),
    );
  }
}
