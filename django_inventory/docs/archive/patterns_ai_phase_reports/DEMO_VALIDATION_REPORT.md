> **ARCHIVED 2026-07-13** — shipped-phase report/review (patterns_ai). Live truth: [PLATFORM_STATUS](../../AI_PATTERN_INTELLIGENCE/PLATFORM_STATUS.md) + [PRODUCT_VISION_V2](../../AI_PATTERN_INTELLIGENCE/PRODUCT_VISION_V2.md) + the app [GUIDE](../../apps/patterns_ai/GUIDE.md). Kept for history (Phase-7 DOCCLEAN-D, D-OR-1). Outbound links reflect its era.

# DEV-TEE DEMO VALIDATION REPORT (2026-07-07) — pre-Phase-6

**Purpose: validate the complete production workflow under the 🔒
Product+Size grain ruling. DEV data only — NOT a production feature.
No feature code was written; everything ran through the existing frozen
services and pages.**

## 1. Design verdict first

**The built model already has the Product+Size grain** (ADR-D2):
Pattern Type = `PatternPiece`; Pattern Design = a confirmed
`PieceSizeGeometry` row per (piece-version × `ProductSize`). Zero schema
change. Design docs updated (INTEGRATION_DESIGN §3b + §5.5 readiness
matrix; ROADMAP header).

## 2. The demonstration product (seeded via REAL single-writer services)

**DEV-TEE — Classic Crew Neck T-Shirt (DEV)** · Sizes S M L XL XXL ·
Pattern Types: Front Panel · Back Panel · Left Sleeve · Right Sleeve ·
Neck Rib · Pocket (optional). **30 size-specific Pattern Designs, all
CONFIRMED · MEASURED (tape-accepted)**:
- 25 designs via the legitimate no-photo path: real DXF export→import
  through `import_dxf` + confirm with grain + tape (graded rectangles,
  e.g. Front L = 540×730 mm).
- Pocket = the photo path proof: synthetic golden capture on the new
  **MAT-DEV-02** (1.4×1.0 m spec, tape-commissioned) through the REAL
  wizard — gate PASSED (residual p95 0.0385 mm) → accept → confirm
  (tape 130×140) → **MEASURED**; then M–XXL completed via
  **copy-forward v2** + DXF imports.
- Honest note on "photos: public reference images": real downloaded
  photos cannot pass the metrology gate (no calibration mat in them) —
  the gate exists precisely to refuse such images. Synthetic goldens
  with known mm truth are the honest stand-in until the physical mat
  (D7) exists.

## 3. Workflow validations (fabric width 990 mm ≈ 39", initial length 2000 mm)

| Test | Result |
|---|---|
| **Missing-design detection** (Pocket had no designs) | Generate refused BEFORE any layout: **"confirmed geometry missing — Pocket (no confirmed version)"** — exact, honest, no guessing. After Pocket S existed but M–XXL didn't, the same refusal named the specific sizes. The tool never invents designs. ✓ |
| **Single-size layout (L×1)** | 6 pieces auto-loaded from L geometry (user never picked pieces) → **minimum required fabric = 1707.0 mm**, verified, both methods within 0.5 mm of each other. ✓ |
| **Custom production mix (S×2 M×3 L×4 XL×1 XXL×1 = 11 garments)** | 66 size-correct pieces auto-loaded → **minimum required fabric = 15,094.5 mm @ 75.98% utilization, verified**. ✓ (see finding F1) |
| **Manual editing** | L layout opened in the editor at height 2000 ("fits fabric"), pocket dragged + locked. ✓ |
| **AI optimization honesty chain** | With the pocket locked and height 2000, optimize **refused honestly**: "couldn't fit within the fabric height — unlock…, shorten…, or increase the height." Height 2400 → options returned, **badged "Worse than Current"** (the untouched 1707 layout was already tighter — truth over flattery). ✓ |
| **Keep + Save** | Option kept (2039 mm, fits) → **"Layout saved (2039.0 mm, verified)"** → editing the saved version. ✓ |
| **Current Production Layout** | Validated as the latest saved layout (the smart-redirect #2 case). The explicit "Approve for production" act = **Phase 6 item 4, not yet built** — stated honestly. |
| **Export** | Layout SVG: 200 · `image/svg+xml` · 6 polygons. ✓ (PDF + full-marker print = Phase 6.) |

Screenshots: `tee_missing_refusal · tee_single_L · tee_editor_2000 ·
tee_optimized`.

## 4. Findings (honest, for Phase 6)

- **F1 — BLF scale envelope (REAL finding):** the 66-piece mix TIMED OUT
  on the grid-BLF path (no internal timebox; placement scan cost grows
  with marker length × piece count). The SVGnest path handled it
  (internally timeboxed, 15.1 m verified). **Phase-6 hardening item:
  BLF needs an internal timebox (honest give-up) — and the practical
  envelope documented (BLF ≈ small/medium layouts + the lock-respecting
  optimizer; SVGnest = large mixes).** This also bounds the in-editor
  optimizer for very large mixed markers (it is BLF-based when locks
  exist) — same honest-refusal behavior applies.
- F2 — a browser crash mid-test lost one form submit (environment, not
  product); rerun through the identical service path succeeded.

## 5. Conclusion

The Product+Size grain works end-to-end on realistic data with zero
schema change: size-specific designs load automatically, missing designs
block generation with exact names, mixed production scenarios produce
verified minimum-fabric answers, and the edit→optimize→save→export loop
holds with every honesty behavior intact. **Phase 6 list gains F1
(BLF internal timebox) alongside its existing items. STOPPED.**


## 6. ADDENDUM — realistic outlines upgrade (2026-07-07, owner §6 v2)

Rectangles replaced with **realistic garment outlines** for all 30
designs, entirely through the existing frozen services (copy-forward →
`edit_draft_geometry` per size → confirm with grain + tape): Front/Back
panels with shoulder slopes, armhole curves and neck scoops (front deep,
back shallow) · set-in sleeve caps · curved neck-rib strip · pentagon
pocket. All CONFIRMED · MEASURED — and the **tape gate caught a real
authoring bug during the upgrade** (my front outline measured 675 mm
where I claimed 690 — confirmation refused until the tape told the
truth; tape is now the ring's measured bbox).

**Result:** the L-size tee now nests to **1291 mm (70.54% utilization)
vs 1707 mm for the rectangle version** — curved outlines interlock, which
is the whole point of real nesting. Editor screenshot
(`tee_realistic_editor.png`) shows actual garment shapes on the canvas:
fits fabric, 0 collisions.

**Reference images (owner §6):** the display-only reference-image field
does not exist yet — it is Phase-6 item 7 (INTEGRATION_DESIGN §3c).
Attaching public images today would either bypass the metrology gate or
falsely enter the geometry path; deferred honestly rather than faked.
