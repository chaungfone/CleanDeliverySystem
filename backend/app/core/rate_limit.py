import json
import logging

import redis
from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request

from app.core.config import settings

logger = logging.getLogger(__name__)

_REDIS_PING_TIMEOUT = 1.0


def auth_rate_key(request: Request) -> str:
    """
    Rate-limit key for auth endpoints = remote IP + (normalized) phone number.

    Using only the IP lets an attacker rotate phone numbers; using only the phone
    lets an attacker rotate IPs. Combining both prevents OTP-spam on a victim's
    number (request-otp) and limits brute-force attempts on one number (verify-otp).
    Falls back to the IP alone if the body can't be read.
    """
    ip = get_remote_address(request)
    try:
        body = getattr(request, "_body", b"") or b""
        if body:
            payload = json.loads(body)
            phone = payload.get("phone_number")
            if isinstance(phone, str) and phone:
                digits = "".join(ch for ch in phone if ch.isdigit())
                return f"{ip}:{digits}"
    except Exception as exc:  # noqa: BLE001 - body not JSON / not yet parsed; fall back to IP key
        logger.debug("auth_rate_key: could not read phone from body: %s", exc)
    return ip


def redis_reachable(uri: str, timeout: float = _REDIS_PING_TIMEOUT) -> bool:
    """Best-effort liveness probe for the configured Redis URL.

    Uses RESP2 (protocol=2) for compatibility with older Redis servers that
    do not implement the Redis 6+ HELLO handshake. Never raises: a failed
    probe just means "fall back to in-memory".
    """
    try:
        client = redis.from_url(
            uri,
            socket_connect_timeout=timeout,
            socket_timeout=timeout,
            decode_responses=True,
            protocol=2,
        )
        return bool(client.ping())
    except Exception as exc:  # noqa: BLE001 - probe must never crash startup
        logger.debug("Redis reachability probe failed for %s: %s", uri, exc)
        return False


def select_storage() -> tuple[str, dict]:
    """Choose the rate-limiter storage URI + options.

    - settings.REDIS_URL set AND reachable  -> use Redis (persistent, multi-instance),
      with RESP2 options for older Redis servers
    - settings.REDIS_URL set but unreachable -> in-memory fallback + startup WARNING
    - settings.REDIS_URL unset              -> in-memory (offline dev), INFO log
    """
    redis_url = (settings.REDIS_URL or "").strip()
    if redis_url and redis_reachable(redis_url):
        logger.info("Rate limiter using Redis storage: %s", redis_url)
        return redis_url, {"protocol": 2}
    if redis_url:
        logger.warning(
            "REDIS_URL=%s configured but unreachable; falling back to in-memory rate limiting.",
            redis_url,
        )
    else:
        logger.info("REDIS_URL not configured; rate limiter using in-memory storage.")
    return "memory://", {}


_storage_uri, _storage_options = select_storage()

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=_storage_uri,
    storage_options=_storage_options,
)

# Strict enforcement in production; allow dev/tests to run unthrottled.
limiter.enabled = not settings.DEBUG
