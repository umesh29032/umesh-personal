# Pre-S1 Design Addendum — resolving the 7 MUST items (2026-06-14)

Binding design decisions that close the pre-S1 blockers from [FOUNDATION_DESIGN_CHALLENGE](FOUNDATION_DESIGN_CHALLENGE_2026_06_14.md) §F. **Amends, does not rewrite,** the locked foundation ([REVIEW](PRODUCTION_TRUTH_FOUNDATION_REVIEW.md)/[FINAL](PRODUCTION_TRUTH_FOUNDATION_FINAL.md)/[ROADMAP](PRODUCTION_TRUTH_FOUNDATION_ROADMAP.md)/[LOCKED](PRODUCTION_TRUTH_FOUNDATION_LOCKED.md)). No code, no migrations — architecture only. Each decision is verified against: settlement-first · ADR-0009 cost-truth · Option-B · AddaStageRoleRate roadmap · WorkerStageAllocation roadmap · future Missing-Pieces · future Alter/Rework · auditability · forward-only migration.

**One unifying move resolves 1–4:** generalize the pattern the codebase already uses at Cutting — `AddaProductSizeColorPieceBreakdown` (a frozen, per-(size,color), write-once-at-completion stage snapshot) — into a **per-stage `StagePoolSnapshot`** at the stage's own grain. That snapshot is simultaneously the pool source (M-1), the lock anchor + audit record (M-2), a lock-order citizen (M-3), and the thing reopen must protect (M-4).

---

## MUST-1 — Allocation/pool grain
**Problem.** The pool/allocation model assumes a per-`(color,size)` quantity at every stage, but only Cutting captures color/size (`cutting/handler.py`); coarse stages report quantity-only and `WorkerStageContribution.color/size` are nullable.

**Current-design weakness.** `pool(stage N, color, size) = stage N−1 good by (color,size)` is uncomputable downstream — no data. `AddaProductSizeColorPieceBreakdown` is a dead snapshot (0 consumers).

**Options.** (a) **Per-stage-variable grain** — each WorkflowStage declares its tracking dimensions; Cutting = `{color,size}`, coarse stages = `{}` (quantity-only). (b) Force color/size capture on all stages. (c) Always pool by (color,size); backfill downstream from cutting.

**Recommended: (a).** A new per-`WorkflowStage` field `allocation_dimensions` (enum: `color_size` | `quantity`). Allocation rows + the pool snapshot are stored at the stage's own grain (color/size NULL for `quantity` stages). The pool composes by **aggregating the upstream snapshot down to the downstream stage's (never-finer) grain**: a `quantity`-grain stitching stage's pool = Σ(cutting good over all color/size) = total available. **Invariant: grain may only coarsen downstream** (Cutting is finest; garments never re-fine). The anti-over-report property holds at whatever grain a stage tracks (Σ good ≤ total upstream good).
- *Reject (b):* fabricates color/size where the floor works mixed bundles — invented data, heavy worker UX.
- *Reject (c):* downstream good isn't attributable to (color,size) without capture — same invented data.

**Consequences.** Allocation UI + pool fn are dimension-aware (one branch). Strict at coarse stages = per-worker *quantity* slices (far fewer rows than color×size — also relieves M-13 friction). **Ties to TM-1:** `allocation_dimensions` is a sibling of TM-1's per-stage tracking mode — declare it as a per-stage setting, don't build TM-1.
**Migration.** Additive: `WorkflowStage.allocation_dimensions` (default `quantity`; Cutting flows set `color_size`); `WorkerStageContribution.color/size` already nullable. Forward-only.
**Future-domain.** Missing/Alter aggregate cleanly at coarse grain. Barcode (TM-2) can later *refine* a coarse stage to piece grain without breaking the formula (it adds a finer source).
**Rollback.** Drop the field; coarse stages simply have no allocation (pre-foundation behavior).

## MUST-2 — Pool lock anchor + materialization
**Problem.** Derived pool has no lock anchor (allocation→pool over-allocation race), is a recursive recompute, and is non-reconstructable for audit.

**Weakness.** Two managers each allocate 30 against pool 40 → Σ80; no row to `select_for_update`; "what ceiling was this allocation bound to 6 months ago?" unanswerable.

**Options.** (a) **Materialize a per-`(stage_record, dims)` `StagePoolSnapshot`** at stage completion (write-once, append-only, single-writer) — it is the pool source AND the lock anchor AND the audit record. (b) Lock the upstream `AddaStageRecord` (no materialization). (c) Mutable pool-counter decremented per allocation.

**Recommended: (a).** Generalize `AddaProductSizeColorPieceBreakdown` to all stages at the stage's grain. **`available = snapshot.good + Σ recovered_credits − Σ non-voided allocations`**; the snapshot is **immutable** (never decremented), allocations are the moving ledger. Allocation draw-down `select_for_update`s the `StagePoolSnapshot` row → the over-allocation race closes (M-3 orders it). Snapshot frozen at completion = full reconstruction.
- *Reject (b):* solves neither recompute nor audit, and locking SR collides with the settlement lock order (deadlock).
- *Reject (c):* a mutable counter is the exact drift hazard the locked design avoided; here the snapshot is immutable so there's no drift.

**Consequences.** Re-introduces a stored snapshot — but **write-once-at-completion, not a mutable counter**, so no drift (it mirrors the existing cutting breakdown's lifecycle). Reopen→recomplete clears+refreezes it (like cost snapshots), permitted only when no downstream consumer exists (M-4).
**Migration.** New `StagePoolSnapshot` table; backfill known facts only (existing cutting breakdowns → snapshot rows for completed cutting stages; downstream historical stages get none → forward-only enforcement).
**Future-domain.** `recovered_credits` is the seam for Rework (M-7). Auditability ✓.
**Rollback.** Drop the table; pool reverts to underived (no allocation enforcement) — flag-gated like S5.

## MUST-3 — Global lock order
**Problem.** Allocation draw-down vs settlement acquire `AddaStageRecord`/allocation in opposite orders → cross-transaction deadlock.

**Decision.** ONE documented global order, extended:
```
advisory(5374) → AddaSettlement → AddaStageRecord → StagePoolSnapshot → WorkerStageAllocation(by pk) → WorkerProfile → WorkerAdvance
```
Allocation draw-down acquires `StagePoolSnapshot` then `WorkerStageAllocation` rows — both **before** any WorkerProfile/settlement-level lock, and in this order everywhere. **Correct the P0-5 framing:** P0-5 locks the *task* row (worker-vs-stage-complete) — it is NOT the S5 pool-race anchor; S5's anchor is the `StagePoolSnapshot` row (+ allocation rows). Allocation (management, pre-production) and settlement (later) rarely interleave, but when they do they obey the single order.
**Consequences.** Allocations on one stage serialize on its snapshot row — acceptable (one shared pool is inherently serial; allocation is low-frequency vs reporting).
**Migration/Rollback.** Doc + code-discipline only; no schema. Rollback = revert the draw-down lock (flag-gated S5).
**Verify.** Mirrors the existing deadlock-safe ordered-lock discipline (`adda_settlement_service.py:22`).

## MUST-4 — Cutting-reopen ↔ pool contract + save_draft interaction
**Problem.** Cutting reopen CASCADE-deletes the pool origin under live downstream allocations; `save_draft_contributions` delete+recreates lines (would destroy allocation draw-down + alter/missing).

**Decision (reopen): REFUSE upstream reopen when any downstream consumer exists** — a `WorkerStageAllocation`, a good/alter/missing contribution, or (future) an `AlterCase` on a later stage of the Adda. Mirrors the existing settlement-reopen armor + the "reverse, don't edit" discipline: to fix Cutting, reverse downstream first (explicit, audited). *Reject "version the breakdown"* — version-awareness would leak into the pool fn, allocation, and every snapshot read.

**Decision (save_draft): the allocation bound + good/alter/missing crystallize at COMPLETE, not at draft.** Drafts stay replaceable scratch (no money, no pool draw-down) — `save_draft_contributions` is unchanged. `complete_worker_task` is the single crystallization point: enforce `good+alter+missing ≤ allocation`, freeze the observations, draw down the pool (under the M-2/M-3 lock). Add a *soft* warning at draft-save (over-allocation hint) but the *hard* gate is at complete. This is pure Option-B (truth begins at complete).

**Consequences.** Reopen after downstream work is a deliberate, audited multi-step reversal (correct cost of changing the source). Draft UX: a worker can over-draft, then complete rejects — soft-warn at draft mitigates surprise.
**Migration/Rollback.** No schema (a reopen guard + a complete-time check). Rollback = drop the guard.
**Verify.** Option-B ✓; reuses settlement-reopen-armor; auditability ✓ (no orphaned snapshots).

## MUST-5 — AddaStageRoleRate = resolved-rate + role snapshot + lock
**Problem.** Duplicates `WorkflowStageRoleRate`; a raw `ws.cost_rate` copy drops the grouped-member→₹0 rule; rate read against the live mutable `User.role`; first-completion lock races + can freeze a typo.

**Decision.**
- **Store the RESOLVED payable rate**, not a raw copy: at Adda-start, for each `(stage_record, role)`, freeze `role_rate_for(ws, role)`'s output (grouped-member `cost_billed_at`→0 · role override · else `ws.cost_rate`). This makes `AddaStageRoleRate` semantically distinct from `WorkflowStageRoleRate` (template *input* override) — it is the frozen resolved *output*. Document the relationship in both models.
- **Snapshot the worker's role** onto the contribution (new `role_snapshot` FK) at report/complete; the rate resolver reads the snapshot, never live `User.role`. (Primary-role resolution, matching `role_rate_for` today.)
- **Lock the `AddaStageRoleRate` row** inside `complete_worker_task` (extend the P0-5 lock) before reading/freezing; lock predicate = "rate locks once ANY contribution on that (stage_record,role) completes."
- **Typo safety:** the copied resolved rate IS the correct workflow default, so the common path is safe with no gate. Adda-start edits are the exception; post-lock corrections go through the **audited re-rate recompute, which REFUSES any contribution with an active `settlement_line`** (reverse the settlement first — resolves challenge #14). No mandatory confirm-gate (avoids friction); the resolved-copy default is correct-by-construction.

**Consequences.** A-5 (unpriced→₹0) is also closed — rates always exist (copied). Two role-rate tables, but now clearly *template* vs *frozen-resolved*.
**Migration.** New `AddaStageRoleRate` + `WorkerStageContribution.role_snapshot` (additive). Backfill: historical contributions' `expected_rate` already carries the frozen value → derive snapshot rows; role_snapshot ← the worker's role at the time where known, else current (flag ambiguous in-progress Addas — RC-4). Forward-only.
**Future-domain.** Per-team rate divergence (multi-team) would extend the grain to `(stage_record, role, team)` later — additive.
**Rollback.** Drop the tables/field; `complete_worker_task` falls back to live `role_rate_for` (today's behavior).

## MUST-6 — B-1 reconciliation backstop INTO the foundation
**Problem.** Allocation-bounding stops *downstream* over-report, but Cutting's own over-count (records 120 when 105 cut) is the pool origin and is never reconciled; the backstop was deferred to P3 — so the headline leak stays open through staging + S1–S6.

**Decision.** Add a **finalize-time reconciliation gate** (in the S5 settlement work, not P3): for each settled stage, compare Σ(settled good qty) against the stage's independently-recorded physical output — `AddaStageRecord.cost_quantity_snapshot` (= the handler quantity: `CuttingRecord.pieces_cut`, lay count, etc.). If Σ settled > output beyond a configurable tolerance → **block finalize** with the exact numbers, allowing a **management override that records a reason** (audited). This is the cheap backstop [ARCH_EVAL Part 2](audit_phases/ARCH_EVAL_source_prevention_rates_variance.md) already proposed.
- This closes B-1 *fully*: downstream over-report via the allocation bound; **Cutting-source over-report via this gate** (pieces_cut is recorded from breakup/bundle counts, independent of worker reports).

**Consequences.** Complements (doesn't double-count) the allocation bound. Tolerance + override handle legitimate re-cut timing (re-cut raises pieces_cut; if not yet recorded, the override covers it).
**Migration/Rollback.** No schema (a finalize check + an override-reason field on the settlement, additive). Rollback = drop the gate.
**Verify.** ADR-0009 ✓ (reads `cost_quantity_snapshot`, the standard-cost quantity — comparison, never addition); settlement-first ✓; auditability ✓ (override logged).

## MUST-7 — Rework/Missing settlement + pool-credit contract
**Problem.** Recovered-alter / reappeared-missing feed only the downstream pool, never *pay* the worker; the "future-shaped, no-redesign" pool term is unfounded; count-based alter has no piece identity.

**Decision (contract now; build later).**
- **alter_quantity / missing_quantity are immutable count observations** at the stage's grain. Documented soundness limit: count-based netting is valid **only same-stage, same-grain, same-Adda**.
- **Recovered-alter pays as NEW work:** the future Rework domain creates a *new* rework task → contribution → its own settlement on the rework worker. **Never edits the frozen original settlement.** Rework pay = the normal new-work pay path (reuses everything). The original worker is correctly *not* paid for the defect; the rework worker is paid for the fix.
- **Pool credit via a stable accessor:** the pool fn reads `recovered_alter(stage_record, dims) → Decimal` and `found_missing(stage_record, dims) → Decimal`, both returning **0 until the domains ship**. `available = snapshot.good + recovered − allocated` (M-2). **Define these accessor signatures now** — that is the concrete "future-shaped" guarantee (an interface S4 commits to, not faith). Recovered credits the **stage where the alter was observed** (rework restores that stage's good → its downstream pool grows); recovered pieces arriving late = a pool top-up → a new downstream allocation.
- **Reappeared-missing:** a "found" event is a new append-only record the `found_missing` accessor reads; `missing_quantity` (the original observation) stays immutable.
- **Out of scope (documented limit):** cross-Adda / cross-stage batched rework requires **piece identity** (ADR-0010 D3, future Barcode module) — the count-based foundation explicitly does not handle it.

**Consequences.** S4's pool fn ships calling stable accessors (return 0) → Rework/Missing plug in with no pool-formula change. Auditability ✓ (append-only). Option-B ✓ (rework = new contributions).
**Migration/Rollback.** No schema now (accessor interface + doc). When Rework ships: additive records. Rollback: accessors return 0 = today.

---

## Constraint verification matrix
| MUST | settlement-first | ADR-0009 | Option-B | AddaStageRoleRate rm | WorkerStageAllocation rm | Missing | Alter/Rework | Auditability | Forward-only |
|------|---|---|---|---|---|---|---|---|---|
| 1 grain | ✓ | ✓ | ✓ | — | ✓ refined | ✓ | ✓ | ✓ snapshot grain | ✓ |
| 2 pool snapshot | ✓ | ✓ separate | ✓ | — | ✓ | seam | seam | ✓ frozen | ✓ |
| 3 lock order | ✓ | — | — | — | ✓ | — | — | — | n/a |
| 4 reopen/draft | ✓ | ✓ | ✓ truth@complete | — | ✓ | ✓ | ✓ (AlterCase guard) | ✓ no orphans | ✓ |
| 5 rate | ✓ reads frozen | ✓ payable≠cost | ✓ | ✓ resolved | — | — | — | ✓ snapshot | ✓ |
| 6 recon gate | ✓ @finalize | ✓ uses cost_qty | ✓ | — | complements | — | — | ✓ override logged | ✓ |
| 7 rework contract | ✓ new settlement | ✓ | ✓ new contributions | — | ✓ accessor | ✓ accessor | ✓ accessor | ✓ append-only | ✓ |

---

## B. Addendum Challenge Review (second-pass hostile — breaking my own fixes)
- **M-1 grain → "what if a downstream stage needs FINER grain than upstream?"** Garment flows only coarsen (Cutting finest). **Codified as an invariant** (grain monotonically non-finer downstream); a flow editor that violates it is a config error to validate. Holds.
- **M-2 snapshot → "you re-introduced the stored counter you feared."** No — it's **write-once-at-completion + immutable**; allocations are the only moving part. Drift is impossible because the snapshot never mutates. Reopen→refreeze is gated by M-4 (no downstream). Holds.
- **M-2/M-7 → "recovered pieces make the pool time-varying vs an immutable snapshot."** Resolved by formula: `available = snapshot + Σ recovered_credits − Σ allocated`; recovered is an append-only credit ledger, not a snapshot mutation. Coherent.
- **M-3 → "more locks = more contention."** Allocation is low-frequency (management pre-assign) vs reporting; per-stage serialization on the snapshot row is inherent to a shared pool. Acceptable.
- **M-4 reopen-refuse → "too rigid for a legit cutting fix."** That's the correct, audited cost of changing the source after work flowed (reverse-downstream-first) — identical to settlement armor. Accepted.
- **M-4 draft → "worker over-drafts 999, complete rejects, confusing."** Soft-warn at draft + hard-gate at complete. Acceptable; not a data risk (draft = scratch).
- **M-5 → "grouped-0 computed at copy time, but grouping changes mid-Adda?"** The Adda's flow (incl. `cost_billed_at` grouping) is frozen at Adda-start like its rates — no mid-Adda regrouping. Holds. Role snapshot uses primary-role (documented).
- **M-6 recon → "re-cut after an earlier settlement false-blocks."** The logged override covers legit re-cut timing; tolerance configurable. Doesn't double-count the allocation bound (different layer). Holds.
- **M-7 → "rework-as-new-work means the recovered piece's downstream needs a new allocation."** Yes — recovered arrives late → pool top-up → new downstream allocation (normal flow). The accessor + additive credit make this a populate-not-redesign. Cross-Adda explicitly punted to piece-identity. Holds.
- **Residual genuine unknowns (not breakable on paper, only in staging/S4):** allocation-UI friction at coarse grain (M-13 — prototype before S4), recon tolerance value (tune in staging), grain-config UX in the flow editor.

**No second-pass finding overturns a resolution.** Three need a one-line codification (grain monotonicity, draft soft-warn, recon tolerance+override) — folded in above.

## C. Updated confidence score: **8.5 / 10**
The five deep flaws now each have a concrete decision, verified across 9 constraints, and survive a second hostile pass. The unifying `StagePoolSnapshot` (generalizing an existing pattern) collapses four of them into one well-understood mechanism. Remaining 1.5 = the should-fix-during items + genuine implementation/staging unknowns (UI friction, tolerance tuning) that no paper review can close.

## D. GO / NO-GO for S1: **GO**
- **S1 (settlement_quantity resolver + AddaStageRoleRate) is unblocked:** M-5 fully specifies the rate (resolved snapshot + role snapshot + lock), M-6 lands the recon gate in the settlement work, and the resolver gets its named default + alter/missing golden fixture (should-fix). None of the deferred-to-S4 items (grain/pool/lock/reopen) block S1.
- **Binding condition:** this addendum governs S2–S6; the locked docs are read *through* it. **Mandatory checkpoint re-review before S4** (where `StagePoolSnapshot` + grain + the allocation lock are implemented) — confirm the M-1/M-2/M-3/M-4 decisions against the S1–S3 reality + the staging RC-5 evidence (does the floor pre-allocate?).
- Carry the **should-fix-during** items (resolver fixture, rename-not-drop reported_quantity, show-cap-in-Strict, partial/reassign resolution state, allocation-UI prototype, naming) into their sprints.

**Start S1. Re-review this addendum's S4 items before S4.**
