from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

import httpx


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _base_url(name: str, fallback: str) -> str:
    return os.getenv(name, fallback).rstrip("/")


AWS_MOCK_URL = _base_url("AWS_MOCK_URL", "http://localhost:8001")
GITLAB_MOCK_URL = _base_url("GITLAB_MOCK_URL", "http://localhost:8002")
JIRA_MOCK_URL = _base_url("JIRA_MOCK_URL", "http://localhost:8003")
SERVICENOW_MOCK_URL = _base_url("SERVICENOW_MOCK_URL", "http://localhost:8004")
CONFLUENCE_MOCK_URL = _base_url("CONFLUENCE_MOCK_URL", "http://localhost:8005")
SHAREPOINT_MOCK_URL = _base_url("SHAREPOINT_MOCK_URL", "http://localhost:8006")


def _get_json(url: str) -> Any:
    try:
        response = httpx.get(url, timeout=5.0)
        response.raise_for_status()
        return response.json()
    except Exception:
        return None


def _post_json(url: str, payload: dict[str, Any] | None = None) -> Any:
    try:
        response = httpx.post(url, json=payload or {}, timeout=5.0)
        response.raise_for_status()
        return response.json()
    except Exception:
        return None


def _put_json(url: str, payload: dict[str, Any]) -> Any:
    response = httpx.put(url, json=payload, timeout=5.0)
    response.raise_for_status()
    return response.json()


def _payments_page(pages: list[dict[str, Any]] | None) -> dict[str, Any] | None:
    if not pages:
        return None
    return next((page for page in pages if page.get("application") == "Payments"), None)


def collect_evidence(application: str = "Payments") -> dict[str, Any]:
    slug = application.lower().replace(" ", "-")
    return {
        "application": application,
        "collected_at": now_iso(),
        "aws": _get_json(f"{AWS_MOCK_URL}/aws/resources/{slug}"),
        "aws_changes": _get_json(f"{AWS_MOCK_URL}/aws/changes"),
        "gitlab_project": _get_json(f"{GITLAB_MOCK_URL}/gitlab/projects"),
        "gitlab_commits": _get_json(f"{GITLAB_MOCK_URL}/gitlab/projects/payments-api/commits"),
        "gitlab_deployments": _get_json(f"{GITLAB_MOCK_URL}/gitlab/projects/payments-api/deployments"),
        "jira": _get_json(f"{JIRA_MOCK_URL}/jira/issues/PAY-4821"),
        "servicenow": _get_json(f"{SERVICENOW_MOCK_URL}/servicenow/changes/CHG003421"),
        "confluence": _payments_page(_get_json(f"{CONFLUENCE_MOCK_URL}/confluence/pages")),
        "sharepoint": _payments_page(_get_json(f"{SHAREPOINT_MOCK_URL}/sharepoint/documents")),
    }


def list_documents() -> list[dict[str, Any]]:
    confluence_pages = _get_json(f"{CONFLUENCE_MOCK_URL}/confluence/pages") or []
    sharepoint_docs = _get_json(f"{SHAREPOINT_MOCK_URL}/sharepoint/documents") or []
    return confluence_pages + sharepoint_docs


def simulate_migration() -> dict[str, Any]:
    return {
        "aws": _post_json(f"{AWS_MOCK_URL}/aws/demo/migrate"),
        "gitlab": _post_json(f"{GITLAB_MOCK_URL}/gitlab/demo/migrate"),
        "jira": _post_json(f"{JIRA_MOCK_URL}/jira/demo/migrate"),
        "servicenow": _post_json(f"{SERVICENOW_MOCK_URL}/servicenow/demo/migrate"),
    }


def simulate_prompt_injection() -> dict[str, Any]:
    return _post_json(f"{CONFLUENCE_MOCK_URL}/confluence/demo/inject-agent-attack") or {"ok": False}


def reset_demo() -> dict[str, Any]:
    return {
        "aws": _post_json(f"{AWS_MOCK_URL}/aws/demo/reset"),
        "gitlab": _post_json(f"{GITLAB_MOCK_URL}/gitlab/demo/reset"),
        "jira": _post_json(f"{JIRA_MOCK_URL}/jira/demo/reset"),
        "servicenow": _post_json(f"{SERVICENOW_MOCK_URL}/servicenow/demo/reset"),
        "confluence": _post_json(f"{CONFLUENCE_MOCK_URL}/confluence/demo/reset"),
        "sharepoint": _post_json(f"{SHAREPOINT_MOCK_URL}/sharepoint/demo/reset"),
    }


def update_confluence(page_id: str, content: str, author: str) -> dict[str, Any]:
    return _put_json(
        f"{CONFLUENCE_MOCK_URL}/confluence/pages/{page_id}",
        {"content": content, "author": author},
    )


def update_sharepoint(document_id: str, content: str, author: str) -> dict[str, Any]:
    return _put_json(
        f"{SHAREPOINT_MOCK_URL}/sharepoint/documents/{document_id}",
        {"content": content, "author": author},
    )
