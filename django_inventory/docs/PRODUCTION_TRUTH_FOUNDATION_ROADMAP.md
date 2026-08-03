---
id: docs-production-truth-foundation-roadmap
type: topic-canonical
status: active
owner: handwritten
scope: project
anchors: —
verified: 2026-07-18
---

# Production-Truth Foundation — Implementation Roadmap & Migration-Safety Review

Planning only. **No code, no migrations, no implementation.** Baseline = the approved foundation ([REVIEW](PRODUCTION_TRUTH_FOUNDATION_REVIEW.md) + [FINAL](PRODUCTION_TRUTH_FOUNDATION_FINAL.md)). Current migration heads: **production 0036, expense 0009, tracking 0014.**

---

## 0. Design challenges & tech-debt flags (read FIRST — these shape the plan)

The approved design is sound, but five risks must be acknowledged before code:

1. **🔴 Open-mode pool race has no lock anchor.** In Open/pool-bound mode the bound is a *derived* aggregate (Σ good − allocated) — there is **no row to `select_for_update`**. Two workers reporting concurrently can both pass the check and jointly exceed the pool. Strict mode is safe (lock the per-worker allocation row); Open mode is not. **Mitigation options:** lock the `AddaStageRecord` (or the cutting-breakdown rows that define the pool) for the duration of an Open-mode report, OR keep a thin per-(stage,color,size) **pool-counter row** purely as a lock anchor (not as truth — truth stays derived). This is the single biggest hidden risk; decide before Slice 4.

2. **🟠 `reported_quantity` semantic overload = naming debt.** Reusing the column as "Good" is migration-cheap but the name lies. Future devs will misread it. **Choice:** (a) keep the column + add a `good_quantity` property/alias + loud docs (accepted debt, zero migration), or (b) rename column → `good_quantity` (honest, but a data migration touching every read-site). Recommend (a) now, (b) only if it bites.

3. **🟠 Two allocation concepts will coexist.** `expense.StageWorkAssignment` already carries (color, size, allocated_quantity) — but it's a **settlement earning line** (money, era-B). The new `production.WorkerStageAllocation` is a **pre-production bound** (truth). Similar names, different layers. **Risk:** future confusion / accidental coupling. Mitigation: name deliberately (consider `WorkerPieceAllocation` or `StagePieceAllocation`), and document the truth-vs-money distinction in both models' docstrings.

4. **🟠 Forward-only = a bimodal system.** Old Addas (unbounded, no allocations) and new Addas (bounded) coexist permanently. Every dashboard/report/query must tolerate both (e.g. "pieces produced" on an old Adda may exceed physical output; a new one cannot). Don't write queries that *assume* bounds hold. Document the cutover Adda/date.

5. **🟡 In-progress-Adda rate backfill is ambiguous.** A historical *completed* contribution has a real `expected_rate` (known fact → backfill it). An Adda mid-flight at migration time has some completed (rate known) + some not (rate = current workflow, which may already have drifted). **Rule:** backfill only completed-derived rates; for not-yet-completed stages snapshot the current workflow rate **and flag those Addas for owner review** — never silently assert a rate that was never used.

---

## 1. Phase-by-phase rollout sequence

Five slices, each independently shippable and reversible. Ordered safest-first; the behavioral/UX change is last and flagged.

| Slice | What | Depends on | Ships independently? | Risk |
|-------|------|-----------|----------------------|------|
| **S1 — Settlement resolver refactor** | Extract `settlement_quantity(c, policy)`; default policy = exact current (`verified ?? reported`) | nothing | ✅ yes | Low (behavior-preserving) |
| **S2 — AddaStageRoleRate** | Adda-start rate copy + first-completion lock + read-frozen | nothing (fallback to workflow rate if no snapshot) | ✅ yes | Low–Med |
| **S3 — Good/Alter/Missing columns** | +`alter_quantity`,`missing_quantity` (nullable); loosen the positivity constraint; optional UI inputs | nothing | ✅ yes (no enforcement) | Med (constraint swap) |
| **S4 — Allocation model + pool** | `WorkerStageAllocation` table + pool-derivation fn (future-shaped) + Strict/Open stage flag + allocation UI | S3 (fields) | ✅ yes (no enforcement yet) | Med |
| **S5 — Bounded reporting (ENFORCE)** | `good+alter+missing ≤ allocation|pool`; color/size from allocation; flagged, forward-only | S3 + S4 | ⚠️ behind flag | **High** (behavior + UX + race #1) |

**Build first:** S1 (de-risk settlement) + S2 (independent, delivers A-5 fix). **Defer:** Rework domain (populates the Recovered term), Missing-Pieces domain, packed-based settlement policy, the actual policy choice. **What blocks TM-1:** S3+S4+S5 must land before TM-1 (a barcode scan must draw down an allocation + carry good/alter/missing).

---

## 2. Database migration strategy

**New tables:** `AddaStageRoleRate` (S2), `WorkerStageAllocation` (S4), `WorkerStageAllocationHistory` (S4, append-only audit). Optional pool-counter-as-lock-anchor (S5, only if Open-mode race mitigation chooses it).

**New columns:** `WorkerStageContribution.alter_quantity`, `.missing_quantity` (S3, `Decimal`/int, null=True, default 0). `WorkflowStage.allocation_mode` (S4, choices strict/open, default open so the floor is never blocked). Possibly `AddaStageRoleRate.locked_at`.

**Constraint change (S3 — the notable one):** replace `wsc_reported_quantity_positive` (`reported_quantity > 0`) with the new shape: `reported_quantity ≥ 0`, `alter_quantity ≥ 0`, `missing_quantity ≥ 0`, and `reported_quantity + alter_quantity + missing_quantity > 0`. **Safety:** this is a **loosening** — every existing row (reported>0, alter/missing null→0) already satisfies the new constraint, so validation cannot fail on current data. Still do it as one atomic migration; test on a prod-shaped dump.

**Backfill approach (known facts only):**
- `alter/missing` → leave NULL/0 on all historical rows (no invention).
- `AddaStageRoleRate` → per `(completed stage_record, role)` derive from existing `contribution.expected_rate`; for not-yet-completed stages on in-progress Addas, snapshot current workflow rate + flag for review (challenge #5).
- `WorkerStageAllocation` → **none** for historical Addas (forward-only; no retro-allocation).

**Data-integrity risks:** constraint swap (mitigated: loosening); backfill rate ambiguity (mitigated: flag in-progress); bimodal queries (challenge #4).

**Rollback strategy:** every slice is additive ⇒ rollback = reverse-migration drops the new table/column with no data loss to existing tables. S1 (resolver) rolls back by code revert (no schema). S5 enforcement rolls back by **flag off** (no migration) — the flag is the primary kill-switch, the migration is secondary. Keep S2's "read frozen rate" behind a fallback so reverting the read-path can't strand earnings.

---

## 3. Service-layer impact analysis

Verified read-sites (18 non-test `reported_quantity` reads; the money-critical ones):

| Service | Today | Change | Slice |
|---------|-------|--------|-------|
| `worker_task_service.save_draft_contributions` / `complete_worker_task` | writes `reported_quantity`; freezes `expected_rate` from live `ws` ([:156-219](config/production/services/worker_task_service.py#L156)) | + allocation bound; + alter/missing; rate source → `AddaStageRoleRate` | S5 / S2 / S3 |
| `adda_settlement_service` finalize `:314` + preview `:184` | hardcoded `verified ?? reported` | → `settlement_quantity(c, policy)` resolver | S1 |
| `expense/views.py _line_dict :341` | same hardcoded rule | → resolver | S1 |
| `payroll_service :227-237` ("pieces produced" = Σ `reported_quantity`) | sums reported | unchanged semantics (reported = good); self-corrects forward | — |
| `cost_service` (processing_cost) | `ws.cost_rate × handler qty` (standard) | **unchanged** — standard cost stays separate from payable rate | — |
| `flow_service` | template rates | unchanged; rates now *copied* at Adda-start (additive) | S2 |
| `WorkerStageTask` lifecycle | roster only | **unchanged** (allocation is a sibling, not on the task) | — |

**Assignment flow:** `set_stage_workers` (roster) stays; gains a companion allocation step (S4). **Reporting flow:** the single-writer chokepoint gains the bound (S5) — keeps service-layer-owns-writes (rule 4). **Settlement flow:** only the *quantity source* changes (resolver); reverse/supersede machinery **untouched** (already correct — Phase-B Part 6). **Costing flow:** untouched (standard cost is a deliberately separate measurement). **Dashboard/reporting:** stage-loss view is a new derived read-model (S4+); "pieces produced" stat unaffected.

---

## 4. UI impact analysis

| Surface | Impact | Slice |
|---------|--------|-------|
| **Manager assignment screen** | New: allocate color/size/qty per worker (Strict) or skip (Open). Redesign of the roster screen. **Phase-C carve-out applies.** | S4 |
| **Worker reporting screen** | Form driven by *their allocations* (color/size locked, qty blank); + optional Alter/Missing inputs; cap never rendered. **Phase-C carve-out applies.** | S5/S3 |
| **Mobile worker flow** | Most affected — must stay phone-first (rule 11): big touch targets for good/alter/missing, no cap leakage, low-friction numeric entry. | S5 |
| **Expected earnings visibility** | Unchanged concept; number now = good × Adda-frozen-rate. "Pieces produced" becomes trustworthy on new Addas. | S2/S5 |
| **Rate review at Adda-start** | New optional owner review/edit screen for copied rates. | S2 |
| **Good/Alter/Missing inputs** | New input group on the report form. | S3 |

The two carved-out screens (worker report + assignment) are exactly the S4/S5 UI — review them with the foundation, not in Phase C.

---

## 5. Testing strategy

- **Migration tests:** constraint swap against a prod-shaped dump incl. edge rows (reported=1); confirm loosening never fails; backfill rate-derivation correctness; reversibility (migrate up→down→up). Verify the existing `wsc_*` constraints survive.
- **Unit:** pool-derivation fn (incl. `Recovered=0` term present); rate-lock predicate (editable before first completion, locked after); resolver returns current behavior for default policy.
- **Service:** allocation bound Strict (reject good+alter+missing > allocation); Open (reject > remaining pool); reduce-allocation-below-reported rejected; re-cut raises pool; reassign moves bound; rate read from snapshot not workflow.
- **Integration:** full new-Adda path (copy rates → allocate → bounded report → complete → rate locks → settle via resolver) **vs** historical-Adda path (unbounded, still settles, no allocations) — both green.
- **Golden/regression:** the existing ₹225 supersede chain must reconcile **identically** before/after S1 (resolver refactor is behavior-preserving) and after S2 (rate source change must not move historical numbers).
- **Concurrency:** two-tab Open-mode report (the race in challenge #1) — assert the chosen lock prevents joint over-pool.
- **Edge coverage:** zero-good + alter>0; decimal vs integer; in-progress-Adda backfill flagged; flag-off = old behavior exactly.

---

## 6. Risk analysis

| Risk | Severity | Mitigation |
|------|----------|-----------|
| **Open-mode pool race** (no lock anchor) | 🔴 High | Lock stage_record / breakdown rows, or a pool-counter lock-anchor row (challenge #1). Decide before S5. |
| **Settlement regression** in resolver refactor | 🔴 High | Default policy = byte-identical current rule; golden-test the ₹225 chain before/after. Pure refactor, no policy change in S1. |
| **Constraint swap** on populated table | 🟠 Med | It's a *loosening* — existing rows can't violate it. One atomic migration; test on dump. |
| **Rate-source change** moves historical earnings | 🟠 Med | Fallback to workflow rate when no snapshot; backfill from existing frozen `expected_rate`; golden-test historical settlements. |
| **Bimodal historical data** | 🟠 Med | Forward-only; queries tolerate both; document cutover. |
| **Two allocation concepts drift** | 🟡 Low–Med | Deliberate naming + docstrings (challenge #3). |
| **Production-truth consistency** (pool defined twice) | 🟠 Med | ONE pool-derivation function used by allocation-check, reporting-bound, and dashboard — never re-implement. |

---

## 7. Build-order recommendation (safest incremental)

```
S1  Settlement-quantity resolver refactor   (behavior-preserving; golden-tested)   ← de-risk money first, zero user impact
S2  AddaStageRoleRate (rate copy + lock)    (independent; fixes A-5 + drift)        ← reversible via fallback
S3  Good/Alter/Missing columns + constraint loosen (additive, no enforcement)      ← fields exist, UI optional
S4  WorkerStageAllocation + pool fn + Strict/Open mode (no enforcement)             ← populate + validate the math live
S5  Allocation-bounded reporting ENFORCE    (feature-flag, forward-only)           ← the behavior change, last, kill-switch = flag
────────────────────────────────────────────
DEFER: Rework domain (populates Recovered term) · Missing-Pieces domain · packed-based settlement policy · the policy choice
```

**Why this order:** money is de-risked first (S1) with no user-visible change; the highest-value independent win (rates, S2) ships early; the structural pieces (S3, S4) land additively with **no enforcement**, so you can populate allocations and watch the derived pool/loss numbers *before* anything is bound; the single behavior-changing slice (S5) is last, **forward-only, and gated by a flag** that is the instant rollback. Nothing in S1–S4 can break the current production-truth or settlement behavior; only S5 changes worker-facing behavior, and only for new Addas, and only when the flag is on.

**Resolve before starting S5:** the Open-mode race (challenge #1) and the `reported_quantity`-vs-`good_quantity` naming decision (challenge #2).

---

## Verdict
The approved design is buildable **safely and incrementally** with **zero destructive migrations** and a flag-gated behavior change. The roadmap surfaces one true hidden risk (Open-mode pool race) and four tech-debt items to decide consciously. Recommend: **lock the design + the S1→S5 order**, resolve challenges #1 and #2 as S5 design tasks, then build S1 first. Phase C can proceed now (worker-report + assignment screens carved out — they are the S4/S5 UI).
