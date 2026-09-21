"""One janitorial job money loop. Stubs for collect. Caps via Warden."""

from __future__ import annotations

import os
import uuid
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Money Loop", version="0.1.0")
WARDEN = os.environ.get("LOOP_WARDEN_URL", "http://127.0.0.1:8120")
EVENTS = os.environ.get("LOOP_EVENT_URL", "http://127.0.0.1:8100")
TAX_RATE = 0.08
jobs: dict[str, dict[str, Any]] = {}
ledger: list[dict[str, Any]] = []


class NewJob(BaseModel):
    customer: str
    amount_usd: float
    description: str = "janitorial"


def _emit(typ: str, data: dict[str, Any]) -> None:
    try:
        httpx.post(
            f"{EVENTS}/v1/events/publish",
            json={"type": typ, "source": "loop", "subject": data.get("job_id"), "data": data},
            timeout=2.0,
        )
    except Exception:
        pass


def _gate(amount: float, kind: str, irreversible: bool = False) -> dict[str, Any]:
    try:
        r = httpx.post(
            f"{WARDEN}/v1/warden/gate",
            json={"actor": "loop", "kind": kind, "amount_usd": amount, "irreversible": irreversible},
            timeout=3.0,
        )
        return r.json()
    except Exception:
        return {"verdict": "review" if amount >= 50 else "admit"}


@app.get("/v1/loop/health")
def health() -> dict[str, Any]:
    return {"status": "ok", "jobs": len(jobs), "ledger_rows": len(ledger)}


@app.post("/v1/loop/jobs", status_code=201)
def create_job(body: NewJob) -> dict[str, Any]:
    g = _gate(body.amount_usd, "job_accept")
    job_id = f"job_{uuid.uuid4().hex[:8]}"
    job = {
        "job_id": job_id,
        "customer": body.customer,
        "amount_usd": body.amount_usd,
        "description": body.description,
        "state": "quoted",
        "gate": g,
    }
    if g.get("verdict") == "kill":
        job["state"] = "blocked"
        jobs[job_id] = job
        _emit("com.aethermesh.job.blocked", job)
        raise HTTPException(status_code=423, detail=job)
    if g.get("verdict") == "review":
        job["state"] = "review"
        jobs[job_id] = job
        _emit("com.aethermesh.job.review", job)
        return job
    job["state"] = "booked"
    jobs[job_id] = job
    _emit("com.aethermesh.job.booked", job)
    return _collect(job_id)


@app.post("/v1/loop/jobs/{job_id}/collect")
def collect(job_id: str) -> dict[str, Any]:
    return _collect(job_id)


def _collect(job_id: str) -> dict[str, Any]:
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(404, "no job")
    if job["state"] == "blocked":
        raise HTTPException(423, "blocked")
    if job["state"] == "review":
        raise HTTPException(409, "waiting owner review")
    g = _gate(job["amount_usd"], "collect")
    if g.get("verdict") != "admit":
        job["state"] = g.get("verdict")
        job["gate"] = g
        return job
    tax = round(job["amount_usd"] * TAX_RATE, 2)
    net = round(job["amount_usd"] - tax, 2)
    ledger.append({"job_id": job_id, "debit": "cash_stub", "amount": job["amount_usd"]})
    ledger.append({"job_id": job_id, "credit": "revenue", "amount": net})
    ledger.append({"job_id": job_id, "credit": "tax_reserve", "amount": tax})
    job["state"] = "collected"
    job["tax_reserve_usd"] = tax
    job["net_usd"] = net
    _emit("com.aethermesh.job.collected", job)
    return job


@app.post("/v1/loop/jobs/{job_id}/fulfill")
def fulfill(job_id: str) -> dict[str, Any]:
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(404, "no job")
    if job["state"] != "collected":
        raise HTTPException(409, f"state={job['state']}")
    job["state"] = "fulfilled"
    _emit("com.aethermesh.job.fulfilled", job)
    return job


@app.post("/v1/loop/jobs/{job_id}/refund")
def refund(job_id: str) -> dict[str, Any]:
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(404, "no job")
    g = _gate(job["amount_usd"], "refund", irreversible=False)
    if g.get("verdict") == "kill":
        raise HTTPException(status_code=423, detail=g)
    if g.get("verdict") == "review":
        job["state"] = "refund_review"
        return job
    ledger.append({"job_id": job_id, "debit": "revenue", "amount": job.get("net_usd", 0)})
    ledger.append({"job_id": job_id, "debit": "tax_reserve", "amount": job.get("tax_reserve_usd", 0)})
    ledger.append({"job_id": job_id, "credit": "cash_stub", "amount": job["amount_usd"]})
    job["state"] = "refunded"
    _emit("com.aethermesh.job.refunded", job)
    return job


@app.get("/v1/loop/jobs")
def list_jobs() -> dict[str, Any]:
    return {"items": list(jobs.values())}


@app.get("/v1/loop/ledger")
def show_ledger() -> dict[str, Any]:
    return {"items": ledger}
