import json
import logging

from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request

from app.core.config import settings

logger = logging.getLogger(__name__)


def auth_rate_key(request: Request) -> str:
    """
    Rate-limit key for auth endpoints = remote IP + (normalized) phone number.

    Using only the IP lets an attacker rotate phone numbers; using only the phone
    lets an attacker rotate IPs. Combining both prevents OTP-spam on a victim's
    number (request-otp) and limits brute-force attempts on one number (verify-otp).
    Falls back to the IP alone if the body can't be read.
    """
    ip = get_remote_address(request)
    try:
        body = getattr(request, "_body", b"") or b""
        if body:
            payload = json.loads(body)
            phone = payload.get("phone_number")
            if isinstance(phone, str) and phone:
                digits = "".join(ch for ch in phone if ch.isdigit())
                return f"{ip}:{digits}"
    except Exception as exc:  # noqa: BLE001 - body not JSON / not yet parsed; fall back to IP key
        logger.debug("auth_rate_key: could not read phone from body: %s", exc)
    return ip


limiter = Limiter(key_func=get_remote_address)

# Strict enforcement in production; allow dev/tests to run unthrottled.
limiter.enabled = not settings.DEBUG