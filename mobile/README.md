# Clean Delivery — Flutter Mobile App

**Clean Delivery** is the mobile app for a Myanmar purified-water delivery
logistics platform. This is the **Flutter** implementation of the previous
Kotlin (Jetpack Compose) Android app, rewritten from scratch with a modern,
luxury UI.

It talks to the FastAPI backend in the same repository
(`backend/`, `/api/v1`). Roles are supported: **Customer** (order water) and
**Driver** (accept & complete deliveries).

---

## Features

### Customer
- Phone + OTP authentication (`POST /auth/request-otp`, `POST /auth/verify-otp`)
- Product catalogue with stock status (`GET /products`)
- Cart with per-product quantity steppers and a live total
- Checkout: delivery address, payment method (COD / KBZ Pay / Wave Pay),
  empty-bottle returns (`POST /orders`)
- Order tracking: live status timeline, driver card, periodic auto-refresh
  (`GET /orders/{id}`, `GET /orders/history`)
- Session restore, token refresh and automatic sign-out on expiry

### Driver
- Online / offline toggle
- Assigned delivery jobs (`GET /drivers/orders`)
- Start trip (`PATCH /drivers/orders/{id}/status` → `IN_TRANSIT`)
- Complete delivery dialog with bottle verification and COD collection
  (→ `DELIVERED`)
- Earnings & delivery history screen
- Location reporting (`POST /drivers/location`) and route optimisation
  (`POST /drivers/optimize-route`)

### Robustness
- Friendly, human-readable error messages for network / server / validation
  failures (never raw exceptions)
- Single-flight **access-token refresh** via `POST /auth/refresh`
  (mobile JSON flow) with automatic retry of the failed request
- Refresh-token extraction from the backend's `Set-Cookie` header
- Offline-tolerant: the last known profile is cached so a network hiccup at
  startup does not lock the user out
- Defensive JSON parsing (prices accepted as `number` or `string`)
- Responsive layout that adapts to phones and tablets (2-column catalogue on
  wide screens)

---

## Tech Stack

| Area        | Choice                                                       |
|-------------|--------------------------------------------------------------|
| Framework   | Flutter 3.16 (Dart 3.2)                                      |
| Language    | Dart (null-safe)                                             |
| State       | `provider` (`ChangeNotifier`)                                |
| Networking  | `dio` + interceptors (auth, refresh, logging)                |
| Storage     | `shared_preferences` (tokens + cached profile + address)     |
| Formatting  | `intl` (MMK currency + dates)                                |
| Fonts       | Bundled **Pyidaungsu** fallback for Myanmar glyphs            |

---

## Project Structure

```
mobile/
├── android/                     # Android host (Gradle 8.5, AGP 8.2, minSdk 21)
├── assets/
│   ├── fonts/                   # Pyidaungsu (Myanmar) font
│   └── images/
├── lib/
│   ├── main.dart                # Entry point: wires storage + dio
│   ├── app.dart                 # Provider tree + MaterialApp/theme
│   ├── core/
│   │   ├── constants/           # API base URL, limits
│   │   ├── errors/              # AppException hierarchy
│   │   ├── network/             # Dio factory, interceptors, error mapper
│   │   ├── storage/             # TokenStorage (SharedPreferences)
│   │   ├── theme/               # Luxury navy/gold design system
│   │   └── utils/               # MMK/date formatters
│   ├── data/
│   │   ├── models/              # Auth, User, Product, Order, Driver models
│   │   └── repositories/        # Auth / Product / Order / Driver repos
│   ├── providers/               # Auth / Home(cart) / Order / Driver
│   └── ui/
│       ├── screens/             # login, otp, home, checkout, tracking,
│       │                        # driver/* (home, delivery list, nav, earnings)
│       ├── widgets/             # shared luxury widgets
│       ├── navigation.dart      # navigator key + helpers
│       └── root_gate.dart       # auth-state → start screen
└── test/                        # unit + widget tests (23 tests)
```

**Data flow:** `Screen → Provider (ChangeNotifier) → Repository → Dio → API`.
All failures cross the boundary as `AppException` with user-friendly messages.

---

## Getting Started

### Prerequisites
- Flutter **3.16+** (Dart 3.2+) — earlier versions may not compile the theme
  code (uses `withOpacity`, `CardTheme`, `MaterialStateProperty`).
- Android SDK (platform 34) + a JDK 17–21 (Gradle 8.5 / AGP 8.2.2 are pinned
  in `android/` and are compatible with JDK 21).

### 1. Install dependencies
```bash
cd mobile
flutter pub get
```

### 2. Point the app at your backend
The backend base URL defaults to `http://10.0.2.2:8000/api/v1/` (Android
emulator → host machine). Override at build/run time:

```bash
# Real device / remote backend
flutter run --dart-define=API_BASE_URL=https://your-backend.example.com/api/v1/

# Android emulator with local FastAPI on port 8000 (default, no flag needed)
flutter run
```

Cleartext HTTP is permitted **only** for `10.0.2.2` / `localhost` via the
Android network security config; everything else must be HTTPS.

### 3. Run
```bash
flutter run                # on a connected device / emulator
flutter build apk --debug  # debug APK → build/app/outputs/flutter-apk/
flutter build apk --release
```

---

## Configuration

| Key | Default | Purpose |
|-----|---------|---------|
| `API_BASE_URL` | `http://10.0.2.2:8000/api/v1/` | Backend root (dart-define) |
| `org.gradle.jvmargs` | `-Xmx4G` | Gradle heap (`android/gradle.properties`) |
| `compileSdk/targetSdk` | 34 | Android SDK levels |
| `minSdk` | 21 (Flutter default) | Minimum Android version |

Application ID: `com.lastmoribund.cleandelivery`.

---

## Dependencies

```yaml
dependencies:
  dio: ^5.4.0        # HTTP client + interceptors
  provider: ^6.1.1   # state management
  shared_preferences: ^2.2.2  # secure-ish local storage
  intl: ^0.19.0      # MMK currency / date formatting
```

Run `flutter pub outdated` to see newer versions (several newer majors exist;
pin deliberately for Dart 3.2 compatibility).

---

## Testing & Verification

```bash
cd mobile
flutter analyze        # static analysis — must report "No issues found"
flutter test           # 23 unit + widget tests
flutter build apk --debug   # full Gradle smoke build
```

The test suite covers:
- Model JSON parsing incl. string-vs-number prices and missing fields
- Money / date / status-label formatters
- `AuthRepository` success + error mapping using an in-memory fake HTTP
  adapter (including refresh-token cookie extraction)
- Widget tests for login validation, OTP navigation, catalogue rendering and
  cart totals

An end-to-end smoke test on an Android emulator verified: install, launch,
login-screen render, client-side validation, and the friendly network-error
path (backend offline) with **no crashes**.

---

## API Endpoints Used

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/auth/request-otp` | Request 6-digit OTP |
| POST | `/auth/verify-otp` | Verify OTP → tokens |
| POST | `/auth/refresh` | Rotate access token (mobile JSON flow) |
| GET  | `/auth/me` | Current user profile |
| GET  | `/products` | Product catalogue |
| POST | `/orders` | Place order |
| GET  | `/orders/history` | Customer order history |
| GET  | `/orders/{id}` | Single order (tracking) |
| GET  | `/drivers/orders` | Assigned deliveries |
| PATCH| `/drivers/orders/{id}/status` | Update status |
| POST | `/drivers/location` | Report GPS position |
| POST | `/drivers/optimize-route` | Optimised delivery sequence |

---

## Troubleshooting

- **`flutter` hangs on first run** — the tool performs a version check that
  needs network access to GitHub. With restricted network, pre-seed
  `bin/cache/flutter_version_check.stamp` or use `--no-version-check`.
- **Java/Gradle version mismatch** — JDK 21 requires Gradle 8.5+; the pinned
  `gradle-wrapper.properties` (8.5) and AGP 8.2.2 already satisfy this.
- **`One or more plugins require a higher Android NDK version`** — advisory
  only; the app does not use NDK plugins and builds fine.
- **Login on a physical device** — replace the default API base URL with your
  LAN/HTTPS address via `--dart-define=API_BASE_URL=...`.
