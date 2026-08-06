# Runbook — Server Down

**Scope:** Backend (Uvicorn :8000/:8001) or web-dashboard (Vite :3000/:3005) is down or unhealthy.

## 1. Detect
```powershell
# Backend health (must return {"status":"ok"})
Invoke-RestMethod http://127.0.0.1:8000/healthz -TimeoutSec 5

# Ports listening
Get-NetTCPConnection -State Listen | Where-Object { $_.LocalPort -in 8000,8001,3000,3005 }
```

Symptoms: `connection refused`, request timeout, `/healthz` returns `degraded`, browser `Failed to fetch`.

## 2. Diagnose
```powershell
# Backend logs (if captured to a file)
Get-Content backend/logs/*.log -Tail 50
# Windows Event / process check
Get-Process python -ErrorAction SilentlyContinue | Select-Object Id, StartTime
```

Check `/healthz` JSON: if `services.supabase` = `unreachable`, DB credential/Supabase outage (see `supabase_restore.md`).

## 3. Restart Backend (dev/staging)
```powershell
cd backend
.\.venv\Scripts\activate
# Dev
uvicorn app.main:app --port 8000
# Staging
uvicorn app.main:app --port 8001 --env-file .env.staging
```
Verify: `Invoke-RestMethod http://127.0.0.1:8000/healthz`.

## 4. Restart Web-dashboard
```powershell
cd web-dashboard
npm run dev          # :3000
npm run dev:staging  # :3005 --mode staging
```

## 5. If it still fails
1. Check `.env` exists + is populated (backend) and `web-dashboard/.env.staging` exists.
2. Confirm Supabase project reachable (see `supabase_restore.md`).
3. Review `backend⇒logs` and replicate the failing request; open a bug against `docs/bug_inventory.md`.

> **Rollback:** if a recent commit broke startup, `git log --oneline -5`, then
> `git checkout <last-good-commit> -- backend` and restart.