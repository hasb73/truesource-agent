from __future__ import annotations

from fastapi import FastAPI, HTTPException

from shared.demo_data import apply_gitlab_scenario, clone_seed, gitlab_seed, migrate_gitlab

app = FastAPI(title="TrueSource Mock GitLab", version="0.1.0")
STATE = clone_seed(gitlab_seed)


@app.get("/health")
def health() -> dict[str, bool]:
    return {"ok": True}


@app.get("/gitlab/projects")
def list_projects() -> list[dict]:
    return STATE["projects"]


@app.get("/gitlab/projects/{project}/commits")
def list_commits(project: str) -> list[dict]:
    details = _project(project)
    return details["commits"]


@app.get("/gitlab/projects/{project}/deployments")
def list_deployments(project: str) -> list[dict]:
    details = _project(project)
    return details["deployments"]


@app.post("/gitlab/demo/migrate")
def migrate() -> dict:
    return migrate_gitlab(STATE)


@app.post("/gitlab/demo/change/{scenario}")
def change(scenario: str) -> dict:
    try:
        return apply_gitlab_scenario(STATE, scenario)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/gitlab/demo/reset")
def reset() -> dict[str, bool]:
    global STATE
    STATE = clone_seed(gitlab_seed)
    return {"ok": True}


def _project(project: str) -> dict:
    for item in STATE["projects"]:
        if item["id"] == project:
            return item
    raise HTTPException(status_code=404, detail="Project not found")
