-- 20260806000002_orders_customer_idx.sql
-- Support order-history lookups: filter by customer_id, sorted by created_at DESC.
-- The legacy idx_orders_customer_created was never applied to the live project,
-- so it is created here explicitly.
CREATE INDEX IF NOT EXISTS idx_orders_customer_created
    ON public.orders (customer_id, created_at DESC);