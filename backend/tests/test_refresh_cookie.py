import time

import jwt
from fastapi.testclient import TestClient

from app.api.v1.endpoints.auth import _REFRESH_COOKIE
from app.core.config import settings
from app.core.security import _decode_token
from app.main import app

client = TestClient(app)


def _login_as(phone: str = "09234567890"):
    """Logs a fresh TestClient in and returns (client, verify_otp_response)."""
    c = TestClient(app)
    req = c.post("/api/v1/auth/request-otp", json={"phone_number": phone})
    otp = req.json()["debug_otp"]
    verify = c.post("/api/v1/auth/verify-otp", json={"phone_number": phone, "otp": otp})
    return c, verify


def test_verify_otp_sets_httponly_refresh_cookie():
    c, verify = _login_as()
    assert c.cookies.get(_REFRESH_COOKIE) is not None

    raw = verify.headers.get("set-cookie", "")
    assert "httponly" in raw.lower()


def test_verify_otp_response_has_no_refresh_token_in_body():
    _, verify = _login_as()
    body = verify.json()
    assert "access_token" in body
    assert "refresh_token" not in body


def test_refresh_cookie_returns_new_access_token():
    c, verify = _login_as()
    assert verify.status_code == 200
    login_access = verify.json()["access_token"]

    resp = c.post("/api/v1/auth/refresh-cookie")
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["access_token"] != login_access


def test_refresh_cookie_without_cookie_returns_401():
    c = TestClient(app)
    resp = c.post("/api/v1/auth/refresh-cookie")
    assert resp.status_code == 401


def test_refresh_cookie_with_tampered_cookie_returns_401():
    c = TestClient(app)
    c.cookies.set(_REFRESH_COOKIE, "not-a-valid-jwt")
    resp = c.post("/api/v1/auth/refresh-cookie")
    assert resp.status_code == 401


def test_logout_clears_refresh_cookie():
    c, _ = _login_as()
    resp = c.post("/api/v1/auth/logout")
    assert resp.status_code == 200
    assert c.cookies.get(_REFRESH_COOKIE) is None


def test_expired_refresh_cookie_returns_401():
    c, _ = _login_as()
    resp = c.post("/api/v1/auth/refresh-cookie")
    assert resp.status_code == 200

    # Force the cookie to an expired (but correctly signed) token.
    payload = _decode_token(c.cookies.get(_REFRESH_COOKIE))
    expired = jwt.encode(
        {
            **payload,
            "exp": int(time.time()) - 10,
            "iat": int(time.time()) - 3600,
        },
        settings.SUPABASE_JWT_SECRET,
        algorithm=settings.jwt_algorithm,
    )
    c.cookies.set(_REFRESH_COOKIE, expired)
    resp = c.post("/api/v1/auth/refresh-cookie")
    assert resp.status_code == 401
