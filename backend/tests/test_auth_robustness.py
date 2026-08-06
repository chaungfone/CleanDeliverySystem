import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.api.v1.endpoints.auth import _otp_store, _normalize_phone
import time

client = TestClient(app)

def test_normalize_phone_robustness():
    assert _normalize_phone("+959692117187") == "09692117187"
    assert _normalize_phone("959692117187") == "09692117187"
    assert _normalize_phone("09692117187") == "09692117187"
    assert _normalize_phone("9692117187") == "09692117187"
    assert _normalize_phone("+95 9 692117187") == "09692117187"

def test_request_otp_invalid_phone():
    response = client.post("/api/v1/auth/request-otp", json={"phone_number": "123"})
    assert response.status_code == 422
    assert response.json()["success"] is False
    assert "validation" in response.json()["error"]["message"].lower()

def test_verify_otp_wrong_code():
    phone = "09692117187"
    # Request OTP first
    client.post("/api/v1/auth/request-otp", json={"phone_number": phone})
    
    # Verify with wrong code
    response = client.post("/api/v1/auth/verify-otp", json={"phone_number": phone, "otp": "000000"})
    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert "incorrect" in data["error"]["message"].lower()

def test_verify_otp_expired():
    phone = "09692117188"
    _otp_store[_normalize_phone(phone)] = {
        "otp": "123456",
        "expires_at": time.time() - 10,  # Expired 10s ago
        "full_name": "Test User"
    }
    
    response = client.post("/api/v1/auth/verify-otp", json={"phone_number": phone, "otp": "123456"})
    assert response.status_code == 400
    assert "expired" in response.json()["error"]["message"].lower()

def test_verify_otp_missing_request():
    response = client.post("/api/v1/auth/verify-otp", json={"phone_number": "09111111111", "otp": "123456"})
    assert response.status_code == 400
    assert "request a verification code first" in response.json()["error"]["message"].lower()
