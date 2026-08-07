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


def test_mobile_json_refresh_returns_rotated_tokens():
    c, _ = _login_as()
    old_refresh = c.cookies.get(_REFRESH_COOKIE)
    assert old_refresh is not None

    # Mobile client posts JSON refresh token
    resp = c.post(
        "/api/v1/auth/refresh",
        headers={"X-Client-Type": "mobile"},
        json={"refresh_token": old_refresh},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["refresh_token"] != old_refresh

    # Mobile response should not set an HttpOnly cookie for the refresh token
    # (server returns rotated refresh token in JSON instead).
    set_cookie_hdr = resp.headers.get("set-cookie", "")
    assert _REFRESH_COOKIE not in set_cookie_hdr


def test_reuse_of_revoked_refresh_token_fails_and_new_token_works():
    c, _ = _login_as()
    old = c.cookies.get(_REFRESH_COOKIE)
    assert old is not None

    # First refresh rotates and revokes the old token
    resp = c.post(
        "/api/v1/auth/refresh",
        headers={"X-Client-Type": "mobile"},
        json={"refresh_token": old},
    )
    assert resp.status_code == 200
    new = resp.json().get("refresh_token")
    assert new is not None

    # Reusing old refresh token must be rejected
    resp2 = c.post(
        "/api/v1/auth/refresh",
        headers={"X-Client-Type": "mobile"},
        json={"refresh_token": old},
    )
    assert resp2.status_code == 401

    # New refresh token should work
    resp3 = c.post(
        "/api/v1/auth/refresh",
        headers={"X-Client-Type": "mobile"},
        json={"refresh_token": new},
    )
    assert resp3.status_code == 200
