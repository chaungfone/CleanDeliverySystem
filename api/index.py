import os
import sys
from pathlib import Path

_project_root = Path(__file__).resolve().parent.parent
_backend_dir = _project_root / "backend"
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

os.environ.setdefault("VERCEL", "1")

try:
    from mangum import Mangum
    from app.main import app

    handler = Mangum(app, lifespan="off")
except Exception as exc:  # pragma: no cover - boot guard for serverless platforms
    # The backend app imports Settings at module load time and requires the
    # Supabase credentials (SUPABASE_URL / SUPABASE_KEY / SUPABASE_JWT_SECRET).
    # If they are missing or are placeholders, the import raises and the
    # platform would otherwise answer every /api/* call with a generic 500.
    # Answer with a clear 503 diagnostic so the misconfiguration is visible in
    # the dashboard's error panel (the frontend surfaces the message as the
    # error "Details").
    import json

    _boot_error = str(exc)

    def handler(event, context):  # noqa: ANN001, ANN201
        return {
            "statusCode": 503,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(
                {
                    "success": False,
                    "error": {
                        "code": 503,
                        "message": (
                            "Backend configuration error. Missing required environment "
                            "variables: SUPABASE_URL, SUPABASE_KEY, SUPABASE_JWT_SECRET."
                        ),
                        "details": _boot_error,
                    },
                }
            ),
        }
