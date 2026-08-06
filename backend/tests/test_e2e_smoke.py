"""Offline E2E smoke for the 6 critical flows (no live DB/network required).

Recommended alternative (1): API/state-machine-level E2E using an in-memory fake
Supabase client, driving the real FastAPI route/service code deterministically.

Flows:
  1. Admin login (OTP verify -> ADMIN session + /auth/me)
  2. Order creation
  3. Order status -> DELIVERED (state machine)
  4. Non-admin 403
  5. Stock deduction on order placement
  6. Logout clears session cookie
"""
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app import main
from app.api.v1.endpoints import auth as auth_ep
from app.api.v1.endpoints import customer as customer_mod
from app.api.v1.endpoints.customer import place_order
from app.core import security
from app.main import app
from app.models.order import (
    OrderCreate,
    OrderItemCreate,
    OrderStatus,
    PaymentMethod,
)
from app.models.user import UserResponse, UserRole
from app.services.order_logic import validate_status_transition


class _Res:
    def __init__(self, data):
        self.data = data


class _Builder:
    def __init__(self, db, table):
        self._db = db
        self._table = table
        self._eq = []
        self._in_ = None
        self._payload = None
        self._action = None
        self._single = False

    def select(self, *cols, **kw):
        return self

    def eq(self, k, v):
        self._eq.append((k, v))
        return self

    def in_(self, k, vals):
        self._in_ = (k, {str(v) for v in vals})
        return self

    def maybe_single(self):
        self._single = True
        return self

    def single(self):
        self._single = True
        return self

    def limit(self, n):
        return self

    def order(self, *a, **k):
        return self

    def insert(self, payload):
        self._action = "insert"
        self._payload = payload
        return self

    def update(self, payload):
        self._action = "update"
        self._payload = payload
        return self

    def upsert(self, payload, on_conflict=None):
        return self.insert(payload)

    def delete(self):
        self._action = "delete"
        return self

    def execute(self):
        db = self._db
        if self._action == "insert":
            inserted = db.apply_insert(self._table, self._payload)
            return _Res(inserted if isinstance(inserted, list) else [inserted])
        if self._action == "update":
            db.apply_update(self._table, self._eq, self._payload)
            return _Res([])
        if self._action == "delete":
            db.apply_delete(self._table, self._eq)
            return _Res([])
        rows = db.scan(self._table, self._eq, self._in_)
        if self._single:
            return _Res(rows[0] if rows else None)
        return _Res(rows)


class _Table:
    def __init__(self, db, name):
        self._db = db
        self._name = name

    def select(self, *cols, **kw):
        return _Builder(self._db, self._name)

    def insert(self, payload):
        return _Builder(self._db, self._name).insert(payload)

    def update(self, payload):
        return _Builder(self._db, self._name).update(payload)

    def delete(self):
        return _Builder(self._db, self._name).delete()

    def upsert(self, payload, on_conflict=None):
        return _Builder(self._db, self._name).insert(payload)


class FakeDB:
    def __init__(self):
        self.store = {}

    def seed(self, table, rows):
        self.store[table] = [dict(r) for r in rows]

    def table(self, name):
        return _Table(self, name)

    def scan(self, table, eq, in_):
        rows = [dict(r) for r in self.store.get(table, [])]
        for k, v in eq:
            rows = [r for r in rows if str(r.get(k)) == str(v)]
        if in_:
            k, vals = in_
            rows = [r for r in rows if str(r.get(k)) in vals]
        return rows

    def apply_insert(self, table, payload):
        self.store.setdefault(table, [])
        if isinstance(payload, list):
            new = []
            for item in payload:
                row = dict(item)
                row.setdefault("id", str(uuid4()))
                self.store[table].append(row)
                new.append(row)
            return new
        row = dict(payload)
        row.setdefault("id", str(uuid4()))
        self.store[table].append(row)
        return row

    def apply_update(self, table, eq, payload):
        for r in self.store.get(table, []):
            if all(str(r.get(k)) == str(v) for k, v in eq):
                r.update(payload)

    def apply_delete(self, table, eq):
        self.store[table] = [
            r for r in self.store.get(table, [])
            if not all(str(r.get(k)) == str(v) for k, v in eq)
        ]


CUSTOMER_ID = str(uuid4())
DRIVER_ID = str(uuid4())
ADMIN_ID = str(uuid4())
PRODUCT_ID = str(uuid4())
ADDR_ID = str(uuid4())


@pytest.fixture
def fake(monkeypatch):
    db = FakeDB()
    db.seed("users", [
        {"id": CUSTOMER_ID, "phone_number": "0911112222", "full_name": "Cust",
         "role": "CUSTOMER", "branch_id": None, "created_at": 0},
    ])
    db.seed("products", [
        {"id": PRODUCT_ID, "name": "Bottle", "price": "1000", "stock_quantity": 10},
    ])
    db.seed("addresses", [
        {"id": ADDR_ID, "user_id": CUSTOMER_ID, "address_line": "123 Yangon"},
    ])
    db.seed("orders", [
        {"id": str(uuid4()), "customer_id": CUSTOMER_ID, "driver_id": DRIVER_ID,
         "status": "CONFIRMED", "total_amount": "1000", "payment_status": "PENDING",
         "payment_method": "COD", "empty_bottles_returned": 0, "created_at": 0},
    ])
    monkeypatch.setattr(main, "get_supabase_client", lambda: db)
    monkeypatch.setattr(security, "get_supabase_client", lambda: db)
    monkeypatch.setattr(auth_ep, "get_supabase_client", lambda: db)
    monkeypatch.setattr(customer_mod, "get_supabase_client", lambda: db)
    return db


def _user(uid: str, role: UserRole) -> UserResponse:
    return UserResponse(
        id=uid, phone_number="09123456789", full_name="T",
        role=role, branch_id=None, created_at=datetime.now(timezone.utc),
    )


# 1) Admin login ------------------------------------------------
def test_flow1_admin_login(fake):
    phone = "09999999999"
    fake.store["users"] = [{"id": ADMIN_ID, "phone_number": phone, "full_name": "Admin",
                            "role": "ADMIN", "branch_id": None, "created_at": 0}]
    with TestClient(app) as c:
        otp = c.post("/api/v1/auth/request-otp", json={"phone_number": phone}).json()["debug_otp"]
        login = c.post("/api/v1/auth/verify-otp", json={"phone_number": phone, "otp": otp})
        assert login.status_code == 200
        assert login.json()["role"] == "ADMIN"
        me = c.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {login.json()['access_token']}"})
        assert me.status_code == 200
        assert me.json()["role"] == "ADMIN"


# 2 + 5) Order creation deducts stock ---------------------------
def test_flow2_and_5_order_creation_deducts_stock(fake):
    before = fake.store["products"][0]["stock_quantity"]
    payload = OrderCreate(
        address_id=ADDR_ID,
        payment_method=PaymentMethod.COD,
        empty_bottles_returned=0,
        items=[OrderItemCreate(product_id=PRODUCT_ID, quantity=3)],
    )
    order = place_order(payload, _user(CUSTOMER_ID, UserRole.CUSTOMER))
    assert order["items"] is not None
    stock_after = fake.store["products"][0]["stock_quantity"]
    assert stock_after == before - 3


# 3) Status -> DELIVERED via state machine ----------------------
def test_flow3_status_delivered():
    # Full valid path to DELIVERED per the state machine + role permissions.
    assert validate_status_transition(OrderStatus.ASSIGNED, OrderStatus.IN_TRANSIT, "DRIVER") is True
    assert validate_status_transition(OrderStatus.IN_TRANSIT, OrderStatus.DELIVERED, "DRIVER") is True
    # Cannot jump PENDING -> DELIVERED (not in the state machine) -> 400
    with pytest.raises(HTTPException):
        validate_status_transition(OrderStatus.PENDING, OrderStatus.DELIVERED, "DRIVER")


# 4) Non-admin 403 ----------------------------------------------
def test_flow4_non_admin_forbidden():
    checker = security.require_roles(UserRole.ADMIN)
    with pytest.raises(HTTPException) as exc:
        checker(_user(CUSTOMER_ID, UserRole.CUSTOMER))
    assert exc.value.status_code == 403


# 6) Logout clears session cookie -------------------------------
def test_flow6_logout_clears_session(fake):
    phone = "09888888888"
    fake.store["users"] = [{"id": ADMIN_ID, "phone_number": phone, "full_name": "A",
                            "role": "ADMIN", "branch_id": None, "created_at": 0}]
    with TestClient(app) as c:
        otp = c.post("/api/v1/auth/request-otp", json={"phone_number": phone}).json()["debug_otp"]
        c.post("/api/v1/auth/verify-otp", json={"phone_number": phone, "otp": otp})
        assert c.cookies.get("cd_refresh_token") is not None
        resp = c.post("/api/v1/auth/logout")
        assert resp.status_code == 200
        assert c.cookies.get("cd_refresh_token") is None
