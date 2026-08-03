> **ARCHIVED 2026-07-13** — shipped-phase report/review (patterns_ai). Live truth: [PLATFORM_STATUS](../../AI_PATTERN_INTELLIGENCE/PLATFORM_STATUS.md) + [PRODUCT_VISION_V2](../../AI_PATTERN_INTELLIGENCE/PRODUCT_VISION_V2.md) + the app [GUIDE](../../apps/patterns_ai/GUIDE.md). Kept for history (Phase-7 DOCCLEAN-D, D-OR-1). Outbound links reflect its era.

# PHASE 5 PLAN — workspace interactions (manual layout builder)
(2026-07-09 · owner-scoped: Import · Select · Move · Rotate · Mirror ·
Delete · Undo — NOTHING else. Zero writes, zero persistence, zero
models. Pure client-side session on the frozen shell.)

## How (all inside the frozen architecture)

**Data** — the shell view already builds palette rows from the facade;
it now ALSO emits `workspace_payload` (design_key → name · size · group
· grain_rule · pair · outline_mm · w/h) via `json_script`. GET-only;
facade untouched; no duplication (same rows, one serialization).

**Canvas** — one SVG, viewBox in mm (width = fabric width, height
fixed this phase; length math = Phase 6). Pieces = `<g><polygon>` from
`outline_mm` + translate/rotate/mirror transforms. Vanilla JS in the
page (same pattern as the proven ROADMAP-V2 workspace — pointer drag,
transform state), no libraries, no forks of geometry code.

**Interactions (exactly the 7):**
1. **Import** — [+ Import] affordance on each palette row (the atom's
   documented palette-mode "selection affordance"); each click = one
   instance, staggered drop. **LAW 12 enforced at import**: first
   import fixes the session's fabric group; a different group refuses
   with the honest one-layout-one-group message (client-side; the law
   is frozen, silence would violate it).
2. **Select** — click piece = single selection (marquee/multi = later).
3. **Move** — pointer drag, free placement; no snapping (not trivial →
   out, per owner).
4. **Rotate** — 90° steps filtered by the Blueprint grain rule:
   STRICT → 0° only (button disabled + reason) · TWO_WAY → 0/180 ·
   FREE → 0/90/180/270.
5. **Mirror** — only when the Blueprint pair rule allows; otherwise
   disabled with reason.
6. **Delete** — removes the INSTANCE from the workspace only.
7. **Undo** — session snapshot stack (import/move/rotate/mirror/delete);
   dies with the page. No redo (not in scope).

**Where the controls live** — the frozen toolbar stays EXACTLY as
Phase 4 (owner diagram: "only Generate remains active"). Interactions
get: palette [+ Import] · click/drag on canvas · a small SELECTION BAR
inside the workspace header (Rotate ⟳ / Mirror ⇋ / Delete ✕ — visible
when a piece is selected, touch-friendly 44px) · Undo in the workspace
header · keyboard R / M / Delete / Ctrl+Z on desktop.

**Live counters (display-only, client-side):** Imported / Placed /
Remaining in Layout Information + status bar; Fabric Group fills from
the session's group. Utilization/Length stay "--" (Phase 6 math).

**MUST-NOT list honored:** no writes (POST still 405), no models, no
save, no AI, no nesting, no collision, no utilization, no history.

## Files (~5)
`views.py` CuttingTableShellView (+payload) · `cutting_table.html`
(canvas SVG + selection bar + JS + counters) · `_design_row.html`
(palette [+ Import] button) · NEW `tests/test_phase5_interactions.py`
(server-side: payload correctness incl. grain/pair/outline per design ·
import affordance rendered · interaction chrome present · POST still
405 · zero GET writes · toolbar unchanged) · report.
Browser = the real interaction proof (scripted click/drag/rotate/
mirror/delete/undo + LAW-12 refusal + screenshots).
