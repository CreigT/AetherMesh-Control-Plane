"""Governance — evaluate action against caps. Motion below review cap."""

from __future__ import annotations

import os
import uuid
from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI(title="Governance Agent", version="0.1.0")
REVIEW = float(os.environ.get("REVIEW_CAP_USD", "50"))
FREEZE = float(os.environ.get("FREEZE_CAP_USD", "250"))
queue: list[dict[str, Any]] = []
IRREVERSIBLE = {"wire", "ach", "tax_file", "contract_sign", "ad_spend"}


class Action(BaseModel):
    actor: str
    kind: str
    amount_usd: float = 0
    irreversible: bool = False
    memory_ids: list[str] = Field(default_factory=list)
    note: str | None = None


@app.get("/v1/governance/health")
def health() -> dict[str, Any]:
    return {"status": "ok", "review_cap_usd": REVIEW, "freeze_cap_usd": FREEZE, "queued": len(queue)}


@app.post("/v1/governance/evaluate")
def evaluate(body: Action) -> dict[str, Any]:
    decision_id = f"dec_{uuid.uuid4().hex[:10]}"
    irreversible = body.irreversible or body.kind in IRREVERSIBLE
    if body.amount_usd >= FREEZE or (irreversible and body.amount_usd >= REVIEW):
        verdict = "kill"
    elif body.amount_usd >= REVIEW or irreversible:
        verdict = "review"
        queue.append({"decision_id": decision_id, **body.model_dump()})
    else:
        verdict = "admit"
    return {
        "decision_id": decision_id,
        "verdict": verdict,
        "review_cap_usd": REVIEW,
        "freeze_cap_usd": FREEZE,
        "memory_ids": body.memory_ids,
    }


@app.get("/v1/governance/queue")
def show_queue() -> dict[str, Any]:
    return {"items": queue}


@app.post("/v1/governance/queue/{decision_id}/resolve")
def resolve(decision_id: str, verdict: str = "admit") -> dict[str, str]:
    global queue
    queue = [q for q in queue if q["decision_id"] != decision_id]
    return {"decision_id": decision_id, "verdict": verdict}
