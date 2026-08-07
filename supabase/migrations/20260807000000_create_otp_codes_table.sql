-- OTP storage table for cross-instance verification (serverless-safe)
create table if not exists public.otp_codes (
    phone_number text primary key,
    otp_code text not null,
    full_name text,
    expires_at timestamptz not null,
    created_at timestamptz not null default now()
);

create index if not exists idx_otp_codes_expires_at on public.otp_codes(expires_at);

-- Cleanup expired OTPs via row level security or periodic cron; for now rely on expiry check in-app.
alter table public.otp_codes enable row level security;

-- Service role bypasses RLS; we do not add user-facing policies here.
