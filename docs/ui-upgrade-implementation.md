# UI Upgrade — Implementation Record

> Web dashboard (`web-dashboard/`) · 2026-08-10 · Sprint: UI/UX polish
> Companion spec: [`docs/ui-design-system.md`](./ui-design-system.md)

## 1. Goal

Improve UX and visual appeal of the Clean Delivery admin dashboard — color,
typography, layout, interaction, and responsiveness — without breaking any
existing functionality, while staying on-brand (clean-water logistics, blue +
teal).

## 2. What changed

### 2.1 Design system (`tailwind.config.js`)
- Added full **primary** (water blue) and **secondary** (teal) scales
  (`50`–`900`) with `DEFAULT` mapped to the existing brand colors
  (`#1976D2`, `#009688`) so every legacy `bg-primary`/`text-primary` keeps
  working.
- Cooled the neutrals (`neutral-99 #F5F7FA`, `neutral-90 #E4E8EF`,
  `neutral-10 #16181D`).
- Added **Inter** to the font stack (Latin) ahead of Noto Sans Myanmar /
  Pyidaungsu (Myanmar).
- New tokens: `shadow-card`, `shadow-card-hover`, `shadow-drawer`,
  `shadow-modal`, `shadow-pop`; animations `fade-in`, `fade-in-up`,
  `scale-in`, `slide-in-right`.

### 2.2 Global styles (`src/index.css`)
- Component classes: `.card`, `.card-hover`, `.btn-primary/.secondary/
  .ghost/.danger`, `.input/.textarea/.select/.field-label/.input-with-icon`,
  `.badge`, `.table-card/.table-wrap/.table-head/.table-body/.table-row/
  .table-cell`.
- Custom scrollbars, `:focus-visible` brand outline, `::selection`,
  `prefers-reduced-motion` support, `color-scheme: light`.

### 2.3 Shell & navigation
- `Sidebar.tsx`: gradient brand panel with droplet mark, icon-tinted active
  nav pills with indicator dot, avatar + signed-in footer, scrollable mobile
  drawer, backdrop blur scrim, `role="dialog" aria-modal="true"`.
- **UX bug fix:** mobile hamburger previously called `onClose` (drawer could
  never open). Added `onOpen` prop wired in `App.tsx`.
- **UX fix:** mobile drawer `NavList` is now `overflow-y-auto` so all 8 nav
  items are reachable on short screens.
- `App.tsx`: spinner page loader, content `max-w-[1600px]`, cleaner mobile
  padding.

### 2.4 Login (`pages/Login.tsx`)
- Split-screen redesign: gradient brand panel (tagline + feature list,
  desktop only) and a form panel with the mobile brand header.
- Same OTP flow, same `name="phone_number"` / `name="otp"` inputs, same
  buttons — no behavioral change.

### 2.5 Pages
- `DashboardOverview`: gradient stat-card icon tiles with lift-on-hover,
  styled chart tooltips, chart grid/axis polish, area gradient fill.
- `OrderManagement`: new `.table-*` structure, dot status badges,
  `.input/.select/.btn-*`, labeled icons.
- `Products` / `Staff` / `BranchManagement` / `InventoryManager`: consistent
  cards, gradient icon tiles, tinted action buttons, badge-based stock/role
  chips, `.input/.textarea/.select` forms, error alert styling.
- `LiveFleetTracker`: `.card` map frame + driver cards, legend chips.
- `Settings`: `.card` panels, tinted section icons.
- `Modal.tsx`: fade/scale animations, sticky header, `aria-label`.
- `ui.tsx`: spinner `LoadingState`, polished `ErrorState`.

### 2.6 `index.html`
- Inter + Noto Sans Myanmar preloaded (non-blocking), inline SVG droplet
  favicon, theme-color → brand blue.

## 3. What did NOT change

- All routes, query keys, API paths, auth flow, i18n keys, and form field
  `name` attributes are untouched → no functional regressions.
- Existing `e2e/smoke.spec.ts` selectors (OTP inputs, "Request OTP" button)
  still match.

## 4. Verification

| Check | Command | Result |
|-------|---------|--------|
| TypeScript + production build | `npm run build` | ✅ exit 0 |
| Frontend unit regressions | `node tests/test_api_errors.mjs` (+2 others) | ✅ 29/29 |
| Responsive login @375/768/1440 | `npx playwright test e2e/ui-layout.spec.ts` | ✅ 9/9 |
| App shell + mobile drawer | `npx playwright test e2e/app-shell.spec.ts` | ✅ 4/4 |
| Screenshots (login/dashboard) | Playwright capture | saved for review |

### 4.1 Issues found & fixed during testing
1. Hamburger could not open the mobile drawer (pre-existing) → added `onOpen`.
2. Mobile drawer overflowed on short screens → `NavList` now scrolls.
3. (Tests only) Locators resolved to hidden desktop-brand duplicates →
   scoped to the form panel / aside.

### 4.2 Not run
- `e2e/smoke.spec.ts` requires a live backend + seeded users; skipped (the
  two new suites cover the UI without a backend).
- `npm run lint` has no ESLint config in the repo (CI runs build + Lighthouse
  instead).
- Lighthouse CI runs in GitHub Actions on `main`.

## 5. Files touched

```
web-dashboard/tailwind.config.js        web-dashboard/src/index.css
web-dashboard/index.html                web-dashboard/src/App.tsx
web-dashboard/src/components/Sidebar.tsx
web-dashboard/src/components/Modal.tsx
web-dashboard/src/lib/ui.tsx
web-dashboard/src/pages/Login.tsx       web-dashboard/src/pages/DashboardOverview.tsx
web-dashboard/src/pages/OrderManagement.tsx
web-dashboard/src/pages/InventoryManager.tsx
web-dashboard/src/pages/Products.tsx    web-dashboard/src/pages/Staff.tsx
web-dashboard/src/pages/BranchManagement.tsx
web-dashboard/src/pages/LiveFleetTracker.tsx
web-dashboard/src/pages/Settings.tsx
web-dashboard/e2e/ui-layout.spec.ts      (new)
web-dashboard/e2e/app-shell.spec.ts      (new)
docs/ui-design-system.md                 (new)
docs/ui-upgrade-implementation.md        (this file)
```

## 6. Rollback

UI changes are confined to `web-dashboard/` + the two new docs. Reverting the
frontend to the previous styling is a `git checkout` of the `web-dashboard/src`
and `web-dashboard/tailwind.config.js` paths; no database or backend changes
were introduced.
