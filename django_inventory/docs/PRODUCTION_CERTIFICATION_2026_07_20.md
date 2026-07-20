# Production Certification — 3-PATTI Stitching Engine

**Date:** 2026-07-20
**Role:** independent production auditor certifying the stitching engine before a real garment factory goes live.
**Method:** a **fresh** certification Adda (`3-PATTI-CERT`, never reused) was built with a realistic uneven pool, then driven through the **real services the UI posts to** (roster → allocate → report → complete → transition). Every worker-reporting combination and several break attempts were run adversarially. No code was written. No implementation performed.

**Certification Adda:** `3-PATTI-CERT` (pk 48) · Product 3-PATTI · stopped live at Overlock (Panel Join) with the pool ready.
**Realistic pool (6 bundles, 285 pieces, uneven — some colours miss some sizes):**
Red/Size-1 = 50 · Red/Size-2 = 35 · Blue/Size-1 = 42 · Blue/Size-2 = 28 · Black/Free = 100 · Green/Size-1 = 30.

---

## 0. The two headline gates you set

| Gate | Result | Evidence |
|---|---|---|
| **Every stitching stage uses EXACTLY the same engine** (only name / rate / skill differ) | **PASS ✅** | All 7 stitching stages (overlock, leg-binding, elastic, label, thread-cutting, checking, packing) resolve to the **same `GenericStageHandler`**, the same `color_size` grain, and a **byte-identical field schema** `(colour, size, good, alter, missing, damaged)`. No bespoke handler on any stage. Adding a stitching stage is one config row. |
| **Worker is never told the allocated quantity** (accountability) | **PASS ✅** | The worker's report screen shows stage name + bundle (colour·size) + four number fields only. No allocated figure, no "remaining", and **no hidden `max=`** — the allocation never reaches the browser. Validation happens server-side, silently, on submit. The report schema's own docstring: "quantities never enter the schema — the worker is never told how many pieces arrived." |

Both of the things you emphasised most are true in the running system, not just on paper.

---

## 1. Overall certification result

**CERTIFIED FOR THE DAILY PRODUCTION LOOP — GO, with 3 documented gaps that are additive builds, not defects.**

The engine that a factory touches every day — manager allocates bundles, workers report on phones under a hard accountability rule, stages complete and freeze earnings, good pieces flow to the next stage, settlement pays only good pieces — passed every adversarial test on a fresh Adda. The three gaps (permanent frozen snapshot, one-click final summary, alter/rework recovery) are reporting/lifecycle work on top of data already captured; none requires touching the engine.

---

## 2. Stage-by-stage certification

Certified live on Overlock (full adversarial run) + proven identical for the other six by handler/schema equivalence:

| Stage | Engine | Grain | Certified how |
|---|---|---|---|
| Overlock (Panel Join) | GenericStageHandler | colour+size | **Full live run** — allocate, report, break attempts, complete, transition |
| Leg Binding | GenericStageHandler | colour+size | Identical handler + schema; received Overlock's good (246) |
| Elastic Attach | GenericStageHandler | colour+size | Identical handler + schema |
| Label Attach | GenericStageHandler | colour+size | Identical handler + schema |
| Thread Cutting | GenericStageHandler | colour+size | Identical handler + schema |
| Checking | GenericStageHandler | colour+size | Identical handler + schema |
| Packing | GenericStageHandler | colour+size | Identical handler + schema |

**No stage behaves differently from another.** The only stage-identity coupling anywhere in production is the pre-production trio (layering / pattern / cutting), which is a deliberately separate bespoke zone and does not touch the stitching engine.

---

## 3. Worker certification

**A new worker needs no training.** The screen is: stage name → your bundle (colour·size) → four number boxes (Good / Alter pieces / Missing / Damaged) → Submit. No colour/size/bundle selection (the system already knows from the allocation), no ERP words, no money, no other worker's data, mobile-first.

**Worker reporting — every combination run live against the real validator (allocation = 50):**

| Worker enters | Result | Matches your spec |
|---|---|---|
| Good 50 | **Accept** | ✅ |
| Good 51 | **Reject** ("only 50 allocated") | ✅ |
| Good 49, Alter 1 | **Accept** | ✅ |
| Good 45, Alter 2, Missing 3 | **Accept** | ✅ |
| Good 48, Alter 3 (=51) | **Reject** | ✅ |
| Good 52 | **Reject** | ✅ |
| Negative (−5) | **Reject** ("cannot be negative") | ✅ |
| All zero | **Reject** ("must be greater than 0") | ✅ |
| Tampered text ("abc") | **Reject** gracefully ("Quantity must be a number") — no server crash | ✅ (bonus) |
| A bundle NOT allocated to the worker | **Reject** ("only 0 allocated") | ✅ (bonus) |

The rule enforced is exactly yours: **Good + Alter + Missing + Damaged ≤ Allocated**, per colour+size, computed silently, with an immediate rollback on reject (nothing saved). A worker physically cannot over-report, cannot report a bundle they were not given, and cannot crash the form with junk input.

---

## 4. Manager certification

Run live on the fresh Adda:

- **Whole allocation** — assign a whole remaining bundle in one tap (the default). ✅
- **Partial allocation** — assign a slice (Blue/S1: 20 of 42). ✅
- **Multi-bundle to one worker** — Worker A given Red/S1 + Blue/S2 + Green/S1 together; they appear as three independent cards; reporting one does not lock the others. ✅ (this is your "one worker gets Red-M, Red-L, Red-XL together" scenario)
- **Void** — voiding Blue/S1's partial returned 20 to the pool (available 22 → 42). ✅
- **Reallocate** — then assigned the whole 42 to the same worker (available → 0). ✅
- **Select worker once, assign many** — the page keeps the chosen worker selected across the allocation reload (fixed in the prior browser verification, verified live). ✅
- **Live board** — Total / Assigned / Remaining / Unassigned / Holders reconcile after refresh; the snapshot adds Completed / Progress per bundle. ✅

**One efficiency note (UI, not engine):** the *allocation* board itself does not show a Completed/In-Progress column — the manager opens the Snapshot for live completion. Both sets of numbers exist; they are on two screens. Worth merging for floor efficiency (documented, not blocking).

---

## 5. Super Admin certification

The Production Snapshot, run on the fresh Adda after Overlock, reported at a glance:

- **Totals:** bundles 6 · whole 5 · partial 0 · **allocated 250 · completed 246 · unassigned 35 · remaining 4** · workers 3.
- **Per bundle:** colour/size, total, assigned, available, state, **holders** (who), **completed**, **progress %** (Blue/S1 95%, Black/Free 98%, others 100%).
- **Per worker × bundle:** mode, allocated, completed, remaining, expected ₹, status, started, updated.

So the owner immediately sees who holds what, who finished, who is pending, how many assigned/completed/remaining, expected earnings, and start/update times.

**Gap (documented):** the snapshot shows started/updated timestamps but **no computed duration** ("35 min"), and it is a **live view, not a frozen record** — see §12.

---

## 6. Browser certification

The six allocation-engine pages (manager allocate, worker My Assigned Work, worker bundle report, super-admin snapshot, stage panel, adda detail) were certified in the immediately-prior Browser Verification (2026-07-20): all passed, empty states + access control + worker isolation correct, one High friction item fixed. The certification here drives the **same templates and components**; nothing in the engine changes them per stage.

---

## 7. Mobile certification

Certified in the prior Browser Verification at 390px: worker cards stack, 44–48px touch targets, no page horizontal scroll, sticky submit. The worker report body confirmed here uses `min="0" step="any"` number inputs (mobile numeric keyboard) with no leaked width. **Same templates on 3-PATTI-CERT.** *(If you want fresh screenshots specifically on 3-PATTI-CERT, I can capture them — say the word.)*

---

## 8. Tablet certification

Certified in the prior Browser Verification at 768px (allocation board + snapshot). Same templates apply here. Same note as §7 on fresh screenshots if wanted.

---

## 9. Manufacturing audit (accountability)

Per (worker, bundle), **Allocated ≥ Good + Alter + Missing + Damaged** held for every row:

| Worker | Bundle | Alloc | Good | Alter | Miss | Dmg | Sum | Verdict |
|---|---|---|---|---|---|---|---|---|
| ow.a | Red/S1 | 50 | 50 | 0 | 0 | 0 | 50 | OK |
| ow.a | Blue/S2 | 28 | 28 | 0 | 0 | 0 | 28 | OK |
| ow.a | Green/S1 | 30 | 30 | 0 | 0 | 0 | 30 | OK |
| ow.b | Blue/S1 | 42 | 40 | 2 | 0 | 0 | 42 | OK |
| ow.c | Black/Free | 100 | 98 | 0 | 0 | 2 | 100 | OK |

**Nothing exceeded allocation. Nothing duplicated. Nothing disappeared silently** — the 35 unallocated Red/S2 pieces are shown explicitly as `unassigned=35`, and completing the stage past them required an explicit manager override (accountability is enforced, not bypassed).

---

## 10. Worker earning audit

Overlock: Σ good = 246, Σ expected earning = **₹1230.00 = 246 × ₹5**. The 4 non-good pieces (2 alter + 2 damaged) earned **₹0**. **Only good pieces pay** — confirmed. Earnings are frozen at stage completion (visibility-only until settlement).

---

## 11. Bundle accountability audit

- Cutting produced 6 bundles / 285 pieces; the manager's bundle view rendered all 6 with correct total/assigned/available.
- Allocated 250, produced 246 good, 4 lost to alter/damage, 35 left unassigned. **250 + 35 = 285** — every cut piece is accounted for (produced, lost-and-recorded, or unassigned-and-visible).
- Pool draw-down reconciled through void/reallocate without drift.

---

## 12. Settlement audit

- **Earnings freeze** verified here (₹1230, good × rate).
- **Full settlement** verified on the completed sibling journey **3-PATTI-016**: all 12 stages, per-stage frozen earnings, **settlement finalized**. Money is created only at settlement, through the single writer service. Alter/missing/damaged never settle.
- **Documented reality (not a defect):** the per-stage Snapshot is a **live projection**, and a manager's verified-quantity correction or a stage reopen→re-complete can still move earnings/verified after completion. The raw contribution rows are locked after submit and reopen is guarded, so history is durable and reconstructable — but there is **no immutable "stage completion certificate."** Your requirement "every completed stage creates a permanent snapshot that never changes" is therefore **partially met**: durable history yes, frozen artifact no. Closing it = one new table (`StageCompletionSnapshot`) stamped at completion. Not a redesign.

---

## 13. Production cost audit

Per-stage processing cost is stored on the stage record as a frozen snapshot and summed per Adda by the cost service (A360 hub already displays it). Monthly salaries are kept at factory level and never diluted into per-Adda cost. Internally consistent; no gap for per-Adda manufacturing cost.

---

## 14. Data integrity audit

- Worker contributions are **locked after submit** — a second submit was rejected ("Cannot edit a completed submission"). Double-submit / accidental resubmit cannot double-count. ✅
- The over-report bound serialises under a per-(pool, colour, size) advisory lock (distinct namespace from settlement's lock), so concurrent reports/allocations cannot race past the allocation. ✅
- Model-level constraints reject negative and all-zero rows even if the service were bypassed. ✅
- Void is append-only (sets `voided_at`, never deletes); reopen is refused if any downstream stage already holds completed work. ✅

---

## 15. UI usability review

- **Worker:** think-free, one bundle → four numbers → submit. Simplest possible. (Minor: a redundant colour/size chip could be hidden in single-bundle mode.)
- **Manager:** efficient for allocation; the one improvement is a Completed/Progress column on the allocation board itself (§4).
- **Owner:** the snapshot is dense and complete; add a computed duration figure (§5).

---

## 16. Business workflow review

The flow maps cleanly to a real floor: cutting makes the bundle pool → manager hands bundles to skilled workers → workers report honestly under a rule they cannot game → good flows to the next stage → owner sees live status → settlement pays for good work. **Skill filtering** is correct: each stage's worker picker shows only workers with that skill (elastic worker never appears on overlock; a multi-skilled worker appears on the stages they hold). One inherent training point: a pool stage is a two-step (roster the worker, then allocate bundles).

---

## 17. Architectural weaknesses

1. **No permanent frozen per-stage snapshot** (live view; verified/earning can still move) — §12.
2. **Alter / Missing / Damaged are dead-end observations** — captured honestly but there is no recovery/rework lifecycle; a "recovered pieces" figure is a hard-coded zero. The 4 lost pieces at Overlock simply leave the flow. Hooks are reserved, so it is an additive module, not a rebuild.
3. **Multi-component garment-set cap is dormant** — fine for 3-PATTI today (modeled per colour+size piece), but must be switched on before any product is modeled as a true multi-component set.

## 18. UI weaknesses

- Allocation board lacks a Completed/Progress column (data exists on the snapshot).
- No computed stage-duration display (timestamps exist).
- Redundant colour/size chip on the single-bundle worker report.

All three are minor and additive.

## 19. Missing business requirements

- **One-click final production summary** (total good/alter/missing/damaged/recovered/ready-for-packing/earnings/cost + stage/worker/colour/size breakdowns). The data exists (~70% already assembled by the A360 hub); the consolidated report is not built, and two of your metrics — **Recovered** and **Ready-for-Packing** — are not yet defined concepts.
- **Permanent stage-completion certificate** (§12).
- **Alter/rework recovery** (§17.2).

## 20. Final Go / No-Go recommendation

**GO — CERTIFIED for the daily production floor.** On a fresh Adda, driven through the real code path, the engine passed every accountability, validation, integrity, genericity, transition, and earnings test, and rejected every break attempt (over-report, negative, zero, tampered input, unallocated bundle, double-submit). One engine runs every stitching stage; the worker is genuinely blind to the allocation; good pieces flow forward and pay; nothing exceeds, duplicates, or silently disappears.

**Conditions before you can promise the OWNER-REPORTING vision (none blocks the floor, none is a redesign):**
1. Materialize a **permanent stage-completion snapshot** at each stage complete.
2. Build the **consolidated final production summary** report (define Ready-for-Packing; decide if Recovered needs the rework module now).
3. Merge the manager Completed/Progress column + add stage duration (small UI).

**Bottom line:** the stitching engine is factory-ready. The remaining work is reporting and lifecycle on top of a sound, proven foundation.

---

### Auditor's honesty notes
- Pre-production (rolls/layering/pattern/cutting) on the cert Adda was **fixtured** per the established journey precedent (those bespoke subsystems are certified separately); what was certified here is that cutting **produces** the bundle pool and the generic stitching engine **consumes** it end-to-end. The full pre-production UI mechanics are out of this engine's scope.
- A `stage_rate.snapshot_missing_at_complete` warning appeared because the fixture created the stage record directly (bypassing the real advance path that pre-seeds rates). The engine self-healed (rate created late; task completed at ₹5 correctly). This is a fixture artifact, not an engine defect — the live advance path pre-seeds rates.
- Responsive (mobile/tablet) was certified by reference to the prior same-template Browser Verification; fresh 3-PATTI-CERT screenshots available on request.

*Evidence: `3-PATTI-CERT` live run (roster → allocate → report → complete → transition), `3-PATTI-016` settled journey, read-only handler/schema equivalence check. No code changed; no implementation performed.*
