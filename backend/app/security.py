from __future__ import annotations

import os
import re
from typing import Any

from fastapi import HTTPException, Request

REDACTION_PATTERNS = [
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9._-]+\.[a-zA-Z0-9._-]+"),
    re.compile(r"(?i)(api[_-]?key|token|password|secret)\s*[:=]\s*[^\s,;]+"),
    re.compile(r"-----BEGIN [A-Z ]+PRIVATE KEY-----[\s\S]+?-----END [A-Z ]+PRIVATE KEY-----"),
    re.compile(r"[A-Za-z][A-Za-z0-9+.-]*://[^\s:@/]+:[^\s@/]+@[^\s]+"),
]


def redact_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: redact_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [redact_value(item) for item in value]
    if isinstance(value, str):
        redacted = value
        for pattern in REDACTION_PATTERNS:
            redacted = pattern.sub("[REDACTED]", redacted)
        return redacted
    return value


def auth_summary() -> dict[str, Any]:
    return {
        "mode": "development",
        "default_role": os.getenv("DEV_AUTH_ROLE", "administrator"),
    }


def get_actor(request: Request) -> dict[str, str]:
    role = request.headers.get("X-Demo-Role", os.getenv("DEV_AUTH_ROLE", "administrator"))
    return {
        "id": request.headers.get("X-Demo-User", "demo-reviewer"),
        "name": request.headers.get("X-Demo-User", "Demo Reviewer"),
        "role": role,
        "tenant_id": request.headers.get("X-Demo-Tenant", "demo-airline"),
    }


def require_reviewer(actor: dict[str, str]) -> None:
    if actor["role"] not in {"reviewer", "administrator"}:
        raise HTTPException(status_code=403, detail="Reviewer permissions required")
