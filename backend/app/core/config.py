import json
import logging
import os
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

_PLACEHOLDER_MARKERS = (
    "your-",
    "your_",
    "yourproject",
    "changeme",
    "replaceme",
    "placeholder",
    "dummy",
    "xxxx",
)

_ENVIRONMENT_VALUES = ("development", "staging", "production", "test")
EnvironmentName = Literal["development", "staging", "production", "test"]


def _detect_environment() -> EnvironmentName:
    """
    Determine which environment we're running in.

    Resolution order (first match wins):
      1. APP_ENVIRONMENT / ENVIRONMENT / ENV variables (explicit operator override)
      2. Vercel's VERCEL_ENV (system variable for Preview/Production/Development)
      3. Fallback: 'production' for safety (never accidentally ship DEBUG=True)
    """
    for key in ("APP_ENVIRONMENT", "ENVIRONMENT", "ENV"):
        raw = os.getenv(key)
        if raw:
            lowered = raw.strip().lower()
            if lowered in _ENVIRONMENT_VALUES:
                return lowered  # type: ignore[return-value]
    vercel_env = (os.getenv("VERCEL_ENV") or "").strip().lower()
    if vercel_env == "preview":
        return "staging"
    if vercel_env == "production":
        return "production"
    if vercel_env == "development":
        return "development"
    return "production"


def _env_files() -> list[str | Path]:
    """
    Ordered list of dotenv files to load (later entries override earlier ones).
    Loads: .env -> .env.{environment} -> .env.{environment}.local
    Files that don't exist are silently skipped by pydantic-settings.
    """
    env = _detect_environment()
    project_root = Path(__file__).resolve().parent.parent.parent.parent
    candidates: list[str | Path] = []
    for name in (".env", f".env.{env}", f".env.{env}.local"):
        candidates.append(project_root / name)
    # pydantic-settings 2.x supports a list of env files; non-existent paths are OK.
    return candidates


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_env_files(),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    ENVIRONMENT: EnvironmentName = Field(default_factory=_detect_environment)

    PROJECT_NAME: str = "Clean Water Delivery Management System"
    API_V1_PREFIX: str = "/api/v1"

    @property
    def DEBUG(self) -> bool:  # type: ignore[override]
        # Always DEBUG for local dev; staging/production opt-in via explicit DEBUG=1.
        if self.ENVIRONMENT == "development":
            return True
        return os.getenv("DEBUG", "").strip() in {"1", "true", "True", "yes"}
    # Production MUST override via CORS_ORIGINS_JSON; only defaults to ["*"] in dev/DEBUG.
    CORS_ORIGINS: list[str] = Field(
        default_factory=lambda: json.loads(os.getenv("CORS_ORIGINS_JSON", '["*"]')),
        validation_alias="CORS_ORIGINS_JSON",
    )

    # Graceful defaults: allow the FastAPI app to import/start even when secrets
    # aren't present in the runtime environment (e.g. initial Vercel deploy
    # before env vars are configured). The specific endpoints that need these
    # values will fail explicitly with clear messages instead of the whole
    # server crashing at module-import time.
    SUPABASE_URL: str | None = None
    SUPABASE_KEY: str | None = None
    SUPABASE_JWT_SECRET: str | None = None

    SENTRY_DSN: str | None = None

    SMS_BASE_URL: str | None = None
    SMS_API_KEY: str | None = None
    SMS_SENDER: str | None = None
    TWILIO_ACCOUNT_SID: str | None = None
    TWILIO_AUTH_TOKEN: str | None = None

    # Redis (optional) - persistent rate-limiting / caching backend. When empty
    # or unreachable, the rate limiter falls back to in-memory storage.
    REDIS_URL: str | None = None

    # Database connection strings
    # DATABASE_URL: pooled connection (pgBouncer) used by application runtime.
    # DIRECT_URL: direct database URL (port 5432) suitable for migrations or admin tasks.
    DATABASE_URL: str | None = None
    DIRECT_URL: str | None = None
    PGBOUNCER_TRANSACTION_POOLING: bool = False

    @staticmethod
    def _is_placeholder(value: str) -> bool:
        lowered = value.lower()
        return any(marker in lowered for marker in _PLACEHOLDER_MARKERS)

    def validate_secrets(self) -> None:
        if self.DEBUG:
            return
        if "*" in self.CORS_ORIGINS or self.CORS_ORIGINS == ["*"]:
            if os.getenv("VERCEL") != "1":
                raise RuntimeError(
                    "CORS_ORIGINS cannot contain '*' when not in DEBUG. "
                    "Set CORS_ORIGINS_JSON to explicit allowed origins, "
                    "e.g. CORS_ORIGINS_JSON='[\"https://admin.example.com\"]'."
                )
        secrets_to_check = {
            "SUPABASE_URL": self.SUPABASE_URL,
            "SUPABASE_KEY": self.SUPABASE_KEY,
            "SUPABASE_JWT_SECRET": self.SUPABASE_JWT_SECRET,
        }
        # Skip validation when secrets are not yet provided; endpoints using
        # them will return explicit, actionable errors later.
        if not all(secrets_to_check.values()):
            return
        placeholders = [name for name, val in secrets_to_check.items() if self._is_placeholder(val or "")]
        if placeholders:
            raise RuntimeError(
                "Placeholder/dummy secrets detected in environment "
                f"({', '.join(placeholders)}). Set real values in .env before running without DEBUG."
            )

    @property
    def jwt_algorithm(self) -> str:
        return "HS256"


@lru_cache
def get_settings() -> Settings:
    _settings = Settings()
    _settings.validate_secrets()
    return _settings


settings = get_settings()

