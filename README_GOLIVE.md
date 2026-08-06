# Clean Delivery System - Go-Live & Launch Checklist

This document provides a step-by-step guide for deploying the Clean Water Delivery System to a production environment.

## 1. Production Security Checklist

- [ ] **Row Level Security (RLS)**: 
    - Ensure all tables in Supabase have RLS enabled.
    - Verify that `service_role` keys are NOT used in the mobile apps or frontend.
    - Check that users can only modify their own profiles and addresses.
- [ ] **API Security**:
    - Set `DEBUG=False` in FastAPI `.env`.
    - Configure `CORS_ORIGINS` to only allow your production frontend/mobile app domains.
    - Ensure `SENTRY_DSN` is set for real-time crash reporting.
- [ ] **Secrets Management**:
    - Use GitHub Secrets or a specialized vault for all production keys (Supabase JWT Secret, Twilio API Key, etc.).

## 2. Infrastructure Deployment

### Backend (FastAPI)
1. **Containerization**: Build the production image using the provided `Dockerfile`.
2. **Orchestration**: Deploy using `docker-compose.yml` or a Kubernetes manifest.
3. **Domain & SSL**: Setup a production domain with HTTPS (e.g., via Let's Encrypt and Nginx).

### Supabase Cloud
1. **Migrations**: Run `supabase db push` to apply all schema changes to your production project.
2. **Edge Functions**: Deploy functions using `supabase functions deploy notify-order-status`.
3. **Auth**: Configure allowed redirect URLs and SMS provider settings in the Supabase Dashboard.

## 3. Mobile App Release (Play Store / App Store)

1. **Production URLs**: Update `SupabaseModule.kt` and `NetworkModule.kt` with the production API and Supabase URLs.
2. **Signing**: Generate a release keystore and sign the APK/AAB.
3. **ProGuard/R8**: Ensure R8 rules are configured to keep necessary classes for Retrofit and Supabase SDK.
4. **FCM**: Configure the production Firebase project and upload the `google-services.json` for production.

## 4. End-to-End Flow Verification (Manual)

Before announcement, perform the following flow on production devices:
1. Register a new customer via Phone/OTP.
2. Place a real order.
3. Verify that the Admin Dashboard shows the new PENDING order.
4. Log in as a Driver and ACCEPT the order.
5. Verify that the Customer sees the "Driver Assigned" status in real-time.
6. Complete the delivery and verify that the product stock is deducted and revenue is updated.

---

> [!CAUTION]
> **Database Backups**: Always enable automatic daily backups in the Supabase Dashboard before going live with real customer data.
