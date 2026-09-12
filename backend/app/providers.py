from __future__ import annotations

import json
import os
from typing import Any, Optional

from .security import redact_value

try:
    from openai import OpenAI
except Exception:
    OpenAI = None


def configured_provider(provider_override: Optional[str] = None) -> str:
    chosen = provider_override or os.getenv("LLM_PROVIDER", "openai")
    chosen = chosen.lower()
    if chosen not in {"openai", "openrouter", "deterministic"}:
        return os.getenv("LLM_PROVIDER", "openai").lower()
    return chosen


def llm_available(provider_override: Optional[str] = None) -> bool:
    provider = configured_provider(provider_override)
    if provider == "deterministic":
        return False
    if OpenAI is None:
        return False
    if provider == "openrouter":
        return bool(os.getenv("OPENROUTER_API_KEY"))
    return bool(os.getenv("OPENAI_API_KEY"))


def effective_provider(provider_override: Optional[str] = None) -> str:
    provider = configured_provider(provider_override)
    if provider == "deterministic":
        return provider
    if llm_available(provider):
        return provider
    return "deterministic"


def provider_summary() -> dict[str, Any]:
    current = configured_provider()
    return {
        "active_provider": current,
        "providers": {
            "openai": {
                "configured": bool(os.getenv("OPENAI_API_KEY")),
                "model": os.getenv("OPENAI_MODEL", "gpt-5.6"),
            },
            "openrouter": {
                "configured": bool(os.getenv("OPENROUTER_API_KEY")),
                "model": os.getenv("OPENROUTER_MODEL", "openai/gpt-5.6"),
                "base_url": "https://openrouter.ai/api/v1",
            },
            "deterministic": {
                "configured": True,
                "model": "deterministic-rules",
            },
        },
    }


def run_json_prompt(system_prompt: str, payload: dict[str, Any], response_keys: list[str], provider_override: Optional[str] = None) -> dict[str, Any] | None:
    if not llm_available(provider_override) or OpenAI is None:
        return None

    provider = configured_provider(provider_override)
    if provider == "openrouter":
        client = OpenAI(
            api_key=os.getenv("OPENROUTER_API_KEY"),
            base_url="https://openrouter.ai/api/v1",
            default_headers={
                "HTTP-Referer": os.getenv("OPENROUTER_SITE_URL", os.getenv("APP_BASE_URL", "http://localhost:3000")),
                "X-OpenRouter-Title": os.getenv("OPENROUTER_APP_NAME", "TrueSource"),
            },
        )
        model = os.getenv("OPENROUTER_MODEL", "openai/gpt-5.6")
    else:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        model = os.getenv("OPENAI_MODEL", "gpt-5.6")

    prompt = (
        f"{system_prompt}\n"
        f"Return JSON with keys: {', '.join(response_keys)}.\n"
        "Do not invent facts beyond the payload.\n"
        f"Payload: {json.dumps(redact_value(payload), indent=2)}"
    )
    response = client.responses.create(model=model, input=prompt)
    try:
        return json.loads(response.output_text)
    except Exception:
        return None
