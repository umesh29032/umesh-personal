> **ARCHIVED 2026-07-13** — shipped-phase report/review (patterns_ai). Live truth: [PLATFORM_STATUS](../../AI_PATTERN_INTELLIGENCE/PLATFORM_STATUS.md) + [PRODUCT_VISION_V2](../../AI_PATTERN_INTELLIGENCE/PRODUCT_VISION_V2.md) + the app [GUIDE](../../apps/patterns_ai/GUIDE.md). Kept for history (Phase-7 DOCCLEAN-D, D-OR-1). Outbound links reflect its era.

# Phase 6 · M6 REPORT — the Pattern Design Hub (Rules J/K/L/M/N)
(2026-07-07)

**Status: ✅ M6 COMPLETE — STOPPED. M7 will not start without approval.**

Rules J–N conflict-checked — **no conflicts with the frozen
architecture**: everything is derived-at-read UI; every write posts to a
frozen M3 single-writer; ZERO models, ZERO migrations (pin stays 17),
zero service-API changes. Locked into INTEGRATION_DESIGN **§2d** before
coding.

## What was built
- **The Hub** (`/patterns/pieces/?product=N` — the library page reborn):
  product-first hero ("Product Setup · <name>"), completion dashboard,
  blockers/warnings panels, readiness matrix, piece-first cards,
  reference-image UI, fabric-defaults panel. Without a product param the
  page is a **chooser, never a filter** (Rule C honored — the product
  dropdown is gone).
- **Rule J dashboard** — derived ONLY (`_hub_readiness`, computed per
  request from pieces → latest confirmed version → per-size rows;
  nothing stored, F6): the 9-item checklist (Sizes · Pattern Types ·
  Required Pieces · Confirmed Geometry · Grain · Fold Rules · Reference
  Images · Optional Pieces · Fabric Profile) + **Readiness %** +
  **Production Ready ✅** (only when zero blockers).
- **Rule K piece-first cards** — each card: badges
  (required/optional/pair/on-fold), per-size chips, reference image
  block, and ONE **Next step** ("Capture or import geometry" → "Add XL
  geometry" → "Confirm the drawn sizes" → "Add a reference image" →
  "Ready ✓") — the ladder is unit-tested.
- **Rule L validation before Generate** — blockers (red panel, ✗) vs
  warnings (amber panel, ⚠), exact names ("Back Panel — missing XL
  geometry" · "Cuff — M, XL drawn but not confirmed" · "Pocket — missing
  M, XL (optional: skipped honestly, never blocks)"). The SAME matrix
  partial renders on the Generate page (§3b satisfied); generation's
  honest refusal stays the backstop.
- **Rule M reference images** — labeled "display only — never geometry"
  everywhere; large-preview **zoom lightbox** (whitelisted 1024px
  rendition — the original is still never served, per the existing
  security stance); **Add / Replace / Remove** through
  `store_capture(kind=reference_image)` + `set_reference_image` (the
  frozen writers); replacing moves the pointer, the old asset stays
  immutably stored.
- **Optional/Required UI** — one-click toggle per card (frozen
  `set_piece_optional`) + an *Optional piece* checkbox at registration
  (the view calls the frozen create API, then the setter — no API
  change).
- **Rule N** — the page itself is the guide: hero states the workflow,
  every card names its next step, every issue is named exactly, the
  Ready banner offers the two next actions (Open Layout Tool ·
  Generate).

## DEV-TEE walkthrough — the permanent golden demo (browser, live data)
Populated via the frozen writers: **Pocket → optional**, **6
self-rendered reference images** (drawn with PIL from each piece's own
confirmed geometry — license-safe, per the owner refinement), fabric
profile already present from M5.
Result on screen: **100% · Production Ready ✅ · checklist 9/9 ✓ ·
matrix 30/30 green cells · 6/6 piece cards "Ready ✓" · 6 reference
thumbnails** (screenshot `m6_devtee_ready.png`). Zoom lightbox opens the
1024px rendition and closes on click (`m6_lightbox.png`).

## Validation walkthrough — DEV-HUB (deliberately incomplete demo product)
Created DEV-HUB (pk 19): Front Panel complete, Back Panel M-only,
Cuff drawn-not-confirmed, Pocket optional with nothing.
On screen: **27% · In preparation**, blockers panel = exactly
`Back Panel — missing XL geometry`, warnings panel = 6 honest lines
(not-confirmed · missing references · optional-skips), checklist shows
✗ Required Pieces (3/6), ⚠ Confirmed Geometry (2 drawn awaiting
confirm), ⚠ Reference Images 0/4 (screenshot `m6_devhub_incomplete.png`).
The Generate page for DEV-HUB carries the same matrix with 3 missing
cells + a link back to the Hub (`m6_generate_matrix.png`).

## Readiness walkthrough (how % is derived — explainable, never stored)
`done / total` where total = required (piece×size) cells + one
reference-image point per piece + one fabric-profile point; done =
confirmed required cells + illustrated pieces + profile-set.
**Ready = zero blockers** (all required cells confirmed · sizes exist ·
pieces exist · no on-fold pieces). Drafts count toward NOTHING (they are
warnings) — mirrors generation truth exactly (latest CONFIRMED version
only, same as `resolve_generation_geometry`).

## Test results
- **M6 suite 19/19**: empty-product not-ready · exact blocker naming ·
  draft=warning-not-done · optional=warning-never-blocker ·
  on-fold-blocks-even-optional · full-product = ready+100% · **Rule-K
  next-step ladder** · dashboard+matrix render · Rule-C
  chooser-vs-no-selector · Generate-page matrix · GET-writes-nothing ·
  worker 403 (GET+POST) · optional toggle roundtrip · **reference
  upload → replace (pointer moves, old asset immutable) → clear** ·
  uploaded kind forced to reference_image · cross-product piece tamper
  404 · profile save + prefill display · profile bad-value honest error ·
  registration checkbox wires through.
- Two test-only fixes (test bugs): my ladder fixture accidentally
  CONFIRMED the XL-only version (which correctly became the latest
  confirmed truth — the helper mirrors generation semantics); the
  synthetic PNG compressed below the capture door's 1 KB minimum
  (stored-level zlib fixed it).
- One infra addition: thumbnail renditions accept a whitelisted size
  (320 default, 1024 for the lightbox) — original never served,
  backward-compatible.

## Regression
patterns_ai **301/301 OK** (282 + 19 M6) · full manufacturing suite **1186/1186 OK** (serial, fresh) ·
`makemigrations --check`: **No changes detected** · import contracts **unchanged — 1 kept, 1 broken (pre-existing target)** ·
zero migrations (pin 17) · frozen M3 services untouched (orchestration
only) · docs: §2d lock + this report.

**STOPPED — awaiting approval for M7 (Approve UI + Production Layout
Summary). Approve UI / Summary / PDF / print NOT started, per scope.**
