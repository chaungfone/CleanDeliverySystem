import re
import secrets
import time
from typing import Any

import jwt
from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.database import get_supabase_client
from app.core.rate_limit import auth_rate_key, limiter
from app.core.security import CurrentUser, _decode_token
from app.models.user import UserResponse, UserRole

router = APIRouter()

_otp_store: dict[str, dict[str, Any]] = {}
_OTP_TTL_SECONDS = 300

_REFRESH_COOKIE = "cd_refresh_token"
_REFRESH_TTL_SECONDS = 30 * 24 * 3600  # 30 days


def _set_refresh_cookie(response: Response, refresh_token: str) -> None:
    """Stores the refresh token in an HttpOnly cookie, never exposed to JS/XSS."""
    response.set_cookie(
        key=_REFRESH_COOKIE,
        value=refresh_token,
        httponly=True,
        secure=not settings.DEBUG,
        samesite="lax",
        max_age=_REFRESH_TTL_SECONDS,
        path=f"{settings.API_V1_PREFIX}/auth",
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        key=_REFRESH_COOKIE,
        path=f"{settings.API_V1_PREFIX}/auth",
    )


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


class OtpRequest(BaseModel):
    phone_number: str = Field(..., pattern=r"^\+?[0-9]{9,15}$")
    full_name: str | None = Field(None, min_length=1, max_length=255)


class OtpVerify(BaseModel):
    phone_number: str = Field(..., pattern=r"^\+?[0-9]{9,15}$")
    otp: str = Field(..., pattern=r"^[0-9]{6}$")


def _issue_tokens(user_id: str, role: str) -> dict[str, str]:
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
    # RLS/Triggers will handle cascaded deletion of orders, addresses, etc.
    # We delete from public.users first, then auth.users management would happen via Supabase Admin API
    db.table("users").delete().eq("id", str(user.id)).execute()


@router.post("/request-otp")
@limiter.limit("5/minute", key_func=auth_rate_key)  # 5 OTP requests per IP+phone
def request_otp(request: Request, body: OtpRequest):
    phone = _normalize_phone(body.phone_number)
    otp = f"{secrets.randbelow(1_000_000):06d}"
    _otp_store[phone] = {
        "otp": otp,
        "full_name": body.full_name,
        "expires_at": time.time() + _OTP_TTL_SECONDS,
    }
    print(f"[MOCK OTP] Phone: {phone} | Code: {otp}")

    result = {
        "message": "OTP sent (mock: check console)",
        "phone_number": phone,
    }
    if settings.DEBUG:
        result["debug_otp"] = otp
    return result


@router.post("/verify-otp")
@limiter.limit("10/minute", key_func=auth_rate_key)  # OTP brute-force prevention
def verify_otp(request: Request, body: OtpVerify, response: Response):
    phone = _normalize_phone(body.phone_number)
    entry = _otp_store.get(phone)
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

    _otp_store.pop(phone, None)
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

    tokens = _issue_tokens(str(user_id), payload.get("role") or UserRole.CUSTOMER.value)
    _set_refresh_cookie(response, tokens["refresh_token"])
    return {
        "access_token": tokens["access_token"],
        "role": payload.get("role") or UserRole.CUSTOMER.value,
        "user_id": user_id,
    }


@router.post("/logout")
def logout(response: Response):
    _clear_refresh_cookie(response)
    return {"message": "Logged out"}
