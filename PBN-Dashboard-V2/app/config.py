import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

DB_PATH = os.getenv("DB_PATH", str(BASE_DIR / "pbn_matrix.db"))
STATIC_DIR = os.getenv("STATIC_DIR", str(BASE_DIR / "static"))
PLUGIN_FILE = os.getenv("PLUGIN_FILE", str(BASE_DIR / "pbn-manager.php"))

JWT_SECRET = os.getenv("JWT_SECRET", "pbn-matrix-secret-2026-v2-super-secure")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_DAYS = 7

PORT = int(os.getenv("PORT", "5555"))
HOST = os.getenv("HOST", "0.0.0.0")
