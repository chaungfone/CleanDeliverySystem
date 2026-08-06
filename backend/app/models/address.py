from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AddressCreate(BaseModel):
    address_line: str = Field(..., min_length=1, max_length=255)
    township: str | None = Field(None, min_length=1, max_length=100)
    latitude: Decimal | None = Field(None, ge=-90, le=90)
    longitude: Decimal | None = Field(None, ge=-180, le=180)


class AddressUpdate(BaseModel):
    address_line: str | None = Field(None, min_length=1, max_length=255)
    township: str | None = Field(None, min_length=1, max_length=100)
    latitude: Decimal | None = Field(None, ge=-90, le=90)
    longitude: Decimal | None = Field(None, ge=-180, le=180)


class AddressResponse(AddressCreate):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    created_at: datetime
