import json
import logging
import os
from functools import lru_cache

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


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    PROJECT_NAME: str = "Clean Water Delivery Management System"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = False
    # Production MUST override via CORS_ORIGINS_JSON; only defaults to ["*"] in dev/DEBUG.
    CORS_ORIGINS: list[str] = Field(
        default_factory=lambda: json.loads(os.getenv("CORS_ORIGINS_JSON", '["*"]')),
        validation_alias="CORS_ORIGINS_JSON",
    )

    SUPABASE_URL: str
    SUPABASE_KEY: str
    SUPABASE_JWT_SECRET: str

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
        placeholders = [name for name, val in secrets_to_check.items() if self._is_placeholder(val)]
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

