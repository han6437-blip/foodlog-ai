import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from typing import Any

from fastapi import Header, HTTPException, Query, Request

from app.services.store import find_user_by_email, set_current_user_id


TOKEN_TTL_SECONDS = 60 * 60 * 24 * 30


def _secret() -> str:
    secret = os.getenv("JWT_SECRET", "").strip()
    if not secret:
        raise HTTPException(status_code=500, detail="JWT_SECRET 未配置")
    return secret


def _b64_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def hash_password(password: str) -> str:
    iterations = 210_000
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return f"pbkdf2_sha256${iterations}${_b64_encode(salt)}${_b64_encode(digest)}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        algorithm, iterations_text, salt_text, digest_text = password_hash.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        iterations = int(iterations_text)
        salt = _b64_decode(salt_text)
        expected = _b64_decode(digest_text)
        actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
        return hmac.compare_digest(actual, expected)
    except Exception:
        return False


def create_access_token(user_id: str, email: str) -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "exp": int(time.time()) + TOKEN_TTL_SECONDS,
    }
    payload_text = _b64_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signature = hmac.new(_secret().encode("utf-8"), payload_text.encode("ascii"), hashlib.sha256).digest()
    return f"{payload_text}.{_b64_encode(signature)}"


def verify_access_token(token: str) -> dict[str, Any]:
    try:
        payload_text, signature_text = token.split(".", 1)
        expected = hmac.new(_secret().encode("utf-8"), payload_text.encode("ascii"), hashlib.sha256).digest()
        if not hmac.compare_digest(_b64_decode(signature_text), expected):
            raise ValueError("bad signature")
        payload = json.loads(_b64_decode(payload_text))
        if int(payload.get("exp", 0)) < int(time.time()):
            raise ValueError("expired")
        return payload
    except Exception as exc:
        raise HTTPException(status_code=401, detail="登录已失效，请重新登录") from exc


def authenticate_user(email: str, password: str) -> dict[str, Any]:
    user = find_user_by_email(email)
    if not user or not verify_password(password, user.get("password_hash") or ""):
        raise HTTPException(status_code=401, detail="邮箱或密码错误")
    if not user.get("is_active", True):
        raise HTTPException(status_code=403, detail="账号已停用")
    return user


def require_auth(
    request: Request,
    authorization: str | None = Header(default=None),
    access_token: str | None = Query(default=None),
) -> dict[str, Any]:
    token = access_token
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()
    if not token:
        raise HTTPException(status_code=401, detail="请先登录")
    payload = verify_access_token(token)
    set_current_user_id(payload["sub"])
    request.state.user = payload
    return payload
