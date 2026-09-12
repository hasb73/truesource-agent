from __future__ import annotations

from fastapi import FastAPI, HTTPException

from shared.demo_data import clone_seed, migrate_servicenow, servicenow_seed

app = FastAPI(title="TrueSource Mock ServiceNow", version="0.1.0")
STATE = clone_seed(servicenow_seed)


@app.get("/health")
def health() -> dict[str, bool]:
    return {"ok": True}


@app.get("/servicenow/changes")
def list_changes() -> list[dict]:
    return STATE["changes"]


@app.get("/servicenow/changes/{change}")
def get_change(change: str) -> dict:
    for item in STATE["changes"]:
        if item["number"] == change:
            return item
    raise HTTPException(status_code=404, detail="Change not found")


@app.post("/servicenow/demo/migrate")
def migrate() -> dict:
    return migrate_servicenow(STATE)


@app.post("/servicenow/demo/reset")
def reset() -> dict[str, bool]:
    global STATE
    STATE = clone_seed(servicenow_seed)
    return {"ok": True}
