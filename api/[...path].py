import os
import sys
from pathlib import Path

_project_root = Path(__file__).resolve().parent.parent
_backend_dir = _project_root / "backend"
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

os.environ.setdefault("VERCEL", "1")

from mangum import Mangum
from app.main import app

handler = Mangum(app, lifespan="off")
