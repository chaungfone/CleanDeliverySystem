import os
import sys
from dotenv import load_dotenv
from supabase import create_client, Client

# Add the parent directory to sys.path to import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_connection():
    load_dotenv()

    url: str = os.getenv("SUPABASE_URL")
    key: str = os.getenv("SUPABASE_KEY")

    if not url or not key:
        print("Error: SUPABASE_URL or SUPABASE_KEY not found in .env")
        return

    print(f"Testing connection to: {url}")

    try:
        supabase: Client = create_client(url, key)
        # Try a simple select from the users table which we know should exist
        response = supabase.table("users").select("id", count="exact").limit(1).execute()
        print("Connection Successful!")
        print(f"Data received: {response.data}")
    except Exception as e:
        print(f"Connection Failed: {str(e)}")

if __name__ == "__main__":
    test_connection()
