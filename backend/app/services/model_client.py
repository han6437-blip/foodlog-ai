import json
import base64
from typing import Any

import httpx

from app.services.secrets import ModelConfig, get_text_model_config, get_vision_model_config


def _extract_json(text: str) -> dict[str, Any]:
    content = text.strip()
    if content.startswith("```"):
        content = content.strip("`")
        if content.startswith("json"):
            content = content[4:]
    start = content.find("{")
    end = content.rfind("}")
    if start >= 0 and end >= start:
        content = content[start : end + 1]
    return json.loads(content)


def _post_chat_json(config: ModelConfig | None, messages: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not config:
        return None

    response = httpx.post(
        f"{config.base_url}/chat/completions",
        headers={
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": config.model_name,
            "messages": messages,
            "temperature": 0.3,
            "response_format": {"type": "json_object"},
        },
        timeout=30,
    )
    response.raise_for_status()
    content = response.json()["choices"][0]["message"]["content"]
    return _extract_json(content)


def chat_json(system_prompt: str, user_prompt: str) -> dict[str, Any] | None:
    return _post_chat_json(
        get_text_model_config(),
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )


def vision_json(system_prompt: str, user_prompt: str, image_bytes: bytes, image_mime: str) -> dict[str, Any] | None:
    image_base64 = base64.b64encode(image_bytes).decode("ascii")
    return _post_chat_json(
        get_vision_model_config(),
        [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{image_mime};base64,{image_base64}"},
                    },
                ],
            },
        ],
    )
