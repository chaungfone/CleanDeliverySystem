import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Set environment variables for the test
os.environ['DEBUG'] = 'true'
os.environ['SUPABASE_URL'] = 'http://example.com'
os.environ['SUPABASE_KEY'] = 'anon'
os.environ['SUPABASE_JWT_SECRET'] = 'secret'
os.environ['CORS_ORIGINS_JSON'] = '["http://localhost"]'  # Non-wildcard for testing

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

@pytest.fixture(scope="module")
def auth_headers():
    # In integration tests, we might want to get a real token from Supabase Auth
    # For now, we return a mock or expect a test environment setup
    return {"Authorization": "Bearer test-token"}
