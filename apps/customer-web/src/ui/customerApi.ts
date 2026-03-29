import type {
  ApiMode,
  CartPayload,
  CreateOrderResult,
  MenuPayload,
  OrderDetail,
  OrdersPayload,
  ProductConfiguratorState,
  ProductDetailPayload,
  Session,
  SlotPayload,
} from './types';
import { MockCustomerStore } from './mockData';

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

export class CustomerApi {
  private readonly config: ApiConfig;
  private readonly mockStore: MockCustomerStore;
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
    this.mockStore = new MockCustomerStore(searchParams);
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

  async getSession(): Promise<Session> {
    return this.withFallback(
      () => this.runLive<Session>('/customer/session'),
      () => this.mockStore.getSession(),
    );
  }

  async getMenu(categoryId?: string): Promise<MenuPayload> {
    const query = categoryId ? `?categoryId=${encodeURIComponent(categoryId)}` : '';
    return this.withFallback(
      () => this.runLive<MenuPayload>(`/customer/menu${query}`),
      () => this.mockStore.getMenu(categoryId),
    );
  }

  async getProduct(productId: string): Promise<ProductDetailPayload> {
    return this.withFallback(
      () => this.runLive<ProductDetailPayload>(`/customer/products/${productId}`),
      () => this.mockStore.getProduct(productId),
    );
  }

  async getCart(): Promise<CartPayload> {
    return this.withFallback(
      () => this.runLive<CartPayload>('/customer/cart'),
      () => this.mockStore.getCart(),
    );
  }

  async addCartItem(productId: string, config: ProductConfiguratorState): Promise<CartPayload> {
    return this.withFallback(
      async () => {
        const payload = await this.runLive<{ cart: CartPayload }>('/customer/cart/items', {
          method: 'POST',
          body: JSON.stringify({
            productId,
            sizeCode: config.sizeCode,
            qty: config.qty,
            modifierOptionIds: config.modifierOptionIds,
          }),
        });
        return payload.cart;
      },
      () => this.mockStore.addToCart(productId, config),
    );
  }

  async updateCartItem(
    cartItemId: string,
    patch: Partial<{ qty: number; sizeCode: string; modifierOptionIds: string[] }>,
  ): Promise<CartPayload> {
    return this.withFallback(
      async () => {
        const payload = await this.runLive<{ cart: CartPayload }>(`/customer/cart/items/${cartItemId}`, {
          method: 'PATCH',
          body: JSON.stringify(patch),
        });
        return payload.cart;
      },
      () => this.mockStore.updateCartItem(cartItemId, patch),
    );
  }

  async removeCartItem(cartItemId: string): Promise<CartPayload> {
    return this.withFallback(
      async () => {
        await fetch(`${this.config.apiBaseUrl}/customer/cart/items/${cartItemId}`, {
          method: 'DELETE',
        });
        return this.getCart();
      },
      async () => {
        this.mockStore.removeCartItem(cartItemId);
        return this.mockStore.getCart();
      },
    );
  }

  async getSlots(): Promise<SlotPayload> {
    return this.withFallback(
      () => this.runLive<SlotPayload>('/customer/slots?date=today'),
      () => this.mockStore.getSlots(),
    );
  }

  async createOrder(slotStart: string, cartVersion: number): Promise<CreateOrderResult> {
    return this.withFallback(
      () =>
        this.runLive<CreateOrderResult>('/customer/orders', {
          method: 'POST',
          body: JSON.stringify({ slotStart, cartVersion }),
        }),
      () => this.mockStore.createOrder(slotStart, cartVersion),
    );
  }

  async listOrders(): Promise<OrdersPayload> {
    return this.withFallback(
      () => this.runLive<OrdersPayload>('/customer/orders'),
      () => this.mockStore.listOrders(),
    );
  }

  async getOrder(orderId: string): Promise<OrderDetail> {
    return this.withFallback(
      () => this.runLive<OrderDetail>(`/customer/orders/${orderId}`),
      () => this.mockStore.getOrder(orderId),
    );
  }
}
