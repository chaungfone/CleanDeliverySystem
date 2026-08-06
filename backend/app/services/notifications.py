import logging
from app.models.order import OrderStatus

logger = logging.getLogger(__name__)

async def trigger_order_notification(order_id: str, status: OrderStatus, recipient_id: str, recipient_role: str):
    """
    Triggers a real-time notification based on order status changes.
    This can be integrated with FCM (Firebase Cloud Messaging), Twilio (SMS), or WebSockets.
    """
    message = ""

    if status == OrderStatus.CONFIRMED:
        message = f"Your order #{order_id} has been confirmed!"
    elif status == OrderStatus.ASSIGNED:
        message = f"A driver has been assigned to your order #{order_id}."
    elif status == OrderStatus.IN_TRANSIT:
        message = "Your water delivery is on its way!"
    elif status == OrderStatus.DELIVERED:
        message = "Order delivered. Thank you for using Clean Delivery!"
    elif status == OrderStatus.CANCELLED:
        message = f"Order #{order_id} has been cancelled."

    if not message:
        return

    # MOCK INTEGRATION: Log the notification
    # In production, call FirebaseAdmin or SMS API here
    logger.info("NOTIFICATION [%s - %s]: %s", recipient_role, recipient_id, message)

    # Example logic for specific roles
    if recipient_role == "DRIVER" and status == OrderStatus.ASSIGNED:
        logger.info("PUSH to Driver: New delivery task assigned.")

    return True
