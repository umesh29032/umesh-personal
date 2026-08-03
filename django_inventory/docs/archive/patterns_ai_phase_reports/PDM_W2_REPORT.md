> **ARCHIVED 2026-07-13** — shipped-phase report/review (patterns_ai). Live truth: [PLATFORM_STATUS](../../AI_PATTERN_INTELLIGENCE/PLATFORM_STATUS.md) + [PRODUCT_VISION_V2](../../AI_PATTERN_INTELLIGENCE/PRODUCT_VISION_V2.md) + the app [GUIDE](../../apps/patterns_ai/GUIDE.md). Kept for history (Phase-7 DOCCLEAN-D, D-OR-1). Outbound links reflect its era.

# PDM · W2 REPORT — the Product Pattern Workspace page
(2026-07-07)

**Status: ✅ W2 COMPLETE — STOPPED. W3 will not start without approval.**

## What was built (plan §W2 + owner's reusable-atom guideline, exactly)
- **`_design_row.html` — THE reusable UI atom.** Renders one Design Row
  business object (the W1 facade contract); mode-aware
  (`workspace` today; `palette`/`review` documented in the partial
  header for the future Cutting Table Available list, Layout/Approval
  Review and History — same object, different fields shown; no
  presentation logic will ever be duplicated).
- **`piece_list.html` → the Workspace** per the approved design:
  hero → **Product Summary** (％ + Ready badge + counts + fabric-
  defaults one-liner + `▸ details` expander keeping the readiness
  checklist, blockers, warnings AND the defaults form + the primary
  **[🪡 Open Cutting Table]** action) → **Sizes strip** (per-size
  completion chips, tap-jump-and-open; `[matrix view]`) → **size-first
  accordions** of design rows with **ghost rows in place** →
  piece-level settings bar (every control labeled *"applies to all
  sizes of ⟨piece⟩"* — §0 note 2) → **Layouts** (★ card first, saved
  list, no history claims) → footer (Register · Mats).
- Design-row facts per row: shape preview (new pure-string
  `outline_preview_svg`, tap-zoom) · reference thumb with `REF` tag
  (tap-zoom 1024) · name + size + badges · `v1 · Confirmed ✓` + amber
  `v2 draft in progress` chip · dims + honesty label
  (`tape-accepted` green vs trust-label amber) · status chip ·
  **Edit → deep-link carrying `#size-<id>`** (version page gained
  per-size anchors + `:target` highlight — size-first even inside the
  piece-family edit room).
- Production page button → **"🧵 Open Pattern Workspace"**, now
  targeting the Workspace itself (design §1); the smart-redirect URL
  keeps serving the Cutting-Table entry unchanged.
- Rule C intact: with `?product` no switcher anywhere; without —
  the chooser. All POST actions byte-unchanged (frozen writers).

## Browser walkthrough (REAL T-SHIRT, live server)
- Desktop: **100% · Production Ready ✅ · 4 sizes · 8 types · 30/32
  confirmed**; strip `S 8/8 ✓ · M 8/8 ✓ · L 7/8 ⚠ · XL 7/8 ⚠` (the
  real Care-Label gap); 32 design rows across 4 sections — every row
  showing shape + REF thumb + version + tape-accepted dims
  (`w2_workspace_top.png`).
- Ghost row live: `Care Label · L — ✗ NO DESIGN YET · optional —
  skipped honestly when absent · [+ ADD GEOMETRY]` (`w2_ghost_row.png`).
- Matrix overlay opens/closes (`w2_matrix_overlay.png`); lightbox zooms
  a shape preview; **Layouts**: `★ Production: Layout #22 · 1700 mm ·
  4005.99 mm · approved by … 20:58` + saved rows (`w2_layouts.png`).
- Mobile 390×844: **no horizontal scroll**, stacked cards, sticky
  mini-header hooks (`w2_mobile_top.png`, `w2_mobile_rows.png`).

## Tests — 16/16
size-first sections w/ every piece (4 atoms, 2 ghosts) · the atom's
facts (id, version chip, tape dims, preview class, **size-focused edit
href**) · draft chip appears on a new v2 draft while `v1 · Confirmed`
stays · ghost-row link + honest optional wording · strip counts +
matrix overlay content · summary keeps checklist/warnings/defaults
form · piece-level labeling · layouts ★-first w/o duplication ·
CT button + tool URL · chooser & Rule C · GET writes nothing ·
worker 403 · POST actions still work (optional toggle) · production
relabel + new target · version-page `#size-` anchor · mobile hooks.
Honest notes: 3 first-run test bugs (mine) — `design-row` substring
count caught CSS too; the template id used `slugify('12:18')`→`1218`
(collision-prone — FIXED to explicit `piece-size` id, a real
improvement the test surfaced); fixture was actually Ready, not
In-preparation.

**Battery honesty:** the FIRST full battery FAILED with 4 stale
assertions from the intentional page evolution (M4's two button tests
still expected "Open Layout Tool"/the tool URL; M6's render test + W1's
reroute test still expected the old "Pattern Design Status" heading).
All four consciously updated to the Workspace truths (comments mark
the W2 rework) — no code defects; the fresh battery below is the
post-fix rerun. (I had also pre-filled this section before reading the
battery output — corrected here; numbers below are from the verified
rerun.)

## Regression (post-fix rerun)
patterns_ai **344/344 OK** (328 + 16 W2) · full manufacturing suite **1229/1229 OK** (serial, fresh) ·
`makemigrations --check`: **No changes detected** · import contracts **unchanged — 1 kept, 1 broken (pre-existing target)** ·
zero schema · frozen writers untouched · facade unchanged (view-layer
enrichment only: preview svg + edit URL added per row in the view).
Known W3 item (already planned): the page currently derives readiness
more than once per GET (facade summary + matrix lens) — the W3 perf
pass unifies it.

**STOPPED — awaiting approval for W3 (General-size shortcut · scale/
perf pass · vocabulary sweep · PDM acceptance + stage close).**
