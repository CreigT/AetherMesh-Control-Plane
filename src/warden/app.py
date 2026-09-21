"""Warden gate — admit / review / kill. Kill calls PAMF freeze."""

from __future__ import annotations

import os
from typing import Any

import httpx
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Warden Gate", version="0.1.0")
PAMF = os.environ.get("WARDEN_PAMF_URL", "http://127.0.0.1:8080")
GOV = os.environ.get("WARDEN_GOV_URL", "http://127.0.0.1:8110")
frozen_local = False


class GateReq(BaseModel):
    actor: str
    kind: str
    amount_usd: float = 0
    irreversible: bool = False
    memory_ids: list[str] = []


def _eval(body: GateReq) -> dict[str, Any]:
    try:
        r = httpx.post(f"{GOV}/v1/governance/evaluate", json=body.model_dump(), timeout=3.0)
        r.raise_for_status()
        return r.json()
    except Exception:
        if body.amount_usd >= 250:
            return {"verdict": "kill", "decision_id": "local-kill"}
        if body.amount_usd >= 50 or body.irreversible:
            return {"verdict": "review", "decision_id": "local-review"}
        return {"verdict": "admit", "decision_id": "local-admit"}


def _freeze() -> dict[str, Any]:
    global frozen_local
    frozen_local = True
    try:
        r = httpx.post(
            f"{PAMF}/v1/memory/admin/freeze",
            json={"frozen": True, "actor": "warden", "reason": "kill"},
            timeout=3.0,
        )
        return {"pamf": r.status_code, "body": r.text[:200]}
    except Exception as exc:
        return {"pamf": "unreachable", "error": str(exc), "local_frozen": True}


@app.get("/v1/warden/health")
def health() -> dict[str, Any]:
    return {"status": "ok", "local_frozen": frozen_local, "pamf": PAMF}


@app.post("/v1/warden/gate")
def gate(body: GateReq) -> dict[str, Any]:
    ev = _eval(body)
    if ev.get("verdict") == "kill":
        ev["freeze"] = _freeze()
    return ev


@app.post("/v1/warden/thaw")
def thaw() -> dict[str, Any]:
    global frozen_local
    frozen_local = False
    try:
        httpx.post(
            f"{PAMF}/v1/memory/admin/freeze",
            json={"frozen": False, "actor": "owner", "reason": "thaw"},
            timeout=3.0,
        )
    except Exception:
        pass
    return {"frozen": False}
