# Runbook — HTTP Cache Headers & Back/Forward Cache (bfcache)

The web-dashboard is a static SPA (Vite build → `dist/`). Correct `Cache-Control`
headers matter for two things:

1. **Back/Forward cache (bfcache)** — Chrome restores the page instantly on
   Back/Forward **only if** the HTML response is cacheable. A `Cache-Control:
   no-store` header **disables bfcache**.
2. **Load performance** — hashed assets (all filenames are content-addressed,
   e.g. `index-Db3Vlkld.js`) can be cached forever (`immutable`).

## Current status (verified 2026-08-07)
- Lighthouse `bf-cache` audit → **PASS** (score 1): no `unload`/`beforeunload`
  handlers in the app, HTML is served with `Cache-Control: no-cache`.
- Vite preview server sends `no-cache` for HTML and assets — acceptable for the
  HTML, sub-optimal for assets.

## Production configuration (nginx example)
```nginx
# SPA root
location / {
    try_files $uri /index.html;

    # HTML must be revalidated but NOT no-store (keeps bfcache working).
    add_header Cache-Control "public, max-age=0, must-revalidate";
}

# Hashed, immutable build assets (fingerprinted filenames => safe to cache forever)
location /assets/ {
    add_header Cache-Control "public, max-age=31536000, immutable";
    expires 1y;
}

# robots.txt can be cached
location = /robots.txt {
    add_header Cache-Control "public, max-age=86400";
}
```

### Rules
- **NEVER** send `Cache-Control: no-store` for `index.html` — it disables bfcache
  (Chrome refuses to bfcache a `no-store` page).
- Long-cache `/assets/` with `immutable` only because filenames are hash-based;
  a cache-busting deploy just changes the filename.
- Keep `Vary: Origin` handling consistent with CORS if you proxy through the API
  origin (the backend already emits security headers via FastAPI middleware).

## Verify
```powershell
# HTML must NOT say no-store (no-cache/must-revalidate is correct)
(Invoke-WebRequest https://yourdomain/ -UseBasicParsing).Headers['Cache-Control']

# Assets should be immutable
(Invoke-WebRequest https://yourdomain/assets/index-xxx.js -UseBasicParsing).Headers['Cache-Control']
```

## bfcache smoke check
Run the Lighthouse `bf-cache` audit against the production URL:
```powershell
cd web-dashboard
npm run build
lighthouse http://localhost:4173 --only-categories=performance --output=json `
  --chrome-flags="--headless=new"  # check "bf-cache" audit = PASS
```
`bf-cache` = `Page didn't prevent back/forward cache restoration` when healthy.
