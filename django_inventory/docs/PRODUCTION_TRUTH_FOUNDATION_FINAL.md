---
id: docs-production-truth-foundation-final
type: topic-canonical
status: active
owner: handwritten
scope: project
anchors: —
verified: 2026-07-18
---

# Production-Truth Foundation — FINAL Factory-Floor Review & Lock Decisions

Companion to [PRODUCTION_TRUTH_FOUNDATION_REVIEW.md](PRODUCTION_TRUTH_FOUNDATION_REVIEW.md). Resolves the 4 factory-floor questions and states the lockable design. **No implementation.**

**One governing principle that resolves all four:** the **worker bound is HARD** (a worker can never report beyond their allocation/pool); **all flexibility lives at the ALLOCATION + SOURCE layer** (manager actions, audited). This keeps production "correct by construction" *and* keeps the floor unblocked — the two are not in tension once flexibility is moved off the worker and onto the manager/source.

---

## 1. Manager override scenarios

There is **no "let the worker exceed" override** — you cannot create pieces from nothing. Every real-world case resolves to a *manager/source action*, not a worker-bound bypass:

| Scenario | Correct mechanism | Audited how |
|----------|-------------------|-------------|
| **Re-cut** (extra/replacement pieces actually cut) | A new **cutting production entry** (additive) → raises the cutting good total for that (color,size) → the derived pool grows. Not an override — it's real new production. | Cutting contribution row carries who/when; a `reason='re-cut'` tag + note. |
| **Additional work after initial allocation** | **Top-up the allocation** (increase `allocated_quantity` or add a row) — instant if pool has remaining. | Allocation-history row (old→new, by, when). |
| **Reassign** (worker drops, another takes over) | **Move allocation** from worker A to B for the un-reported remainder. | Allocation-history (move event). |
| **Emergency: worker physically did more than allocated** | Resolve at the allocation layer: either (a) it was someone else's slice → reassign that slice to them, or (b) the pool itself is wrong → a **source recount/re-cut** correction. Never a worker over-report. | Allocation move OR audited source-correction. |
| **Reduce an allocation** | Allowed only **down to what the worker already reported** (good+alter+missing); cannot strand reported work. | Allocation-history; blocked below reported. |

**Audit model:** reuse the existing **single-writer history pattern** (CLAUDE.md rule 5 — `history_service` owns `*History` tables, append-only). Add a `WorkerStageAllocationHistory` (or route through `history_service`): every allocation create/move/top-up/reduce and every re-cut/recount writes an append-only row with `actor, timestamp, old→new, reason`. Re-cut/recount require a **reason** (management-only). No edits, no deletes — same discipline as the ledger.

**Net:** the only way "more" enters the system is **audited real production at the source**; the only way a worker's ceiling changes is an **audited allocation action**. The worker bound never bends.

---

## 2. Future Alter/Rework interactions

**Decision: downstream pool = Good + Recovered-Alter (recovered arrives asynchronously). NOT Good-only, and NOT Good+raw-Alter.**

Physical reasoning: an Alter piece is defective-but-fixable. While pending rework it must NOT flow downstream (it isn't good yet). If rework **recovers** it → it becomes good and **should** flow. If rework **scraps** it → it becomes Missing (write-off). So a raw alter is a *pending* state, not available stock.

**Architecture that supports this without redesign — make the pool formula future-shaped NOW:**

```
pool(stage N, color, size) =
      Σ upstream Good
    + Σ upstream Recovered-Alter      ← term exists now, = 0 until Rework domain ships
    − Σ already-allocated downstream
```

- `alter_quantity` on the contribution is the **immutable observation** ("1 piece needed rework here") — never mutated.
- Rework resolution is a **future additive domain**: a `ReworkRecord` (or similar) references the alter source and records `recovered` / `scrapped`. It **adds rows**; it never edits the contribution.
- The pool-derivation function includes the `+ Recovered-Alter` term from day one (returning 0 today). When the Rework domain ships, it just **populates** that term — **no change to the pool formula, no migration of existing data, no redesign.** That is the "without redesign" guarantee.

**Owner answer:** Good + Recovered-Alter, where recovered pieces re-enter the *same* (color,size) pool as their rework completes; unrecoverable alters convert to Missing. Build the formula with the Recovered term now; leave it zero until Alter/Rework is built.

(Edge — double-count: a recovered piece must net against its original alter, not add a brand-new piece. The `ReworkRecord→alter source` link enforces identity.)

---

## 3. Allocation flexibility — where controlled override points live

**Goal: strong control without blocking the floor.** Achieved by a **per-stage allocation MODE** (a setting, not a hard global rule), so rigidity is applied where it pays and relaxed where it would slow the floor:

| Mode | Worker bound | Use where |
|------|--------------|-----------|
| **Strict** (per-worker allocation required) | `report ≤ this worker's allocation` | High-value / high-fraud-risk stages (e.g. cutting hand-off, finishing) |
| **Open / pool-bound** (no per-worker allocation needed) | `report ≤ remaining stage pool` (first-come) | Fast stages where pre-allocation slows the floor |

**Why this never blocks the floor:** even with zero per-worker allocations, the **pool itself is the ceiling** — workers collectively can't exceed physical upstream output, but any worker can start reporting immediately. The manager opts into Strict only where the control is worth the setup.

**Controlled override/flex points (all audited, management-only):**
1. Top-up allocation (within pool) — instant.
2. Reassign / move allocation (un-reported remainder) — audited.
3. Reduce allocation (≥ already-reported) — audited.
4. Switch a stage Strict↔Open — audited setting change.
5. Source correction (re-cut/recount) — the **only** way to raise the pool — audited with reason.

This dovetails with **TM-1**: the per-stage Tracking Mode (Manual/Barcode/Both/None) and the per-stage Allocation Mode (Strict/Open) are the same kind of per-stage policy knob — design them as sibling stage settings.

---

## 4. Adda-level rate snapshot — safest lock boundary

**Recommendation: rate is editable per `(AddaStageRecord, role)` from Adda-start until that stage's FIRST task COMPLETION; immutable thereafter.** Not first-report, not first-settlement-draft.

Reasoning against each candidate:
- **First report (draft):** too early/rigid. Drafting shows no money (Option B), so editing the rate while workers merely have drafts open harms no one — locking here removes a safe edit window for no benefit.
- **First completion ✅ (recommended):** completion is exactly when `expected_earning` is frozen *and* the worker can see the number in My Earnings. The moment one worker has "done and seen" pay at a rate, changing it would (a) break trust and (b) require recomputing already-frozen earnings. Lock precisely here.
- **First settlement draft:** too late. By draft, many workers have completed and seen earnings at that rate; editing then silently rewrites numbers people already saw.

**Why per-(stage,role), not Adda-wide:** stages complete at different times. Locking cutting's rate when cutting's first task completes still lets the owner fix a downstream stage's rate (stitching not started) — flexibility without breaking any shown number. An Adda-wide lock would freeze downstream rates prematurely.

**Lifecycle:**
1. **Adda start** → copy each workflow stage rate into `AddaStageRoleRate` (so unpriced-silent-₹0 from A-5 is impossible — rates always exist), shown for optional owner review/edit.
2. **Editable window** → until that stage's first task completion (management-only; audited).
3. **Locked** → on first completion. `complete_worker_task` and settlement read the locked Adda rate, never the live workflow.
4. **Post-lock correction (rare)** → no silent edit; a management-only **re-rate event** that recomputes affected frozen `expected_earning`s and is audited — same "reverse, don't edit" discipline as settlement.

This gives the owner a real review window, eliminates mid-Adda drift, makes unpriced stages impossible, and never silently changes a number a worker already saw.

---

## FINAL architecture recommendation (lockable)

The foundation in the companion doc stands, refined by the four decisions above:

1. **`AddaStageRoleRate`** — copied at Adda-start; editable per-(stage,role) **until first completion**; locked after; re-rate is an audited recompute event.
2. **`WorkerStageAllocation`** — quantity-bearing sibling of the task; per (stage_record, worker, color, size); supports **Strict** (per-worker) and **Open** (pool-bound) modes per stage so the floor is never blocked.
3. **`WorkerStageContribution`** extended with `alter_quantity` + `missing_quantity` (immutable observations); `reported_quantity` = Good.
4. **Pool-derivation formula written future-shaped now:** `Good + Recovered-Alter − allocated`, Recovered = 0 until Rework ships.
5. **Worker bound is hard; flexibility is manager/source-side and audited** via the single-writer history pattern.
6. **Settlement-quantity resolver** keeps settlement policy-flexible (stage-good / verified / packed / hybrid) — chosen later, not now.
7. **All additive; forward-only enforcement; backfill known facts only.**

**Build order (inside the foundation):** `AddaStageRoleRate` (independent, ship first) → `WorkerStageAllocation` + modes → allocation-bounded reporting → Good/Alter/Missing → settlement resolver → (later) Rework populates the Recovered term.

**Build before TM-1: YES.** **Phase C: proceed now with the worker-report + assignment screens carved out** (they're redesigned by this foundation).

**Status: ready to LOCK.** On your confirmation I'll record it as the agreed direction and resume **Phase C (with carve-out)**.
