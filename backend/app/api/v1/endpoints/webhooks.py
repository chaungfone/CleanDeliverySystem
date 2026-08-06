import logging
from enum import Enum
from typing import Any

from fastapi import APIRouter, Header
from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)

router = APIRouter()


class WebhookType(str, Enum):
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"


class WebhookPayload(BaseModel):
    model_config = ConfigDict(extra="ignore")

    type: WebhookType
    table: str = Field(..., min_length=1, max_length=100)
    payload_schema: str | None = Field(None, min_length=1, max_length=100, alias="schema")
    record: dict[str, Any] | None = None
    old_record: dict[str, Any] | None = None


@router.post("/supabase-db-webhook")
async def handle_supabase_webhook(
    payload: WebhookPayload,
    x_supabase_signature: str | None = Header(None),
):
    """
    Endpoint for Supabase Database Webhooks.
    Allows real-time reactions to database changes (e.g., table 'orders' INSERT/UPDATE).
    """
    # Simple validation - in production, verify the signature if configured
    # if x_supabase_signature != settings.WEBHOOK_SECRET:
    #     raise HTTPException(status_code=401, detail="Unauthorized webhook")

    logger.info("Received Supabase Webhook: %s", payload.model_dump())

    if payload.table == "orders" and payload.type == WebhookType.UPDATE:
        record = payload.record or {}
        old_record = payload.old_record or {}
        new_status = record.get("status")
        old_status = old_record.get("status")

        if new_status != old_status:
            logger.info(
                "Order %s status changed from %s to %s",
                record.get("id"),
                old_status,
                new_status,
            )
            # Here we could trigger async notifications or external integrations

    return {"status": "processed"}
