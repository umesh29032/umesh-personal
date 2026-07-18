---
id: docs-ai-pattern-intelligence-adr-adr-d2-piece-grain
type: adr
status: active
owner: frozen
scope: architecture
anchors: —
verified: 2026-07-18
---

# ADR-D2 — Piece-Version Grain & Per-Size Geometry (P2 entry decision)

**Status: DECIDED 2026-07-07 (Phase 2 entry; slot reserved by the master
plan as "D2 mini-ADR during P1/P2"). Owner reviews with the P2 package.**

## Problem
Where does captured geometry live: one version per piece, or per
(piece, size)? A wrong grain either forces re-capturing every size when one
changes, or shatters the review/confirm unit into size fragments with no
coherent lineage.

## Decision
1. **Version chain stays PIECE-level** (`PatternPieceVersion`, ADR-D
   unchanged): one draft → confirm/reject cycle per piece revision. The
   version is the REVIEW UNIT.
2. **Geometry is a PER-SIZE child row:** `PieceSizeGeometry` =
   (version, `production.ProductSize`) → one canonical ADR-C payload.
   UNIQUE(version, size). A draft version accumulates size rows as the
   cutting master captures them; **confirm freezes the version with
   whatever sizes it honestly has** (partial size coverage is a fact, not
   an error).
3. **Later sizes = COPY-FORWARD, never mutation:** adding size XL after v1
   confirmed ⇒ create v2 (draft), **copy v1's geometry rows forward**
   (each copied row records `copied_from` = the source row; provenance
   survives), capture/extract XL into v2, confirm v2 → v1 auto-supersedes
   (ADR-D lineage). No re-capture of unchanged sizes, no edit of confirmed
   rows, complete history.
4. **Size FK targets `production.ProductSize`** (per-product size chart —
   the manufacturing-native grain; read-only FK, PROTECT, no reverse
   dependency). No parallel size registry is invented.
5. **`PatternSetLabel`** (master-plan model): a product-homed label row
   grouping versions into a named graded set (e.g. "3-PATTI cardboard set
   Jul-2026"); `PatternPieceVersion.set_label` = nullable FK, additive.
   Identity only — no logic hangs on it in P2.

## Alternatives considered
- **Version per (piece, size)** — rejected: review/lineage fragments per
  size; a piece revision (shape fix) would need N parallel version bumps.
- **Geometry JSON keyed by size inside ONE payload** — rejected: sizes
  confirm at different times; per-row trust grades/tape acceptance
  impossible; violates one-fact-one-row.
- **Mutable confirmed version accepting late sizes** — rejected outright:
  breaks ADR-D immutability and the F5 append-only constitution.

## Consequences
Capture burden matches reality (sizes arrive over days); confirmed truth
is immutable; "what changed in v2?" is answerable row-by-row
(`copied_from` null = newly captured). Grading engines (future) get
per-size rows exactly where ADR-C expects them.
