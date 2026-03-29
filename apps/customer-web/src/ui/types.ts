export type Screen = 'menu' | 'history' | 'slots' | 'result';
export type SessionState = 'loading' | 'ready' | 'blocked' | 'error';
export type ApiMode = 'auto' | 'live' | 'mock';

export interface Session {
  userId: string;
  displayName: string;
  isBlocked: boolean;
  telegramId: string;
  isTelegramContext: boolean;
}

export interface Category {
  id: string;
  name: string;
  description: string;
}

export interface ProductCard {
  id: string;
  categoryId: string;
  name: string;
  description: string;
  priceFromRub: number;
  badge?: string;
  isAvailable: boolean;
}

export interface MenuPayload {
  categories: Category[];
  products: ProductCard[];
}

export interface ModifierOption {
  id: string;
  label: string;
  priceDeltaRub: number;
  isAvailable: boolean;
}

export interface ModifierGroup {
  id: string;
  name: string;
  minSelect: number;
  maxSelect: number;
  options: ModifierOption[];
}

export interface ProductSize {
  code: string;
  label: string;
  priceRub: number;
}

export interface ProductDetailPayload {
  product: ProductCard;
  sizes: ProductSize[];
  modifierGroups: ModifierGroup[];
}

export interface CartItem {
  cartItemId: string;
  productId: string;
  productName: string;
  sizeCode: string;
  sizeLabel: string;
  qty: number;
  modifierOptionIds: string[];
  modifierLabels: string[];
  unitPriceRub: number;
  totalPriceRub: number;
  availabilityConflict?: boolean;
}

export interface CartPayload {
  items: CartItem[];
  subtotalRub: number;
  totalRub: number;
  version: number;
}

export interface Slot {
  start: string;
  end: string;
  capacityLeft: number;
  isAvailable: boolean;
}

export interface SlotPayload {
  slots: Slot[];
}

export interface OrderSummary {
  orderId: string;
  status: string;
  slotStart: string;
  totalRub: number;
  createdAt: string;
  itemCount: number;
  rejectReason?: string;
}

export interface StatusEntry {
  status: string;
  changedAt: string;
  changedBy: string;
}

export interface OrderDetail {
  order: OrderSummary;
  items: CartItem[];
  statusHistory: StatusEntry[];
}

export interface OrdersPayload {
  orders: OrderSummary[];
}

export interface CreateOrderResult {
  orderId: string;
  status: string;
  slotStart: string;
  totalRub: number;
}

export interface ProductConfiguratorState {
  sizeCode: string;
  modifierOptionIds: string[];
  qty: number;
}
