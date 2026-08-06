
from app.core import db


def test_to_asyncpg_url_appends_prepared_statement_cache_size_for_pooler():
    raw = "postgresql://postgres:pw@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres?pgbouncer=true"
    converted = db._to_asyncpg_url(raw)
    assert converted.startswith("postgresql+asyncpg://")
    assert "prepared_statement_cache_size=0" in converted


def test_is_pooler_url_true_for_pooler_host_and_port():
    raw = "postgresql://user:pw@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres"
    assert db.is_pooler_url(raw) is True


def test_is_pooler_url_false_for_direct_db():
    raw = "postgresql://postgres:pw@db.eettoiqgeecfnjbbuyni.supabase.co:5432/postgres"
    assert db.is_pooler_url(raw) is False

def test_to_asyncpg_url_appends_prepared_statement_cache_size_when_flag_true(monkeypatch):
    # Explicit flag overrides URL heuristics
    monkeypatch.setattr(db.settings, "PGBOUNCER_TRANSACTION_POOLING", True)
    raw = "postgresql://postgres:pw@db.example.com:5432/db"  # direct URL
    converted = db._to_asyncpg_url(raw)
    assert converted.startswith("postgresql+asyncpg://")
    assert "prepared_statement_cache_size=0" in converted

def test_pool_class_for_url_returns_nullpool_when_flag_true(monkeypatch):
    monkeypatch.setattr(db.settings, "PGBOUNCER_TRANSACTION_POOLING", True)
    raw = "postgresql://postgres:pw@db.example.com:5432/db"  # direct URL
    if db.SQLALCHEMY_AVAILABLE:
        assert db.pool_class_for_url(raw) is db.NullPool
    else:
        assert db.pool_class_for_url(raw) == "NullPool"


def test_to_asyncpg_url_no_cache_param_when_flag_false_and_direct_url(monkeypatch):
    # Explicit flag disabled + direct (non-pooler) URL -> no prepared statement tweak.
    monkeypatch.setattr(db.settings, "PGBOUNCER_TRANSACTION_POOLING", False)
    raw = "postgresql://postgres:pw@db.example.com:5432/db"  # direct URL
    converted = db._to_asyncpg_url(raw)
    assert converted.startswith("postgresql+asyncpg://")
    assert "prepared_statement_cache_size" not in converted


def test_pool_class_for_url_returns_queuepool_when_flag_false_and_direct_url(monkeypatch):
    monkeypatch.setattr(db.settings, "PGBOUNCER_TRANSACTION_POOLING", False)
    raw = "postgresql://postgres:pw@db.example.com:5432/db"  # direct URL
    if db.SQLALCHEMY_AVAILABLE:
        assert db.pool_class_for_url(raw) is db.QueuePool
    else:
        assert db.pool_class_for_url(raw) == "QueuePool"

