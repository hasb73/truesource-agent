from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class DriftEvent:
    id: str
    title: str
    application: str
    attribute: str
    severity: str
    documented_value: str
    observed_value: str
    confidence: float
    confidence_breakdown: dict[str, Any]
    status: str
    evidence: list[dict[str, Any]]
    proposed_changes: list[dict[str, Any]]
    affected_documents: list[str]
    finding: str
    rationale: str
    dedupe_key: str
    created_at: str
    updated_at: str
    approved_by: str | None = None


@dataclass
class ScanRun:
    id: str
    trigger: str
    scope: list[str]
    status: str
    created_at: str
    started_at: str | None = None
    finished_at: str | None = None
    incident_ids: list[str] = field(default_factory=list)
    activity: list[dict[str, Any]] = field(default_factory=list)
    summary: str | None = None
    error: str | None = None
