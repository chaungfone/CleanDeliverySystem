import httpx

BASE_URL = "http://127.0.0.1:8000/api/v1"

def test_wrong_otp():
    phone = "09692117187"
    print(f"Requesting OTP for {phone}...")
    resp = httpx.post(f"{BASE_URL}/auth/request-otp", json={"phone_number": phone})
    print(f"Status: {resp.status_code}")
    
    print("Verifying with WRONG OTP 000000...")
    resp = httpx.post(f"{BASE_URL}/auth/verify-otp", json={"phone_number": phone, "otp": "000000"})
    print(f"Status: {resp.status_code}")
    print(f"Body: {resp.text}")

if __name__ == "__main__":
    test_wrong_otp()
