-- 20260806000001_perf_indexes.sql
-- Performance: B-tree indexes for top-7 slow-query columns.
-- Apply via migration/CI. After applying, run `EXPLAIN ANALYZE` on the hot
-- queries to confirm the planner uses Index Scan instead of Seq Scan.
-- All statements are idempotent (IF NOT EXISTS).

-- 1. Orders filtered by assigned driver (load_orders_with_items / dispatch).
CREATE INDEX IF NOT EXISTS idx_orders_driver_id ON public.orders (driver_id);

-- 2. Order items fetched by order_id (load_orders_with_items, admin detail).
CREATE INDEX IF NOT EXISTS idx_order_items_order_id ON public.order_items (order_id);

-- 3. Role-based account queries (admin staff/drivers lists, authz lookups).
CREATE INDEX IF NOT EXISTS idx_users_role ON public.users (role);

-- 4. Login/OTP lookup by normalized phone number.
CREATE INDEX IF NOT EXISTS idx_users_phone_number ON public.users (phone_number);

-- 5. Per-branch inventory lookups/updates.
CREATE INDEX IF NOT EXISTS idx_inventory_branch_id ON public.inventory (branch_id);

-- 6. Addresses owned by a user (place_order ownership check).
CREATE INDEX IF NOT EXISTS idx_addresses_user_id ON public.addresses (user_id);

-- 7. Driver "last-ping" freshness for the live fleet tracker.
CREATE INDEX IF NOT EXISTS idx_driver_locations_updated ON public.driver_locations (updated_at DESC);

-- Refresh planner statistics so the optimizer favors the new indexes
-- (helps turn Seq Scans into Index Scans).
ANALYZE public.orders;
ANALYZE public.order_items;
ANALYZE public.users;
ANALYZE public.inventory;
ANALYZE public.addresses;
ANALYZE public.driver_locations;