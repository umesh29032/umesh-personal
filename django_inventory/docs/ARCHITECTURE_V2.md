# Architecture V2 — Adda Production Tracking & Settlement

> Status (updated 2026-06-14): **V2-1a→1d + V2-2 + V2-3 BUILT & COMMITTED**, AND the
> **PRODUCTION-TRUTH FOUNDATION (S1, S1.1, S3, S4, F1-F4, S5) is COMPLETE & COMMITTED** (prod
> migrations 0037→0042, expense 0010/0011; 641 tests green). V2-1a→1d (worker truth; legacy
> M2M dropped, migration 0035) · V2-2 (§11 AddaSettlement — finalize/reverse/supersede +
> management UI; the AddaSettlement/AddaSettlementItem tables ARE built — the "design only"
> note inside §11 is historical) · V2-3 (settlement-FIRST cutover: `LEDGER_CREDIT_AT_ALLOCATION`
> default False, env True = rollback lever) · C-1 money-truth hardening (ADR-0009/0010).
> **The foundation layer this doc predates — AddaStageRoleRate (S1), good/alter/missing (S3),
> allocation_dimensions + StagePoolSnapshot + WorkerStageAllocation (S4), M-6 finalize BLOCK
> (S5) — is summarized in §2.1 below; full current-state in
> [FOUNDATION_STATUS_SUMMARY_2026_06_14.md](FOUNDATION_STATUS_SUMMARY_2026_06_14.md) and the
> governing design [PRE_S1_DESIGN_ADDENDUM.md](PRE_S1_DESIGN_ADDENDUM.md).**
> Remaining: **S6** (reported_quantity drop, irreversible, post-deploy soak-gated), then the
> soak-gated era-A deletion PR + Missing/Alter modules.
> First-read for new developers: [docs/PROJECT_KNOWLEDGE_MAP.md](PROJECT_KNOWLEDGE_MAP.md).
> Ledger cutover for V2-2 is decided: **ADR 0007 (Option A — coexist; cross-era double-credit guard;
> `LEDGER_CREDIT_AT_ALLOCATION` rollback flag).** This is a production-execution
> + Adda-centric settlement system with worker isolation — **NOT a traditional payroll app.**
> Supersedes the M2.7 *crediting trigger* (see "M2.7 delta"); reuses its ledger/advance machinery.
> **Option B:** Production Truth ≠ Financial Truth — money touches the ledger only at settlement.

## Founding principle
Two layers, one immutable ledger as the single financial truth:
```
PRODUCTION TRUTH (operational)              |  FINANCIAL TRUTH (money)
WorkerStageTask → WorkerStageContribution   |  AddaSettlement → WorkerLedgerEntry (the ONE source)
(lifecycle)       (qty + frozen expected_*) |  WorkerAdvance (early pay, separate loan pool)
```
Production records *what happened* and *what's expected* (visibility, not money); settlement is the
**only** place money is booked to the ledger, at the Adda end. Never merged. `StageWorkAssignment`
(the M2.7 allocate-time earning) is **transitional** — its allocate-time crediting role ends, but
the model is retained (likely repurposed as the *settlement* earning line) until the financial
design is locked; see §10.

---

## 1. Access model (5 concepts)
| Concept | Means | Enforced |
|---|---|---|
| UserType | identity/classification (Worker/Employee/Supplier/Manager/SuperAdmin) | **display only — never gates** |
| Role | actions / management / module access | `user_has_role`, perms |
| Skill | manufacturing capability (can do stage type) | `Stage.access_by_skill` |
| **Assignment** | object-level access to a **specific Adda/stage** | **`WorkerStageTask` membership** (NEW enforced layer) |
| Ownership | self-scope of own earnings/advances/ledger | `can_view_worker` (exists) |

**Worker access to an Adda's stage = Skill ∧ Assignment.** Manager/SuperAdmin bypass Assignment per role. Supplier = no production access.

---

## 2. Data model (the locked foundation)

### Production layer (NEW)
**`WorkerStageTask`** — per-worker assignment + lifecycle (owns *lifecycle*, not quantity):
```
stage_record (FK → AddaStageRecord → Adda + Stage)
worker (FK)
status: assigned → in_progress → completed → [verified]   + cancelled (terminal)
started_at · completed_at · verified_at · verified_by      (verification OPTIONAL, non-blocking)
notes ; created/updated (audit)
```
**`WorkerStageContribution`** — dimensional lines under a task (owns *quantity* + the *expected-earning snapshot*; ≥1 per task):
```
task (FK)
color (FK, nullable)   size (FK, nullable)       ← capture from day one (un-backfillable)
reported_quantity      (worker-entered; locked after submit; S3: dual-written = good, renamed-not-dropped @S6)
good_quantity          (S3, NOT NULL = the PAYABLE good; what settlement pays via the resolver)
alter_quantity         (S3, default 0; immutable count observation, future Alter module)
missing_quantity       (S3, default 0; immutable count observation, future Missing module)
verified_quantity      (nullable; only manager/supervisor/super_admin may set/correct)
role_snapshot (FK Role, nullable)  ← S1: the worker's role FROZEN at complete (the rate is resolved against THIS)
expected_rate          (FROZEN at complete = AddaStageRoleRate frozen rate for (stage_record, role_snapshot); S1)
expected_earning       (FROZEN at complete = good_quantity × expected_rate)   ← S3 reads good, not reported
settlement_line (FK expense.StageWorkAssignment, nullable)  ← stamped at finalize; per-row era-B provenance
bundle_item (FK, nullable)   ← optional piece-precision (cutting today; any stage later)
created/updated (audit)
```
> **S3 (migration 0039) split the payable grain:** `good_quantity` (NOT NULL) is the payable
> truth; `alter`/`missing` are immutable observations; `reported_quantity` is dual-written = good
> (kept for legacy reads, renamed at S6). The settlement resolver + `expected_earning` + payroll +
> worker display all read **good**, never reported. **S1 (migration 0037)** made `expected_rate`
> resolve from `AddaStageRoleRate` (frozen per (stage_record, role) at first completion), not a
> raw WorkflowStage.cost_rate copy. See §2.1.
- Worker reports N lines (Red-M:120, Blue-L:80). Multi-color/size per worker per stage = native.
- Simple stage = one line (`color/size = null`). Task total = `Σ lines` (derived, never stored).
- Worker **cannot edit after submit**; corrections set `verified_quantity` (manager only).
- **`expected_*` are operational visibility ONLY** — frozen at complete, NEVER mutated by later
  rate changes, and **NOT money**: no ledger entry, not a payable. They answer "what this worker
  is on track to earn" during production. Real money is decided at settlement (§5–§6).

### 2.1 Production-truth foundation layer (S1–S5, COMMITTED 2026-06-14 — post-dates this doc's original §2)
The foundation that this V2 doc predates. Governing design: [PRE_S1_DESIGN_ADDENDUM.md](PRE_S1_DESIGN_ADDENDUM.md)
+ [S4_DESIGN_CORRECTION_ADDENDUM_2026_06_14.md](S4_DESIGN_CORRECTION_ADDENDUM_2026_06_14.md);
current-state narrative: [FOUNDATION_STATUS_SUMMARY_2026_06_14.md](FOUNDATION_STATUS_SUMMARY_2026_06_14.md).

- **`AddaStageRoleRate`** (S1, prod 0037) — frozen RESOLVED payable rate per `(stage_record, role)`,
  snapshotted at stage-start, locked at first completion (M1 = per (stage,role)), `edit_until_lock`
  before lock. `complete`/settlement read THIS (not the live workflow). `RateCorrectionAudit` (S1.1,
  prod 0038) + super-admin `rerate_stage_role` correct it until settlement (F1: serialized with
  finalize on advisory lock 5374; F2: grouped→0 structural; F4: re-floated on reopen).
- **good/alter/missing** (S3, prod 0039) — see §2 schema above. The payable-grain split; RC-3
  constraint swap; resolver reads good.
- **`WorkflowStage.allocation_dimensions`** {NONE, QUANTITY, COLOR_SIZE} (S4, prod 0040) — PIECE-POOL
  grain ONLY, **orthogonal** to `credits_workers` (settlement) and `cost_method` (costing); the
  piece-pool starts at CUTTING (pre-piece stages = NONE).
- **`StagePoolSnapshot`** (S4, prod 0041, downstream-only) + **`WorkerStageAllocation`** (S4, prod
  0042, **production-truth, NO money**, append-only) — the pool + draw-down in `pool_service`
  (advisory lock classid 5375, disjoint from settlement's bigint 5374; never locks AddaStageRecord).
  Cutting's pool good = `AddaProductSizeColorPieceBreakdown` (single source, NOT duplicated), via
  handler-dispatched `pool_good`. **All S4 is service+tests-only and INERT in the current 4-stage
  flow** (no piece-consumer downstream of cutting yet).
- **Enforcement (both default OFF, soak-gated — ENFORCEMENT_ROLLOUT_RUNBOOK):**
  `ENFORCE_ALLOCATION_BOUND` (S4 P4: complete-time `Σ(good+alter+missing) ≤ Σ allocated`) +
  `ENFORCE_SETTLEMENT_RECONCILIATION` (S5 M-6: finalize refuses settled-more-than-produced beyond
  tolerance, super-admin audited override → `SettlementReconciliationEvidence`, expense 0010/0011).
- **Reopen** (S4 P5) — `_downstream_consumer_guard` refuses upstream reopen while a downstream
  non-voided allocation or completed contribution exists (transitive; reverse-first; actionable).
- 🔒 **Four independent concerns** (allocation / cost_method / earning / settlement) hold throughout;
  `WorkerStageAllocation` is never money; **settlement is the only money boundary**; golden ₹225
  byte-identical across every phase.

### Financial layer (REUSE + extend) — ONE source of truth: the ledger
> **The single financial source of truth is `WorkerLedgerEntry`. It is written ONLY at Adda
> settlement.** Nothing before settlement is money: contribution `expected_*` is visibility,
> advances are a separate loan pool. Everything financial reconciles back to the ledger.

- **`StageWorkAssignment`** (existing) — **TRANSITIONAL under Option B (NOT removed).** It was the
  M2.7 *allocate-time immutable earning line* (credit-at-allocation). Option B no longer credits at
  allocation, but SWA is still woven into live readers (worker dashboard, PAY-4 reconciliation,
  costing column, reopen-reversal, the PAY-2 guard) and is the **source FK every `stage_earning`
  ledger credit points to** (`WorkerLedgerEntry.assignment`, PROTECT). Disposition (remove /
  **repurpose as the settlement earning line** / deprecate-retain) is **deferred** until the V2
  financial architecture is finalized and every reader is repointed. Leading candidate: **repurpose**
  — write it *at settlement* (one row per settled worker-stage line) so the ledger's source FK stays
  intact. No removal migration in this wave. (See the dependency review in the chat for the full map.)
- **`WorkerLedgerEntry`** (existing, immutable, single-writer) — **the one financial truth.**
  Earnings CREDITs are created **only at settlement** (not at complete). Plus debits
  (advance recovery / payment / adjustment). Earning credits link to the settlement
  (`settlement` FK) and trace back to the contribution(s) they settle — **not** to a
  `StageWorkAssignment`.
- **`WorkerAdvance`** (existing) — early payment; **separate from earnings**; recovered (configurably) at settlement. ~~+ add `adda` FK~~ **REJECTED by locked §11.3 ("Do not add it") — §11 wins; this line reconciled in R0.**
- **`AddaSettlement`** (NEW) — adda · status · expected/packed/missing/rejected/variance (per color/size) · totals · created_by · settled_at. The reconciliation EVENT that *produces* ledger entries.
- **`AddaSettlementItem`** (NEW) — per worker: expected_earned · final_payable · advance_deducted (manager-chosen) · amount_paid · remaining. The human-readable settlement breakdown beside each ledger credit it generates.

---

## 3. Derived Stage Progress (service, NOT a table)
A service function over **active** (non-cancelled) `WorkerStageTask` for a stage_record:
```
assigned_count · pending · in_progress · completed · verified
readiness_percentage = (completed + verified) / assigned · 100
ready_for_review   = assigned>0 AND pending==0 AND in_progress==0     (all workers done)
ready_for_advance  = assigned>0 AND (completed + verified)==assigned   (← gate; verification NOT required)
```
Always correct under changing assignments (derived). `cancelled` prevents readiness deadlock. Used by **both** the manager dashboard and the advance gate (single source).

---

## 4. Stage completion / advancement (verification non-blocking — per requirement #5)
Three SEPARATE concepts:
- **Worker completion** — worker submits → task `completed` → **expected-earning snapshot frozen** on the contribution lines (`expected_rate`/`expected_earning`). **No ledger entry, no money** (see §5).
- **Manager review/verification** — OPTIONAL today; sets `verified` + may correct `verified_quantity`. Does **NOT** gate advancement.
- **Stage advancement** — management action; gated on **all active tasks `completed`** (NOT verified). `advance_to_next_stage` enforces this for worker-staffed stages.

Future: verification *may* become a gate — additive policy, no model change.

---

## 5. Earning model — **Option B: Production Truth ≠ Financial Truth** (the locked decision)
Two distinct layers, never conflated:

| | **Production Truth** | **Financial Truth** |
|---|---|---|
| Lives in | `WorkerStageContribution` (+ `WorkerStageTask`) | `WorkerLedgerEntry` (the ONE source) |
| Created when | worker **completes** | Adda **settlement** |
| Holds | reported_quantity, frozen `expected_rate`/`expected_earning` | settled CREDITs/DEBITs (real money) |
| Mutable? | reported locked at submit; expected frozen forever | immutable, append-only |
| Is it money? | **No** — operational visibility only | **Yes** — payable |

**At worker completion** (`reported_quantity × rate` computed once):
- Freeze `expected_rate` + `expected_earning` onto each contribution line. **That's it — no ledger entry.**
- These are a *snapshot for visibility*: worker sees "on track to earn X", manager sees per-worker/per-Adda expected totals, all *during* production — satisfying the early-visibility requirement **without** booking money.
- Frozen means frozen: editing `WorkflowStage.cost_rate` afterward does **not** touch already-captured snapshots (same posture as `cost_rate_snapshot`).

**Why no ledger at complete (vs the old M2.7 accrue-at-allocate model):**
- Reported quantity is *operational data*, not a payable. The payable is determined only after the Adda finishes — once packed/missing/rejected/variance and advance recovery are known.
- Booking a credit at complete would make the ledger provisional (credit → correction-adjustment → variance-adjustment → reversal…), i.e. a second moving "earning" surface racing the contribution snapshot. Two sources of earning truth = the exact bug single-writer discipline exists to prevent.
- Deferring the *only* money-write to settlement keeps the ledger immutable-and-final: every entry in it is real, settled money.

**At settlement** (§6) — the single financial write:
- Compute final payable per worker from expected vs packed/missing/rejected (variance policy) minus advance recovery (manager-chosen).
- Write the earning CREDIT(s) + advance-recovery DEBIT(s) to `WorkerLedgerEntry`, linked to the `AddaSettlement`. `AddaSettlementItem` records the human-readable breakdown beside them.
- This is the *first and only* time money touches the ledger for the Adda's stage work.

So: **the contribution answers "expected so far"; the ledger answers "owed/paid" — and only the ledger is money.**

---

## 6. Adda settlement (Adda-centric reconciliation)
At Adda end (post-packing), `AddaSettlement` shows the drill-down — comparing **expected
(production truth)** against **actual (settlement reality)** to derive the payable:
```
Adda → Stage → Worker → Color → Size → reported_qty / verified_qty → EXPECTED earning (snapshot)
     → packed / missing / rejected / variance (per color/size)
     → advances paid → advance deducted now (manager-chosen) → remaining advance
     → FINAL PAYABLE → final paid
                          └──▶ writes WorkerLedgerEntry CREDIT/DEBIT  (the one money-write)
```
Advance deduction is **configurable** (e.g., advance 50, expected 100, final payable 90, deduct 30 now → remaining advance 20, paid 60). Preserves advance taken / balance / deduction / remaining. The expected column is the frozen contribution snapshot; the final payable is what actually books to the ledger.

---

## 7. Isolation (hard requirement)
Worker sees ONLY: own tasks, own contributions, own earnings/advances, own settlement breakdown. Never: others' contributions/earnings, unassigned Addas, factory totals, management-only breakdowns. Manager/SuperAdmin: broader per role. Enforced via Assignment (`WorkerStageTask` membership) + Ownership (`can_view_worker`) at every view/query/service.

---

## 8. Build now · Defer · Lock-now · Policy · Refactor-risks

### LOCK NOW (foundational, cannot be reconstructed later)
- `WorkerStageTask` + `WorkerStageContribution` **lines** (multi color/size per worker).
- **Capture color/size on contribution lines from day one** (un-backfillable).
- **`reported_quantity` vs `verified_quantity` as separate fields.**
- **`expected_rate` + `expected_earning` frozen on the contribution at complete** (visibility snapshot, never money, never re-derived).
- **`cancelled` terminal task status.**
- **Ledger is the single financial source of truth, written only at settlement** (Production Truth ≠ Financial Truth — §5).
- Assignment as the object-level access layer; advance separate from earnings; ledger immutable.

### BUILD NOW (foundation + the live security fix)
1. `WorkerStageTask` + `WorkerStageContribution` (migrate the `workers` M2M — P0.5).
2. **Assignment isolation** on `WorkerStageTask` (the HIGH security leak from the prior review).
3. Worker self-report UI (no totals); worker-can't-edit-after-submit.
4. **Freeze `expected_rate`/`expected_earning` on the contribution at complete** (visibility snapshot — NO ledger write).
5. Derived stage-progress service + dashboard (shows expected totals).
6. Advance gate = all active tasks `completed`.
7. **Keep `StageWorkAssignment` as transitional** — no removal migration; disposition decided after the dependency review + settlement design lock (§10).

### DEFER (build after tracking works; additive, no redesign)
- `AddaSettlement` + variance/missing/rejected + `WorkerAdvance.adda` reconciliation **+ the settlement ledger write** (the one money-write).
- Manager verification workflow (optional; correction sets `verified_quantity`, feeds settlement).
- Piece-level (`bundle_item`) for non-cutting stages; machine sub-stages.
- Factory scoping (multi-site).

### POLICY (changeable later, NO schema impact)
- Whether verification becomes blocking.
- Variance attribution (factory-absorbs / proportional / stage / worker / color) — applied **at settlement**, so changeable without touching frozen snapshots.
- Advance deduction amount per settlement.
- Whether the settlement payable equals expected, or is adjusted — settlement-time policy, never a model change.

### REFACTOR RISKS if modeled wrong today (all avoided by the locks above)
- Single color/size FK → no color-wise settlement/variance later (un-backfillable). → **lines.**
- Not capturing color/size at production → unreconstructable. → **capture now.**
- Merging advance into earnings → can't separate. → **keep separate.**
- No expected-earning field on the contribution → no production-time visibility, and back-deriving it after a rate change is impossible. → **freeze `expected_*` at complete.**
- Booking money at complete → ledger becomes provisional + a second earning surface races the snapshot. → **money only at settlement; ledger stays final.** `StageWorkAssignment` kept transitional (no churn).
- Stored progress summary → staleness. → **derived.**
- No `cancelled` status → readiness deadlock. → **add it.**

---

## 9. Answers to the 12 questions
1. Dedicated `WorkerStageTask`? **Yes.**
2. `WorkerStageContribution` lines under it? **Yes.**
3. Stage progress derived (not stored)? **Yes.**
4. `cancelled`/`removed` terminal status? **Yes.**
5. Verification optional + non-blocking today? **Yes** — advance gates on `completed`, not `verified`.
6. `reported_quantity` vs `verified_quantity` separate? **Yes.**
7. `WorkerAdvance` separate from earnings? **Yes** (configurable deduction at settlement).
8. `AddaSettlement` the final Adda-centric reconciliation? **Yes.**
9. Ledger accrue before/at settlement? **Ledger writes ONLY at settlement (Option B).** At complete, freeze an `expected_*` snapshot on the contribution for visibility — that is not money. The ledger is the single financial source of truth and stays final, not provisional.
10. Simplest architecture? The 3-model production foundation (`WorkerStageTask` + `WorkerStageContribution` with `expected_*`) + reused expense (advance/**ledger**) + `AddaSettlement`/`Item` + derived progress. **`StageWorkAssignment` kept transitional (disposition deferred); no new app, no workflow engine.**

---

## 10. M2.7 delta (what changes vs what's kept)
- **Kept:** immutable `WorkerLedgerEntry` (now the *single* financial source of truth), advance pool, data-driven payability (`credits_workers`), the stage registry/handlers.
- **Transitional (NOT removed):** `StageWorkAssignment`. M2.7 modelled it as the *allocate-time immutable earning* (credit booked when management allocated). Option B no longer credits at allocation, so its M2.7 *role* ends — but it still backs live readers and is the source FK for every `stage_earning` ledger credit. Decision: **deprecate-retain now; likely repurpose as the settlement earning line** (write at settlement so `WorkerLedgerEntry.assignment` stays intact). No removal migration until the financial design is locked and readers are repointed.
- **Changed:** the money-write moves from *allocate-time credit* (M2.7) → *settlement-time credit* (Option B). Worker completion now freezes a visibility snapshot, books nothing. The PAY-2 guard reframes from "≥1 allocation" → "all active tasks completed" before advance.
- **Added:** `WorkerStageTask`, `WorkerStageContribution` (with `expected_rate`/`expected_earning`), derived progress, `AddaSettlement`/`Item`. (~~`WorkerAdvance.adda`~~ rejected by §11.3 — R0 reconciliation.)

### Responsibility map (the question you asked — where each job lives under Option B)
| Responsibility | Owner | Money? |
|---|---|---|
| Production contribution (who did what, qty, color/size) | `WorkerStageContribution` (+ `WorkerStageTask` lifecycle) | No |
| Expected-earning snapshot (frozen at complete) | `WorkerStageContribution.expected_rate` / `.expected_earning` | No (visibility) |
| Settlement calculation (expected vs packed/missing/rejected − advance) | `AddaSettlement` / `AddaSettlementItem` | breakdown |
| **Final ledger booking** | **`WorkerLedgerEntry` (only at settlement)** | **Yes — the one truth** |
| Allocate-time earning line (M2.7) | `StageWorkAssignment` — **transitional**; candidate to repurpose as the *settlement* earning line | role ends, model retained |

**One financial source of truth, confirmed:** only `WorkerLedgerEntry` carries money, and it is
written only by the settlement service. Expected snapshots and settlement items are reporting
artifacts that reconcile to it; they never compete with it.

This is the locked V2 foundation: production tracking, assignment isolation, stage progress,
expected-earning visibility, Adda settlement (the single money-write), advances, variance, and
future color/size/piece traceability all rest on it with no foreseeable schema redesign.

---

## 11. AddaSettlement architecture — 🔒 LOCKED 2026-06-09

> **LOCKED.** Synthesized from two independent designs (immutability-first + minimal-schema) +
> adversarial pass, finalized against owner decisions. Design only — no code yet; deferred bucket;
> SWA not removed. **Locked terms:**
> 1. **Settlement-time advance recovery** — recovery posts at settlement (earning credit − advance
>    recovery debit = final payable); payment never re-runs recovery logic.
> 2. **Settlement separate from payment** — settlement = financial truth (no cash); payment = separate
>    cash event(s), partial/multiple/later.
> 3. **Missing Pieces & Alter/Rework = future first-class domain modules** — own lifecycles/audit/
>    reporting, built later; settlement consumes summarized outcomes only.
> 4. **Frozen `AddaSettlementItem`** — append-only per-worker business snapshot; ledger stays the
>    single live money truth.

### 11.0 Owner decisions (locked 2026-06-09) — drive everything below
1. **Settlement ≠ Payment (Model A).** `AddaSettlement` finalizes *financial truth* (earnings,
   variance/missing/rejected/alter adjustments, advance-recovery decision, final payable). It does
   **NOT** move cash. Cash payout is a **separate event**, allowed immediately / partially / later /
   across many payments. → §11.2, §11.5b lifecycle.
2. **`factory_absorbs` at launch** — variance is *tracked & reported*, never auto-reduces payable now;
   future deduction policies must stay possible with no schema redesign. → §11.7, §11.10.
3. **Frozen `AddaSettlementItem`** (owner override of the minimal "derive it" rec) — settlement freezes
   an immutable per-worker business snapshot, append-only, never recomputed after finalize. → §11.3.
4. **Manual variance entry now, source-agnostic** — packed/missing/rejected/alter are manually entered
   into the frozen snapshot for V2; future Packing/QC/Missing/Alter modules become the authoritative
   source with **no settlement schema change**. → §11.10.
5. **Missing Pieces & Alter/Rework are first-class domain concepts** — modeled as their own
   modules/lifecycles later; settlement **consumes their summaries**, never owns their workflow. → §11.11.

### 11.1 The core finding — two ORTHOGONAL settlement axes already exist
The existing `PayrollSettlement` is **worker-centric** (1 worker : 1 payout, settles that worker's
whole cross-Adda payable, debits only — the owner's D1–D4 "settle anytime / partial" flow). The
proposed `AddaSettlement` is **Adda-centric** (1 Adda : N workers, reconciles expected vs
packed/missing/rejected, and is the event that *creates* the earning credits under Option B).
Different keys, different fan-out. `PayrollSettlementItem` today = **advance-recovery lines**, NOT
a per-worker payable breakdown. So "AddaSettlement" is **not a rename** of anything.

### 11.2 Resolution: TWO events, ONE ledger (Model A) — `AddaSettlement` ≠ `PayrollSettlement`
The orthogonal axes (§11.1) map onto **two distinct events**, each writing a *different, non-overlapping*
slice of the one ledger:

- **`AddaSettlement` (NEW) = the EARNING + RECOVERY-DECISION event.** At finalize it posts, per worker:
  the `STAGE_EARNING` **credit** (Option-B money-creation) **and** the agreed `ADVANCE_RECOVERY`
  **debit**. After finalize, the worker's live balance = **final payable owed in cash** (earnings −
  recovered advances). It moves **no cash**.
- **`PayrollSettlement` (EXISTING) = the PAYMENT event.** Repurposed to **cash payout only** — posts the
  `SETTLEMENT_PAYMENT` **debit**. Stays worker-centric, settle-anytime, partial, multi-payment (D1–D4
  preserved). It no longer needs to bundle earnings or recovery.
- **`ledger_service` remains the sole ledger writer.** No double-writer: AddaSettlement owns credits +
  recovery debits; PayrollSettlement owns payment debits. Disjoint categories, no overlap.

**Architectural consequence (honest — this is NOT zero-churn on the built flow):** advance recovery
**re-homes** from the payment event to the settlement event. Concretely:
- `PayrollSettlementItem` (the per-advance recovery line) gains a **nullable `adda_settlement` FK**; new
  recovery lines parent to the `AddaSettlement`, legacy lines keep their `settlement` FK. The
  `advance_remaining`/`advance_outstanding` math is unchanged — it sums `amount_recovered` regardless of
  parent. (One nullable FK; existing rows stay valid.)
- `settlement_service.create_settlement` splits in two service paths sharing the locks: `finalize_adda_settlement`
  (earning credit + recovery debit, over-recovery guard) and the existing `create_settlement` reduced to
  **payment-only** (cash debit, guard: `amount_paid ≤ worker_balance`). Both still go through `ledger_service`.
- Rejected: RENAME (orphans worker-centric payout), REUSE-with-adda-FK (two modes one table),
  bare COEXIST (two ledger writers), and **bundling pay into settlement** (the owner's Model-A separation).

### 11.3 Schema: `AddaSettlement` (event) + frozen `AddaSettlementItem` (per-worker snapshot)
Two new financial tables (owner chose the frozen snapshot over deriving it — auditability):
- **`AddaSettlement`** (the event header): `reference` (ADST-####), `adda` (FK PROTECT), `status`
  (draft/finalized/reversed/superseded), `variance_policy` (frozen), `expected_total / packed_total /
  missing_total / rejected_total / alter_total / variance_total` (frozen audit snapshots), `settled_at`,
  `created_by`, plus `supersedes` (self FK null) + `reversed_at`/`reversed_by` (correction chain).
- **`AddaSettlementItem`** (the frozen per-worker business record — **append-only, never recomputed
  after finalize**): `adda_settlement` (FK), `worker` (FK), optional `stage_record` (drill-down grain),
  and the frozen snapshot the owner specified — `expected_earning`, `advance_outstanding_before`,
  `advance_recovered`, `final_payable`, `variance_amount`, `packed_quantity`, `missing_quantity`,
  `rejected_quantity`, `alter_quantity`, `settled_at`, `settled_by`, plus `earning_assignment` (FK →
  the settlement-written SWA, closing the audit loop item ↔ SWA ↔ ledger credit). Six months on, this
  row shows exactly what was reviewed and approved — independent of later rate/advance/policy changes.
- **Two truths, no conflict:** `WorkerLedgerEntry` is the *live money* truth (balance recomputes
  forever); `AddaSettlementItem` is the *frozen business record* of the settlement moment. They tie out
  at finalize (`final_payable` == that worker's net booked credit−recovery for the Adda) and then the
  snapshot **never recomputes** — divergence later (after a supersede) is intended and itself auditable.
- **Grafts kept:** `supersedes` chain + `reversed_at/by` (un-retrofittable; add now).
- **Rejected:** `WorkerAdvance.adda` FK — per-Adda advance scoping conflicts with the worker-level
  loan-pool math (`advance_remaining` sums across ALL settlements), is reconstructable via
  `PayrollSettlementItem → adda_settlement → adda`, and is a *feature* not a seam. **Do not add it.**

### 11.4 SWA's exact role (keeps the ledger FK invariant intact)

> **STATUS (V2-3, 2026-06-11): repurpose COMPLETE + cutover EXECUTED.** SWA is
> the settlement earning line (written at finalize, `adda_settlement` FK =
> structural era marker). Allocation-time crediting is rollback-only behind
> `LEDGER_CREDIT_AT_ALLOCATION` (default False). Settlement money mutates ONLY
> via adda_settlement_service (reopen/void guards + gate 4c). Worker visibility:
> `unsettled_expected` (frozen WSC) → Earned (ledger) → Paid (cash) — three
> non-overlapping views. Legacy-path deletion soak-gated. See
> docs/archive/reviews/V2_3_EXECUTION_REVIEW.md.
At `finalize`, for each settled `(worker, stage_record[, color/size])` line derived from a
`WorkerStageContribution`, write ONE `StageWorkAssignment` row: `allocated_quantity` = policy-adjusted
settled qty, `earning_rate_snapshot` = the contribution's frozen `expected_rate`,
`earning_amount_snapshot` = `final_payable`. Then `ledger_service.log_credit(category=STAGE_EARNING,
amount=final_payable, assignment=<that SWA>)`. So **every `stage_earning` credit still traces to one
SWA source row** — `WorkerLedgerEntry.assignment` (PROTECT) satisfied with **zero ledger schema
change**; the only difference is the SWA row is written at *settlement*, not *allocation*.
`allocation_service.allocate_stage_work` retires from the live complete-path (kept for back-compat;
**no removal migration**). Voiding/reopening soft-voids the SWA (`voided_at`) and reverses its credit
— `reconcile_stage_pay` already ignores voided SWAs.

### 11.5 Lifecycle
`draft → finalized → (reversed | superseded)`.
- **draft** — manager opens once the derived gate holds (every payable stage's active
  `WorkerStageTask`s `completed`). Manager enters packed/missing/rejected, picks `variance_policy`,
  picks per-advance recoveries. **No ledger rows yet** — a draft is a recomputable scratchpad
  (the only mutable surface, and it carries no money).
- **finalize** — the settlement money-write (earnings + recovery, **no cash**), single
  `@transaction.atomic`, lock order mirroring `create_settlement`: pg advisory lock 5374 (shared, so
  ADST/SETL refs never collide) → `AddaSettlement` row lock (reject double-finalize) → `AddaStageRecord`
  row locks (freeze the output qty the calc reads) → per-worker `WorkerProfile` lock → `WorkerAdvance`
  lock (over-recovery). Per worker: write SWA earning line(s) → `STAGE_EARNING` credit; write the agreed
  `ADVANCE_RECOVERY` debit + `PayrollSettlementItem` recovery lines (parented to this AddaSettlement);
  freeze the `AddaSettlementItem` snapshot. **No `SETTLEMENT_PAYMENT` debit here** — cash is a later event.
- **reversed / superseded** — never edits. Reverse every credit/debit via
  `ledger_service.reverse_entry` (copies original `entry_date` so it nets in-period), void the SWA
  lines, set status + `reversed_at/by`; `superseded` additionally creates a fresh `AddaSettlement`
  with `supersedes` pointing back. Balance auto-corrects via the live SUM. (Frozen `AddaSettlementItem`
  rows are NOT edited — the reversal is new ledger rows + a successor settlement's new snapshot.)

### 11.5b Full lifecycle: Contribution → Expected → Settlement → Final payable → Payment(s)
```
1. CONTRIBUTION (worker completes)        production truth, NO money
     WorkerStageTask.completed
     WorkerStageContribution: reported_quantity, color/size  + FROZEN expected_rate, expected_earning
        │
2. EXPECTED EARNING (during production)   visibility only, NO money
     Σ expected_earning shown to worker/manager (derived). Not a payable.
        │
3. ADDA SETTLEMENT — finalize (per Adda)  FINANCIAL TRUTH, no cash
     reconcile expected vs packed/missing/rejected/alter (manual snapshot)
     variance_policy = factory_absorbs → final_payable = expected (launch)
     decide advance recovery per worker
     LEDGER:  + STAGE_EARNING credit (per worker)     ─┐ net = final payable
              − ADVANCE_RECOVERY debit (agreed)        ─┘ owed in cash
     FREEZE AddaSettlementItem snapshot (append-only)
        │
4. FINAL PAYABLE                          = live worker_balance after step 3
     (Σcredit − Σdebit). Frozen copy on AddaSettlementItem.final_payable for audit;
     the live owed-now figure is the ledger balance.
        │
5. PAYMENT(S) — separate cash event(s)    immediate / partial / later / many
     PayrollSettlement (payment-only): − SETTLEMENT_PAYMENT debit (cash)
     guard: amount_paid ≤ current worker_balance
     remaining = live balance after each payment; reaches 0 when fully paid
```

### 11.5c Does Settlement≠Payment create architectural problems? (review — all manageable)
1. **Advance recovery re-homes** (payment→settlement). Cost: nullable `PayrollSettlementItem.adda_settlement`
   FK + splitting `create_settlement` into `finalize_adda_settlement` (earning+recovery) and payment-only.
   Advance math unaffected (sums regardless of parent). **Acceptable, flagged — not zero-churn.**
2. **Over-settle guard splits.** Recovery guarded at settlement (≤ advance remaining); payment guarded at
   pay-time (≤ worker_balance). Both under existing locks. Clean.
3. **"Paid for this Adda" is not a hard concept.** Once earnings from several Addas pool into one worker
   balance, money is **fungible** — you pay a *worker*, not an *Adda*. `AddaSettlementItem.final_payable`
   freezes what was owed *for that Adda*; "is it paid?" is a worker-balance question, not per-Adda.
   **Decision: do NOT build a per-Adda paid/unpaid flag** (it would lie). Report payable vs paid at the
   worker level; show the Adda's frozen final_payable as the historical figure.
4. **Snapshot vs live divergence is intended.** `AddaSettlementItem` is frozen; ledger balance is live.
   After a supersede they differ — that is the audit trail, not a bug. Never reconcile by editing the snapshot.
5. **No new "payment" model needed.** The existing `PayrollSettlement` already *is* the payment record;
   Model A just narrows it to cash. No extra table.

**Verdict:** the separation is *cleaner* than bundling (truth and cash decouple naturally onto the
append-only ledger). The only real cost is re-homing advance recovery — bounded and worth it.

### 11.6 Source of truth per layer
| Layer | Source of truth | Money? |
|---|---|---|
| Production lifecycle | `WorkerStageTask` (+ derived stage progress) | No |
| Production quantity | `WorkerStageContribution.reported_quantity` / `verified_quantity` | No |
| Expected earning (visibility) | `WorkerStageContribution.expected_rate` / `.expected_earning` (frozen) | No |
| Settlement business record | `AddaSettlement` + frozen `AddaSettlementItem` (the immutable approved snapshot) | snapshot/audit only |
| **Financial (money)** | **`WorkerLedgerEntry`** — Σcredit−Σdebit, never stored, sole writer `ledger_service`. Settlement = earning credit + recovery debit; payment = cash debit | **Yes — the one truth** |

### 11.7 Frozen (un-reconstructable) vs derived
**MUST be frozen** (cannot be rebuilt later):
- `contribution.expected_rate` / `expected_earning` (rate at complete; later rate edits destroy it).
- `contribution.reported_quantity` (the worker's locked claim — corrections go to `verified_quantity`).
- `contribution.color` / `size` / `bundle_item` (dimensional grain; un-backfillable).
- `WorkerStageTask` `started_at`/`completed_at`/`verified_at`/`verified_by` (event timestamps).
- `AddaSettlement.packed/missing/rejected/alter_total` + `AddaSettlementItem.packed/missing/rejected/alter_quantity`
  — **manually entered; NO production module holds these today** → the genuinely un-reconstructable
  settlement inputs (and the reason the snapshot must be stored).
- `AddaSettlement.variance_policy` (the credits don't carry their generating policy).
- **The full `AddaSettlementItem` snapshot** (`expected_earning`, `advance_outstanding_before`,
  `advance_recovered`, `final_payable`, `variance_amount`, settled_at/by) — owner-required frozen
  business record; never recomputed after finalize.
- The settlement-written SWA's `earning_rate_snapshot`/`earning_amount_snapshot`/`allocated_quantity`
  (the booked result; frozen so it always equals its ledger credit).

**Safely derived** (never store — storing invites drift):
- Worker payable / remaining = Σcredit − Σdebit (existing invariant) — the LIVE owed figure.
- `advance_remaining` / `advance_outstanding` = Σ given − Σ `PayrollSettlementItem.amount_recovered`.
- Worker-level paid-so-far / outstanding (NOT per-Adda — money is fungible, §11.5c.3).
- Stage progress counts / readiness; reconciliation classification.
- *(Note: the per-worker breakdown is intentionally BOTH frozen on `AddaSettlementItem` AND
  reconcilable to the live ledger — the frozen copy is the audit record, the ledger is the live truth.)*

### 11.8 Future-requirement stress test (all absorbed additively — no redesign)
| Scenario | Verdict | Seam already in the design |
|---|---|---|
| Worker disputes a settled amount | Absorbed | frozen contribution = worker's evidence; SWA+credit = factory's; `reported` vs `verified` kept separate |
| Settlement revision after finalize | Absorbed | `reversed/superseded` status + `supersedes` chain + reversal entries (append-only) |
| Partial settlement (some workers/stages now) | Absorbed | NO `unique(adda)`; index `(adda, -settled_at)`; **idempotency guard** below |
| Reopening a settled Adda | Absorbed | reverse affected settlement + void SWA lines + existing production reopen + new `AddaSettlement` |

### 11.9 Adversarial findings → INVARIANTS to lock at build time
1. **Double-credit guard (partial + reopen).** `finalize` MUST skip any `WorkerStageContribution`
   line already backed by a **non-voided** settlement SWA line (match on `worker, stage_record,
   color/size`). Without it, a second pass or a re-settle double-credits. **Hard invariant: a
   contribution maps to ≤1 non-voided settlement SWA earning line.**
2. **Quantity-freeze at finalize.** The settled quantity used (`verified_quantity` if set, else
   `reported_quantity`) is frozen onto the SWA line. A *later* `verified_quantity` edit must NOT
   silently change booked money — it requires reverse/supersede. Lock this.
3. **Per-color variance grain (bounded).** `AddaSettlementItem` freezes packed/missing/rejected/alter
   **per worker** (optionally per `stage_record`), not per color/size within a worker. With launch
   policy `factory_absorbs` there is no per-color money impact, so this is fine. If a per-color
   deduction policy is ever enabled, add an `AddaSettlementItemLine` child *additively* — no redesign.
   Bounded limit, logged, not silent.
4. **Audit snapshots are write-once / read-never-as-truth.** `AddaSettlement.*_total`,
   `AddaSettlementItem.*`, and `PayrollSettlement.payable_before` explain history; balances are always
   recomputed from the ledger.

### 11.9b Owner decisions — RESOLVED (2026-06-09), formerly open
- **Q1 → Model A (book earnings only).** Settlement finalizes earnings + recovery decision + final
  payable; **payment is a separate cash event** (immediate/partial/later/many). → §11.2, §11.5b.
- **Q2 → `factory_absorbs` at launch.** Variance tracked & reported, payable not auto-reduced; future
  deduction policies stay possible (settlement-time data, no schema change). → §11.10.
- **Q3 → frozen `AddaSettlementItem` table.** Append-only immutable per-worker business snapshot;
  ledger stays the live money truth. → §11.3.
- **Q4 → manual entry now, source-agnostic.** Snapshot stores manual packed/missing/rejected/alter;
  future modules feed them with no settlement schema change. → §11.10.

### 11.10 Source-agnostic variance inputs (manual now, modules later)
The settlement does **not care where packed/missing/rejected/alter counts come from**. V2: a manager
types them into the finalize form; they freeze onto the snapshot. Later, Packing/QC/Missing/Alter
modules become the authoritative source. The seam: settlement consumes a **summary value per
(adda[, worker, stage, dimension])**, supplied today by the form, tomorrow by a module-summary service —
**the `AddaSettlement`/`AddaSettlementItem` schema is identical either way.** No settlement migration
when the source flips. (`alter_quantity`/`alter_total` columns reserved now so the alter module plugs
in without a schema change.)

### 11.11 Missing Pieces & Alter/Rework — first-class domain concepts (own modules, NOT settlement)
The owner's domain rule: these are **operational lifecycles**, not settlement counters. Recommended:
- **Recognize them as first-class NOW in the domain map; BUILD them as their own modules LATER**
  (their own PRs, when prioritized) — *not* folded into the settlement build (seams-not-features).
- **Settlement consumes their summarized outcomes** (counts at settlement time, frozen on the snapshot)
  and **never owns their workflow.** §11.10's seam is exactly this consumption point.
- **Two distinct lifecycles, lean to two dedicated entities, not one generic counter** (owner's
  known future field sets recorded verbatim so the seam reserves the right shape):
  - **`MissingPieceCase`** — adda · color · size · detection stage · missing_date · resolution status ·
    recovery history · aging (open-duration) · audit trail. Status flow: open → recovered /
    completed-later / adjusted / written-off.
  - **`AlterCase`** — adda · color · size · defect type · defect stage · entered_alter_date ·
    current status · resolution_date · outcome (reworked / rejected / scrapped) · audit trail.
  - (A generic `ProductionVariance` with a type discriminator is viable only if the two lifecycles
    converge; the owner described **distinct** field sets + outcomes, so dedicated entities are the
    safer domain fit. Decide at module-build time — the settlement seam is agnostic to which.)
  - **Not built now** (owner confirmed): settlement consumes summary counts only; these modules ship
    in their own future PRs and then feed the §11.10 seam with zero settlement schema change.
- **Why not build them now:** no workflow exists yet, "no abstraction used <3×", and building lifecycle
  tables with no lifecycle = speculative. The settlement only needs the *summary seam*, which §11.10
  provides. When the owner prioritizes shop-floor missing/alter tracking, it's an additive module that
  feeds the seam — zero settlement redesign.

### 11.12 Net new tables (revised)
Production: `WorkerStageTask`, `WorkerStageContribution` (LOCK-NOW). Financial: `AddaSettlement`,
`AddaSettlementItem` (frozen). FK additions: `PayrollSettlementItem.adda_settlement` (nullable). Zero
ledger schema churn; SWA FK invariant intact; `WorkerAdvance.adda` NOT added. Future (own PRs, not now):
`MissingPieceCase`, `AlterCase` + histories.
