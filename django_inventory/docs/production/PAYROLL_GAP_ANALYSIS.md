# Payroll, Earnings & Manufacturing-Cost — Gap Analysis & Plan

> Review of the built system (PR-1..PR-6, 255 tests green, uncommitted on `new_flask_app`) against the
> 10-question stakeholder review. Code-grounded by 4 audit agents (workflow `wf_69be917e-51b`), 2026-06-02.
> **Analysis only — no code changed.**

## Verdict

**The payroll / earnings / manufacturing-cost ENGINE is built, correct, and well-disciplined — but the system FAILS the stakeholder review as a usable product because nearly every required DASHBOARD/REPORT surface is missing.** The data model, services, freezing, and traceability are solid and need no rework. Gaps are concentrated in read/aggregation layers: no per-Adda cost rollup, no super-admin costing dashboard, no Role/Pieces columns on payroll, no Pieces/Adda-counts/stage-wise breakdown on the worker view, no role-based rates, no supervisor tier. **~70% of the engine done; ~30% of the surfaces (dashboards + 1 model + a few queries) remain.**

## 1. Current State Review (DONE — do not re-touch)

- **Manufacturing-cost engine:** `cost_service.{compute_processing_cost,freeze_stage_cost,clear_stage_cost}` handle all 4 methods, freeze method+rate+qty+cost onto `AddaStageRecord` at the single choke point `advance_to_next_stage`, clear on reopen, distinguish unpriced (NULL) vs grouped/priced-zero (0.00). Well-tested.
- **Allocation-driven earnings:** `allocate_stage_work` writes one `StageWorkAssignment` per slice with frozen `earning_amount_snapshot = rate × qty`, books a tagged ledger credit, enforces per-bundle-item over-allocation under `select_for_update`. Full FK traceability Worker→Qty→Stage→Adda.
- **Append-only money ledger:** `WorkerLedgerEntry`, live balance = Σcredits − Σdebits, reversal-based corrections, DB unique constraint on `reverses`. `ledger_service` sole writer.
- **Rate methods:** per_piece/per_bundle/per_layer/fixed, per-WorkflowStage, frozen at allocation.
- **Views:** worker `/expense/my/`, admin `/expense/payroll/`, per-worker detail (access-scoped), advance/payment entry. Cutting-workspace per-item allocation UI.

## 2. Gap Analysis

| Req | Status | Evidence | Gap |
|---|---|---|---|
| Q1 Worker earnings visibility | PARTIAL | `MyEarningsView` shows month/advance/pending + recent work; `worker_summary` computes total+paid | Lifetime + Paid computed but NOT rendered on `my_earnings.html`; no completed-Adda count; no pieces total |
| Q2 Worker dashboard | PARTIAL | 3 stat cards + flat feed | Missing Assigned/Active/Completed Adda counts, Pieces Produced, stage-wise rollup, Lifetime/Paid cards |
| Q3 Stage-wise cost / total per Adda | PARTIAL | `processing_cost` frozen per stage (correct) | No `SUM(processing_cost)` per Adda anywhere; per-stage cost never displayed |
| Q4 Super-admin per-Adda costing view | **MISSING** | `AddaDetailView.stages_overview` has no cost key; `adda_detail.html` has zero "cost" | No costing view class exists at all |
| Q5 Admin payroll User\|Role\|Pieces\|Earnings\|Pending\|Paid | PARTIAL | `PayrollOverviewView` = Worker\|Earnings\|Advances\|Payments\|Payable | Missing **Role** + **Pieces** columns (4 of 6 present) |
| Q6 Traceable Adda+Stage+Worker+Qty | **EXISTS** | `StageWorkAssignment.stage_record__adda` + `bundle_item` FK chain | Minor: ledger→adda is a 2-join hop (cosmetic) |
| Q7 Rate model incl ROLE-based | PARTIAL | 4 methods wired | **Role-based rate MISSING** — senior + helper earn identical (`rate = ws.cost_rate` regardless of `worker.role`) |
| Q8 Manufacturing cost ledger | PARTIAL | `processing_cost` IS the per-stage cost ledger (no separate table needed) | No Adda rollup, no profitability surface |
| Q9 Dashboards (4 tiers) | PARTIAL | Worker + admin payroll exist | **Supervisor tier MISSING entirely; super-admin factory costing MISSING**; home dashboard doesn't tier |
| Q10 Architecture chain | PARTIAL | 3 links real | No `ProductionOutput` node (collapsed into qty + typed records); PayrollEntry=`WorkerLedgerEntry`, CostLedger=`processing_cost` (renamed, two unreconciled money tracks) |

## 3. Payroll Architecture Plan

Engine is correct — mostly read/aggregation + 2 small additions:
1. **Q5** — add Role + Pieces to `PayrollOverviewView`: second grouped query `StageWorkAssignment...annotate(pieces=Sum('allocated_quantity'))`, merge by worker, `select_related('role')`. No model change.
2. **Q7** — role-based rates (the one new model, §8): resolve `rate = role_rate_for(ws, worker.role) or ws.cost_rate` in `allocate_stage_work` before freezing. `ws.cost_rate` stays fallback; snapshot preserves history.
3. **Q10** — reconciliation read (per-`stage_record` `processing_cost` vs `SUM(earning_amount_snapshot)`); document PayrollEntry=`WorkerLedgerEntry`, CostLedger=`processing_cost`. No new tables.
4. **Q6 (optional)** — nullable `adda` FK on `WorkerLedgerEntry` to skip the 2-join hop. Defer unless reporting needs it.

## 4. Worker Dashboard Plan (zero schema change)

1. `payroll_service.worker_production_stats(worker)` — `pieces_produced = Σ allocated_quantity`; Adda buckets via `.values('stage_record__adda__status').annotate(Count('stage_record__adda', distinct=True))` → Assigned/Active/Completed using `Adda.Status`.
2. `payroll_service.worker_stage_earnings(worker)` — `.values('stage_record__workflow_stage__stage__name').annotate(Sum('earning_amount_snapshot'), Sum('allocated_quantity'))`.
3. Wire into `MyEarningsView` + render: expand to 5 cards (Lifetime = `total_earnings`, Paid = `payments_received` — both already computed, unrendered), add Adda-count strip + pieces, stage-wise panel.
4. Reuse the two fns on `worker_detail.html`.

## 5. Admin Dashboard Plan

1. Tier the home dashboard on the already-computed `is_admin_view` (currently drives nothing): management gets a factory KPI band (open Addas, pieces-in-progress, total pending payable). Reuse existing aggregates. No new model.
2. Complete the payroll table (Role + Pieces, §3.1).

## 6. Super Admin Dashboard Plan (the biggest product gap)

1. **New `ProductionCostingView`** at `/production/costing/`, management-gated. One row/Adda: code, current_stage, status, `total_pieces` (existing property), `total_cost` (`SUM(stage_records__processing_cost)`), worker count, total worker earnings, **margin = revenue − cost**. Annotate the existing `Adda.objects` queryset.
2. **Surface cost in `AddaDetailView`** — add `'cost': sr.processing_cost` to each `stages_overview` row (gate on `is_management`), `ctx['cost_summary'] = adda_cost_summary(adda)`. Answers Q4.
3. **Honest-NULL rule:** any Adda total surfaces "N stages unpriced" — never coerce NULL→0.

## 7. Manufacturing Cost Architecture

- Keep snapshot-as-ledger: `AddaStageRecord` (unique per adda×stage) holding frozen cost **is** the per-stage cost ledger. A separate `CostLedger` table would duplicate + drift. **0 new cost models.**
- Add `cost_service.adda_cost_summary(adda)` → `{stages:[...], total_cost, unpriced_count, priced_zero_count}`.
- Profitability: `Product.manufacturing_cost` exists; costing list shows total_cost vs per-piece vs sale price; reconcile against worker earnings (§3.3).

## 8. Suggested Models (only NEW ones needed)

**Exactly ONE new model justified; everything else is views/queries/fields.**

| Model | Verdict | Why |
|---|---|---|
| **`WorkflowStageRoleRate`** (FK workflow_stage, FK inventory.Role, cost_rate) | **NEW — required for Q7** | No per-role rate exists; rate never consults `worker.role`. Fallback to `ws.cost_rate`; snapshot keeps history frozen. |
| `CostLedger` | NOT needed | `processing_cost` already is it. |
| `ProductionOutput` / `PayrollEntry` | NOT needed | "Output" = `allocated_quantity` + typed records; "PayrollEntry" = `WorkerLedgerEntry`. Document, don't add. |
| Supervisor role + team scope | NEW **only if** supervisor tier required (owner decision) | Today 0% met. Either add `supervisor` role + `supervised_workers` M2M + team-scoped view, OR declare "manager = supervisor". |
| Worker dashboard / costing data | NO new model | All from existing models. |

Optional/deferrable: nullable `adda` FK on `WorkerLedgerEntry` (Q6 convenience).

## 9. Suggested Services

- `payroll_service.worker_production_stats(worker)` — Adda buckets + pieces [Q1/Q2]
- `payroll_service.worker_stage_earnings(worker)` — stage-wise rollup [Q2]
- `cost_service.adda_cost_summary(adda)` — per-stage + total + unpriced counts (honest-NULL) [Q3/Q4/Q8]
- `cost_service.role_rate_for(ws, role)` + edit in `allocate_stage_work` [Q7] *(only service touching the new model)*
- `payroll_service.payroll_overview_rows()` — extract view aggregate + Role + Pieces [Q5]
- (optional) reconciliation read [Q10]

All reads via services (CLAUDE.md rule 4); `ledger_service` stays sole ledger writer.

## 10. UI/UX Recommendations

- Worker: 3→5 cards (Lifetime, Paid), Adda-count strip + pieces, stage-wise panel; keep "estimated — not final pay" copy; reuse `.stat-card`/`.panel` (no new CSS).
- Admin payroll: add Role + Pieces columns with mobile `data-label`; rename headers Earnings/Pending/Paid.
- Super-admin costing: DataTables (search/filter outside `.table-responsive`), Adda/Stage/Status/Pieces/Cost/Earnings/Margin, "N unpriced" warning chip never silent 0.
- Adda detail: per-stage cost column (management-gated) + frosted total footer.
- New entry surfaces follow the form-shell pattern; page-scoped CSS in `extra_head`.

## 11. Future Scalability

- **Reconcile the two money tracks** (`processing_cost` vs `Σ earning_amount_snapshot`) now — add a reconciliation report + invariant test before divergence erodes trust.
- Materialize aggregates only if measured-slow (indexes already exist); don't pre-optimize.
- Generalize allocation beyond cutting as more stages get piece-rate pay (define each stage's grain).
- Role-rate history: keep the snapshot-at-allocation pattern (already immutable).
- Supervisor/team as first-class if the org grows past flat management.
- Wire `Product.manufacturing_cost` + a sale-price source into the costing view so margin is real.

---

## Bottom line for the owner

**Does it satisfy the need? — The brain yes, the face no.** Every calculation, every traceable rupee, every immutable cost snapshot the brief asks for is built and tested. What's missing is what people *see*: the super-admin Adda-costing dashboard (Q4), role-based rates (Q7), a few payroll/worker columns, and the supervisor tier. That's **~1 new model (`WorkflowStageRoleRate`) + a handful of read services + 3-4 dashboard surfaces** — no rework of the engine. Estimated as a focused PR-7 (dashboards + role rates).
