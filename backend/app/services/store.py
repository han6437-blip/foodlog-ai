import json
import mimetypes
import os
from pathlib import Path
from threading import Lock
from typing import Any

import httpx


ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
DB_FILE = DATA_DIR / "db.json"
UPLOAD_DIR = DATA_DIR / "uploads"
_LOCK = Lock()
DEFAULT_USER_ID = "00000000-0000-0000-0000-000000000001"
DEFAULT_BUCKET = "meal-images"


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


def _env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def _supabase_url() -> str:
    return _env("SUPABASE_URL").rstrip("/")


def _service_key() -> str:
    return _env("SUPABASE_SERVICE_ROLE_KEY")


def _user_id() -> str:
    return _env("APP_USER_ID", DEFAULT_USER_ID)


def _bucket() -> str:
    return _env("SUPABASE_STORAGE_BUCKET", DEFAULT_BUCKET)


def supabase_enabled() -> bool:
    return bool(_supabase_url() and _service_key())


def _headers(prefer: str | None = None) -> dict[str, str]:
    headers = {
        "apikey": _service_key(),
        "Authorization": f"Bearer {_service_key()}",
        "Content-Type": "application/json",
    }
    if prefer:
        headers["Prefer"] = prefer
    return headers


def _request(method: str, path: str, **kwargs: Any) -> httpx.Response:
    response = httpx.request(method, f"{_supabase_url()}{path}", timeout=20, **kwargs)
    response.raise_for_status()
    return response


def _analysis_from_row(row: dict[str, Any]) -> dict[str, Any] | None:
    if row.get("health_score") is None and not row.get("foods") and not row.get("risk_tags"):
        return None
    nutrition_result = row.get("nutrition_result") or {}
    return {
        "foods": row.get("foods") or [],
        "health_score": row.get("health_score") or 0,
        "risk_tags": row.get("risk_tags") or [],
        "summary": nutrition_result.get("summary") or "",
        "next_meal_advice": row.get("next_meal_advice") or "",
    }


def _meal_from_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": row["id"],
        "meal_type": row["meal_type"],
        "eaten_at": row["eaten_at"],
        "image_url": row["image_url"],
        "description": row.get("description") or "",
        "status": row.get("status") or "待分析",
        "analysis": _analysis_from_row(row),
        "created_at": row.get("created_at"),
    }


def _meal_to_row(meal: dict[str, Any]) -> dict[str, Any]:
    analysis = meal.get("analysis") or {}
    return {
        "id": meal["id"],
        "user_id": _user_id(),
        "meal_type": meal["meal_type"],
        "image_url": meal["image_url"],
        "description": meal.get("description") or "",
        "foods": analysis.get("foods") or [],
        "nutrition_result": {"summary": analysis.get("summary") or ""},
        "health_score": analysis.get("health_score"),
        "risk_tags": analysis.get("risk_tags") or [],
        "next_meal_advice": analysis.get("next_meal_advice") or "",
        "status": meal.get("status") or "待分析",
        "eaten_at": meal["eaten_at"],
        "created_at": meal.get("created_at"),
    }


def _report_from_row(row: dict[str, Any] | None) -> dict[str, Any] | None:
    if not row:
        return None
    return {
        "week_start": row["week_start"],
        "week_end": row["week_end"],
        "completeness": row.get("completeness") or "",
        "average_score": row.get("average_score"),
        "summary": row["summary"],
        "frequent_risks": row.get("frequent_risks") or [],
        "nutrition_lack": row.get("nutrition_lack") or [],
        "risk_analysis": row.get("risk_analysis") or "",
        "compensation_plan": row.get("compensation_plan") or [],
        "note": row.get("note") or "",
    }


def _report_to_row(report: dict[str, Any]) -> dict[str, Any]:
    return {
        "user_id": _user_id(),
        "week_start": report["week_start"],
        "week_end": report["week_end"],
        "summary": report["summary"],
        "completeness": report.get("completeness") or "",
        "average_score": report.get("average_score"),
        "frequent_risks": report.get("frequent_risks") or [],
        "nutrition_lack": report.get("nutrition_lack") or [],
        "risk_analysis": report.get("risk_analysis") or "",
        "compensation_plan": report.get("compensation_plan") or [],
        "note": report.get("note") or "",
    }


def _read_supabase_db() -> dict[str, Any]:
    user_id = _user_id()
    profile_rows = _request(
        "GET",
        f"/rest/v1/user_profile?user_id=eq.{user_id}&select=*",
        headers=_headers(),
    ).json()
    meal_rows = _request(
        "GET",
        f"/rest/v1/meal_record?user_id=eq.{user_id}&select=*&order=eaten_at.asc",
        headers=_headers(),
    ).json()
    report_rows = _request(
        "GET",
        f"/rest/v1/weekly_report?user_id=eq.{user_id}&select=*&order=week_start.desc&limit=1",
        headers=_headers(),
    ).json()
    return {
        "profile": profile_rows[0] if profile_rows else None,
        "meals": [_meal_from_row(row) for row in meal_rows],
        "weekly_report": _report_from_row(report_rows[0] if report_rows else None),
    }


def _write_supabase_db(data: dict[str, Any]) -> None:
    user_id = _user_id()
    profile = data.get("profile")
    if profile:
        _request(
            "POST",
            "/rest/v1/user_profile?on_conflict=user_id",
            headers=_headers("resolution=merge-duplicates"),
            json={**profile, "user_id": user_id},
        )
    meals = data.get("meals") or []
    if meals:
        _request(
            "POST",
            "/rest/v1/meal_record?on_conflict=id",
            headers=_headers("resolution=merge-duplicates"),
            json=[_meal_to_row(meal) for meal in meals],
        )
    report = data.get("weekly_report")
    if report:
        _request(
            "POST",
            "/rest/v1/weekly_report?on_conflict=user_id,week_start",
            headers=_headers("resolution=merge-duplicates"),
            json=_report_to_row(report),
        )


def read_db() -> dict[str, Any]:
    if supabase_enabled():
        return _read_supabase_db()
    ensure_store()
    with _LOCK:
        return json.loads(DB_FILE.read_text(encoding="utf-8"))


def write_db(data: dict[str, Any]) -> None:
    if supabase_enabled():
        _write_supabase_db(data)
        return
    ensure_store()
    with _LOCK:
        DB_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def save_image(filename: str, content: bytes, content_type: str) -> str:
    if supabase_enabled():
        response = httpx.post(
            f"{_supabase_url()}/storage/v1/object/{_bucket()}/{filename}",
            headers={
                "apikey": _service_key(),
                "Authorization": f"Bearer {_service_key()}",
                "Content-Type": content_type,
                "x-upsert": "true",
            },
            content=content,
            timeout=30,
        )
        response.raise_for_status()
        return f"/api/meal/image/{filename}"

    ensure_store()
    (UPLOAD_DIR / filename).write_bytes(content)
    return f"/api/meal/image/{filename}"


def load_image(filename: str) -> tuple[bytes, str]:
    if supabase_enabled():
        response = httpx.get(
            f"{_supabase_url()}/storage/v1/object/{_bucket()}/{filename}",
            headers={
                "apikey": _service_key(),
                "Authorization": f"Bearer {_service_key()}",
            },
            timeout=20,
        )
        response.raise_for_status()
        return response.content, response.headers.get("content-type", "application/octet-stream")

    path = UPLOAD_DIR / filename
    content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    return path.read_bytes(), content_type
