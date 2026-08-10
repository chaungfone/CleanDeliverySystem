import json
import os
import sys
import traceback
from pathlib import Path

_API_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _API_DIR.parent
_BACKEND_DIR = _PROJECT_ROOT / "backend"
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

os.environ.setdefault("VERCEL", "1")
os.environ.setdefault("PYTHONUNBUFFERED", "1")

try:
    from mangum import Mangum
    from app.main import app
    _handler = Mangum(app, lifespan="off")
except Exception as _exc:  # noqa: BLE001 - startup diagnostic
    _tb = traceback.format_exc()
    print("[VERCEL-FN-STARTUP] Import failed:", file=sys.stderr)
    print(_tb, file=sys.stderr)

    def _handler(event, context):
        path = ""
        try:
            if isinstance(event, dict):
                path = event.get("rawPath") or event.get("path") or ""
        except Exception:
            path = ""
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
                    "path": path,
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


def handler(event, context):
    return _handler(event, context)
