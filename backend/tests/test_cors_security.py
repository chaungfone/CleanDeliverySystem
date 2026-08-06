import pytest

from app.core.config import Settings
from fastapi.testclient import TestClient


def test_production_refuses_wildcard_origins(monkeypatch):
    monkeypatch.setenv("DEBUG", "false")
    monkeypatch.setenv("CORS_ORIGINS_JSON", '["*"]')
    with pytest.raises(RuntimeError):
        Settings().validate_secrets()


def test_production_allows_explicit_origins(monkeypatch):
    monkeypatch.setenv("DEBUG", "false")
    monkeypatch.setenv(
        "CORS_ORIGINS_JSON",
        '["https://admin.example.com", "capacitor://localhost"]',
    )
    s = Settings()
    assert s.CORS_ORIGINS == [
        "https://admin.example.com",
        "capacitor://localhost",
    ]
    # Should not raise
    s.validate_secrets()


def test_cors_rejects_disallowed_origin(monkeypatch):
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware

    test_app = FastAPI()

    @test_app.get("/healthz")
    def healthz():
        return {"status": "ok"}

    test_app.add_middleware(
        CORSMiddleware,
        allow_origins=["https://admin.example.com"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Requested-With"],
    )

    with TestClient(test_app) as client:
        # Allowed origin gets CORS headers
        resp_allowed = client.options(
            "/healthz",
            headers={
                "Origin": "https://admin.example.com",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert "access-control-allow-origin" in resp_allowed.headers

        # Disallowed origin gets NO CORS allow-origin header
        resp = client.options(
            "/healthz",
            headers={
                "Origin": "https://evil-attacker.com",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert "access-control-allow-origin" not in resp.headers