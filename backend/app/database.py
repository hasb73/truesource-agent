from __future__ import annotations

import os
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Iterator, Optional

from sqlalchemy import JSON, DateTime, Float, String, Text, create_engine, delete, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

from .models import DriftEvent, ScanRun
from .state import INITIAL_VERIFIED_KNOWLEDGE

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./truesource.db")

engine = create_engine(DATABASE_URL, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False, future=True)
_DB_READY = False


class Base(DeclarativeBase):
    pass


class ScanRunRecord(Base):
    __tablename__ = "scan_runs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    trigger: Mapped[str] = mapped_column(String(32))
    scope: Mapped[list[str]] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(32))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    incident_ids: Mapped[list[str]] = mapped_column(JSON, default=list)
    activity: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class IncidentRecord(Base):
    __tablename__ = "incidents"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    application: Mapped[str] = mapped_column(String(128))
    attribute: Mapped[str] = mapped_column(String(64))
    severity: Mapped[str] = mapped_column(String(32))
    documented_value: Mapped[str] = mapped_column(String(255))
    observed_value: Mapped[str] = mapped_column(String(255))
    confidence: Mapped[float] = mapped_column(Float)
    confidence_breakdown: Mapped[dict[str, Any]] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(32))
    evidence: Mapped[list[dict[str, Any]]] = mapped_column(JSON)
    proposed_changes: Mapped[list[dict[str, Any]]] = mapped_column(JSON)
    affected_documents: Mapped[list[str]] = mapped_column(JSON)
    finding: Mapped[str] = mapped_column(Text)
    rationale: Mapped[str] = mapped_column(Text)
    dedupe_key: Mapped[str] = mapped_column(String(255), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    approved_by: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)


class AuditEventRecord(Base):
    __tablename__ = "audit_events"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    event: Mapped[str] = mapped_column(String(64))
    payload: Mapped[dict[str, Any]] = mapped_column(JSON)


class KnowledgeFactRecord(Base):
    __tablename__ = "knowledge_facts"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    entity: Mapped[str] = mapped_column(String(128))
    attribute: Mapped[str] = mapped_column(String(64))
    value: Mapped[str] = mapped_column(String(255))
    verified_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    confidence: Mapped[float] = mapped_column(Float)
    sources: Mapped[list[str]] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(32))
    version: Mapped[int]


class KnowledgeMetaRecord(Base):
    __tablename__ = "knowledge_meta"

    entity: Mapped[str] = mapped_column(String(128), primary_key=True)
    documents_updated: Mapped[list[str]] = mapped_column(JSON, default=list)


@contextmanager
def session_scope() -> Iterator[Session]:
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def _parse_datetime(value: Optional[str]) -> Optional[datetime]:
    if value is None:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _to_iso(value: Optional[datetime]) -> Optional[str]:
    if value is None:
        return None
    return value.astimezone(timezone.utc).isoformat()


def ensure_db_ready() -> None:
    global _DB_READY
    if not _DB_READY:
        Base.metadata.create_all(bind=engine)
        _DB_READY = True


def init_db() -> None:
    ensure_db_ready()
    with session_scope() as session:
        meta = session.get(KnowledgeMetaRecord, INITIAL_VERIFIED_KNOWLEDGE["entity"])
        if meta is None:
            session.add(
                KnowledgeMetaRecord(
                    entity=INITIAL_VERIFIED_KNOWLEDGE["entity"],
                    documents_updated=[],
                )
            )
        has_facts = session.scalar(select(KnowledgeFactRecord.id).limit(1))
        if has_facts is None:
            for fact in INITIAL_VERIFIED_KNOWLEDGE["facts"]:
                session.add(
                    KnowledgeFactRecord(
                        id=f"{INITIAL_VERIFIED_KNOWLEDGE['entity']}:{fact['attribute']}",
                        entity=INITIAL_VERIFIED_KNOWLEDGE["entity"],
                        attribute=fact["attribute"],
                        value=fact["value"],
                        verified_at=_parse_datetime(fact["verified_at"]) or datetime.now(timezone.utc),
                        confidence=fact["confidence"],
                        sources=fact["sources"],
                        status=fact["status"],
                        version=fact["version"],
                    )
                )


def health_summary() -> dict[str, Any]:
    try:
        ensure_db_ready()
        with session_scope() as session:
            session.execute(select(KnowledgeFactRecord.id).limit(1)).all()
        return {"ok": True, "url": DATABASE_URL}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def load_runtime_state() -> dict[str, Any]:
    ensure_db_ready()
    with session_scope() as session:
        scan_rows = session.scalars(select(ScanRunRecord).order_by(ScanRunRecord.created_at)).all()
        incident_rows = session.scalars(select(IncidentRecord).order_by(IncidentRecord.created_at)).all()
        audit_rows = session.scalars(select(AuditEventRecord).order_by(AuditEventRecord.created_at)).all()
        fact_rows = session.scalars(select(KnowledgeFactRecord).where(KnowledgeFactRecord.entity == INITIAL_VERIFIED_KNOWLEDGE["entity"]).order_by(KnowledgeFactRecord.attribute)).all()
        meta = session.get(KnowledgeMetaRecord, INITIAL_VERIFIED_KNOWLEDGE["entity"])

    knowledge = {
        "entity": INITIAL_VERIFIED_KNOWLEDGE["entity"],
        "facts": [
            {
                "attribute": row.attribute,
                "value": row.value,
                "verified_at": _to_iso(row.verified_at),
                "confidence": row.confidence,
                "sources": row.sources,
                "status": row.status,
                "version": row.version,
            }
            for row in fact_rows
        ] or INITIAL_VERIFIED_KNOWLEDGE["facts"],
        "documents_updated": meta.documents_updated if meta else [],
    }

    scans = {
        row.id: ScanRun(
            id=row.id,
            trigger=row.trigger,
            scope=row.scope,
            status=row.status,
            created_at=_to_iso(row.created_at) or "",
            started_at=_to_iso(row.started_at),
            finished_at=_to_iso(row.finished_at),
            incident_ids=row.incident_ids,
            activity=row.activity,
            summary=row.summary,
            error=row.error,
        )
        for row in scan_rows
    }
    drifts = {
        row.id: DriftEvent(
            id=row.id,
            title=row.title,
            application=row.application,
            attribute=row.attribute,
            severity=row.severity,
            documented_value=row.documented_value,
            observed_value=row.observed_value,
            confidence=row.confidence,
            confidence_breakdown=row.confidence_breakdown,
            status=row.status,
            evidence=row.evidence,
            proposed_changes=row.proposed_changes,
            affected_documents=row.affected_documents,
            finding=row.finding,
            rationale=row.rationale,
            dedupe_key=row.dedupe_key,
            created_at=_to_iso(row.created_at) or "",
            updated_at=_to_iso(row.updated_at) or "",
            approved_by=row.approved_by,
        )
        for row in incident_rows
    }
    audit = [
        {"time": _to_iso(row.created_at), **row.payload, "event": row.event}
        for row in audit_rows
    ]
    return {"knowledge": knowledge, "scans": scans, "drifts": drifts, "audit": audit}


def save_scan(scan: ScanRun) -> None:
    ensure_db_ready()
    with session_scope() as session:
        session.merge(
            ScanRunRecord(
                id=scan.id,
                trigger=scan.trigger,
                scope=scan.scope,
                status=scan.status,
                created_at=_parse_datetime(scan.created_at) or datetime.now(timezone.utc),
                started_at=_parse_datetime(scan.started_at),
                finished_at=_parse_datetime(scan.finished_at),
                incident_ids=scan.incident_ids,
                activity=scan.activity,
                summary=scan.summary,
                error=scan.error,
            )
        )


def save_incident(incident: DriftEvent) -> None:
    ensure_db_ready()
    with session_scope() as session:
        session.merge(
            IncidentRecord(
                id=incident.id,
                title=incident.title,
                application=incident.application,
                attribute=incident.attribute,
                severity=incident.severity,
                documented_value=incident.documented_value,
                observed_value=incident.observed_value,
                confidence=incident.confidence,
                confidence_breakdown=incident.confidence_breakdown,
                status=incident.status,
                evidence=incident.evidence,
                proposed_changes=incident.proposed_changes,
                affected_documents=incident.affected_documents,
                finding=incident.finding,
                rationale=incident.rationale,
                dedupe_key=incident.dedupe_key,
                created_at=_parse_datetime(incident.created_at) or datetime.now(timezone.utc),
                updated_at=_parse_datetime(incident.updated_at) or datetime.now(timezone.utc),
                approved_by=incident.approved_by,
            )
        )


def save_audit(event: dict[str, Any]) -> None:
    ensure_db_ready()
    timestamp = _parse_datetime(event.get("time")) or datetime.now(timezone.utc)
    payload = {key: value for key, value in event.items() if key not in {"time", "event"}}
    with session_scope() as session:
        session.add(
            AuditEventRecord(
                id=f"audit:{timestamp.timestamp()}:{event.get('event','unknown')}",
                created_at=timestamp,
                event=event.get("event", "UNKNOWN"),
                payload=payload,
            )
        )


def replace_knowledge(knowledge: dict[str, Any]) -> None:
    ensure_db_ready()
    entity = knowledge["entity"]
    with session_scope() as session:
        session.execute(delete(KnowledgeFactRecord).where(KnowledgeFactRecord.entity == entity))
        session.merge(KnowledgeMetaRecord(entity=entity, documents_updated=knowledge.get("documents_updated", [])))
        for fact in knowledge["facts"]:
            session.add(
                KnowledgeFactRecord(
                    id=f"{entity}:{fact['attribute']}",
                    entity=entity,
                    attribute=fact["attribute"],
                    value=fact["value"],
                    verified_at=_parse_datetime(fact["verified_at"]) or datetime.now(timezone.utc),
                    confidence=fact["confidence"],
                    sources=fact["sources"],
                    status=fact["status"],
                    version=fact["version"],
                )
            )


def reset_all_state() -> None:
    ensure_db_ready()
    with session_scope() as session:
        session.execute(delete(ScanRunRecord))
        session.execute(delete(IncidentRecord))
        session.execute(delete(AuditEventRecord))
        session.execute(delete(KnowledgeFactRecord))
        session.execute(delete(KnowledgeMetaRecord))
    init_db()
