> **ARCHIVED 2026-07-13** — shipped-phase report/review (patterns_ai). Live truth: [PLATFORM_STATUS](../../AI_PATTERN_INTELLIGENCE/PLATFORM_STATUS.md) + [PRODUCT_VISION_V2](../../AI_PATTERN_INTELLIGENCE/PRODUCT_VISION_V2.md) + the app [GUIDE](../../apps/patterns_ai/GUIDE.md). Kept for history (Phase-7 DOCCLEAN-D, D-OR-1). Outbound links reflect its era.

# PLATFORM · PHASE 6B REPORT — manual optimization
(2026-07-09)

**Status: ✅ 6B COMPLETE — STOPPED. 6C (auto placement + AI, AI last)
will not start without approval.**

All 8 owner rules honored. Still session-only, still ZERO writes.

## What shipped

**1 · Fabric boundary = constraint LAYER 0** (rule 1). The pipeline is
now `boundary → collision → spacing` in ONE function
(`placementStatus`) — manual move reporting, import placement, Compact,
and (6C) Auto/AI all consume it. Off-fabric pieces paint violet
(`col-bound`), count in the violations counter. Boundary is a REPORT on
manual moves (operator freedom stays — manual wins) and a hard
constraint for everything algorithmic.

**2 · Runtime frozen** (rule 2) — every 6B feature mutates only the
runtime object; render stayed a pure projection; undo still serializes
runtime fields.

**3 · Camera ≠ World** (rules 3+6). `camera {x, y, scale}` lives only
in the SVG viewBox; world mm never move. **Zoom** toolbar button LIVE
(click in · Shift-click out · wheel-at-pointer · `0` resets); **pan** =
drag on empty fabric. Browser-proven: after zooming, the piece
transform is byte-identical while the viewBox changed
(`world-unchanged:true camera-changed:true`).

**4 · Compact = assist, not optimizer** (rules 4+5). Gravity passes
(left, then up) in 50→10→1 mm steps through the SAME pipeline; locked
pieces never move; rotation/mirror (operator intent) never change; no
search, no scoring. A piece already IN violation may only step where
its verdict IMPROVES — or, off-fabric, where its overflow strictly
shrinks (it "walks home"); equal-rank collision/spacing steps are
rejected (no tunneling).

**5 · Import lands on clear fabric** — first-fit row-major scan through
the same pipeline (the old fixed stagger overlapped real 480 mm panels
at birth); honest fallback message when nothing fits.

**6 · Nudge** (rule 7): arrows 1 mm · Shift 10 mm; `NUDGE_JUMP_MM=100`
exists as a constant only (Ctrl = future); one undo snapshot per burst.

## Fixes found by my own browser run (before report)
- First compact could not rescue an off-fabric piece (`tryShift`
  demanded `clear`, so a violating piece could never step out) → the
  improve-or-shrink-overflow rule above.
- First fix's equal-rank acceptance would have let colliding pieces
  tunnel and off-fabric-left run away → tightened to strict-improve +
  boundary-overflow-shrink only.
- Import stagger overlapped real-size panels → first-fit placement.

## Tests
NEW `test_phase6b_manual.py` (4): boundary = pipeline layer 0
(+`col-bound` channel) · CAMERA ≠ WORLD structural + Zoom live ·
Compact control + "not an optimizer" stated in source + nudge constants
(1/10/100) · still zero-writes + POST 405. Conscious update: phase-5
toolbar test (Zoom span→button, commented).

## Battery (counts from output, serial, fresh — re-run AFTER the fixes)
patterns_ai **394/394** (390+4 exact) · full **1279/1279** (1275+4
exact) · `--check` No changes (zero-migration phase).

## Browser (live, REAL T-SHIRT, scripted)
- **Boundary**: piece dragged past the right edge → `boundary:1
  counter:1`, violet paint.
- **Zoom camera-only**: piece transform unchanged, viewBox changed.
- **Nudge**: x 4767→4766→4756 (deltas exactly −1, −10).
- **Compact + lock + rescue**: off-fabric piece at x=4767 walked home
  to (603,0); locked piece stayed at (210,40) untouched.
- **Clean end state** (`p6b_compact_live.png`): 4 real T-Shirt pieces
  imported onto clear fabric (0 violations at import), Compact →
  tight-left marker, **0 violations · 58.9% utilization · 660 mm
  length** — it already looks like marker making.

**STOPPED — 6B done and verified. 6C (Auto Place via the existing BLF
floor + AI Optimize via the existing op:'optimize' engine through a
stateless endpoint — reuse only, never fork) awaits your approval.**
