import logging
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, Path, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from postgrest.exceptions import APIError

from app.core.config import settings
from app.core.database import get_supabase_client
from app.models.user import UserResponse, UserRole

logger = logging.getLogger(__name__)

_bearer = HTTPBearer(auto_error=False)


def _decode_token(token: str) -> dict:
    if not settings.SUPABASE_JWT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "Server is not configured: SUPABASE_JWT_SECRET is missing from "
                "environment variables. Add it in Vercel Project Settings -> "
                "Environment Variables and redeploy."
            ),
        )
    try:
        return jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=[settings.jwt_algorithm],
            audience="authenticated",
            options={
                "require": ["exp", "iat", "aud"],
                "verify_signature": True,
                "verify_exp": True,
                "verify_iat": True,
                "verify_aud": True,
            },
        )
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired"
        ) from exc
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        ) from exc


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),  # noqa: B008 - FastAPI idiom
) -> UserResponse:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
        )

    payload = _decode_token(credentials.credentials)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload"
        )

    try:
        result = (
            get_supabase_client()
            .table("users")
            .select("*")
            .eq("id", user_id)
            .maybe_single()
            .execute()
        )
    except APIError as exc:
        logger.error("Supabase error while fetching user %s: %s", user_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error while resolving user",
        ) from exc

    data = result.data if result else None
    if not data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
        )

    return UserResponse(**data)


CurrentUser = Annotated[UserResponse, Depends(get_current_user)]


def require_roles(*roles: UserRole) -> Callable[[UserResponse], UserResponse]:
    allowed = set(roles)

    def checker(user: UserResponse = Depends(get_current_user)) -> UserResponse:  # noqa: B008 - FastAPI idiom
        if user.role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions"
            )
        return user

    return checker


require_admin = require_roles(UserRole.ADMIN)
require_driver = require_roles(UserRole.DRIVER)
require_customer = require_roles(UserRole.CUSTOMER)


OrderIdPath = Annotated[
    UUID, Path(description="Order ID from the URL path", alias="order_id")
]


def require_owner_or_admin(
    order_id: OrderIdPath,
    user: CurrentUser,
) -> dict:
    """
    Authorization guard so a customer can only read/modify their own order.

    - CUSTOMER: must be the order's `customer_id`, otherwise 403.
    - ADMIN / BRANCH_MANAGER: may access any order.
    - Missing order: 404.

    Returns the order row (dict) so routes can use it directly.
    """
    try:
        order = (
            get_supabase_client()
            .table("orders")
            .select("*")
            .eq("id", str(order_id))
            .maybe_single()
            .execute()
            .data
        )
    except APIError as exc:
        logger.error("Supabase error while resolving order %s: %s", order_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error while resolving order",
        ) from exc

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Order not found"
        )

    if (
        user.role not in (UserRole.ADMIN, UserRole.BRANCH_MANAGER)
        and str(order["customer_id"]) != str(user.id)
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not your order"
        )

    return order


OwnerOrAdminOrder = Annotated[dict, Depends(require_owner_or_admin)]


def require_driver_or_admin(
    order_id: OrderIdPath,
    user: CurrentUser,
) -> dict:
    """
    Authorization guard so a driver can only act on an order assigned to them.

    - DRIVER: must be the order's `driver_id`, otherwise 403.
    - ADMIN / BRANCH_MANAGER: may access any order.
    - Missing/not-assigned order: 404.

    Distinct from :func:`require_owner_or_admin` (which checks the *customer*),
    because a driver is the assigned courier, not the ordering customer.
    """
    try:
        order = (
            get_supabase_client()
            .table("orders")
            .select("*")
            .eq("id", str(order_id))
            .maybe_single()
            .execute()
            .data
        )
    except APIError as exc:
        logger.error("Supabase error while resolving order %s: %s", order_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error while resolving order",
        ) from exc

    if not order or not order.get("driver_id"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found or not assigned",
        )

    if (
        user.role not in (UserRole.ADMIN, UserRole.BRANCH_MANAGER)
        and str(order["driver_id"]) != str(user.id)
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not your assigned order",
        )

    return order


AssignedDriverOrder = Annotated[dict, Depends(require_driver_or_admin)]


# ---- JWT jti deny-list / revocation -----------------------------------------
_REVOKED_TABLE = "revoked_tokens"
_USER_REVOKE_PREFIX = "user:"
_REFRESH_LIFETIME_SECONDS = 30 * 24 * 3600


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def is_token_revoked(jti: str | None, user_id: str | None = None) -> bool:
    """
    True if `jti` (or any token of `user_id`) appears on the deny-list.

    A per-user marker row `user:{user_id}` allows "revoke all sessions"
    (password reset / GDPR force logout) without enumerating every jti.
    """
    candidates: list[str] = []
    if jti:
        candidates.append(jti)
    if user_id:
        candidates.append(f"{_USER_REVOKE_PREFIX}{user_id}")
    if not candidates:
        return False
    try:
        result = (
            get_supabase_client()
            .table(_REVOKED_TABLE)
            .select("id")
            .in_("jti", candidates)
            .maybe_single()
            .execute()
        )
        row = result.data if result else None
    except APIError as exc:
        logger.error("Error checking revoked token: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error while checking token revocation",
        ) from exc
    return bool(row)


def revoke_token(jti: str | None, user_id: str, expires_at: int | None) -> None:
    """Add a single token jti to the deny-list (idempotent)."""
    if not jti:
        return
    expires = (
        datetime.fromtimestamp(expires_at, tz=timezone.utc).isoformat()
        if expires_at
        else _now_iso()
    )
    try:
        get_supabase_client().table(_REVOKED_TABLE).upsert(
            {"jti": jti, "user_id": user_id, "expires_at": expires},
            on_conflict="jti",
        ).execute()
    except APIError as exc:
        logger.error("Error revoking token %s: %s", jti, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error while revoking token",
        ) from exc


def revoke_all_user_tokens(user_id: str) -> None:
    """
    Revoke every active session for `user_id` (password reset / GDPR force logout).

    Inserts a `user:{user_id}` marker so any of the user's tokens are denied by
    :func:`is_token_revoked` without knowing each jti. Idempotent (upsert on jti).
    """
    if not user_id:
        return
    expires_at = int(datetime.now(timezone.utc).timestamp()) + _REFRESH_LIFETIME_SECONDS
    try:
        get_supabase_client().table(_REVOKED_TABLE).upsert(
            {
                "jti": f"{_USER_REVOKE_PREFIX}{user_id}",
                "user_id": user_id,
                "expires_at": datetime.fromtimestamp(expires_at, tz=timezone.utc).isoformat(),
            },
            on_conflict="jti",
        ).execute()
    except APIError as exc:
        logger.error("Error revoking all tokens for %s: %s", user_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error while revoking user tokens",
        ) from exc


def purge_expired_revoked_tokens() -> int:
    """
    Delete deny-list rows whose expires_at has passed.

    Intended for a scheduled/periodic job; returns the number of rows removed.
    """
    try:
        result = (
            get_supabase_client()
            .table(_REVOKED_TABLE)
            .delete()
            .lt("expires_at", _now_iso())
            .execute()
        )
        return len(result.data) if result and result.data else 0
    except APIError as exc:
        logger.error("Error purging expired revoked tokens: %s", exc)
        return 0
