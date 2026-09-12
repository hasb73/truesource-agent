from __future__ import annotations

import hashlib
import re
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any


PROMPT_INJECTION = re.compile(
    r"(?i)(ignore|forget|bypass|override).{0,45}(instruction|policy|rule|evidence)|"
    r"system\s*(override|message)|agent\s*instruction|developer\s*message"
)
SECRET_REQUEST = re.compile(
    r"(?i)(read|reveal|retrieve|print|expose|append|include|send|upload).{0,50}"
    r"(\.env|credential|password|secret|token|api[_ -]?key|aws[_ -]?(key|credential))"
)
EXTERNAL_TRANSFER = re.compile(
    r"(?i)(send|upload|post|forward|exfiltrat).{0,80}(external|https?://|webhook|attacker|credential|secret)"
)
CONCEALMENT = re.compile(
    r"(?i)(do not|don't|never).{0,35}(mention|tell|show|log|record)|"
    r"(remove|delete|clear).{0,35}(audit|logs?|history)"
)
DESTRUCTIVE_ACTION = re.compile(
    r"(?i)(delete|destroy|wipe|remove).{0,50}(production|document|secret|credential|database|logs?)"
)

FIREWALL_INCIDENTS: dict[str, dict[str, Any]] = {}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _incident_id(source: str, source_reference: str, content: str) -> str:
    digest = hashlib.sha256(f"{source}:{source_reference}:{content}".encode()).hexdigest()[:6].upper()
    return f"AF-{digest}"


def _sanitize_blocked_content(content: str) -> str:
    unsafe_patterns = [PROMPT_INJECTION, SECRET_REQUEST, EXTERNAL_TRANSFER, CONCEALMENT, DESTRUCTIVE_ACTION]
    retained = [
        line for line in content.splitlines()
        if not any(pattern.search(line) for pattern in unsafe_patterns)
    ]
    return "\n".join(retained).strip()


def inspect_content(
    content: str,
    *,
    source: str,
    source_reference: str,
    record: bool = True,
) -> dict[str, Any]:
    signals: list[str] = []
    checks = ["Source provenance checked"]
    risk = 5

    if PROMPT_INJECTION.search(content):
        signals.append("Instruction hierarchy override")
        checks.append("Instruction hierarchy inspected")
        risk += 38
    if SECRET_REQUEST.search(content):
        signals.append("Credential access requested")
        checks.append("Sensitive capability request inspected")
        risk += 28
    if EXTERNAL_TRANSFER.search(content):
        signals.append("External data transfer requested")
        checks.append("Destination trust checked")
        risk += 22
    if CONCEALMENT.search(content):
        signals.append("Audit or disclosure suppression")
        checks.append("Concealment indicators inspected")
        risk += 18
    if DESTRUCTIVE_ACTION.search(content):
        signals.append("Destructive operation requested")
        checks.append("Blast radius estimated")
        risk += 30

    risk = min(risk, 99)
    decision = "BLOCK" if risk >= 60 else "REVIEW" if risk >= 30 else "ALLOW"
    sanitized_content = _sanitize_blocked_content(content) if decision == "BLOCK" else content
    actions = (
        ["Content quarantined from model context", "Sensitive tools denied", "Scan continued with trusted evidence"]
        if decision == "BLOCK"
        else ["Content retained with human review required"]
        if decision == "REVIEW"
        else ["Content admitted to the evidence pipeline"]
    )

    assessment = {
        "id": _incident_id(source, source_reference, content),
        "time": now_iso(),
        "source": source,
        "source_reference": source_reference,
        "decision": decision,
        "risk": risk,
        "signals": signals,
        "checks": checks,
        "actions": actions,
        "sanitized_content": sanitized_content,
    }
    if record and decision == "BLOCK":
        FIREWALL_INCIDENTS[assessment["id"]] = {key: value for key, value in assessment.items() if key != "sanitized_content"}
    return assessment


def inspect_evidence_payload(payload: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    safe_payload = deepcopy(payload)
    blocked: list[dict[str, Any]] = []

    def inspect_field(container: dict[str, Any] | None, field: str, source: str, reference: str) -> None:
        if not container or not isinstance(container.get(field), str):
            return
        assessment = inspect_content(
            container[field],
            source=source,
            source_reference=reference,
        )
        if assessment["decision"] == "BLOCK":
            container[field] = assessment["sanitized_content"]
            blocked.append({key: value for key, value in assessment.items() if key != "sanitized_content"})

    confluence = safe_payload.get("confluence")
    inspect_field(
        confluence,
        "content",
        "confluence",
        f"confluence://{(confluence or {}).get('id', 'unknown')}",
    )
    sharepoint = safe_payload.get("sharepoint")
    inspect_field(
        sharepoint,
        "content",
        "sharepoint",
        f"sharepoint://{(sharepoint or {}).get('id', 'unknown')}",
    )

    for index, commit in enumerate(safe_payload.get("gitlab_commits") or []):
        inspect_field(commit, "message", "gitlab", f"gitlab://commit/{commit.get('sha', index)}")
    jira = safe_payload.get("jira") or {}
    for index, comment in enumerate(jira.get("comments") or []):
        if not isinstance(comment, str):
            continue
        assessment = inspect_content(
            comment,
            source="jira",
            source_reference=f"jira://{jira.get('key', 'unknown')}/comment/{index}",
        )
        if assessment["decision"] == "BLOCK":
            jira["comments"][index] = assessment["sanitized_content"]
            blocked.append({key: value for key, value in assessment.items() if key != "sanitized_content"})
    servicenow = safe_payload.get("servicenow")
    inspect_field(
        servicenow,
        "implementation_plan",
        "servicenow",
        f"servicenow://{(servicenow or {}).get('number', 'unknown')}",
    )
    return safe_payload, blocked


def authorize_document_change(actor: dict[str, str], change: dict[str, Any]) -> dict[str, Any]:
    assessment = inspect_content(
        str(change.get("after", "")),
        source=f"proposed-{change.get('source', 'document')}",
        source_reference=str(change.get("document_id", "unknown")),
        record=False,
    )
    policy_checks = ["Reviewer role checked", "Tenant boundary checked", "Proposed diff inspected"]
    if actor.get("role") not in {"reviewer", "administrator"}:
        assessment["decision"] = "BLOCK"
        assessment["risk"] = 99
        assessment["signals"].append("Actor lacks reviewer permission")
    if change.get("source") not in {"confluence", "sharepoint"} or not change.get("document_id"):
        assessment["decision"] = "BLOCK"
        assessment["risk"] = 99
        assessment["signals"].append("Write target is outside the approved connector scope")
    assessment["checks"] = policy_checks + assessment["checks"]
    return assessment


def list_firewall_incidents() -> list[dict[str, Any]]:
    return list(reversed(list(FIREWALL_INCIDENTS.values())))


def reset_firewall_incidents() -> None:
    FIREWALL_INCIDENTS.clear()
