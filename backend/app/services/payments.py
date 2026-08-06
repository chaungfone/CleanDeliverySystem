import logging
from decimal import Decimal
from supabase import Client

logger = logging.getLogger(__name__)

class PaymentAggregator:
    """
    Unified interface for KBZPay, WavePay, and Card payments.
    """
    async def create_checkout_session(self, order_id: str, amount: Decimal, method: str):
        """Generates payment redirect URL or QR data."""
        logger.info("Creating %s session for Order %s (Amt: %s)", method, order_id, amount)
        return {"payment_url": f"https://gateway.com/pay/{order_id}", "qr_code": "..."}

    async def verify_webhook(self, payload: dict, signature: str) -> bool:
        """Validates incoming webhook authenticity."""
        return True # Mock validation

async def process_wallet_payment(db: Client, user_id: str, amount: Decimal, order_id: str):
    """Deducts balance from digital wallet."""
    wallet = db.table("wallets").select("balance").eq("user_id", user_id).maybe_single().execute().data

    if not wallet or wallet["balance"] < amount:
        return {"success": False, "error": "Insufficient balance"}

    new_balance = float(wallet["balance"]) - float(amount)

    # Atomic transaction (pseudo-code)
    db.table("wallets").update({"balance": new_balance}).eq("user_id", user_id).execute()
    db.table("wallet_transactions").insert({
        "wallet_id": user_id,
        "amount": -float(amount),
        "type": "PAYMENT",
        "order_id": order_id
    }).execute()

    return {"success": True, "new_balance": new_balance}
