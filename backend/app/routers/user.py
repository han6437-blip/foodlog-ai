from datetime import datetime
from fastapi import APIRouter, Depends
from app.schemas.models import UserProfile
from app.services.auth import require_auth
from app.services.store import read_db, write_db

router = APIRouter(prefix="/api/user", tags=["user"])


@router.get("/profile", dependencies=[Depends(require_auth)])
def get_profile() -> UserProfile | None:
    profile = read_db()["profile"]
    return UserProfile(**profile) if profile else None


@router.post("/profile", dependencies=[Depends(require_auth)])
def save_profile(profile: UserProfile) -> UserProfile:
    data = read_db()
    profile.updated_at = datetime.utcnow()
    data["profile"] = profile.model_dump(mode="json")
    write_db(data)
    return profile
