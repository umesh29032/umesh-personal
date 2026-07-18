---
id: s1-s4-hostile-review-2026-06-14
type: receipt
status: active
owner: append-only
scope: campaign/audit evidence
anchors: —
verified: 2026-07-13
---

# S1–S4 Foundation Hostile Review — Findings + Fix Plan (2026-06-14)

Full adversarial review of the shipped S1–S4 production-truth foundation (44 agents:
5 subsystem reviewers + per-finding independent verification, grounded in real code).
Step 2 of the validation sequence. **Verdict: architecture SOUND; implementation has 1
critical + 1 high money-safety defect to fix + a few medium robustness fixes. No
architectural uncertainty — all fixable now, no production evidence needed.**

## Confirmed-correct (reviewers verified these HOLD)
Dual-write invariant (`reported==good`) · RC-3 constraint logic · `good_quantity` NOT-NULL
backfill · `expected_earning` freeze · single settlement-quantity policy · `settlement_line`
provenance · cross-era double-credit guard · settlement touches only completed/verified ·
advisory-lock namespace disjointness (5375 two-int vs 5374 bigint) · the 4-concern decoupling
(allocation/cost_method/credits_workers/settlement) · pool/allocation inert + money-free in
the live flow. **The foundation's core is verified correct.**

## MUST FIX (money-safety) — before S5

### F1 🔴 CRITICAL — `rerate_stage_role` races `finalize` (S1-RACE-001 / S1-BOUNDARY-001) — ✅ FIXED 2026-06-14
**Fixed:** `rerate_stage_role` now acquires `pg_advisory_xact_lock(5374)` (the settlement
`_REF_LOCK`, shared with finalize/reverse) FIRST, before the settled-check → serialized
against finalize; the race window is closed. Lock-order docstrings updated (rerate joins the
settlement serialization boundary). 47/47 + full suite green; golden ₹225 byte-identical.
`rerate_stage_role`'s settled-check is an **unlocked** `.exists()` read
(`stage_rate_service.py:145-149`); it then locks the WSC rows only at `:161`. A concurrent
`finalize_adda_settlement` can write `settlement_line` (`adda_settlement_service.py:338-339`)
**between** the check and the lock → rerate then recalcs `expected_rate`/`expected_earning`
on a contribution that was **just settled**, leaving the SWA earning inconsistent with the
`RateCorrectionAudit`. Verified exploitable (high confidence). The "disjoint lock domains"
claim is wrong for rerate-vs-finalize (S1-LOCK-ORDER-001, same root).
- **Fix:** `rerate_stage_role` acquires the settlement advisory lock `pg_advisory_xact_lock(5374)`
  (the same `_REF_LOCK` finalize/reverse hold) at the top, before the settled-check →
  serializes rerate against finalize/reverse → the check can no longer be overtaken. Update
  the lock-order docstring: rerate **joins** the settlement serialization domain (it is a
  settlement-boundary operation). Closes F1 + S1-LOCK-ORDER-001.

### F2 🟠 HIGH — grouped-member stale non-zero rate → double-pay (S1-GROUPED-001) — ✅ FIXED 2026-06-14
**Fixed:** new structural guard `cost_service.effective_pay_rate(ws, candidate) → 0 if
ws.cost_billed_at_id else candidate`, applied at **all three** sites where expected_rate/
earning is (re)computed — `complete_worker_task` (freeze), `rerate_stage_role` (recalc), and
the **finalize money boundary** (`adda_settlement_service`, per-contribution earning). A
grouped member now pays 0 even if a stale non-zero snapshot was frozen before grouping — and
even for pre-existing stale frozen contributions (the finalize guard catches them at the money
boundary). Tests: stale-snapshot→complete→0, rerate-grouped→0, helper. Golden ₹225 byte-
identical (existing grouped stages were already 0 → no-op); full suite green.
`AddaStageRoleRate` freezes the resolved rate at stage-start. If a stage's `cost_billed_at`
is set NULL→payer **after** the snapshot (a mid-Adda regrouping), the frozen rate stays
**non-zero**; `complete`/`rerate` pay it from the snapshot while the payer also covers the
group → **grouped member double-pay** (violates C-1). Verified.
- **Fix:** enforce the C-1 **structural** invariant at freeze time — in `complete_worker_task`
  (and `rerate`), if `ws.cost_billed_at_id is not None` (grouped NOW), pay **0** regardless of
  the frozen snapshot. Grouped→0 is structural, not a rate value; it must win over a stale
  snapshot. (Rate freezing still applies to non-structural rate edits — M-5 intact.)

## SHOULD FIX (cheap, correctness/robustness) — before S5

### F3 🟡 MEDIUM — `void_allocation` resolves source before locking (S4-VOID-007) — ✅ FIXED 2026-06-14
**Fixed at the root:** `move_stage_in_product_flow` now refuses to reorder a flow while the
product has any in-flight (non-completed/cancelled) Adda → `_upstream_pool_source` stays stable
for an active Adda's lifetime, eliminating the void/allocate source-resolution window. Tests:
reorder refused with in-flight Adda; allowed with none / only terminal Addas. Full suite green.
`void_allocation` (`pool_service.py:284-286`) resolves `_upstream_pool_source` then acquires
the advisory lock — a brief window vs a concurrent `move_stage_in_product_flow` reorder.
- **Fix:** acquire the pool lock first (or resolve+lock atomically); cheap reorder of statements.

### F4 🟡 MEDIUM — reopen clears cost but not `AddaStageRoleRate.locked_at` (S1-COST-SNAPSHOT-001) — ✅ FIXED 2026-06-14
**Fixed (owner: symmetric model):** `stage_rate_service.refloat_rates_on_reopen(sr)` re-resolves
each `AddaStageRoleRate` row from the current config + clears `locked_at`, wired into the reopen
skeleton right after `clear_stage_cost` — so cost-freeze and worker-rate-freeze behave
symmetrically (re-complete re-freezes the rate at the current value; grouped→0 via the F2
guard). Documented in the reopen contract. Tests: reopen re-resolves+unlocks (5→8); grouped
re-resolves to 0. Full suite green; golden ₹225 byte-identical.
Reopen runs `clear_stage_cost` but leaves the rate row **locked** → asymmetric (cost
re-freezes at re-complete; worker rate stays frozen). Recoverable (super_admin `rerate`), but
inconsistent.
- **Fix (owner-confirm):** reset `AddaStageRoleRate.locked_at = NULL` in the reopen skeleton
  (symmetric with `clear_stage_cost`) so re-complete re-freezes the rate at the current
  resolved value. *Decision:* does reopen re-float the worker rate (symmetric, recommended) or
  keep it frozen at first completion? Recommend re-float (symmetry + `edit_until_lock` works
  again post-reopen).

## NOTE / DEFER (S5-prep or non-issues)
- **S4-005 (→ S5):** flipping `ENFORCE_ALLOCATION_BOUND=True` has no soft-landing — no draft
  soft-warn, no "preview unallocated completions" pre-check. **This IS the S5 rollout work**
  (soft-warn + a pre-flip audit utility). Not a current bug.
- **TEST-WARN-003 / DORMANT-002 (→ S5):** recon WARN records only `over_allocated`; the S5
  BLOCK + tolerance lands then. Expected.
- **S4-006:** `worker_allocated` is implicitly Adda-scoped (stage_record is Adda-unique) —
  verified safe today; add a clarifying comment. Non-issue functionally.
- **S4-007:** the reopen guard ignores CANCELLED-task contributions — correct (cancelled ≠
  production truth); a bypass needs manually cancelling a *completed* task (not a normal path).
  Note only.
- **S4-001/004:** `clear_stage_pool`'s nested `@transaction.atomic` is harmless (savepoint);
  optional cleanup.
- **S1-RECON-001: REFUTED** (the over_allocated-only scope is the intended H1 narrowing).

## Outcome
No finding indicates **architectural** uncertainty — the pool/allocation/rate/settlement
separation, lock-domain design, and freeze model are verified sound. The defects are
implementation-level (a concurrency window + a structural-invariant gap + two robustness
nits), all fixable now without production data. **Fix F1+F2 (must) and F3+F4 (should), then
proceed: browser E2E (step 3) → S5 (flag-off) → S6-reversible.** S4-005/TEST-WARN-003 fold
into S5's rollout scope. The irreversible S6 column DROP remains post-deploy (step 9).

## ✅ ALL FOUR FIXED 2026-06-14 — foundation review CLOSED
F1 `8faa0230` · F2 `890665ce` · F3 `ad00c3b2` · F4 (this commit). Each its own gated commit,
golden ₹225 byte-identical + full suite green after every step. No architectural uncertainty
remained; no production data was needed. **Next: step 3 browser/manual E2E of the corrected
system; then S5 (flag-off) + S6-reversible.** Deferred (correctly): S4-005 + TEST-WARN-003 →
S5 rollout scope (soft-warn + pre-flip audit utility); S6 irreversible DROP → post-deploy
(step 9).
