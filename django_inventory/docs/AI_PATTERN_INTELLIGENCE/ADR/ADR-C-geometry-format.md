---
id: docs-ai-pattern-intelligence-adr-adr-c-geometry-format
type: adr
status: active
owner: frozen
scope: architecture
anchors: —
verified: 2026-07-18
---

# ADR-C — Canonical Geometry Format & Versioning (P1 GATE)

**Status: DRAFT (Phase 1) — owner sign-off pending. This spec is a P1 gate:
no geometry row is written before the spec document is checked in.**

## Problem
Pattern geometry is a PERMANENT company asset that must outlive every engine,
library, and language choice (10-year lens). It must round-trip to SVG and
DXF-AAMA, carry garment features segmentation cannot see (grain, notches,
drills, internal lines, fold edges, seam-allowance semantics, future grade
rules), never drift numerically, and never require destructive migration.

## Decision
1. **Internal canonical format = versioned JSON** stored on `PieceSizeGeometry`
   (and placements on `MarkerPlacement` rows), with `schema_version` mandatory
   on EVERY payload (F3).
2. **Numbers: INTEGER micrometers** for lengths/coordinates; **integer
   centi-degrees** for angles. One quantization helper owns every conversion
   (I-4). No floats at rest.
3. **Coordinate conventions (written once, forever):** piece-local origin at
   bounding-box minimum corner; x right, y up; outer boundary wound CCW, holes
   CW; closed polylines; per-geometry `chord_tolerance_um` records the capture
   simplification; vertex-count sanity bounds.
4. **Curves: polyline-at-tolerance is the v1 canonical representation.**
   Chord tolerance (default 500 µm) is honest for nesting, printing, plotting,
   and DXF-AAMA (predominantly polyline in practice). A future additive curve
   representation (arcs/beziers alongside the polyline) is reserved in the
   spec, never replacing it.
5. **First-class features (fields may be empty in year 1, absent never):**
   grain vector (mandatory at confirm) · notches (boundary parameter t + depth
   + type) · drill points · internal lines (polyline + role) · fold edge
   reference · seam-allowance semantics flag (default "as-cut") · optional
   `grade_rule` payload (per-point deltas, own schema_version).
6. **No engine-native data ever** (F4); adapters translate at boundaries.
7. **Guaranteed exports:** SVG from P1; DXF-AAMA import P2/P3 and export by P4
   with round-trip tests as permanent proof the data is never trapped.
8. **Evolution rules:** additive-only; enums never repurposed; new fields
   nullable/empty-first; re-interpretation forbidden (F3).

## Alternatives considered
- **SVG as canonical** — rejected: float text, no feature semantics, style noise.
- **DXF as canonical** — rejected: entity zoo, library lossiness; it is an
  interchange target, not a home.
- **Floats in mm** — rejected (V2 C12): drift + cross-language round-trip risk
  in a permanent asset.
- **Beziers as v1 canonical** — rejected: complexity without a consumer;
  polyline+tolerance serves every planned output; curves stay a reserved
  additive extension.

## Tradeoffs
Integer µm requires disciplined conversion at edges (one helper, tested).
Polyline canonical means very tight curve tolerances inflate vertex counts
(bounded; tolerance recorded). JSON payloads are larger than binary (irrelevant
at our scale; compresses well).

## Consequences
Any tool in any language can read the asset with a one-page spec. Plotter/
projector output (P5) consumes stored geometry directly. Historical geometry
never needs migration — new schema_versions coexist.

## Future evolution
Grade-rule engine (reads the reserved payload) · curve extension · additional
feature types (splice marks, matching points) — all additive. A format v2
would be a new schema_version read alongside v1, never a rewrite.

## Why it respects Manufacturing V1
Self-contained in `patterns_ai`; no production schema involvement; mirrors
V1's frozen-snapshot discipline (immutable confirmed geometry = the same
philosophy as frozen rates/costs).

## Why it respects Blueprint V3
Directly implements C12 (µm), C11 (grade slot), F3 (evolution constitution),
F4 (engine independence), F6 companion (facts at rest, derivations at read),
and the export guarantees of the offline/open-source lock.
