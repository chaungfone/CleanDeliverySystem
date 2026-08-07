# Deployment Guide: Koyeb (Backend) & Vercel (Frontend)

## Backend — Koyeb

### Prerequisites
- A [Koyeb](https://app.koyeb.com/) account (no VPN required).
- Git repository hosted on GitHub/GitLab.
- Environment variables ready (see `.env.production` in `backend/`).

### Steps
1. Push the repository to GitHub/GitLab.
2. In the [Koyeb Control Panel](https://app.koyeb.com/), create a new **Web Service**.
3. Select your repository and branch.
4. Set the **Build path** to `backend` and use the included `Dockerfile`.
5. Under **Environment Variables**, add all variables from `backend/.env.production`.
6. Set the **Port** to `8000`.
7. Deploy. Koyeb will build the image and expose the service at `https://<app-name>.<koyeb-app-id>.koyeb.app`.

### Health Check
Verify the deployment:
```bash
curl https://<your-koyeb-app>.koyeb.app/healthz
```

Expected response:
```json
{
  "status": "ok",
  "services": { "supabase": "connected" }
}
```

---

## Frontend — Vercel

### Prerequisites
- A [Vercel](https://vercel.com/) account (no VPN required).
- Git repository hosted on GitHub/GitLab.

### Steps
1. In the [Vercel Dashboard](https://vercel.com/new), import the project.
2. Set the **Root Directory** to `web-dashboard`.
3. Add environment variables from `web-dashboard/.env.production` (e.g., `VITE_API_BASE_URL` pointing to the Koyeb backend).
4. Deploy. Vercel will build the React app and serve it.

### SPA Routing
The included `vercel.json` handles client-side routing via rewrites:
```json
{
  "rewrites": [
    { "source": "/(.*)", "dest": "/index.html" }
  ]
}
```

### Verify
Open the deployed Vercel URL and confirm the app loads and can reach the backend API.

---

## Notes
- Both platforms support automatic deployments on every push to the configured branch.
- No VPN or special network configuration is required for either platform.
