from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import BackgroundTasks, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from .agent import analyze_all, answer_question
from .connectors import list_confluence_pages, list_documents, list_scenarios, list_sharepoint_documents, reset_demo, simulate_change, simulate_migration, simulate_prompt_injection, update_confluence, update_sharepoint
from .database import health_summary, init_db, load_runtime_state, replace_knowledge, reset_all_state, save_audit, save_incident, save_scan
from .models import DriftEvent, ScanRun
from .providers import provider_summary
from .security import auth_summary, get_actor, require_reviewer
from .firewall import authorize_document_change, list_firewall_incidents, reset_firewall_incidents
from .state import AUDIT, DRIFTS, SCAN_RUNS, VERIFIED_KNOWLEDGE, load_control_plane_state, reset_control_plane_state

app = FastAPI(title="TrueSource API", version="0.1.0")

origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def now():
    return datetime.now(timezone.utc).isoformat()


@app.on_event("startup")
def startup() -> None:
    init_db()
    load_control_plane_state(load_runtime_state())

class AskRequest(BaseModel):
    question: str
    provider: Optional[str] = None


class ScanRequest(BaseModel):
    scope: list[str] = ["Payments"]
    trigger: str = "manual"
    provider: Optional[str] = None


class DecisionRequest(BaseModel):
    reason: Optional[str] = None


class DemoChangeRequest(BaseModel):
    scenario: str = "eks_migration"


class PortalDocUpdateRequest(BaseModel):
    content: str
    source: str = "confluence"

@app.get("/api/health")
def health():
    return {
        "ok": True,
        "service": "truesource",
        "scan_runs": len(SCAN_RUNS),
        "incidents": len(DRIFTS),
        "database": health_summary(),
        "auth": auth_summary(),
        "runtime": provider_summary(),
    }


@app.get("/api/runtime")
def runtime_config():
    return {
        "auth": auth_summary(),
        "llm": provider_summary(),
        "copilotkit": {
            "runtime_url": os.getenv("COPILOTKIT_RUNTIME_URL"),
            "agent_id": os.getenv("COPILOTKIT_AGENT_ID", "truesource_guardian"),
        },
    }


@app.get("/api/auth/me")
def auth_me(request: Request):
    return get_actor(request)

@app.get("/api/dashboard")
def dashboard():
    active = [d for d in DRIFTS.values() if d.status in ("detected", "investigating", "pending_review")]
    verified = sum(1 for fact in VERIFIED_KNOWLEDGE["facts"] if fact["status"] == "verified")
    return {
        "documents": len(list_documents()),
        "health": 86 if active else 100,
        "open_drift": len(active),
        "verified": verified,
        "stale": len(VERIFIED_KNOWLEDGE["facts"]) - verified,
        "auto_fixed": len([d for d in DRIFTS.values() if d.status == "resolved"]),
        "knowledge": VERIFIED_KNOWLEDGE,
        "latest_scan": next(reversed(list(SCAN_RUNS.values()))).__dict__ if SCAN_RUNS else None,
        "runtime": provider_summary(),
        "auth": auth_summary(),
    }

@app.get("/api/drift")
def drift():
    return [d.__dict__ for d in DRIFTS.values()]

@app.get("/api/drift/{drift_id}")
def drift_detail(drift_id: str):
    if drift_id not in DRIFTS:
        raise HTTPException(status_code=404, detail="Incident not found")
    return DRIFTS[drift_id].__dict__


@app.get("/api/drift/{drift_id}/evidence")
def evidence(drift_id: str):
    if drift_id not in DRIFTS:
        raise HTTPException(status_code=404, detail="Incident not found")
    return {
        "incident_id": drift_id,
        "evidence": DRIFTS[drift_id].evidence,
        "confidence_breakdown": DRIFTS[drift_id].confidence_breakdown,
    }

@app.get("/api/documents")
def documents():
    docs = []
    facts = {fact["attribute"]: fact["value"] for fact in VERIFIED_KNOWLEDGE["facts"]}
    quarantined = {item["source_reference"].split("//")[-1] for item in list_firewall_incidents()}
    for item in list_documents():
        source = "Confluence" if item["id"].startswith("CONF") else "SharePoint"
        status = "QUARANTINED" if item["id"] in quarantined else "STALE" if facts.get("compute") == "EKS" and "EC2" in item.get("content", "") else "VERIFIED"
        docs.append({
            "id": item["id"],
            "source": source,
            "title": item["title"],
            "version": item["version"],
            "status": status,
            "application": item.get("application"),
        })
    return docs


@app.get("/api/docs/portal")
def docs_portal():
    return {
        "confluence": list_confluence_pages(),
        "sharepoint": list_sharepoint_documents(),
    }


@app.put("/api/docs/portal/confluence/{page_id}")
def portal_update_confluence(page_id: str, payload: PortalDocUpdateRequest, request: Request):
    actor = get_actor(request)
    require_reviewer(actor)
    updated = update_confluence(page_id, payload.content, actor["name"])
    event = {
        "time": now(),
        "actor": actor,
        "event": "PORTAL_DOC_UPDATED",
        "source": "confluence",
        "document_id": page_id,
    }
    AUDIT.append(event)
    save_audit(event)
    return {"ok": True, "document": updated}


@app.put("/api/docs/portal/sharepoint/{document_id}")
def portal_update_sharepoint(document_id: str, payload: PortalDocUpdateRequest, request: Request):
    actor = get_actor(request)
    require_reviewer(actor)
    updated = update_sharepoint(document_id, payload.content, actor["name"])
    event = {
        "time": now(),
        "actor": actor,
        "event": "PORTAL_DOC_UPDATED",
        "source": "sharepoint",
        "document_id": document_id,
    }
    AUDIT.append(event)
    save_audit(event)
    return {"ok": True, "document": updated}


@app.get("/api/demo/scenarios")
def demo_scenarios():
    return list_scenarios()


@app.get("/api/knowledge")
def knowledge():
    return VERIFIED_KNOWLEDGE


@app.get("/api/scans/{scan_id}")
def scan_status(scan_id: str):
    if scan_id not in SCAN_RUNS:
        raise HTTPException(status_code=404, detail="Scan not found")
    return SCAN_RUNS[scan_id].__dict__

@app.post("/api/demo/migrate")
def demo_migrate(request: Request):
    actor = get_actor(request)
    result = simulate_migration()
    event = {"time": now(), "actor": actor, "event": "DEMO_CHANGE_APPLIED", "scenario": "eks_migration", "result": result}
    AUDIT.append(event)
    save_audit(event)
    return {"ok": True, "scenario": "eks_migration", "result": result}


@app.post("/api/demo/change")
def demo_change(payload: DemoChangeRequest, request: Request):
    actor = get_actor(request)
    result = simulate_change(payload.scenario)
    if not all(result.values()):
        raise HTTPException(status_code=400, detail=f"Unable to apply scenario: {payload.scenario}")
    event = {"time": now(), "actor": actor, "event": "DEMO_CHANGE_APPLIED", "scenario": payload.scenario, "result": result}
    AUDIT.append(event)
    save_audit(event)
    return {"ok": True, "scenario": payload.scenario, "result": result}


@app.post("/api/demo/inject-agent-attack")
def demo_inject_agent_attack(request: Request):
    actor = get_actor(request)
    result = simulate_prompt_injection()
    if not result.get("ok"):
        raise HTTPException(status_code=502, detail="The Confluence demo connector did not accept the attack scenario")
    event = {"time": now(), "actor": actor, "event": "AGENT_ATTACK_INJECTED", "result": {"ok": result.get("ok", False)}}
    AUDIT.append(event)
    save_audit(event)
    return {"ok": True, "result": result}


@app.post("/api/demo/reset")
def demo_reset(request: Request):
    actor = get_actor(request)
    result = reset_demo()
    reset_control_plane_state()
    reset_firewall_incidents()
    reset_all_state()
    event = {"time": now(), "actor": actor, "event": "DEMO_RESET", "result": result}
    AUDIT.append(event)
    save_audit(event)
    return {"ok": True, "result": result}

@app.post("/api/scan")
def scan(background_tasks: BackgroundTasks, request: Request, payload: Optional[ScanRequest] = None):
    actor = get_actor(request)
    payload = payload or ScanRequest()
    scan_id = "scan_" + uuid.uuid4().hex[:8]
    SCAN_RUNS[scan_id] = ScanRun(
        id=scan_id,
        trigger=payload.trigger,
        scope=payload.scope,
        status="queued",
        created_at=now(),
    )
    save_scan(SCAN_RUNS[scan_id])
    event = {"time": now(), "actor": actor, "event": "SCAN_QUEUED", "scan_id": scan_id}
    AUDIT.append(event)
    save_audit(event)
    background_tasks.add_task(execute_scan, scan_id, payload.scope, actor, payload.provider)
    return {"scan_id": scan_id, "status": "queued"}

@app.post("/api/drift/{drift_id}/approve")
def approve(drift_id: str, payload: DecisionRequest, request: Request):
    actor = get_actor(request)
    require_reviewer(actor)
    if drift_id not in DRIFTS:
        raise HTTPException(status_code=404, detail="Incident not found")
    drift = DRIFTS[drift_id]
    assessments = [authorize_document_change(actor, change) for change in drift.proposed_changes]
    blocked = [assessment for assessment in assessments if assessment["decision"] == "BLOCK"]
    if blocked:
        event = {"time": now(), "actor": actor, "event": "DOCUMENT_WRITE_BLOCKED", "drift_id": drift_id, "security": blocked}
        AUDIT.append(event)
        save_audit(event)
        raise HTTPException(status_code=403, detail={"message": "AgentFirewall blocked the document write", "assessments": blocked})
    authorization_event = {
        "time": now(),
        "actor": actor,
        "event": "DOCUMENT_WRITE_AUTHORIZED",
        "drift_id": drift_id,
        "security": [
            {
                "source_reference": assessment["source_reference"],
                "decision": assessment["decision"],
                "risk": assessment["risk"],
                "checks": assessment["checks"],
            }
            for assessment in assessments
        ],
    }
    AUDIT.append(authorization_event)
    save_audit(authorization_event)
    updated_documents = []
    for change in drift.proposed_changes:
        if change["source"] == "confluence":
            updated_documents.append(update_confluence(change["document_id"], change["after"], actor["name"]))
        elif change["source"] == "sharepoint":
            updated_documents.append(update_sharepoint(change["document_id"], change["after"], actor["name"]))
    drift.status = "resolved"
    drift.approved_by = actor["id"]
    drift.updated_at = now()
    save_incident(drift)
    VERIFIED_KNOWLEDGE["facts"] = [
        {
            "attribute": "compute",
            "value": drift.observed_value,
            "verified_at": now(),
            "confidence": drift.confidence,
            "sources": ["aws", "gitlab", "jira", "servicenow"],
            "status": "verified",
            "version": VERIFIED_KNOWLEDGE["facts"][0]["version"] + 1,
        },
        {
            "attribute": "database",
            "value": "RDS PostgreSQL",
            "verified_at": now(),
            "confidence": drift.confidence,
            "sources": ["aws", "gitlab", "jira", "servicenow"],
            "status": "verified",
            "version": VERIFIED_KNOWLEDGE["facts"][1]["version"] + 1,
        },
    ]
    VERIFIED_KNOWLEDGE["documents_updated"] = [item["title"] for item in updated_documents]
    replace_knowledge(VERIFIED_KNOWLEDGE)
    event = {
        "time": now(),
        "actor": actor,
        "event": "DRIFT_APPROVED",
        "drift_id": drift_id,
        "reason": payload.reason,
        "documents": VERIFIED_KNOWLEDGE["documents_updated"],
    }
    AUDIT.append(event)
    save_audit(event)
    return {"ok": True, "knowledge": VERIFIED_KNOWLEDGE, "documents": updated_documents}

@app.post("/api/drift/{drift_id}/reject")
def reject(drift_id: str, payload: DecisionRequest, request: Request):
    actor = get_actor(request)
    require_reviewer(actor)
    if drift_id not in DRIFTS:
        raise HTTPException(status_code=404, detail="Incident not found")
    DRIFTS[drift_id].status = "rejected"
    DRIFTS[drift_id].updated_at = now()
    save_incident(DRIFTS[drift_id])
    event = {"time": now(), "actor": actor, "event": "DRIFT_REJECTED", "drift_id": drift_id, "reason": payload.reason}
    AUDIT.append(event)
    save_audit(event)
    return {"ok": True}

@app.post("/api/ask")
def ask(req: AskRequest):
    return answer_question(req.question, req.provider)

@app.get("/api/audit")
def audit():
    return AUDIT


@app.get("/api/firewall/incidents")
def firewall_incidents():
    return list_firewall_incidents()


def execute_scan(scan_id: str, scope: list[str], actor: dict[str, str], provider: Optional[str]) -> None:
    scan_run = SCAN_RUNS[scan_id]
    scan_run.status = "running"
    scan_run.started_at = now()
    scan_run.activity.append({"time": now(), "status": "running", "message": "Discovering enterprise systems"})
    save_scan(scan_run)
    results = analyze_all(scope[0] if scope else "Payments", provider)
    scan_run.activity.extend([
        {"time": now(), "status": "ok", "message": "AWS checked"},
        {"time": now(), "status": "ok", "message": "GitLab checked"},
        {"time": now(), "status": "ok", "message": "Jira checked"},
        {"time": now(), "status": "ok", "message": "ServiceNow checked"},
    ])
    security_events = [event for result in results for event in result.get("security_events", [])]
    if security_events:
        scan_run.activity.extend([
            {"time": now(), "status": "warn", "message": "AgentFirewall detected an attempted knowledge manipulation"},
            {"time": now(), "status": "warn", "message": "Malicious instructions quarantined from model context"},
            {"time": now(), "status": "ok", "message": "Scan continued with trusted evidence"},
        ])
        security_event = {
            "time": now(),
            "actor": actor,
            "event": "AGENT_ATTACK_BLOCKED",
            "scan_id": scan_id,
            "incidents": [item["id"] for item in security_events],
        }
        AUDIT.append(security_event)
        save_audit(security_event)
    incident_ids = []
    findings = []
    for result in results:
        findings.append(result["finding"])
        if not (result["drift_detected"] and result["confidence"] >= 0.85):
            continue
        existing = next(
            (
                item for item in DRIFTS.values()
                if item.dedupe_key == result["dedupe_key"] and item.status in {"detected", "investigating", "pending_review"}
            ),
            None,
        )
        if existing:
            drift = existing
            drift.confidence = result["confidence"]
            drift.evidence = result["evidence"]
            drift.proposed_changes = result["proposed_changes"]
            drift.confidence_breakdown = result["confidence_breakdown"]
            drift.finding = result["finding"]
            drift.rationale = result["rationale"]
            drift.updated_at = now()
        else:
            drift_id = "KI-" + uuid.uuid4().hex[:6].upper()
            drift = DriftEvent(
                id=drift_id,
                title=f"Payments {result['attribute']} profile drift",
                application=result["application"],
                attribute=result["attribute"],
                severity="HIGH",
                documented_value=result["documented_value"],
                observed_value=result["observed_value"],
                confidence=result["confidence"],
                confidence_breakdown=result["confidence_breakdown"],
                status="pending_review",
                evidence=result["evidence"],
                proposed_changes=result["proposed_changes"],
                affected_documents=result["affected_documents"],
                finding=result["finding"],
                rationale=result["rationale"],
                dedupe_key=result["dedupe_key"],
                created_at=now(),
                updated_at=now(),
            )
            DRIFTS[drift.id] = drift
        save_incident(drift)
        incident_ids.append(drift.id)
        scan_run.activity.extend([
            {"time": now(), "status": "warn", "message": f"Documentation contradicts {result['attribute']} operational state"},
            {"time": now(), "status": "running", "message": f"Preparing {result['attribute']} repair proposal"},
        ])
        event = {"time": now(), "actor": actor, "event": "DRIFT_DETECTED", "drift_id": drift.id, "scan_id": scan_id}
        AUDIT.append(event)
        save_audit(event)
    scan_run.incident_ids = incident_ids
    scan_run.summary = " ".join(dict.fromkeys(findings))
    scan_run.status = "completed"
    scan_run.finished_at = now()
    save_scan(scan_run)
