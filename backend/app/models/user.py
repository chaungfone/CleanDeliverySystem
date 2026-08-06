from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class UserRole(str, Enum):
    CUSTOMER = "CUSTOMER"
    DRIVER = "DRIVER"
    ADMIN = "ADMIN"
    BRANCH_MANAGER = "BRANCH_MANAGER"


class UserBase(BaseModel):
    phone_number: str = Field(..., pattern=r"^\+?[0-9]{9,15}$")
    full_name: str = Field(..., min_length=1, max_length=255)
    branch_id: UUID | None = None


class UserCreate(UserBase):
    role: UserRole = UserRole.CUSTOMER


class UserUpdate(BaseModel):
    full_name: str | None = Field(None, min_length=1, max_length=255)
    role: UserRole | None = None


class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    role: UserRole
    created_at: datetime
