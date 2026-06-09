# Worker Payroll, Ledger & Expense App — Architecture Review

> ⚠️ **SUPERSEDED-FOR-DIRECTION (2026-06-09) by [../ARCHITECTURE_V2.md](../ARCHITECTURE_V2.md) §11
> (🔒LOCKED).** The expense app described here is BUILT, but its **earning-credit timing changes under
> Option B**: today earnings credit at *allocation* (M2.7); V2 books them **only at Adda settlement**
> (production `expected_*` is visibility, not money). `StageWorkAssignment` is **transitional** (candidate
> to become the settlement earning line — not removed). The immutable single-writer ledger + advance-pool
> machinery here is **reused as-is**. Read ARCHITECTURE_V2 §11 + V2_1_REVIEW before touching earnings.

> **Status:** IMPLEMENTED (as of 2026-06-02) — all models, services, views, and tests live
> (expense app migrations 0001–0005, 270+ tests). Original design produced 2026-06-01 by a 7-specialist debate
> (Django Architecture · Manufacturing Workflow · Payroll · Accounting · Security · Mobile UX ·
> DB Scalability). All claims verified against live code at `4fd746d2`.
> The synthesis agent hit a session limit; this doc is the lead-architect synthesis of the 7
> proposals + 7 challenges (which converged strongly).
> **Companion:** `STAGE_COSTING_PLAN.md` (production-side manufacturing cost — the foundation).

---

## Saved-Plan Verdict & Required Revisions

**The saved costing plan is ~70% right — a correct production-cost foundation — but NOT the payroll system.** Two load-bearing errors (exactly the two the owner flagged) must be corrected:

1. **❌ Equal-split earnings (`processing_cost ÷ workers`) — REJECTED.** It is not an imprecise estimate; it is *fabricated data with no source transaction behind it*. Live code proves why it's unsound: `adda_service.create_adda` does `sr.workers.set(skilled_pks)` (the **entire** skilled pool), and `sync_layering_workers_for_skill` retro-adds every new skilled user to every active layering stage. So `|workers|` = "everyone who *could* have worked," not "who *did*." Dividing by it is garbage, and it makes the owner's #1 rule — *every payroll amount traceable Worker → WorkAssignment → Bundle → Stage → Adda* — structurally impossible (no per-worker source row). **Replace with allocation-driven earnings.** Equal-split may survive ONLY as a labelled UI hint when zero allocations exist.

2. **❌ `workers M2M → through=expense.StageWorkAssignment` — DEAD.** A `through` still backs a `ManyToManyField` whose semantics are *set membership* (≤1 join row per (record, worker)). The requirement is **multiple allocations per worker per stage** (User A cuts Bundle A *and* Bundle D). Add uniqueness → lose the 2nd allocation; drop it → `sr.workers.all()` returns dup workers and `.set()`/`.add()` (used in 5 live callsites) corrupt. **Resolution:** keep `AddaStageRecord.workers` a **bare M2M** (roster / visibility); `StageWorkAssignment` is a **standalone FK model** in the `expense` app, no uniqueness on `(stage_record, worker)`. *(Fix the SYSTEM_DESIGN.md doc-drift line claiming the through-conversion.)*

**Kept from the saved plan:** production owns manufacturing cost (`processing_cost` frozen on `AddaStageRecord`); `WorkflowStage.cost_method/cost_rate/cost_billed_at`; freeze in `advance_to_next_stage`; cleared on reopen; grouping self-FK (cost concept only — does NOT affect earnings); extend `AddaHistory` for narrative tracking (never summed for money).

**Net new for payroll: 4 core models in a new `expense` app** (+2 optional). Production gains 0 further models beyond the costing plan.

---

## 1. Production Architecture Review

Unchanged from `STAGE_COSTING_PLAN.md`, with the semantics sharpened:
- `WorkflowStage.cost_method` + `cost_rate` = the **configured manufacturing rate** (production).
- `AddaStageRecord.processing_cost` (frozen) = the **manufacturing cost** of that stage execution. **This is product-costing/profitability data, NOT worker pay.** Manufacturing cost per Adda = `Σ AddaStageRecord.processing_cost`. Profitability = revenue − (`Σ processing_cost` + material cost from `ClothRoll.cost_per_kg`). Pure read aggregate — no new model.
- `cost_billed_at` grouping stays for manufacturing cost roll-up only. **0 new production models.**
- `AddaStageRecord.workers` stays a **bare M2M** = the roster of who is broadly on the stage (drives dashboards, retro-tagging). Earnings come from allocations, not this set.

**Reconciliation note:** `Σ StageWorkAssignment.earning_amount` for a stage *should* reconcile toward that stage's `processing_cost` (same rate, same pieces) but is computed **independently** from per-worker allocations. A reconciliation report flags gaps (unallocated pieces, over-allocation) — it does not auto-balance.

---

## 2. Payroll Architecture Review

Payroll is a **read layer over an immutable ledger** — never a stored balance.

- **Worker sees:** earnings this month, total earnings, pending payable, advance taken (outstanding), last payments, work history. All = scoped aggregations over `WorkerLedgerEntry` + `StageWorkAssignment` for `request.user`.
- **Admin sees:** payroll by worker / stage / Adda / product; outstanding advances; manufacturing cost; profitability. All = aggregations grouped by the relevant FK.
- **Pay periods:** a payroll "run" is a **read** (filter ledger by date range), optionally frozen into an immutable `Payslip`/`PayrollPeriod` snapshot for historical statements. Periods do not own the money; the ledger does.

---

## 3. Expense App Design

New Django app `expense`, **downstream of `production` + `tracking` + `accounts`** (same tier as `tracking`; acyclic boundary). String FKs upstream only (`'production.AddaStageRecord'`, `'production.CuttingBundle'`, `settings.AUTH_USER_MODEL`). **Production never imports `expense`.**

```
accounts (User) ─┐   production (AddaStageRecord, CuttingBundle, ProductSize, Adda) ─┐
                 ▼                                                                    ▼
                          NEW: expense  ── string FKs upstream only ──▶
                 StageWorkAssignment · WorkerLedgerEntry · WorkerAdvance · WorkerPayment
```

**Single-writer discipline (mirrors `history_service`):**
- `expense/services/allocation_service.py` → sole writer of `StageWorkAssignment` (+ its `stage_earning` credit).
- `expense/services/ledger_service.py` → **sole writer of `WorkerLedgerEntry`**.
- `expense/services/advance_service.py` → sole writer of `WorkerAdvance` (+ its `advance` debit).
- `expense/services/payment_service.py` → sole writer of `WorkerPayment` (+ its `payment` debit).
- `expense/services/payroll_service.py` → read-only aggregations (worker payable, reports). No signals.

---

## 4. StageWorkAssignment Design (the keystone)

Standalone FK model (NOT an M2M through). One worker → many rows per stage.

| Field | Type | Notes |
|---|---|---|
| `stage_record` | `FK('production.AddaStageRecord', PROTECT, related_name='work_assignments')` | the executed stage |
| `worker` | `FK(AUTH_USER_MODEL, PROTECT, related_name='work_assignments')` | who did the work |
| `bundle` | `FK('production.CuttingBundle', PROTECT, null, blank)` | bundle-level allocation |
| `size` | `FK('production.ProductSize', PROTECT, null, blank)` | size-level |
| `color` | `FK('raw_materials.ClothColor', PROTECT, null, blank)` | color-level |
| `allocated_quantity` | `DecimalField(12,2)` | pieces/bundles/layers this worker did (the basis) |
| `earning_rate_snapshot` | `DecimalField(10,4)` | rate at allocation time (frozen) |
| `earning_amount_snapshot` | `DecimalField(12,2)` | = quantize(quantity × rate, 2), frozen |
| `notes` | `CharField` | |
| `entered_by` | `FK(AUTH_USER_MODEL, PROTECT, '+')` | audit |
| `created_at` | auto | |

- **Immutable:** never UPDATE; corrections = a reversing assignment + ledger reversal, then a fresh row.
- **No uniqueness on `(stage_record, worker)`** — multiple bundles per worker.
- Supports the example: Cutting → Bundle A Red-S → User A (60 pcs); Bundle C Black-XL → User C (200 pcs) — two rows, two amounts.
- **Future-proof:** `bundle/size/color` nullable so coarser stages (stitching/finishing/checking/packing) allocate at whatever grain they need. Future stages just create assignments against their own `AddaStageRecord` — zero schema change.
- Index: `(worker, -created_at)`, `(stage_record)`.

---

## 5. Worker Ledger Design

`WorkerLedgerEntry` — append-only, immutable, double-entry-style. **The financial source of truth.** (`AddaHistory` is narrative only — never summed for money.)

| Field | Type | Notes |
|---|---|---|
| `worker` | `FK(AUTH_USER_MODEL, PROTECT, related_name='ledger_entries')` | |
| `entry_type` | `CharField` choices | `credit` / `debit` |
| `category` | `CharField` choices | `stage_earning`, `production_earning`, `advance`, `payment`, `deduction`, `adjustment`, `reversal` |
| `amount` | `DecimalField(12,2)` | always positive; direction from `entry_type` |
| `assignment` | `FK(StageWorkAssignment, PROTECT, null, '+')` | source for `stage_earning` |
| `advance` | `FK(WorkerAdvance, PROTECT, null, '+')` | source for `advance` |
| `payment` | `FK(WorkerPayment, PROTECT, null, '+')` | source for `payment` |
| `reverses` | `FK('self', PROTECT, null, '+')` | the entry this reverses |
| `entry_date` | `DateField` | business date (period bucketing) |
| `notes` | `CharField` | |
| `created_by` | `FK(AUTH_USER_MODEL, PROTECT, '+')` | |
| `created_at` | auto | |

**Laws:**
1. **Append-only / immutable** — never UPDATE/DELETE. Mistakes → a `reversal` entry (opposite direction, `reverses` FK) + a fresh correct entry. "You don't erase ink."
2. **Balance NEVER stored.** Worker payable = `SUM(credit) − SUM(debit)`, computed live.
3. **Every credit traces to a source** (PROTECT FK chain): `WorkerLedgerEntry → StageWorkAssignment → CuttingBundle → AddaStageRecord → Adda`. Traceability holds by construction.
4. **Single writer** = `ledger_service`.

Sign convention (payable = what factory owes the worker):

| Kind | type | effect |
|---|---|---|
| `stage_earning` / `production_earning` / `adjustment` (up) | credit | ↑ payable |
| `advance` / `payment` / `deduction` | debit | ↓ payable |
| `reversal` | opposite of reversed | undoes |

**Pending payable = SUM(credits) − SUM(debits).** Outstanding advance = filtered SUM over `category='advance'` net of repayments.

**Optional read-model:** `WorkerBalanceSnapshot` (recomputable cache for dashboard perf) — explicitly rebuildable from entries, never authoritative.

---

## 6. Advance Management Design

`WorkerAdvance` — immutable, full audit.

| Field | Type |
|---|---|
| `worker` | `FK(AUTH_USER_MODEL, PROTECT)` |
| `amount` | `DecimalField(12,2)` |
| `advance_date` | `DateField` |
| `notes` | `TextField` |
| `attachment` | `FileField(upload_to=…, null, blank)` |
| `entered_by` | `FK(AUTH_USER_MODEL, PROTECT, '+')` |
| `created_at` | auto |

- **Immutable, no overwrite.** Reversal = an `adjustment`/`reversal` ledger entry, never an edit.
- Creating an advance writes a `debit` ledger entry (category `advance`) in the same `advance_service` transaction → it nets against the worker's payable automatically.

---

## 7. Security Design

Worker payroll is sensitive. **All access through `permission_service` + queryset scoping** (production has no per-row worker scope today — this is net-new).

- **Worker** → sees ONLY own rows: every `expense` queryset filtered `worker=request.user`. Never another worker's data exposed in any view, API, or template.
- **Manager** → assigned-team scope (team membership model TBD — Open Question).
- **Admin / accountant** → all.
- New gates: `expense.view_own_payroll`, `expense.view_all_payroll`, `expense.manage_advances`, `expense.manage_payments`. ROLE_SUPER_ADMIN bypass as usual.
- Advance attachments served through a permission-checked view, not raw `MEDIA_URL`.
- All money-writers audit `entered_by` / `created_by`.

---

## 8. Mobile UX Design

**Worker screen (factory floor — 5 cards only, no tables):**
1. Earnings this month (Σ credits, current period)
2. Advance taken (outstanding)
3. Pending payroll (live payable balance)
4. Today's work (today's `StageWorkAssignment` rows)
5. Recent Addas (worked on)

All scoped to `request.user`; read from `payroll_service` aggregates. No cross-worker data, no large reports.

**Admin screen:** detailed tables — payroll by worker/stage/Adda/product, outstanding advances, manufacturing cost, profitability, reconciliation gaps.

---

## 9. Data Integrity Review (highest priority)

- **No stored balances** — payable always recomputed → can't drift.
- **Append-only immutable** ledger + assignments + advances + payments → no data loss, no overwrite.
- **PROTECT** on every source FK → can't orphan a payroll amount; full chain `Worker → StageWorkAssignment → Bundle → Stage → Adda` enforced.
- **Single-writer services**, no signals → one code path per table.
- **Reversal-by-entry** correction discipline → audit trail of every change.
- **Snapshotted rates** on assignments → a rate-card edit never alters historical pay.
- Reconciliation report: `Σ assignment.earning_amount` vs stage `processing_cost` (flags unallocated/over-allocated pieces).

---

## 10. Migration Plan

1. (Costing plan migrations first — `STAGE_COSTING_PLAN.md` §5.)
2. `startapp expense`; add to `INSTALLED_APPS`. Additive — new tables only.
3. Migration: `StageWorkAssignment`, `WorkerLedgerEntry`, `WorkerAdvance`, `WorkerPayment` (+ optional `WorkerBalanceSnapshot`). All new tables, zero touch to existing schema.
4. Services + RBAC gates + worker/admin dashboards built incrementally; each PR additive.
5. **No backfill** — historical Addas have no allocations (honest "not allocated"). Allocation begins from go-live.
6. Tests: ledger reconstructability (balance == Σ credits − Σ debits), traceability chain, immutability (no UPDATE path), reversal correctness, per-worker scoping (worker can't read another's rows).

## 11. Rollback Plan

`expense` is a leaf app — drop the migrations / uninstall the app; production + tracking untouched (they never import `expense`). Code-only rollback leaves new tables inert. No production data depends on `expense`, so removal cannot corrupt the manufacturing chain.

## 12. Scalability & Multi-Factory Review

- **5+ years:** at ~50 Addas/mo × a handful of allocations each, `StageWorkAssignment` + `WorkerLedgerEntry` are low-volume (tens of thousands of rows over 5y). Indexes `(worker, -created_at)`, `(worker, entry_type)`, `(stage_record)` keep dashboards fast. Optional `WorkerBalanceSnapshot` if live SUM ever gets hot.
- **Multi-factory seam:** add a `Factory` model later; `Adda` (and optionally `User`) gain a nullable `factory` FK; `expense` aggregations gain a `factory` filter. All **additive** — nothing in this design blocks it. Do NOT build now; just leave the seam (don't hardcode single-factory assumptions in services).
- Period close (`Payslip`) can archive/roll up old ledger ranges if volume ever grows.

---

## New Model Count

| App | New models | Justification |
|---|---|---|
| `production` | **0** (beyond the costing plan's field additions) | manufacturing cost rides on `AddaStageRecord` |
| `expense` | **4 core** + 2 optional | `StageWorkAssignment`, `WorkerLedgerEntry`, `WorkerAdvance`, `WorkerPayment` (+ optional `WorkerBalanceSnapshot`, `Payslip`/`PayrollPeriod`) |

Each earns its place: allocation (the per-worker source), ledger (the immutable money truth), advances + payments (the two debit sources). None is collapsible without losing traceability or immutability.

---

## Open Questions for the Owner

1. **Manager "assigned team":** how is a manager's team defined (explicit membership model, or a `manager` FK on `User`, or factory/role scope)? Drives the manager-scope security filter.
2. **Advance ↔ earnings netting:** advances net directly against the running payable (simplest), or tracked as separate repayable balances with explicit repayment entries?
3. **Production earnings (whole-Adda bonus):** is there pay beyond per-stage allocation (e.g. a finishing bonus on completed Addas)? If yes, it's another `StageWorkAssignment`/credit source.
4. **Allocation timing:** who allocates and when — manager assigns bundles up front, or the worker self-claims at stage start, or recorded at stage completion?
5. **Unallocated pieces:** if not every piece in a stage is allocated to a worker, is that allowed (gap flagged) or must allocation sum to the stage total before completion?
6. **`Payslip`/period close:** needed now (immutable monthly statements) or defer (live ledger reads suffice)?
7. **Multi-factory:** confirm it stays a *future* seam (not built now).

---

## Debate Resolution (consensus across the 7 lenses)

| Contested point | Resolution |
|---|---|
| Equal-split earnings | **REJECTED** (all lenses) — fabricated, untraceable. Allocation-driven only. |
| `StageWorkAssignment`: through vs standalone | **Standalone FK model** (all lenses) — through can't hold multiple allocations/worker; would corrupt 5 live `.set()`/`.add()` callers. |
| Ledger: stored vs derived | **Append-only immutable rows + balance never stored** (Accounting lens) — reconstructable, auditable. |
| Production/payroll boundary | **Hard split** — production = manufacturing cost; `expense` = worker money. Production never imports `expense`. |
| Where earnings DISPLAY lives | **`expense` app**, scoped to the worker; production shows manufacturing cost only. |
| Multi-factory | **Future additive seam**, not built now. |
| Model count | **0 new production / 4 core expense** — the floor for traceable, immutable payroll. |

*Proposals + challenges retained in workflow run `wf_19fc340a-de8` (synthesis step failed on a session limit; this doc is the manual lead-architect synthesis).*
