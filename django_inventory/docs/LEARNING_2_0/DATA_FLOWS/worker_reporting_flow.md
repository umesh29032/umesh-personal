# Data flow: Worker Reporting

> **TL;DR** — A worker submits per-line `{color, size, qty}` from their phone;
> `worker_task_service` writes IMMUTABLE WorkerStageContribution rows, then "Submit
> & Complete" marks the task done and FREEZES `expected_*` (visibility, not money —
> money is written only at settlement, ADR-0005). Operational diagram + debug +
> constraints below.

```
INPUT (phone form) VALIDATION SERVICE DB WRITE
───────────────── ────────── ─────── ────────
lines: [{color_id, → assignment gate (own WST) → worker_task_service → INSERT
 size_id, + schema parse.report_contributions production_workerstagecontribution
 reported_qty}] + qty > 0 (reported_quantity, IMMUTABLE)
 on Submit:.complete_worker_task → UPDATE WST.status=completed
 freeze expected_* → UPDATE WSC.expected_rate/earning
```
**Reads:** WST (own), stage handler schema. **Events:** none until settlement.
**Constraints:** WSC qty>0; WST ≤1 active/(sr,worker). **Future:** barcode scans
feed the same service (C-TM); none-mode skips report (TM-1).
**Debug:** wrong/duplicate qty → `reported_quantity` is immutable, correct via
`verified_quantity` (`worker_task_service.set_verified_quantity`); no earning shown
→ `expected_*` freezes only on complete. Full call chain + debug points:
[../REQUEST_JOURNEYS/worker_reporting.md](../REQUEST_JOURNEYS/worker_reporting.md).
