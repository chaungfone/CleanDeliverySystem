import logging
from uuid import UUID
from supabase import Client

logger = logging.getLogger(__name__)

def award_points(db: Client, user_id: str, points: int):
    """Awards loyalty points to a user."""
    try:
        db.rpc("award_loyalty_points", {"p_user_id": user_id, "p_points": points}).execute()
        logger.info("Awarded %d points to user %s", points, user_id)
    except Exception as e:
        logger.error("Failed to award points: %s", str(e))

def validate_promo_code(db: Client, code: str, user_id: str) -> dict | None:
    """Validates a coupon code and checks if the user has enough points."""
    coupon = db.table("coupons").select("*").eq("code", code).eq("is_active", True).maybe_single().execute().data

    if not coupon:
        return None

    user_points = db.table("loyalty_points").select("points_balance").eq("user_id", user_id).maybe_single().execute().data
    points_balance = user_points.get("points_balance", 0) if user_points else 0

    if points_balance < coupon["points_required"]:
        return {"valid": False, "error": "Insufficient loyalty points"}

    return {"valid": True, "discount": coupon["discount_amount"]}
