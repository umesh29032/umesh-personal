---
id: l2-data-flows-worker-reporting-flow
type: data-flow
status: active
owner: handwritten
scope: worker_reporting_flow (data-flow)
anchors: —
verified: 2026-07-13
---

# Data flow: Worker Reporting

> **TL;DR** — A worker submits per-line `{color, size, qty}` from their phone;
> `worker_task_service` writes IMMUTABLE WorkerStageContribution rows, then "Submit
> & Complete" marks the task done and FREEZES `expected_*` (visibility, not money —
> money is written only at settlement, ADR-0005). Operational diagram + debug +
> constraints below.

```
INPUT (phone form) VALIDATION SERVICE DB WRITE
───────────────── ────────── ─────── ────────
lines: [{color_id, → assignment gate (own WST) + LIVE Stage-Access gate (C-3) → worker_task_service → INSERT
 size_id, + schema parse.report_contributions production_workerstagecontribution
 reported_qty}] + qty > 0 (reported_quantity, IMMUTABLE)
 on Submit:.complete_worker_task → UPDATE WST.status=completed
 freeze expected_* → UPDATE WSC.expected_rate/earning
```
**Reads:** WST (own), stage handler schema. **Events:** none until settlement.
**Constraints:** WSC qty>0; WST ≤1 active/(sr,worker). **Future:** barcode scans
feed the same service (C-TM); none-mode skips report (TM-1).
**Membership validation (C-2, 2026-07-06):** `_parse_lines` refuses any choice value
(`color_id`/`size_id`) not present in that field's schema `options`. On a pool stage the
worker-scoped schema lists only the worker's active allocation, so a forged POST for an
unallocated dim — or from an unallocated worker (empty options) — is refused at parse,
independent of `ENFORCE_ALLOCATION_BOUND`. Nothing is written; task stays open.
**Worker instruction line (Phase-3, 2026-07-06):** the report hero renders `stage_record.workflow_stage.stage.description` (floor-language, owner-editable per Stage) as the worker's one-line prompt, falling back to the generic prompt when blank — display-only, no engine change.
**Damaged/scrap + machine + timestamps (pre-Phase-3, 2026-07-06):** every line may
carry `damaged_quantity` (4th observation: capacity yes, pool no, pay no) and is
stamped with `machine_code` (worker's open machine assignment); the task stamps
`first_report_at` once. **Void-report (D):** a manager voids a wrong SUBMIT in Report
Review (audited REPORT_VOIDED + reason) → task CANCELLED (lines = inert history) →
fresh task → worker re-reports. Verification never increases production.
**Prefill (J-2, 2026-07-06):** with no saved draft, the form pre-renders one editable row
per allocated colour+size pair (`schema['initial_lines']` from the handler; labels only,
never quantities — blind rule holds). Saved drafts still win.
**Generic-operation mode (R10-B, 2026-07-05):** config-only stages (registry fallback) use the archetype schema — Good + Alter + Missing per line through this SAME chokepoint; only good freezes/pays (D2). **Checklist mode (R8, 2026-07-05):** a stage whose `contribution_schema` sets
`mode='checklist'` (Pattern Design) swaps the line form for a tick-list; the
view dispatches to `handler.checklist_submit`, which syncs the stage's
verification rows (same truth as the console) and reports ONE line qty=1
through this SAME chokepoint — fixed pay = rate × 1. Freeze note: since the
A360 follow-up, `expected_*` freezes **0 on grouped AND non-payable
(`credits_workers=False`) stages** (`effective_pay_rate`, one rule).
**Debug:** wrong/duplicate qty → `reported_quantity` is immutable, correct via
`verified_quantity` (`worker_task_service.set_verified_quantity`); no earning shown
→ `expected_*` freezes only on complete. Full call chain + debug points:
[../REQUEST_JOURNEYS/worker_reporting.md](../REQUEST_JOURNEYS/worker_reporting.md).
