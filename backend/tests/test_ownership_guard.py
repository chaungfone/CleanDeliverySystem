from datetime import datetime, timezone
from uuid import UUID

import pytest
from fastapi import HTTPException

from app.core import security
from app.models.user import UserResponse, UserRole


class _FakeExecute:
    def __init__(self, data):
        self.data = data


class _FakeQuery:
    def __init__(self, row):
        self._row = row

    def select(self, *args, **kwargs):
        return self

    def eq(self, *args, **kwargs):
        return self

    def maybe_single(self):
        return self

    def execute(self):
        return _FakeExecute(self._row)


class _FakeTable:
    def __init__(self, row):
        self._row = row

    def select(self, *args, **kwargs):
        return _FakeQuery(self._row)


class _FakeClient:
    def __init__(self, row):
        self._row = row

    def table(self, name):
        return _FakeTable(self._row)


def _user(uid: str, role: UserRole) -> UserResponse:
    return UserResponse(
        id=UUID(uid),
        phone_number="09123456789",
        full_name="Test",
        role=role,
        branch_id=None,
        created_at=datetime.now(timezone.utc),
    )


ORDER_ID = "11111111-1111-1111-1111-111111111111"
OWNER = "22222222-2222-2222-2222-222222222222"
OTHER = "33333333-3333-3333-3333-333333333333"


def _order_row(customer_id: str) -> dict:
    return {
        "id": ORDER_ID,
        "customer_id": customer_id,
        "driver_id": None,
        "status": "PENDING",
    }


def test_customer_owner_can_access(monkeypatch):
    monkeypatch.setattr(
        security, "get_supabase_client", lambda: _FakeClient(_order_row(OWNER))
    )
    order = security.require_owner_or_admin(UUID(ORDER_ID), _user(OWNER, UserRole.CUSTOMER))
    assert order["id"] == ORDER_ID


def test_customer_non_owner_gets_403(monkeypatch):
    monkeypatch.setattr(
        security, "get_supabase_client", lambda: _FakeClient(_order_row(OWNER))
    )
    with pytest.raises(HTTPException) as exc:
        security.require_owner_or_admin(UUID(ORDER_ID), _user(OTHER, UserRole.CUSTOMER))
    assert exc.value.status_code == 403
    assert "Not your order" in str(exc.value.detail)


def test_admin_can_access_any_order(monkeypatch):
    monkeypatch.setattr(
        security, "get_supabase_client", lambda: _FakeClient(_order_row(OWNER))
    )
    order = security.require_owner_or_admin(UUID(ORDER_ID), _user(OTHER, UserRole.ADMIN))
    assert order["customer_id"] == OWNER


def test_branch_manager_can_access_any_order(monkeypatch):
    monkeypatch.setattr(
        security, "get_supabase_client", lambda: _FakeClient(_order_row(OWNER))
    )
    order = security.require_owner_or_admin(
        UUID(ORDER_ID), _user(OTHER, UserRole.BRANCH_MANAGER)
    )
    assert order["id"] == ORDER_ID


def test_missing_order_gets_404(monkeypatch):
    monkeypatch.setattr(security, "get_supabase_client", lambda: _FakeClient(None))
    with pytest.raises(HTTPException) as exc:
        security.require_owner_or_admin(UUID(ORDER_ID), _user(OWNER, UserRole.CUSTOMER))
    assert exc.value.status_code == 404


DRIVER = "44444444-4444-4444-4444-444444444444"


def _assigned_order_row(driver_id=DRIVER) -> dict:
    return {
        "id": ORDER_ID,
        "customer_id": OWNER,
        "driver_id": driver_id,
        "status": "ASSIGNED",
    }


def test_driver_can_access_assigned_order(monkeypatch):
    monkeypatch.setattr(
        security, "get_supabase_client", lambda: _FakeClient(_assigned_order_row())
    )
    order = security.require_driver_or_admin(UUID(ORDER_ID), _user(DRIVER, UserRole.DRIVER))
    assert order["driver_id"] == DRIVER


def test_driver_gets_403_for_order_assigned_to_other(monkeypatch):
    monkeypatch.setattr(
        security, "get_supabase_client", lambda: _FakeClient(_assigned_order_row())
    )
    other_driver = "55555555-5555-5555-5555-555555555555"
    with pytest.raises(HTTPException) as exc:
        security.require_driver_or_admin(UUID(ORDER_ID), _user(other_driver, UserRole.DRIVER))
    assert exc.value.status_code == 403


def test_driver_admin_can_access_any_assigned_order(monkeypatch):
    monkeypatch.setattr(
        security, "get_supabase_client", lambda: _FakeClient(_assigned_order_row())
    )
    order = security.require_driver_or_admin(UUID(ORDER_ID), _user(OTHER, UserRole.ADMIN))
    assert order["driver_id"] == DRIVER


def test_driver_guard_404_when_order_unassigned(monkeypatch):
    monkeypatch.setattr(
        security, "get_supabase_client", lambda: _FakeClient(_assigned_order_row(driver_id=None))
    )
    with pytest.raises(HTTPException) as exc:
        security.require_driver_or_admin(UUID(ORDER_ID), _user(DRIVER, UserRole.DRIVER))
    assert exc.value.status_code == 404


def test_driver_guard_404_for_missing_order(monkeypatch):
    monkeypatch.setattr(security, "get_supabase_client", lambda: _FakeClient(None))
    with pytest.raises(HTTPException) as exc:
        security.require_driver_or_admin(UUID(ORDER_ID), _user(DRIVER, UserRole.DRIVER))
    assert exc.value.status_code == 404
