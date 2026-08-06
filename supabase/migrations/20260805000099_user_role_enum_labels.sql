-- 20260805000099_user_role_enum_labels.sql
-- Extend the public.user_role enum with labels the app and RLS policies use
-- but that are missing on the live project (e.g. 'BRANCH_MANAGER').
-- Idempotent: ADD VALUE IF NOT EXISTS (PostgreSQL 14+).
-- Runs in its OWN migration transaction, before any policy that references
-- these labels (so the new values are safe to use in the next migration).
ALTER TYPE public.user_role ADD VALUE IF NOT EXISTS 'BRANCH_MANAGER';
ALTER TYPE public.user_role ADD VALUE IF NOT EXISTS 'FRANCHISE_DEALER';