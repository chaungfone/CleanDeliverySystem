
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.api.v1.endpoints.auth import _otp_store
import time

client = TestClient(app)

def test_request_otp_success():
    response = client.post("/api/v1/auth/request-otp", json={"phone_number": "09123456789"})
    assert response.status_code == 200
    assert "debug_otp" in response.json()
    assert response.json()["phone_number"] == "09123456789"

def test_request_otp_invalid_phone():
    response = client.post("/api/v1/auth/request-otp", json={"phone_number": "123"})
    assert response.status_code == 422 # Validation error

def test_verify_otp_success():
    # First request OTP
    resp = client.post("/api/v1/auth/request-otp", json={"phone_number": "09123456789"})
    otp = resp.json()["debug_otp"]
    
    # Then verify
    response = client.post("/api/v1/auth/verify-otp", json={"phone_number": "09123456789", "otp": otp})
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert "role" in response.json()

def test_verify_otp_wrong_code():
    client.post("/api/v1/auth/request-otp", json={"phone_number": "09123456789"})
    response = client.post("/api/v1/auth/verify-otp", json={"phone_number": "09123456789", "otp": "000000"})
    assert response.status_code == 400
    assert "incorrect" in response.json()["error"]["message"]

def test_verify_otp_expired():
    client.post("/api/v1/auth/request-otp", json={"phone_number": "09123456789"})
    # Manually expire the OTP
    from app.api.v1.endpoints.auth import _normalize_phone
    phone = _normalize_phone("09123456789")
    _otp_store[phone]["expires_at"] = time.time() - 1
    
    response = client.post("/api/v1/auth/verify-otp", json={"phone_number": "09123456789", "otp": "000000"})
    assert response.status_code == 400
    assert "expired" in response.json()["error"]["message"]

def test_verify_otp_no_request():
    response = client.post("/api/v1/auth/verify-otp", json={"phone_number": "09888888888", "otp": "123456"})
    assert response.status_code == 400
    assert "request a verification code first" in response.json()["error"]["message"]
