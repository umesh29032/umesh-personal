> **ARCHIVED 2026-07-13** — shipped-phase report/review (patterns_ai). Live truth: [PLATFORM_STATUS](../../AI_PATTERN_INTELLIGENCE/PLATFORM_STATUS.md) + [PRODUCT_VISION_V2](../../AI_PATTERN_INTELLIGENCE/PRODUCT_VISION_V2.md) + the app [GUIDE](../../apps/patterns_ai/GUIDE.md). Kept for history (Phase-7 DOCCLEAN-D, D-OR-1). Outbound links reflect its era.

# Phase 6 · M8 REPORT — production exports (PDF · tiled print · SVG stamp)
(2026-07-07)

**Status: ✅ M8 COMPLETE — STOPPED. M9 will not start without approval.**

Implemented exactly per plan: `compute/patterns_ai/pdf_io.py` (NEW pure-
python PDF writer, **zero new dependencies**), `nest.py` untouched,
bridge gains the `pdf` tool entry, two new views + URLs, one print
template, SVG summary stamping. Zero models/migrations (pin 17); frozen
services untouched (exports are DERIVED artifacts — §3f constitutional).

## The PDF — a production document (owner refinement 6)
- **Page 1 = the Production Layout Summary**: product · layout # ·
  width/length (facts) · utilization/waste ("derived at read", labeled)
  · pattern count · size ratio · verified · **production status with the
  approve audit line** · exported-by/at · tile count — plus ASSEMBLY
  instructions (print at 100%, check the scale bar, C/R order, overlap
  to the dashed lines, regenerate after a new approval).
- **Remaining pages = the tiled TRUE-SCALE marker**: A4 portrait,
  window 190×277 mm, 10 mm overlap (step 180×267), tiles numbered
  `C{col}-R{row}` with col/row-of-total in every header, dashed match
  lines at the step boundaries, corner trim ticks, piece outlines with
  centroid labels (`Right Sleeve·l #1`), fabric boundary, and a
  **100 mm scale bar on every tile** (printer honesty, Gate-1 spirit).
- **True scale pinned**: 1 mm = 72/25.4 pt; the 100 mm bar spans exactly
  283.46 pt (byte-asserted in tests: bar end at 311.81 pt from a
  28.35 pt margin).
- Structure: uncompressed content streams (byte-greppable tests),
  correct xref/trailer, WinAnsiEncoding fonts (· and × render), honest
  `{ok: false}` on build failure.

## Tiled print page (browser)
`/candidates/<pk>/print/` — summary block first, then every tile as a
**true-scale SVG** (`width="190mm"`, windowed viewBox — same grid +
numbering as the PDF via `svg_render.marker_tile_svg`), Gate-1-style
10 cm honesty bar under each tile, `@page A4 portrait 10mm` +
print-only visibility CSS (app chrome vanishes), one sheet per tile.

## SVG stamping (§3f)
The SVG download now carries `<desc>Production Layout Summary …</desc>`
+ `<metadata id="production-layout-summary">{json}</metadata>`
(sorted-keys JSON incl. the production flag). Drawable content
unchanged — web display untouched (only the download stamps).

## Safety
PDF + print are **verified-layouts-only** — the gate fires BEFORE any
compute call; unverified ⇒ honest refusal message + no buttons on the
layout page. Both views management-gated (worker 403 tested).

## Validation (real DEV-TEE ★ layout #12, live)
- Layout page shows both new export buttons (verified layout).
- Real production PDF built via the bridge: **31 pages (1 + 6×5)**,
  page 1 carries the ★ approval audit line ("YES - approved by … at
  2026-07-07 17:23"), tiles show the REAL garment curves (sleeve caps,
  shoulder slopes) with piece labels — artifact reviewed page-by-page
  (`m8_devtee_star12.pdf` + earlier `m8_smoke.pdf`).
- Print page live: **30 tiles, 30 honesty bars**, grid header
  "6 column(s) × 5 row(s) = 30 tile page(s)" (`m8_print_page.png`).
- SVG download live: metadata + desc + `"production": true` confirmed.

## Test results
- **M8 suite 7/7** (6 + 1 runtime-gated): tile grid math + labels
  (C1-R1 … C6-R5, 30× "TRUE SCALE", @page CSS, windowed viewBoxes,
  mm-sized tiles, summary block) · unverified print refused ·
  worker 403 (pdf + print) · SVG metadata/desc/values · export buttons
  verified-only · unverified PDF refused BEFORE the bridge ·
  **full PDF document assertions** (header, `/Count 31`, summary
  strings, last tile label, scale bar, 311.81 true-scale pin, %%EOF).
- Build-time findings fixed before wiring (caught by my own smoke):
  a leftover placeholder line in the tile renderer; StandardEncoding
  dropped `×`/`—` → switched to WinAnsiEncoding + cp1252 streams.
- Docs-sync bonus: compute README's tool table was missing `nest.py`
  (pre-existing drift) — added together with the `pdf_io.py` row.

## Regression
patterns_ai **318/318 OK** (311 + 7 M8) · full manufacturing suite **1203/1203 OK** (serial, fresh) ·
`makemigrations --check`: **No changes detected** · import contracts **unchanged — 1 kept, 1 broken (pre-existing target)** ·
ADR-F walls re-ran green (Django still never imports the cv stack;
the PDF rides the same JSON-file bridge, base64-encoded).

**STOPPED — awaiting approval for M9 (final validation + PROJECT
CLOSE). Acceptance validation remains owner-held, AFTER M9, on the
owner's real T-Shirt product, with the owner's dedicated prompt.**
