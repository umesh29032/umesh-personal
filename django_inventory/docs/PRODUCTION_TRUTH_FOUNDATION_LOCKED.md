---
id: docs-production-truth-foundation-locked
type: topic-canonical
status: active
owner: handwritten
scope: project
anchors: —
verified: 2026-07-18
---

# 🔒 Production-Truth Foundation — LOCKED Architecture Direction

**Status: LOCKED 2026-06-14** (owner-approved). Design & roadmap frozen. **No implementation yet** — this records the agreed direction that governs the build when it starts. Supersedes nothing; it finalizes [REVIEW](PRODUCTION_TRUTH_FOUNDATION_REVIEW.md) + [FINAL](PRODUCTION_TRUTH_FOUNDATION_FINAL.md) + [ROADMAP](PRODUCTION_TRUTH_FOUNDATION_ROADMAP.md) with two final decisions.

---

## The locked model (one line)
A **production-truth quantity layer** — manager allocates `worker × color × size × quantity`; workers self-report **Good / Alter / Missing** bounded by their allocation (cap never shown); rates frozen per-Adda at start and locked at first completion; expected-earnings is pure visibility; settlement is a separate, policy-flexible decision via a quantity resolver. Production data correct **by construction**; settlement never compensates for bad production data.

## Final decisions (this session)

### D1 — Open Mode: **DEFERRED entirely to a future ADR.**
- Phase 1 ships **Strict mode only** (per-worker allocation always required).
- Rationale: factory workflow is allocation-oriented; Strict covers the real need; **deferring Open eliminates the pool-race risk** (the only 🔴 risk) because the worker bound becomes a lockable per-worker allocation row, not a derived aggregate.
- **No `allocation_mode` flag in Phase 1** — added only if/when Open is ever built (additive).
- Guardrail: ship a **low-friction allocation default** (auto-even-split among assigned workers, then adjust) so "allocate before report" never stalls the floor.

### D2 — Naming: **Option B — `good_quantity` is the real field; `reported_quantity` retired.**
- Add `good_quantity` (+ `alter_quantity`, `missing_quantity`); backfill `good_quantity ← reported_quantity` (exact known fact).
- Migrate all read-sites to `good_quantity`.
- **Drop `reported_quantity` as the final step of the foundation** (after S5, tested) — the foundation lands with honest naming and **zero residual naming debt**. Safe because pre-staging (no production consumers, ~4 rows). Immutability rule transfers to `good_quantity`.

---

## Locked entities
| Entity | Status |
|--------|--------|
| `AddaStageRoleRate` | NEW — copied at Adda-start; editable per-(stage,role) until first completion; locked after; rare post-lock = audited re-rate recompute |
| `WorkerStageAllocation` (deliberate name TBD at build; NOT `StageWorkAssignment` which is the money/settlement line) | NEW — `(stage_record, worker, color, size) → allocated_quantity`; **Strict only** |
| `WorkerStageAllocationHistory` | NEW — append-only audit (single-writer pattern, rule 5) |
| `WorkerStageContribution` | EXTEND — `+good_quantity` (replaces reported_quantity), `+alter_quantity`, `+missing_quantity` |
| Pool-derivation fn | DERIVED (no table) — **future-shaped:** `Σ Good + Σ Recovered-Alter(=0 until Rework) − Σ allocated` |
| `settlement_quantity(c, policy)` | NEW resolver — default policy = current behavior; policies (stage-good/verified/packed/hybrid) chosen later |

## Locked invariants
- Worker bound is **HARD**: `good + alter + missing ≤ allocation` (Strict). Cap never sent to client.
- Quantity may **decrease** across stages, never increase (enforced by the pool ceiling).
- All flexibility is **manager/source-side and audited** (top-up, reassign, reduce≥reported, re-cut/recount). No worker-bound bypass.
- Rate read from the Adda snapshot, never the live workflow.
- Production-truth, expected-earnings, settlement stay **three separate concepts**.
- ONE pool-derivation function used everywhere (no re-implementation).

## Frozen build order (S1 → S5)
```
S1  Settlement-quantity resolver refactor (behavior-preserving; golden-test ₹225 chain)
S2  AddaStageRoleRate (rate copy + first-completion lock)
S3  good_quantity + alter_quantity + missing_quantity (+ constraint loosen; backfill good←reported)
S4  WorkerStageAllocation + pool fn (Strict only; low-friction default; no enforcement yet)
S5  Allocation-bounded reporting ENFORCE (feature-flag, forward-only)
FINAL  Drop reported_quantity (after read-sites migrated; tested) — zero naming debt
DEFER  Open mode (ADR) · Rework domain (populates Recovered term) · Missing-Pieces domain · packed-based settlement policy · the policy choice
```

## Locked sequencing decisions
- **Build this foundation BEFORE TM-1** (TM-1 capture must draw down an allocation + carry good/alter/missing).
- **Phase C proceeds now** with the **worker-report screen + stage-assignment screen carved out** (they are the S4/S5 UI and will be redesigned).

## Open items to resolve at build time (not blockers to lock)
- Final name for `WorkerStageAllocation` (avoid confusion with `expense.StageWorkAssignment`).
- Decimal vs integer quantities per stage.
- In-progress-Adda rate backfill review list (flag, don't invent).

## Doc-sync note (deferred to implementation)
When build starts: add a CLAUDE.md pointer to this locked foundation; cross-link from ARCHITECTURE_V2 §11 and REQUIREMENT_REVIEW_STAGE_TRACKING (TM-1 dependency). Not done now (review-only phase).

---
**LOCKED. Roadmap frozen. Proceeding to Phase C with the two screens carved out.**
