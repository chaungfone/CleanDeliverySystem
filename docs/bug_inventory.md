# Bug Inventory — Sprint 0

| ID | Severity | Description | File Path | Fix Status | Verification Method |
|----|----------|-------------|-----------|------------|---------------------|
| BUG-001 | Critical | Unhandled exception in handlers caused `NameError: name 'any' is not defined` → 0-byte 500 (no CORS headers, opaque "Failed to fetch") | `backend/app/main.py` | Fixed | `tests/test_admin_endpoints_robustness.py` (standardized error body, non-empty 500/404) |
| BUG-002 | Critical | Supabase schema gaps surfaced as raw 500 empty-body responses instead of graceful errors | `backend/app/api/v1/endpoints/admin.py` | Fixed | `tests/test_admin_endpoints_robustness.py::test_admin_endpoints_no_raw_500_on_missing_schema` |
| BUG-003 | High | CORS wildcard `["*"]` with credentials allowed any origin | `backend/app/core/config.py` | Fixed | `tests/test_cors_security.py` + smoke (disallowed origin → no allow-origin header) |
| BUG-004 | High | Refresh token persisted in `localStorage` (XSS exfiltration) | `web-dashboard/src/lib/api.ts`, `backend/app/api/v1/endpoints/auth.py` | Fixed | `tests/test_refresh_cookie.py` (HttpOnly flag, token not in body, rotation) |
| BUG-005 | High | No ownership check on customer order read/review (IDOR) | `backend/app/core/security.py`, `backend/app/api/v1/endpoints/customer.py` | Fixed | `tests/test_ownership_guard.py` (403 for non-owner, 404 missing) |
| BUG-006 | High | Driver status route lacked assigned-courier authorization | `backend/app/core/security.py`, `backend/app/api/v1/endpoints/driver.py` | Fixed | `tests/test_ownership_guard.py` (driver guard 403/404) |
| BUG-007 | High | `/request-otp` and `/verify-otp` unthrottled (OTP spam / brute force) | `backend/app/api/v1/endpoints/auth.py`, `backend/app/core/rate_limit.py` | Fixed | `tests/test_rate_limit.py` (429 on 6th/11th call) |
| BUG-008 | Medium | RLS permissive "Public profiles are viewable by everyone." on `users`; reviews had no self policy | `supabase/migrations/20260806000000_rls_policies.sql` | Fixed | Migration SQL review + policy drops (apply via CI/dashboard) |
| BUG-009 | Medium | JWT decode did not require `exp/iat/aud` claims | `backend/app/core/security.py` | Fixed | `tests/test_refresh_cookie.py` expired/tampered → 401 |
| BUG-010 | Medium | Missing `max_length`/bounds on several inputs; negatives allowed in some numerics | `backend/app/models/*.py`, `backend/app/api/v1/endpoints/*.py` | Fixed | `tests/test_input_validation.py` |
| BUG-011 | Medium | Session tokens identical within same second (no `jti`) — weak rotation | `backend/app/api/v1/endpoints/auth.py` | Fixed | `tests/test_refresh_cookie.py::test_refresh_cookie_returns_new_access_token` |
| BUG-012 | Low | Frontend single 841 kB JS bundle; local font failed at build time | `web-dashboard/src/App.tsx`, `index.css`, `index.html` | Fixed | `npm run build` (214 kB initial; font build warning gone) |
| BUG-013 | Low | `ruff` reported 92 lint issues (74 auto + 18 manual) | `backend/app/**` | Fixed | `ruff check app` → All checks passed |
| BUG-014 | Low | `dashboard_analytics`/`export_sales_report` used naive (tz-unaware) datetimes | `backend/app/api/v1/endpoints/admin.py` | Fixed | `ruff check app` (DTZ005/DTZ011) + suite |
| BUG-015 | Medium | Order placement didn't surface stock-deduction/ownership defects (no coverage) | `backend/app/api/v1/endpoints/customer.py` | Fixed | `tests/test_e2e_smoke.py` flow 2 & 5 (stock 10→7) |