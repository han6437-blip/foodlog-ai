import os
from functools import lru_cache
from typing import NamedTuple

import httpx


class ModelConfig(NamedTuple):
    base_url: str
    api_key: str
    model_name: str


def _env_secret(name: str) -> str:
    return os.getenv(name, "").strip()


def _read_supabase_secret(name: str) -> str:
    supabase_url = _env_secret("SUPABASE_URL").rstrip("/")
    service_role_key = _env_secret("SUPABASE_SERVICE_ROLE_KEY")
    if not supabase_url or not service_role_key:
        return ""

    response = httpx.post(
        f"{supabase_url}/rest/v1/rpc/get_app_secret",
        headers={
            "apikey": service_role_key,
            "Authorization": f"Bearer {service_role_key}",
            "Content-Type": "application/json",
        },
        json={"secret_name": name},
        timeout=10,
    )
    response.raise_for_status()
    value = response.json()
    return value.strip() if isinstance(value, str) else ""


def _read_config(prefix: str, default_model: str) -> ModelConfig | None:
    base_url = (
        _read_supabase_secret(f"{prefix}_MODEL_BASE_URL")
        or _env_secret(f"{prefix}_MODEL_BASE_URL")
        or _read_supabase_secret("MODEL_BASE_URL")
        or _env_secret("MODEL_BASE_URL")
    )
    api_key = (
        _read_supabase_secret(f"{prefix}_MODEL_API_KEY")
        or _env_secret(f"{prefix}_MODEL_API_KEY")
        or _read_supabase_secret("MODEL_API_KEY")
        or _env_secret("MODEL_API_KEY")
    )
    model_name = (
        _read_supabase_secret(f"{prefix}_MODEL_NAME")
        or _env_secret(f"{prefix}_MODEL_NAME")
        or _read_supabase_secret("MODEL_NAME")
        or _env_secret("MODEL_NAME")
        or default_model
    )

    if not base_url or not api_key:
        return None
    return ModelConfig(base_url=base_url.rstrip("/"), api_key=api_key, model_name=model_name)


@lru_cache(maxsize=1)
def get_text_model_config() -> ModelConfig | None:
    return _read_config("TEXT", "gpt-4o-mini")


@lru_cache(maxsize=1)
def get_vision_model_config() -> ModelConfig | None:
    return _read_config("VISION", "gpt-4o-mini")
