-- ============================================================================
-- Next-Gen Ecosystem Migration: IoT, Wallets, Franchise & B2B
-- ============================================================================

-- 1. ENUM & ROLE UPDATES
ALTER TYPE public.user_role ADD VALUE IF NOT EXISTS 'FRANCHISE_DEALER';

-- 2. SMART IoT HARDWARE
CREATE TABLE IF NOT EXISTS public.iot_devices (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    address_id        UUID NOT NULL REFERENCES public.addresses(id) ON DELETE CASCADE,
    device_token      VARCHAR(100) UNIQUE NOT NULL,
    current_level     INTEGER DEFAULT 100 CHECK (current_level >= 0 AND current_level <= 100),
    low_level_threshold INTEGER DEFAULT 20,
    last_ping         TIMESTAMPTZ DEFAULT NOW(),
    is_active         BOOLEAN DEFAULT TRUE
);

-- 3. DIGITAL WALLET ENGINE
CREATE TABLE IF NOT EXISTS public.wallets (
    user_id           UUID PRIMARY KEY REFERENCES public.users(id) ON DELETE CASCADE,
    balance           NUMERIC(15, 2) DEFAULT 0 CHECK (balance >= 0),
    currency          VARCHAR(3) DEFAULT 'MMK',
    updated_at        TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.wallet_transactions (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    wallet_id         UUID NOT NULL REFERENCES public.wallets(user_id),
    amount            NUMERIC(15, 2) NOT NULL,
    type              VARCHAR(20) NOT NULL, -- 'TOPUP', 'PAYMENT', 'REFUND'
    order_id          UUID REFERENCES public.orders(id),
    status            VARCHAR(20) DEFAULT 'COMPLETED',
    created_at        TIMESTAMPTZ DEFAULT NOW()
);

-- 4. FRANCHISE & B2B NETWORK
CREATE TABLE IF NOT EXISTS public.franchises (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id          UUID NOT NULL REFERENCES public.users(id),
    business_name     VARCHAR(255) NOT NULL,
    region            TEXT NOT NULL,
    commission_rate   NUMERIC(5, 2) DEFAULT 10.00, -- 10% commission
    royalty_fee_rate  NUMERIC(5, 2) DEFAULT 5.00,   -- 5% bottling fee
    is_verified       BOOLEAN DEFAULT FALSE,
    created_at        TIMESTAMPTZ DEFAULT NOW()
);

-- 5. AUTOMATED COMMISSIONS & ROYALTY
CREATE OR REPLACE FUNCTION public.calculate_franchise_payout()
RETURNS TRIGGER AS $$
DECLARE
    v_franchise_id UUID;
    v_comm_rate NUMERIC;
BEGIN
    -- Check if order belongs to a franchise-assigned zone/branch
    -- For simplicity, assume orders at specific branches are franchise-owned
    SELECT id, commission_rate INTO v_franchise_id, v_comm_rate
    FROM public.franchises
    WHERE id = (SELECT franchise_id FROM public.branches WHERE id = NEW.branch_id);

    IF v_franchise_id IS NOT NULL AND NEW.status = 'DELIVERED' THEN
        -- Record commission logic here
        RAISE NOTICE 'Calculating commission for franchise %', v_franchise_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 6. RLS POLICIES
ALTER TABLE public.iot_devices ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.wallets ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.wallet_transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.franchises ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can see their own IoT devices." ON public.iot_devices FOR SELECT USING (address_id IN (SELECT id FROM public.addresses WHERE user_id = auth.uid()));
CREATE POLICY "Users can see their own wallet." ON public.wallets FOR SELECT USING (user_id = auth.uid());
CREATE POLICY "Dealers can view their own franchise data." ON public.franchises FOR SELECT USING (owner_id = auth.uid());
