# Clean Delivery System - Production Deployment Guide

## 1. Supabase Setup
### Local Development
1. Install Supabase CLI.
2. Run `supabase init`.
3. Start local emulator: `supabase start`.
4. Apply migrations: `supabase db reset`.

### Cloud Deployment
1. Link project: `supabase link --project-ref <your-project-id>`.
2. Push migrations: `supabase db push`.
3. Deploy Edge Functions: `supabase functions deploy notify-order-status`.

## 2. Backend (FastAPI) Setup
### Environment Variables (.env)
Set the following variables in your production environment:
- `SUPABASE_URL`
- `SUPABASE_KEY` (service_role for backend)
- `SUPABASE_JWT_SECRET`
- `SENTRY_DSN`
- `WEBHOOK_SECRET` (for verifying Supabase calls)

### Deployment
Use the provided `Dockerfile` and `docker-compose.yml` for containerized deployment.

## 3. Production Security Checklist
- [ ] **RLS Policies**: Ensure `public.users` can only be updated by the owner.
- [ ] **Service Role Key**: Never expose the `service_role` key in the frontend or mobile app.
- [ ] **Database Backups**: Enable Supabase point-in-time recovery for production.
- [ ] **SSL**: Ensure all communication is over HTTPS.
- [ ] **Rate Limiting**: Monitor `slowapi` logs for potential abuse.

## 4. CI/CD
The project includes a GitHub Actions workflow in `.github/workflows/supabase_deploy.yml` that automates testing and deployment to Supabase Cloud.
