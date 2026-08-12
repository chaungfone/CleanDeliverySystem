# Clean Delivery System - Production Deployment Guide

## 0. Mobile App (Flutter)

The mobile application is a **Flutter** rewrite of the previous Kotlin
(Android) app and lives in [`mobile/`](mobile/README.md).

- **Customer app:** phone + OTP login, water product catalogue, cart,
  checkout, order tracking.
- **Driver app:** online/offline toggle, assigned deliveries, status updates,
  earnings history.
- **Build:** `cd mobile && flutter pub get && flutter build apk --debug`
- **Backend URL:** defaults to `http://10.0.2.2:8000/api/v1/` (emulator →
  host). Override with `--dart-define=API_BASE_URL=...`.

See [`mobile/README.md`](mobile/README.md) for full documentation, setup and
testing instructions.

## 1. Supabase Setup
### Local Development
1. Install Supabase CLI.
2. Run `supabase init`.
3. Start local emulator: `supabase start`.
4. Apply migrations: `supabase db reset`.

### Cloud Deployment
1. Link project: `supabase link --project-ref <your-project-id>`.
2. Push migrations: `supabase db push`.
3. Deploy Edge Functions: `supabase functions deploy notify-order-status`.

## 2. Backend (FastAPI) Setup
### Environment Variables (.env)
Set the following variables in your production environment:
- `SUPABASE_URL`
- `SUPABASE_KEY` (service_role for backend)
- `SUPABASE_JWT_SECRET`
- `SENTRY_DSN`
- `WEBHOOK_SECRET` (for verifying Supabase calls)

### Deployment
Use the provided `Dockerfile` and `docker-compose.yml` for containerized deployment.

## 3. Production Security Checklist
- [ ] **RLS Policies**: Ensure `public.users` can only be updated by the owner.
- [ ] **Service Role Key**: Never expose the `service_role` key in the frontend or mobile app.
- [ ] **Database Backups**: Enable Supabase point-in-time recovery for production.
- [ ] **SSL**: Ensure all communication is over HTTPS.
- [ ] **Rate Limiting**: Monitor `slowapi` logs for potential abuse.

## 4. CI/CD
The project includes a GitHub Actions workflow in `.github/workflows/supabase_deploy.yml` that automates testing and deployment to Supabase Cloud.

## 5. Database Migrations and Testing

### Running Migrations
To apply database migrations, use the provided script:
- Windows: .\scripts\run_migrations.ps1
- Unix: ./scripts/run_migrations.sh
Alternatively, if you have make installed, you can run make migrate.


### Required GitHub Repository Secrets
For GitHub Actions workflows (e.g., supabase_deploy.yml and lighthouse.yml), the following secrets must be set:
- SUPABASE_DATABASE_URL: The pooled connection string (port 6543) used by the application runtime.
- SUPABASE_DIRECT_URL: The direct connection string (port 5432) used for migrations and admin tasks.


### Running Tests
To execute the test suite locally:
- Windows: .\scripts\run_tests.ps1
- Unix: pytest backend/tests

### PgBouncer transaction pooling
When running the app against a Supabase **transaction-pooler** endpoint, set
`PGBOUNCER_TRANSACTION_POOLING=true` in the environment (or `.env`). The DB helper
(`backend/app/core/db.py`) then selects `NullPool` and appends
`prepared_statement_cache_size=0` for asyncpg. If unset, it falls back to
URL-based heuristics (port 6543 / `pgbouncer=true` / host containing "pooler").


