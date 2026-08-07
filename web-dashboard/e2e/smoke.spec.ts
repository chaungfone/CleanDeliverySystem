import { test, expect } from '@playwright/test';

// NOTE: These tests assume a running backend + web-dashboard served on localhost.
// Adjust BASE_URL and test credentials as needed.
const BASE_URL = process.env.E2E_BASE_URL || 'http://localhost:3000';
const ADMIN_PHONE = process.env.E2E_ADMIN_PHONE || '+959123456789';
const NON_ADMIN_PHONE = process.env.E2E_NONADMIN_PHONE || '+959987654321';

test.describe('E2E Smoke Flows', () => {
  test('Flow 1: Admin login via UI (OTP)', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);

    // Request OTP
    await page.fill('input[name="phone_number"]', ADMIN_PHONE);
    await page.click('button:has-text("Request OTP")');

    // In test environments we expect the OTP to be shown in console or test hook.
    // For now, wait for the OTP input to appear and mock value if test hook is available.
    await page.waitForSelector('input[name="otp"]', { timeout: 5000 });

    // Replace with test OTP retrieval if available; use 000000 as fallback
    const otp = process.env.E2E_TEST_OTP || '000000';
    await page.fill('input[name="otp"]', otp);
    await page.click('button:has-text("Verify")');

    // Expect redirect to dashboard
    await page.waitForURL('**/dashboard', { timeout: 5000 });
    expect(page.url()).toContain('/dashboard');

    // Ensure session cookie exists (HttpOnly cannot be read, but check presence of session indicator in UI)
    await expect(page.locator('text=Logout')).toBeVisible();
  });

  test('Flow 2: Create order and mark delivered', async ({ page }) => {
    await page.goto(`${BASE_URL}/dashboard`);

    // Open create order modal
    await page.click('button:has-text("Create Order")');
    await page.waitForSelector('form#create-order-form');

    // Fill form fields (selectors are approximations; adapt to real app)
    await page.fill('input[name="customer_name"]', 'E2E Tester');
    await page.fill('input[name="phone"]', '+959111222333');
    await page.fill('input[name="address_line1"]', '123 Test St');
    await page.fill('input[name="city"]', 'Yangon');
    await page.click('button:has-text("Submit")');

    // Wait for order to appear in table
    const row = page.locator('table >> text=E2E Tester').first();
    await expect(row).toBeVisible({ timeout: 5000 });

    // Change status to DELIVERED (selector depends on app)
    await row.locator('button:has-text("Actions")').click();
    await page.click('button:has-text("Mark as Delivered")');

    // Assert status badge changed
    await expect(row.locator('text=DELIVERED')).toBeVisible({ timeout: 5000 });
  });

  test('Flow 3: Role-based guard', async ({ page }) => {
    // Log out current session to simulate fresh user
    await page.goto(`${BASE_URL}/logout`);

    // Login as non-admin
    await page.goto(`${BASE_URL}/login`);
    await page.fill('input[name="phone_number"]', NON_ADMIN_PHONE);
    await page.click('button:has-text("Request OTP")');
    await page.waitForSelector('input[name="otp"]');
    const otp = process.env.E2E_TEST_OTP || '000000';
    await page.fill('input[name="otp"]', otp);
    await page.click('button:has-text("Verify")');
    await page.waitForURL('**/dashboard');

    // Try to access admin-only page
    await page.goto(`${BASE_URL}/staff`);

    // Expect access denied UI or redirect to unauthorized page
    await expect(page.locator('text=Access Denied').first()).toBeVisible({ timeout: 5000 });
  });

  test('Flow 4: Logout flow', async ({ page }) => {
    await page.goto(`${BASE_URL}/dashboard`);
    await page.click('text=Logout');
    await page.waitForURL('**/login');
    await expect(page.locator('button:has-text("Request OTP")')).toBeVisible();
  });
});
