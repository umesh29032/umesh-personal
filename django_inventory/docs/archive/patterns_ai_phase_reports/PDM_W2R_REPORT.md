> **ARCHIVED 2026-07-13** — shipped-phase report/review (patterns_ai). Live truth: [PLATFORM_STATUS](../../AI_PATTERN_INTELLIGENCE/PLATFORM_STATUS.md) + [PRODUCT_VISION_V2](../../AI_PATTERN_INTELLIGENCE/PRODUCT_VISION_V2.md) + the app [GUIDE](../../apps/patterns_ai/GUIDE.md). Kept for history (Phase-7 DOCCLEAN-D, D-OR-1). Outbound links reflect its era.

# PDM · W2R REPORT — the locked two-page workflow
(2026-07-08)

**Status: ✅ W2R COMPLETE — STOPPED. W3 will not start without approval.**

Implemented the owner-locked direction exactly — no design documents,
straight implementation:
`Production Product → PRODUCT PATTERN MANAGER (sizes only) →
PATTERN DESIGN LIBRARY (one size) → Cutting Table (gated)`.

## Page 1 — the Product Pattern Manager (`?product=N`)
- SIZES ONLY. Each size = one verdict card:
  **`S — Ready for Cutting ✓ · 8/8 Pattern Designs`** /
  **`L — Needs Attention ⚠ · 7/8 · Missing: ⟨required names⟩`** +
  progress bar + **[Manage Pattern Designs]**. NO design rows anywhere
  on the page (tested).
- **`+ Add Size`** (hand-off to production Product Sizes — boundary
  clean, labeled "(opens Product Sizes)").
- **Cutting-Table gate (owner-locked rule):** enabled when ≥1 size is
  Ready — else `aria-disabled` with the honest reason ("no size is
  ready yet — finish the required designs of at least one size").
- Product details (readiness checklist · warnings · fabric-defaults
  form · mats link) live in a collapsed details sheet; the matrix stays
  as the power-lens overlay. Header = product name + confirmed-counts
  only — nothing competes with the size cards.
- Verdict LAW: `ready` = ALL REQUIRED designs confirmed for that size;
  optional gaps never block a size (mirrors generation truth).

## Page 2 — the Pattern Design Library (`?product=N&size=l`)
- ONE size, complete source of truth. Header: `← Sizes · Pattern
  Designs · L · Ready/Needs-Attention · n/m confirmed · Missing: …`.
- Every Design-Row atom (mode=`library`) now carries the owner's full
  list: shape preview (tap-zoom) · reference (REF-tagged, tap-zoom) ·
  piece name + badges · **version + draft chip** · status ·
  **W × H mm + honesty label** · **area cm²** (new, shoelace) ·
  **DXF download** (per-design) · **last updated** · contextual
  primary action (**+ Add geometry** / **Confirm →** / **Edit →**,
  size-focused anchors).
- **Issues float to the top** (required-missing → draft →
  optional-missing → confirmed; facade-ordered).
- Manage-in-place: optional toggle + reference add/replace/remove ON
  the rows, each labeled *"applies to all sizes of ⟨piece⟩"*.
  `+ Add Pattern Design` (register, labeled all-sizes). Unknown size →
  404; worker → 403; GET writes nothing.

## Facade (contract-additive only)
Per-section: `ready` · `required_missing` · issues-first row order.
Per-row: `area_cm2` · `updated_at`. Summary: `any_size_ready` (the
gate). `design_key`/existing keys untouched — the CT contract stands.

## Vocabulary
Page/product language: **Pattern Manager** (production button:
"🧵 Open Pattern Manager"). Conscious test updates in M4/M6/W1
(comments mark the W2R rework); W1's two ordering assertions updated
for issues-first (comments).

## Browser (live, real data)
- **T-SHIRT manager**: 4 clean cards, ALL `Ready for Cutting ✓` — the
  law showing itself: Care Label is OPTIONAL, so L/XL are rightly Ready
  at 7/8 — gate ENABLED (`w2r_manager.png`).
- **DEV-HUB manager** (real required gaps): `Needs Attention ⚠` cards
  with `Missing: Cuff` / `Missing: Back Panel, Cuff`, gate **DISABLED**
  with the reason (`w2r_manager_warn.png`); [Manage Pattern Designs]
  click → `?product=19&size=m` library with 4 rows.
- **T-SHIRT library L**: 8 rows, optional Care-Label ghost FIRST
  (issues-first), verdict + counts (`w2r_library_L.png`).
- **Mobile 390×844** both pages: stacked cards, full-width actions,
  no horizontal scroll (`w2r_mobile_manager.png`,
  `w2r_mobile_library.png`).

## Tests — 14 W2R + updated neighbors, 59/59 on the affected block
(first draft of this report said 17 — honest correction: the suite is 14)
Manager: verdict cards + missing names + NO rows law · gate enabled
(≥1 ready) · gate disabled + reason (fixture with a required gap) ·
details sheet + matrix retained · no-sizes state · chooser + worker
403. Library: one-size-only + issues-first + row-count · full-facts row
(version, tape dims, **area**, **DXF url**, **updated**, size-anchor) ·
contextual actions per status · manage-in-place labels · POST works ·
unknown-size 404 + worker 403 · zero-writes. Vocabulary: production
button. (Conscious updates: W1 ordering ×2, M4 button ×2, M6/W1
heading — all commented.)

## Regression
patterns_ai **342/342 OK** (old W2 suite 16 replaced by W2R suite 14) · full manufacturing suite **1227/1227 OK** (serial, fresh) ·
`makemigrations --check`: **No changes detected** · import contracts
**unchanged — 1 kept, 1 broken (pre-existing target)** · zero schema · frozen writers untouched · facade
contract-additive only.

**STOPPED — awaiting approval for W3 (General-size shortcut · perf
unify · vocabulary sweep · PDM acceptance on the real T-SHIRT + stage
close). The Cutting Table remains the next stage after that.**
