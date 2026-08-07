# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: smoke.spec.ts >> E2E Smoke Flows >> Flow 1: Admin login via UI (OTP)
- Location: e2e\smoke.spec.ts:10:3

# Error details

```
TimeoutError: page.fill: Timeout 10000ms exceeded.
Call log:
  - waiting for locator('input[name="phone_number"]')

```

# Page snapshot

```yaml
- generic [ref=e3]:
  - button "မြန်မာ" [ref=e5] [cursor=pointer]
  - generic [ref=e11]:
    - generic [ref=e17]:
      - heading "Clean Delivery" [level=1] [ref=e18]
      - paragraph [ref=e19]: Admin Dashboard
    - generic [ref=e20]:
      - generic [ref=e21]: Phone Number
      - textbox "09xxxxxxxxx" [ref=e25]
      - button "Request OTP" [ref=e26] [cursor=pointer]
```

# Test source

```ts
  1  | import { test, expect } from '@playwright/test';
  2  | 
  3  | // NOTE: These tests assume a running backend + web-dashboard served on localhost.
  4  | // Adjust BASE_URL and test credentials as needed.
  5  | const BASE_URL = process.env.E2E_BASE_URL || 'http://localhost:3000';
  6  | const ADMIN_PHONE = process.env.E2E_ADMIN_PHONE || '+959123456789';
  7  | const NON_ADMIN_PHONE = process.env.E2E_NONADMIN_PHONE || '+959987654321';
  8  | 
  9  | test.describe('E2E Smoke Flows', () => {
  10 |   test('Flow 1: Admin login via UI (OTP)', async ({ page }) => {
  11 |     await page.goto(`${BASE_URL}/login`);
  12 | 
  13 |     // Request OTP
> 14 |     await page.fill('input[name="phone_number"]', ADMIN_PHONE);
     |                ^ TimeoutError: page.fill: Timeout 10000ms exceeded.
  15 |     await page.click('button:has-text("Request OTP")');
  16 | 
  17 |     // In test environments we expect the OTP to be shown in console or test hook.
  18 |     // For now, wait for the OTP input to appear and mock value if test hook is available.
  19 |     await page.waitForSelector('input[name="otp"]', { timeout: 5000 });
  20 | 
  21 |     // Replace with test OTP retrieval if available; use 000000 as fallback
  22 |     const otp = process.env.E2E_TEST_OTP || '000000';
  23 |     await page.fill('input[name="otp"]', otp);
  24 |     await page.click('button:has-text("Verify")');
  25 | 
  26 |     // Expect redirect to dashboard
  27 |     await page.waitForURL('**/dashboard', { timeout: 5000 });
  28 |     expect(page.url()).toContain('/dashboard');
  29 | 
  30 |     // Ensure session cookie exists (HttpOnly cannot be read, but check presence of session indicator in UI)
  31 |     await expect(page.locator('text=Logout')).toBeVisible();
  32 |   });
  33 | 
  34 |   test('Flow 2: Create order and mark delivered', async ({ page }) => {
  35 |     await page.goto(`${BASE_URL}/dashboard`);
  36 | 
  37 |     // Open create order modal
  38 |     await page.click('button:has-text("Create Order")');
  39 |     await page.waitForSelector('form#create-order-form');
  40 | 
  41 |     // Fill form fields (selectors are approximations; adapt to real app)
  42 |     await page.fill('input[name="customer_name"]', 'E2E Tester');
  43 |     await page.fill('input[name="phone"]', '+959111222333');
  44 |     await page.fill('input[name="address_line1"]', '123 Test St');
  45 |     await page.fill('input[name="city"]', 'Yangon');
  46 |     await page.click('button:has-text("Submit")');
  47 | 
  48 |     // Wait for order to appear in table
  49 |     const row = page.locator('table >> text=E2E Tester').first();
  50 |     await expect(row).toBeVisible({ timeout: 5000 });
  51 | 
  52 |     // Change status to DELIVERED (selector depends on app)
  53 |     await row.locator('button:has-text("Actions")').click();
  54 |     await page.click('button:has-text("Mark as Delivered")');
  55 | 
  56 |     // Assert status badge changed
  57 |     await expect(row.locator('text=DELIVERED')).toBeVisible({ timeout: 5000 });
  58 |   });
  59 | 
  60 |   test('Flow 3: Role-based guard', async ({ page }) => {
  61 |     // Log out current session to simulate fresh user
  62 |     await page.goto(`${BASE_URL}/logout`);
  63 | 
  64 |     // Login as non-admin
  65 |     await page.goto(`${BASE_URL}/login`);
  66 |     await page.fill('input[name="phone_number"]', NON_ADMIN_PHONE);
  67 |     await page.click('button:has-text("Request OTP")');
  68 |     await page.waitForSelector('input[name="otp"]');
  69 |     const otp = process.env.E2E_TEST_OTP || '000000';
  70 |     await page.fill('input[name="otp"]', otp);
  71 |     await page.click('button:has-text("Verify")');
  72 |     await page.waitForURL('**/dashboard');
  73 | 
  74 |     // Try to access admin-only page
  75 |     await page.goto(`${BASE_URL}/staff`);
  76 | 
  77 |     // Expect access denied UI or redirect to unauthorized page
  78 |     await expect(page.locator('text=Access Denied').first()).toBeVisible({ timeout: 5000 });
  79 |   });
  80 | 
  81 |   test('Flow 4: Logout flow', async ({ page }) => {
  82 |     await page.goto(`${BASE_URL}/dashboard`);
  83 |     await page.click('text=Logout');
  84 |     await page.waitForURL('**/login');
  85 |     await expect(page.locator('button:has-text("Request OTP")')).toBeVisible();
  86 |   });
  87 | });
  88 | 
```