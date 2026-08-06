export interface UserInfo {
  id: string;
  phone_number: string;
  full_name: string;
  role: string;
  branch_id: string | null;
  created_at: string;
}

export interface OtpRequestResult {
  message: string;
  phone_number: string;
  debug_otp?: string;
}

export interface LoginResult {
  access_token: string;
  role: string;
  user_id: string;
}

export interface Analytics {
  period: string;
  start_date: string;
  total_revenue: string;
  delivered_volume: number;
  pending_deliveries: number;
  active_drivers: number;
}

export interface OrderItem {
  id: string;
  order_id: string;
  product_id: string;
  quantity: number;
  unit_price: string;
}

export interface Order {
  id: string;
  customer_id: string;
  driver_id: string | null;
  branch_id: string | null;
  address_id: string;
  status: string;
  total_amount: string;
  payment_status: string;
  payment_method: string;
  empty_bottles_returned: number;
  created_at: string;
  customer_name?: string;
  customer_phone?: string;
  driver_name?: string | null;
  items: OrderItem[];
}

export interface Product {
  id: string;
  name: string;
  description: string | null;
  price: string;
  deposit_fee: string;
  stock_quantity: number;
  created_at?: string;
}

export interface ProductInput {
  name: string;
  description?: string | null;
  price: number;
  deposit_fee?: number;
  stock_quantity?: number;
}

export interface BranchInventory {
  id: string;
  branch_id: string;
  full_bottles: number;
  empty_bottles: number;
  caps_count: number;
  labels_count: number;
  water_liters: number;
  updated_at: string;
  branch_name?: string;
}

export interface InventoryData {
  branches: BranchInventory[];
  totals: {
    full_bottles: number;
    empty_bottles: number;
    caps_count: number;
    labels_count: number;
    water_liters: number;
  };
  products: Product[];
}

export interface StaffMember {
  id: string;
  full_name: string;
  role: string;
  branch_id: string | null;
  phone_number?: string;
  created_at?: string;
}

export interface StaffInput {
  full_name: string;
  role: string;
  branch_id: string | null;
  phone_number?: string;
}

export interface InventoryInput {
  full_bottles?: number;
  empty_bottles?: number;
  caps_count?: number;
  labels_count?: number;
  water_liters?: number;
}

export interface Branch {
  id: string;
  name: string;
  address: string;
  is_active: boolean;
  staff: StaffMember[];
}

export interface BranchInput {
  name: string;
  address: string;
  latitude: number;
  longitude: number;
  is_active?: boolean;
}

export interface BranchData {
  branches: Branch[];
  staff: StaffMember[];
}

export interface Driver {
  id: string;
  full_name: string;
  phone_number: string;
  branch_id: string | null;
  location: unknown;
  last_ping: string | null;
}
