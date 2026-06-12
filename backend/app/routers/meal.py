from datetime import datetime
from pathlib import Path
from uuid import uuid4
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import Response
import httpx
from app.schemas.models import FollowUpRequest, FollowUpResponse, MealCreateResponse, MealRecord, UserProfile
from app.services.ai import analyze_meal, answer_follow_up
from app.services.store import load_image, read_db, save_image, write_db

router = APIRouter(prefix="/api/meal", tags=["meal"])


@router.post("/analyze", response_model=MealCreateResponse)
async def create_and_analyze_meal(
    image: UploadFile = File(...),
    meal_type: str = Form(...),
    eaten_at: str = Form(...),
    description: str = Form(""),
):
    if image.content_type not in {"image/jpeg", "image/png", "image/webp"}:
        raise HTTPException(status_code=400, detail="图片格式不支持，请上传 JPG、PNG 或 WebP")
    ext = Path(image.filename or "meal.jpg").suffix or ".jpg"
    record_id = str(uuid4())
    filename = f"{record_id}{ext}"
    content = await image.read()
    if len(content) > 1_500_000:
        raise HTTPException(status_code=400, detail="图片过大，请压缩后重试")
    try:
        image_url = save_image(filename, content, image.content_type)
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="图片上传到 Supabase Storage 失败") from exc

    data = read_db()
    profile = UserProfile(**data["profile"]) if data.get("profile") else None
    analysis = analyze_meal(description, profile, image_bytes=content, image_mime=image.content_type)
    record = MealRecord(
        id=record_id,
        meal_type=meal_type,
        eaten_at=datetime.fromisoformat(eaten_at),
        image_url=image_url,
        description=description,
        status="已分析",
        analysis=analysis,
    )
    data["meals"].append(record.model_dump(mode="json"))
    write_db(data)
    return MealCreateResponse(record=record)


@router.get("/history")
def history() -> list[MealRecord]:
    data = read_db()
    records = [MealRecord(**meal) for meal in data["meals"]]
    return sorted(records, key=lambda item: item.eaten_at, reverse=True)[:50]


@router.get("/{meal_id}")
def get_meal(meal_id: str) -> MealRecord:
    for meal in read_db()["meals"]:
        if meal["id"] == meal_id:
            return MealRecord(**meal)
    raise HTTPException(status_code=404, detail="记录不存在")


@router.post("/{meal_id}/follow-up", response_model=FollowUpResponse)
def follow_up(meal_id: str, payload: FollowUpRequest) -> FollowUpResponse:
    data = read_db()
    meal = next((item for item in data["meals"] if item["id"] == meal_id), None)
    if not meal:
        raise HTTPException(status_code=404, detail="记录不存在")
    profile = UserProfile(**data["profile"]) if data.get("profile") else None
    return FollowUpResponse(answer=answer_follow_up(payload.question, meal, profile))


@router.get("/image/{filename}")
def image(filename: str):
    try:
        content, content_type = load_image(filename)
    except (FileNotFoundError, httpx.HTTPStatusError) as exc:
        raise HTTPException(status_code=404, detail="图片不存在")
    return Response(content=content, media_type=content_type)
