import httpx
import json

BASE_URL = "http://127.0.0.1:8000/api/v1"

def test_login_flow():
    phone = "09692117187"
    
    # 1. Request OTP
    print(f"Requesting OTP for {phone}...")
    try:
        resp = httpx.post(f"{BASE_URL}/auth/request-otp", json={"phone_number": phone})
        print(f"Status: {resp.status_code}")
        print(f"Body: {resp.text}")
        if resp.status_code != 200:
            return
        
        data = resp.json()
        otp = data.get("debug_otp")
        if not otp:
            print("No debug_otp found. Check server logs for OTP.")
            return
        
        # 2. Verify OTP
        print(f"Verifying OTP {otp} for {phone}...")
        resp = httpx.post(f"{BASE_URL}/auth/verify-otp", json={"phone_number": phone, "otp": otp})
        print(f"Status: {resp.status_code}")
        print(f"Body: {resp.text}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_login_flow()
