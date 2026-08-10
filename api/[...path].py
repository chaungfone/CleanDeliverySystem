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
    Given a Vercel/Lambda event, reliably extract the ORIGINAL request path
    the user typed into the browser or frontend sent via fetch().

    Order of candidates (most likely to be unmodified first):
      1. event.headers["x-vercel-original-url"] / x-now-original-url
      2. event["rawPath"]              (API Gateway v2 / HTTP API style)
      3. event["requestContext"]["http"]["path"]
      4. event["requestContext"]["path"]
      5. event["path"]                 (API Gateway v1 - MAY be rewritten to
                                         "/api/index" by a rewrite rule)
    Falls back to "/" when nothing is available.
    Only the PATH portion is returned (query string stripped).
    """
    if not isinstance(event, dict):
        return "/"

    raw_header_url = None
    headers = event.get("headers") or {}
    if isinstance(headers, dict):
        for h in (
            "x-vercel-original-url",
            "x-now-original-url",
            "x-forwarded-uri",
        ):
            v = headers.get(h)
            if v and isinstance(v, str):
                raw_header_url = v
                break
    if raw_header_url:
        path_only = raw_header_url.split("?", 1)[0]
        if path_only.startswith("/"):
            return path_only

    for key in ("rawPath", "raw_path"):
        v = event.get(key)
        if isinstance(v, str) and v.startswith("/"):
            return v

    rc = event.get("requestContext") or {}
    if isinstance(rc, dict):
        http = rc.get("http") or {}
        if isinstance(http, dict):
            v = http.get("path")
            if isinstance(v, str) and v.startswith("/"):
                return v
        v = rc.get("path")
        if isinstance(v, str) and v.startswith("/"):
            return v

    v = event.get("path")
    if isinstance(v, str) and v.startswith("/"):
        return v

    return "/"


def _ensure_path_starts_with_api(path: str) -> str:
    """
    The FastAPI router is mounted under settings.API_V1_PREFIX ("/api/v1")
    and also exposes "/docs" and "/healthz" at the root.  As long as the
    path starts with "/" we hand it through as-is; this helper just guards
    against very broken rewrites that drop the leading slash.
    """
    if not path:
        return "/"
    if not path.startswith("/"):
        return "/" + path
    return path


def _normalize_event_for_mangum(event: Any) -> Any:
    """
    Mutate a COPY of the event so Mangum -> FastAPI definitely sees the
    ORIGINAL request path and not whatever Vercel rewrites did (e.g. to
    "/api/index" or "/api/[...path]").

    Mangum 0.17 primarily looks at event["rawPath"] for HTTP API (v2)
    events, but older consumers look at event["path"].  We overwrite BOTH
    on a shallow copy so the original event dict is not touched for other
    consumers downstream (e.g. context extraction).
    """
    if not isinstance(event, dict):
        return event

    original = _extract_original_path(event)
    normalized = _ensure_path_starts_with_api(original)

    evt = copy.copy(event)
    evt["rawPath"] = normalized
    evt["path"] = normalized

    rc = evt.get("requestContext")
    if isinstance(rc, dict):
        new_rc = copy.copy(rc)
        http = new_rc.get("http")
        if isinstance(http, dict):
            new_http = copy.copy(http)
            new_http["path"] = normalized
            new_rc["http"] = new_http
        new_rc["path"] = normalized
        evt["requestContext"] = new_rc

    return evt


def _safe_print_json_event(event: Any) -> None:
    try:
        print(
            "[VERCEL-FN-EVENT] path_candidates="
            + json.dumps(
                {
                    "headers": {
                        k: v
                        for k, v in (event.get("headers") or {}).items()
                        if isinstance(k, str)
                        and k.lower()
                        in {
                            "x-vercel-original-url",
                            "x-now-original-url",
                            "host",
                        }
                    },
                    "rawPath": event.get("rawPath") if isinstance(event, dict) else None,
                    "path": event.get("path") if isinstance(event, dict) else None,
                    "rc": event.get("requestContext") if isinstance(event, dict) else None,
                },
                default=str,
            )
        )
    except Exception:  # noqa: BLE001 - diagnostic code must never break the request
        pass


try:
    from mangum import Mangum
    from app.main import app
    _mangum = Mangum(app, lifespan="off")

    def _handler(event: Any, context: Any) -> Any:
        _safe_print_json_event(event)
        normalized_event = _normalize_event_for_mangum(event)
        resolved = _extract_original_path(normalized_event)
        print(f"[VERCEL-FN-ROUTE] resolved_path={resolved}")
        return _mangum(normalized_event, context)

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
    return _handler(event, context)
