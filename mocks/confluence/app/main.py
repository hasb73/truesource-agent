from __future__ import annotations

from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from shared.demo_data import clone_seed, confluence_seed

app = FastAPI(title="TrueSource Mock Confluence", version="0.1.0")
STATE = clone_seed(confluence_seed)


class PageUpdate(BaseModel):
    content: str
    author: str = "TrueSource Reviewer"


@app.get("/health")
def health() -> dict[str, bool]:
    return {"ok": True}


@app.get("/confluence/pages")
def list_pages() -> list[dict]:
    return STATE["pages"]


@app.get("/confluence/pages/{page}")
def get_page(page: str) -> dict:
    return _page(page)


@app.put("/confluence/pages/{page}")
def update_page(page: str, payload: PageUpdate) -> dict:
    record = _page(page)
    record["content"] = payload.content
    record["author"] = payload.author
    record["version"] += 1
    record["last_modified"] = datetime.now(timezone.utc).isoformat()
    return record


@app.post("/confluence/demo/reset")
def reset() -> dict[str, bool]:
    global STATE
    STATE = clone_seed(confluence_seed)
    return {"ok": True}


def _page(page: str) -> dict:
    for item in STATE["pages"]:
        if item["id"] == page:
            return item
    raise HTTPException(status_code=404, detail="Page not found")
