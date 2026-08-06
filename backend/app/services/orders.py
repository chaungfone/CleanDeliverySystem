import logging

from fastapi import HTTPException
from postgrest.exceptions import APIError
from supabase import Client

logger = logging.getLogger(__name__)


def load_orders_with_items(
    db: Client,
    *,
    customer_id: str | None = None,
    driver_id: str | None = None,
    order_ids: list[str] | None = None,
) -> list[dict]:
    try:
        query = db.table("orders").select("*")
        if customer_id is not None:
            query = query.eq("customer_id", customer_id)
        if driver_id is not None:
            query = query.eq("driver_id", driver_id)
        if order_ids is not None:
            query = query.in_("id", order_ids)
        orders = query.order("created_at", desc=True).execute().data

        ids = [str(o["id"]) for o in orders]
        items: list[dict] = []
        if ids:
            items = db.table("order_items").select("*").in_("order_id", ids).execute().data

        grouped: dict[str, list[dict]] = {}
        for item in items:
            grouped.setdefault(item["order_id"], []).append(item)

        for order in orders:
            order["items"] = grouped.get(order["id"], [])
        return orders
    except APIError as exc:
        logger.error("Supabase error in load_orders_with_items: %s", exc)
        raise HTTPException(status_code=500, detail="Database error while loading orders") from exc
