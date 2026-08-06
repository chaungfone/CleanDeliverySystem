import logging
from uuid import UUID
from supabase import Client
from app.models.order import OrderStatus

logger = logging.getLogger(__name__)

def assign_driver_to_order(db: Client, order_id: str) -> str | None:
    """
    Automated Driver Assignment Logic.
    Finds the most suitable driver based on:
    1. Active status (online)
    2. Current workload (number of active assignments)
    3. (Future) Geographic proximity to order delivery address
    """
    try:
        # 1. Fetch all online drivers
        # In a real system, we'd check driver_locations table for recent heartbeats
        drivers_resp = db.table("users").select("id").eq("role", "DRIVER").execute()
        drivers = drivers_resp.data

        if not drivers:
            logger.warning("No drivers available for assignment for order %s", order_id)
            return None

        # 2. Get active assignment counts for each driver
        # Active statuses: ASSIGNED, IN_TRANSIT
        active_orders_resp = db.table("orders").select("driver_id") \
            .in_("status", ["ASSIGNED", "IN_TRANSIT"]).execute()

        workload_map = {}
        for order in active_orders_resp.data:
            d_id = order["driver_id"]
            workload_map[d_id] = workload_map.get(d_id, 0) + 1

        # 3. Pick driver with the least workload
        # Sort drivers by their current assignment count
        drivers.sort(key=lambda d: workload_map.get(d["id"], 0))
        best_driver_id = drivers[0]["id"]

        # 4. Update order with driver_id and move to ASSIGNED
        db.table("orders").update({
            "driver_id": best_driver_id,
            "status": OrderStatus.ASSIGNED.value
        }).eq("id", order_id).execute()

        logger.info("Automatically assigned driver %s to order %s", best_driver_id, order_id)
        return best_driver_id

    except Exception as e:
        logger.error("Error during automated driver assignment: %s", str(e))
        return None
