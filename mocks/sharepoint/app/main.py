from __future__ import annotations

from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from shared.demo_data import clone_seed, sharepoint_seed

app = FastAPI(title="TrueSource Mock SharePoint", version="0.1.0")
STATE = clone_seed(sharepoint_seed)


class DocumentUpdate(BaseModel):
    content: str
    author: str = "TrueSource Reviewer"


@app.get("/health")
def health() -> dict[str, bool]:
    return {"ok": True}


@app.get("/sharepoint/documents")
def list_documents() -> list[dict]:
    return STATE["documents"]


@app.get("/sharepoint/documents/{document}")
def get_document(document: str) -> dict:
    return _document(document)


@app.put("/sharepoint/documents/{document}")
def update_document(document: str, payload: DocumentUpdate) -> dict:
    record = _document(document)
    record["content"] = payload.content
    record["author"] = payload.author
    record["version"] += 1
    record["last_modified"] = datetime.now(timezone.utc).isoformat()
    return record


@app.post("/sharepoint/demo/reset")
def reset() -> dict[str, bool]:
    global STATE
    STATE = clone_seed(sharepoint_seed)
    return {"ok": True}


def _document(document: str) -> dict:
    for item in STATE["documents"]:
        if item["id"] == document:
            return item
    raise HTTPException(status_code=404, detail="Document not found")
