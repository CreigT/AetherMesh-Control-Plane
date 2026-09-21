from fastapi.testclient import TestClient

from src.governance.app import app

c = TestClient(app)


def test_under_cap_admits() -> None:
    r = c.post("/v1/governance/evaluate", json={"actor": "loop", "kind": "job_accept", "amount_usd": 45})
    assert r.json()["verdict"] == "admit"


def test_over_review_queues() -> None:
    r = c.post("/v1/governance/evaluate", json={"actor": "loop", "kind": "job_accept", "amount_usd": 80})
    assert r.json()["verdict"] == "review"


def test_over_freeze_kills() -> None:
    r = c.post("/v1/governance/evaluate", json={"actor": "loop", "kind": "job_accept", "amount_usd": 300})
    assert r.json()["verdict"] == "kill"
