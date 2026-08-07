-- ============================================================================
-- Migration: Create audit_logs table
-- Created: 2026-08-06
-- Purpose: Store change audit trails with who/when/what/old_value/new_value
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.audit_logs (
    id           BIGSERIAL PRIMARY KEY,
    who          TEXT, -- identifier of actor (user id, service name, or system)
    action_time  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    what         TEXT NOT NULL, -- brief description or object identifier (e.g. "orders.update")
    old_value    JSONB, -- previous state (nullable)
    new_value    JSONB  -- new state (nullable)
);

-- Useful index for retention/queries by time
CREATE INDEX IF NOT EXISTS idx_audit_logs_action_time ON public.audit_logs (action_time DESC);

-- Optional: index on who for faster actor lookups
CREATE INDEX IF NOT EXISTS idx_audit_logs_who ON public.audit_logs (who);
