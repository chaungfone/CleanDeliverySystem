# Runbook — Supabase Restore / Recovery

**Scope:** Supabase (e.g. `eettoiqgeecfnjbbuyni`) is unreachable, degraded, or a schema/data rollback is needed.

## 1. Detect
`/healthz` returns `"supabase": "unreachable"`; `status: degraded`. Backend routes return 5xx from PostgREST.
```powershell
Invoke-RestMethod http://127.0.0.1:8000/healthz -TimeoutSec 5
```

## 2. Connectivity & credentials
1. Confirm project reachable: dashboard https://supabase.com/dashboard/project/eettoiqgeecfnjbbuyni.
2. Verify `SUPABASE_URL`, `SUPABASE_KEY`, `SUPABASE_JWT_SECRET` in `backend/.env` (or `.env.staging`).
   - Service-role key rotates → update all environments; NEVER commit.
3. DB status page (Postgres, connection poolers).

## 3. Backup before any change
- Enable PITR / take a database backup via Dashboard → Database → Backups.
  Manual SQL backup (needs `pg_dump` + DB password):
  ```powershell
  pg_dump "postgresql://postgres:[DB_PASSWORD]@db.eettoiqgeecfnjbbuyni.supabase.co:5432/postgres" -Fc -f backup.dump
  ```

## 4. Apply schema migrations (runbooks Option B)
Supabase CLI (npx):
```powershell
npx supabase login                 # supply SUPABASE_ACCESS_TOKEN
npx supabase link --project-ref eettoiqgeecfnjbbuyni
npx supabase db push --dry-run     # preview first
npx supabase db push               # apply pending migrations under supabase/migrations/
```
Then verify each new index/RLS policy with `EXPLAIN ANALYZE` (expect `Index Scan`, not `Seq Scan`).

## 5. Revert a migration
Inside the Supabase SQL Editor run the inverse `DROP`:
```sql
-- Example: undo perf indexes
DROP INDEX IF EXISTS public.idx_orders_driver_id;
DROP INDEX IF EXISTS public.idx_order_items_order_id;
-- ... drop the rest from 20260806000001_perf_indexes.sql
-- Revert RLS in 20260806000000 as needed (policy drops before re-creating prior state)
```

## 6. Verify recovery
```powershell
# Supabase reachable
Invoke-RestMethod http://127.0.0.1:8000/healthz -TimeoutSec 5
# Backend tests
cd backend; .\.venv\Scripts\python.exe -m pytest tests/ -q
# Security smoke
.\scripts\security_smoke.ps1
```

> **Never run manual `DROP/TRUNCATE/UPDATE` on production directly** — use a migration file under `supabase/migrations/` (Option B policy).