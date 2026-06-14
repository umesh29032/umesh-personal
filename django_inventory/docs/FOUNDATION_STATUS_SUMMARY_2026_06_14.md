# Production-Truth Foundation — Status Summary (2026-06-14)

The current production architecture after the S1–S5 foundation + the F1–F4 hostile-review
fixes. **Single source for "what the foundation is, right now."** Built on Django 5.0 +
PostgreSQL. **641 tests green · golden ₹225 supersede chain byte-identical · both enforcement
flags ship OFF.** Governing design: [PRE_S1_DESIGN_ADDENDUM](PRE_S1_DESIGN_ADDENDUM.md) +
[S4_DESIGN_CORRECTION_ADDENDUM](S4_DESIGN_CORRECTION_ADDENDUM_2026_06_14.md).

## The problem this foundation solved
The pre-staging audit found workers could be **paid 120 pieces against 105 produced** (the
B-1 leak) — settlement compensated for unreliable production data. The foundation makes
production data **correct by construction** and keeps **four concerns independent**:
**allocation** (capacity) · **costing** (`cost_method`) · **earnings** (rate × good) ·
**settlement** (the only money boundary).

## What shipped (sprint → reality)

| Phase | Shipped | Migration |
|---|---|---|
| **S1** | `settlement_quantity` resolver (verified??good); **`AddaStageRoleRate`** (frozen resolved payable rate per `(stage_record, role)`, snapshot at stage-start, locked at first completion); `WorkerStageContribution.role_snapshot`; M-6 reconciliation WARN | prod **0037** |
| **S1.1** | H1 WARN scoped to `over_allocated`; H2 **`SettlementReconciliationEvidence`** (persisted); super-admin **`rerate_stage_role`** + **`RateCorrectionAudit`** + thin UI; M1 = lock per `(stage_record, role)` | prod 0038 · expense 0010 |
| **S3** | **good/alter/missing** on `WorkerStageContribution` (`good_quantity` NOT NULL = payable; alter/missing immutable observations); RC-3 constraint swap; `reported_quantity` **dual-written = good** (renamed-not-dropped @S6); resolver/earning/payroll/display read **good** | prod **0039** |
| **S4** | **`allocation_dimensions`** {NONE,QUANTITY,COLOR_SIZE} (pool-only, orthogonal); **`StagePoolSnapshot`** (downstream-only); **`WorkerStageAllocation`** (production-only, no money, append-only) + pool draw-down (`pool_service`, advisory lock 5375); complete-time bound (`ENFORCE_ALLOCATION_BOUND`); Era-A reopen guard + `clear_stage_pool` | prod **0040–0042** |
| **F1–F4** | F1 rerate↔finalize race closed (advisory lock 5374); F2 grouped→0 structural guard (`effective_pay_rate`); F3 no flow-reorder while Adda in-flight; F4 reopen re-floats worker rate | — |
| **S5** | **M-6 finalize BLOCK** (`ENFORCE_SETTLEMENT_RECONCILIATION` + tolerance; super-admin audited override → evidence) + rollout safety (`preview_bound_violations` + `preview_allocation_bound` cmd + worker-report soft-warn + runbook) | expense **0011** |

## Current production architecture (how the pieces fit)

**Rate truth (S1).** A stage's payable rate is frozen per `(stage_record, role)` in
`AddaStageRoleRate` at stage-start, locked at first completion. `complete_worker_task` freezes
`expected_rate` from it (never the live workflow). Corrections: management `edit_until_lock`
(pre-lock); super-admin `rerate_stage_role` (until settlement, auto-recalcs, audited via
`RateCorrectionAudit`, refused once settled). **Grouped members always resolve to 0** —
`cost_service.effective_pay_rate` enforces it structurally at complete, rerate, AND finalize
(F2), so a stale snapshot can never double-pay.

**Production-truth grain (S3).** `WorkerStageContribution.good_quantity` (NOT NULL) is the
payable truth; `alter`/`missing` are immutable observations. `reported_quantity` is dual-written
equal to good (legacy reads; dropped at S6). Settlement pays **good**, never the raw claim.

**Piece-pool + allocation (S4, INERT until a piece-consumer stage exists).** Each
`WorkflowStage` declares `allocation_dimensions` (pool grain) — **independent** of
`credits_workers` and `cost_method`. The piece-pool starts at **Cutting** (pre-piece stages =
NONE); cutting's pool good is `AddaProductSizeColorPieceBreakdown` (single source, never
duplicated), read via handler-dispatched `pool_good`. `WorkerStageAllocation` draws the pool
down (`pool_service`, advisory lock 5375 — disjoint from settlement's 5374, never locks
`AddaStageRecord`); it carries **no money**. The complete-time bound (`good+alter+missing ≤
allocated`) and the finalize BLOCK (settled ≤ produced) are both available but **gated OFF**.

**Reopen (S4 P5).** `_downstream_consumer_guard` refuses upstream reopen while any downstream
stage has a non-voided allocation or completed contribution (transitive, reverse-first,
actionable error); reopen re-floats the rate (F4) + clears the stage pool.

**Settlement boundary.** Money books **only** at `finalize_adda_settlement` (the ledger is the
sole money truth). The M-6 BLOCK (S5) gates finalize on the B-1 leak (settled > produced) when
enabled, with a super-admin audited override. The foundation never moves money outside
settlement.

## Invariants (hold across all phases — verified)
1. **Four independent concerns** — allocation / cost_method / earning / settlement never couple.
2. **`WorkerStageAllocation` is production-only** — no rate/earning/ledger/settlement field.
3. **Settlement is the only money boundary** — pool/allocation/bound read quantities only.
4. **Golden ₹225 byte-identical** — every phase + every fix.
5. **Grouped → 0 is structural** — wins over any stale rate, at every pay-rate site.
6. **Lock domains disjoint** — production-allocation (5375) ⊥ settlement (5374); rerate is the
   one production op that *intentionally* joins settlement's 5374 (F1).

## Validation done
- **Hostile review** of S1–S4 (44 agents, per-finding verified) → caught the F1 critical race +
  F2/F3/F4; all fixed ([S1_S4_HOSTILE_REVIEW](S1_S4_HOSTILE_REVIEW_2026_06_14.md)).
- **Browser E2E** of the corrected system ([S1_S4_E2E_REVIEW](S1_S4_E2E_REVIEW_2026_06_14.md)) —
  login/landing, the rate-correction UI end-to-end (incl. mobile), flow editor, settlement.
  No new Critical.
- **641 tests green**; no migration drift.

## What remains
- **Enable enforcement** (post-deploy, per [ENFORCEMENT_ROLLOUT_RUNBOOK](ENFORCEMENT_ROLLOUT_RUNBOOK_2026_06_14.md)):
  deploy OFF → run `preview_allocation_bound` + `reconcile_pay --all` during soak → resolve →
  flip `ENFORCE_SETTLEMENT_RECONCILIATION` then `ENFORCE_ALLOCATION_BOUND`.
- **S6** — `reported_quantity` retirement + column DROP. The **only irreversible** foundation
  step; post-deploy, soak-gated, MT-1 backup + rollback review (design-only so far).
- **Future-fit** (not blockers): Adda-level cost-method/behavior override (today: product-level
  config + per-Adda rate correction); `allocation_dimensions` flow-editor UI (when a piece-
  consuming stage like stitching ships). See [S1_S4_E2E_REVIEW](S1_S4_E2E_REVIEW_2026_06_14.md) §N.

## Current factory flow (where the foundation is active vs dormant)
`Layering (NONE) → Cutting Pattern (NONE) → Cutting (COLOR_SIZE) → Barcode (NONE)`. Cutting is
the first + only piece stage; nothing downstream consumes its pieces yet, so the pool /
allocation / bound machinery is **built but dormant** — it activates when a piece-consuming,
worker-allocated stage (e.g. stitching) is added. Rate truth (S1), good/alter/missing (S3),
M-6 reconciliation (S1.1/S5), and the reopen guard are **active now**.
