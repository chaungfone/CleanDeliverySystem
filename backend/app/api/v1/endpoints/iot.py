from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.core.database import get_supabase_client
from app.services.iot import process_iot_ping

router = APIRouter()

class IoTPing(BaseModel):
    device_token: str = Field(..., min_length=1, max_length=255)
    water_level: int = Field(..., ge=0, le=100)

@router.post("/ingest")
async def ingest_sensor_data(payload: IoTPing):
    """
    Endpoint for IoT devices (ESP32/Pi) to report water levels.
    """
    db = get_supabase_client()
    await process_iot_ping(db, payload.device_token, payload.water_level)
    return {"status": "received"}
