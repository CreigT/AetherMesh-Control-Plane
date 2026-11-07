# AetherMesh Control Plane — steps 3–5

Doctrine: motion by default. Review only on over-cap and irreversible.

Defaults (override anytime):
- `REVIEW_CAP_USD=50`
- `FREEZE_CAP_USD=250`
- First loop: **one janitorial job** (not a catalog)

| Step | Service | Port |
|---|---|---|
| 3 | Event Trigger (`src/event/app.py`) | 8100 |
| 4 | Governance (`src/governance/app.py`) | 8110 |
| 4 | Warden gate (`src/warden/app.py`) | 8120 |
| 5 | Money loop (`src/loop/app.py`) | 8130 |

PAMF 8080 · IdMA 8090 stay in their own repos.

## Run the slice

```bash
pip install -r requirements.txt
PYTHONPATH=. uvicorn src.event.app:app --port 8100
PYTHONPATH=. uvicorn src.governance.app:app --port 8110
WARDEN_PAMF_URL=http://127.0.0.1:8080 PYTHONPATH=. uvicorn src.warden.app:app --port 8120
PYTHONPATH=. uvicorn src.loop.app:app --port 8130
```

## One job through the loop

```bash
curl -s -X POST localhost:8130/v1/loop/jobs \
  -H 'Content-Type: application/json' \
  -d '{"customer":"Fontana Daycare","amount_usd":45,"description":"nightly floor work"}'
```

$45 → admit, book, collect-stub, ledger, tax reserve.  
$80 → review queue, no collect.  
$300 → Warden kill + PAMF freeze request.

Collect and ads are **stubs**. No live Stripe.

## SECURE

- Caps are explicit and overridable (REVIEW $50 / FREEZE $250).
- Over-cap actions route to review or freeze; they do not auto-execute.
- Collect and payment steps are stubs only. No live Stripe or real fund movement.
- Services are separate processes. No automatic credential sharing across them.
- A requested freeze is not hardware isolation or tamper-proof enforcement.

## VERIFY

Verification is evidence of threshold behavior and stub boundaries, not production claims.

- Confirm $45 proceeds through stubs without review.
- Confirm $80 enters review and does not collect.
- Confirm $300 triggers Warden kill + freeze request.
- Confirm no live external payment execution occurs.

See `docs/VERIFY_WALKTHROUGH.md` for the concrete steps.

## DOCUMENT

- This README is the public summary of the slice.
- Full operational card: `docs/OPERATIONAL_CARD.md`
- Verification walkthrough: `docs/VERIFY_WALKTHROUGH.md`
- Documentation defines the intended thresholds and stub boundaries; code is the illustrated implementation.

## Relevance to secure systems / edge / defense
A control plane can help edge and defensive agents separate requested operations from policy-controlled execution. Existing collection and payment steps include stubs and are not production enforcement.

## Trusted execution and verifiability
The event, governance, Warden and job-loop services illustrate a policy-mediated control-plane pattern: request intake, risk thresholds, review gates, freeze requests, and traceable decisions. A requested freeze is not proof of hardware-level isolation or tamper-proof enforcement. Validate authorization, failure handling, audit integrity and kill-switch behavior before any sensitive deployment.
