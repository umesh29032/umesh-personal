> **ARCHIVED 2026-07-13** — shipped-phase report/review (patterns_ai). Live truth: [PLATFORM_STATUS](../../AI_PATTERN_INTELLIGENCE/PLATFORM_STATUS.md) + [PRODUCT_VISION_V2](../../AI_PATTERN_INTELLIGENCE/PRODUCT_VISION_V2.md) + the app [GUIDE](../../apps/patterns_ai/GUIDE.md). Kept for history (Phase-7 DOCCLEAN-D, D-OR-1). Outbound links reflect its era.

# PLATFORM · PHASE 6A REPORT — physics
(2026-07-09)

**Status: ✅ 6A COMPLETE — STOPPED. 6B (manual optimization) will not
start without approval.**

Collision · spacing · grid snap · utilization — all live, all
session-only, still ZERO writes. All 9 owner refinements honored.

## The frozen coordinate system (refinement 1 — documented as ordered)
**World coordinates = MILLIMETRES, permanently.** Piece positions,
outlines, snap, collision distances, utilization math — all mm. Pixels
exist only in the SVG rendering layer (viewBox maps mm→px). Zoom/pan
(6B) will move the CAMERA, never coordinates. Export, AI, DXF, layout
saving and Adda consume these same mm coordinates. Stated in the source
at the engine's head.

## What shipped
- **Runtime object = single truth** (refinement 2): every instance is
  `{instance_id, design_key, fabric_group, grain_rule, pair, x_mm,
  y_mm, rotation, mirror, locked}` + cached `_outline`/`_bbox`; every
  operation mutates the runtime, the DOM only renders it. Undo
  serializes runtime fields only.
- **Collision pipeline** (refinement 3): `collidePair` = bbox check
  (spacing-inflated prune) → polygon check (segment intersection +
  containment) → spacing-margin check (min edge-edge distance) →
  `'clear' | 'spacing' | 'collision'`. Reusable — spacing is literally
  layer 3, and 6B/6C consume the same function.
- **Spacing rule** — from the profile's `default_spacing_mm` (3.0 mm on
  T-SHIRT), shown in the workspace meta.
- **Grid snap** — toolbar **Grid** now LIVE (its phase arrived);
  `SNAP_MM = 10` internal config only (refinement 5 — 5/20/50 later,
  no UI).
- **Utilization** (refinement 4): isolated `layoutMetrics(widthMm,
  pieces)` → usedCm2/lengthMm/utilPct/freeCm2 — the UI only displays
  it; AI + approval will call the same function. Canvas Length +
  Utilization slots alive in Layout Information + status bar.
- **Locked pieces** (refinement 6): selectable always; move/rotate/
  mirror/delete refused with honest hints; 🔒 toggle on the selection
  bar + `L` key; grey paint. **Manual-first** (refinement 7) is now
  structural: `locked` on the runtime object is exactly the constraint
  6B compact and 6C auto/AI will treat as immovable.
- Collision paint: red = collision · amber = spacing violation ·
  live `Collisions: n` counter.

## Tests
NEW `test_phase6a_physics.py` (4): payload carries area (1200 cm² for
the 400×300 fixture — facade truth, no recompute) · spacing 3.0 reaches
the pipeline + meta · Grid live + SNAP_MM internal + physics slots +
the mm-freeze documented in source · still zero-writes + POST 405.
Conscious updates (commented "6A"): both toolbar tests — Grid became a
live button, ORDER still asserted frozen via position sort; one of my
new asserts counted a JS selector (c-util ×3) → `class="c-util"`.

## Battery (counts from output, serial, fresh)
patterns_ai **390/390** (386+4 exact) · full **1275/1275** (1271+4
exact) · `--check` No changes (zero-migration phase) · money/facade/
writers untouched.

## Browser (live, REAL T-SHIRT, scripted)
- **Collision**: two Back Panels dragged onto each other →
  `collisions:2 red-pieces:2`; red paint visible
  (`p6a_collision_red.png` — also shows live Layout Info: BODY · 2 ·
  2 · 29 · Utilization 49.3%, selection bar with 🔒 Lock, Grid button,
  `Spacing: 3.0 mm`).
- **Spacing layer distinct**: pieces at <3 mm gap → `spacing-violations:2
  hard:0` (amber channel, not red).
- **Snap**: Grid ON → dragged coords land on exact 10 mm multiples
  (1710, 810).
- **Utilization hand-verified**: 2×2930.6 cm² ÷ (1700×1470/100) =
  23.45% → display `23.5%` — exact.
- **Lock**: locked piece still selectable, drag refused ("locked piece —
  selectable, not movable"), rotate disabled, transform unchanged.
- Undo covers every op incl. lock toggles.

## Honest observation (not fixed — out of 6A scope)
Pieces can be dragged past the fabric's right edge (x > width); 6A
physics is piece-vs-piece only per the approved order. Fabric-bounds
checking belongs naturally to 6B compact / 6C auto-place (they respect
width) and Phase-7 save validation. Flagged so it's a decision, not an
oversight.

**STOPPED — 6A done and verified. 6B (Compact ← · nudge · zoom ·
lock-aware manual optimization) awaits your approval.**
