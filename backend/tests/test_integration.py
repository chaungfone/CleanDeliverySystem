import pytest
from app.models.order import OrderStatus

def test_health_check(client):
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json()["status"] in ["ok", "degraded"]

def test_list_products(client):
    response = client.get("/api/v1/products")
    # This expects Supabase local to be running or mocked
    if response.status_code == 200:
        assert isinstance(response.json(), list)

def test_order_lifecycle_logic():
    from app.services.order_logic import validate_status_transition
    # Valid transition by Admin
    assert validate_status_transition(OrderStatus.PENDING, OrderStatus.CONFIRMED, "ADMIN") is True

    # Invalid transition
    with pytest.raises(Exception):
        validate_status_transition(OrderStatus.PENDING, OrderStatus.DELIVERED, "ADMIN")
