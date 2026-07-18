---
id: s5-design-receipt-2026-06-14
type: receipt
status: active
owner: append-only
scope: campaign/audit evidence
anchors: —
verified: 2026-07-13
---

# S5 Design Receipt — M-6 finalize BLOCK + allocation-bound rollout safety (2026-06-14)

Governed by [MASTER_PLAN_V2 (S5)](IMPLEMENTATION_MASTER_PLAN_V2.md) + the
[S1–S4 hostile review](S1_S4_HOSTILE_REVIEW_2026_06_14.md) (I-1 = the BLOCK; I-2/S4-005 =
rollout safety). **Design receipt only — no code.** Migration cursor: expense at **0010** →
S5 = **0011**. Two distinct reconciliation gates land here; keep them separate in your head:

| Gate | When | What it compares | Flag (default) |
|---|---|---|---|
| **M-6 settlement BLOCK** (the headline) | **finalize** (money boundary) | Σ settled good vs frozen **produced** output (`cost_quantity_snapshot`) — the B-1 leak: paid > produced | `ENFORCE_SETTLEMENT_RECONCILIATION` (False = WARN) |
| **Allocation bound** (S4 Phase 4, already shipped) | **complete** | Σ(good+alter+missing) vs Σ allocated | `ENFORCE_ALLOCATION_BOUND` (False) |

S5 = (A) flip M-6 WARN→configurable BLOCK + (B) the **rollout safety for both** flags
(S4-005): soft-warn, preview report, operator guidance.

---

## A. M-6 finalize BLOCK

### 1. Configurable WARN → BLOCK
- New setting **`ENFORCE_SETTLEMENT_RECONCILIATION`** (env, default **False** = today's
  WARN-only behavior — safe + reversible, mirrors `LEDGER_CREDIT_AT_ALLOCATION` /
  `ENFORCE_ALLOCATION_BOUND`). When **True**, an `over_allocated` stage beyond tolerance
  **blocks finalize**.
- **Scope = `over_allocated` ONLY** (consistent with H1's `SETTLEMENT_WARN_FLAGS`). The B-1
  leak is `Σ settled good > produced` (`reconcile_stage_pay._classify`: `alloc_qty > out_qty`).
  `grouped_paid`/`unpriced_paid`/`no_output_qty` are NOT finalize-blockers (you can't block a
  fixed-cost / no-output stage) — they stay in the integrity report, never the BLOCK.

### 2. Tolerance handling
- New setting **`SETTLEMENT_RECONCILIATION_TOLERANCE`** (Decimal, default **0** = strict when
  enabled). A stage blocks only when `Σ settled good − produced > tolerance` (absolute pieces).
  Absorbs legit small discrepancies (rounding, minor rework) without false-positives. Global
  for S5; per-stage tolerance is a documented future refinement (not S5).

### 3. Where it runs (pre-check, no write-then-rollback)
- A **pre-finalize** check computes the would-be over-allocation from the contributions about
  to settle (`Σ settlement_quantity(c)` per stage vs `cost_quantity_snapshot`) — **before** any
  SWA/ledger write. If `ENFORCE` + a stage exceeds tolerance + no override → **raise** (block);
  nothing books (clean, no rollback churn). Quantity-only — reads `settlement_quantity` (= good)
  + `cost_quantity_snapshot` (= produced); **never rate/earning/cost_method** (keeps the 4
  concerns independent; same quantity-based logic `reconcile_stage_pay` already uses).
- On a **successful** (or overridden) finalize, the existing `record_reconciliation_evidence`
  (S1.1 H2) still persists the over_allocated evidence rows for the soak trail.

### 4. Audited override flow
- `finalize_adda_settlement(..., reconciliation_override=None)`. If blocked AND a non-empty
  `reconciliation_override` reason is supplied AND the actor is **super_admin** → finalize
  proceeds, and each over_allocated evidence row is stamped with the override. Without an
  override (or by non-super-admin) → blocked. Override is the owner's explicit "I accept this
  over-allocation, here's why" — **append-only audited forever**.
- **Persistence:** extend `SettlementReconciliationEvidence` (migration **expense 0011**) with
  `override_reason` (TextField, blank) + `overridden_by` (FK User, null). A normal WARN finalize
  → no override; an overridden BLOCK finalize → evidence rows carry the reason + actor + the
  over-amount. Reuses the evidence table (no new model).

### 5. Operator diagnostics (why finalize is blocked)
- The block `ValidationError` is **actionable**, naming every blocked stage: *"Cannot finalize
  {ref}: stage '{stage}' settles {settled} pieces but only {produced} were produced (over by
  {delta}; tolerance {tol}). Fix the verified quantity (Review Reports), void the over-allocation,
  or finalize with a super-admin override (reason required)."* Mirrors the F5 reopen-guard
  actionable style.
- **UI surfacing (thin, operator-facing — like the S1.1 rate-correction UI):** the settlement
  detail/finalize screen shows a **blocked banner** with the per-stage diagnostics + (for
  super_admin) a **"Finalize with override"** action that requires a reason. Management without
  super_admin sees the diagnostics + the corrective paths, no override button.

---

## B. Rollout safety (S4-005 — for `ENFORCE_ALLOCATION_BOUND`, the Phase-4 bound)

### 6a. Soft-warn before enforcement
- `save_draft_contributions` (and `report_contributions`) return a **non-blocking** warning when
  `good+alter+missing` for a (worker, stage, dims) would exceed `Σ allocated` — surfaced in the
  worker report UI as a hint, **even while `ENFORCE_ALLOCATION_BOUND` is off**. So workers/managers
  see over-allocation BEFORE complete, with no hard failure during the ramp.

### 6b. Preview utility / report (the pre-flip audit)
- `pool_service.preview_bound_violations(adda=None)` → every COMPLETED contribution that *would*
  fail the bound if the flag were flipped: (i) over-bound (`Σ good+alter+missing > Σ allocated`),
  and (ii) **unallocated** completions (`allocated = 0`, reported > 0) on pool-participant stages.
- Surfaced two ways: a **management command** `preview_allocation_bound` (mirrors `reconcile_pay`
  — runnable pre-deploy / cron, exit 1 if violations) + a read-only **management report screen**
  (optional, thin). This is the "show unallocated/over-allocated completions" the review asked for.

### 6c. Operator guidance
- A runbook section: **before** flipping `ENFORCE_ALLOCATION_BOUND=True` — run
  `preview_allocation_bound`, confirm zero violations (allocate the unallocated, correct the
  over-bound), THEN enable. Same pattern documented for `ENFORCE_SETTLEMENT_RECONCILIATION`
  (run `reconcile_pay --all`, clear over_allocations or pre-authorize overrides, then enable).

---

## Enumerations
- **Settings:** `ENFORCE_SETTLEMENT_RECONCILIATION` (False) + `SETTLEMENT_RECONCILIATION_TOLERANCE`
  (Decimal 0), in `config/config/settings/base.py`, env-overridable, documented as the M-6
  kill-switch + tolerance.
- **Migration:** expense **0011** — add `override_reason` + `overridden_by` to
  `SettlementReconciliationEvidence` (additive, nullable/blank).
- **Services:** `reconciliation_service.settlement_block_check(adda, tolerance)` (over_allocated
  stages beyond tolerance, from settlement_quantity vs output) · `adda_settlement_service.finalize`
  pre-check + override param + evidence stamp · `pool_service.preview_bound_violations` ·
  `worker_task_service` draft soft-warn. No new writer of money.
- **Commands:** `preview_allocation_bound` (+ existing `reconcile_pay` reused for M-6 pre-flip).
- **UI (thin):** settlement-detail blocked banner + super-admin override-with-reason action;
  (optional) bound-violations report screen.
- **Invariants preserved:** allocation / cost_method / earning / settlement independent — the
  BLOCK reads quantities only (good vs produced), no rate/earning/cost. `WorkerStageAllocation`
  untouched (production-only). **Settlement stays the only money boundary** — the BLOCK is AT
  finalize, gating money before it books; it moves no money itself.
- **Golden ₹225: byte-identical** — the golden Adda reconciles clean (no over_allocation), so it
  finalizes whether ENFORCE is on or off; default-off means zero behavior change. Merge gate.
- **Rollback:** both settings default-off → instant disable, no migration; the evidence-field
  migration is additive/reversible. No irreversible step (unlike S6).

## Test strategy
- M-6: ENFORCE off → over-allocated Adda finalizes with WARN (back-compat). ENFORCE on →
  over-allocated beyond tolerance **blocked** (diagnostic message names stage + delta); within
  tolerance → finalizes; super-admin override + reason → finalizes + evidence stamped
  (override_reason/overridden_by); non-super-admin override → still blocked; clean Adda →
  finalizes regardless. **Golden ₹225 byte-identical** (clean → unaffected, both flag states).
- Rollout safety: `preview_bound_violations` lists over-bound + unallocated completions; draft
  soft-warn returns the hint without raising; `preview_allocation_bound` command exit codes.
- Decoupling: a blocked/overridden finalize reads no rate/earning (assert quantities-only).
- Migration drift clean; full suite green.

## DOCS-SYNC
expense README (M-6 BLOCK + override + the two settings), `adda_settlement_service` +
`pool_service` chokepoints, FILE_MAP, PENDING_BACKLOG (S5), CLAUDE.md, a **runbook** section
(the two pre-flip checklists), the S1–S4 review (I-1/I-2 → addressed).

## Open decisions (confirm at approval)
1. **Override authority:** super_admin only (recommended — money-boundary override is an owner
   call) vs any management.
2. **UI depth:** thin (settlement blocked-banner + override action + a `preview_allocation_bound`
   command) — recommended — vs add a full bound-violations report screen now.
3. **Tolerance unit:** absolute pieces, global, default 0 (recommended) vs percentage / per-stage
   (future).

---
**STOP — full S5 design receipt delivered. Awaiting approval (and the 3 decisions) before any
code.** On approval: settings + migration 0011 + the finalize pre-check/override + diagnostics +
rollout-safety (soft-warn + preview) + thin UI + tests (golden gate) + DOCS-SYNC, gated as usual.
