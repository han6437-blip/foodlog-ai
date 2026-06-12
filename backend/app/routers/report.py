from fastapi import APIRouter, Depends, HTTPException
from app.schemas.models import WeeklyReport
from app.services.ai import generate_weekly_report
from app.services.auth import require_auth
from app.services.security import rate_limit
from app.services.store import read_db, write_db

router = APIRouter(prefix="/api/report", tags=["report"])


@router.get("/weekly", response_model=WeeklyReport | None, dependencies=[Depends(require_auth)])
def get_weekly_report():
    report = read_db().get("weekly_report")
    return WeeklyReport(**report) if report else None


@router.post(
    "/weekly-generate",
    response_model=WeeklyReport,
    dependencies=[
        Depends(require_auth),
        Depends(rate_limit(limit=5, window_seconds=3600, name="weekly_generate")),
    ],
)
def generate_report() -> WeeklyReport:
    report = generate_weekly_report()
    if not report:
        raise HTTPException(status_code=400, detail="最近 7 天没有饮食记录")
    data = read_db()
    data["weekly_report"] = report.model_dump(mode="json")
    write_db(data)
    return report
