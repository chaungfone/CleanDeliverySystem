import re
import secrets
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from enum import Enum
from typing import Any
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from postgrest.exceptions import APIError
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.database import get_supabase_client
from app.core.security import require_admin
from app.models.order import OrderResponse, OrderStatus
from app.models.product import ProductCreate, ProductResponse, ProductUpdate
from app.models.user import UserRole
from app.services.dispatch import assign_driver_to_order
from app.services.orders import load_orders_with_items
from app.services.reporting import generate_sales_csv

router = APIRouter(dependencies=[Depends(require_admin)])


def _normalize_phone(phone: str) -> str:
    digits = re.sub(r"\D", "", phone)
    if digits.startswith("95") and len(digits) == 11:
        return "0" + digits[2:]
    return digits


def _to_e164(phone: str) -> str:
    """Converts a local number (e.g. 09xxxxxxxxx) to E.164 for GoTrue."""
    digits = re.sub(r"\D", "", phone)
    if digits.startswith("95") and len(digits) == 11:
        return "+" + digits
    if digits.startswith("0") and len(digits) == 10:
        return "+95" + digits[1:]
    if digits.startswith("9") and len(digits) == 10:
        return "+95" + digits
    return "+" + digits


def _admin_request(method: str, path: str, json: dict | None = None) -> dict:
    """Calls the GoTrue Admin API with the service role key."""
    headers = {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_KEY}",
    }
    url = f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1/admin{path}"
    try:
        with httpx.Client(timeout=30) as client:
            resp = client.request(method, url, headers=headers, json=json)
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Auth service unavailable: {exc}") from exc
    if resp.status_code >= 400:
        try:
            body = resp.json()
            msg = body.get("msg") or body.get("message") or body.get("error_description") or resp.text
        except Exception:  # noqa: BLE001 - non-JSON upstream error body; fall back to raw text
            msg = resp.text
        raise HTTPException(status_code=400, detail=msg)
    return resp.json()


def _product_payload(data: dict) -> dict:
    """Serializes a product payload for Supabase (Decimal -> str)."""
    payload = dict(data)
    for key in ("price", "deposit_fee"):
        if payload.get(key) is not None:
            payload[key] = str(payload[key])
    return payload


def _branch_payload(data: dict) -> dict:
    """Builds a branch payload for Supabase (lat/lng -> GeoJSON point)."""
    payload = dict(data)
    lat = payload.pop("latitude", None)
    lng = payload.pop("longitude", None)
    if lat is not None and lng is not None:
        payload["location"] = {
            "type": "Point",
            "coordinates": [float(lng), float(lat)],
        }
    return payload


class AnalyticsPeriod(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


_UUID_PATTERN = r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"


class BranchCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    address: str = Field(..., min_length=1, max_length=500)
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    is_active: bool = True


class BranchUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    address: str | None = Field(None, min_length=1, max_length=500)
    latitude: float | None = Field(None, ge=-90, le=90)
    longitude: float | None = Field(None, ge=-180, le=180)
    is_active: bool | None = None


class StaffCreate(BaseModel):
    phone_number: str = Field(..., pattern=r"^\+?[0-9]{9,15}$")
    full_name: str = Field(..., min_length=1, max_length=255)
    role: UserRole = UserRole.DRIVER
    branch_id: str | None = Field(None, pattern=_UUID_PATTERN)


class StaffUpdate(BaseModel):
    full_name: str | None = Field(None, min_length=1, max_length=255)
    role: UserRole | None = None
    branch_id: str | None = Field(None, pattern=_UUID_PATTERN)


class InventoryUpdate(BaseModel):
    full_bottles: int | None = Field(None, ge=0)
    empty_bottles: int | None = Field(None, ge=0)
    caps_count: int | None = Field(None, ge=0)
    labels_count: int | None = Field(None, ge=0)
    water_liters: float | None = Field(None, ge=0)

class AssignDriver(BaseModel):
    driver_id: str | None = Field(None, pattern=_UUID_PATTERN)  # None -> automated assignment


@router.get("/orders")
def list_orders(status: OrderStatus | None = None, limit: int = Query(200, ge=1, le=500)):
    """Lists all orders with customer/driver names and items."""
    db = get_supabase_client()
    query = db.table("orders").select("*")
    if status:
        query = query.eq("status", status.value)
    orders = query.order("created_at", desc=True).limit(limit).execute().data

    if not orders:
        return []

    user_ids = {str(o["customer_id"]) for o in orders}
    user_ids.update(str(o["driver_id"]) for o in orders if o.get("driver_id"))
    users_map: dict[str, dict[str, Any]] = {}
    if user_ids:
        users = (
            db.table("users")
            .select("id, full_name, role, phone_number")
            .in_("id", list(user_ids))
            .execute()
            .data
        )
        users_map = {u["id"]: u for u in users}

    order_ids = [str(o["id"]) for o in orders]
    items: list[dict] = []
    if order_ids:
        items = (
            db.table("order_items")
            .select("*")
            .in_("order_id", order_ids)
            .execute()
            .data
        )
    grouped: dict[str, list[dict]] = {}
    for item in items:
        grouped.setdefault(item["order_id"], []).append(item)

    result: list[dict[str, Any]] = []
    for order in orders:
        customer = users_map.get(str(order.get("customer_id")), {})
        driver = users_map.get(str(order.get("driver_id")), {})
        result.append(
            {
                **order,
                "customer_name": customer.get("full_name") or "Unknown",
                "customer_phone": customer.get("phone_number"),
                "driver_name": driver.get("full_name"),
                "items": grouped.get(order["id"], []),
            }
        )
    return result


@router.get("/inventory")
def get_inventory():
    """Returns per-branch inventory totals plus product stock."""
    db = get_supabase_client()
    try:
        rows = db.table("inventory").select("*").order("updated_at", desc=True).execute().data or []
    except APIError:
        rows = []
    try:
        branches = db.table("branches").select("id, name").execute().data or []
    except APIError:
        branches = []
    branch_map = {b["id"]: b["name"] for b in branches}

    for row in rows:
        row["branch_name"] = branch_map.get(str(row.get("branch_id")), "Unknown")

    totals = {
        "full_bottles": sum(int(r.get("full_bottles") or 0) for r in rows),
        "empty_bottles": sum(int(r.get("empty_bottles") or 0) for r in rows),
        "caps_count": sum(int(r.get("caps_count") or 0) for r in rows),
        "labels_count": sum(int(r.get("labels_count") or 0) for r in rows),
        "water_liters": sum(float(r.get("water_liters") or 0) for r in rows),
    }
    try:
        products = (
            db.table("products").select("id, name, price, stock_quantity").order("name").execute().data or []
        )
    except APIError:
        products = []
    return {"branches": rows, "totals": totals, "products": products}


@router.get("/branches")
def list_branches():
    """Returns branches with their staff members."""
    db = get_supabase_client()
    try:
        branches = db.table("branches").select("*").order("name").execute().data or []
    except APIError:
        branches = []
    try:
        staff = (
            db.table("users")
            .select("id, full_name, role")
            .neq("role", "CUSTOMER")
            .order("full_name")
            .execute()
            .data
            or []
        )
    except APIError:
        staff = []
    for s in staff:
        if "branch_id" not in s:
            s["branch_id"] = None
    for branch in branches:
        branch["staff"] = [s for s in staff if str(s.get("branch_id")) == str(branch["id"])]
    return {"branches": branches, "staff": staff}


@router.get("/drivers")
def list_drivers():
    """Returns all drivers with their latest reported location."""
    db = get_supabase_client()
    try:
        drivers = (
            db.table("users")
            .select("id, full_name, phone_number")
            .eq("role", "DRIVER")
            .order("full_name")
            .execute()
            .data
            or []
        )
    except APIError:
        drivers = []
    try:
        locations = (
            db.table("driver_locations").select("driver_id, location, updated_at").execute().data or []
        )
    except APIError:
        locations = []
    loc_map = {loc["driver_id"]: loc for loc in locations}
    for driver in drivers:
        loc = loc_map.get(driver["id"], {})
        driver["location"] = loc.get("location")
        driver["last_ping"] = loc.get("updated_at")
        if "branch_id" not in driver:
            driver["branch_id"] = None
    return drivers

@router.get("/dashboard/analytics")
def dashboard_analytics(period: AnalyticsPeriod = AnalyticsPeriod.DAILY):
    """
    Returns aggregated delivery volume and revenue analytics.
    Periods: daily, weekly, monthly
    """
    db = get_supabase_client()
    now = datetime.now(timezone.utc)

    if period == "weekly":
        start_date = (now - timedelta(days=7)).isoformat()
    elif period == "monthly":
        start_date = (now - timedelta(days=30)).isoformat()
    else:  # daily
        start_date = now.date().isoformat()

    orders_data = db.table("orders") \
        .select("status, total_amount, created_at") \
        .gte("created_at", start_date) \
        .execute().data

    delivered_orders = [o for o in orders_data if o["status"] == OrderStatus.DELIVERED]

    total_revenue = sum(Decimal(str(o["total_amount"])) for o in delivered_orders)
    total_volume = len(delivered_orders)

    return {
        "period": period,
        "start_date": start_date,
        "total_revenue": str(total_revenue),
        "delivered_volume": total_volume,
        "pending_deliveries": sum(1 for o in orders_data if o["status"] not in (OrderStatus.DELIVERED, OrderStatus.CANCELLED)),
        "active_drivers": len(db.table("driver_locations").select("driver_id").execute().data)
    }

@router.get("/reports/sales/csv")
def export_sales_report(start_date: date | None = None):
    """Exports sales data to CSV."""
    db = get_supabase_client()
    query = db.table("orders").select("*")
    if start_date:
        query = query.gte("created_at", start_date.isoformat())

    orders = query.execute().data
    csv_content = generate_sales_csv(orders)

    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=sales_report_{datetime.now(timezone.utc).date()}.csv"}
    )

@router.get("/reviews")
def list_reviews():
    """Returns all customer reviews."""
    db = get_supabase_client()
    return db.table("reviews").select("*, users!customer_id(full_name)").order("created_at", desc=True).execute().data

@router.post("/orders/{order_id}/assign", response_model=OrderResponse)
def handle_assignment(order_id: UUID, body: AssignDriver):
    """
    Assigns a driver to an order.
    If driver_id is provided, it's a manual assignment.
    If driver_id is null, it triggers the automated dispatch logic.
    """
    order_id = str(order_id)
    db = get_supabase_client()

    if body.driver_id:
        # Manual Assignment
        driver_resp = db.table("users").select("id, role").eq("id", body.driver_id).maybe_single().execute()
        driver = driver_resp.data if driver_resp else None
        if not driver or driver["role"] != "DRIVER":
            raise HTTPException(status_code=400, detail="Valid Driver not found")

        db.table("orders").update({
            "driver_id": body.driver_id,
            "status": OrderStatus.ASSIGNED.value
        }).eq("id", order_id).execute()
    else:
        # Automated Assignment
        best_driver = assign_driver_to_order(db, order_id)
        if not best_driver:
            raise HTTPException(status_code=404, detail="No available drivers for automated assignment")

    return load_orders_with_items(db, order_ids=[order_id])[0]


@router.get("/products", response_model=list[ProductResponse])
def list_admin_products():
    """Lists all products (bypasses the public catalog cache)."""
    db = get_supabase_client()
    return db.table("products").select("*").order("name").execute().data


@router.post("/products", response_model=ProductResponse, status_code=201)
def create_product(payload: ProductCreate):
    """Creates a new product."""
    db = get_supabase_client()
    rows = db.table("products").insert(_product_payload(payload.model_dump())).execute().data
    if not rows:
        raise HTTPException(status_code=500, detail="Failed to create product")
    return rows[0]


@router.patch("/products/{product_id}", response_model=ProductResponse)
def update_product(product_id: UUID, payload: ProductUpdate):
    """Updates an existing product (partial update supported)."""
    product_id = str(product_id)
    db = get_supabase_client()
    existing = (
        db.table("products").select("id").eq("id", product_id).maybe_single().execute().data
    )
    if not existing:
        raise HTTPException(status_code=404, detail="Product not found")

    data = payload.model_dump(exclude_unset=True)
    if not data:
        return (
            db.table("products").select("*").eq("id", product_id).maybe_single().execute().data
        )

    rows = db.table("products").update(_product_payload(data)).eq("id", product_id).execute().data
    return rows[0]


@router.delete("/products/{product_id}", status_code=204)
def delete_product(product_id: UUID):
    """Deletes a product."""
    product_id = str(product_id)
    db = get_supabase_client()
    existing = (
        db.table("products").select("id").eq("id", product_id).maybe_single().execute().data
    )
    if not existing:
        raise HTTPException(status_code=404, detail="Product not found")
    db.table("products").delete().eq("id", product_id).execute()


@router.post("/branches", status_code=201)
def create_branch(payload: BranchCreate):
    """Creates a new branch."""
    db = get_supabase_client()
    try:
        rows = db.table("branches").insert(_branch_payload(payload.model_dump())).execute().data
    except APIError as exc:
        raise HTTPException(status_code=400, detail=f"Failed to create branch: {exc.message}") from exc
    if not rows:
        raise HTTPException(status_code=500, detail="Failed to create branch")
    return rows[0]


@router.patch("/branches/{branch_id}")
def update_branch(branch_id: UUID, payload: BranchUpdate):
    """Updates an existing branch (partial update supported)."""
    branch_id = str(branch_id)
    db = get_supabase_client()
    existing = (
        db.table("branches").select("id").eq("id", branch_id).maybe_single().execute().data
    )
    if not existing:
        raise HTTPException(status_code=404, detail="Branch not found")

    data = payload.model_dump(exclude_unset=True)
    if not data:
        return (
            db.table("branches").select("*").eq("id", branch_id).maybe_single().execute().data
        )

    try:
        rows = db.table("branches").update(_branch_payload(data)).eq("id", branch_id).execute().data
    except APIError as exc:
        raise HTTPException(status_code=400, detail=f"Failed to update branch: {exc.message}") from exc
    return rows[0]


@router.delete("/branches/{branch_id}", status_code=204)
def delete_branch(branch_id: UUID):
    """Deletes a branch."""
    branch_id = str(branch_id)
    db = get_supabase_client()
    existing = (
        db.table("branches").select("id").eq("id", branch_id).maybe_single().execute().data
    )
    if not existing:
        raise HTTPException(status_code=404, detail="Branch not found")
    try:
        db.table("branches").delete().eq("id", branch_id).execute()
    except APIError as exc:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete branch with linked orders/staff. Reassign or deactivate it first.",
        ) from exc


@router.get("/staff")
def list_staff():
    """Lists all staff (non-customer) accounts."""
    db = get_supabase_client()
    try:
        rows = (
            db.table("users")
            .select("id, phone_number, full_name, role, created_at")
            .neq("role", "CUSTOMER")
            .order("created_at", desc=True)
            .execute()
            .data
            or []
        )
    except APIError:
        rows = []
    for row in rows:
        if "branch_id" not in row:
            row["branch_id"] = None
    return rows


@router.post("/staff", status_code=201)
def create_staff(payload: StaffCreate):
    """Creates a staff account via Supabase Auth (auto-creates the profile)."""
    if payload.role == UserRole.CUSTOMER:
        raise HTTPException(status_code=400, detail="Staff role must be ADMIN, DRIVER, or BRANCH_MANAGER")

    auth_user = _admin_request(
        "POST",
        "/users",
        json={
            "phone": _to_e164(payload.phone_number),
            "password": secrets.token_urlsafe(12),
            "phone_confirm": False,
            "user_metadata": {"full_name": payload.full_name},
            "role": "authenticated",
        },
    )
    user_id = auth_user["id"]

    db = get_supabase_client()
    rows = (
        db.table("users")
        .update(
            {
                "phone_number": _normalize_phone(payload.phone_number),
                "full_name": payload.full_name,
                "role": payload.role.value,
                "branch_id": payload.branch_id,
            }
        )
        .eq("id", user_id)
        .execute()
        .data
    )
    return rows[0]


@router.patch("/staff/{user_id}")
def update_staff(user_id: UUID, payload: StaffUpdate):
    """Updates a staff account (role, name, branch assignment)."""
    user_id = str(user_id)
    db = get_supabase_client()
    existing = (
        db.table("users").select("id").eq("id", user_id).maybe_single().execute().data
    )
    if not existing:
        raise HTTPException(status_code=404, detail="Staff member not found")

    data = payload.model_dump(exclude_unset=True)
    if data.get("role") == UserRole.CUSTOMER.value:
        raise HTTPException(status_code=400, detail="Staff role must be ADMIN, DRIVER, or BRANCH_MANAGER")
    if not data:
        return db.table("users").select("*").eq("id", user_id).maybe_single().execute().data

    rows = db.table("users").update(data).eq("id", user_id).execute().data
    return rows[0]


@router.delete("/staff/{user_id}", status_code=204)
def delete_staff(user_id: UUID):
    """Deletes a staff account (removes the Auth user and cascades to the profile)."""
    user_id = str(user_id)
    db = get_supabase_client()
    existing = (
        db.table("users").select("id, role").eq("id", user_id).maybe_single().execute().data
    )
    if not existing:
        raise HTTPException(status_code=404, detail="Staff member not found")
    try:
        _admin_request("DELETE", f"/users/{user_id}")
    except HTTPException as exc:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete this user: they have linked records (e.g. orders).",
        ) from exc


@router.patch("/inventory/{branch_id}")
def update_inventory(branch_id: UUID, payload: InventoryUpdate):
    """Adjusts inventory levels for a branch (creates a row if missing)."""
    branch_id = str(branch_id)
    db = get_supabase_client()
    branch = (
        db.table("branches").select("id").eq("id", branch_id).maybe_single().execute().data
    )
    if not branch:
        raise HTTPException(status_code=404, detail="Branch not found")

    data = payload.model_dump(exclude_unset=True)
    if not data:
        raise HTTPException(status_code=400, detail="No inventory fields provided")

    existing_resp = db.table("inventory").select("id").eq("branch_id", branch_id).limit(1).execute()
    existing = existing_resp.data[0] if existing_resp.data else None
    if existing:
        rows = db.table("inventory").update(data).eq("branch_id", branch_id).execute().data
    else:
        rows = db.table("inventory").insert({"branch_id": branch_id, **data}).execute().data
    return rows[0]
