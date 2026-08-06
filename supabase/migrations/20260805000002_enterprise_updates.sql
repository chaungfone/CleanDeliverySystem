-- ============================================================================
-- Enterprise Scaling Migration: Multi-Branch, Inventory, Loyalty, and Subscriptions
-- ============================================================================

-- 1. ENUM & ROLE UPDATES
ALTER TYPE public.user_role ADD VALUE IF NOT EXISTS 'BRANCH_MANAGER';

-- 2. MULTI-BRANCH INFRASTRUCTURE
CREATE TABLE IF NOT EXISTS public.branches (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name              VARCHAR(255) NOT NULL,
    address           TEXT NOT NULL,
    location          GEOGRAPHY(POINT, 4326) NOT NULL,
    coverage_zone     GEOGRAPHY(POLYGON, 4326),
    is_active         BOOLEAN DEFAULT TRUE,
    created_at        TIMESTAMPTZ DEFAULT NOW()
);

-- Add branch context to users (Managers/Drivers) and orders
ALTER TABLE public.users ADD COLUMN IF NOT EXISTS branch_id UUID REFERENCES public.branches(id);
ALTER TABLE public.orders ADD COLUMN IF NOT EXISTS branch_id UUID REFERENCES public.branches(id);

-- 3. MANUFACTURING & INVENTORY CONTROL
CREATE TABLE IF NOT EXISTS public.inventory (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    branch_id         UUID NOT NULL REFERENCES public.branches(id) ON DELETE CASCADE,
    full_bottles      INTEGER DEFAULT 0 CHECK (full_bottles >= 0),
    empty_bottles     INTEGER DEFAULT 0 CHECK (empty_bottles >= 0),
    caps_count        INTEGER DEFAULT 0 CHECK (caps_count >= 0),
    labels_count      INTEGER DEFAULT 0 CHECK (labels_count >= 0),
    water_liters      NUMERIC(12, 2) DEFAULT 0 CHECK (water_liters >= 0),
    updated_at        TIMESTAMPTZ DEFAULT NOW()
);

-- Trigger to update inventory on Order Delivered
CREATE OR REPLACE FUNCTION public.sync_inventory_on_delivery()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status = 'DELIVERED' AND OLD.status <> 'DELIVERED' THEN
        -- Deduct Full Bottles, caps, and labels based on order items
        -- Assume standard 1 bottle = 1 cap + 1 label for now
        UPDATE public.inventory
        SET full_bottles = full_bottles - (SELECT SUM(quantity) FROM public.order_items WHERE order_id = NEW.id),
            empty_bottles = empty_bottles + NEW.empty_bottles_returned,
            caps_count = caps_count - (SELECT SUM(quantity) FROM public.order_items WHERE order_id = NEW.id),
            labels_count = labels_count - (SELECT SUM(quantity) FROM public.order_items WHERE order_id = NEW.id)
        WHERE branch_id = NEW.branch_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_sync_inventory_on_delivery
AFTER UPDATE OF status ON public.orders
FOR EACH ROW EXECUTE FUNCTION public.sync_inventory_on_delivery();

-- 4. CUSTOMER LOYALTY PROGRAM
CREATE TABLE IF NOT EXISTS public.loyalty_points (
    user_id           UUID PRIMARY KEY REFERENCES public.users(id) ON DELETE CASCADE,
    points_balance    INTEGER DEFAULT 0 CHECK (points_balance >= 0),
    updated_at        TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.coupons (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code              VARCHAR(50) UNIQUE NOT NULL,
    discount_amount   NUMERIC(10, 2) NOT NULL,
    points_required   INTEGER NOT NULL,
    is_active         BOOLEAN DEFAULT TRUE,
    expiry_date       TIMESTAMPTZ
);

-- 5. RECURRING ORDERS (SUBSCRIPTIONS)
CREATE TABLE IF NOT EXISTS public.subscriptions (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id       UUID NOT NULL REFERENCES public.users(id),
    address_id        UUID NOT NULL REFERENCES public.addresses(id),
    interval_days     INTEGER NOT NULL DEFAULT 7, -- e.g., weekly
    next_order_date   DATE NOT NULL,
    is_active         BOOLEAN DEFAULT TRUE,
    created_at        TIMESTAMPTZ DEFAULT NOW()
);

-- RLS POLICIES
ALTER TABLE public.branches ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.inventory ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.loyalty_points ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.coupons ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.subscriptions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Branches are viewable by everyone." ON public.branches FOR SELECT USING (true);
CREATE POLICY "Managers can update their branch inventory." ON public.inventory
    FOR ALL USING (branch_id IN (SELECT branch_id FROM public.users WHERE id = auth.uid()));
