from fastapi import APIRouter, Depends

from app.schemas.models import LoginRequest, LoginResponse
from app.services.auth import authenticate_user, create_access_token, require_auth

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest) -> LoginResponse:
    user = authenticate_user(payload.email, payload.password)
    return LoginResponse(
        access_token=create_access_token(user["id"], user["email"]),
        email=user["email"],
    )


@router.get("/me")
def me(user=Depends(require_auth)):
    return {"email": user["email"], "user_id": user["sub"]}
