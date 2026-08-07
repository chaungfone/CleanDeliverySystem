import logging
from typing import Optional
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode

from app.core.config import settings

logger = logging.getLogger(__name__)

# Try to create an async SQLAlchemy engine tailored for pgBouncer/asyncpg if SQLAlchemy is installed.
try:
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, async_sessionmaker
    from sqlalchemy.engine.url import make_url
    from sqlalchemy.pool import NullPool, QueuePool
    SQLALCHEMY_AVAILABLE = True
except Exception:
    SQLALCHEMY_AVAILABLE = False
    logger.debug("SQLAlchemy async not available in environment; db helper will be disabled.")


def _to_asyncpg_url(raw: str) -> str:
    """
    Convert a postgresql:// URL to postgresql+asyncpg:// and when a pooled pgBouncer
    endpoint is detected, add a parameter to disable prepared statement caching for asyncpg.

    This is lenient: it appends prepared_statement_cache_size=0 when the URL contains
    "pgbouncer=true" or points at port 6543 which our pooler examples use.
    """
    if not raw:
        return raw

    # Quick transform for scheme
    if raw.startswith("postgresql+asyncpg://"):
        base = raw
    elif raw.startswith("postgresql://"):
        base = "postgresql+asyncpg://" + raw[len("postgresql://"):]
    else:
        # Unknown scheme, just return as-is
        return raw

    # Parse and possibly append prepared_statement_cache_size=0 for pooled URL
    parsed = urlparse(base)
    qs = parse_qs(parsed.query or "")

    is_pooler = settings.PGBOUNCER_TRANSACTION_POOLING or is_pooler_url(base)

    if is_pooler:
        # Only add if not already present
        if "prepared_statement_cache_size" not in qs:
            qs["prepared_statement_cache_size"] = ["0"]

    new_query = urlencode({k: v[0] for k, v in qs.items()}) if qs else ""
    new_parsed = parsed._replace(query=new_query)
    return urlunparse(new_parsed)


def is_pooler_url(raw: Optional[str]) -> bool:
    """Return True if the provided DB URL looks like a pooler/pgBouncer endpoint.

    Heuristics:
    - query param pgbouncer is present and truthy
    - port == 6543 (common pooler port in our infra)
    - hostname contains 'pooler' or 'pgbouncer'
    """
    if not raw:
        return False
    parsed = urlparse(raw)
    qs = parse_qs(parsed.query or "")
    if qs.get("pgbouncer"):
        return True
    if parsed.port == 6543:
        return True
    hostname = (parsed.hostname or "")
    if "pooler" in hostname or "pgbouncer" in hostname:
        return True
    return False


def pool_class_for_url(raw: Optional[str]):
    """Return the SQLAlchemy pool class to use for the given URL.
    
    For pgBouncer transaction pooling, NullPool is recommended. Otherwise QueuePool is fine.
    If SQLAlchemy is not available, returns the string name for testing purposes.
    """
    if settings.PGBOUNCER_TRANSACTION_POOLING or is_pooler_url(raw):
        if SQLALCHEMY_AVAILABLE:
            return NullPool
        return "NullPool"
    else:
        if SQLALCHEMY_AVAILABLE:
            return QueuePool
        return "QueuePool"


# Expose engine and sessionmaker if possible
engine: Optional["AsyncEngine"] = None
async_session = None

if SQLALCHEMY_AVAILABLE and settings.DATABASE_URL:
    try:
        async_url = _to_asyncpg_url(settings.DATABASE_URL)
        # Decide pool class based on whether URL looks like a pooler (pgBouncer)
        pool_cls = pool_class_for_url(settings.DATABASE_URL)
        create_args = {
            "pool_pre_ping": True,
            "future": True,
        }
        # When using pgBouncer transaction pooling, prefer NullPool and avoid
        # connection pooling in SQLAlchemy layer. Otherwise use default pool settings.
        if pool_cls is not None:
            create_args["poolclass"] = pool_cls

        engine = create_async_engine(async_url, **create_args)
        async_session = async_sessionmaker(engine, expire_on_commit=False)
        logger.info("Async DB engine created from DATABASE_URL (pool=%s)", getattr(pool_cls, "__name__", str(pool_cls)))
    except Exception as exc:
        logger.exception("Failed to create async SQLAlchemy engine: %s", exc)
else:
    if not settings.DATABASE_URL:
        logger.debug("No DATABASE_URL provided; async DB engine not created.")


def get_engine() -> Optional["AsyncEngine"]:
    return engine


def get_async_sessionmaker():
    return async_session


__all__ = [
    "get_engine",
    "get_async_sessionmaker",
    "_to_asyncpg_url",
    "is_pooler_url",
    "pool_class_for_url",
]

