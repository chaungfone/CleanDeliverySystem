import re
from fastapi import HTTPException
from supabase import Client, create_client

from app.core.config import settings

_client: Client | None = None

_BAD_CHARS_RE = re.compile(r"[\[\](){}\"'<>|`‘’“”\s]")
_SUPABASE_URL_RE = re.compile(r"^https://[a-zA-Z0-9-]+\.supabase\.(co|in|com)(/.*)?$", re.IGNORECASE)


def _sanitize_and_validate_supabase_url(raw: str) -> tuple[str, str | None]:
    if raw is None:
        return "", "SUPABASE_URL is None"
    stripped = raw.strip()
    original_len = len(stripped)
    cleaned = _BAD_CHARS_RE.sub("", stripped)
    if len(cleaned) != original_len:
        return cleaned, (
            f"SUPABASE_URL contained leading/trailing or forbidden characters "
            f"([ ] ( ) quotes whitespace) which were stripped. "
            f"Paste the URL directly from Supabase Settings → API → Project URL."
        )
    if not cleaned.lower().startswith("https://"):
        return cleaned, "SUPABASE_URL must start with 'https://' (not http or missing scheme)."
    if not _SUPABASE_URL_RE.match(cleaned.rstrip("/") + "/"):
        m = re.match(r"^https://([^/]+)", cleaned.lower())
        host = m.group(1) if m else cleaned
        if "supabase" not in host:
            return cleaned, (
                f"SUPABASE_URL host '{host}' does not look like a Supabase project URL "
                f"(expected format: https://<project-ref>.supabase.co). "
                f"Copy from Supabase → Project Settings → API → Project URL."
            )
    if cleaned.endswith("/"):
        cleaned = cleaned[:-1]
    return cleaned, None


def _sanitize_supabase_key(raw: str | None) -> str:
    if raw is None:
        return ""
    return _BAD_CHARS_RE.sub("", raw.strip())


def get_supabase_client() -> Client:
    global _client
    if _client is None:
        raw_url = settings.SUPABASE_URL
        raw_key = settings.SUPABASE_KEY
        if not raw_url or not raw_key:
            raise HTTPException(
                status_code=500,
                detail=(
                    "Server is not configured: missing SUPABASE_URL or SUPABASE_KEY "
                    "in the runtime environment variables. Please set them in "
                    "Vercel Project Settings -> Environment Variables and redeploy."
                ),
            )
        cleaned_url, url_warning = _sanitize_and_validate_supabase_url(raw_url)
        cleaned_key = _sanitize_supabase_key(raw_key)
        if not cleaned_url:
            raise HTTPException(
                status_code=500,
                detail="SUPABASE_URL is empty after sanitizing whitespace/forbidden chars. Copy a fresh value from Supabase Project Settings → API → Project URL.",
            )
        if not cleaned_key:
            raise HTTPException(
                status_code=500,
                detail="SUPABASE_KEY is empty after sanitizing whitespace/forbidden chars. Copy a fresh service_role key from Supabase Project Settings → API → service_role secret.",
            )
        if url_warning:
            import logging
            logging.getLogger(__name__).warning(
                "SUPABASE_URL sanitization warning: %s (original len=%s cleaned len=%s)",
                url_warning, len(raw_url or ""), len(cleaned_url),
            )
            settings.SUPABASE_URL = cleaned_url
            settings.SUPABASE_KEY = cleaned_key
        _client = create_client(cleaned_url, cleaned_key)
    return _client


def get_db() -> Client:
    return get_supabase_client()
