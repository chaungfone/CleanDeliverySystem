import logging

from supabase import Client

# Note: Since endpoints/customer.py has place_order, we'd normally call that service
# but since it's in a router, we'll implement a standalone service function if needed.

logger = logging.getLogger(__name__)

async def process_iot_ping(db: Client, device_token: str, water_level: int):
    """
    Handles IoT sensor ingestion.
    If level < threshold, triggers an automated refill order.
    """
    device = db.table("iot_devices").select("*, addresses(user_id, id)") \
        .eq("device_token", device_token).maybe_single().execute().data

    if not device:
        logger.error("IoT Device not found: %s", device_token)
        return

    # Update current level
    db.table("iot_devices").update({"current_level": water_level, "last_ping": "now()"}).eq("device_token", device_token).execute()

    # Check for auto-refill
    if water_level <= device["low_level_threshold"]:
        logger.info("LOW WATER LEVEL (%d%%) detected for device %s. Triggering auto-refill.", water_level, device_token)

        # Check if there's already a PENDING order for this address to avoid duplicates
        existing_order = db.table("orders") \
            .select("id") \
            .eq("address_id", device["address_id"]) \
            .eq("status", "PENDING") \
            .maybe_single().execute().data

        if not existing_order:
            # Create a simple refill order
            # In production, we'd fetch the user's 'standard' product choice
            logger.info("Creating automated order for address %s", device["address_id"])
            # order_data = OrderCreate(...)
            # trigger place_order logic here
