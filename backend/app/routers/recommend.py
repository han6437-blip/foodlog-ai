from fastapi import APIRouter
from app.schemas.models import Recommendation, RecommendationRequest, UserProfile
from app.services.ai import recommend_next_meal
from app.services.store import read_db

router = APIRouter(prefix="/api/recommend", tags=["recommend"])


@router.get("/next-meal", response_model=Recommendation)
def next_meal() -> Recommendation:
    data = read_db()
    profile = UserProfile(**data["profile"]) if data.get("profile") else None
    return recommend_next_meal(profile)


@router.post("/next-meal", response_model=Recommendation)
def next_meal_with_conditions(payload: RecommendationRequest) -> Recommendation:
    data = read_db()
    profile = UserProfile(**data["profile"]) if data.get("profile") else None
    return recommend_next_meal(profile, payload.temporary_conditions)
