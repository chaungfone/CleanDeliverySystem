# Deployment Guide: Vercel (Frontend + Serverless Backend)

> **Current architecture:** the FastAPI backend is deployed on Vercel as a
> Python serverless function (`api/index.py`, wrapped with Mangum), and the
> dashboard is served from `web-dashboard/dist`. Both live on the same origin,
> so `VITE_API_URL=/api/v1` and no CORS is required.

## 1. Vercel project settings (IMPORTANT)

| Setting | Value |
|---------|-------|
| **Root Directory** | `/` (repo root — NOT `web-dashboard`) |
| **Framework Preset** | Other (Vite is detected from `vercel.json` build commands) |
| **Build Command** | `cd web-dashboard && npm run build` |
| **Install Command** | `cd web-dashboard && npm install` |
| **Output Directory** | `web-dashboard/dist` |

> ⚠️ The Python function lives at `api/index.py` and imports the backend from
> `backend/`. Both must be inside the deployed root, so the Root Directory
> MUST be the repository root. If it is set to `web-dashboard`, every
> `/api/v1/*` request falls through to the SPA fallback and returns
> `index.html`, and the dashboard shows
> *"The API returned an HTML page instead of JSON."*

These settings are already encoded in the root `vercel.json`. The Python
function is declared explicitly with the `functions` key — Vercel's zero-config
Python detection does NOT build `api/index.py` for projects that use a custom
`buildCommand`/`installCommand`, which makes every `/api/*` request return a
platform 404 (`The page could not be found`):

```json
{
  "version": 2,
  "functions": {
    "api/index.py": { "runtime": "python@3.12" }
  },
  "installCommand": "cd web-dashboard && npm install",
  "buildCommand": "cd web-dashboard && npm run build",
  "outputDirectory": "web-dashboard/dist",
  "cleanUrls": true,
  "rewrites": [
    { "source": "/api/:path*", "destination": "/api/index" },
    { "source": "/((?!api/).*)", "destination": "/index.html" }
  ]
}
```

## 2. Environment variables (Vercel dashboard)

These are required at import time by `backend/app/core/config.py`; if they are
missing or placeholders the function fails to boot:

```
SUPABASE_URL          = https://<project-ref>.supabase.co
SUPABASE_KEY          = <anon or service_role key>   # backend -> service_role
SUPABASE_JWT_SECRET   = <JWT secret from Supabase dashboard>
```

Optional: `DATABASE_URL`, `DIRECT_URL`, `SENTRY_DSN`, `REDIS_URL`.

The Python dependencies are installed from the root `requirements.txt`
(`fastapi`, `supabase`, `pydantic-settings`, `mangum`, ...). No runtime pin is
needed (zero-config Python detection).

## 3. Deploy & verify

Push to the branch connected to Vercel, or redeploy from the dashboard. Then
check the API responds with JSON (NOT HTML):

```
https://<your-site>.vercel.app/api/v1/openapi.json
```

- JSON OpenAPI document → backend is live ✅
- HTML (the dashboard page) → Root Directory is still `web-dashboard` ❌

Also confirm the health endpoint from the backend service, e.g. via a local
FastAPI run, shows `"services": { "supabase": "connected" }`.

## 4. Troubleshooting checklist

| Symptom | Cause | Fix |
|---------|-------|-----|
| `/api/*` returns HTML (SPA page) | Root Directory = `web-dashboard` | Set Root Directory to `/` |
| `/api/*` returns platform 404 (`The page could not be found / NOT_FOUND`) | Vercel is not building the Python function | Ensure `functions: { "api/index.py": { "runtime": "python@3.12" } }` is in `vercel.json` and redeploy. If it still 404s, Vercel's Python serverless runtime is not available for the project/plan — deploy the backend to Koyeb instead (section 5) |
| `/api/*` returns 503 "Backend configuration error… Missing required environment variables" | `SUPABASE_URL`/`SUPABASE_KEY`/`SUPABASE_JWT_SECRET` missing or placeholders | Set real values in Vercel env vars |
| Data pages show "Server error" | Backend boot failure (see previous row) | See above |
| Login bypass works but data pages are empty | Demo session has no real credentials | Fix env vars so real login works |

## 5. Fallback: backend on Koyeb (most reliable)

If Vercel's Python serverless runtime stays broken (platform 404 on `/api/*`),
run the backend on Koyeb as a normal Docker service — this is the architecture
`koyeb.yaml` was written for, and it avoids every Vercel serverless quirk.

1. Create a Koyeb Web Service from this repo (build path `backend`,
   `backend/Dockerfile`, port `8000`).
2. Set env vars (from `backend/.env.production`):
   `SUPABASE_URL`, `SUPABASE_KEY`, `SUPABASE_JWT_SECRET`, `DATABASE_URL`,
   `DIRECT_URL`, `SENTRY_DSN`, plus `CORS_ORIGINS_JSON` =
   `["https://<your-app>.vercel.app"]` (JSON array, no wildcard).
3. Note the service URL, e.g. `https://clean-delivery-backend-<id>.koyeb.app`.
4. Verify: `https://<koyeb>.koyeb.app/healthz` → `"supabase": "connected"`.
5. On Vercel, set the env var `VITE_API_URL =
   https://<koyeb>.koyeb.app/api/v1` and redeploy (this is baked into the
   bundle at build time). The `api/` function and `/api` rewrites in
   `vercel.json` become unused; you may remove them later.

---

*Runbook:* `docs/runbooks/server_down.md` · *Frontend UI spec:*
`docs/ui-design-system.md`.
