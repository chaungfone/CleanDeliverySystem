import logging
import re
import secrets
import time
from typing import Any

import json
import jwt
from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.database import get_supabase_client
from app.core.rate_limit import auth_rate_key, limiter
from app.core.security import (
    CurrentUser,
    _decode_token,
    is_token_revoked,
    revoke_all_user_tokens,
    revoke_token,
)
from app.models.user import UserResponse, UserRole
from app.services.sms import sms_service

logger = logging.getLogger(__name__)

router = APIRouter()

import redis

_otp_store: dict[str, dict[str, Any]] = {}
_OTP_TTL_SECONDS = 300

# Redis client (lazy init) for cross-process OTP storage. Falls back to in-memory dict if Redis is unavailable.
_redis_client: redis.Redis | None = None

_REFRESH_COOKIE = "cd_refresh_token"
_REFRESH_TTL_SECONDS = 30 * 24 * 3600  # 30 days


def _set_refresh_cookie(response: Response, refresh_token: str) -> None:
    """Stores the refresh token in an HttpOnly cookie, never exposed to JS/XSS."""
    secure = not settings.DEBUG
    same_site: str = "none" if secure else "lax"
    response.set_cookie(
        key=_REFRESH_COOKIE,
        value=refresh_token,
        httponly=True,
        secure=secure,
        samesite=same_site,
        max_age=_REFRESH_TTL_SECONDS,
        path="/",
    )


def _clear_refresh_cookie(response: Response) -> None:
    secure = not settings.DEBUG
    same_site: str = "none" if secure else "lax"
    response.set_cookie(
        key=_REFRESH_COOKIE,
        value="",
        httponly=True,
        secure=secure,
        samesite=same_site,
        max_age=0,
        expires="Thu, 01 Jan 1970 00:00:00 GMT",
        path="/",
    )
    try:
        response.delete_cookie(
            key=_REFRESH_COOKIE,
            path="/",
        )
    except Exception:
        pass


def _normalize_phone(phone: str) -> str:
    """
    Normalizes phone numbers to 09... format for Myanmar.
    Handles +959..., 959..., 09..., and 9... formats.
    """
    digits = re.sub(r"\D", "", phone)
    if digits.startswith("95"):
        return "0" + digits[2:]
    if not digits.startswith("0") and len(digits) >= 7:
        return "0" + digits
    return digits


def _get_redis_client() -> redis.Redis | None:
    """Lazily initialize and return a Redis client or None if unavailable."""
    global _redis_client
    if _redis_client:
        return _redis_client
    try:
        url = settings.REDIS_URL
        if not url:
            return None
        client = redis.from_url(url, decode_responses=True)
        # quick health check
        if client.ping():
            _redis_client = client
            return _redis_client
        return None
    except Exception:
        # If Redis isn't available, fall back to in-memory store
        return None


def _otp_key(phone: str) -> str:
    return f"otp:{phone}"


def _set_otp(phone: str, otp: str, full_name: str | None) -> None:
    """Store OTP in Supabase otp_codes table so it survives serverless instance restarts."""
    try:
        db = get_supabase_client()
        expires_at_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time() + _OTP_TTL_SECONDS))
        payload = {
            "phone_number": phone,
            "otp_code": otp,
            "full_name": full_name,
            "expires_at": expires_at_iso,
        }
        db.table("otp_codes").upsert(payload, on_conflict="phone_number").execute()
        return
    except Exception as exc:
        logger.warning("Supabase OTP store failed, falling back to Redis/in-memory: %s", str(exc))
    client = _get_redis_client()
    payload = {"otp": otp, "full_name": full_name, "expires_at": time.time() + _OTP_TTL_SECONDS}
    if client:
        try:
            client.set(_otp_key(phone), json.dumps(payload), ex=_OTP_TTL_SECONDS)
            return
        except Exception:
            pass
    _otp_store[phone] = payload


def _pop_otp(phone: str) -> dict[str, Any] | None:
    """Retrieve and remove OTP from Supabase otp_codes table first, then fallback to Redis/in-memory."""
    try:
        db = get_supabase_client()
        res = db.table("otp_codes").select("phone_number, otp_code, full_name, expires_at").eq("phone_number", phone).maybe_single().execute()
        row = res.data if res else None
        if row:
            try:
                db.table("otp_codes").delete().eq("phone_number", phone).execute()
            except Exception:
                pass
            import datetime as _dt
            expires_at_epoch: float = 0.0
            expires_raw = row.get("expires_at")
            if isinstance(expires_raw, str):
                try:
                    if expires_raw.endswith("Z"):
                        expires_dt = _dt.datetime.fromisoformat(expires_raw.replace("Z", "+00:00"))
                    else:
                        expires_dt = _dt.datetime.fromisoformat(expires_raw)
                    if expires_dt.tzinfo is None:
                        expires_dt = expires_dt.replace(tzinfo=_dt.timezone.utc)
                    expires_at_epoch = expires_dt.timestamp()
                except Exception:
                    expires_at_epoch = 0.0
            elif isinstance(expires_raw, (int, float)):
                expires_at_epoch = float(expires_raw)
            return {
                "otp": row.get("otp_code"),
                "full_name": row.get("full_name"),
                "expires_at": expires_at_epoch,
            }
    except Exception as exc:
        logger.warning("Supabase OTP fetch failed, falling back to Redis/in-memory: %s", str(exc))
    client = _get_redis_client()
    if client:
        try:
            raw = client.get(_otp_key(phone))
            if not raw:
                return None
            client.delete(_otp_key(phone))
            return json.loads(raw)
        except Exception:
            pass
    return _otp_store.pop(phone, None)


class OtpRequest(BaseModel):
    phone_number: str = Field(..., pattern=r"^\+?[0-9]{9,15}$")
    full_name: str | None = Field(None, min_length=1, max_length=255)


class OtpVerify(BaseModel):
    phone_number: str = Field(..., pattern=r"^\+?[0-9]{9,15}$")
    otp: str = Field(..., pattern=r"^[0-9]{6}$")


def _issue_tokens(user_id: str, role: str) -> dict[str, str]:
    if not settings.SUPABASE_JWT_SECRET:
        raise HTTPException(
            status_code=500,
            detail=(
                "Server is not configured: SUPABASE_JWT_SECRET is missing from "
                "environment variables. Add it in Vercel Project Settings -> "
                "Environment Variables and redeploy."
            ),
        )
    now = int(time.time())
    base = {
        "sub": user_id,
        "role": role,
        "aud": "authenticated",
        "iat": now,
        "jti": secrets.token_urlsafe(16),
    }
    access_token = jwt.encode(
        {**base, "exp": now + 3600},
        settings.SUPABASE_JWT_SECRET,
        algorithm=settings.jwt_algorithm,
    )
    refresh_token = jwt.encode(
        {**base, "exp": now + 30 * 24 * 3600},
        settings.SUPABASE_JWT_SECRET,
        algorithm=settings.jwt_algorithm,
    )
    return {"access_token": access_token, "refresh_token": refresh_token}


@router.get("/me", response_model=UserResponse)
def get_me(user: CurrentUser):
    return user


@router.delete("/me", status_code=204)
def delete_my_account(user: CurrentUser):
    """
    Deletes the current user's account and all associated data.
    Implements GDPR 'Right to be Forgotten'.
    """
    db = get_supabase_client()
    # GDPR force logout: revoke every session before removing the account.
    revoke_all_user_tokens(str(user.id))
    # RLS/Triggers will handle cascaded deletion of orders, addresses, etc.
    # We delete from public.users first, then auth.users management would happen via Supabase Admin API
    db.table("users").delete().eq("id", str(user.id)).execute()


@router.post("/request-otp")
@limiter.limit("5/minute", key_func=auth_rate_key)  # 5 OTP requests per IP+phone
def request_otp(request: Request, body: OtpRequest):
    phone = _normalize_phone(body.phone_number)
    otp: str | None = None
    delivery_status = "not_configured"
    try:
        configured = (
            (sms_service.base_url and sms_service.api_key)
            or (sms_service.twilio_sid and sms_service.twilio_auth_token)
        )
        if configured:
            otp = sms_service.send_otp(phone)
            delivery_status = "sent"
    except Exception as exc:  # noqa: BLE001 - never let SMS failures block OTP issuance; fall back.
        logger.exception("SMS provider error when sending OTP to %s: %s", phone, str(exc))
        delivery_status = "sms_failed"
        otp = None
    if not otp:
        otp = f"{secrets.randbelow(1_000_000):06d}"
    _set_otp(phone, otp, body.full_name)
    print(f"[OTP] Phone: {phone} | Code: {otp} | Status: {delivery_status}")

    result = {
        "message": f"OTP processed ({delivery_status})",
        "phone_number": phone,
    }
    result["debug_otp"] = otp
    return result


@router.post("/verify-otp")
@limiter.limit("10/minute", key_func=auth_rate_key)  # OTP brute-force prevention
def verify_otp(request: Request, body: OtpVerify, response: Response):
    phone = _normalize_phone(body.phone_number)
    entry = _pop_otp(phone)
    if not entry:
        raise HTTPException(
            status_code=400,
            detail="Please request a verification code first by entering your phone number and tapping 'Request OTP'.",
        )
    if entry["expires_at"] < time.time():
        raise HTTPException(status_code=400, detail="This verification code has expired. Please go back and request a new code.")
    if entry["otp"] != body.otp:
        raise HTTPException(status_code=400, detail="The verification code you entered is incorrect. Please double-check the 6-digit code and try again.")

    db = get_supabase_client()
    existing_resp = (
        db.table("users")
        .select("*")
        .eq("phone_number", phone)
        .maybe_single()
        .execute()
    )
    existing = existing_resp.data if existing_resp else None

    if existing:
        user_id = existing["id"]
        role = existing["role"]
    else:
        user_id = (
            db.table("users")
            .insert(
                {
                    "phone_number": phone,
                    "full_name": entry.get("full_name") or "User",
                    "role": UserRole.CUSTOMER.value,
                }
            )
            .execute()
            .data[0]
        )["id"]
        role = UserRole.CUSTOMER.value

    tokens = _issue_tokens(str(user_id), role)
    _set_refresh_cookie(response, tokens["refresh_token"])
    return {
        "access_token": tokens["access_token"],
        "role": role,
        "user_id": user_id,
    }


class RefreshResult(BaseModel):
    access_token: str
    role: str
    user_id: str


class MobileRefreshResult(RefreshResult):
    """Response model for mobile JSON refresh responses that include the rotated refresh token."""
    refresh_token: str


@router.post("/refresh-cookie", response_model=RefreshResult)
def refresh_cookie(request: Request, response: Response):
    """
    Exchanges the HttpOnly refresh cookie for a fresh short-lived access token.
    The refresh cookie is rotated on every call. Returns 401 when absent/invalid/expired.
    """
    refresh = request.cookies.get(_REFRESH_COOKIE)
    if not refresh:
        raise HTTPException(
            status_code=401, detail="No refresh cookie present. Please log in again."
        )

    payload = _decode_token(refresh)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid refresh token payload")

    # Deny-list check: reject revoked (logout / force-logout) refresh tokens.
    if is_token_revoked(payload.get("jti"), str(user_id)):
        raise HTTPException(status_code=401, detail="Token has been revoked")

    # Single-use rotation: revoke the presented refresh token's jti so it cannot be reused.
    try:
        revoke_token(payload.get("jti"), str(user_id), payload.get("exp"))
    except Exception:
        # If revocation fails for some reason, log and continue to avoid locking out users;
        # revoke_token itself should handle idempotency.
        logger.exception("Failed to revoke used refresh token jti during rotation")

    tokens = _issue_tokens(str(user_id), payload.get("role") or UserRole.CUSTOMER.value)
    _set_refresh_cookie(response, tokens["refresh_token"])
    return {
        "access_token": tokens["access_token"],
        "role": payload.get("role") or UserRole.CUSTOMER.value,
        "user_id": user_id,
    }


@router.post("/refresh", response_model=MobileRefreshResult)
async def refresh(request: Request, response: Response):
    """
    Mobile-friendly refresh endpoint.
    - Accepts JSON body {"refresh_token": "..."} for mobile clients or when X-Client-Type: mobile header is present.
    - For web/browser clients, the existing /refresh-cookie endpoint should be used (cookies are preferred).
    - Enforces single-use rotation by revoking the presented refresh token's jti and returning a rotated refresh token in the JSON response.
    """
    refresh = None
    # Detect mobile client hint via header
    client_type = request.headers.get("X-Client-Type", "").lower()

    if client_type == "mobile":
        # Expect JSON payload with refresh_token for mobile
        try:
            body = await request.json()
            refresh = body.get("refresh_token")
        except Exception:
            raise HTTPException(status_code=401, detail="Missing or invalid JSON body for mobile refresh")
        if not refresh:
            raise HTTPException(status_code=401, detail="Missing refresh_token in request body")
    else:
        # Fallback: if a JSON body contains refresh_token, allow it (helps some clients)
        try:
            body = await request.json()
            if isinstance(body, dict) and body.get("refresh_token"):
                refresh = body.get("refresh_token")
        except Exception:
            # no valid JSON body; fall back to cookie behavior
            pass

    # If still no refresh token found, try cookie (browser flow)
    if not refresh:
        refresh = request.cookies.get(_REFRESH_COOKIE)
        if not refresh:
            raise HTTPException(status_code=401, detail="No refresh token provided")

    payload = _decode_token(refresh)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid refresh token payload")

    # Deny-list check: reject revoked (logout / force-logout) refresh tokens.
    if is_token_revoked(payload.get("jti"), str(user_id)):
        raise HTTPException(status_code=401, detail="Token has been revoked")

    # Single-use rotation: revoke the presented refresh token's jti so it cannot be reused.
    try:
        revoke_token(payload.get("jti"), str(user_id), payload.get("exp"))
    except Exception:
        logger.exception("Failed to revoke used refresh token jti during rotation")

    # Issue rotated tokens
    tokens = _issue_tokens(str(user_id), payload.get("role") or UserRole.CUSTOMER.value)

    # For cookie-based (browser) flow, set HttpOnly cookie. For mobile/JSON flow, return rotated refresh token in body.
    if client_type == "mobile" or (not request.cookies.get(_REFRESH_COOKIE)):
        # Return rotated refresh token in JSON body for mobile clients
        return {
            "access_token": tokens["access_token"],
            "role": payload.get("role") or UserRole.CUSTOMER.value,
            "user_id": user_id,
            "refresh_token": tokens["refresh_token"],
        }
    else:
        # Browser flow: rotate cookie
        _set_refresh_cookie(response, tokens["refresh_token"])
        return {
            "access_token": tokens["access_token"],
            "role": payload.get("role") or UserRole.CUSTOMER.value,
            "user_id": user_id,
        }


@router.post("/logout")
def logout(request: Request, response: Response):
    """Revokes the current refresh token's jti, then clears the HttpOnly cookie."""
    refresh = request.cookies.get(_REFRESH_COOKIE)
    if refresh:
        try:
            payload = _decode_token(refresh)
            revoke_token(payload.get("jti"), str(payload.get("sub", "")), payload.get("exp"))
        except HTTPException as exc:
            logger.debug("Logout: refresh token invalid/expired (%s); clearing cookie anyway", exc.detail)
        except Exception:
            logger.exception("Logout: token revocation failed; clearing cookie anyway")
    _clear_refresh_cookie(response)
    return {"message": "Logged out"}
