-- 20260806000000_rls_policies.sql
-- RLS sanity audit: self-owned read/write + role-based visibility.
-- NOTE: the backend authenticates with the service_role key (bypasses RLS), so these
-- policies are defense-in-depth for anonymous/authenticated client access. Code-level
-- authorization (CurrentUser / require_* / require_owner_or_admin) remains the authority.

-- Users: Self-only read/update/delete
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
-- Remove the old permissive policy that undermined self-only access.
DROP POLICY IF EXISTS "Public profiles are viewable by everyone." ON users;
DROP POLICY IF EXISTS "Users self access" ON users;
CREATE POLICY "Users self access" ON users
  FOR ALL USING (auth.uid() = id)
  WITH CHECK (auth.uid() = id);

-- Orders: Customer sees own and can create own; staff sees branch
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Order visibility" ON orders;
DROP POLICY IF EXISTS "Orders insert own" ON orders;
CREATE POLICY "Order visibility" ON orders FOR SELECT USING (
  customer_id = auth.uid()
  OR EXISTS (SELECT 1 FROM users u WHERE u.id = auth.uid() AND u.role IN ('ADMIN','BRANCH_MANAGER','DRIVER','FRANCHISE_DEALER'))
);
CREATE POLICY "Orders insert own" ON orders FOR INSERT
  WITH CHECK (customer_id = auth.uid());

-- Addresses: Self only (select/insert/update/delete)
ALTER TABLE addresses ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Addresses self access" ON addresses;
CREATE POLICY "Addresses self access" ON addresses FOR ALL
  USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());

-- Reviews: author reads/writes own; driver reads reviews of their orders
ALTER TABLE reviews ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Anyone can view reviews." ON reviews;
DROP POLICY IF EXISTS "Reviews visibility" ON reviews;
DROP POLICY IF EXISTS "Reviews insert own" ON reviews;
DROP POLICY IF EXISTS "Reviews update own" ON reviews;
CREATE POLICY "Reviews visibility" ON reviews FOR SELECT USING (
  customer_id = auth.uid()
  OR driver_id = auth.uid()
  OR EXISTS (SELECT 1 FROM users u WHERE u.id = auth.uid() AND u.role IN ('ADMIN','BRANCH_MANAGER','FRANCHISE_DEALER'))
);
CREATE POLICY "Reviews insert own" ON reviews FOR INSERT
  WITH CHECK (customer_id = auth.uid());
CREATE POLICY "Reviews update own" ON reviews FOR UPDATE
  USING (customer_id = auth.uid());