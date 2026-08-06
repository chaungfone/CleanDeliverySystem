# Debug Session: dashboard-nav-failed-fetch-settings-wrong-page

**Status**: [OPEN]  
**Session ID**: dashboard-nav-failed-fetch-settings-wrong-page  
**Created**: 2026-08-05  
**Bug Description**:  
1. Navigating to Staff, Branches, Inventory, Fleet pages shows generic "Failed to Fetch" error banner.  
2. Clicking Settings sidebar link renders DashboardOverview page (overview cards) instead of a Settings page.

---

## Hypotheses (Falsifiable)

| # | Hypothesis | Prediction | Verification Point |
|---|-----------|------------|-------------------|
| H1 | Settings route has no dedicated component: App.tsx maps /settings → DashboardOverview; no Settings.tsx page file exists | Browser devtools React tree on /settings shows DashboardOverview component | App.tsx Routes block, glob for Settings*.tsx |
| H2 | Backend lacks all `/admin/*` endpoints used by pages: `/admin/staff`, `/admin/branches`, `/admin/inventory`, `/admin/fleet/drivers` return 404 → Frontend treats 404 as generic "Failed to Fetch" | Network tab: GET /admin/* returns 404 status + FastAPI default 404 JSON body | Grep backend for /admin/ route decorators |
| H3 | CORS / Auth missing: `/admin/*` requests lack Authorization Bearer or require_admin dependency not injected → 401/403 → wrapped as generic message | apiFetch.ts: does it auto-inject token for admin-prefix? Security.py: require_admin dep on any existing /admin route | api.ts apiFetch headers, security.py Depends |
| H4 | Pages use tanstack-query useQuery; onError path only reads generic `err.message` which becomes "Failed to fetch" for network/4xx — real ApiError.status lost | Staff.tsx, InventoryManager.tsx useQuery options: error.message concatenation pattern | Search page components for useQuery + error display |
| H5 | NavLink path param mismatch: Sidebar list uses e.g. "/branches" but Route was accidentally "/branch" (singular) etc. → URL updates but route matches only catch-all → renders DashboardOverview | Click Staff → window.location.pathname = "/staff"; check Routes for path="/staff" vs "/staffs" | Sidebar.tsx link paths vs App.tsx Route paths |

---

## Evidence Log

| Phase | Timestamp | Observations | Conclusion |
|-------|-----------|-------------|------------|
| Pre-Instrumentation | | | |
| Post-Instrumentation | | | |
| Post-Fix | | | |

---

## Artifacts

- Debug Server logs: `trae-debug-log-dashboard-nav-failed-fetch-settings-wrong-page.ndjson`
- Instrumentation points: TBD
