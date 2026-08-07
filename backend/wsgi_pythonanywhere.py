"""
PythonAnywhere WSGI entrypoint (free tier, single web app).

Serves BOTH the FastAPI backend (mounted under /api/*) and the built React
dashboard (SPA with index.html fallback) on one domain, so auth cookies and
CORS just work (same origin).

SETUP (PythonAnywhere web tab):
  1. Web -> New web app -> Manual configuration -> Python 3.11 (or 3.12).
  2. Bash console -> create & use a virtualenv, then:
       pip install -r requirements.txt a2wsgi
  3. Upload this repo so that on the server you have:
       /home/<user>/cds/backend/...        (this file lives in backend/)
       /home/<user>/cds/web-dashboard/dist  (built frontend)
  4. Web tab -> Code -> WSGI configuration file -> set to:
       /home/<user>/cds/backend/wsgi_pythonanywhere.py
  5. Fill the SECRETS below, then hit Reload.

TEST:
  https://<user>.pythonanywhere.com             -> login page
  https://<user>.pythonanywhere.com/healthz     -> backend health
"""

import mimetypes
import os
import sys

# ---------------------------------------------------------------------------
# CONFIG - fill in your real values
# ---------------------------------------------------------------------------
PYTHONANYWHERE_USERNAME = "YOUR-USERNAME"   # your free-tier subdomain

SUPABASE_URL = "https://YOUR-PROJECT-REF.supabase.co"
SUPABASE_KEY = "YOUR-SERVICE-ROLE-KEY"      # server-side only, never expose
SUPABASE_JWT_SECRET = "YOUR-SUPABASE-JWT-SECRET"

# ---------------------------------------------------------------------------
# Paths (usually correct when this file sits in backend/)
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")

for candidate in (
    os.environ.get("STATIC_DIR"),
    os.path.join(BASE_DIR, "web-dashboard", "dist"),
    os.path.join(BASE_DIR, "dist"),
):
    if candidate and os.path.isdir(candidate):
        DIST_DIR = candidate
        break
else:  # pragma: no cover
    DIST_DIR = os.path.join(BASE_DIR, "dist")

# ---------------------------------------------------------------------------
# Environment (must be set BEFORE importing app.main -> app.core.config)
# ---------------------------------------------------------------------------
os.environ.setdefault("DEBUG", "False")
os.environ.setdefault("SUPABASE_URL", SUPABASE_URL)
os.environ.setdefault("SUPABASE_KEY", SUPABASE_KEY)
os.environ.setdefault("SUPABASE_JWT_SECRET", SUPABASE_JWT_SECRET)
os.environ.setdefault(
    "CORS_ORIGINS_JSON",
    '["https://%s.pythonanywhere.com"]' % PYTHONANYWHERE_USERNAME,
)
os.environ.setdefault("SENTRY_DSN", "")
os.environ.setdefault("REDIS_URL", "")          # rate limiter -> in-memory
os.environ.setdefault("DATABASE_URL", "")       # runtime uses the Supabase REST client
os.environ.setdefault("DIRECT_URL", "")

sys.path.insert(0, BACKEND_DIR)

# ---------------------------------------------------------------------------
# WSGI dispatch
# ---------------------------------------------------------------------------
from a2wsgi import ASGIMiddleware  # noqa: E402
from app.main import app           # noqa: E402

api_wsgi = ASGIMiddleware(app)


def _response(environ, start_response, status, content_type, body: bytes):
    start_response(status, [("Content-Type", content_type)])
    return [body]


def _serve_file(environ, start_response, rel_path: str):
    full = os.path.normpath(os.path.join(DIST_DIR, rel_path.lstrip("/")))
    if not full.startswith(DIST_DIR) or not os.path.isfile(full):
        return None
    ctype, _ = mimetypes.guess_type(full)
    with open(full, "rb") as fh:
        body = fh.read()
    return _response(
        environ, start_response, "200 OK", ctype or "application/octet-stream", body
    )


def _serve_index(environ, start_response):
    with open(os.path.join(DIST_DIR, "index.html"), "rb") as fh:
        body = fh.read()
    return _response(environ, start_response, "200 OK", "text/html; charset=utf-8", body)


def application(environ, start_response):
    path = environ.get("PATH_INFO", "/") or "/"

    # Backend routes
    if (
        path.startswith("/api/")
        or path == "/api"
        or path in ("/docs", "/redoc", "/openapi.json", "/healthz")
    ):
        return api_wsgi(environ, start_response)

    # Static assets (has a file extension) -> serve from dist, else SPA fallback
    last_segment = path.rstrip("/").split("/")[-1]
    if "." in last_segment:
        if ".." in path:  # basic traversal guard
            return _response(environ, start_response, "403 Forbidden", "text/plain", b"forbidden")
        result = _serve_file(environ, start_response, path)
        if result is not None:
            return result

    # SPA deep-link fallback
    return _serve_index(environ, start_response)
