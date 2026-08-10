import { test, expect } from '@playwright/test';

// Authenticated app-shell checks. The backend is NOT required: every API call
// is stubbed so we can verify layout, navigation and the mobile drawer.
const BASE_URL = process.env.E2E_BASE_URL || 'http://localhost:4173';

const ADMIN = {
  id: 'admin-1',
  phone_number: '+959123456789',
  full_name: 'Aung Admin',
  role: 'ADMIN',
  branch_id: null,
  created_at: new Date().toISOString(),
};

async function seedDashboard(page, viewport) {
  if (viewport) await page.setViewportSize(viewport);
  await page.addInitScript(() => {
    localStorage.setItem('cd_dashboard_token', 'fake.admin.token');
  });
  // Authenticate: token present -> AuthProvider calls /auth/me.
  await page.route('**/api/v1/auth/me', (route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(ADMIN) }),
  );
  // Dashboard queries so the overview page settles quickly.
  await page.route('**/api/v1/admin/dashboard/analytics', (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        period: 'daily',
        start_date: new Date().toISOString(),
        total_revenue: '0',
        delivered_volume: 0,
        pending_deliveries: 0,
        active_drivers: 0,
      }),
    }),
  );
  await page.route('**/api/v1/admin/orders', (route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: '[]' }),
  );
}

test('desktop: sidebar renders brand + all nav items', async ({ page }) => {
  await seedDashboard(page, { width: 1440, height: 900 });
  await page.goto(`${BASE_URL}/`);
  await expect(page.locator('aside').getByText('Clean Delivery').first()).toBeVisible();
  for (const label of ['Overview', 'Orders', 'Fleet', 'Inventory', 'Products', 'Branches', 'Staff', 'Settings']) {
    await expect(page.locator('aside').getByText(label, { exact: true })).toBeVisible();
  }
});

test('desktop: clicking a nav item navigates without reload', async ({ page }) => {
  await seedDashboard(page, { width: 1440, height: 900 });
  await page.goto(`${BASE_URL}/`);
  await page.locator('aside').getByText('Orders', { exact: true }).click();
  await expect(page).toHaveURL(`${BASE_URL}/orders`);
  await page.locator('aside').getByText('Settings', { exact: true }).click();
  await expect(page).toHaveURL(`${BASE_URL}/settings`);
});

test('mobile: hamburger opens the drawer and close button dismisses it', async ({ page }) => {
  await seedDashboard(page, { width: 375, height: 812 });
  await page.goto(`${BASE_URL}/`);
  // Desktop sidebar is hidden on mobile; only the top-bar hamburger exists.
  await expect(page.locator('aside')).toBeHidden();
  await page.getByRole('button', { name: 'Open navigation' }).click();
  const drawer = page.locator('[role="dialog"][aria-modal="true"]');
  await expect(drawer).toBeVisible();
  await expect(drawer.getByText('Orders', { exact: true })).toBeVisible();
  // Navigate from within the drawer.
  await drawer.getByText('Staff', { exact: true }).click();
  await expect(page).toHaveURL(`${BASE_URL}/staff`);
});

test('mobile: page has no horizontal overflow in the app shell', async ({ page }) => {
  await seedDashboard(page, { width: 375, height: 812 });
  await page.goto(`${BASE_URL}/`);
  await expect(page.locator('main')).toBeVisible();
  const overflow = await page.evaluate(
    () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
  );
  expect(overflow).toBeLessThanOrEqual(1);
});
