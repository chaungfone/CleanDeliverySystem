-- 20260805000006_create_reviews_table.sql
-- The live project predates the reviews table (defined only in a legacy migration
-- that was never applied). Ensure it exists (idempotent) before RLS policies attach.
CREATE TABLE IF NOT EXISTS public.reviews (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id    UUID NOT NULL REFERENCES public.orders(id) ON DELETE CASCADE,
    customer_id UUID NOT NULL REFERENCES public.users(id),
    driver_id   UUID REFERENCES public.users(id),
    rating      INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
    comment     TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);