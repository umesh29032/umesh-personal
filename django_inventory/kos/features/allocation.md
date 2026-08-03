---
id: feature-allocation
type: feature
verified: 2026-07-27
knowledge_confidence: verified_against_code
answers: "How does the system stop workers being paid for more pieces than a stage ever produced?"
related: [feature-stage-tracking, feature-cutting, concept-two-truths]
---

# Allocation & the Piece Pool — you can't hand out what you don't have

> 📂 [Features](README.md) · [LOS home](../README.md) — *pehle yeh page, phir code.*

## Business Purpose

The audit headline that started it all: **paid for 120, produced 105.**
Nothing in the old flow bounded what workers on a stage could collectively
claim against what the previous stage actually delivered. The piece pool
fixes it at the SOURCE: every downstream stage draws work from a frozen,
counted pool — and the pool refuses over-draw **by construction**, before
any money logic ever runs.

## Mental Model

> **A stage is a warehouse with a counted shelf.** When a stage completes,
> its verified output is frozen onto the shelf (`StagePoolSnapshot`). The
> next stage's manager hands out slices from that shelf
> (`WorkerStageAllocation`) — and the shelf arithmetic (`available =
> pool − Σ active allocations`) refuses a slice bigger than what remains.
> Money never enters the warehouse; this is capacity, not cost.

## 💡 Samjho Aise

Halwai ki mithai ki tray. Pichhle counter ne 105 laddu banaye — tray par
105 ginti ke rakhe. Agla counter बांटte waqt tray se hi de sakta hai;
110 baantne ki koshish = tray khali, haath ruk gaya. Aur tray par bhaav
nahi likha hota — sirf GINTI. Bhaav ka hisaab doosri kitaab mein.

## Technical Deep Dive

**One chokepoint:** `config/production/services/pool_service.py` — sole
writer of `StagePoolSnapshot` (SPS) + `WorkerStageAllocation` (WSA), sole
reader of pool good. **Production-truth ONLY — carries NO money; never
touches costing/earning/rate/settlement** (owner-locked orthogonality).
(Naming trap: `expense.services.allocation_service` is the UNRELATED
legacy era-A earning path.)

**The pool's source, by stage position** (handler-dispatched, no
stage-name conditionals):
- Cutting (the first real quantities): pool good =
  `AddaProductSizeColorPieceBreakdown` — the verified breakdown IS the
  source, never duplicated.
- Downstream stages: pool good = frozen SPS rows, written once at stage
  complete (`materialize_stage_pool`, wired into `advance_to_next_stage`
  since OP-1 — the pool's first live consumer).

**Verified-else-good (owner rule 2026-07-06):** the pool a stage offers =
`Coalesce(verified_quantity, good_quantity)` per contribution — the SAME
resolver rule settlement uses for money, applied independently per concern.
One manager correction in Report Review updates both the next stage's
capacity AND the pay basis, from one truth.

**Grain** — how finely a stage splits work (`WorkflowStage.allocation_dimensions`):
`NONE` (pre-piece stages) → `QUANTITY` → `COLOR_SIZE`; flow-editor sets it
(`set_stage_grain`), and `flow_service` enforces **grain monotonicity**
down the flow. Pool starts at cutting — pre-piece stages have nothing to count.

**Draw-down verbs:**
- `allocate(consuming_sr, worker, qty, color, size)` — management;
  **refuses `qty > available`, always-on** (the one guard that never
  flags off); advisory lock `(5375, objid)` — deliberately DISJOINT from
  settlement's 5374 (capacity and money never queue behind each other).
- `void_allocation(wsa)` — append-only void; **H-2: refuses once the
  worker's submitted production no longer fits the remaining allocation**
  (correct via Report Review first, then void — never strand reported work).
- Worker's report screen scopes its choices to THEIR allocation dims —
  **blind reporting**: labels only, never quantities, so the allocation
  can't anchor what a worker claims.
- **Blind means EVERY worker-facing surface, not just the entry form.** The
  report form was always blind, but the *My Assigned Work* dashboard was
  printing `Allocated` and `Remaining` next to a "report work" button — the
  anchor arrived one click before the input. Since 2026-07-27 the target is
  revealed only **after** that bundle is done, and `Remaining` is floored at 0
  (legacy over-reports used to render as `-4`). Rule: *if a worker can read a
  target before they type their count, the surface is not blind.*

**The complete-time bound** (S4 Phase 4 → hardened AE-1 2026-07-20): `complete_worker_task`
checks `Σ(good+alter+missing+damaged) ≤ Σ active allocated` per reported dim. **AE-1 (owner
bundle model): this is now HARD + ALWAYS-ON — no feature flag, no warning mode** (the FAT
proved the old soft/off default let a worker report 10 against 6 allocated). A reported-but-
unallocated (colour,size) pair → allocated=0 → refused. PRODUCER stages (no upstream pool)
are skipped — they create the pool, they don't consume it. Refusal freezes nothing — strict
but recoverable. Whole-bundle allocation (`allocate_whole`, the default) vs partial
(`allocate(qty=)`, explicit) both draw from the same pool; `bundle_service` projects the
"Red / M / 100" view. Design: [ADD](../../docs/ALLOCATION_ENGINE_REDESIGN_ADD_2026_07_20.md).

**Reopen armor** (S4 Phase 5): reopening a stage while ANY later stage has
non-voided allocations / completed contributions is refused with an
actionable error naming the furthest blocker — reverse-first peel, so the
pool chain never dangles.

## Debugging Guide

| Symptom | Start |
|---|---|
| "Allocation refused" | `available` math: pool good − Σ active WSA on that dim — someone else allocated first |
| "Void refused" | H-2 — worker already reported against it; fix via `set_verified_quantity`, then void |
| "Pool empty on a downstream stage" | Was `materialize_stage_pool` reached (stage advanced through the funnel)? NONE-grain = 0 rows by design |
| "Reopen refused" | Read the error — it names the furthest downstream blocker and the action (void/reverse) |
| Bound refusal at complete | over-report vs allocation — always enforced; `preview_allocation_bound` audits any pre-existing legacy rows |

## Change Impact

`advance_to_next_stage` funnel · generic stage panel ("Split the work" UI)
· worker report schema (dim scoping) · reopen guard `_downstream_consumer_guard`
· flow editor grain select · tests in production app (S4 phase suites) ·
NOT settlement/rates (orthogonal by lock — verify it stays that way).

## AI Implementation Pitfalls

- ❌ Reading pool/allocation data in ANY money computation — WSA ⊥
  costing/earning/rate/settlement is owner-locked and tested.
- ❌ Confusing `pool_service` with expense's `allocation_service` (era-A money path).
- ❌ Duplicating cutting's breakdown into SPS "for consistency" — cutting's
  pool source is APSCPB, single source, BY DESIGN.
- ❌ Showing allocation quantities on ANY worker-facing surface before the work
  is reported — the report form AND the dashboard cards. Blind reporting
  prevents anchored claims; a target one click upstream anchors just as well.
- ❌ Taking 5374 inside pool operations or 5375 inside settlement — disjoint namespaces.
- ✅ Always verify: over-allocation refusal (always-on) + H-2 refusal + reopen
  guard tests green; goldens untouched (no money = no golden drift).

## Interview Notes

*Interview Signal: 🟠 Senior — capacity invariants + lock granularity.*

**Q. "How do you prevent over-claiming against limited capacity in a workflow system?"**
- *Short:* Freeze upstream output into a counted pool; allocate slices; refuse over-draw at write time; bound claims at submission.
- *Senior:* Enforce at the SOURCE (capacity), not the sink (payment audit) — by the time money math notices, the dispute already exists. Keep capacity orthogonal to money so each can be corrected independently; share the correction resolver so one fix propagates. Preview strictness before you enforce it (a `preview` command over historical rows) — strictness you can't preview is an outage.
- *Project example:* SPS/WSA + always-on over-draw refusal + always-on complete bound (previewed on legacy rows, then made unconditional) + H-2 void guard + the 120-vs-105 origin story.
- *Follow-ups:* "Why advisory lock per pool object?" (serialize draw-downs on ONE pool without blocking others — (5375, objid)) · "Why preview a bound before enforcing?" (find pre-existing violations first so hard enforcement doesn't strand in-flight work).

## 🧠 Remember This

Tray par ginti, kitaab mein bhaav — dono kabhi ek jagah nahi. Shelf freeze
hota hai complete par, slice milti hai manager se, aur tray se zyada kabhi
nahi. Worker ko slice ka LABEL dikhta hai, ginti nahi. Capacity ka jhagda
source par khatam karo, payment par nahi.

## 30-Second Revision

- pool_service = sole writer SPS + WSA; NO money, ever (owner-locked ⊥)
- Cutting pool = APSCPB (never duplicated); downstream = frozen SPS
- Offer = Coalesce(verified, good) — same resolver as settlement, per concern
- allocate refuses > available (ALWAYS-ON); void refuses stranding reports (H-2)
- Complete bound: Σ(g+a+m+damaged) ≤ allocated — HARD + always-on (AE-1; flag retired), producers skipped
- Locks: (5375, objid), disjoint from 5374; grain monotonic, starts at cutting
- Blind reporting: labels, never quantities

## DSA & Complexity

The pool is a **bounded counter with an invariant**: `Σ active allocations
≤ frozen pool`, checked under a per-object lock — the same shape as a
semaphore (`acquire` = allocate, `release` = void), enforced in SQL
instead of memory. The advisory key `(5375, objid)` is **lock sharding**:
one lock per pool object, so contention is per-Adda-stage, not global —
compare settlement's single global 5374 (one gate for ALL money) and you
have both ends of the granularity spectrum in one repo. Interview framing:
"pick lock granularity by what the invariant spans — the invariant here is
per-pool, so the lock is per-pool."

## Implementation References

- Canonical: [pool_service chokepoint](../../docs/LEARNING_2_0/CHOKEPOINTS/pool_service.md) (TL;DR + hardening history)
- Design: [docs/S4_PHASE3_RECEIPT_2026_06_14.md](../../docs/S4_PHASE3_RECEIPT_2026_06_14.md) · [S4_PHASE5 (reopen guard)](../../docs/S4_PHASE5_RECEIPT_2026_06_14.md) · runbook [docs/ENFORCEMENT_ROLLOUT_RUNBOOK_2026_06_14.md](../../docs/ENFORCEMENT_ROLLOUT_RUNBOOK_2026_06_14.md)

## Code References
- `config/production/services/pool_service.py` · `flow_service.py` (grain)

## Related Concepts

[stage-tracking](stage-tracking.md) · [cutting](cutting.md) ·
[two-truths](../concepts/architecture/two-truths.md) · [pg/locks](../concepts/postgresql/locks.md)
