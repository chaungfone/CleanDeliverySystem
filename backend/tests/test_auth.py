"""JWT jti deny-list / revocation tests (offline, no live DB/network)."""
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app import main
from app.api.v1.endpoints import auth as auth_ep
from app.api.v1.endpoints.auth import _REFRESH_COOKIE
from app.core import security
from app.main import app


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
        self._eq.append((k, v)); return self

    def in_(self, k, vals):
        self._in_ = (k, {str(v) for v in vals}); return self

    def maybe_single(self):
        self._single = True; return self

    def single(self):
        self._single = True; return self

    def limit(self, n):
        return self

    def order(self, *a, **k):
        return self

    def insert(self, payload):
        self._action = "insert"; self._payload = payload; return self

    def update(self, payload):
        self._action = "update"; self._payload = payload; return self

    def upsert(self, payload, on_conflict=None):
        return self.insert(payload)

    def delete(self):
        self._action = "delete"; return self

    def execute(self):
        db = self._db
        if self._action == "insert":
            rows = db.apply_insert(self._table, self._payload)
            return _Res(rows if isinstance(rows, list) else [rows])
        if self._action == "update":
            db.apply_update(self._table, self._eq, self._payload); return _Res([])
        if self._action == "delete":
            db.apply_delete(self._table, self._eq); return _Res([])
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

    def upsert(self, payload, on_conflict=None):
        return _Builder(self._db, self._name).insert(payload)

    def delete(self):
        return _Builder(self._db, self._name).delete()


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
        rows = []
        items = payload if isinstance(payload, list) else [payload]
        for item in items:
            row = dict(item)
            row.setdefault("id", str(uuid4()))
            self.store[table].append(row)
            rows.append(row)
        return rows

    def apply_update(self, table, eq, payload):
        for r in self.store.get(table, []):
            if all(str(r.get(k)) == str(v) for k, v in eq):
                r.update(payload)

    def apply_delete(self, table, eq):
        self.store[table] = [
            r for r in self.store.get(table, [])
            if not all(str(r.get(k)) == str(v) for k, v in eq)
        ]


USER_ID = str(uuid4())


@pytest.fixture
def fake(monkeypatch):
    db = FakeDB()
    db.seed("users", [{
        "id": USER_ID, "phone_number": "09123456789", "full_name": "T",
        "role": "ADMIN", "branch_id": None, "created_at": 0,
    }])
    monkeypatch.setattr(auth_ep, "get_supabase_client", lambda: db)
    monkeypatch.setattr(security, "get_supabase_client", lambda: db)
    monkeypatch.setattr(main, "get_supabase_client", lambda: db)
    return db


def _login(client):
    otp = client.post("/api/v1/auth/request-otp", json={"phone_number": "09123456789"}).json()["debug_otp"]
    client.post("/api/v1/auth/verify-otp", json={"phone_number": "09123456789", "otp": otp})
    refresh = client.cookies.get(_REFRESH_COOKIE)
    payload = security._decode_token(refresh)
    return payload


def test_refresh_ok_when_not_revoked(fake):
    with TestClient(app) as c:
        _login(c)
        resp = c.post("/api/v1/auth/refresh-cookie")
        assert resp.status_code == 200
        assert "access_token" in resp.json()


def test_logout_revokes_jti_and_clears_cookie(fake):
    with TestClient(app) as c:
        payload = _login(c)
        jti = payload.get("jti")
        resp = c.post("/api/v1/auth/logout")
        assert resp.status_code == 200
        assert c.cookies.get(_REFRESH_COOKIE) is None
        rev = fake.store.get("revoked_tokens") or []
        assert any(r.get("jti") == jti for r in rev)


def test_revoked_jti_cannot_refresh(fake):
    with TestClient(app) as c:
        payload = _login(c)
        fake.apply_insert("revoked_tokens", {
            "jti": payload["jti"], "user_id": str(payload["sub"]), "expires_at": "2999-01-01T00:00:00+00:00",
        })
        resp = c.post("/api/v1/auth/refresh-cookie")
        assert resp.status_code == 401
        assert "revoked" in resp.json()["error"]["message"].lower()


def test_revoke_all_user_tokens_blocks_refresh(fake):
    with TestClient(app) as c:
        _login(c)
        security.revoke_all_user_tokens(USER_ID)
        resp = c.post("/api/v1/auth/refresh-cookie")
        assert resp.status_code == 401
        assert "revoked" in resp.json()["error"]["message"].lower()


def test_revoke_all_user_tokens_helper_inserts_marker(fake):
    security.revoke_all_user_tokens(USER_ID)
    rev = fake.store.get("revoked_tokens") or []
    assert any(r.get("jti") == f"user:{USER_ID}" for r in rev)