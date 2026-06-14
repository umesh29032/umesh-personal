# production — every important file (FILE_MAP)

## TL;DR (1 min)
FILE_MAP: every important file in this app and how they connect.

> Junior orientation: open this when you touch the production app. Each entry =
> what the file is + the key classes/functions + how it connects.

## models/ (one file per domain concern → tables)
- `core.py` — **Product** (the garment type), **Stage** (global stage library),
 **WorkflowStage** (per-product policy row: order, `cost_rate` [dual-duty:
 standard cost + default pay, ADR-0009], `credits_workers`, `cost_billed_at`
 [grouping]), **WorkflowStageRoleRate** (per-role pay override).
- `adda.py` — **Adda** (`code` unique auto, `status`, `current_stage`),
 **AddaStageRecord** (one per Adda×WorkflowStage; frozen `processing_cost`;
 `pending_report_workers` helper for P2). Polymorphic parent of typed records.
- `worker_task.py` — **WorkerStageTask** (WHO; partial-unique active per
 sr+worker), **WorkerStageContribution** (WHAT; reported immutable, verified
 correction, frozen expected_*, `settlement_line` provenance). THE production truth.
 **S3: `good_quantity` (NOT NULL, payable — settlement pays this) + `alter_quantity`/
 `missing_quantity` (immutable observations, default 0). `reported_quantity` dual-written
 = good (renamed-not-dropped @S6). Constraint `wsc_gam_nonneg_sum_positive` (each≥0 ∧ sum>0).**
- `layering.py` — LayeringRecord, LayeringRollEntry (per-roll verify),
 RemainingClothOfClothRoll (leftover + weight, mandatory at complete).
- `cutting.py` — CuttingRecord, ProductSize, CuttingPatternVerification,
 CuttingPieceBreakup (size denominators), CuttingBundle(+items), ProductPattern.
- `barcode.py` — BarcodeGenerationRecord.

## services/ (ALL writes; views never write)
- `worker_task_service.py` ★ — sole WST/WSC writer (chokepoint; CI gate 4/4).
 Key: set_stage_workers, report_contributions, complete_worker_task,
 set_verified_quantity, resolve_stage_tasks_on_complete.
- `adda_service.py` — create_adda (race-safe per-product code via select_for_update), stage advance.
- `cost_service.py` ★ — freeze/clear processing_cost; role_rate_for (grouped-member guard); **`resolved_payable_rate` (S2): the single resolved-rate source — grouped→0/override/base/0 — for the AddaStageRoleRate snapshot + complete-time freeze.**
- `stage_rate_service.py` — **Foundation S2: sole writer of `AddaStageRoleRate` (frozen resolved payable rate per (stage_record, role)). `ensure_stage_role_rates` (snapshot at stage-start, idempotent) · `frozen_rate_for(lock=)` · `mark_locked` (first-completion immutability) · `edit_until_lock` (management, refuses post-lock). `rerate_stage_role` (S1.1) — super-admin override of the completion lock UNTIL settlement: recalcs every completed-but-unsettled contribution's expected_rate/expected_earning, refuses once actively settled, mandatory `reason`, writes `RateCorrectionAudit`. Lock order: task → AddaStageRoleRate → WorkerStageContribution (contracts 1 & 2; M1 per-(stage,role) lock).**
- `rate_views.py` (S1.1) — super-admin-only `StageRateListView` (per-Adda role-rates: rate/locked/settled) + `StageRateCorrectView` (current→new rate + mandatory reason + confirm → `rerate_stage_role`). `forms/rate_forms.py` = `StageRateCorrectionForm`. Templates `stage_rate_list.html` (mobile-first cards) + `stage_rate_correct.html` (form shell). Entry: super-admin "Stage Rates" link on adda_detail.
- `models/core.py` → `RateCorrectionAudit` (S1.1) — append-only typed financial audit (actor/stage_record/role/old_rate/new_rate/recalc_count/reason); PROTECT FKs; written only by `rerate_stage_role`.
- `flow_service.py` — WorkflowStage CRUD + grouping guards.
- `_shared.py` — auth helpers + `reopen_stage_record` (template-method skeleton;
 V2-3 settled-stage block lives here).
- `access_service.py` — skill-gating reads. `activity_service.py` — timeline UNION.
- `product_service.py`, `product_size_service.py` — masters. `reconciliation_service.py` — read-only counter check.
- `operations_digest.py` — read-only management "morning pulse" (P1-1): stalled/pending-reports/active/completed-today + payroll totals. Foundation-independent; rendered on the Operations landing (management-gated in the view).

## stages/ — the OPEN-CLOSED engine
`base/handler.py` (StageHandler contract: typed record, complete validations,
`cost_quantity`, `contribution_schema`) + `base/registry` + per-stage packages
(layering / cutting / cutting_pattern / barcode_generation = handler + service each).
**New stage = new package; worker UI unchanged.**

## views/ (parse → gate → ONE service → redirect; FILE MAPs in-code)
stage_views.py (1.4k — layering+cutting consoles; 6 sections at top),
worker_report_views.py (★ phone report + AddaReportReviewView P1),
pattern_stage_views.py, barcode_gen_views.py, adda_views.py, flow_views.py,
costing_views.py, dashboard.py, product_views.py, pattern_views.py,
access_views.py, mixins.py (ProductionRoleMixin, StageViewAccessMixin).

## forms/ — adda_forms, layering, cutting, cutting_pattern, product_forms,
`_shared.py` (worker checkbox→chip widget). Plain Django forms (not ModelForm-heavy).

## urls.py — route-group map in its header. management/commands/reconcile_denorm.py
— denormalized-counter sanity. templates/production/ — `_stage_panel_*.html`
(operator consoles), `worker_report*.html` (phone), `product_flow.html` (editor).

## transaction boundaries here
adda_service.create_adda (advisory + select_for_update on counter);
_shared.reopen_stage_record (select_for_update SR); worker_task_service writes
(atomic). Money atomicity is in expense, not here.

---
*Canonical depth (don't duplicate — read these):* business view →
[config/production/README.md](../../../../config/production/README.md) · file-by-file dev
view → [docs/apps/production/GUIDE.md](../../../apps/production/GUIDE.md) · this folder =
the NAVIGATION + FLOW layer only.*
