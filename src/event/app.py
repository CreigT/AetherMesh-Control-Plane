"""Event Trigger Agent — CloudEvents in-process bus. Swap body for NATS later."""

from __future__ import annotations

import time
import uuid
from collections import defaultdict
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="Event Trigger Agent", version="0.1.0")
streams: dict[str, list[dict[str, Any]]] = defaultdict(list)
subs: dict[str, list[str]] = defaultdict(list)


class CloudEvent(BaseModel):
    type: str
    source: str
    subject: str | None = None
    data: dict[str, Any] = Field(default_factory=dict)


class Sub(BaseModel):
    type: str
    webhook: str


@app.get("/v1/events/health")
def health() -> dict[str, Any]:
    return {"status": "ok", "types": {k: len(v) for k, v in streams.items()}}


@app.post("/v1/events/publish", status_code=202)
def publish(evt: CloudEvent) -> dict[str, str]:
    rec = {
        "id": f"evt_{uuid.uuid4().hex[:12]}",
        "specversion": "1.0",
        "type": evt.type,
        "source": evt.source,
        "subject": evt.subject,
        "time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "data": evt.data,
    }
    streams[evt.type].append(rec)
    return {"id": rec["id"], "status": "accepted"}


@app.get("/v1/events")
def list_events(type: str | None = None, limit: int = 50) -> dict[str, Any]:
    if type:
        items = streams.get(type, [])[-limit:]
    else:
        items = []
        for v in streams.values():
            items.extend(v)
        items = items[-limit:]
    return {"items": items}


@app.post("/v1/events/subscribe")
def subscribe(body: Sub) -> dict[str, str]:
    if not body.webhook.startswith("http"):
        raise HTTPException(400, "webhook must be http(s)")
    subs[body.type].append(body.webhook)
    return {"status": "subscribed", "type": body.type}
