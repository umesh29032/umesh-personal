# ADR 0004 — `tracking` is an append-only history + barcode primitive

**Status:** Accepted (DECISION_LOG #8; refined by docs/P4_2_BARCODE_DESIGN_REVIEW.md)

## Context
History/audit and per-piece barcode state must be durable and never silently mutated. We
also want `tracking` to be cleanly extractable later (a scan/range microservice).

## Decision
- `tracking` owns `BarcodeBatch` (contiguous seq range per Adda·color·size), `BatchBarcode`
  (lazy per-piece scan state — a row exists only once a piece is scanned), `BarcodeExportBatch`
  (manifest; files regenerated on the fly, never stored), and the `*History` tables.
- It references upstream apps **only via string FKs + lazy imports** — no module-level
  `import production`. Its data layer is already decoupled (string FKs); the residual
  service/view coupling is the subject of the parked P4.2 cycle-break review.
- Barcode value format is canonical: `{adda.code}-{seq:04d}`; range invariants are DB
  `CheckConstraint`s; one generation per Adda (one-shot, `IntegrityError` on rerun).

## Consequences
- The range is the source of truth for piece existence/count; unscanned pieces cost no rows.
- Future Missing-Piece / Alter-Rework domains *read* this scan state by id; they don't move it.
- Direction of the production↔tracking edge (assembly ownership) is **deferred** to the
  manufacturing-domain review — see `docs/P4_2_BARCODE_DESIGN_REVIEW.md` (D3).
