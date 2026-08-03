> **ARCHIVED 2026-07-13** — shipped-phase report/review (patterns_ai). Live truth: [PLATFORM_STATUS](../../AI_PATTERN_INTELLIGENCE/PLATFORM_STATUS.md) + [PRODUCT_VISION_V2](../../AI_PATTERN_INTELLIGENCE/PRODUCT_VISION_V2.md) + the app [GUIDE](../../apps/patterns_ai/GUIDE.md). Kept for history (Phase-7 DOCCLEAN-D, D-OR-1). Outbound links reflect its era.

# PLATFORM · PHASE 4 REPORT — the Digital Cutting Table SHELL
(2026-07-09)

**Status: ✅ PHASE 4 COMPLETE — STOPPED for the owner's real-T-Shirt
review. Phase 5 (canvas interaction) will not start without approval.**

The permanent workspace, built exactly to the owner's amended diagram —
all 7 amendments in, read-only, zero migrations, zero writers.

## What shipped
- **Route** `patterns_ai:cutting-table` (`table/<pk>/`); Manager gate +
  Dashboard STEP-3 open it; not-ready product → Dashboard redirect with
  the honest "locked" message; worker 403; POST → 405 (read-only shell).
- **Toolbar — frozen forever** (amendment 5): Import · Select · Rotate ·
  Mirror · Zoom · Grid · AI Optimize · Approve Layout · Export — all
  disabled with phase tooltips (5/5/5/5/5/5/6/7/7); **Generate (current
  tool) →** stays live (the working generator one tap away).
- **Pattern Library** (amendments 1+6): FABRIC GROUP → size → confirmed
  Design-Row atoms in `palette` mode (previews · dims · area ·
  tape-accepted · grain + fabric group). Confirmed-ONLY law enforced
  (draft-only piece excluded, tested); non-ready sizes = one honest
  muted line.
- **Digital Fabric Workspace** (amendment 2): fabric width (profile
  default 1700 mm live) · group/ratio/layout "--" · grid background ·
  width ruler · "Drop patterns here / Canvas interaction begins in
  Phase 5."
- **Layout Information** (amendment 3): all 10 permanent slots
  (Product…History), "--" where empty.
- **Approved Layout Library** (amendment 7): permanent section, "No
  layouts created yet. (Phase 7)".
- **Status bar** (amendment 4): Imported 0 · Placed 0 · Remaining n ·
  Fabric Width · Canvas Length -- · Utilization --.
- Responsive: 3-col → 2-col (1000px) → stacked (700px/390).

## Tests
NEW `test_phase4_shell.py` (6): all permanent regions · toolbar frozen
ORDER + phase tooltips + live Generate link · palette law (group-first,
confirmed-only, draft excluded, not-ready line, grain visible) · gate
redirect + message · worker 403/404/zero-GET-writes · POST 405.
Conscious updates (commented "Phase 4"): 3 gate-href asserts
(`test_pdm_w2` ×2, `test_phase1_dashboard` ×2) tool → cutting-table.
One template fix during the run: group header needed `|title`
(raw code rendered).

## Battery (counts from output, serial, fresh)
patterns_ai **382/382** (376+6 exact) · full suite **1267/1267**
(1261+6 exact) · `--check` No changes (zero-migration phase) ·
contracts 1 kept/1 broken pre-existing baseline.

## Browser (live, REAL T-SHIRT — the review artifact)
- `p4_shell_tshirt.png` (desktop): the owner's diagram live — frozen
  toolbar, BODY→S palette with real confirmed designs (Back/Front
  480×660 · Sleeves 380×220 · Pocket optional 130×140, previews + refs
  + tape-accepted + grain), 1700 mm ruler + grid workspace, Layout
  Information fully slotted, 30 confirmed available.
- RIB group renders after BODY; Approved Layout Library + full status
  bar verified (js booleans).
- DEV-HUB (0 Ready): URL → Dashboard redirect + "Digital Cutting Table
  is locked" message live.
- `p4_shell_mobile.png` (390×844): stacked panels, full palette, no
  horizontal scroll.

**STOPPED — the shell is ready for your hands-on T-Shirt review.
Phase 5 (canvas interaction: import/select/place) awaits your approval
after that review.**
