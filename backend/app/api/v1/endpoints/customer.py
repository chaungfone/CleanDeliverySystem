from decimal import Decimal

from fastapi import APIRouter, HTTPException

from app.core.database import get_supabase_client
from app.core.security import CurrentUser, OwnerOrAdminOrder
from app.models.order import OrderCreate, OrderResponse
from app.models.product import ProductResponse
from app.services.ai_voice import parse_voice_intent, transcribe_audio
from app.services.caching import catalog_cache
from app.services.orders import load_orders_with_items

router = APIRouter()


from pydantic import BaseModel, Field


class OrderReview(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    comment: str | None = Field(None, max_length=1000)

@router.get("/products", response_model=list[ProductResponse])
def list_products():
    # Attempt to get from cache first
    cached_products = catalog_cache.get("all_products")
    if cached_products:
        return cached_products

    db = get_supabase_client()
    products = db.table("products").select("*").order("name").execute().data

    # Cache for next time
    catalog_cache.set("all_products", products)

    return products


@router.post("/orders", response_model=OrderResponse, status_code=201)
def place_order(payload: OrderCreate, user: CurrentUser):
    db = get_supabase_client()

    address_resp = (
        db.table("addresses")
        .select("id")
        .eq("id", str(payload.address_id))
        .eq("user_id", str(user.id))
        .maybe_single()
        .execute()
    )
    address = address_resp.data if address_resp else None
    if not address:
        raise HTTPException(status_code=400, detail="Delivery address not found")

    product_ids = [str(item.product_id) for item in payload.items]
    products_data = (
        db.table("products")
        .select("id, name, price, stock_quantity")
        .in_("id", product_ids)
        .execute()
        .data
    )
    product_map = {p["id"]: p for p in products_data}
    if len(product_map) != len(set(product_ids)):
        raise HTTPException(status_code=400, detail="One or more products do not exist")

    total = Decimal(0)
    line_rows: list[dict] = []
    for item in payload.items:
        product = product_map[str(item.product_id)]
        if product["stock_quantity"] < item.quantity:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Insufficient stock for '{product['name']}' "
                    f"(available: {product['stock_quantity']})"
                ),
            )
        unit_price = (
            item.unit_price
            if item.unit_price is not None
            else Decimal(str(product["price"]))
        )
        line_rows.append(
            {
                "product_id": str(item.product_id),
                "quantity": item.quantity,
                "unit_price": str(unit_price),
            }
        )
        total += unit_price * item.quantity

    order = None
    try:
        order = (
            db.table("orders")
            .insert(
                {
                    "customer_id": str(user.id),
                    "address_id": str(payload.address_id),
                    "status": "PENDING",
                    "total_amount": str(total),
                    "payment_status": "PENDING",
                    "payment_method": payload.payment_method.value,
                    "empty_bottles_returned": payload.empty_bottles_returned,
                }
            )
            .execute()
            .data[0]
        )

        for row in line_rows:
            row["order_id"] = order["id"]
        created_items = db.table("order_items").insert(line_rows).execute().data

        for item in payload.items:
            product = product_map[str(item.product_id)]
            db.table("products").update(
                {"stock_quantity": product["stock_quantity"] - item.quantity}
            ).eq("id", str(item.product_id)).execute()
    except Exception as exc:
        if order:
            db.table("orders").delete().eq("id", order["id"]).execute()
        raise HTTPException(status_code=500, detail="Failed to place order") from exc

    order["items"] = created_items
    return order


@router.get("/orders/history", response_model=list[OrderResponse])
def order_history(user: CurrentUser):
    db = get_supabase_client()
    return load_orders_with_items(db, customer_id=str(user.id))

@router.get("/orders/{order_id}", response_model=OrderResponse)
def get_my_order(order: OwnerOrAdminOrder):
    """Returns one order; a customer may only view their own order."""
    return order


@router.post("/orders/{order_id}/review")
def submit_order_review(order: OwnerOrAdminOrder, review: OrderReview):
    """Submits a review for a delivered order (owner or ADMIN/BRANCH_MANAGER)."""
    if order["status"] != "DELIVERED":
        raise HTTPException(status_code=400, detail="Only delivered orders can be reviewed")

    db = get_supabase_client()
    return db.table("reviews").insert({
        "order_id": order["id"],
        "customer_id": order["customer_id"],
        "driver_id": order["driver_id"],
        "rating": review.rating,
        "comment": review.comment
    }).execute().data

@router.post("/voice-order")
async def voice_order(user: CurrentUser, audio_file: bytes):
    """Processes a voice order using AI STT and NLP."""
    # 1. Transcribe
    text = await transcribe_audio(audio_file)
    # 2. Parse Intent
    intent = await parse_voice_intent(text)

    return {
        "transcription": text,
        "parsed_intent": intent,
        "message": "Please confirm these details to place the order."
    }

@router.get("/wallet/balance")
def get_wallet_balance(user: CurrentUser):
    db = get_supabase_client()
    wallet = db.table("wallets").select("balance").eq("user_id", str(user.id)).maybe_single().execute().data
    return wallet or {"balance": 0}
