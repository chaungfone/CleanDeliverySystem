from decimal import Decimal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.core.database import get_supabase_client
from app.core.security import AssignedDriverOrder, CurrentUser, require_roles
from app.models.order import OrderResponse, OrderStatus
from app.services.notifications import trigger_order_notification
from app.services.order_logic import validate_status_transition
from app.services.orders import load_orders_with_items
from app.services.routing import optimize_route

router = APIRouter(dependencies=[Depends(require_roles("DRIVER"))])

class StatusUpdate(BaseModel):
    status: OrderStatus

class LocationUpdate(BaseModel):
    latitude: Decimal = Field(..., ge=-90, le=90)
    longitude: Decimal = Field(..., ge=-180, le=180)

@router.get("/orders", response_model=list[OrderResponse])
def assigned_orders(user: CurrentUser):
    db = get_supabase_client()
    return load_orders_with_items(db, driver_id=str(user.id))

@router.patch("/orders/{order_id}/status", response_model=OrderResponse)
async def update_order_status(order: AssignedDriverOrder, body: StatusUpdate):
    db = get_supabase_client()
    order_id = str(order["id"])

    current_status = OrderStatus(order["status"])

    # Use the State Machine Service
    validate_status_transition(current_status, body.status, "DRIVER")

    db.table("orders").update({"status": body.status.value}).eq("id", order_id).execute()

    # Trigger Real-time Notification
    await trigger_order_notification(
        order_id=order_id,
        status=body.status,
        recipient_id=order["customer_id"],
        recipient_role="CUSTOMER"
    )

    return load_orders_with_items(db, order_ids=[order_id])[0]

@router.post("/location")
def update_location(body: LocationUpdate, user: CurrentUser):
    db = get_supabase_client()
    # PostGIS Point format
    point = f"POINT({body.longitude} {body.latitude})"
    db.table("driver_locations").upsert(
        {"driver_id": str(user.id), "location": point},
        on_conflict="driver_id",
    ).execute()
    return {"status": "ok"}

@router.post("/optimize-route")
def get_optimized_route(user: CurrentUser, current_lat: float, current_lng: float):
    """
    Returns an optimized delivery sequence for the driver's assigned orders.
    """
    db = get_supabase_client()
    # Fetch assigned orders with addresses
    orders = db.table("orders") \
        .select("id, addresses(latitude, longitude)") \
        .eq("driver_id", str(user.id)) \
        .in_("status", ["ASSIGNED", "IN_TRANSIT"]) \
        .execute().data

    destinations = []
    for o in orders:
        addr = o.get("addresses")
        if addr:
            destinations.append({
                "order_id": o["id"],
                "latitude": float(addr["latitude"]),
                "longitude": float(addr["longitude"])
            })

    return optimize_route(current_lat, current_lng, destinations)
