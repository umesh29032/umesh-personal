---
id: docs-ai-pattern-intelligence-phase4-workspace-design
type: topic-canonical
status: active
owner: handwritten
scope: patterns_ai
anchors: config/patterns_ai/
verified: 2026-07-18
---

# Phase 4 DESIGN — Interactive Marker Workspace (2026-07-07)

**Governed by PRODUCT_VISION_V2 + ROADMAP_V2. Scope = the owner's 18-item
list, nothing else. Architecture review inline (§4).**

## 1. Core decision: the workspace edits a CANDIDATE and saves a NEW one

- **Open:** `/patterns/workspace/<candidate_pk>/` loads that candidate's
  placements (absolute lay-frame rings, mm — the format everything
  already speaks).
- **Save:** `save_manual_layout` (single writer, marker_generation_service)
  creates a **new immutable run+candidate pair with `engine='manual'`** —
  the run records fabric width + height + the source candidate id +
  carried-forward ratio; the candidate stores the adjusted placements
  (with per-piece `locked` flags) and the INDEPENDENT verification
  verdict. Everything downstream (visualization, derived metrics, SVG
  export, immutability guards) works on it unchanged.
- **Reload:** open any candidate (engine or manual) in the workspace.
  Save/reload = **zero new models, zero migrations.**

## 2. Fabric width & HEIGHT

Workspace inputs; the marker boundary rect = height(length axis) ×
width. Save refuses layouts whose verified length exceeds the height or
whose pieces exit the width (the SAME verifier as generation — one
verification home: `nest.py` gains a tiny `op:"verify"` mode reusing
`verify_layout` verbatim). Height stored in the manual run's params.

## 3. The canvas (vanilla JS, page-scoped — the P2 editor's proven pattern)

SVG with a viewBox camera: wheel/buttons zoom, background-drag pan
(infinite canvas) · toggleable 10/50 mm grid (`<pattern>`) · draggable
V/H guides · pieces as `<g>` groups — pointer-drag translate,
**rotate = 180° toggle only (the standing grain rule; 90° stays
forbidden)**, lock toggle (locked = undraggable, styled) · snap to grid
step and to guides on drop · client-side collision highlight (bbox
prefilter + segment-intersection/containment test → red stroke) · live
utilization % / wastage % / marker length / fits-height flag recomputed
on every drop (shoelace areas; **display only — the server verifier is
authoritative at save**).

## 4. Architecture review (why this is the simple version)

- Reuses: placements format, candidate immutability, run params spine,
  the one verifier, derived metrics, marker_svg, candidate pages, the
  P2 drag technique. New surface = ONE view + ONE template + ONE service
  function + ONE compute op flag.
- No new models/tables/caches/workers/websockets. No canvas framework.
  No client authority over stored numbers.
- Refusals recorded honestly: overlapping or oversize saves are REFUSED
  with the verifier's numbers (fix, then save).
- Piece-set integrity: save accepts moves/rotations/locks ONLY — the
  piece multiset must equal the source candidate's (no adds/removes).
