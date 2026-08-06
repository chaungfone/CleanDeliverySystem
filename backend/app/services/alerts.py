import logging
import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)

async def send_system_alert(message: str, severity: str = "INFO"):
    """
    Sends an alert message to an external webhook (Slack/Telegram).
    """
    # MOCK Logic: In production, configure SLACK_WEBHOOK_URL or TELEGRAM_BOT_TOKEN
    alert_payload = {
        "text": f"🚨 *SYSTEM ALERT [{severity}]*\n{message}",
        "severity": severity
    }

    logger.warning("SYSTEM ALERT: %s", message)

    # Example for Slack
    webhook_url = getattr(settings, "ALERT_WEBHOOK_URL", None)
    if webhook_url:
        try:
            async with httpx.AsyncClient() as client:
                await client.post(webhook_url, json=alert_payload)
        except Exception as e:
            logger.error("Failed to send external alert: %s", str(e))

    return True
