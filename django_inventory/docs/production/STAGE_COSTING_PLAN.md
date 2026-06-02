# Stage Costing + Unified Tracking — Architecture Review & Implementation Plan

> **Status:** PLAN ONLY — no code written. Produced 2026-06-01 by a 4-agent architecture
> debate + a cutting data-flow audit. All claims verified against live code.
> **Headline:** **0 new models** (baseline) / **+1 field** (delta). Costing rides on a
> template-default + frozen-snapshot split; unified tracking extends `AddaHistory`.
>
> **Companion doc:** `PAYROLL_ARCHITECTURE.md` — the full worker payroll / ledger / advances /
> `expense`-app design. **It supersedes this doc's R2 "equal-split earnings"** (see note in §1).

---

## 0. The four goals (recap)

- **G1 Stage Costing** — attach processing cost to stage execution; rate changes over time; methods `per_piece` / `per_bundle` / `per_layer` / `fixed_cost`.
- **G2 Unified Stage Tracking** — one admin timeline: active/completed/reopened stages, worker assignments, bundle creation, barcode generation, all major actions.
- **G3 Expense-App Compatibility** — future `expense` app computes worker earnings / payouts / profitability with zero production schema churn later.
- **G4 Keep Model Count Low** — prefer fields on existing models; target 0 new models.

---

## 1. Final Recommendation (the decisions)

| Decision | Verdict | Why |
|---|---|---|
| **Where the rate lives** | **`WorkflowStage`** (binding, per-product-per-stage) + **`Stage`** (nullable library default) | A global `Stage` rate can't price T-SHIRT cutting ≠ NIKKAR cutting. `WorkflowStage` is the per-product-per-stage join. `Stage` only seeds a default at flow-attach. |
| **Where the cost is recorded** | **`AddaStageRecord`** — frozen snapshot | Price-at-time-of-order. The execution row is the natural home of the manufacturing-cost truth. |
| **Store vs compute `processing_cost`** | **STORE** (frozen `Decimal` column) | Unanimous. A live property re-derives *closed money* from quantities that mutate on reopen + can't `SUM()` in SQL. |
| **Where to freeze** | **Inside `adda_service.advance_to_next_stage`** | The ONE universal choke point every complete path funnels through. |
| **History** | **Extend `AddaHistory`** (new ChangeTypes + `metadata` JSON + `stage_record` FK) | A second generic log would split the single-writer law. |
| **New models** | **0** (baseline) | Fields on `Stage` / `WorkflowStage` / `AddaStageRecord` / `AddaHistory`. |
| **Cutting model-collapse** | **DEFER** | Orthogonal to costing; high blast radius. Separate follow-up PR. |

> ⚠️ **SUPERSEDED — R2 worker earnings.** This plan originally proposed a read-only *equal-split*
> earnings estimate (`processing_cost ÷ workers`). The owner has since confirmed that is **wrong**
> (workers contribute different quantities). **`processing_cost` here is MANUFACTURING COST only**
> (product costing / profitability). Worker **earnings are allocation-driven** and live entirely in
> the `expense` app — see `PAYROLL_ARCHITECTURE.md`. Also: the "`workers` M2M → `through=expense.StageWorkAssignment`"
> idea is **dead** — `StageWorkAssignment` is a standalone allocation table (a worker has many
> allocations per stage). Keep `AddaStageRecord.workers` a bare M2M (roster).

### The decisive engineering insight

Freeze the cost **inside `advance_to_next_stage` (`adda_service.py:120`)**, not inside each `complete_*`.
It's the single choke point all complete paths call; it reads `adda.current_stage` (the stage being
**left**) before moving it → resolves the just-completed `AddaStageRecord` reliably; and it does its
**own** `sr.save(update_fields=[cost columns])` so the narrow `update_fields` lists in each
`complete_*` can't silently drop the new columns.

---

## 2. Cutting Data-Flow Map

| Model | Grain (one row =) | Written by | Derived from |
|---|---|---|---|
| `CuttingPieceBreakup` | planned count per (size,color,pattern); `consumed_count` | `upsert_breakup_row` | operator-entered planning table |
| `CuttingBundleItem` | **actual** count per (bundle,pattern,color); `source_breakup` FK | `add_pieces_to_bundle`, `add_item_to_bundle` | breakup.available_count — true line-level source |
| `CuttingBundle` | per-size container; `total_pieces` denorm | `create_bundle` + `_recompute_bundle_total` | Σ its items |
| `CuttingRecord.pieces_cut` | whole-Adda total | `_complete_cutting_*` | Σ bundle items |
| `AddaProductSizeColorPieceBreakdown` | frozen per-(size,color), patterns collapsed | `_materialize_breakdown` | Σ bundle items by (size,color) |
| `tracking.BarcodeBatch` | per-(adda,size,color) seq range | `generate_from_breakdown` | the frozen breakdown |

**Real bug found:** `add_item_to_bundle` / `add_bundle_item` create items **without** `source_breakup`,
bypassing `consumed_count` → same physical piece double-allocated. The whole-Adda total is materialized
in **5 places**. **Verdict: DEFER cutting collapse** (orthogonal to costing, high risk). Fix the
`source_breakup` bypass in a separate follow-up PR. Keep all 5 cutting models (`per_bundle` costing
NEEDS `CuttingBundle`; the breakdown is cross-stage decoupling).

---

## 3. Model Changes (baseline — 0 new models)

`CostMethod` TextChoices: `per_piece` / `per_bundle` / `per_layer` / `fixed_cost`.

### `Stage` — nullable library seed (never binding)
| Field | Type |
|---|---|
| `default_cost_method` | `CharField(16, choices=CostMethod, blank=True)` |
| `default_cost_rate` | `DecimalField(10,4, null=True, blank=True)` |

### `WorkflowStage` — BINDING per-product rate
| Field | Type | Notes |
|---|---|---|
| `cost_method` | `CharField(16, choices=CostMethod, default='per_piece')` | only grain that lets NIKKAR-cutting ≠ T-SHIRT-cutting |
| `cost_rate` | `DecimalField(10,4, null=True, blank=True)` | `null` = unpriced → freeze stores NULL, **never 0** |

### `AddaStageRecord` — FROZEN manufacturing-cost snapshot
| Field | Type | Notes |
|---|---|---|
| `cost_method_snapshot` | `CharField(16, choices=CostMethod, blank=True)` | frozen at completion |
| `cost_rate_snapshot` | `DecimalField(10,4, null=True, blank=True)` | |
| `cost_quantity_snapshot` | `DecimalField(12,2, null=True, blank=True)` | Decimal (admits future per_meter/per_kg) |
| `processing_cost` | `DecimalField(12,2, null=True, blank=True)` | STORED frozen = quantize(rate×qty,2); NULL when unpriced. **Manufacturing cost, NOT worker pay.** |
| `cost_frozen_at` | `DateTimeField(null=True, blank=True)` | strictly advances on every re-freeze |

### `AddaHistory` — extend
| Field | Type |
|---|---|
| `metadata` | `JSONField(default=dict, blank=True)` |
| `stage_record` | `FK(AddaStageRecord, SET_NULL, null, '+')` |
| ChangeType `+=` | `STAGE_STARTED, WORKERS_ASSIGNED, BUNDLE_CREATED, BARCODES_GENERATED, EXPORTED, COST_FROZEN` |

---

## 4. Service Changes (baseline)

- **NEW `production/services/cost_service.py`:** `freeze_stage_cost(sr, user)` (own `save(update_fields=[...])`), `_quantity_for(sr)` (per_layer→`lay_count`, per_piece→`pieces_cut`/`total_barcodes`, per_bundle→`bundles.count()`, fixed→None), `clear_stage_cost(sr)`, `recompute_stage_cost(sr)`.
- **`adda_service.advance_to_next_stage`:** THE FREEZE SITE — resolve the leaving stage's `sr`, call `freeze_stage_cost`, log `COST_FROZEN`.
- **All `reopen_*`:** call `clear_stage_cost(sr)` under the existing `select_for_update`.
- **Event wiring:** `WORKERS_ASSIGNED` (create_adda + start_*), `BUNDLE_CREATED`, `BARCODES_GENERATED`, `EXPORTED`.
- **`history_service.log_adda`:** widen `(…, metadata=None, stage_record=None)`, stays sole writer.
- **`activity_service`:** teach verb_map the new types.
- **NEW test `test_cost_snapshot_invariants.py`:** processing_cost == quantize(rate×qty) for frozen+priced rows only; NULL-rate→NULL-cost; reopened→NULL; fixed_cost→NULL qty, cost==rate.

---

## 5. Migration Plan

1. Add `CostMethod` enum.
2. Additive production migration (Stage ×2, WorkflowStage ×2, AddaStageRecord ×5) — all nullable/defaulted → zero-downtime.
3. Additive tracking migration (`AddaHistory.metadata` default=dict, `stage_record` FK).
4. **No backfill** of `processing_cost` (NULL = honest "cost-unknown").
5. Optional RunPython/admin to seed `Stage.default_cost_method` per code.
6. Wire freeze + reopen-clear + history events. Run suite.
7. Add invariant + metadata payload tests; document in OVERVIEW.md.
8. Manual exercise (rate edit doesn't change history; reopen→recomplete re-freezes; unpriced→NULL).

## 6. Rollback Plan

Code-only revert leaves nullable columns harmless. Full schema downgrade clean (purely additive). No backfill → reversing loses only post-deploy snapshots (recomputable). Manufacturing chain untouched. Partial: short-circuit `freeze_stage_cost` to no-op.

## 7. Risk Register (highlights)

| Risk | Sev | Mitigation |
|---|---|---|
| Freeze resolves wrong `AddaStageRecord` | HIGH | advance reads `cur` before mutating; assert `completed_at` set |
| New columns dropped by narrow `update_fields` | HIGH | freeze does its OWN `save(update_fields=[cost cols])` |
| Reopen leaves stale cost | HIGH | `clear_stage_cost` in every reopen; `cost_frozen_at` strictly advances |
| NULL rate booked as 0 | MED | store NULL; surface "unpriced"; never coalesce |
| Decimal scale drift | MED | rate 4dp, cost 2dp, ROUND_HALF_UP |

---

## 8. Owner-locked decisions (2026-06-01)

- Cutting method = **per_piece**. Rate precision = **4dp rate / 2dp cost**.
- Rate **effectively mandatory** (UI-required; DB nullable; succeed-and-flag net).
- `cutting_pattern` = grouped **member only**, never a fixed_cost payer.

---
---

# DELTA — Cost Grouping (`paid_at`) + Mandatory Rate (2026-06-01)

> Net schema cost: **ONE new field — `WorkflowStage.cost_billed_at`.** Validated by a 7-agent debate
> (`wf_2baf413a-025`). **Earnings display (R2) moved out — see `PAYROLL_ARCHITECTURE.md`.**

## R3 Cost Grouping — Final Decision

**Field:** `WorkflowStage.cost_billed_at = ForeignKey('self', on_delete=SET_NULL, null=True, blank=True, related_name='billed_stages')`. NULL = self-paid.
- Home is **WorkflowStage** (per-product topology; co-locates with the rate). No `Stage` seed.
- **Paying stage** = `cost_billed_at IS NULL`. **Grouped** = set; labor rolls up to the payer.
- Canonical T-SHIRT today: `layering.cost_billed_at = cutting_ws`, `cutting_pattern.cost_billed_at = cutting_ws`, `cutting = NULL` (payer, per_piece). One master does all three, paid once at cutting.

**Freeze rule** (`freeze_stage_cost` dispatches on `cost_billed_at_id`):
- Grouped → `processing_cost = Decimal('0.00')` (priced-zero, NOT NULL), snapshots blank/NULL, `COST_FROZEN.metadata = {'billed_at_ws': <payer WorkflowStage id>}`.
- Paying → freeze normally with own method/rate/quantity.
- **`0.00` (billed-elsewhere) vs `NULL` (unpriced) is load-bearing.** Store the payer's **WorkflowStage id** (payer `sr` may not exist when an upstream member freezes).

**Quantity:** payer uses its **own** `_quantity_for` (no cross-stage sum). **Reopen:** existing downstream-started guard makes reopening a grouped member under a complete payer impossible; `clear_stage_cost` suffices; attribute only when payer fully frozen.

**Guards** (form + `flow_service`, never DB CHECK): same product; strict `cost_billed_at.order > self.order`; single-hop only (target self-paid); payer must be priced + NOT fixed_cost; removal guard; reorder re-validation.

## R1 Rate Mandatory — Final Decision

UI-required, DB nullable. New `production/forms/flow.py::WorkflowStageCostForm` (`cost_rate.required = True`, strict `> 0`); `flow_service.set_stage_cost(...)` + new `set_cost` action in `ProductFlowEditView.post`; "Unpriced — set a rate" badge; `create_adda` priced-flow guard (grouped members exempt); freeze stays succeed-and-flag.

## Delta Model Changes

| Model | Field | Type | Notes |
|---|---|---|---|
| `WorkflowStage` | `cost_billed_at` | `FK('self', SET_NULL, null, blank, related_name='billed_stages')` | **The only new field in the delta.** NULL = self-paid. |
| `WorkflowStage` | `cost_rate` | (above) | gains form-level `required=True`; DB nullable. |

## Delta Migration / Rollback

New additive migration: `WorkflowStage.cost_billed_at` self-FK (all legacy rows → NULL). No backfill. Rollback: code-only revert harmless; schema downgrade clean.

*Full debate transcripts: `wf_802a4eb5-22f` (baseline), `wf_2baf413a-025` (delta).*
