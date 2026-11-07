# AetherMesh Control Plane Operational Card
**Policy-mediated control plane slice (event → governance → Warden gate → money loop)**  
Sponsored by CREIGNIFICENT LLC · Status: Prototype slice with stubs

## Purpose
Illustrate a motion-by-default control plane for a single janitorial money loop: request intake, risk thresholds, review/freeze gates, and traceable decisions. Review only on over-cap or irreversible actions.

## Trust Boundaries
- Caps are explicit: REVIEW_CAP_USD=50, FREEZE_CAP_USD=250 (overridable).
- $45 example → admit and proceed (stubs).
- $80 example → review queue, no collect.
- $300 example → Warden kill + PAMF freeze request.
- Collect and ads are stubs. No live Stripe or real payment execution.
- Services are separate (ports 8100–8130). No automatic cross-service credential sharing.
- A requested freeze is not proof of hardware isolation or tamper-proof enforcement.

## Core Flow
POST /v1/loop/jobs → event/governance check → Warden gate (if threshold) → stub collect/ledger or review/freeze

## Current Enforcement (slice)
- Threshold logic present for review and freeze.
- Warden gate and PAMF freeze request are implemented as illustrated calls.
- Collection and payment steps are stubs only.
- No durable production store or live external integrations in this slice.

## Explicit Non-Goals (current)
- Does not process real payments.
- Does not provide hardware-level isolation.
- Does not automatically enforce across unrelated agents.
- Stubs are not production enforcement.

## Verification Points
1. $45 job proceeds through stubs without review.
2. $80 job enters review queue and does not collect.
3. $300 job triggers Warden kill + freeze request.
4. No live Stripe or real fund movement occurs.

## Next Secure Step
Replace stubs with real (or clearly isolated) execution paths and add durable audit logging before any sensitive deployment. Validate kill-switch and freeze behavior against actual failure cases.
