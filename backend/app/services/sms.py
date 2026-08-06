import logging
import random

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class SMSService:
    def __init__(self) -> None:
        self.base_url = settings.SMS_BASE_URL
        self.api_key = settings.SMS_API_KEY
        self.sender = settings.SMS_SENDER
        self.twilio_sid = settings.TWILIO_ACCOUNT_SID
        self.twilio_auth_token = settings.TWILIO_AUTH_TOKEN

    def _send_otp_via_local(self, phone_number: str, message: str) -> None:
        response = httpx.post(
            f"{self.base_url}/send",
            json={
                "to": phone_number,
                "sender": self.sender,
                "message": message,
            },
            headers={"Authorization": f"Bearer {self.api_key}"},
            timeout=10.0,
        )
        response.raise_for_status()
        logger.info("OTP delivered via local SMS gateway to %s", phone_number)

    def _send_otp_via_twilio(self, phone_number: str, message: str) -> None:
        response = httpx.post(
            f"https://api.twilio.com/2010-04-01/Accounts/{self.twilio_sid}/Messages.json",
            data={
                "From": self.sender,
                "To": phone_number,
                "Body": message,
            },
            auth=(self.twilio_sid, self.twilio_auth_token),
            timeout=10.0,
        )
        response.raise_for_status()
        logger.info("OTP delivered via Twilio to %s", phone_number)

    def send_otp(self, phone_number: str) -> str:
        otp = f"{random.randint(0, 999999):06d}"
        message = f"Your verification code is {otp}"

        try:
            if self.base_url and self.api_key:
                self._send_otp_via_local(phone_number, message)
            elif self.twilio_sid and self.twilio_auth_token:
                self._send_otp_via_twilio(phone_number, message)
            else:
                logger.warning(
                    "No SMS provider configured - OTP %s NOT delivered for %s",
                    otp,
                    phone_number,
                )
        except httpx.TimeoutException as exc:
            logger.error("SMS delivery timed out for %s: %s", phone_number, exc)
            raise
        except httpx.HTTPError as exc:
            logger.error("SMS delivery failed for %s: %s", phone_number, exc)
            raise

        return otp


sms_service = SMSService()
