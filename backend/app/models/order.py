from datetime import datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class OrderStatus(str, Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    ASSIGNED = "ASSIGNED"
    IN_TRANSIT = "IN_TRANSIT"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"


class PaymentStatus(str, Enum):
    PENDING = "PENDING"
    PAID = "PAID"
    FAILED = "FAILED"


class PaymentMethod(str, Enum):
    COD = "COD"
    KPAY = "KPAY"
    WAVE_PAY = "WAVE_PAY"
    OTHER = "OTHER"


class OrderItemCreate(BaseModel):
    product_id: UUID
    quantity: int = Field(..., gt=0)
    unit_price: Decimal | None = Field(None, ge=0)


class OrderItemSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    order_id: UUID
    product_id: UUID
    quantity: int
    unit_price: Decimal


class OrderCreate(BaseModel):
    address_id: UUID
    payment_method: PaymentMethod = PaymentMethod.COD
    empty_bottles_returned: int = Field(0, ge=0)
    items: list[OrderItemCreate] = Field(..., min_length=1)


class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    customer_id: UUID
    driver_id: UUID | None
    branch_id: UUID | None
    address_id: UUID
    status: OrderStatus
    total_amount: Decimal
    payment_status: PaymentStatus
    payment_method: PaymentMethod
    empty_bottles_returned: int
    created_at: datetime
    items: list[OrderItemSchema] = Field(default_factory=list)
