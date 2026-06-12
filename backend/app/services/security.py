import os
import time
from collections import defaultdict, deque
from collections.abc import Callable

from fastapi import HTTPException, Request


_VISITS: dict[str, deque[float]] = defaultdict(deque)


def allowed_origins() -> list[str]:
    raw = os.getenv("ALLOWED_ORIGINS", "").strip()
    if not raw:
        return ["*"]
    return [origin.strip().rstrip("/") for origin in raw.split(",") if origin.strip()]


def client_ip(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for", "")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    cf_ip = request.headers.get("cf-connecting-ip")
    if cf_ip:
        return cf_ip
    return request.client.host if request.client else "unknown"


def rate_limit(limit: int, window_seconds: int, name: str) -> Callable[[Request], None]:
    def dependency(request: Request) -> None:
        now = time.monotonic()
        key = f"{name}:{client_ip(request)}"
        visits = _VISITS[key]
        while visits and now - visits[0] > window_seconds:
            visits.popleft()
        if len(visits) >= limit:
            raise HTTPException(status_code=429, detail="请求过于频繁，请稍后再试")
        visits.append(now)

    return dependency
