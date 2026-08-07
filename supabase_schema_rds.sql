-- ============================================================================
-- Water Delivery Management System - AWS RDS (PostgreSQL) Database Schema
-- Based on PRD v2.1 - Section 9 (Database Design) & Section 11 (Security)
-- AWS-compatible variant of supabase_schema.sql
--
-- Prerequisites:
--   * RDS PostgreSQL 13+ (gen_random_uuid built-in; pgcrypto loaded as backup)
--   * Run as rds_superuser so CREATE EXTENSION postgis is allowed:
--       GRANT rds_superuser TO <db_user>;   (once, by the master user)
-- ============================================================================

-- ============================================================================
-- 1. EXTENSIONS & ENUM TYPES
-- ============================================================================

-- PostGIS: enables GEOGRAPHY type and spatial / distance queries
CREATE EXTENSION IF NOT EXISTS postgis;

-- gen_random_uuid() fallback (built into PG 13+; harmless to keep)
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- User role: who can do what in the system
CREATE TYPE user_role AS ENUM ('CUSTOMER', 'DRIVER', 'ADMIN');

-- Order lifecycle states
CREATE TYPE order_status AS ENUM (
    'PENDING', 'CONFIRMED', 'ASSIGNED', 'IN_TRANSIT', 'DELIVERED', 'CANCELLED'
);

-- Payment flow states
CREATE TYPE payment_status AS ENUM ('PENDING', 'PAID', 'FAILED');

-- Accepted payment channels
CREATE TYPE payment_method AS ENUM ('COD', 'KPAY', 'WAVE_PAY', 'OTHER');

-- ============================================================================
-- 1.5 AUTH HELPER (AWS has no auth.uid() - backend sets request.jwt.claims)
-- ============================================================================

-- Returns the UUID of the current authenticated user.
-- The FastAPI backend MUST set the GUC before each statement / transaction:
--
--   SET LOCAL request.jwt.claims = '{"sub": "user-uuid", "role": "CUSTOMER"}';
--
-- Returns NULL when unauthenticated (server-side/backoffice connections
-- may then rely on an admin bypass role instead of RLS).
CREATE OR REPLACE FUNCTION requesting_user_id()
RETURNS UUID
LANGUAGE sql
STABLE
AS $$
    SELECT NULLIF(
        current_setting('request.jwt.claims', true)::json ->> 'sub',
        ''
    )::uuid;
$$;

-- ============================================================================
-- 2. DATABASE TABLES
-- ============================================================================

-- ----------------------------------------------------------------------------
-- users: every account (customer, driver, admin)
-- ----------------------------------------------------------------------------
CREATE TABLE users (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone_number VARCHAR(20)  NOT NULL UNIQUE,
    full_name    VARCHAR(255) NOT NULL,
    role         user_role    NOT NULL DEFAULT 'CUSTOMER',
    created_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- ----------------------------------------------------------------------------
-- addresses: customer delivery addresses (multi-address support)
-- ----------------------------------------------------------------------------
CREATE TABLE addresses (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id      UUID             NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    address_line TEXT             NOT NULL,
    township     VARCHAR(100),
    latitude     DECIMAL(10, 8),
    longitude    DECIMAL(11, 8),
    -- Generated PostGIS point (longitude, latitude) for distance calculations
    location     GEOGRAPHY(POINT, 4326) GENERATED ALWAYS AS (
                     ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)::geography
                 ) STORED,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ----------------------------------------------------------------------------
-- products: catalogue items (bottled water, dispensers, ...)
-- ----------------------------------------------------------------------------
CREATE TABLE products (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name           VARCHAR(255) NOT NULL,
    description    TEXT,
    price          NUMERIC(10, 2) NOT NULL CHECK (price >= 0),
    deposit_fee    NUMERIC(10, 2) NOT NULL DEFAULT 0 CHECK (deposit_fee >= 0),
    stock_quantity INTEGER       NOT NULL DEFAULT 0 CHECK (stock_quantity >= 0),
    created_at     TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

-- ----------------------------------------------------------------------------
-- orders: order headers
-- ----------------------------------------------------------------------------
CREATE TABLE orders (
    id                     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id            UUID NOT NULL REFERENCES users(id),
    driver_id              UUID REFERENCES users(id) ON DELETE SET NULL,
    address_id             UUID NOT NULL REFERENCES addresses(id),
    status                 order_status   NOT NULL DEFAULT 'PENDING',
    total_amount           NUMERIC(10, 2) NOT NULL DEFAULT 0 CHECK (total_amount >= 0),
    payment_status         payment_status NOT NULL DEFAULT 'PENDING',
    payment_method         payment_method NOT NULL DEFAULT 'COD',
    empty_bottles_returned INTEGER        NOT NULL DEFAULT 0 CHECK (empty_bottles_returned >= 0),
    created_at             TIMESTAMPTZ    NOT NULL DEFAULT NOW()
);

-- ----------------------------------------------------------------------------
-- order_items: line items belonging to an order
-- ----------------------------------------------------------------------------
CREATE TABLE order_items (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id   UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    product_id UUID NOT NULL REFERENCES products(id),
    quantity   INTEGER       NOT NULL CHECK (quantity > 0),
    unit_price NUMERIC(10, 2) NOT NULL CHECK (unit_price >= 0)
);

-- ----------------------------------------------------------------------------
-- driver_locations: live GPS position of each driver (latest position only)
-- ----------------------------------------------------------------------------
CREATE TABLE driver_locations (
    driver_id  UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    location   GEOGRAPHY(POINT, 4326) NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ----------------------------------------------------------------------------
-- user_bottle_balances: empty bottles currently held at each customer
-- ----------------------------------------------------------------------------
CREATE TABLE user_bottle_balances (
    user_id            UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    empty_bottles_held INTEGER     NOT NULL DEFAULT 0 CHECK (empty_bottles_held >= 0),
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================================
-- 3. TRIGGERS & FUNCTIONS
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 3.1 Stock auto-deduction on order DELIVERED
--     - If order transitions INTO 'DELIVERED': deduct sold quantities
--       from products.stock_quantity, aborting if stock is insufficient.
--     - If order transitions OUT OF 'DELIVERED': restore stock (safety).
-- ----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION deduct_stock_on_delivery()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.status = 'DELIVERED' AND OLD.status <> 'DELIVERED' THEN

        -- Fail the whole operation if any line cannot be satisfied
        IF EXISTS (
            SELECT 1
            FROM order_items oi
            JOIN products  p ON p.id = oi.product_id
            WHERE oi.order_id = NEW.id
              AND p.stock_quantity < oi.quantity
        ) THEN
            RAISE EXCEPTION 'Insufficient stock to deliver order %', NEW.id;
        END IF;

        -- Deduct stock for every line item
        UPDATE products p
        SET stock_quantity = p.stock_quantity - oi.quantity
        FROM order_items oi
        WHERE oi.product_id = p.id
          AND oi.order_id   = NEW.id;

    ELSIF OLD.status = 'DELIVERED' AND NEW.status <> 'DELIVERED' THEN

        -- Order moved back from DELIVERED (e.g. cancelled after delivery):
        -- put the stock back so totals stay consistent
        UPDATE products p
        SET stock_quantity = p.stock_quantity + oi.quantity
        FROM order_items oi
        WHERE oi.product_id = p.id
          AND oi.order_id   = NEW.id;
    END IF;

    RETURN NEW;
END;
$$;

-- Run the stock logic whenever the order status column is updated
CREATE TRIGGER trg_deduct_stock_on_delivery
BEFORE UPDATE OF status ON orders
FOR EACH ROW
EXECUTE FUNCTION deduct_stock_on_delivery();

-- ----------------------------------------------------------------------------
-- 3.2 Automatic updated_at maintenance
-- ----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_driver_locations_updated_at
BEFORE UPDATE ON driver_locations
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_user_bottle_balances_updated_at
BEFORE UPDATE ON user_bottle_balances
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

-- ----------------------------------------------------------------------------
-- 3.3 Role-change protection: only an ADMIN may change a user's role
-- ----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION protect_role_change()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    IF OLD.role IS DISTINCT FROM NEW.role THEN
        IF public.app_role() IS DISTINCT FROM 'ADMIN' THEN
            RAISE EXCEPTION 'Only an admin can change user roles';
        END IF;
    END IF;
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_protect_role_change
BEFORE UPDATE OF role ON users
FOR EACH ROW
EXECUTE FUNCTION protect_role_change();

-- ============================================================================
-- 4. ROW LEVEL SECURITY (RLS) - PRD v2.1 Section 11.1
-- ============================================================================

-- Helper: current user's role, read from our own public.users table.
-- SECURITY DEFINER + security_invoker NOT set => bypasses RLS on users.
CREATE OR REPLACE FUNCTION app_role()
RETURNS user_role
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
    SELECT role FROM public.users WHERE id = requesting_user_id();
$$;

-- ----------------------------------------------------------------------------
-- users
--   - users: view / update own profile
--   - admin: full access
-- ----------------------------------------------------------------------------
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

CREATE POLICY "users_select_own" ON users
    FOR SELECT USING (id = requesting_user_id());

CREATE POLICY "users_update_own" ON users
    FOR UPDATE USING (id = requesting_user_id()) WITH CHECK (id = requesting_user_id());

CREATE POLICY "users_all_admin" ON users
    FOR ALL USING (public.app_role() = 'ADMIN')
    WITH CHECK (public.app_role() = 'ADMIN');

-- ----------------------------------------------------------------------------
-- addresses
--   - customer: full CRUD on own addresses
--   - admin: full access
-- ----------------------------------------------------------------------------
ALTER TABLE addresses ENABLE ROW LEVEL SECURITY;

CREATE POLICY "addresses_select_own" ON addresses
    FOR SELECT USING (user_id = requesting_user_id());

CREATE POLICY "addresses_insert_own" ON addresses
    FOR INSERT WITH CHECK (user_id = requesting_user_id());

CREATE POLICY "addresses_update_own" ON addresses
    FOR UPDATE USING (user_id = requesting_user_id()) WITH CHECK (user_id = requesting_user_id());

CREATE POLICY "addresses_delete_own" ON addresses
    FOR DELETE USING (user_id = requesting_user_id());

CREATE POLICY "addresses_all_admin" ON addresses
    FOR ALL USING (public.app_role() = 'ADMIN')
    WITH CHECK (public.app_role() = 'ADMIN');

-- ----------------------------------------------------------------------------
-- products
--   - any authenticated user: view catalogue
--   - admin: full access
-- ----------------------------------------------------------------------------
ALTER TABLE products ENABLE ROW LEVEL SECURITY;

CREATE POLICY "products_select_all" ON products
    FOR SELECT USING (true);

CREATE POLICY "products_all_admin" ON products
    FOR ALL USING (public.app_role() = 'ADMIN')
    WITH CHECK (public.app_role() = 'ADMIN');

-- ----------------------------------------------------------------------------
-- orders
--   - customer: view / update own orders (place order = INSERT own)
--   - driver: view / update only orders assigned to them
--   - admin: full access
-- ----------------------------------------------------------------------------
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;

CREATE POLICY "orders_select_own" ON orders
    FOR SELECT USING (customer_id = requesting_user_id());

CREATE POLICY "orders_insert_own" ON orders
    FOR INSERT WITH CHECK (customer_id = requesting_user_id());

CREATE POLICY "orders_update_own" ON orders
    FOR UPDATE USING (customer_id = requesting_user_id()) WITH CHECK (customer_id = requesting_user_id());

CREATE POLICY "orders_select_assigned_driver" ON orders
    FOR SELECT USING (driver_id = requesting_user_id());

CREATE POLICY "orders_update_assigned_driver" ON orders
    FOR UPDATE USING (driver_id = requesting_user_id()) WITH CHECK (driver_id = requesting_user_id());

CREATE POLICY "orders_all_admin" ON orders
    FOR ALL USING (public.app_role() = 'ADMIN')
    WITH CHECK (public.app_role() = 'ADMIN');

-- ----------------------------------------------------------------------------
-- order_items
--   - customer: view / insert items of own orders
--   - driver: view items of assigned orders
--   - admin: full access
-- ----------------------------------------------------------------------------
ALTER TABLE order_items ENABLE ROW LEVEL SECURITY;

CREATE POLICY "order_items_select_customer" ON order_items
    FOR SELECT USING (
        order_id IN (SELECT id FROM orders WHERE customer_id = requesting_user_id())
    );

CREATE POLICY "order_items_insert_customer" ON order_items
    FOR INSERT WITH CHECK (
        order_id IN (SELECT id FROM orders WHERE customer_id = requesting_user_id())
    );

CREATE POLICY "order_items_select_driver" ON order_items
    FOR SELECT USING (
        order_id IN (SELECT id FROM orders WHERE driver_id = requesting_user_id())
    );

CREATE POLICY "order_items_all_admin" ON order_items
    FOR ALL USING (public.app_role() = 'ADMIN')
    WITH CHECK (public.app_role() = 'ADMIN');

-- ----------------------------------------------------------------------------
-- driver_locations
--   - driver: view / update own location
--   - customer: view live location of the driver handling their order
--   - admin: full access
-- ----------------------------------------------------------------------------
ALTER TABLE driver_locations ENABLE ROW LEVEL SECURITY;

CREATE POLICY "driver_locations_select_own" ON driver_locations
    FOR SELECT USING (driver_id = requesting_user_id());

CREATE POLICY "driver_locations_insert_own" ON driver_locations
    FOR INSERT WITH CHECK (driver_id = requesting_user_id());

CREATE POLICY "driver_locations_update_own" ON driver_locations
    FOR UPDATE USING (driver_id = requesting_user_id()) WITH CHECK (driver_id = requesting_user_id());

CREATE POLICY "driver_locations_select_customer" ON driver_locations
    FOR SELECT USING (
        driver_id IN (
            SELECT driver_id FROM orders
            WHERE customer_id = requesting_user_id() AND driver_id IS NOT NULL
        )
    );

CREATE POLICY "driver_locations_all_admin" ON driver_locations
    FOR ALL USING (public.app_role() = 'ADMIN')
    WITH CHECK (public.app_role() = 'ADMIN');

-- ----------------------------------------------------------------------------
-- user_bottle_balances
--   - customer: view / update own bottle balance
--   - admin: full access
-- ----------------------------------------------------------------------------
ALTER TABLE user_bottle_balances ENABLE ROW LEVEL SECURITY;

CREATE POLICY "bottle_balances_select_own" ON user_bottle_balances
    FOR SELECT USING (user_id = requesting_user_id());

CREATE POLICY "bottle_balances_insert_own" ON user_bottle_balances
    FOR INSERT WITH CHECK (user_id = requesting_user_id());

CREATE POLICY "bottle_balances_update_own" ON user_bottle_balances
    FOR UPDATE USING (user_id = requesting_user_id()) WITH CHECK (user_id = requesting_user_id());

CREATE POLICY "bottle_balances_all_admin" ON user_bottle_balances
    FOR ALL USING (public.app_role() = 'ADMIN')
    WITH CHECK (public.app_role() = 'ADMIN');

-- ============================================================================
-- 5. PERFORMANCE INDEXES - PRD v2.1 Section 11.2
-- ============================================================================

-- orders: fast filtering by customer / driver / status / payment / recency
CREATE INDEX idx_orders_customer_id     ON orders (customer_id);
CREATE INDEX idx_orders_driver_id       ON orders (driver_id);
CREATE INDEX idx_orders_status          ON orders (status);
CREATE INDEX idx_orders_payment_status  ON orders (payment_status);
CREATE INDEX idx_orders_created_at      ON orders (created_at DESC);

-- addresses: fast lookup of a customer's addresses
CREATE INDEX idx_addresses_user_id      ON addresses (user_id);

-- order_items: fast joins to orders / products
CREATE INDEX idx_order_items_order_id   ON order_items (order_id);
CREATE INDEX idx_order_items_product_id ON order_items (product_id);

-- products: full-text search over product names
CREATE INDEX idx_products_name_fts      ON products
    USING GIN (to_tsvector('simple', name));

-- driver_locations: GiST spatial index so nearby-driver / distance
-- queries (ST_DWithin / ST_Distance) use the index
CREATE INDEX idx_driver_locations_location ON driver_locations
    USING GIST (location);

-- ============================================================================
-- 6. HELPER FUNCTION (OPTIONAL): nearest active drivers
--    Used by admin auto-assign: returns drivers within radius ordered by distance
-- ============================================================================
CREATE OR REPLACE FUNCTION find_nearby_drivers(
    ref_lat   DOUBLE PRECISION,
    ref_lng   DOUBLE PRECISION,
    radius_m  DOUBLE PRECISION DEFAULT 10000
)
RETURNS TABLE (
    driver_id  UUID,
    full_name  TEXT,
    distance_m DOUBLE PRECISION
)
LANGUAGE sql
STABLE
AS $$
    SELECT dl.driver_id,
           u.full_name,
           ST_Distance(
               dl.location,
               ST_SetSRID(ST_MakePoint(ref_lng, ref_lat), 4326)::geography
           ) AS distance_m
    FROM driver_locations dl
    JOIN users u ON u.id = dl.driver_id
    WHERE ST_DWithin(
        dl.location,
        ST_SetSRID(ST_MakePoint(ref_lng, ref_lat), 4326)::geography,
        radius_m
    )
    ORDER BY distance_m;
$$;

-- ----------------------------------------------------------------------------
-- audit_logs: immutable change history (who, when, what, old_value, new_value)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.audit_logs (
    id           BIGSERIAL PRIMARY KEY,
    who          TEXT,
    action_time  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    what         TEXT NOT NULL,
    old_value    JSONB,
    new_value    JSONB
);

CREATE INDEX IF NOT EXISTS idx_audit_logs_action_time ON public.audit_logs (action_time DESC);
CREATE INDEX IF NOT EXISTS idx_audit_logs_who ON public.audit_logs (who);
