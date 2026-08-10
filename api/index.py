import copy
import json
import os
import sys
import traceback
from pathlib import Path
from typing import Any

_API_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _API_DIR.parent
_BACKEND_DIR = _PROJECT_ROOT / "backend"
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

os.environ.setdefault("VERCEL", "1")
os.environ.setdefault("PYTHONUNBUFFERED", "1")


def _extract_original_path(event: Any) -> str:
    """
    Recover the ORIGINAL request path the user/frontend sent BEFORE any
    Vercel rewrite rules ran. Vercel forwards API requests to this exact
    file via `rewrites: [ { source: '/api/:path*', dest: '/api/index' } ]`
    and, by default, overwrites event.path / rawPath /
    requestContext.http.path with the rewritten destination ("/api/index"),
    which FastAPI can never match to "/api/v1/...".

    To defeat that we try, in order of preference:
      1. x-vercel-original-url / x-forwarded-uri headers  (set by Vercel edge)
      2. event.rawPath
      3. event.requestContext.http.path
      4. event.requestContext.path
      5. event.path
    and keep the FIRST value that starts with "/" and still looks like a
    real URL path (not the rewritten "/api/index").
    """
    if not isinstance(event, dict):
        return "/"

    headers = event.get("headers") or {}
    if isinstance(headers, dict):
        for h in (
            "x-vercel-original-url",
            "x-now-original-url",
            "x-forwarded-uri",
        ):
            v = headers.get(h)
            if isinstance(v, str) and v:
                path_only = v.split("?", 1)[0]
                if path_only.startswith("/") and path_only != "/api/index":
                    return path_only

    # rawPath / requestContext.http.path / requestContext.path / path
    candidates: list[str] = []
    for key in ("rawPath", "raw_path"):
        v = event.get(key)
        if isinstance(v, str) and v.startswith("/"):
            candidates.append(v)
    rc = event.get("requestContext") or {}
    if isinstance(rc, dict):
        http = rc.get("http") or {}
        if isinstance(http, dict):
            v = http.get("path")
            if isinstance(v, str) and v.startswith("/"):
                candidates.append(v)
        v = rc.get("path")
        if isinstance(v, str) and v.startswith("/"):
            candidates.append(v)
    v = event.get("path")
    if isinstance(v, str) and v.startswith("/"):
        candidates.append(v)

    # Prefer the first candidate that is NOT the rewritten /api/index sentinel.
    for c in candidates:
        if c != "/api/index":
            return c
    return candidates[0] if candidates else "/"


def _ensure_leading_slash(path: str) -> str:
    if not path:
        return "/"
    if not path.startswith("/"):
        return "/" + path
    return path


def _normalize_event_paths(event: Any) -> Any:
    """
    Returns a SHALLOW COPY of `event` with every location Mangum 0.17 /
    Starlette might consult for the request path overwritten to the
    recovered ORIGINAL path. Using a copy guarantees the raw event is not
    mutated for any other consumer.
    """
    if not isinstance(event, dict):
        return event
    original = _ensure_leading_slash(_extract_original_path(event))

    evt = copy.copy(event)
    evt["rawPath"] = original
    evt["path"] = original

    rc = evt.get("requestContext")
    if isinstance(rc, dict):
        new_rc = copy.copy(rc)
        http = new_rc.get("http")
        if isinstance(http, dict):
            new_http = copy.copy(http)
            new_http["path"] = original
            new_rc["http"] = new_http
        new_rc["path"] = original
        evt["requestContext"] = new_rc
    return evt


def _safe_print_event_summary(event: Any) -> None:
    try:
        if not isinstance(event, dict):
            return
        headers = event.get("headers") or {}
        print(
            "[VERCEL-FN-EVENT] "
            + json.dumps(
                {
                    "path": event.get("path"),
                    "rawPath": event.get("rawPath"),
                    "rc_path": (event.get("requestContext") or {}).get("path")
                    if isinstance(event.get("requestContext"), dict)
                    else None,
                    "http_path": ((event.get("requestContext") or {}).get("http") or {}).get("path")
                    if isinstance(event.get("requestContext"), dict)
                    and isinstance((event.get("requestContext") or {}).get("http"), dict)
                    else None,
                    "x-vercel-original-url": headers.get("x-vercel-original-url")
                    if isinstance(headers, dict)
                    else None,
                    "host": headers.get("host") if isinstance(headers, dict) else None,
                },
                default=str,
            )
        )
    except Exception:  # noqa: BLE001 - diagnostics must not break the request
        pass


try:
    from mangum import Mangum
    from app.main import app
    _mangum = Mangum(app, lifespan="off")

    def _handler(event: Any, context: Any) -> Any:
        _safe_print_event_summary(event)
        normalized = _normalize_event_paths(event)
        resolved = _extract_original_path(normalized)
        print(f"[VERCEL-FN-ROUTE] resolved_request_path={resolved}")
        return _mangum(normalized, context)

except Exception as _exc:  # noqa: BLE001 - startup diagnostic
    _tb = traceback.format_exc()
    print("[VERCEL-FN-STARTUP] Import failed:", file=sys.stderr)
    print(_tb, file=sys.stderr)

    def _handler(event: Any, context: Any) -> Any:
        resolved = _extract_original_path(event) if isinstance(event, dict) else ""
        body = {
            "success": False,
            "error": {
                "code": 500,
                "message": "Backend failed to start on Vercel",
                "details": {
                    "type": type(_exc).__name__,
                    "error": str(_exc),
                    "traceback": _tb.splitlines(),
                    "cwd": str(Path.cwd()),
                    "sys_path": sys.path,
                    "path": resolved,
                },
            },
        }
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps(body, default=str),
        }


def handler(event: Any, context: Any) -> Any:
    """Public entrypoint used by the Vercel Python runtime."""
    return _handler(event, context)
