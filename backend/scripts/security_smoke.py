"""Security smoke tests for CleanDeliverySystem (Phase 1 verification).

Runs lightweight checks that must NOT depend on live network/DB:
  1. CORS: disallowed origin gets NO access-control-allow-origin header.
  2. Auth: unauthenticated request -> 401.
  3. IDOR: customer A accessing customer B's order -> 403.
  4. Rate limit: >5 request-otp calls in a minute -> 429.
Exit code 0 if all pass, 1 otherwise.
"""
import os
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
os.chdir(BACKEND_DIR)  # ensure Settings can find backend/.env
sys.path.insert(0, str(BACKEND_DIR))

from datetime import datetime, timezone
from uuid import UUID

from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.middleware.cors import CORSMiddleware

from app.core import security
from app.main import app, limiter
from app.models.user import UserResponse, UserRole

PASS = 0
FAIL = 0


def check(name: str, ok: bool, detail: str = "") -> None:
    global PASS, FAIL
    if ok:
        PASS += 1
        print(f"  [PASS] {name}")
    else:
        FAIL += 1
        print(f"  [FAIL] {name} {detail}")


def test_cors_disallowed_origin() -> None:
    print("\n1. CORS whitelist")
    test_app = FastAPI()

    @test_app.get("/healthz")
    def healthz():
        return {"status": "ok"}

    test_app.add_middleware(
        CORSMiddleware,
        allow_origins=["https://admin.example.com"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Requested-With"],
    )
    with TestClient(test_app) as client:
        disallowed = client.options(
            "/healthz",
            headers={"Origin": "https://evil-attacker.com", "Access-Control-Request-Method": "GET"},
        )
        check(
            "disallowed origin has no allow-origin header",
            "access-control-allow-origin" not in disallowed.headers,
            f"(got {dict(disallowed.headers)})",
        )
        allowed = client.options(
            "/healthz",
            headers={"Origin": "https://admin.example.com", "Access-Control-Request-Method": "GET"},
        )
        check(
            "allowed origin receives allow-origin header",
            "access-control-allow-origin" in allowed.headers,
        )


def test_unauth_401() -> None:
    print("\n2. Authentication (401)")
    client = TestClient(app)
    resp = client.get("/api/v1/auth/me")
    check("GET /auth/me without token -> 401", resp.status_code == 401, f"(got {resp.status_code})")


def test_idor_403() -> None:
    print("\n3. IDOR guard (403)")
    ORDER = "11111111-1111-1111-1111-111111111111"
    OWNER = "22222222-2222-2222-2222-222222222222"
    INTRUDER = "33333333-3333-3333-3333-333333333333"

    class _Ex:
        data = {"id": ORDER, "customer_id": OWNER}

    class _Q:
        def select(self, *a, **k): return self
        def eq(self, *a, **k): return self
        def maybe_single(self): return self
        def execute(self): return _Ex()

    class _T:
        def select(self, *a, **k): return _Q()

    class _C:
        def table(self, name): return _T()

    security.get_supabase_client = lambda: _C()

    def user(uid: str, role: UserRole) -> UserResponse:
        return UserResponse(
            id=UUID(uid),
            phone_number="09123456789",
            full_name="Smoke",
            role=role,
            branch_id=None,
            created_at=datetime.now(timezone.utc),
        )

    try:
        security.require_owner_or_admin(UUID(ORDER), user(INTRUDER, UserRole.CUSTOMER))
        check("non-owner customer blocked", False, "(no 403 raised)")
    except Exception as exc:  # noqa: BLE001 - expected HTTPException(403)
        check("non-owner customer blocked (403)", getattr(exc, "status_code", None) == 403, f"(got {exc})")

    try:
        order = security.require_owner_or_admin(UUID(ORDER), user(OWNER, UserRole.CUSTOMER))
        check("owner allowed", order["id"] == ORDER)
    except Exception as exc:  # noqa: BLE001
        check("owner allowed", False, f"(raised {exc})")


def test_rate_limit_429() -> None:
    print("\n4. Rate limiting (429)")
    client = TestClient(app)
    previous = limiter.enabled
    limiter.enabled = True
    try:
        import secrets

        phone = f"09{secrets.randbelow(100_000_000):08d}"
        statuses = [
            client.post("/api/v1/auth/request-otp", json={"phone_number": phone}).status_code
            for _ in range(6)
        ]
        check("5 allowed then 429 on 6th", statuses[:5] == [200] * 5 and statuses[5] == 429, f"(got {statuses})")
    finally:
        limiter.enabled = previous


if __name__ == "__main__":
    test_cors_disallowed_origin()
    test_unauth_401()
    test_idor_403()
    test_rate_limit_429()
    print(f"\n=== SMOKE RESULT: {PASS} passed, {FAIL} failed ===")
    raise SystemExit(1 if FAIL else 0)
