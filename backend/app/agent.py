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

ATTRIBUTE_LABELS = {
    "compute": ("Compute", "Runtime"),
    "database": ("Database", "Database"),
    "region": ("Region", "Region"),
    "deployment": ("Deployment", "Deployment"),
}


def _extract(content: str | None, label: str) -> str | None:
    if not content:
        return None
    match = re.search(rf"{label}:\s*(.+)", content)
    return match.group(1).strip() if match else None


def _replace_line(content: str, label: str, value: str) -> str:
    pattern = rf"({re.escape(label)}:\s*)(.+)"
    return re.sub(pattern, rf"\1{value}", content)


def _support_evidence(attribute: str, observed: str | None, commit: dict[str, Any], jira: dict[str, Any], servicenow: dict[str, Any]) -> tuple[bool, bool, bool]:
    commit_text = f"{commit.get('message', '')} {' '.join(commit.get('files_changed', []))}".lower()
    jira_text = " ".join(jira.get("comments", [])).lower()
    sn_text = f"{servicenow.get('status', '')} {servicenow.get('implementation_plan', '')}".lower()
    target = (observed or "").lower()
    gitlab_support = target in commit_text if target else False
    jira_support = jira.get("status") == "Done"
    servicenow_support = servicenow.get("status") == "Closed"
    if attribute == "compute":
        gitlab_support = gitlab_support or "eks" in commit_text or "runtime" in commit_text
    return gitlab_support, jira_support, servicenow_support


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


def deterministic_analysis(
    application: str = "Payments",
    provider_override: Optional[str] = None,
    attribute_override: Optional[str] = None,
    payload_override: Optional[dict[str, Any]] = None,
    security_events_override: Optional[list[dict[str, Any]]] = None,
) -> dict[str, Any]:
    if payload_override is None:
        raw_payload = collect_evidence(application)
        payload, security_events = inspect_evidence_payload(raw_payload)
    else:
        payload = payload_override
        security_events = security_events_override or []
    aws = payload.get("aws") or {}
    commits = payload.get("gitlab_commits") or []
    deployments = payload.get("gitlab_deployments") or []
    jira = payload.get("jira") or {}
    servicenow = payload.get("servicenow") or {}
    confluence = payload.get("confluence") or {}
    sharepoint = payload.get("sharepoint") or {}

    observed_state = {
        "compute": aws.get("compute"),
        "database": aws.get("database"),
        "region": aws.get("region"),
        "deployment": aws.get("deployment"),
    }
    documented_state = {
        "compute": _extract(confluence.get("content"), "Compute") or _extract(sharepoint.get("content"), "Runtime"),
        "database": _extract(confluence.get("content"), "Database") or _extract(sharepoint.get("content"), "Database"),
        "region": _extract(confluence.get("content"), "Region") or _extract(sharepoint.get("content"), "Region"),
        "deployment": _extract(confluence.get("content"), "Deployment"),
    }

    drift_attributes = [
        attribute
        for attribute in ["compute", "database", "region", "deployment"]
        if observed_state.get(attribute) and documented_state.get(attribute) and observed_state[attribute] != documented_state[attribute]
    ]
    drift_attribute = attribute_override if attribute_override in drift_attributes else (drift_attributes[0] if drift_attributes else None)

    migration_commit = commits[0] if commits else {}
    latest_deployment = deployments[0] if deployments else {}
    gitlab_support, jira_support, servicenow_support = _support_evidence(
        drift_attribute or "compute",
        observed_state.get(drift_attribute or "compute"),
        migration_commit,
        jira,
        servicenow,
    )

    evidence = [
        {
            "source": "aws",
            "source_type": "operational",
            "entity": application,
            "attribute": drift_attribute or "compute",
            "value": observed_state.get(drift_attribute or "compute"),
            "observed_at": payload["collected_at"],
            "source_reference": "aws://payments",
            "confidence": 0.99,
            "collected_at": payload["collected_at"],
            "authority_weight": AUTHORITY["aws"],
            "supports": bool(observed_state.get(drift_attribute or "compute")),
            "fact": (
                f"AWS reports Payments {drift_attribute or 'compute'} as "
                f"{observed_state.get(drift_attribute or 'compute') or 'unknown'}."
            ),
        },
        {
            "source": "gitlab",
            "source_type": "deployment",
            "entity": application,
            "attribute": drift_attribute or "compute",
            "value": latest_deployment.get("runtime"),
            "observed_at": latest_deployment.get("timestamp", payload["collected_at"]),
            "source_reference": "gitlab://payments-api/deployments",
            "confidence": 0.93,
            "collected_at": payload["collected_at"],
            "authority_weight": AUTHORITY["gitlab"],
            "supports": gitlab_support,
            "fact": migration_commit.get("message", "No recent migration commit found."),
        },
        {
            "source": "jira",
            "source_type": "workflow",
            "entity": application,
            "attribute": drift_attribute or "compute",
            "value": jira.get("status"),
            "observed_at": jira.get("updated_at", payload["collected_at"]),
            "source_reference": "jira://PAY-4821",
            "confidence": 0.9,
            "collected_at": payload["collected_at"],
            "authority_weight": AUTHORITY["jira"],
            "supports": jira_support,
            "fact": f"Jira issue PAY-4821 status is {jira.get('status', 'unknown')}.",
        },
        {
            "source": "servicenow",
            "source_type": "change_management",
            "entity": application,
            "attribute": drift_attribute or "compute",
            "value": servicenow.get("status"),
            "observed_at": servicenow.get("updated_at", payload["collected_at"]),
            "source_reference": "servicenow://CHG003421",
            "confidence": 0.95,
            "collected_at": payload["collected_at"],
            "authority_weight": AUTHORITY["servicenow"],
            "supports": servicenow_support,
            "fact": f"ServiceNow change CHG003421 is {servicenow.get('status', 'unknown')}.",
        },
        {
            "source": "confluence",
            "source_type": "documentation",
            "entity": application,
            "attribute": drift_attribute or "compute",
            "value": documented_state.get(drift_attribute or "compute"),
            "observed_at": confluence.get("last_modified", payload["collected_at"]),
            "source_reference": f"confluence://{confluence.get('id', 'unknown')}",
            "confidence": 0.65,
            "collected_at": payload["collected_at"],
            "authority_weight": AUTHORITY["confluence"],
            "supports": documented_state.get(drift_attribute or "compute") == observed_state.get(drift_attribute or "compute"),
            "fact": confluence.get("content", "Confluence page unavailable."),
        },
        {
            "source": "sharepoint",
            "source_type": "documentation",
            "entity": application,
            "attribute": drift_attribute or "compute",
            "value": documented_state.get(drift_attribute or "compute"),
            "observed_at": sharepoint.get("last_modified", payload["collected_at"]),
            "source_reference": f"sharepoint://{sharepoint.get('id', 'unknown')}",
            "confidence": 0.6,
            "collected_at": payload["collected_at"],
            "authority_weight": AUTHORITY["sharepoint"],
            "supports": documented_state.get(drift_attribute or "compute") == observed_state.get(drift_attribute or "compute"),
            "fact": sharepoint.get("content", "SharePoint document unavailable."),
        },
    ]

    supporting = [item for item in evidence if item.get("supports") and item["source"] in {"aws", "gitlab", "jira", "servicenow"}]
    contradicting = [
        item for item in evidence
        if item["source"] in {"confluence", "sharepoint"}
        and drift_attribute
        and documented_state.get(drift_attribute)
        and observed_state.get(drift_attribute)
        and documented_state[drift_attribute] != observed_state[drift_attribute]
    ]
    confidence, confidence_breakdown = _confidence(supporting, contradicting)

    proposed_changes = []
    if confluence:
        before = confluence["content"]
        after = before
        for attribute, value in observed_state.items():
            if value and documented_state.get(attribute) and documented_state[attribute] != value:
                confluence_label = ATTRIBUTE_LABELS[attribute][0]
                after = _replace_line(after, confluence_label, value)
        proposed_changes.append({
            "source": "confluence",
            "document_id": confluence["id"],
            "document": f"Confluence / {confluence['title']}",
            "before": before,
            "after": after,
        })
    if sharepoint:
        before = sharepoint["content"]
        after = before
        for attribute, value in observed_state.items():
            if value and documented_state.get(attribute) and documented_state[attribute] != value:
                sharepoint_label = ATTRIBUTE_LABELS[attribute][1]
                if sharepoint_label != "Deployment":
                    after = _replace_line(after, sharepoint_label, value)
        proposed_changes.append({
            "source": "sharepoint",
            "document_id": sharepoint["id"],
            "document": f"SharePoint / {sharepoint['title']}",
            "before": before,
            "after": after,
        })

    drift_detected = bool(drift_attribute and len(supporting) >= 2)
    documented_value = documented_state.get(drift_attribute or "compute") or "Unknown"
    observed_value = observed_state.get(drift_attribute or "compute") or "Unknown"
    if drift_detected:
        finding = (
            f"Payments documentation is stale for {drift_attribute} because operational sources show "
            f"{observed_value} while documentation still says {documented_value}."
        )
        rationale = "Operational systems outrank documentation, and independent workflow systems corroborate the change."
    else:
        finding = "No high-confidence documentation drift detected."
        rationale = "The available evidence does not exceed the drift threshold."

    result = {
        "application": application,
        "attribute": drift_attribute or "compute",
        "drift_detected": drift_detected,
        "finding": finding,
        "rationale": rationale,
        "confidence": confidence if drift_detected else max(0.28, round(confidence - 0.35, 2)),
        "documented_value": documented_value,
        "observed_value": observed_value,
        "observed_database": observed_state.get("database") or documented_state.get("database") or "Unknown",
        "documented_database": documented_state.get("database") or "Unknown",
        "evidence": redact_value(evidence),
        "proposed_changes": proposed_changes,
        "confidence_breakdown": confidence_breakdown,
        "affected_documents": [change["document"] for change in proposed_changes],
        "dedupe_key": f"{application}:{drift_attribute or 'compute'}:{documented_value}->{observed_value}",
        "drift_attributes": drift_attributes,
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


def analyze_all(application: str = "Payments", provider_override: Optional[str] = None) -> list[dict[str, Any]]:
    """Evaluate every independently stale attribute from one normalized evidence snapshot."""
    raw_payload = collect_evidence(application)
    payload, security_events = inspect_evidence_payload(raw_payload)
    first_result = deterministic_analysis(
        application,
        provider_override,
        payload_override=payload,
        security_events_override=security_events,
    )
    results = [first_result]
    for attribute in first_result["drift_attributes"][1:]:
        results.append(
            deterministic_analysis(
                application,
                "deterministic",
                attribute_override=attribute,
                payload_override=payload,
            )
        )
    return results


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
