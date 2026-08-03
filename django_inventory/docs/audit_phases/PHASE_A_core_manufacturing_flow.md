---
id: docs-audit-phases-phase-a-core-manufacturing-flow
type: receipt
status: active
owner: append-only
scope: audit
anchors: —
verified: 2026-07-18
---

# Phase A — Core Manufacturing Flow

**Scope:** product create → workflow stage create → rate setup → cloth intake → adda create → stage progression (layering→pattern→cutting→barcode) → worker assignment → worker reporting → stage completion → settlement draft → finalize → payment → My Earnings → advances.
**Method:** code reads of the production flow (views/services/forms) + the 68-route crawl (status/text/screenshots) + mobile shots. Settlement *math* is deferred to Phase B; this phase covers flow integrity, validation, gating, usability.

---

## Flow integrity verdict

The manufacturing pipeline is **architecturally sound**: schema-driven stage handlers (adding a stage needs no view edits), single-writer services for every contribution write, object-level worker isolation, and real validation at the service boundary. Two real defects (one 500-class, one confusing 404) and several owner-confirm items. No flow dead-ends found beyond the documented stage-gating.

---

## Findings

### MEDIUM

**A-1 — Non-numeric reported quantity crashes with HTTP 500.** *validation / robustness* · confidence high (code-confirmed)
- Repro: POST a worker report where a quantity field carries a non-numeric value (crafted POST, or any path that bypasses the browser `type=number`).
- Expected: a clean "enter a valid number" validation message. Actual: [worker_task_service.py:156](config/production/services/worker_task_service.py#L156) does `Decimal(str(line['reported_quantity']))` with no guard → `decimal.InvalidOperation`. The view only catches `ValidationError` ([worker_report_views.py:200](config/production/views/worker_report_views.py#L200)), so it propagates → **500**.
- Fix: wrap the `Decimal(...)` in try/except → `ValidationError("reported_quantity must be a number.")`. Effort: **S**.

**A-2 — settlement-start GET 500** — *(see Phase-1 A1; same root cause, restated here for flow completeness)* [config/expense/views.py:301](config/expense/views.py#L301). Effort **S**.

### LOW

**A-3 — Worker-report on a not-yet-started stage returns a raw 404.** *workflow / UX* · confidence high
- Repro: `GET /production/addas/3-PATTI-002/report/cutting/` (adda is still at layering; no cutting `AddaStageRecord`).
- Cause: `_resolve` → `get_object_or_404(AddaStageRecord, …stage__code=stage_type)` ([worker_report_views.py:137](config/production/views/worker_report_views.py#L137)). No record → bare 404.
- Impact: low — workers reach this via a task link, not by typing; but a stale link / early click yields an unexplained 404. Fix: friendly "this stage hasn't started yet" page. Effort: **S**.

### INFO / CONFIRM-INTENDED

**A-4 — Verification is possible but NOT mandatory before settlement.** *refines Phase-B B1*
- `AddaReportReviewView` (`/production/addas/<code>/review-reports/`, management-gated) lets management set `verified_quantity` via `set_verified_quantity`; reported is never mutated ([worker_report_views.py:207](config/production/views/worker_report_views.py#L207)). The verification surface **exists and works** — but nothing forces management to visit it, so an un-reviewed contribution settles at the worker's self-reported quantity. This is the precise mechanism behind Phase-B B1.

**A-5 — A stage can sit in a product flow unpriced.** *by-design; confirm*
- `add_stage_to_flow` leaves `cost_rate` NULL if no default is seeded, surfaced as an "unpriced" badge; cost-freeze "tolerates it (succeed-and-flag)" ([flow_service.py:49](config/production/services/flow_service.py#L49)). Layering runs at rate 0 by this path. Deliberate — confirm an unpriced stage paying ₹0 is the intended owner behavior (it interacts with Phase-B B2).

### OK / WORKS-WELL

- **Worker reporting surface is strong:** object-level isolation (resolves only the requester's own non-cancelled task, else 403 — [worker_report_views.py:144](config/production/views/worker_report_views.py#L144)); schema-driven & stage-agnostic; draft + submit both route through single-writer services (`save_draft_contributions` / `complete_worker_task`); submit requires ≥1 line; input bounded to 200 lines with PK int-guards.
- **Service-layer validation:** `reported_quantity > 0` enforced ([worker_task_service.py:157](config/production/services/worker_task_service.py#L157)); `verified_quantity` non-negative ([:267](config/production/services/worker_task_service.py#L267)); reported is immutable post-submit; cannot report on completed/cancelled tasks.
- **Flow editor (rate setup) guards:** no inactive/duplicate stage; cost-grouping rules enforced (payer must be later in flow, same flow, priced; self-paid stage must have rate > 0; fixed-cost stage can't be a group payer) — [flow_service.py:162-195](config/production/services/flow_service.py#L162).
- **Stage gating works:** downstream stages blocked with a clear message + recovery ("Cutting stage not yet reached. Complete Layering first." + Back-to-Adda) — visually confirmed on mobile.
- **Crawl page-health (flow routes):** all flow pages return 200 except the two defects above (A-2 500, A-3 404). No JS console errors of note.

---

## Phase A coverage / gaps for later

- Settlement **math** (draft/finalize/payment totals, advances) → **Phase B**.
- Concurrency (double-submit, two-tab stage-complete race) → **Phase I**.
- Visual usability of each create form (product/stage/adda) reviewed at status level only; deep UX → **Phase C**.
- Not visually re-confirmed this session (to conserve login budget): worker-report *locked* state render, full cutting workspace at the cutting stage (3-PATTI-002 is pre-cutting). Code-verified.

**Net Phase A:** flow is solid; fix A-1 (500 on bad number) and A-2 (settlement-start 500); decide A-4 (mandatory verification) and A-5 (unpriced stage) as policy.
