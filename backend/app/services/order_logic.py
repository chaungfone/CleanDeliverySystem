import logging
from typing import Dict, Set

from fastapi import HTTPException
from app.models.order import OrderStatus

logger = logging.getLogger(__name__)

# Define allowed transitions for the Order State Machine
# Format: { CURRENT_STATUS: {ALLOWED_NEXT_STATUSES} }
STATUS_TRANSITIONS: Dict[OrderStatus, Set[OrderStatus]] = {
    OrderStatus.PENDING: {OrderStatus.CONFIRMED, OrderStatus.CANCELLED},
    OrderStatus.CONFIRMED: {OrderStatus.ASSIGNED, OrderStatus.CANCELLED},
    OrderStatus.ASSIGNED: {OrderStatus.IN_TRANSIT, OrderStatus.CANCELLED},
    OrderStatus.IN_TRANSIT: {OrderStatus.DELIVERED, OrderStatus.CANCELLED},
    OrderStatus.DELIVERED: set(),  # Final state
    OrderStatus.CANCELLED: set(),  # Final state
}

# Role-based restrictions for transitions
ROLE_PERMISSIONS: Dict[str, Set[OrderStatus]] = {
    "ADMIN": {
        OrderStatus.CONFIRMED,
        OrderStatus.ASSIGNED,
        OrderStatus.CANCELLED
    },
    "DRIVER": {
        OrderStatus.IN_TRANSIT,
        OrderStatus.DELIVERED
    },
    "CUSTOMER": {
        OrderStatus.CANCELLED  # Customers can only cancel if still PENDING/CONFIRMED (logic handled below)
    }
}

def validate_status_transition(current_status: OrderStatus, new_status: OrderStatus, user_role: str):
    """
    Validates if an order status transition is allowed by the state machine and the user's role.
    """
    # 1. Check if the transition exists in the state machine
    allowed_next = STATUS_TRANSITIONS.get(current_status, set())
    if new_status not in allowed_next:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid transition: Cannot change status from {current_status} to {new_status}"
        )

    # 2. Check role-based permissions
    allowed_roles_for_status = ROLE_PERMISSIONS.get(user_role, set())
    if new_status not in allowed_roles_for_status:
        raise HTTPException(
            status_code=403,
            detail=f"Role '{user_role}' is not authorized to change status to {new_status}"
        )

    # 3. Specific business rule: Customers can only cancel orders that are PENDING or CONFIRMED
    if user_role == "CUSTOMER" and new_status == OrderStatus.CANCELLED:
        if current_status not in (OrderStatus.PENDING, OrderStatus.CONFIRMED):
            raise HTTPException(
                status_code=400,
                detail="Orders can only be cancelled before they are assigned to a driver."
            )

    return True
