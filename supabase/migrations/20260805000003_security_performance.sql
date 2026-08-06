-- ============================================================================
-- Security Hardening & Performance Optimization
-- 1. Tightened RLS Policies
-- 2. Performance Indexes (Composite)
-- 3. Data Compliance (Cascading Account Deletion)
-- ============================================================================

-- 1. TIGHTENED RLS POLICIES
-- Ensure customers can only see their own address details, including PostGIS location
DROP POLICY IF EXISTS "addresses_select_own" ON public.addresses;
CREATE POLICY "addresses_select_own" ON public.addresses
    FOR SELECT USING (user_id = auth.uid());

-- Ensure drivers can only see orders assigned to them or available for picking (if branch matches)
DROP POLICY IF EXISTS "orders_select_assigned_driver" ON public.orders;
CREATE POLICY "orders_select_assigned_driver" ON public.orders
    FOR SELECT USING (
        driver_id = auth.uid()
        OR (auth.role() = 'authenticated' AND branch_id IN (SELECT branch_id FROM public.users WHERE id = auth.uid()))
    );

-- 2. PERFORMANCE INDEXES
-- Optimized for: "Find all pending orders for my branch"
CREATE INDEX IF NOT EXISTS idx_orders_branch_status ON public.orders (branch_id, status);

-- Optimized for: "Show my order history"
CREATE INDEX IF NOT EXISTS idx_orders_customer_created ON public.orders (customer_id, created_at DESC);

-- Optimized for: "Active driver tracking"
CREATE INDEX IF NOT EXISTS idx_driver_locations_updated ON public.driver_locations (updated_at DESC);

-- 3. DATA COMPLIANCE: Account Deletion Support
-- Ensure deletions cascade correctly across all linked tables
-- Users -> Addresses (already cascade)
-- Users -> Orders (SET NULL or CASCADE based on requirement, here we SET NULL to keep transaction history but anonymized if needed, or CASCADE for "Right to be Forgotten")
-- For "Right to be Forgotten", we CASCADE.
ALTER TABLE public.orders DROP CONSTRAINT IF EXISTS orders_customer_id_fkey;
ALTER TABLE public.orders ADD CONSTRAINT orders_customer_id_fkey
    FOREIGN KEY (customer_id) REFERENCES public.users(id) ON DELETE CASCADE;

-- 4. MATERIALIZED VIEW FOR DAILY STATS (Performance)
CREATE MATERIALIZED VIEW IF NOT EXISTS public.daily_revenue_stats AS
SELECT
    branch_id,
    created_at::date as report_date,
    SUM(total_amount) as revenue,
    COUNT(id) as total_orders
FROM public.orders
WHERE status = 'DELIVERED'
GROUP BY branch_id, created_at::date;

CREATE UNIQUE INDEX IF NOT EXISTS idx_daily_stats_branch_date ON public.daily_revenue_stats (branch_id, report_date);

-- Refresh function for the view
CREATE OR REPLACE FUNCTION refresh_daily_stats()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY public.daily_revenue_stats;
END;
$$ LANGUAGE plpgsql;
