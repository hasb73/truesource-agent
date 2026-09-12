from __future__ import annotations

from fastapi import FastAPI, HTTPException

from shared.demo_data import aws_seed, clone_seed, migrate_aws

app = FastAPI(title="TrueSource Mock AWS", version="0.1.0")
STATE = clone_seed(aws_seed)


@app.get("/health")
def health() -> dict[str, bool]:
    return {"ok": True}


@app.get("/aws/resources")
def list_resources() -> list[dict]:
    return STATE["resources"]


@app.get("/aws/resources/{service}")
def get_resource(service: str) -> dict:
    for resource in STATE["resources"]:
        if resource["application"].lower().replace(" ", "-") == service.lower():
            return resource
    raise HTTPException(status_code=404, detail="Service not found")


@app.get("/aws/accounts")
def list_accounts() -> list[dict]:
    return STATE["accounts"]


@app.get("/aws/changes")
def list_changes() -> list[dict]:
    return STATE["changes"]


@app.post("/aws/demo/migrate")
def migrate() -> dict:
    return migrate_aws(STATE)


@app.post("/aws/demo/reset")
def reset() -> dict[str, bool]:
    global STATE
    STATE = clone_seed(aws_seed)
    return {"ok": True}
