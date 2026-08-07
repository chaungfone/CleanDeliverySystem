import os
import sys
import importlib
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from fastapi.testclient import TestClient

def test_rate_limiter_enforced_in_production():
    'Test that rate limiting is enforced when DEBUG=false.'
    # Override environment variables for this test
    os.environ['DEBUG'] = 'false'
    os.environ['SUPABASE_URL'] = 'http://example.com'
    os.environ['SUPABASE_KEY'] = 'anon'
    os.environ['SUPABASE_JWT_SECRET'] = 'secret'
    # Clear cached modules
    modules_to_clear = [m for m in sys.modules.keys() if m.startswith('app')]
    for m in modules_to_clear:
        del sys.modules[m]
    from app.main import app
    client = TestClient(app)
    # The /request-otp endpoint is limited to 5/minute by IP+phone
    phone = '+959123456789'
    # Make 5 requests (should be allowed)
    for i in range(5):
        response = client.post(
            '/api/v1/auth/request-otp',
            json={'phone_number': phone}
        )
        assert response.status_code == 200, f'Request {i+1} failed: {response.text}'
    # The 6th request should be rate limited (429)
    response = client.post(
        '/api/v1/auth/request-otp',
        json={'phone_number': phone}
    )
    assert response.status_code == 429, f'Expected 429, got {response.status_code}: {response.text}'
    # Ensure the response contains the expected error detail
    assert 'Rate limit exceeded' in response.json().get('error', '')
import pytest
from pydantic import ValidationError
from app.core.config import Settings

def test_cors_wildcard_rejected_in_production():
    'Test that setting CORS_ORIGINS to [\"*\"] raises RuntimeError when DEBUG=false.'
    # We need to create a Settings instance with DEBUG=False and CORS_ORIGINS=['*']
    # We'll set the environment variables accordingly and then try to instantiate Settings.
    import os
    import importlib
    os.environ['DEBUG'] = 'false'
    os.environ['CORS_ORIGINS_JSON'] = '["*"]'  # This is a JSON array with one element: '*'
    os.environ['SUPABASE_URL'] = 'http://example.com'
    os.environ['SUPABASE_KEY'] = 'anon'
    os.environ['SUPABASE_JWT_SECRET'] = 'secret'
    # Try to reload the config module to trigger module-level validation
    try:
        import app.core.config
        importlib.reload(app.core.config)
        pytest.fail("Expected RuntimeError to be raised during reload")
    except RuntimeError as e:
        # Optionally, check the message
        assert "CORS_ORIGINS cannot contain '*'" in str(e)
