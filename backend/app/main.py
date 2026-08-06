import logging
import time
from typing import Any, Callable

import sentry_sdk
from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.v1.router import api_router
from app.core.config import settings
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
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Requested-With"],
)

# Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next: Callable):
    response = await call_next(request)
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

    # Adjusted CSP to allow Swagger UI assets
    csp = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "img-src 'self' data: https://fastapi.tiangolo.com; "
    )
    response.headers["Content-Security-Policy"] = csp
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
async def health_check() -> dict:
    health = {"status": "ok", "timestamp": time.time(), "services": {}}

    # Check Supabase Connection
    try:
        db = get_supabase_client()
        # Simple query to check connectivity
        db.table("users").select("id", count="exact").limit(1).execute()
        health["services"]["supabase"] = "connected"
    except Exception as e:
        logger.error("Healthcheck: Supabase unreachable: %s", str(e))
        health["services"]["supabase"] = "unreachable"
        health["status"] = "degraded"

    return health
