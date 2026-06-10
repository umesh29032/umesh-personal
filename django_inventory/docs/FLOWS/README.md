# docs/FLOWS/ — end-to-end flow documentation

One file per cross-cutting flow (spans models + services + views). Each should
cover: trigger, service choke-point(s), state transitions, history/audit rows
written, reopen/undo semantics, and failure modes.

Today the canonical flow docs live in `docs/production/` — index below. Migrate
them into this directory as they're revised; add new flows here directly.

## Existing flows
- **Production stage flow** — `docs/production/STAGE_FLOW.md` (Adda →
  WorkflowStage → AddaStageRecord; advance/reopen; `advance_to_next_stage` choke
  point; cost freeze/clear).
- **Cutting → bundles → barcodes** — `docs/production/BARCODE_GENERATION.md`
  (+ archived `docs/archive/production/CUTTING_DESIGN.md`) (breakup → bundle items → barcode batches; consumed/
  available counters; uniqueness + contiguity).
- **Payroll / earnings ledger** — `docs/production/PAYROLL_ARCHITECTURE.md`
  (allocation → immutable ledger credit; advances as a separate loan pool).
- **Settlement** — `docs/production/SETTLEMENT_ARCHITECTURE.md` (owner starts a
  settlement anytime; cash + per-advance recovery; invariant
  `paid + recovered ≤ payable_before`; reversal = append-only, no edit).
- **Tracking / export** — `docs/tracking/EXPORTS.md`.

## Open flow gaps (backlog)
- `reverse_settlement` (compensating-item reversal) — not yet built; see
  `docs/archive/QA/bugs_found.md` #2.
