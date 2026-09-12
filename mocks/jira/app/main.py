from __future__ import annotations

from fastapi import FastAPI, HTTPException

from shared.demo_data import clone_seed, jira_seed, migrate_jira

app = FastAPI(title="TrueSource Mock Jira", version="0.1.0")
STATE = clone_seed(jira_seed)


@app.get("/health")
def health() -> dict[str, bool]:
    return {"ok": True}


@app.get("/jira/issues")
def list_issues() -> list[dict]:
    return STATE["issues"]


@app.get("/jira/issues/{issue}")
def get_issue(issue: str) -> dict:
    for item in STATE["issues"]:
        if item["key"] == issue:
            return item
    raise HTTPException(status_code=404, detail="Issue not found")


@app.post("/jira/demo/migrate")
def migrate() -> dict:
    return migrate_jira(STATE)


@app.post("/jira/demo/reset")
def reset() -> dict[str, bool]:
    global STATE
    STATE = clone_seed(jira_seed)
    return {"ok": True}
