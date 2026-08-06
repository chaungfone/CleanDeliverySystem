# Runbook — Lighthouse CI (LHCI) Audit

Automates Lighthouse Performance, Accessibility, Best Practices, and SEO audits
with a **>= 85 score threshold** for each category.

## Config
- `web-dashboard/.lighthouserc.json` — LHCI config.
  - `collect`: starts `npm run preview` on `http://localhost:4173/`, runs 1 audit.
  - `assert`: `categories:performance | accessibility | best-practices | seo` → `error, minScore 0.85`.
  - `upload`: writes reports to `web-dashboard/lhci_reports/` (filesystem target — no LHCI server needed).
- `web-dashboard/package.json` → `"lh:audit": "lhci autorun"`, `@lhci/cli` devDependency.

## Run locally
Prereqs: Chrome installed on the machine.
```powershell
cd web-dashboard
npm ci                 # first time
npm run build          # production build (dist/)
npm run lh:audit       # lhci autorun
```
Results land in `web-dashboard/lhci_reports/`:
- `*.report.html` — open in a browser for the full interactive report.
- `manifest.json` + `*.report.json` — machine-readable results.

The `startServerCommand` (vite preview) is started and stopped by LHCI automatically.

## Run in CI
Pushed via `.github/workflows/lighthouse.yml` on push to `main` and PRs:
1. checkout → setup-node → setup Chrome
2. `npm ci` → `npm run build`
3. `npm run lh:audit` (asserts each category >= 0.85)
4. uploads `lighthouse-reports` artifact (report HTML/JSON) on every run.

## Inspecting results
- In the uploaded artifact, download `lighthouse-reports`, open the `*.report.html`.
- Thresholds come from `assert.assertions`; a category below 85 fails the step (`lhci` exits non-zero).

## Notes / avoiding flaky failures
- **Transient network:** the SPA loads Google Fonts (`fonts.googleapis.com`/`gstatic`) at runtime. A flaky CDN can briefly dip performance — rerun the audit before treating a single run as a regression.
- **Auth-gated pages:** the app redirects unauthenticated users to `/login`, so the audit measures the public/login shell plus lazy chunks of the initial route. For a fully-authenticated audit, run LHCI against a staging URL behind a test account.
- **Strict port:** `--strictPort` on 4173 fails fast if something else holds the port.
- If Chrome is missing locally, install it (or run in CI where `setup-chrome` provides it).
