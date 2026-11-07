# VERIFY Walkthrough — Threshold and Freeze Gates

**Goal:** Confirm review and freeze thresholds behave as documented and that no real payment occurs.

## Steps
1. Start the four services (event 8100, governance 8110, Warden 8120, loop 8130) as shown in the README.
2. POST a $45 job to localhost:8130/v1/loop/jobs. Confirm it admits and proceeds through stubs.
3. POST an $80 job. Confirm it enters the review queue and does not collect.
4. POST a $300 job. Confirm Warden kill and PAMF freeze request are triggered.
5. Inspect logs or responses for the decisions. Confirm no live Stripe call occurs.

## Pass Criteria
- Thresholds match the operational card ($50 review, $250 freeze).
- Review path blocks collection.
- Freeze path is requested on over-cap.
- No real external payment execution.

## Fail Criteria
- Over-cap job collects without review.
- Freeze is not requested on high amount.
- Unexpected live payment activity.

This is a single verification step for the illustrated slice. Expand only after stubs are replaced and audit is durable.
