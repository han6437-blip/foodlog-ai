import json
from pathlib import Path
from threading import Lock
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
DB_FILE = DATA_DIR / "db.json"
UPLOAD_DIR = DATA_DIR / "uploads"
_LOCK = Lock()


def ensure_store() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    if not DB_FILE.exists():
        DB_FILE.write_text(
            json.dumps(
                {"profile": None, "meals": [], "weekly_report": None},
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )


def read_db() -> dict[str, Any]:
    ensure_store()
    with _LOCK:
        return json.loads(DB_FILE.read_text(encoding="utf-8"))


def write_db(data: dict[str, Any]) -> None:
    ensure_store()
    with _LOCK:
        DB_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
