import os
import sys
import traceback
from pathlib import Path

_API_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _API_DIR.parent
_BACKEND_DIR = _PROJECT_ROOT / "backend"
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

os.environ.setdefault("VERCEL", "1")
os.environ.setdefault("PYTHONUNBUFFERED", "1")

# Public ASGI entrypoint for Vercel's Python runtime.
#
# Vercel only treats a file under `api/` as a Vercel Function when it defines a
# top-level `app` (ASGI/WSGI application) or a `handler` class that subclasses
# `BaseHTTPRequestHandler`. The legacy `def handler(event, context)` (Mangum)
# style is no longer detected, which made the `functions` pattern in
# vercel.json fail to match. `app` therefore stays a top-level name here.
app = None

try:
    from app.main import app as _backend_app
except Exception as _boot_exc:  # noqa: BLE001 - surfaced by the fallback app
    _backend_app = None
    _boot_error = _boot_exc
else:
    _boot_error = None


class _OriginalPathRecovery:
    """Restore the ORIGINAL request path after Vercel rewrites mangled it.

    vercel.json rewrites every /api/* request to this function at "/api" and
    Vercel forwards the destination path as the event path. The real path the
    client asked for arrives in the "x-vercel-original-url" header, so this
    ASGI middleware swaps it back before FastAPI routing runs.
    """

    def __init__(self, inner_app):
        self.inner_app = inner_app

    async def __call__(self, scope, receive, send):
        if scope.get("type") == "http":
            for key, value in scope.get("headers") or []:
                if key == b"x-vercel-original-url":
                    original = value.decode("latin-1", "ignore").split("?", 1)[0]
                    if original.startswith("/") and original != "/api/index":
                        scope["path"] = original
                    break
        await self.inner_app(scope, receive, send)


if _backend_app is not None:
    app = _backend_app
else:
    # Backend failed to import (e.g. missing env vars at cold start). Serve a
    # minimal diagnostic app so the failure is visible as JSON instead of a
    # platform 500, and so cold-start crashes do not take down the domain.
    import json

    from fastapi import FastAPI
    from fastapi.responses import JSONResponse

    app = FastAPI(title="CleanDeliverySystem (startup fallback)")

    _exc_type_name = type(_boot_error).__name__
    _exc_message = str(_boot_error)
    _tb_text = traceback.format_exc()

    @app.exception_handler(Exception)
    async def _fallback_unhandled(request, exc):  # noqa: ARG001
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": {
                    "code": 500,
                    "message": "Backend failed to start on Vercel",
                    "details": {
                        "type": _exc_type_name,
                        "error": _exc_message,
                        "traceback": _tb_text.splitlines(),
                        "cwd": str(Path.cwd()),
                        "sys_path": sys.path,
                    },
                },
            },
        )

    @app.get("/healthz")
    @app.get("/api/healthz")
    async def _fallback_health():
        return JSONResponse(
            status_code=503,
            content={
                "status": "degraded",
                "services": {"supabase": "unreachable"},
                "error": {
                    "type": _exc_type_name,
                    "message": _exc_message,
                    "traceback": _tb_text.splitlines()[-5:],
                },
            },
        )

app.add_middleware(_OriginalPathRecovery)
application = app
