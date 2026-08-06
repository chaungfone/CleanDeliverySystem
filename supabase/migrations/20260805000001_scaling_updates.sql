-- ============================================================================
-- Scaling & Advanced Features Migration
-- 1. Reviews Table
-- 2. Archiving Infrastructure
-- 3. Performance Indexes
-- ============================================================================

-- 1. REVIEWS TABLE
CREATE TABLE IF NOT EXISTS public.reviews (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id     UUID NOT NULL REFERENCES public.orders(id) ON DELETE CASCADE,
    customer_id  UUID NOT NULL REFERENCES public.users(id),
    driver_id    UUID REFERENCES public.users(id),
    rating       INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
    comment      TEXT,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- RLS for Reviews
ALTER TABLE public.reviews ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Anyone can view reviews." ON public.reviews FOR SELECT USING (true);
CREATE POLICY "Customers can create reviews for their own orders."
    ON public.reviews FOR INSERT WITH CHECK (customer_id = auth.uid());

-- 2. ARCHIVING INFRASTRUCTURE
-- Create archive tables matching the original schema
CREATE TABLE IF NOT EXISTS public.orders_archive (LIKE public.orders INCLUDING ALL);
CREATE TABLE IF NOT EXISTS public.order_items_archive (LIKE public.order_items INCLUDING ALL);

-- Function to archive old orders (> 6 months)
CREATE OR REPLACE FUNCTION archive_old_orders()
RETURNS void AS $$
BEGIN
    -- Move order items first
    INSERT INTO public.order_items_archive
    SELECT oi.* FROM public.order_items oi
    JOIN public.orders o ON o.id = oi.order_id
    WHERE o.status IN ('DELIVERED', 'CANCELLED')
      AND o.created_at < NOW() - INTERVAL '6 months';

    -- Move orders
    INSERT INTO public.orders_archive
    SELECT * FROM public.orders
    WHERE status IN ('DELIVERED', 'CANCELLED')
      AND created_at < NOW() - INTERVAL '6 months';

    -- Delete from active tables (cascading items will be handled by foreign keys if not using SELECT * archive)
    -- But since we copied data, we delete explicitly
    DELETE FROM public.orders
    WHERE status IN ('DELIVERED', 'CANCELLED')
      AND created_at < NOW() - INTERVAL '6 months';
END;
$$ LANGUAGE plpgsql;

-- 3. PERFORMANCE INDEXES
CREATE INDEX IF NOT EXISTS idx_orders_customer_status ON public.orders (customer_id, status);
CREATE INDEX IF NOT EXISTS idx_orders_created_at_desc ON public.orders (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_reviews_driver_id ON public.reviews (driver_id);
