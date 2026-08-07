# E2E Playwright Test Runbook

This document explains how to run the Playwright E2E suite for the web-dashboard locally and in CI.

Prerequisites
- Node.js 18+ (for Playwright)
- npm or yarn
- A running backend server (default: http://localhost:8000) and the web-dashboard dev server (default: http://localhost:3000)

Install (one-time)
1. From repository root, install frontend deps:
   cd web-dashboard
   npm install

2. Install Playwright browsers (required once):
   npx playwright install chromium

Run tests locally (headless)
1. Ensure backend and web-dashboard are running.
2. Set any environment variables if needed (example):
   export E2E_BASE_URL=http://localhost:3000
   export E2E_ADMIN_PHONE=+959123456789
   export E2E_NONADMIN_PHONE=+959987654321
   export E2E_TEST_OTP=000000
3. Run:
   npm run test:e2e

Run tests in CI (headless)
- Example GitHub Actions step:
  - name: Install frontend deps
    working-directory: web-dashboard
    run: |
      npm ci
      npx playwright install --with-deps
  - name: Run E2E tests
    working-directory: web-dashboard
    run: npm run test:e2e

Notes and tips
- OTP handling: In test mode the application should expose a deterministic OTP (E2E_TEST_OTP) or write it to a test-only endpoint accessible to Playwright. If not available, set E2E_TEST_OTP to the value returned by the test backend (e.g., mock or debug OTP).
- Adjust selectors in e2e/smoke.spec.ts to match real UI elements if any mismatch occurs.
- To run tests against a deployed staging environment set E2E_BASE_URL accordingly.
