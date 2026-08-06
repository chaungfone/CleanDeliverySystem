import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


# --- Numeric non-negative enforcement ---
def test_product_price_type_annotations_enforce_non_negative():
    from app.models.product import ProductCreate

    with pytest.raises(Exception):
        ProductCreate(name="Test", price=-1)


def test_order_item_quantity_must_be_positive():
    from app.models.order import OrderItemCreate

    with pytest.raises(Exception):
        OrderItemCreate(
            product_id="00000000-0000-0000-0000-000000000000", quantity=0
        )


def test_iot_water_level_bounds_validation():
    # ge=0 le=100 enforced by the model
    from app.api.v1.endpoints.iot import IoTPing

    with pytest.raises(Exception):
        IoTPing(device_token="t", water_level=101)
    with pytest.raises(Exception):
        IoTPing(device_token="t", water_level=-1)


def test_order_status_and_payment_method_reject_arbitrary_strings():
    # OrderCreate.payment_method is a Pydantic enum -> free string rejected.
    from app.models.order import OrderCreate

    with pytest.raises(Exception):
        OrderCreate(
            address_id="00000000-0000-0000-0000-000000000000",
            payment_method="HACKED",
            items=[],
        )


def test_branch_validation_rejects_bad_lat_and_overflow_string():
    from app.api.v1.endpoints.admin import BranchCreate

    # Latitude out of range
    try:
        BranchCreate(name="x", address="y", latitude=120.0, longitude=10.0)
        failed = False
    except Exception:
        failed = True
    assert failed

    # name must have max_length (no payload) - ensure long string rejected
    try:
        BranchCreate(name="a" * 9999, address="y", latitude=10.0, longitude=10.0)
        failed = False
    except Exception:
        failed = True
    assert failed


def test_address_line_max_length():
    from app.models.address import AddressCreate

    try:
        AddressCreate(address_line="a" * 256)
        failed = False
    except Exception:
        failed = True
    assert failed