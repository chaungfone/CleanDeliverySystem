import secrets

from fastapi.testclient import TestClient

from app.main import app, limiter

client = TestClient(app)


def _unique_phone() -> str:
    return f"09{secrets.randbelow(100_000_000):08d}"


def test_request_otp_limited_to_5_per_phone_when_enabled():
    previous = limiter.enabled
    limiter.enabled = True
    try:
        phone = _unique_phone()
        statuses = [
            client.post("/api/v1/auth/request-otp", json={"phone_number": phone}).status_code
            for _ in range(6)
        ]
        assert statuses[:5] == [200, 200, 200, 200, 200]
        assert statuses[5] == 429
    finally:
        limiter.enabled = previous


def test_verify_otp_limited_to_10_per_phone_when_enabled():
    previous = limiter.enabled
    limiter.enabled = True
    try:
        phone = _unique_phone()
        statuses = [
            client.post("/api/v1/auth/verify-otp", json={"phone_number": phone, "otp": "000000"}).status_code
            for _ in range(11)
        ]
        assert statuses[:10] == [400] * 10  # "please request first" -> not rate limited yet
        assert statuses[10] == 429
    finally:
        limiter.enabled = previous


def test_rate_limit_key_includes_phone():
    from starlette.requests import Request

    from app.core.rate_limit import auth_rate_key

    scope = {
        "type": "http",
        "method": "POST",
        "path": "/api/v1/auth/request-otp",
        "headers": [],
        "client": ("1.2.3.4", 12345),
        "scheme": "http",
        "query_string": b"",
        "server": ("test", 80),
    }

    async def receive():
        return {"type": "http.request", "body": b'{"phone_number":"+959692117187"}', "more_body": False}

    request = Request(scope, receive)
    import asyncio

    asyncio.run(request.body())
    assert auth_rate_key(request) == "1.2.3.4:959692117187"


def test_auth_rate_key_falls_back_to_ip_without_body():
    from starlette.requests import Request

    from app.core.rate_limit import auth_rate_key

    scope = {
        "type": "http",
        "method": "POST",
        "path": "/api/v1/auth/request-otp",
        "headers": [],
        "client": ("9.9.9.9", 1),
        "scheme": "http",
        "query_string": b"",
        "server": ("test", 80),
    }
    request = Request(scope, lambda: None)  # body never read
    assert auth_rate_key(request) == "9.9.9.9"


def test_redis_storage_selected_when_reachable(monkeypatch):
    from limits.storage import RedisStorage
    from slowapi import Limiter

    from app.core import rate_limit

    monkeypatch.setattr(rate_limit.settings, "REDIS_URL", "redis://localhost:6379/0")
    monkeypatch.setattr(rate_limit, "redis_reachable", lambda uri, timeout=1.0: True)
    uri = rate_limit.select_storage()
    assert uri == "redis://localhost:6379/0"

    limiter = Limiter(key_func=lambda: "test", storage_uri=uri)
    assert isinstance(limiter._limiter.storage, RedisStorage)


def test_memory_storage_fallback_when_redis_unreachable(monkeypatch):
    from limits.storage import MemoryStorage
    from slowapi import Limiter

    from app.core import rate_limit

    monkeypatch.setattr(rate_limit.settings, "REDIS_URL", "redis://localhost:6399/0")
    monkeypatch.setattr(rate_limit, "redis_reachable", lambda uri, timeout=1.0: False)
    assert rate_limit.select_storage() == "memory://"

    limiter = Limiter(key_func=lambda: "test", storage_uri="memory://")
    assert isinstance(limiter._limiter.storage, MemoryStorage)


def test_memory_storage_when_redis_url_unset(monkeypatch):
    from app.core import rate_limit

    monkeypatch.setattr(rate_limit.settings, "REDIS_URL", None)
    assert rate_limit.select_storage() == "memory://"


def test_redis_reachable_returns_false_on_connection_refused():
    # Port 1 on loopback is not listening -> connection refused (fast), no raise.
    from app.core.rate_limit import redis_reachable

    assert redis_reachable("redis://127.0.0.1:1/0", timeout=0.5) is False


def test_app_limiter_uses_memory_storage_in_dev():
    from limits.storage import MemoryStorage

    assert isinstance(limiter._limiter.storage, MemoryStorage)

