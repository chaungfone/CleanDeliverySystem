import logging
from typing import Annotated, Callable
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
    try:
        return jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=[settings.jwt_algorithm],
            audience="authenticated",
            options={
                # Reject tokens missing these claims outright (no silent "no exp" pass).
                "require": ["exp", "iat", "aud"],
                # Reject alg confusion (e.g. attacker switching to "none"/HS).
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
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
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

    def checker(user: UserResponse = Depends(get_current_user)) -> UserResponse:
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

    if user.role not in (UserRole.ADMIN, UserRole.BRANCH_MANAGER):
        if str(order["customer_id"]) != str(user.id):
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

    if user.role not in (UserRole.ADMIN, UserRole.BRANCH_MANAGER):
        if str(order["driver_id"]) != str(user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not your assigned order",
            )

    return order


AssignedDriverOrder = Annotated[dict, Depends(require_driver_or_admin)]
