# Foundation Design Challenge — hostile pre-S1 review (2026-06-14)

Strongest-possible criticism of the LOCKED Production-Truth Foundation before Sprint S1. Six independent hostile lenses (architect/maintainer · concurrency · floor · money · scale · rework/missing) produced **63 findings (7 Critical, 22 High, 32 Medium, 2 Low)**; deduped + ranked below. Challenges the *design*, not completed P0/P1. (The lens fan-out ran as a workflow; this synthesis is hand-written — the auto-synthesis hit the session cap.)

---

## A. Foundation Challenge Report

The design **survives at the principle level** — the three-way separation (production-truth / expected-earnings / settlement), allocation-bounded reporting, Adda-frozen rates, and the additive/forward-only migration posture are all sound and worth building. **But hostile review found five deep execution flaws that the locked docs gloss, three of which are pre-S1 blockers.**

The **deepest** is a grain mismatch: the whole allocation/pool model assumes a per-`(color, size)` quantity at *every* stage, but **only the Cutting stage records color/size** — `base/handler.py` ships a single quantity field; `cutting/handler.py` is the *only* schema that adds color+size, and `WorkerStageContribution.color/size` are nullable. The one per-`(color,size)` source that exists, `AddaProductSizeColorPieceBreakdown`, is **consumed by zero services today** (a dead snapshot). So "pool(stage N, color, size) = stage N−1's good output by (color,size)" is **uncomputable for Stitching/Finishing/Packing** — the model's central join has no data. This isn't fatal to the idea, but it forces a pre-S1 grain decision (per-stage-variable grain) or it will surface as a rewrite mid-S4.

The other four deep concerns: (2) **the allocation→pool race has no lock anchor** — the locked claim that "deferring Open mode makes Strict race-safe" only protects the report→allocation row check, *not* the allocation→pool ceiling, so two managers can over-allocate a pool the design calls bounded; (3) **the original B-1 leak survives the entire foundation** — allocation-bounding stops *downstream* over-report, but Cutting's own over-count (recording 120 when 105 were cut) is the pool *origin* and is never reconciled, and the settlement backstop is deferred to P3; (4) **`AddaStageRoleRate` duplicates the existing `WorkflowStageRoleRate`** and naively copies `ws.cost_rate`, dropping the grouped-member→₹0 rule that `complete_worker_task` computes today; (5) **rework/missing have no settlement re-entry path** — a repaired Alter or a reappeared Missing piece feeds only the downstream *pool*, never *pays* the worker who produces the good piece, and the "future-shaped, no-redesign" pool term is unfounded without piece identity.

**Verdict: PROCEED-WITH-CHANGES — do NOT start S1 until the §F MUST-fix items are resolved on paper.** The grain decision (F-1) is the one that could escalate to "re-shape the allocation model" if downstream stages genuinely cannot capture color/size; resolve it first. Nothing here invalidates the locked *direction* — it hardens an under-specified design before it calcifies in code.

---

## B. Top 20 architecture risks (ranked: severity × likelihood × blast-radius)

| # | Risk | Sev | Target | Scenario (1-line) | Fix |
|---|------|-----|--------|-------------------|-----|
| 1 | **Color/size grain only exists at Cutting** | Crit | WorkerStageAllocation grain + pool fn | Downstream stages record qty-only (color/size NULL); pool-by-(color,size) is uncomputable | Per-stage-variable grain: cutting=color/size, coarse stages=stage-level qty; nullable dims + pool fn that collapses |
| 2 | **No per-(color,size) pool SOURCE downstream** | Crit | pool(stage N)=stage N−1 good | `AddaProductSizeColorPieceBreakdown` consumed by 0 services; only cutting emits it | Scope Strict to the cutting→first-downstream handoff in Phase 1; define pool when no upstream dim source |
| 3 | **Allocation→pool over-allocation race (no lock anchor)** | Crit | Strict "race-safe" claim | 2 managers each allocate 30 against pool 40 → Σ80>40 | Lock anchor at allocation time: `select_for_update` the upstream SR / breakdown rows (or a thin pool-counter row) |
| 4 | **Cutting reopen DELETES the pool origin** | Crit | reopen teardown vs derived pool | reopen_cutting `_teardown` deletes `AddaProductSizeColorPieceBreakdown` while downstream allocations reference it | Refuse reopen when downstream allocation/contribution/AlterCase exists (PROTECT-style), or version the breakdown |
| 5 | **save_draft replace-semantics destroys allocation + alter/missing** | Crit | S5 bound + immutable observations | `save_draft_contributions` deletes+recreates all lines each save | Define alter/missing immutable only at complete; bound-check tolerant of delete-recreate |
| 6 | **B-1's cutting-side leak survives the whole foundation** | High | S5 as B-1 cure; recon deferred P3 | Cutting records 120 (cut 105) → pool=120 → everything downstream bounded to a wrong ceiling | Pull the settlement-side reconciliation backstop INTO finalize as foundation, not P3 |
| 7 | **AddaStageRoleRate duplicates WorkflowStageRoleRate + drops grouped-₹0 rule** | High | new rate table | Maintainer sees 2 role-rate tables; raw `ws.cost_rate` copy ignores `cost_billed_at`→0 | Snapshot the RESOLVED rate (role_rate_for logic incl. grouped-member 0), not a raw copy |
| 8 | **Allocation lock vs settlement lock = opposite order → deadlock** | High | global lock order | settlement locks SR→WorkerProfile; allocation draw-down locks allocation→SR — circular | Extend the documented global lock order to include WorkerStageAllocation; one order everywhere |
| 9 | **Pool is recursive + non-materialized → degrades + non-auditable** | High | DERIVED pool | deep flow at 100x Addas re-derives the whole upstream chain; pool unreconstructable 6mo on | Materialize per-(stage_record,color,size) good/alter/missing rollup at completion (append-only) |
| 10 | **Role read LIVE at completion → role change mis-pays** | High | (stage_record, role) rate | worker.role changed after lock → rate resolves to wrong/zero | Snapshot role onto contribution at report; resolver reads the snapshot |
| 11 | **settlement_quantity resolver collides with verified_quantity** | High | resolver default `verified ?? good` | verified is a full-replacement scalar; can't coexist with good/alter/missing decomp | Decide: verified survives, or is replaced by management editing good/alter/missing |
| 12 | **Resolver default silently moves money at the good/alter/missing split** | Crit | S1 resolver golden-tested pre-split only | post-S3, `reported`→`good`; same Adda pays differently; ₹225 golden chain has no alter/missing | Name the default `stage_good`; add a golden fixture WITH non-zero alter/missing in S3 |
| 13 | **Strict = O(workers×colors×sizes) manager writes** | High | Strict-only + auto-even-split | 20 cells × 8 workers = up to 160 pre-allocation rows on a phone | Prototype the alloc UI on a real 20-cell Adda; coarser grain or batch-allocate if >few taps |
| 14 | **Re-rate vs reversal have no ordering → re-credit at new rate** | High | first-completion lock + re-rate recompute | settled@R1, reversed (netted R1), re-rated R2, re-finalized@R2 — mismatch | Re-rate REFUSES contributions with an active `settlement_line` (reverse first) |
| 15 | **Dual-write reported=good breaks immutability + no constraint** | High | RC-3 dual-write | manager edits good later → reported (the "immutable claim") drifts; no DB guard | CheckConstraint `reported_quantity=good_quantity` during S3→S5; dual-write only at initial write |
| 16 | **S6 drop unverifiable "zero readers"** | High | S6 reported_quantity DROP | value escapes to AddaHistory JSON, frozen snapshots, `payroll Sum(reported_quantity)` | Rename → `original_reported_quantity`, keep frozen forever; don't DROP |
| 17 | **First-completion rate lock races multi-worker + typo freeze** | High | rate lock predicate | 2 near-simultaneous completes; a fast worker freezes a typo'd rate before owner reviews | `select_for_update` the rate row in complete; require owner-confirm before first-complete can lock |
| 18 | **Nothing is factory-scoped** | Med | multi-factory | adda codes, adda_counter, ws rates, pool all implicitly single-factory | Note as a hard prerequisite for the multi-factory ADR; don't bake single-factory assumptions deeper |
| 19 | **WorkerStageAllocation ≈ expense.StageWorkAssignment (naming/coupling)** | High | new table naming | two near-identical (stage_record,worker,color,size,qty) tables — truth vs money | Deliberate distinct name + cross-doc; never let one read the other |
| 20 | **P0-5 task-lock framed as the S5 pool-race precursor — it isn't** | High | P0-5 comment | it locks the TASK row (worker-vs-stage-complete), not the allocation/pool (worker-vs-worker) | Correct the framing; S5's anchor MUST be the allocation/pool rows |

---

## C. Top 20 edge cases not yet handled

1. **Partial completion** (did 6 of 10, went home) — `complete` freezes 6, no `good+alter+missing==allocation` check; remaining 4 strand the pool. → allocation-resolution state (reassign / mark-missing / leave-open).
2. **Reassign half-done allocation** — A reports 6 then pulled; moving the 4 to B collides with A's terminal COMPLETED + reduce-below-reported. → define reassign against the real lifecycle.
3. **Manager wrong color/size/qty + hidden cap** — worker handed Red/L but allocated Red/M; hidden cap removes the only floor error-correction loop. → in **Strict**, SHOW the allocated work (it's deliberately assigned, not a fraud surface).
4. **Missing pieces reappear** (miscount) — `missing_quantity` immutable, permanently shrinks the pool, no reversal. → reconciliation path.
5. **Alter repaired** — recovered piece feeds the downstream pool but **never pays** the rework worker. → settlement re-entry contract.
6. **Scrapped-alter → Missing conversion** — no model home; risks double-decrementing the pool.
7. **Cross-stage rework** — piece altered at Stitching, recovered → which stage's pool? per-stage ceiling broken.
8. **Cross-Adda batched rework** — AlterCase→pool credit assumes same-Adda; rework is often batched across Addas (no FK path).
9. **Worker reports wrong, realizes after submit** — only fix is a management `verified_quantity`; reported immutable. → self-correct-before-complete window.
10. **Shared physical pile** — Strict slices one pile into per-worker (color,size) cuts that don't exist physically.
11. **Multi-CuttingRecord Adda** — nullable color/size + >1 cutting record breaks the (color,size) pool grain.
12. **Re-cut raises the pool after downstream allocated** — orphaned bounds vs regenerated pool.
13. **Top-up/reduce allocation DURING a finalize** — settlement freezes SR but not allocations/pool → re-arms over-pay.
14. **Grouped/member stage allocation** — member stage freezes ₹0; allocating against it has no defined behavior.
15. **Auto-even-split reintroduces over-pay** — blanket even-split across (color,size) ≠ what the floor did; rubber-stamps the bound.
16. **Reversed-then-superseded settlement re-reads `verified ?? good` LIVE** — a correction between reverse and re-finalize silently changes pay.
17. **Advance recovery vs reversal restore** — `advance_remaining` validated at finalize; reversal restores via PSI `reversed_at`; concurrent re-finalize edge.
18. **Reopen-then-recomplete after rate lock** — no defined rate behavior on recomplete.
19. **Barcode (TM-2) encodes a specific piece** but allocation is a per-(color,size) *count* — scan-driven draw-down vs aggregate mismatch.
20. **Forward-only bimodal pool** — `pieces produced = Σ reported_quantity` over historical Addas violates the ≤pool invariant; any pool-assuming query must special-case pre-foundation Addas.

---

## D. Most likely to FAIL in real production
- **B-1 leak stays live (risk #6)** — the headline bug the foundation is *for* isn't closed until P3; staging + all of S1–S6 run with it open. **Highest-confidence real-money failure.**
- **Grain mismatch (#1/#2)** — the first time someone tries to allocate/bound a Stitching stage, the pool query returns nothing usable. **Will surface in S4.**
- **Allocation→pool over-allocation (#3)** + **deadlock (#8)** — concrete multi-manager / concurrent-settlement interleavings; rare but real, and they corrupt the ceiling or hang.
- **Partial completion / reassign (C-1/C-2)** — happens *every day* on a real floor; currently strands pool + allocation.
- **Manager fat-finger + hidden cap (C-3)** — frequent; the worker has no way to say "this isn't my color/size," so they either can't report or orphan-fail.

## E. Looks-correct-now / debt-later
- **DERIVED pool** — elegant on paper (single source, no drift), but unmaterialized it's a recursive recompute + **non-reconstructable audit** (you can't later prove what ceiling a 6-month-old allocation was bound against). Debt compounds with flow depth + Adda count.
- **`AddaStageRoleRate` as a raw `ws.cost_rate` copy** — fine for flat rates today; silently wrong for grouped/role-variant rates, and a second role-rate table future devs must reconcile.
- **`reported_quantity` retired by DROP** — clean-looking, but the value has already leaked into JSON metadata + frozen snapshots; dropping it destroys the only immutable original-claim baseline. Rename-and-freeze is the honest move.
- **`settlement_quantity` resolver shipped in S1** — 5 sprints before its `good_quantity` source exists, rewritten at S3 + S6: an abstraction maintained across three shapes before it has a second policy. YAGNI debt.
- **Strict-only + auto-even-split** — looks like it "keeps the floor unblocked," but even-split is the exact rubber-stamp that re-opens the over-pay hole the bound exists to close.
- **Single-factory assumptions** — codes/counters/rates/pool — invisible until factory #2, then pervasive.

## F. Recommended changes BEFORE S1 starts

**MUST resolve on paper before S1 (pre-S1 blockers):**
1. **Grain decision (risks #1, #2).** Declare allocation/pool grain **per-stage-variable**: Cutting = `(color,size)`; coarse stages = stage-level quantity (or add explicit color/size capture to downstream handlers). Make `WorkerStageAllocation.color/size` nullable + the pool fn dimension-aware. **This is the gate — everything in S4 depends on it.**
2. **Pool lock anchor + materialization (risks #3, #9).** Define the allocation-time lock anchor (lock upstream SR / breakdown rows, or a thin pool-counter row) AND materialize a per-(stage_record,color,size) good/alter/missing rollup at stage completion (append-only) — both correctness (race) and auditability (reconstruction).
3. **Global lock-order extension (risk #8).** Add `WorkerStageAllocation` to the documented settlement lock order before any draw-down lock is written. Correct the P0-5 precursor framing (#20).
4. **Cutting-reopen vs pool contract (risks #4, #5, edge #12).** Decide: refuse upstream reopen when downstream allocations/contributions/AlterCases exist (PROTECT-style), or version the breakdown. Define save_draft's interaction with allocation bound + immutable alter/missing.
5. **AddaStageRoleRate = RESOLVED-rate snapshot (risk #7), role snapshot (#10), rate-row lock + owner-confirm-before-lock (#17).** Snapshot `role_rate_for`'s output (grouped-member 0 included) + the worker's role; lock the rate row in complete; don't let a fast worker freeze an unreviewed rate.
6. **Pull the B-1 reconciliation backstop into the foundation (risk #6).** At finalize, compare Σ settled vs the stage's recorded output (`cost_quantity_snapshot`/`pieces_cut`) — the cheap assertion ARCH_EVAL already proposed — so the headline leak is closed *with* the foundation, not deferred to P3.
7. **Rework/Missing settlement + pool contract (risks #5, edges 4–8).** Before S4 locks the pool read-shape, write the explicit contract: how a recovered-alter / reappeared-missing piece (a) re-enters which pool and (b) *pays* a worker (a new contribution/allocation line, not a frozen-settlement edit). Don't ship the "future-shaped, no-redesign" pool term on faith — define the interface it must satisfy.

**SHOULD address during the sprints (not blockers):**
- Resolver: name the default `stage_good`; add an alter/missing golden fixture in S3 (#12); decide verified vs good/alter/missing (#11).
- Reported→good: CheckConstraint `reported=good` in the dual-write window (#15); RENAME not DROP at S6 (#16).
- Floor UX: in Strict, show the allocated color/size/qty (edge #3); add an allocation-resolution state for partial/reassign (edges 1–2).
- Strict friction: prototype the allocation UI on a realistic 20-cell × 8-worker Adda before committing to the grain (#13); decide whether auto-even-split is safe (edge #15).
- Naming: `WorkerStageAllocation` distinct from `expense.StageWorkAssignment` (#19).
- Multi-factory scoping noted for its ADR (#18); not built now.

---

## Net
**Proceed to S1 — after resolving the seven §F MUST items on paper.** The locked direction is right; the locked *docs* under-specify the pool grain, the allocation-time concurrency, the rate-snapshot resolution, and the rework/settlement re-entry — exactly the things that calcify badly if discovered mid-implementation. Resolve them as a short pre-S1 design addendum, then build. Re-run a (smaller) verification pass on that addendum before S4 locks the pool.
