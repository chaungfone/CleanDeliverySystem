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
    from app.core.rate_limit import auth_rate_key

    from starlette.requests import Request

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
    from app.core.rate_limit import auth_rate_key

    from starlette.requests import Request

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
