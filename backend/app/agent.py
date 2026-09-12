from __future__ import annotations

import re
from typing import Any, Optional

from .connectors import collect_evidence
from .firewall import inspect_evidence_payload
from .providers import effective_provider, run_json_prompt
from .security import redact_value
from .state import VERIFIED_KNOWLEDGE

AUTHORITY = {
    "aws": 1.0,
    "gitlab": 0.9,
    "jira": 0.9,
    "servicenow": 0.95,
    "confluence": 0.6,
    "sharepoint": 0.55,
}


def _extract(content: str | None, label: str) -> str | None:
    if not content:
        return None
    match = re.search(rf"{label}:\s*(.+)", content)
    return match.group(1).strip() if match else None


def _confidence(supporting: list[dict[str, Any]], contradicting: list[dict[str, Any]]) -> tuple[float, dict[str, Any]]:
    support_score = sum(item["authority_weight"] * item["confidence"] for item in supporting)
    contradiction_score = sum(item["authority_weight"] * item["confidence"] for item in contradicting)
    support_max = AUTHORITY["aws"] + AUTHORITY["gitlab"] + AUTHORITY["jira"] + AUTHORITY["servicenow"]
    source_count = len({item["source"] for item in supporting if item.get("supports")})
    support_component = 0.62 * (support_score / support_max if support_max else 0.0)
    coverage_bonus = 0.08 if source_count >= 4 else 0.05 if source_count >= 3 else 0.03 if source_count >= 2 else 0.0
    authority_bonus = 0.17 if any(item["source"] == "aws" for item in supporting) else 0.0
    staleness_bonus = 0.10 if contradiction_score >= 1.0 and source_count >= 4 else 0.03 if contradiction_score > 0 else 0.0
    final_confidence = round(min(0.99, support_component + coverage_bonus + authority_bonus + staleness_bonus), 2)
    return final_confidence, {
        "support_score": round(support_score, 2),
        "contradiction_score": round(contradiction_score, 2),
        "supporting_sources": [item["source"] for item in supporting],
        "contradicting_sources": [item["source"] for item in contradicting],
        "coverage_bonus": coverage_bonus,
        "authority_bonus": authority_bonus,
        "staleness_bonus": staleness_bonus,
        "explanation": "Confidence combines source authority, corroboration count, and contradictory stale documentation.",
    }


def deterministic_analysis(application: str = "Payments", provider_override: Optional[str] = None) -> dict[str, Any]:
    raw_payload = collect_evidence(application)
    payload, security_events = inspect_evidence_payload(raw_payload)
    aws = payload.get("aws") or {}
    commits = payload.get("gitlab_commits") or []
    deployments = payload.get("gitlab_deployments") or []
    jira = payload.get("jira") or {}
    servicenow = payload.get("servicenow") or {}
    confluence = payload.get("confluence") or {}
    sharepoint = payload.get("sharepoint") or {}

    observed_compute = aws.get("compute")
    observed_database = aws.get("database")
    documented_compute = _extract(confluence.get("content"), "Compute") or _extract(sharepoint.get("content"), "Runtime")
    documented_database = _extract(confluence.get("content"), "Database") or _extract(sharepoint.get("content"), "Database")

    migration_commit = commits[0] if commits else {}
    latest_deployment = deployments[0] if deployments else {}
    migrated = observed_compute == "EKS"

    evidence = [
        {
            "source": "aws",
            "source_type": "operational",
            "entity": application,
            "attribute": "compute",
            "value": observed_compute,
            "observed_at": payload["collected_at"],
            "source_reference": "aws://payments",
            "confidence": 0.99,
            "collected_at": payload["collected_at"],
            "authority_weight": AUTHORITY["aws"],
            "supports": observed_compute == "EKS",
            "fact": f"AWS reports Payments compute on {observed_compute or 'unknown'}.",
        },
        {
            "source": "gitlab",
            "source_type": "deployment",
            "entity": application,
            "attribute": "compute",
            "value": latest_deployment.get("runtime"),
            "observed_at": latest_deployment.get("timestamp", payload["collected_at"]),
            "source_reference": "gitlab://payments-api/deployments",
            "confidence": 0.93,
            "collected_at": payload["collected_at"],
            "authority_weight": AUTHORITY["gitlab"],
            "supports": latest_deployment.get("runtime") == "EKS" or "EKS" in migration_commit.get("message", ""),
            "fact": migration_commit.get("message", "No recent migration commit found."),
        },
        {
            "source": "jira",
            "source_type": "workflow",
            "entity": application,
            "attribute": "compute",
            "value": jira.get("status"),
            "observed_at": jira.get("updated_at", payload["collected_at"]),
            "source_reference": "jira://PAY-4821",
            "confidence": 0.9,
            "collected_at": payload["collected_at"],
            "authority_weight": AUTHORITY["jira"],
            "supports": jira.get("status") == "Done",
            "fact": f"Jira issue PAY-4821 status is {jira.get('status', 'unknown')}.",
        },
        {
            "source": "servicenow",
            "source_type": "change_management",
            "entity": application,
            "attribute": "compute",
            "value": servicenow.get("status"),
            "observed_at": servicenow.get("updated_at", payload["collected_at"]),
            "source_reference": "servicenow://CHG003421",
            "confidence": 0.95,
            "collected_at": payload["collected_at"],
            "authority_weight": AUTHORITY["servicenow"],
            "supports": servicenow.get("status") == "Closed",
            "fact": f"ServiceNow change CHG003421 is {servicenow.get('status', 'unknown')}.",
        },
        {
            "source": "confluence",
            "source_type": "documentation",
            "entity": application,
            "attribute": "compute",
            "value": documented_compute,
            "observed_at": confluence.get("last_modified", payload["collected_at"]),
            "source_reference": f"confluence://{confluence.get('id', 'unknown')}",
            "confidence": 0.65,
            "collected_at": payload["collected_at"],
            "authority_weight": AUTHORITY["confluence"],
            "supports": documented_compute == observed_compute and documented_compute is not None,
            "fact": confluence.get("content", "Confluence page unavailable."),
        },
        {
            "source": "sharepoint",
            "source_type": "documentation",
            "entity": application,
            "attribute": "compute",
            "value": _extract(sharepoint.get("content"), "Runtime"),
            "observed_at": sharepoint.get("last_modified", payload["collected_at"]),
            "source_reference": f"sharepoint://{sharepoint.get('id', 'unknown')}",
            "confidence": 0.6,
            "collected_at": payload["collected_at"],
            "authority_weight": AUTHORITY["sharepoint"],
            "supports": _extract(sharepoint.get("content"), "Runtime") == observed_compute and observed_compute is not None,
            "fact": sharepoint.get("content", "SharePoint document unavailable."),
        },
    ]

    supporting = [item for item in evidence if item.get("supports") and item["source"] in {"aws", "gitlab", "jira", "servicenow"}]
    contradicting = [
        item for item in evidence
        if item["source"] in {"confluence", "sharepoint"} and documented_compute and observed_compute and documented_compute != observed_compute
    ]
    confidence, confidence_breakdown = _confidence(supporting, contradicting)

    proposed_changes = []
    if confluence:
        before = confluence["content"]
        after = before.replace("Compute: EC2", "Compute: EKS").replace("Database: RDS MySQL", "Database: RDS PostgreSQL").replace("Deployment: EC2 deployment scripts", "Deployment: GitLab CI/CD")
        proposed_changes.append({
            "source": "confluence",
            "document_id": confluence["id"],
            "document": f"Confluence / {confluence['title']}",
            "before": before,
            "after": after,
        })
    if sharepoint:
        before = sharepoint["content"]
        after = before.replace("Runtime: EC2", "Runtime: EKS").replace("Database: MySQL", "Database: RDS PostgreSQL")
        proposed_changes.append({
            "source": "sharepoint",
            "document_id": sharepoint["id"],
            "document": f"SharePoint / {sharepoint['title']}",
            "before": before,
            "after": after,
        })

    drift_detected = migrated and documented_compute == "EC2" and len(supporting) >= 2
    finding = "Payments documentation is stale because operational sources show an EKS migration while documentation still says EC2." if drift_detected else "No high-confidence documentation drift detected."
    rationale = "Operational sources outrank documentation, and multiple independent systems corroborate the migration." if drift_detected else "The available evidence does not exceed the drift threshold."

    result = {
        "application": application,
        "attribute": "compute",
        "drift_detected": drift_detected,
        "finding": finding,
        "rationale": rationale,
        "confidence": confidence if drift_detected else max(0.28, round(confidence - 0.35, 2)),
        "documented_value": documented_compute or "Unknown",
        "observed_value": observed_compute or "Unknown",
        "observed_database": observed_database or documented_database or "Unknown",
        "documented_database": documented_database or "Unknown",
        "evidence": redact_value(evidence),
        "proposed_changes": proposed_changes,
        "confidence_breakdown": confidence_breakdown,
        "affected_documents": [change["document"] for change in proposed_changes],
        "dedupe_key": f"{application}:compute:{documented_compute}->{observed_compute}",
        "security_events": security_events,
    }

    llm_result = run_json_prompt(
        "You are TrueSource, an enterprise knowledge verification agent. Summarize whether the documentation is stale and explain the reasoning for a human reviewer.",
        result,
        ["finding", "rationale"],
        provider_override=provider_override,
    )
    if llm_result:
        result["finding"] = llm_result.get("finding", result["finding"])
        result["rationale"] = llm_result.get("rationale", result["rationale"])
    result["provider_used"] = effective_provider(provider_override)
    return result


def analyze(application: str = "Payments", provider_override: Optional[str] = None) -> dict[str, Any]:
    return deterministic_analysis(application, provider_override)


def answer_question(question: str, provider_override: Optional[str] = None) -> dict[str, Any]:
    facts = {fact["attribute"]: fact for fact in VERIFIED_KNOWLEDGE["facts"]}
    compute = facts.get("compute")
    database = facts.get("database")
    payload = {
        "knowledge": VERIFIED_KNOWLEDGE,
        "question": question,
    }
    llm_result = run_json_prompt(
        "Answer the employee question using only the verified knowledge. If knowledge is missing, say so explicitly. Keep the answer concise and factual.",
        payload,
        ["answer"],
        provider_override=provider_override,
    )
    if llm_result and llm_result.get("answer"):
        answer = llm_result["answer"]
    elif compute and database:
        answer = (
            f"Payments is currently deployed on {compute['value']} with {database['value']}. "
            f"This was verified from {', '.join(compute['sources'])}."
        )
    else:
        answer = "I cannot verify the current Payments deployment from authoritative sources right now."

    return {
        "answer": answer,
        "knowledge": VERIFIED_KNOWLEDGE,
        "trust_card": {
            "confidence": compute["confidence"] if compute else 0.0,
            "verified_at": compute["verified_at"] if compute else None,
            "sources": compute["sources"] if compute else [],
            "documents_updated": VERIFIED_KNOWLEDGE.get("documents_updated", []),
            "provider": effective_provider(provider_override),
        },
    }
