> **ARCHIVED 2026-07-13** — shipped-phase report/review (patterns_ai). Live truth: [PLATFORM_STATUS](../../AI_PATTERN_INTELLIGENCE/PLATFORM_STATUS.md) + [PRODUCT_VISION_V2](../../AI_PATTERN_INTELLIGENCE/PRODUCT_VISION_V2.md) + the app [GUIDE](../../apps/patterns_ai/GUIDE.md). Kept for history (Phase-7 DOCCLEAN-D, D-OR-1). Outbound links reflect its era.

# PHASE 4 PLAN — the Digital Cutting Table SHELL
(2026-07-09 · PLAN ONLY — no code until owner approval · shell =
permanent workspace STRUCTURE only; every interaction explicitly out)

## Goal (owner spec, verbatim scope)
The permanent DCT workspace: Header · Toolbar · Left (Available Pattern
Library — REAL confirmed designs via the existing facade) · Center
(Digital Fabric Canvas placeholder) · Right (Properties) · Bottom
status · responsive · existing design system. **Everything read-only.**
NOT in Phase 4: drag/drop · placement · canvas interactions ·
optimization · persistence · AI · exports.

## Design decisions (3)

**D-1 · URL + the gate buttons retarget.**
New route `patterns_ai:cutting-table` = `table/<int:pk>/` (product
context locked in the URL, Rule C — same shape as the tool). The
Manager gate button + the Dashboard STEP-3 button retarget here: the
DCT button opens the DCT. The CURRENT working generation tool stays
fully alive at its own URL — the shell's toolbar carries an honest
**"Generate (current tool) →"** link so the working path stays one tap
away until the DCT absorbs it (Phases 5–7). Not-ready product hitting
the URL directly → redirect to the Dashboard with the honest gate
message (no dead ends). Gate = management role + ≥1 Ready size (the
same facade field as everywhere).

**D-2 · Left panel = the facade's reserved `palette` mode.**
`_design_row.html` documented `mode='palette'` for exactly this since
W1. Content law (frozen): the DCT consumes **confirmed designs of READY
sizes only** —
- Ready sizes render as sections with their confirmed Design-Row atoms
  (preview · name · dims · area · pair/fold badges · grain + fabric
  group from the Phase-2 facade additions);
- non-Ready sizes appear greyed with the honest reason ("not ready —
  finish required designs"), never expandable;
- rows grouped under **fabric-group headers** inside each size (LAW 12
  made visible from day one — display-only, no selector logic).
No import buttons yet — the atom renders read-only; Selected/Placed
arrive Phase 5.

**D-3 · Pure read view.** `CuttingTableShellView` = TemplateView,
management gate, ONE facade call + one `ProductFabricProfile` read
(defaults shown read-only in Properties). Zero writes on GET (tested,
as on every platform page). No new services, no facade changes (Phase-2
additions already carry everything the palette needs).

## The shell, concretely
- **Header**: product name/code · "Digital Cutting Table" · ← Dashboard.
- **Toolbar** (read-only placeholders marked for their phases): fabric
  width (profile default) · fabric-group legend · zoom/grid/undo
  buttons DISABLED with "Phase 5" title · Generate-tool link ·
  AI Optimize DISABLED "Phase 6" · Approve DISABLED "Phase 7".
- **Left**: Available Pattern Library (D-2).
- **Center**: static fabric strip (profile width, grid pattern, width
  ruler label) + "canvas interactions arrive in Phase 5" note — an
  honest placeholder, not a fake canvas.
- **Right**: Properties — product summary (sizes ready n/m · confirmed
  designs count · fabric defaults) read-only.
- **Bottom status**: `0 imported · 0 placed · shell milestone` +
  utilization "—".
- **Responsive**: desktop = 3-column grid; tablet = left panel
  collapsible; mobile 390 = stacked (palette as <details>, canvas
  full-width, properties below) — explicit strategy per the mobile
  rule; the DCT is a desktop-first WORK surface but never broken on
  phone.

## File touch list (~7, zero migrations, zero writers)
| File | Change |
|---|---|
| `patterns_ai/views.py` | `CuttingTableShellView` (read-only; gate + redirect-with-message) |
| `patterns_ai/urls.py` | `table/<int:pk>/` = `cutting-table` |
| `patterns_ai/templates/patterns_ai/cutting_table.html` | NEW — the shell |
| `patterns_ai/templates/patterns_ai/_design_row.html` | light `palette` mode block (read-only variant of existing atom) |
| `piece_list.html` + `dashboard.html` | gate/STEP-3 buttons → `cutting-table` |
| tests: NEW `patterns_ai/tests/test_phase4_shell.py` | see below |
| conscious updates | gate-href asserts in `test_pdm_w2` (2) + `test_phase1_dashboard` (1): `tool` → `cutting-table`, commented "Phase 4" |

## New-test coverage
Gate: ready product renders shell · not-ready → dashboard redirect +
message · worker 403 · unknown product 404. Panels: header/toolbar/
left/center/right/status all present. Palette law: confirmed designs of
Ready sizes ONLY (draft + missing excluded; non-ready size greyed with
reason; fabric-group headers present). Read-only: zero writes on GET ·
no POST route. Toolbar: disabled placeholders carry phase labels ·
generate-tool link present. Buttons: Manager + Dashboard now target
`cutting-table`.

## Risks
- R-1 retargeting the gate hides the working generator one level deep —
  mitigated by the explicit toolbar link (D-1); owner reviews on real
  T-SHIRT right after.
- R-2 palette re-uses the atom — any atom tweak must not disturb
  `library` mode (suite guards it).
- R-3 conscious test drift: 3 gate-href asserts, each commented.

## Acceptance criteria
1. T-SHIRT (4/4 Ready) → shell renders: all 6 regions; palette shows
   its REAL confirmed designs grouped size → fabric group, with dims/
   area/badges from the facade.
2. DEV-HUB (0 Ready) → URL redirects to Dashboard with the honest gate
   message; its Manager/Dashboard buttons stay honestly disabled.
3. Read-only proven: zero DB writes on GET; no POST accepted.
4. Toolbar placeholders disabled + phase-labeled; Generate link works.
5. Battery green (counts from output) · zero migrations · contracts
   baseline · browser desktop + 390×844 screenshots on the real
   T-SHIRT (the owner's review artifact).

---

## APPROVED + OWNER AMENDMENTS 1–7 (2026-07-09 — the PERMANENT workspace layout, frozen)

1. Left panel name = **"Pattern Library"** (no "Available" — the panel
   will later hold Available/Selected/Imported/Hidden/Search/Filter).
2. Center = **"Digital Fabric Workspace"** (never "placeholder"):
   fabric width · fabric group ("--" until import exists) · empty
   workspace · grid background · width ruler · "Canvas interaction
   begins in Phase 5."
3. Right panel = **"Layout Information"** with ALL permanent slots:
   Product · Fabric Group · Fabric Width · Cut Plan · Ratio · Imported
   Pieces · Placed Pieces · Utilization · Approval Status · History —
   "--" where empty. Never redesigned later.
4. Bottom status = Imported · Placed · Remaining · Fabric Width ·
   Canvas Length · Utilization ("--" where n/a).
5. **Toolbar frozen forever**: Import · Select · Rotate · Mirror ·
   Zoom · Grid · AI Optimize · Approve Layout · Export — all disabled
   with future-phase tooltips; Generate (current tool) stays enabled.
6. Pattern Library grouping REVERSED: **FABRIC GROUP first → sizes
   inside** (layouts are per fabric group — LAW 12 lived, not just
   labeled). Non-ready sizes = one muted honest line.
7. **"Approved Layout Library"** permanent section below the workspace:
   "No layouts created yet." (Phase 7).

Owner note: post-Phase-4 documentation = reports + minimal GUIDE lines
only; screenshots/working behavior over prose.

**IMPLEMENTATION AUTHORIZED with amendments — proceeding.**
