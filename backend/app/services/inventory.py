import logging
from uuid import UUID
from supabase import Client

logger = logging.getLogger(__name__)

def update_inventory_stock(db: Client, branch_id: str, item_type: str, quantity_delta: float):
    """
    Manually adjusts inventory stock for a specific branch.
    item_type: full_bottles, empty_bottles, caps_count, labels_count, water_liters
    """
    try:
        # Fetch current stock
        current = db.table("inventory").select(item_type).eq("branch_id", branch_id).maybe_single().execute().data

        if not current:
            # Initialize if not exists
            db.table("inventory").insert({"branch_id": branch_id, item_type: quantity_delta}).execute()
        else:
            new_val = current[item_type] + quantity_delta
            db.table("inventory").update({item_type: new_val}).eq("branch_id", branch_id).execute()

        logger.info("Updated %s for branch %s by %f", item_type, branch_id, quantity_delta)
    except Exception as e:
        logger.error("Failed to update inventory: %s", str(e))
