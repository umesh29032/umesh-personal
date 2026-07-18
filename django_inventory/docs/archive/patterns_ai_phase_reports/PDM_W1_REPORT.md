> **ARCHIVED 2026-07-13** — shipped-phase report/review (patterns_ai). Live truth: [PLATFORM_STATUS](../../AI_PATTERN_INTELLIGENCE/PLATFORM_STATUS.md) + [PRODUCT_VISION_V2](../../AI_PATTERN_INTELLIGENCE/PRODUCT_VISION_V2.md) + the app [GUIDE](../../apps/patterns_ai/GUIDE.md). Kept for history (Phase-7 DOCCLEAN-D, D-OR-1). Outbound links reflect its era.

# PDM · W1 REPORT — the read-only Design Facade
(2026-07-07)

**Status: ✅ W1 COMPLETE — STOPPED. W2 will not start without approval.**

## What was built (plan §W1 + owner clarifications §0b, exactly)
- **`services/pattern_design_facade.py` (NEW, READ-ONLY)** — the single
  supplier of Pattern Design knowledge; module docstring carries the
  owner's direction verbatim: the CANONICAL Product Design Library
  whose intended consumer is the future Cutting Table; the Generate
  page is a temporary consumer; consumers think in Design Rows.
- **`product_design_library(product)`** — size-first sections
  (size-chart order), every section listing EVERY piece (ghost rows in
  place), plus the product summary (readiness %, ready, checklist,
  blockers, warnings, counts, fabric profile).
- **The Design Row = a complete business object** with the STABLE
  contract (docstring-frozen keys): `design_key` (piece:size — the
  future Available→Selected→Placed identity) · piece + badges · size ·
  status (confirmed/draft/missing) · version_no/version_id ·
  draft_in_progress + draft_version_no (the "v2 draft in progress"
  truth) · geometry_row_id · **outline_mm** (confirmed geometry —
  palette previews AND future composition read THIS) · **dims with
  honesty label** (tape-accepted + measured=True, else bbox + trust
  label) · reference_asset_id (piece-level, shown per row) ·
  next_step. Zero Cutting-Table functionality — contract only.
- **`product_readiness(product)`** — the legacy readiness derivation
  moved VERBATIM into the facade; `views._hub_readiness` is now a thin
  delegate (the old body is retained this session as
  `_hub_readiness_legacy_reference` purely for the parity test; W2
  review may delete it).
- Hub page + Generate-page matrix now read the facade through the
  unchanged wrapper — zero behaviour change (rendering asserted).

## Tests — 10/10, first pass
sections follow the size chart + every piece in every section ·
**the complete-business-object assertion** (all contract fields on
Front·S incl. tape-accepted dims, draft-in-progress v2, reference id,
outline vertex) · unverified dims carry the honest trust label
(Pocket confirmed WITHOUT tape) · ghost row (Pocket·M missing: no
outline, no dims, 'Add geometry', optional badge) · draft-only row
('Confirm the draft', no version_no) · summary counts (3/4 confirmed) ·
sizeless product payload honest · **zero-writes guard** (captured
queries: no INSERT/UPDATE/DELETE) · **verbatim readiness parity**
(pct/ready/blockers/warnings/checklist/rows all equal old vs new) ·
hub + generate pages still render through the reroute.

## Regression
patterns_ai **328/328 OK** (318 + 10 W1) · full manufacturing suite **1213/1213 OK** (serial, fresh) ·
`makemigrations --check`: **No changes detected** · import contracts **unchanged — 1 kept, 1 broken (pre-existing target)** ·
zero schema · zero writers · frozen services untouched.

## Browser
N/A per plan (backend-only milestone; pages proven unchanged by tests).

**STOPPED — awaiting approval for W2 (the Workspace page).**
