> **ARCHIVED 2026-07-13** — shipped-phase report/review (patterns_ai). Live truth: [PLATFORM_STATUS](../../AI_PATTERN_INTELLIGENCE/PLATFORM_STATUS.md) + [PRODUCT_VISION_V2](../../AI_PATTERN_INTELLIGENCE/PRODUCT_VISION_V2.md) + the app [GUIDE](../../apps/patterns_ai/GUIDE.md). Kept for history (Phase-7 DOCCLEAN-D, D-OR-1). Outbound links reflect its era.

# PLATFORM · PHASE 8B REPORT — the Adda chooses
(2026-07-10)

**Status: ✅ 8B COMPLETE — STOPPED. 8C (expected pieces + advisory
reconciliation) will not start without approval.**

The chain's one missing edge is live: an Adda now SELECTS and DISPLAYS
its manufacturing contract(s) from the Approved Layout Library — and
only from there (rule 9). Zero enforcement, zero completion-behavior
change, exactly as planned.

## What shipped
- **The choose page** (`table-usage/<adda>/`, management-gated):
  current contracts per fabric group (uid · V · name · recorded-by ·
  SVG · the F1 void flow with mandatory reason) + the product's ACTIVE
  library (width/length/util derived). **STALE layouts render disabled
  with "⚠ STALE — cannot manufacture"** (LAW 11 loud at selection —
  and the 8A writer refuses anyway); ARCHIVED layouts aren't offered;
  a taken group greys with "void it first". POST = `record_usage` /
  `void_usage` — the 8A single writer only.
- **The wall, crossed by inversion**: production's
  `cutting_pattern.LAYOUT_PROVIDER = None` registry (imports nothing);
  patterns_ai registers its READ-ONLY `build_layout_panel` in
  `apps.ready()` (the ARCHIVE_VALIDATORS pattern). `_build_pattern_
  context` consumes the plain dict wrapped in try/except — **a provider
  failure can never break the stage page** (tested with an exploding
  provider → 200, section absent, logged).
- **The Manufacturing Layout panel** on the pattern-stage workspace
  (management view): per group — uid · V · name · width × length ·
  live STALE re-check · Marker SVG link · Manage/Choose hand-off.
  Worker checklist untouched.
- Adda detail page: "★ Manufacturing Layouts" link (template-level,
  like the existing Advisor/Yield links).
- **Doc freeze recorded** (owner order): the permanent
  manufacturing-timeline rule now heads PHASE8_IMPLEMENTATION_PLAN.md.

## Tests
NEW `test_phase8b_choose.py` (6): lists-ACTIVE-only + record + taken-
group greys · STALE disabled + ARCHIVED hidden · void flow + worker
403 · provider registered by apps.ready() + returns the contract dict ·
**the production stage workspace renders the uid** (true cross-app
integration through the inversion) · exploding provider → page still
200. All 6 green first run.

## Battery (counts from output, serial, fresh)
patterns_ai **419/419** (413+6 exact) · full **1304/1304** (1298+6
exact) · `--check` No changes (zero-migration milestone) · contracts
1 kept/1 broken pre-existing baseline · ADR-H: the only production
diffs are the data-only registry, the wrapped hook, one template
section and one link — no imports (sweep still green).

## Browser (live — DEV data ONLY; golden T-SHIRT untouched)
Setup: `DEV-P8B` product → confirmed geometry → table-saved + approved
`LAY-DEV-P8B-000001` → Adda `DEV-P8B-A1` on a cutting_pattern flow.
(The verifier honestly REFUSED my first fixture — overlapping rings,
27000 mm² — the save pipeline protecting even DEV setups.)
- Choose page: library row + "★ Use for BODY" → recorded → "Current
  contracts: BODY · LAY-DEV-P8B-000001 · V1 · by umesh…" + Void field
  (`p8b_choose.png`, `p8b_choose_recorded.png`).
- **The stage workspace** (`p8b_stage_panel.png`): the Pattern Design
  page now carries "Manufacturing Layout — the approved contract this
  Adda cuts from (library-only)": BODY · LAY-DEV-P8B-000001 · V1 ·
  1600 mm × 620.0 mm · MARKER SVG · MANAGE LAYOUTS → — rule 9 on
  screen inside a production page, with production importing nothing.

**STOPPED — 8B done and verified. 8C (marker-derived suggested breakup
+ WARN reconciliation, never blocking) awaits your approval.**
