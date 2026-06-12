from fastapi import APIRouter, HTTPException
from app.schemas.models import WeeklyReport
from app.services.ai import generate_weekly_report
from app.services.store import read_db, write_db

router = APIRouter(prefix="/api/report", tags=["report"])


@router.get("/weekly", response_model=WeeklyReport | None)
def get_weekly_report():
    report = read_db().get("weekly_report")
    return WeeklyReport(**report) if report else None


@router.post("/weekly-generate", response_model=WeeklyReport)
def generate_report() -> WeeklyReport:
    report = generate_weekly_report()
    if not report:
        raise HTTPException(status_code=400, detail="最近 7 天没有饮食记录")
    data = read_db()
    data["weekly_report"] = report.model_dump(mode="json")
    write_db(data)
    return report
