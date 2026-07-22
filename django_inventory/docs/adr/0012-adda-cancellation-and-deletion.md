---
id: docs-adr-0012-adda-cancellation-and-deletion
type: adr
status: active
owner: frozen
scope: architecture
anchors: —
verified: 2026-07-22
---

# ADR-0012 — Adda cancellation + super-admin deletion (money-safe)

Status: **ACCEPTED** (owner, 2026-07-22).
Source: owner instruction "if adda is started it can't be deleted, if any user
is earning from it … only super admin can delete that adda." Extends the
FROZEN PDD Adda lifecycle (§3, which listed only `IN_PROGRESS → COMPLETED`) —
recorded here as a PDD amendment (register updated).
Companion locks: ADR-0002 (append-only ledger/history), ADR-0009 (cost truth),
ARCHITECTURE_V2 §11 (settlement = the only money boundary).

## Context

An Adda is the factory's heart. It was already impossible to hard-delete a real
Adda (16 `on_delete=PROTECT` FKs across production/expense/tracking/raw_materials
/machines/patterns_ai, plus every Adda getting a `CuttingStream` + layering
`AddaStageRecord` + `AddaHistory` row at creation). But that protection was
IMPLICIT (relied on child rows), had no business-meaningful message, and the
Django admin exposed a raw delete button that produced a `ProtectedError` 500
(business-acceptance finding **M-5**). There was also NO sanctioned way to
abandon a started batch — `ON_HOLD` / `CANCELLED` were dead enum values.

## Decision

Two explicit lifecycle exits, **super_admin ONLY**, owned by `adda_service`:

1. **`cancel_adda` (SOFT).** status → `CANCELLED`, the row + its `AddaHistory`
   are kept forever (`ADDA_CANCELLED` event). The abandon path for a batch that
   already carries real work. Open (unreported) worker tasks auto-cancel (F3 — no
   pay eligibility); reported/verified work stays immutable. **Refused once a
   settlement exists** (reverse the settlement first) or the batch is completed.
   Touches NO money — settlement remains the only money boundary.

2. **`delete_adda` (HARD, irreversible).** Only for a PRISTINE / mistaken batch.
   `Adda.deletion_block_reason()` refuses the delete when the batch has a
   completed stage, a settlement, a `StageWorkAssignment`, a non-voided
   `WorkerStageAllocation`, a reported-good `WorkerStageContribution`, or a
   generated `BarcodeBatch`. When safe, a leaf-first teardown of the batch's own
   scaffolding runs, then `adda.delete()` — all in ONE transaction. Any leftover
   cross-app PROTECT child (cloth / chosen pattern layout / machine window, which
   this layer must not import — acyclic layers) trips `ProtectedError`, the whole
   transaction rolls back, and the caller is told to Cancel instead. So a delete
   either fully succeeds or changes nothing — never a partial wipe.

Defense-in-depth: `Adda.delete()` is overridden to raise the same block reason,
so a raw admin/shell delete obeys the rule too. `AddaAdmin.has_delete_permission`
is `False` — deletion is channelled through the gated confirm page + service,
which also removes the M-5 ProtectedError-500 surface.

## Consequences

- The only money boundary stays settlement; neither path books/erases money.
- Worker earnings can never be destroyed by a delete (guard refuses; cancel keeps
  the record; hard-delete is pristine-only).
- Governance: PDD §3 lifecycle now also has `→ CANCELLED`; amendment registered.
- Pinned by `production/tests/test_adda_delete.py` (19 tests).
