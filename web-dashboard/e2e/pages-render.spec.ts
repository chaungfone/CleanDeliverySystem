import { test, expect, type Page } from '@playwright/test';

// Regression guard for "blank page" reports: every dashboard route must render
// its page header, even with edge-case data (nullable inventory counts, etc.).
const BASE_URL = process.env.E2E_BASE_URL || 'http://localhost:4173';

const ADMIN = {
  id: 'u1',
  phone_number: '+959123456789',
  full_name: 'Aung Admin',
  role: 'ADMIN',
  branch_id: null,
  created_at: new Date().toISOString(),
};

function stubJson(page: Page, pattern: string, body: unknown) {
  return page.route(pattern, (route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(body) }),
  );
}

const ORDERS = [
  {
    id: 'ORD-1',
    customer_id: 'u2',
    driver_id: 'u3',
    branch_id: null,
    address_id: 'a1',
    status: 'DELIVERED',
    total_amount: '12000',
    payment_status: 'PAID',
    payment_method: 'COD',
    empty_bottles_returned: 2,
    created_at: new Date().toISOString(),
    customer_name: 'Ma Ma',
    customer_phone: '09123456789',
    driver_name: 'U Kyaw',
    items: [{ id: 'i1', order_id: 'o1', product_id: 'p1', quantity: 2, unit_price: '5000' }],
  },
];
const PRODUCTS = [
  { id: 'p1', name: '1.5L Purified Water', description: null, price: '5000', deposit_fee: '1000', stock_quantity: 10 },
];
const INVENTORY = {
  branches: [
    {
      id: 'b1',
      branch_id: 'b1',
      full_bottles: null, // nullable in enterprise migration
      empty_bottles: 0,
      caps_count: 0,
      labels_count: 0,
      water_liters: null,
      updated_at: new Date().toISOString(),
      branch_name: 'Yangon Main',
    },
  ],
  totals: { full_bottles: 0, empty_bottles: 0, caps_count: 0, labels_count: 0, water_liters: 0 },
  products: PRODUCTS,
};
const BRANCHES = { branches: [{ id: 'b1', name: 'Yangon Main', address: 'Downtown', is_active: true, staff: [] }], staff: [] };
const STAFF = [
  { id: 'u1', full_name: 'Aung Admin', role: 'ADMIN', branch_id: null, phone_number: '09123456789', created_at: new Date().toISOString() },
];

const ROUTES: [string, RegExp][] = [
  ['/', /Executive Overview/i],
  ['/orders', /Order Management/i],
  ['/fleet', /Live Fleet Tracker/i],
  ['/inventory', /Inventory Management/i],
  ['/products', /Product Management/i],
  ['/branches', /Branch Management/i],
  ['/staff', /Staff Management/i],
  ['/settings', /Settings/i],
];

for (const [path, title] of ROUTES) {
  test(`page renders: ${path}`, async ({ page }) => {
    await page.addInitScript(() => localStorage.setItem('cd_dashboard_token', 'demo:+959123456789'));
    await stubJson(page, '**/api/v1/auth/me', ADMIN);
    await stubJson(page, '**/api/v1/admin/orders', ORDERS);
    await stubJson(page, '**/api/v1/admin/products', PRODUCTS);
    await stubJson(page, '**/api/v1/admin/inventory', INVENTORY);
    await stubJson(page, '**/api/v1/admin/branches', BRANCHES);
    await stubJson(page, '**/api/v1/admin/staff', STAFF);
    await stubJson(page, '**/api/v1/admin/drivers', []);
    await stubJson(page, '**/api/v1/admin/dashboard/analytics', {
      period: 'daily',
      start_date: new Date().toISOString(),
      total_revenue: '12000',
      delivered_volume: 1,
      pending_deliveries: 0,
      active_drivers: 1,
    });

    await page.goto(`${BASE_URL}${path}`);
    const h2 = page.locator('h2').first();
    await expect(h2).toBeVisible({ timeout: 8000 });
    await expect(h2).toHaveText(title);
  });
}
