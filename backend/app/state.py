from __future__ import annotations

from copy import deepcopy

from .models import DriftEvent, ScanRun

INITIAL_VERIFIED_KNOWLEDGE = {
	"entity": "Payments",
	"facts": [
		{
			"attribute": "compute",
			"value": "EC2",
			"verified_at": "2026-09-10T09:00:00Z",
			"confidence": 0.62,
			"sources": ["confluence", "sharepoint"],
			"status": "stale",
			"version": 1,
		},
		{
			"attribute": "database",
			"value": "RDS MySQL",
			"verified_at": "2026-09-10T09:00:00Z",
			"confidence": 0.62,
			"sources": ["confluence", "sharepoint"],
			"status": "stale",
			"version": 1,
		},
	],
	"documents_updated": [],
}

VERIFIED_KNOWLEDGE = deepcopy(INITIAL_VERIFIED_KNOWLEDGE)
DRIFTS: dict[str, DriftEvent] = {}
SCAN_RUNS: dict[str, ScanRun] = {}
AUDIT: list[dict] = []


def reset_control_plane_state() -> None:
	VERIFIED_KNOWLEDGE.clear()
	VERIFIED_KNOWLEDGE.update(deepcopy(INITIAL_VERIFIED_KNOWLEDGE))
	DRIFTS.clear()
	SCAN_RUNS.clear()
	AUDIT.clear()


def load_control_plane_state(payload: dict) -> None:
	VERIFIED_KNOWLEDGE.clear()
	VERIFIED_KNOWLEDGE.update(deepcopy(payload["knowledge"]))
	DRIFTS.clear()
	DRIFTS.update(payload["drifts"])
	SCAN_RUNS.clear()
	SCAN_RUNS.update(payload["scans"])
	AUDIT.clear()
	AUDIT.extend(payload["audit"])
