---
id: docs-audit-phases-phase-i-edge-cases-integrity
type: receipt
status: active
owner: append-only
scope: audit
anchors: —
verified: 2026-07-18
---

# Phase I — Edge Cases, Concurrency & Data Integrity

**Deep integrity review** (not UI, not features). Goal: find paths where the system can go inconsistent / financially wrong / production-truth wrong / race-prone / partially-saved / double-processed / un-reconcilable. Grounded in actual code + execution paths. Built on A–H + the locked foundation.

---

## Verdict
**Integrity posture is strong, concentrated where it matters (money).** The settlement money-path is atomic + advisory-locked + ordered row-locks + up-front validation + double-credit guards; `on_delete=PROTECT` is universal on money/truth FKs (no cascade loss, no orphans); production truth is immutable + correction-by-reversal. **One real HIGH** (production truth can be internally inconsistent — the B-1 over-report), **one genuine concurrency gap** (`complete_worker_task` doesn't lock the task → a stage-complete race), and a handful of hardening items. No money double-credit or half-written-ledger path found.

---

## HIGH — real integrity risks

**I-1 — Production truth can be internally inconsistent: Σ worker contributions can exceed the stage's measured output.** *production-truth integrity* · confidence HIGH (live data)
- Evidence: cutting `pieces_cut = 105`, Σ billed contributions = 120 (Phase-B B-1). The system stores a "truth" where workers produced **more than the stage output** — irreconcilable by construction, and it flows straight to pay (₹360 vs ₹315).
- Why it's an *integrity* (not just financial) issue: there is no invariant tying Σ(contributions) ≤ stage output. Reported is immutable, so the inconsistent record is permanent unless reversed.
- The **locked foundation fixes this** (allocation-bounded reporting makes over-report impossible). Until then, production truth can be wrong-by-construction. This is the one HIGH integrity finding; it's the same root as B-1.

---

## MEDIUM — potential integrity risks

**I-2 — `complete_worker_task` doesn't lock the task → worker-complete vs manager-stage-complete race.** *concurrency / TOCTOU* · confidence HIGH (code)
- `complete_worker_task` is `@transaction.atomic` ([worker_task_service.py:195](config/production/services/worker_task_service.py#L195)) **but does not `select_for_update` the task** — it checks the in-memory `task.status` (fetched in the view's `_resolve`, before the atomic block) then writes `status=COMPLETED`. Meanwhile `resolve_stage_tasks_on_complete` (manager completing the stage) cancels `assigned`/`in_progress` tasks in a separate locked txn (`set_stage_workers` does `select_for_update`).
- Race outcomes (worker submits at the same moment the manager closes that stage):
  - Worker's COMPLETE commits after the cancel → **resurrects** a cancelled task (status flips back to COMPLETED).
  - Cancel commits after the worker's COMPLETE → worker's contributions are **frozen** (`expected_*` set) but sit on a **CANCELLED** task → settlement reads only COMPLETED/VERIFIED → **the work is silently excluded from settlement (unpaid)**.
- Probability low (needs simultaneous worker-submit + manager-stage-complete on the same stage); impact medium (unpaid frozen work, or a resurrected task). Not a ledger corruption (settlement is separately locked).
- Fix (also a **foundation precursor** — see below): re-fetch + `select_for_update(task)` and re-check status inside `complete_worker_task`. Effort: **S**.

**I-3 — Duplicate-draft protection relies on the Postgres advisory lock.** *concurrency / portability* · confidence MED
- `create_draft` serializes via `pg_advisory_xact_lock` **only when `connection.vendor == 'postgresql'`** + resumes an existing DRAFT. On a non-PG backend the lock is skipped, so two concurrent `create_draft` could both create drafts. Production is PG (safe), but there's **no DB-level partial-unique on (adda, status=DRAFT)** as a cross-backend backstop (not confirmed present).
- Impact: prod-safe today; a latent gap if the backend ever changes or the lock is removed. Fix: add a partial `UniqueConstraint(adda, condition=status='draft')` as defense-in-depth. Effort: **S**.

---

## LOW — hardening opportunities

**I-4 — A-1 (non-numeric quantity → 500) is contained, not corrupting.** Because `save_draft_contributions` is `@transaction.atomic`, the `Decimal(...)` crash rolls back fully — **no partial/lost draft**. So A-1 is a UX/validation bug (Phase A), **not** a data-integrity risk. Add the input guard for UX; no integrity action needed.

**I-5 — Ledger→settlement link is only transitive** (B-4): `WorkerLedgerEntry.settlement` always NULL; reversal entries link only via `reverses`. Reconstructable but not directly queryable. Auditability nit. Effort: **S**.

**I-6 — `report_contributions` (append-only path) is atomic but un-bounded** — quantity `> 0` only, no upper bound (the foundation adds it). Not used by the main submit path today (view uses save_draft + complete), but if wired in, it inherits the un-bounded gap. Note for the foundation.

---

## OK / WORKS-WELL — strong integrity protections

- **Settlement money-path is hardened:** `finalize` / `reverse` are `@transaction.atomic` + `pg_advisory_xact_lock` (single gate-lock) + **ordered** `select_for_update` (ADST → stage records → WorkerProfile → advances) → deadlock-safe; recoveries validated **before any write**; partial failure → full rollback (no orphans). Verified Phase-B Part 6.
- **No double-credit:** era-A (structural `adda_settlement__isnull`) + era-B (`settlement_line` + `voided_at`) guards; reversal voids SWAs to re-arm. Money cannot be credited twice.
- **Double-submit guarded by status:** finalize ("Only a draft"), reverse ("Only a finalized"), complete ("Task already completed"), report ("Cannot report on completed/cancelled"), create_draft (resume existing). Idempotent where it matters.
- **Referential integrity:** `on_delete=PROTECT` on **every** money/truth FK (worker_task + expense) → cannot delete a User/AddaStageRecord/settlement/advance with dependents → no cascade loss, no orphan history. Only DRAFT settlements (no inbound FKs) are deletable.
- **Production truth is immutable + correction-by-reversal:** `reported_quantity` locked after submit; corrections go to `verified_quantity`; drafts replaced atomically; completed work never deleted (cancelled tasks retain their contributions).
- **Append-only history:** `AddaHistory`/`*History` via single-writer `history_service`; settlement supersede chain (`supersedes`); reversals stamped (`reversed_at`, `reverses`). 26 CheckConstraints (DB integrity PR1).
- **Auditability — an auditor CAN reconstruct 6 months later:** every settlement event on the Adda timeline (actor + timestamp + reference), frozen `AddaSettlementItem` snapshots preserved through reversal, full credit/debit/reversal ledger, supersede chain links. The only friction is the transitive ledger→settlement link (I-5).

---

## Foundation Migration Risks (LOCKED foundation — hazards to plan)

1. **Constraint swap `wsc_reported_quantity_positive`** (`reported>0` → `good+alter+missing>0`, each ≥0). **Safe (loosening)** — every existing row satisfies the new constraint — but must be one atomic migration; validate against a prod-shaped dump.
2. **`reported_quantity` → `good_quantity` rename touches 18 read-sites + the settlement quantity rule.** Golden-test the ₹225 supersede chain identical before/after; migrate reads before dropping the column (drop is the only non-additive step, scheduled last).
3. **`I-2` is a PRECURSOR.** Allocation-bounded reporting adds an allocation **draw-down**; if `complete_worker_task`/the report path still don't `select_for_update`, the same TOCTOU becomes a **"consume allocation twice"** race. **Fix I-2's locking before wiring allocation consumption.**
4. **`AddaStageRoleRate` read in `complete_worker_task`** must fall back to the workflow rate when no snapshot exists (historical Addas) — else historical completes break.
5. **Bimodal data:** historical Addas have no allocations; pool-derivation + any "bounds hold" query must tolerate both (forward-only). Don't retro-enforce.
6. **Backfill known-facts-only:** `good ← reported`, `alter/missing = 0/NULL`; Adda rates from existing frozen `expected_rate`; flag in-progress Addas for owner rate review.

---

## Top 10 things most likely to break in production (probability × impact)

| # | Risk | Prob | Impact | Why ranked here |
|---|------|------|--------|-----------------|
| 1 | **Settlement-start GET → 500** (A-2) | High | Med | Any bookmark/refresh/back hits it; trivial to trigger |
| 2 | **Over-report → overpay** (I-1/B-1) | Med-High | High | Every unverified payable stage; real money leak |
| 3 | **Unpriced stage → silent ₹0 pay** (A-5) | Med | Med-High | Easy to forget a rate on a new stage; workers unpaid |
| 4 | **DEBUG traceback leak** if mis-deployed (G-SEC-1) | Med | High | One settings slip exposes internals |
| 5 | **Bare 403 / inconsistent denial** (G-UX-1) | Med | Low | Managers hit restricted URLs routinely |
| 6 | **Unapplied migration 0014** at deploy (E) | Med | Med | Schema head ≠ running; surfaces at deploy |
| 7 | **complete vs stage-complete race** (I-2) | Low | Med | Narrow timing window; stranded/unpaid or resurrected task |
| 8 | **Non-numeric input → 500** (A-1) | Low-Med | Low | Contained by atomic (no corruption), still a 500 |
| 9 | **History cross-Adda visibility** (G-AUTH-1) | Low | Low | Already reachable; operational data only, no money |
| 10 | **Dup-draft on non-PG / lock skip** (I-3) | Low | Low | Prod is PG; latent only |

---

## Net Phase I
The money engine and referential integrity are **production-grade** (atomic + locked settlement, PROTECT-everywhere, immutable truth, append-only audit, reconstructable history). The genuine items: **I-1** (production-truth over-report — fixed by the foundation), **I-2** (task-lock race — small fix, and a **prerequisite** before the foundation's allocation draw-down), and hardening (**I-3** dup-draft backstop, **I-5** ledger link). The most *likely* production breakages are the already-known **A-2 (500)**, **A-5 (unpriced ₹0)**, and **G-SEC-1 (DEBUG)** — all cheap, all worth fixing before staging.
