# Clean Delivery Admin — UI Design System

> Version 2.0 · Applies to `web-dashboard/` (React 18 + Vite + Tailwind CSS v3).
> Updated 2026-08-10.

This document is the single source of truth for the admin dashboard's visual
language. It supersedes the earlier ad-hoc styling and defines tokens,
components, interactions, and responsive rules so every screen stays
consistent and on-brand.

---

## 1. Brand

**Clean Delivery** is a purified-water delivery logistics company in Myanmar.

- **Personality:** clean, trustworthy, fresh, efficient.
- **Mark:** water droplet on a rounded gradient tile (`Droplets` icon, Lucide).
- **Voice:** short, direct, bilingual (English / မြန်မာ).

---

## 2. Color

### 2.1 Brand palette

| Token | Hex | Usage |
|-------|-----|-------|
| `primary.500` | `#1976D2` | Primary buttons, links, active accents (anchor brand blue) |
| `primary.600` | `#1665B4` | Primary hover |
| `primary.100` | `#E3F2FD` | Tinted chips, icon tiles, active nav pill (legacy `accent`) |
| `primary.50` | `#EFF7FE` | Row hover, very light fills |
| `primary.700` | `#12528F` | Headings on light, pressed states |
| `secondary.500` | `#009688` | Secondary actions, "orders per day" bars |
| `secondary.100` | `#C7ECE9` | Secondary tinted tiles |

The full `primary` and `secondary` scales (`50`–`900`) are defined in
`tailwind.config.js` and are available to every utility.

### 2.2 Neutrals (cool gray)

| Token | Hex | Usage |
|-------|-----|-------|
| `neutral.10` | `#16181D` | Primary text (near-black) |
| `neutral.90` | `#E4E8EF` | Borders, dividers |
| `neutral.99` | `#F5F7FA` | Page canvas, subtle fills |
| `neutral.400` | `#4B5563` | Hints / secondary text (WCAG AA ≈7.3:1 on white) |

### 2.3 Semantic status

| Intent | Text/bg pair |
|--------|--------------|
| Success (delivered, stock ok, active) | `green-700`/`green-50` |
| Warning (pending) | `orange-700`/`orange-50`, `yellow-700`/`yellow-50` |
| Danger (cancelled, low stock) | `red-700`/`red-50` |
| Info / in-transit | `blue-700`/`blue-50`, `primary-700`/`primary-100` |

### 2.4 Gradients

Brand gradients run `primary-600 → primary-500 → secondary-600` and are used
for the sidebar brand panel, login brand panel, stat-card icon tiles, and
avatar initials.

---

## 3. Typography

- **Latin (UI):** Inter 400/500/600/700 — loaded from Google Fonts
  (non-blocking `preload` + swap).
- **Myanmar:** Noto Sans Myanmar 400/500/700 — auto-fallback for မြန်မာ glyphs;
  `Pyidaungsu` as a local fallback.
- Stack: `Inter, "Noto Sans Myanmar", Pyidaungsu, system-ui, sans-serif`.
- **Type scale** follows Tailwind defaults:
  - Page titles `text-2xl font-bold tracking-tight`
  - Card titles `text-lg font-bold`
  - Section labels `text-sm font-medium`
  - Body `text-sm`, hints `text-xs`
- Myanmar text uses `line-height: 1.75` for legibility (`[lang='my']` rule).

---

## 4. Elevation & shape

- **Cards:** white, `rounded-2xl`, `border-neutral-90`, `shadow-card`
  (subtle 2-layer shadow). Class: `.card`.
- **Hover lift:** `.card-hover` adds `hover:-translate-y-0.5` +
  `shadow-card-hover`.
- **Modals / drawers:** `shadow-modal` / `shadow-drawer` for depth.
- **Radii:** inputs/buttons `rounded-xl`, badges/pills `rounded-full`,
  modal `rounded-2xl`.

---

## 5. Layout

### 5.1 App shell

```
┌──────────────────────────────────────────┐
│ Brand panel (gradient)        │ Content   │
│ ┌─────────────┐               │ max-w-    │
│ │ Nav (pills) │  fixed 64     │ 1600px    │
│ │             │  desktop      │ p-4/6/8   │
│ │ Footer/user │  sidebar      │           │
└──────────────────────────────────────────┘
```

- **Desktop (≥1024px):** fixed left sidebar (`w-64`), content offset
  `lg:pl-64`.
- **Mobile (<1024px):** sticky top bar with hamburger + brand; slide-in
  drawer (`w-72 max-w-[85vw]`) with scrim + backdrop blur; `NavList` is
  independently scrollable.
- Content max-width `1600px` to keep very wide screens comfortable.

### 5.2 Page header

Every page opens with `h2` (title) + muted subtitle, right-aligned primary
action (e.g. *Add Product*, *Export CSV*).

### 5.3 Grids

- Stat cards: `grid-cols-1 sm:2 lg:4`, gap `4 / lg:6`.
- Two-column panels: `grid-cols-1 lg:2`.
- Tables: `min-w` + `overflow-x-auto` so columns never crush on narrow
  screens.

---

## 6. Components

### 6.1 Buttons (`.btn-*`)

| Class | Look | Use |
|-------|------|-----|
| `.btn-primary` | Blue fill, white text | Primary CTA per page |
| `.btn-secondary` | Teal fill | Secondary CTA |
| `.btn-ghost` | Outline, neutral | Cancel / low emphasis |
| `.btn-danger` | Red tint | Destructive |

All buttons: `rounded-xl`, `active:scale-[0.98]`, visible focus ring,
`disabled:opacity-60`.

### 6.2 Form controls

- `.input`, `.textarea`, `.select` — shared rounded border style; `.select`
  gains a chevron via inline SVG background.
- `.input-with-icon` (left padding) pairs with a `relative` icon wrapper.
- `.field-label` for labels; placeholders use `neutral-400` (AA).

### 6.3 Badges

`.badge` + tinted pair (e.g. `text-green-700 bg-green-50`). Status badges
include a colored dot for quick scanning.

### 6.4 Cards

`.card`, `.card-hover`, `.table-card`. Icon tiles inside cards use brand
gradients with `.shadow-pop`.

### 6.5 Feedback states

- `LoadingState`: centered spinner + label.
- `ErrorState`: tinted alert card with contextual icon
  (network / timeout / 401 / 403 / 404 / 5xx) — see `src/lib/ui.tsx`.
- Modals animate `scale-in`; page content animates `fade-in-up`.

---

## 7. Interaction

- **Hover:** nav items tint `primary-50`; rows tint `primary-50/60`; buttons
  darken.
- **Focus:** global `:focus-visible` outline in `primary.500` (keyboard-first).
- **Motion:** 150–300 ms transitions; `prefers-reduced-motion` globally
  disables animation (see `index.css`).
- **Language toggle:** instant English ⇄ မြန်မာ switch, persisted in
  `localStorage` (`cd_lang`).

---

## 8. Responsiveness (verified)

Breakpoints and behaviors verified via Playwright at **375 / 768 / 1440** px:

| Asset | Mobile | Tablet | Desktop |
|-------|--------|--------|---------|
| Sidebar | Top bar + drawer | Top bar + drawer | Fixed sidebar |
| Login | Brand panel hidden, form-first | same | Split-screen brand panel |
| Stat grids | 1 col | 2 col | 4 col |
| Tables | Horizontal scroll | Horizontal scroll | Full width |
| Horizontal overflow | none | none | none |

---

## 9. Accessibility

- Focus-visible rings on all interactive elements.
- `aria-label` on icon-only buttons (hamburger, close, edit, delete).
- Modal / drawer use `role="dialog" aria-modal="true"`.
- Status colors paired with text/icons — never color-only.
- Placeholder text `#4B5563` (AA on white).
- `prefers-reduced-motion` support.
- Myanmar line-height/letter-spacing tuned for the script.

---

*Files that implement this system:* `tailwind.config.js`, `src/index.css`,
`src/components/*`, `src/lib/ui.tsx`, `src/App.tsx`, all `src/pages/*`.
