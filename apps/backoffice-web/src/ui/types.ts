export type ApiMode = 'auto' | 'live' | 'mock';
export type Role = 'barista' | 'administrator';
export type SessionState = 'loading' | 'ready' | 'forbidden' | 'blocked' | 'error';
export type TabId = 'orders' | 'availability' | 'menu' | 'users' | 'settings';
export type OrderStatus = 'Created' | 'Confirmed' | 'Rejected' | 'Ready for pickup' | 'Closed';

export interface Session {
  userId: string;
  displayName: string;
  role: Role;
  allowedTabs: TabId[];
  isBlocked?: boolean;
}

export interface OrderItem {
  name: string;
  qty: number;
  sizeLabel: string;
}

export interface OrderRecord {
  orderId: string;
  customerName: string;
  slotStart: string;
  totalRub: number;
  status: OrderStatus;
  rejectReason?: string;
  itemCount: number;
  items: OrderItem[];
  updatedAt: string;
}

export interface OrdersPayload {
  orders: OrderRecord[];
  counters: Partial<Record<OrderStatus, number>>;
}

export interface AvailabilityEntity {
  entityId: string;
  entityType: 'product' | 'modifier-group' | 'modifier-option';
  name: string;
  category: string;
  isActive: boolean;
}

export interface AvailabilityPayload {
  entities: AvailabilityEntity[];
}

export interface MenuCategory {
  id: string;
  name: string;
  sortOrder: number;
  isActive: boolean;
}

export interface MenuProduct {
  id: string;
  categoryId: string;
  name: string;
  description: string;
  sizeLabels: string[];
  modifierGroupIds: string[];
  isActive: boolean;
}

export interface MenuPayload {
  categories: MenuCategory[];
  products: MenuProduct[];
  modifierGroups: { id: string; name: string }[];
}

export interface UserRecord {
  id: string;
  displayName: string;
  telegramId: string;
  role: 'customer' | Role;
  isBlocked: boolean;
}

export interface UsersPayload {
  users: UserRecord[];
}

export interface SettingsPayload {
  workingHours: {
    openTime: string;
    closeTime: string;
  };
  slotStepMinutes: number;
  slotCapacity: number;
}

export interface RejectDialogState {
  orderId: string;
  reason: string;
}

export interface MenuDialogState {
  type: 'category' | 'product';
  mode: 'create' | 'edit';
  id?: string;
  categoryId: string;
  name: string;
  description: string;
  sizeLabels: string;
}

export interface UserDialogState {
  id: string;
  role: 'customer' | Role;
  isBlocked: boolean;
}
