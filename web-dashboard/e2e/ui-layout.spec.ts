import { test, expect, type Page } from '@playwright/test';

// Responsive layout / visual regression checks for the redesigned UI.
// These tests run against the PUBLIC login page only, so no backend is required.
const BASE_URL = process.env.E2E_BASE_URL || 'http://localhost:4173';

const VIEWPORTS: { name: string; width: number; height: number }[] = [
  { name: 'mobile', width: 375, height: 812 },
  { name: 'tablet', width: 768, height: 1024 },
  { name: 'desktop', width: 1440, height: 900 },
];

const signInPanel = (page: Page) => page.locator('main[aria-label="Sign in"]');

async function noHorizontalOverflow(page: Page) {
  const overflow = await page.evaluate(
    () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
  );
  expect(overflow, 'page must not scroll horizontally').toBeLessThanOrEqual(1);
}

for (const vp of VIEWPORTS) {
  test.describe(`Login layout @ ${vp.name}`, () => {
    test.use({ viewport: { width: vp.width, height: vp.height } });

    test.beforeEach(async ({ page }) => {
      await page.goto(`${BASE_URL}/login`);
      // The phone input lives inside the sign-in form panel.
      await expect(page.locator('input[name="phone_number"]')).toBeVisible();
    });

    test('renders form panel + phone input without horizontal overflow', async ({ page }) => {
      await expect(signInPanel(page)).toBeVisible();
      await expect(page.getByRole('button', { name: /request otp/i })).toBeVisible();
      await noHorizontalOverflow(page);
    });

    test('language switch toggles Myanmar content', async ({ page }) => {
      await page.getByRole('button', { name: /မြန်မာ|switch/i }).first().click();
      await expect(signInPanel(page).locator('span.field-label').first()).toHaveText('ဖုန်းနံပါတ်');
      await noHorizontalOverflow(page);
    });
  });
}

test.describe('Login responsive breakpoints', () => {
  test.use({ viewport: { width: 1440, height: 900 } });

  test('brand panel is visible on desktop only', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);
    await expect(page.locator('aside').getByText('Clean water.')).toBeVisible();
  });

  test('brand panel is hidden on mobile, mobile brand shown', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 });
    await page.goto(`${BASE_URL}/login`);
    await expect(page.locator('aside')).toBeHidden();
    // Mobile brand header (droplet mark) is present inside the sign-in panel
    await expect(signInPanel(page).getByText('Clean Delivery').first()).toBeVisible();
    await noHorizontalOverflow(page);
  });

  test('debug OTP bypass logs in directly without the OTP step', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);
    await page.fill('input[name="phone_number"]', '+959123456789');
    // Stub the whole auth chain: request-otp returns a debug OTP, which now
    // auto-verifies (temporary bypass) and fetches the current user.
    await page.route('**/api/v1/auth/request-otp', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ debug_otp: '123456' }),
      }),
    );
    await page.route('**/api/v1/auth/verify-otp', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          access_token: 'bypass.token',
          role: 'ADMIN',
          user_id: 'admin-1',
        }),
      }),
    );
    await page.route('**/api/v1/auth/me', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 'admin-1',
          phone_number: '+959123456789',
          full_name: 'Aung Admin',
          role: 'ADMIN',
          branch_id: null,
          created_at: new Date().toISOString(),
        }),
      }),
    );
    await page.getByRole('button', { name: /request otp/i }).click();
    // Redirect to the dashboard root once the bypass auto-verifies.
    await page.waitForURL(`${BASE_URL}/`, { timeout: 8000 });
  });

  test('fallback demo login signs in directly when the backend is down', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);
    await page.fill('input[name="phone_number"]', '+959123456789');
    // Simulate an unreachable backend: the request-otp call fails immediately.
    await page.route('**/api/v1/auth/request-otp', (route) => route.abort());
    await page.getByRole('button', { name: /request otp/i }).click();
    await page.waitForURL(`${BASE_URL}/`, { timeout: 8000 });
    // Demo session is stored so the shell renders (no backend round-trip).
    const token = await page.evaluate(() => localStorage.getItem('cd_dashboard_token'));
    expect(token).toMatch(/^demo:/);
  });
});
