-- 20260805000101_create_inventory_table.sql
-- Live project is missing the inventory table. Create idempotently so the
-- perf-index migration can index inventory.branch_id.
-- NOTE: no FK to branches (the branches table does not exist on this project).
CREATE TABLE IF NOT EXISTS public.inventory (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    branch_id     UUID,
    full_bottles  INTEGER NOT NULL DEFAULT 0,
    empty_bottles INTEGER NOT NULL DEFAULT 0,
    caps_count    INTEGER NOT NULL DEFAULT 0,
    labels_count  INTEGER NOT NULL DEFAULT 0,
    water_liters  NUMERIC NOT NULL DEFAULT 0,
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);