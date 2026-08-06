-- 20260806000003_jwt_denylist.sql
-- JWT jti deny-list for refresh-token revocation (logout, password reset,
-- GDPR force logout). The backend (service_role) inserts/looks-up here.
CREATE TABLE IF NOT EXISTS public.revoked_tokens (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    jti         TEXT NOT NULL UNIQUE,
    user_id     UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    revoked_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at  TIMESTAMPTZ NOT NULL
);

-- Fast O(1)-ish lookup by jti (also served by the UNIQUE constraint).
CREATE INDEX IF NOT EXISTS idx_revoked_tokens_jti ON public.revoked_tokens (jti);

-- RLS: a user may see/insert only their own revocations (service_role bypasses).
ALTER TABLE public.revoked_tokens ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Token revocations self service" ON public.revoked_tokens;
CREATE POLICY "Token revocations self service" ON public.revoked_tokens
    FOR ALL USING (user_id = auth.uid())
    WITH CHECK (user_id = auth.uid());