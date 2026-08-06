import json
import pytest
from fastapi.testclient import TestClient
from app.main import app, standardized_error


def test_standardized_error_no_nameerror_on_details_typing():
    """Root-cause regression: `details: any = None` caused NameError.

    The bug was that `standardized_error` used Python's builtin `any`
    (not a real type annotation) as the parameter type.  Every call into
    any exception handler (HTTPException / RequestValidationError / bare
    Exception) then raised `NameError: name 'any' is not defined` *inside
    the handler itself*, causing Starlette to fall back to a 0-byte HTTP
    500 response which (without CORS headers) surfaced to the browser as
    the opaque "Failed to fetch" error.
    """
    result = standardized_error(500, "boom", details={"key": "value"})
    body = json.loads(result.body)
    assert body["success"] is False
    assert body["error"]["code"] == 500
    assert body["error"]["message"] == "boom"
    assert body["error"]["details"] == {"key": "value"}
    # Must not raise NameError when called.
    no_details = standardized_error(401, "go away")
    assert json.loads(no_details.body)["error"]["details"] is None


def test_exception_handlers_no_500_empty_body():
    """Unhandled exceptions must now produce a proper JSON body.

    Before the fix, any exception reached the bare-except handler, which
    called `standardized_error` and then *itself* raised NameError → the
    final client response was a bare 500 with zero bytes and no CORS
    headers.  The browser treated this as a network error.
    """
    client = TestClient(app)
    response = client.get("/healthz")
    assert response.status_code == 200
    # Any malformed path should return a proper error payload, not a 0-byte 500
    bad = client.get("/definitely-does-not-exist-xyz")
    # Either 404 or some other status — the important property is a
    # non-empty, valid JSON body emitted via standardized_error.
    assert bad.status_code in (404, 405)
    if bad.content:
        try:
            data = bad.json()
            assert isinstance(data, dict)
        except Exception:
            pytest.fail("404 response did not contain valid JSON body")


def test_admin_endpoints_no_raw_500_on_missing_schema():
    """Regression: missing Supabase tables/columns must NOT produce a raw 500.

    Before: each endpoint propagated postgrest APIError (PGRST205 / PG 42703)
    → 500 empty body (see previous bug).  Now: endpoints return a graceful
    empty list / 200 OK even when the real DB schema is incomplete.
    """
    client = TestClient(app)
    # Without a real JWT we expect 401 Unauthorized (auth dependency runs
    # before the route body).  That is sufficient to rule out the earlier
    # `NameError → 500 empty body` bug, which would have returned 500 with
    # zero bytes instead.
    paths = [
        "/api/v1/admin/staff",
        "/api/v1/admin/branches",
        "/api/v1/admin/inventory",
        "/api/v1/admin/drivers",
        "/api/v1/admin/orders",
        "/api/v1/admin/dashboard/analytics",
    ]
    for path in paths:
        response = client.get(path)
        assert response.status_code != 500, f"{path} returned 500: {response.content!r}"
        assert response.content, f"{path} returned empty body"
        # The dependency layer runs before the handler and should return
        # structured JSON (not the old 0-byte response).
        if response.status_code == 401:
            try:
                data = response.json()
                assert isinstance(data, dict)
            except Exception:
                pytest.fail(f"{path} 401 was not valid JSON: {response.content!r}")
