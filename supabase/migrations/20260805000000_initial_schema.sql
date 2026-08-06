-- ============================================================================
-- Initial Schema Migration
-- ============================================================================

-- EXTENSIONS
CREATE EXTENSION IF NOT EXISTS postgis;

-- ENUMS
CREATE TYPE user_role AS ENUM ('CUSTOMER', 'DRIVER', 'ADMIN');
CREATE TYPE order_status AS ENUM ('PENDING', 'CONFIRMED', 'ASSIGNED', 'IN_TRANSIT', 'DELIVERED', 'CANCELLED');
CREATE TYPE payment_status AS ENUM ('PENDING', 'PAID', 'FAILED');
CREATE TYPE payment_method AS ENUM ('COD', 'KPAY', 'WAVE_PAY', 'OTHER');

-- TABLES
CREATE TABLE public.users (
    id           UUID PRIMARY KEY REFERENCES auth.users ON DELETE CASCADE,
    phone_number VARCHAR(20)  NOT NULL UNIQUE,
    full_name    VARCHAR(255) NOT NULL,
    role         user_role    NOT NULL DEFAULT 'CUSTOMER',
    created_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE TABLE public.addresses (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id      UUID             NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    address_line TEXT             NOT NULL,
    township     VARCHAR(100),
    latitude     DECIMAL(10, 8),
    longitude    DECIMAL(11, 8),
    location     GEOGRAPHY(POINT, 4326) GENERATED ALWAYS AS (
                     ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)::geography
                 ) STORED,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE public.products (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name           VARCHAR(255) NOT NULL,
    description    TEXT,
    price          NUMERIC(10, 2) NOT NULL CHECK (price >= 0),
    deposit_fee    NUMERIC(10, 2) NOT NULL DEFAULT 0 CHECK (deposit_fee >= 0),
    stock_quantity INTEGER       NOT NULL DEFAULT 0 CHECK (stock_quantity >= 0),
    created_at     TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

CREATE TABLE public.orders (
    id                     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id            UUID NOT NULL REFERENCES public.users(id),
    driver_id              UUID REFERENCES public.users(id) ON DELETE SET NULL,
    address_id             UUID NOT NULL REFERENCES public.addresses(id),
    status                 order_status   NOT NULL DEFAULT 'PENDING',
    total_amount           NUMERIC(10, 2) NOT NULL DEFAULT 0 CHECK (total_amount >= 0),
    payment_status         payment_status NOT NULL DEFAULT 'PENDING',
    payment_method         payment_method NOT NULL DEFAULT 'COD',
    empty_bottles_returned INTEGER        NOT NULL DEFAULT 0 CHECK (empty_bottles_returned >= 0),
    created_at             TIMESTAMPTZ    NOT NULL DEFAULT NOW(),
    updated_at             TIMESTAMPTZ    NOT NULL DEFAULT NOW()
);

CREATE TABLE public.order_items (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id   UUID NOT NULL REFERENCES public.orders(id) ON DELETE CASCADE,
    product_id UUID NOT NULL REFERENCES public.products(id),
    quantity   INTEGER       NOT NULL CHECK (quantity > 0),
    unit_price NUMERIC(10, 2) NOT NULL CHECK (unit_price >= 0)
);

CREATE TABLE public.driver_locations (
    driver_id  UUID PRIMARY KEY REFERENCES public.users(id) ON DELETE CASCADE,
    location   GEOGRAPHY(POINT, 4326) NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE public.user_bottle_balances (
    user_id            UUID PRIMARY KEY REFERENCES public.users(id) ON DELETE CASCADE,
    empty_bottles_held INTEGER     NOT NULL DEFAULT 0 CHECK (empty_bottles_held >= 0),
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- FUNCTIONS & TRIGGERS

-- Updated at maintenance
CREATE OR REPLACE FUNCTION handle_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_orders_updated_at BEFORE UPDATE ON public.orders FOR EACH ROW EXECUTE FUNCTION handle_updated_at();
CREATE TRIGGER trg_driver_locations_updated_at BEFORE UPDATE ON public.driver_locations FOR EACH ROW EXECUTE FUNCTION handle_updated_at();
CREATE TRIGGER trg_user_bottle_balances_updated_at BEFORE UPDATE ON public.user_bottle_balances FOR EACH ROW EXECUTE FUNCTION handle_updated_at();

-- Stock management on delivery
CREATE OR REPLACE FUNCTION deduct_stock_on_delivery()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status = 'DELIVERED' AND OLD.status <> 'DELIVERED' THEN
        IF EXISTS (
            SELECT 1 FROM order_items oi JOIN products p ON p.id = oi.product_id
            WHERE oi.order_id = NEW.id AND p.stock_quantity < oi.quantity
        ) THEN
            RAISE EXCEPTION 'Insufficient stock for order %', NEW.id;
        END IF;

        UPDATE products p SET stock_quantity = p.stock_quantity - oi.quantity
        FROM order_items oi WHERE oi.product_id = p.id AND oi.order_id = NEW.id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_stock_delivery AFTER UPDATE OF status ON public.orders FOR EACH ROW EXECUTE FUNCTION deduct_stock_on_delivery();

-- Auth sync: Create public.users profile on signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.users (id, phone_number, full_name, role)
    VALUES (NEW.id, NEW.phone, NEW.raw_user_meta_data->>'full_name', 'CUSTOMER');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- RLS POLICIES
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.addresses ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.products ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.order_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.driver_locations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_bottle_balances ENABLE ROW LEVEL SECURITY;

-- Simple RLS Example (expanding in production)
CREATE POLICY "Public profiles are viewable by everyone." ON public.users FOR SELECT USING (true);
CREATE POLICY "Users can update own profile." ON public.users FOR UPDATE USING (auth.uid() = id);
