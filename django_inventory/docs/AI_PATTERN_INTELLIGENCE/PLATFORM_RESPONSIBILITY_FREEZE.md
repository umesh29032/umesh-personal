---
id: docs-ai-pattern-intelligence-platform-responsibility-freeze
type: topic-canonical
status: active
owner: handwritten
scope: patterns_ai
anchors: config/patterns_ai/
verified: 2026-07-18
---

# PLATFORM RESPONSIBILITY FREEZE — permanent, pre-Phase-2
(2026-07-09 · owner-declared, agreed and recorded · no further
architecture redesign)

## The three frozen responsibilities

**1 · Pattern Blueprint = the Product's structural definition.**
Owns the garment structure ONLY: which pieces exist + their rules —
piece count, required/optional, pair/mirror, fold, grain rule, fabric
group. NEVER owns geometry, dimensions, DXF, or images.

**2 · Pattern Manager consumes the Blueprint.**
Never creates product pieces. Sole responsibility: prepare Pattern
Designs for every Product Size until each size is Ready. It asks "for
Size M, have all Blueprint pieces been prepared?" — never "which pieces
exist?" (that answer always comes from the Blueprint).

**3 · Digital Cutting Table consumes only confirmed Pattern Designs.**
Never edits Blueprint data. Never creates Pattern Designs. Only
composes approved geometry into manufacturing layouts.

## Dashboard = the permanent entry point

The Pattern Dashboard remains the permanent home of ALL pattern
modules, present and future. Future modules (Grading · Fabric Library ·
AI Analytics · Layout History · …) join the dashboard as additional
steps/sections — the navigation never changes again. Registered here,
NOT implemented.

## Honest census — where TODAY's code crosses the freeze (Phase-2 migration list)

Recorded so the freeze is real, not aspirational:

| # | Current behavior | Violates | Phase-2 move |
|---|---|---|---|
| V-1 | The per-size Library page carries **“+ Add Pattern Design”** (registers a PatternPiece via `create_piece`) | Resp. 2 — the Manager surface creates product pieces | Piece registration moves to the Blueprint module; the Library keeps preparation only |
| V-2 | Library rows carry the **optional/required toggle** (`set_piece_optional`) | Resp. 1/2 — a Blueprint RULE edited from the Manager surface | Rule editing moves to the Blueprint module’s rows |
| — | Library rows’ **reference image add/replace/remove** | NOT a violation — reference is documentation, deliberately absent from the owner’s Blueprint-rule list; stays with preparation | keep |
| — | Piece rules today are SET ONCE at `create_piece` (pair/fold/fabric_group) with no edit surface; `grain_rule` does not exist yet | gap, not violation | Blueprint module becomes the single rules edit surface; `grain_rule` field lands there |

Single-writer law unchanged: every Blueprint-rule write still goes
through `pattern_geometry_service` (new setters added there, nowhere
else).

**Frozen. Effective immediately. Phase 2 implements the Blueprint
module against exactly this contract.**
