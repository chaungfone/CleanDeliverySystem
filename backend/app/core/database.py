from fastapi import HTTPException
from supabase import Client, create_client

from app.core.config import settings

_client: Client | None = None


def get_supabase_client() -> Client:
    global _client
    if _client is None:
        if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
            raise HTTPException(
                status_code=500,
                detail=(
                    "Server is not configured: missing SUPABASE_URL or SUPABASE_KEY "
                    "in the runtime environment variables. Please set them in "
                    "Vercel Project Settings -> Environment Variables and redeploy."
                ),
            )
        _client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    return _client


def get_db() -> Client:
    return get_supabase_client()
