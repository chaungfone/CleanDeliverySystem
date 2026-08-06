-- ============================================================================
-- Seed Data for Clean Delivery System
-- ============================================================================

-- Products
INSERT INTO public.products (name, description, price, deposit_fee, stock_quantity)
VALUES
('20L Purified Water', 'Standard 20-liter reusable bottle', 1500.00, 5000.00, 500),
('10L Purified Water', '10-liter reusable bottle', 900.00, 3000.00, 200),
('Dispenser Pump', 'Manual hand pump for 20L bottles', 3500.00, 0.00, 50);

-- Note: Users and Orders should generally be created via Auth/API,
-- but we can add test data here for local dev if needed.
