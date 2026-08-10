import logging
import os
import sys
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

# Ensure backend package imports work in serverless environments (e.g. Vercel)
# where the working directory may be backend/app/ rather than backend/.
_backend_dir = Path(__file__).resolve().parent.parent
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

import sentry_sdk
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.v1.router import api_router
from app.core.config import get_settings, settings
from app.core.database import get_supabase_client
from app.core.rate_limit import limiter

# Logging Configuration
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

# Sentry Initialization
if not settings.DEBUG:
    sentry_sdk.init(
        dsn=getattr(settings, "SENTRY_DSN", ""),
        traces_sample_rate=1.0,
        profiles_sample_rate=1.0,
    )

# Rate Limiter (shared instance defined in app.core.rate_limit)
app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url="/docs",
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS Middleware - Production Tightened
# On Vercel the frontend and API share the same apex domain BUT requests can arrive
# with a different Origin header (mobile capacitor://, staging preview, etc.) and the
# browser enforces that cookies set with `credentials: 'include'` require explicit
# Access-Control-Allow-Credentials + a non-wildcard Origin. Therefore we MUST set
# the CORS middleware even on Vercel; it does not hurt "same-origin" requests.
#
# FastAPI's CORSMiddleware rejects the combination allow_origins=["*"] + allow_credentials=True
# (it would not reflect Origin). Instead, when the configured list is "*" (dev / Vercel
# same-origin case) we install a lightweight dynamic reflection below that only echoes
# a known-present Origin header and always sends Allow-Credentials=true.
from urllib.parse import urlparse

cors_origins = settings.CORS_ORIGINS
_origin_allow_all = not cors_origins or cors_origins == ["*"]
if not _origin_allow_all:
    # Explicit safelist configured by operator — use the framework middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Requested-With", "X-Client-Type"],
        expose_headers=["X-CSP-Nonce"],
    )
else:
    # Dynamic reflection: only apply CORS response headers when a request has an
    # Origin header (skip same-origin / no-origin scenarios). The reflected Origin
    # is validated to be a syntactically valid HTTP(S)/capacitor URL.
    _ALLOWED_METHODS_CSV = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
    _ALLOWED_HEADERS_CSV = "Authorization, Content-Type, X-Requested-With, X-Client-Type"

    def _is_safe_origin(origin: str) -> bool:
        if not origin or not isinstance(origin, str):
            return False
        if origin in ("capacitor://localhost", "http://localhost", "http://localhost:3000", "http://localhost:4173", "http://127.0.0.1:3000", "http://127.0.0.1:4173"):
            return True
        try:
            parsed = urlparse(origin)
            return parsed.scheme in ("http", "https", "capacitor") and bool(parsed.netloc)
        except Exception:
            return False

    @app.middleware("http")
    async def _reflective_cors(request: Request, call_next: Callable):
        origin = request.headers.get("origin")
        is_preflight = request.method == "OPTIONS" and origin is not None
        if is_preflight:
            # Short-circuit: respond to preflight directly so that later middlewares
            # (e.g. auth guards) do not reject OPTIONS with 401/405.
            if _is_safe_origin(origin):
                from fastapi.responses import Response
                return Response(
                    status_code=204,
                    headers={
                        "Access-Control-Allow-Origin": origin,
                        "Access-Control-Allow-Credentials": "true",
                        "Access-Control-Allow-Methods": _ALLOWED_METHODS_CSV,
                        "Access-Control-Allow-Headers": _ALLOWED_HEADERS_CSV,
                        "Access-Control-Expose-Headers": "X-CSP-Nonce",
                        "Access-Control-Max-Age": "7200",
                        "Vary": "Origin",
                    },
                    media_type="text/plain",
                )
        response = await call_next(request)
        if origin and _is_safe_origin(origin):
            existing_ao = response.headers.get("Access-Control-Allow-Origin")
            if not existing_ao or existing_ao == "*":
                response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Expose-Headers"] = "X-CSP-Nonce"
            vary = response.headers.get("Vary")
            if vary:
                if "Origin" not in vary:
                    response.headers["Vary"] = f"{vary}, Origin"
            else:
                response.headers["Vary"] = "Origin"
        return response

# Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next: Callable):
    response = await call_next(request)
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

    # Generate a per-request CSP nonce to avoid using 'unsafe-inline'.
    # The nonce is returned in the CSP header and also exposed via X-CSP-Nonce so
    # any server-rendered templates or instrumented UIs (Swagger) can inject it
    # into their inline <script nonce="..."> and <style nonce="..."> tags.
    import secrets

    nonce = secrets.token_urlsafe(16)

    # Tightened CSP: no 'unsafe-inline'. Use nonce for inline scripts/styles and
    # continue to allow trusted CDNs used by the docs UI.
    csp = (
        "default-src 'self'; "
        f"script-src 'self' 'nonce-{nonce}' https://cdn.jsdelivr.net; "
        f"style-src 'self' 'nonce-{nonce}' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
        "font-src 'self' data: https://fonts.gstatic.com; "
        "img-src 'self' data: https://fastapi.tiangolo.com; "
    )
    response.headers["Content-Security-Policy"] = csp
    # Expose the nonce for use by instrumented front-ends (e.g., test harnesses or templates)
    response.headers["X-CSP-Nonce"] = nonce
    return response

# Custom Request Logging Middleware
@app.middleware("http")
async def log_requests(request: Request, call_next: Callable):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    logger.info(
        "Method: %s Path: %s Status: %s Duration: %.4fs",
        request.method, request.url.path, response.status_code, duration
    )
    return response

app.include_router(api_router, prefix=settings.API_V1_PREFIX)


def _registered_route_paths() -> list[str]:
    paths: set[str] = set()
    for route in getattr(app, "routes", []):
        path = getattr(route, "path", None)
        if isinstance(path, str):
            paths.add(path)
    return sorted(paths)


# Standardized Error Response Helper
def standardized_error(code: int, message: str, details: Any = None) -> JSONResponse:
    return JSONResponse(
        status_code=code,
        content={
            "success": False,
            "error": {
                "code": code,
                "message": message,
                "details": details
            }
        },
    )


# Exception Handlers
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    if exc.status_code == 404:
        debug = get_settings().DEBUG or os.getenv("VERCEL") == "1"
        detail: Any = str(exc.detail)
        if debug:
            detail = {
                "reason": str(exc.detail),
                "requested_path": request.url.path,
                "requested_method": request.method,
                "api_prefix_registered": settings.API_V1_PREFIX,
                "known_routes_sample": _registered_route_paths()[:50],
                "env_hint": (
                    "If you see this JSON body, the request reached FastAPI. "
                    "If you see a plain 'Not found' HTML page instead, the request "
                    "never reached the Python function - check api/[...path].py "
                    "discovery and Vercel function logs."
                ),
            }
        return standardized_error(404, "Not found", detail)
    return standardized_error(exc.status_code, str(exc.detail))


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    details = [
        {"loc": list(error.get("loc", [])), "msg": error.get("msg"), "type": error.get("type")}
        for error in exc.errors()
    ]
    return standardized_error(422, "Request validation failed", details)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error on %s %s: %s", request.method, request.url.path, exc)
    return standardized_error(500, "Internal server error")


# Advanced Health Check
@app.get("/healthz", tags=["health"])
@app.get("/api/healthz", tags=["health"])
async def health_check() -> dict:
    health = {"status": "ok", "timestamp": time.time(), "services": {}, "env": {}, "configuration": {}}

    # Environment Configuration diagnostics (never expose actual secrets; only report presence/status)
    s = get_settings()
    env_status: dict = {}
    def _stat(name: str, value: str | None) -> dict:
        if not value:
            return {"present": False, "placeholder": False}
        is_ph = s._is_placeholder(value)
        truncated = "" if is_ph else f"{value[:4]}***{value[-4:]}" if len(value or "") >= 10 else "***"
        return {"present": True, "placeholder": is_ph, "preview": truncated}
    env_status["SUPABASE_URL"] = _stat("SUPABASE_URL", s.SUPABASE_URL)
    env_status["SUPABASE_KEY"] = _stat("SUPABASE_KEY", s.SUPABASE_KEY)
    env_status["SUPABASE_JWT_SECRET"] = _stat("SUPABASE_JWT_SECRET", s.SUPABASE_JWT_SECRET)
    env_status["DATABASE_URL"] = _stat("DATABASE_URL", s.DATABASE_URL)
    env_status["SENTRY_DSN"] = _stat("SENTRY_DSN", s.SENTRY_DSN)
    env_status["REDIS_URL"] = _stat("REDIS_URL", s.REDIS_URL)

    # Supabase URL sanitization check — catches [https://xxx.supabase.co) style copy/paste errors
    url_sanity: dict = {}
    try:
        from app.core.database import _sanitize_and_validate_supabase_url
        if s.SUPABASE_URL:
            cleaned_url, warning = _sanitize_and_validate_supabase_url(s.SUPABASE_URL)
            url_sanity["valid_format"] = warning is None
            url_sanity["cleaned_preview"] = (
                (f"{cleaned_url[:4]}***{cleaned_url[-6:]}") if len(cleaned_url) >= 14 else "***"
            )
            url_sanity["original_length"] = len(s.SUPABASE_URL)
            url_sanity["cleaned_length"] = len(cleaned_url)
            stripped = s.SUPABASE_URL.strip()
            if stripped[:1] in "[({<" or stripped[-1:] in "])}>":
                url_sanity["surrounding_chars_detected"] = True
            if warning:
                url_sanity["warning"] = warning
                if health["status"] == "ok":
                    health["status"] = "degraded"
        else:
            url_sanity["valid_format"] = False
            url_sanity["warning"] = "SUPABASE_URL not set"
    except Exception as _ue:
        url_sanity["error"] = f"sanity check error: {_ue}"
    health["url_sanity"] = url_sanity

    required_ok = (
        s.SUPABASE_URL and not s._is_placeholder(s.SUPABASE_URL) and
        s.SUPABASE_KEY and not s._is_placeholder(s.SUPABASE_KEY) and
        s.SUPABASE_JWT_SECRET and not s._is_placeholder(s.SUPABASE_JWT_SECRET)
    )
    env_status["ALL_REQUIRED_PRESENT"] = bool(required_ok)
    health["env"] = env_status

    health["configuration"]["environment"] = s.ENVIRONMENT
    health["configuration"]["debug"] = s.DEBUG
    health["configuration"]["api_prefix"] = s.API_V1_PREFIX
    health["configuration"]["cors_origins_sample"] = s.CORS_ORIGINS[:10]
    try:
        s.validate_secrets()
        health["configuration"]["validate_secrets_ok"] = True
    except Exception as ve:
        health["configuration"]["validate_secrets_ok"] = False
        health["configuration"]["validate_secrets_error"] = str(ve)
        if health["status"] == "ok":
            health["status"] = "degraded"

    # Check Supabase Connection
    try:
        if not required_ok:
            raise RuntimeError("SUPABASE_URL/SUPABASE_KEY/SUPABASE_JWT_SECRET required secrets not configured (see env.* in response). Login/auth endpoints will fail until these are set in the hosting platform environment variables (Vercel Dashboard → Settings → Environment Variables).")
        db = get_supabase_client()
        # Simple query to check connectivity
        db.table("users").select("id", count="exact").limit(1).execute()
        health["services"]["supabase"] = "connected"
    except Exception as e:  # noqa: BLE001 - health endpoint must never 500; degrade instead
        logger.error("Healthcheck: Supabase unreachable: %s", str(e))
        health["services"]["supabase"] = "unreachable"
        health["services"]["supabase_error"] = str(e)
        if health["status"] == "ok":
            health["status"] = "degraded"

    # Surface route listing for 404 debugging.
    health["routes"] = _registered_route_paths()
    health["api_v1_prefix"] = settings.API_V1_PREFIX
    return health
