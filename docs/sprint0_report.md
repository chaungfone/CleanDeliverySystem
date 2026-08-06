# Sprint 0 — Security, Performance & Reliability Audit Report

**Project:** CleanDeliverySystem (Myanmar water delivery logistics)
**Branch:** `sprint0/security-hardening-audit-0806`
**Commits:** `e7d2f07` (Phase 1 security) · `acb5048` (Phase 2 perf/fixes)
**Date:** 2026-08-06

---

## A. Remediated Vulnerabilities Matrix

| # | Category | Issue | Severity | Fix | Status |
|---|----------|-------|----------|-----|--------|
| 1 | CORS | Wildcard `allow_origins=["*"]` allowed any origin with credentials | High | Env-driven `CORS_ORIGINS_JSON`; production refuses `["*"]` | **Fixed** |
| 2 | Token | Refresh token stored in `localStorage` (XSS-exfiltratable) | High | HttpOnly + Secure + SameSite=Lax cookie; rotated per refresh | **Fixed** |
| 3 | IDOR | Customer order read/edit lacked ownership check | High | `require_owner_or_admin` guard applied to customer order routes | **Fixed** |
| 4 | IDOR | Driver order status lacked assigned-courier check | High | `require_driver_or_admin` guard ("driver owner") | **Fixed** |
| 5 | Rate limit | OTP endpoints unthrottled (spam / brute force) | High | slowapi `5/min` request-otp, `10/min` verify-otp (IP+phone) | **Fixed** |
| 6 | SQLi | Potential raw string concatenation | Critical | Verified PostgREST builder-only (AST audit clean) | **Fixed/Verified** |
| 7 | Session fixation | Non-rotating tokens / cookie reuse | Medium | Add `jti` nonce; refresh cookie rotated on every call | **Fixed** |
| 8 | JWT | Loose decode options | Medium | Decode enforces `exp/iat/aud` + pinned `HS256` | **Fixed** |
| 9 | RLS | Permissive "Public profiles are viewable by everyone." on `users`; no reviews policy | Medium | New RLS migration (users/orders/addresses/reviews) | **Fixed** |
| 10 | Input | Unbounded strings / fields without `min≥0` | Medium | Pydantic `max_length`, regex, `ge=0` on models | **Fixed** |
| 11 | XSS | None (no `dangerouslySetInnerHTML`/`eval`) | Low | Verified; access token only in `localStorage` (short TTL) | **Verified** |
| 12 | CSRF | Refresh-cookie POST | Medium | `SameSite=Lax` blocks cross-site POST cookie attach | **Fixed** |

## B. Performance & Database Indexes

Frontend:
- Route-level code-splitting via `React.lazy` + `<Suspense>` (`web-dashboard/src/App.tsx`).
- Font swapped from unresolved local `Pyidaungsu.ttf` to **Noto Sans Myanmar** (Google Fonts).
- Initial JS chunk: **841.67 kB → 214.74 kB** (gzip **69.82 kB**); >500 kB warning eliminated.

Database indexes (migration `20260806000001_perf_indexes.sql`, all `IF NOT EXISTS` + `ANALYZE`):

| Table | Column(s) | Purpose |
|-------|-----------|---------|
| orders | driver_id | Assigned-order lookups / dispatch |
| order_items | order_id | Items fetch by order |
| users | role | Role filters / staff lists |
| users | phone_number | Login / OTP lookup |
| inventory | branch_id | Per-branch inventory |
| addresses | user_id | Ownership checks |
| driver_locations | updated_at DESC | Fleet "last ping" sorting |

RLS migration: `20260806000000_rls_policies.sql` (users, orders, addresses, reviews).

## C. Bundle Size Metrics

| Metric | Before | After |
|--------|--------|-------|
| Initial JS entry (raw / gzip) | 841.67 kB / 237.89 kB | **214.74 kB / 69.82 kB** |
| Chunks >500 kB | 1 | 0 |
| Font | local `Pyidaungsu.ttf` (build warning) | Google `Noto Sans Myanmar` (online) |

## D. Test Pass Rates

| Suite | Result |
|-------|--------|
| Backend pytest | **52/52 PASS** (0 failed) |
| Security smoke (`backend/scripts/security_smoke.ps1`) | **PASS** (CORS, 401, 403, 429) |
| E2E smoke `tests/test_e2e_smoke.py` (5 tests / 6 flows) | **PASS** |
| `ruff check backend/app` | **All checks passed** |
| `npm run build` | **exit 0** |

## E. Known Risks & Recommendations

1. **Supabase migrations unverified against the remote project** — kept local (Option B). Must run `EXPLAIN ANALYZE` + apply via Dashboard/CI before go-live; confirm Index Scan (not Seq Scan).
2. **Lighthouse ≥85 not measured** — requires headless Chrome + serving the build. Add `lighthouse-ci` to CI for a real number.
3. **Rate limiting uses slowapi default in-memory storage** — resets on restart and won't scale across instances. Move to Redis (`REDIS_URL` already stubbed in `.env.*`).
4. **Refresh-token revocation** — tokens rotate but a stolen refresh cookie stays valid until expiry. Consider an allow-list/deny-list keyed by `jti` if needed.
5. **`service_role` key in a long-running server** — correct for the backend, but never expose it client-side; consider egress controls / secret rotation.
6. **Largest lazy chunk** (DashboardOverview ≈ 382 kB raw / 101 kB gzip) holds charting libs; can be further split via `manualChunks`.

## F. Staging / Production Routing

| Component | Dev | Staging |
|-----------|-----|---------|
| Backend (Uvicorn) | :8000 (`uvicorn app.main:app`) | :8001 (`uvicorn app.main:app --port 8001 --env-file .env.staging`) |
| Web-dashboard | :3000 (`npm run dev`) | :3005 (`npm run dev:staging` → `vite --port 3005 --mode staging`) |
| API base | `VITE_API_URL=http://localhost:8000/api/v1` | `http://localhost:8001/api/v1` |

Env files: `backend/.env.staging(.example)`, `backend/.env.production(.example)`,
`web-dashboard/.env.staging(.example)`, `web-dashboard/.env.production(.example)`.

---

*Runbook references:* `docs/runbooks/server_down.md`, `docs/runbooks/supabase_restore.md`.
*Bug ledger:* `docs/bug_inventory.md`.