> **ARCHIVED 2026-07-13** — shipped-phase report/review (patterns_ai). Live truth: [PLATFORM_STATUS](../../AI_PATTERN_INTELLIGENCE/PLATFORM_STATUS.md) + [PRODUCT_VISION_V2](../../AI_PATTERN_INTELLIGENCE/PRODUCT_VISION_V2.md) + the app [GUIDE](../../apps/patterns_ai/GUIDE.md). Kept for history (Phase-7 DOCCLEAN-D, D-OR-1). Outbound links reflect its era.

# Phase 6 · M3 REPORT — single-writer services (frozen contract)
(2026-07-07)

**Status: ✅ M3 COMPLETE — STOPPED. M4 will not start without approval.
The service architecture is FROZEN (INTEGRATION_DESIGN §3i).**

## Final frozen service API

```python
# services/fabric_profile_service.py — sole ProductFabricProfile writer (NEW)
set_fabric_profile(*, user, product, default_width_mm=None,
                   default_length_mm=None, default_spacing_mm=None,
                   fabric_type='', gsm=None, lay_mode='') -> ProductFabricProfile
#   full-replace, idempotent; bounds reuse the generation constants
#   (width 300..3000 mm, length ≤ 100 m, spacing ≥ 0) — one truth.

# services/production_layout_service.py — sole ProductionLayout writer (NEW)
approve_production_layout(*, user, product, layout) -> ProductionLayout
#   Rule A eligibility → pointer move ONLY. Atomic (transaction +
#   select_for_update + OneToOne backstop). Same-layout re-approve =
#   strict no-op; different layout = fresh approved_by/approved_at.

# services/pattern_geometry_service.py — existing PatternPiece writer gains
set_piece_optional(*, user, piece, is_optional) -> PatternPiece
set_reference_image(*, user, piece, asset) -> PatternPiece   # None clears
#   reference image: kind must be reference_image · same product ·
#   STORED (retired/corrupt refused) · display-only forever.

# services/marker_generation_service.py — RENAMED (frozen name)
resolve_generation_geometry(product, ratio) -> (payload, sources, warnings)
#   was collect_confirmed_geometry; resolves required validation +
#   optional per-(piece,size) skipping + warnings + engine payload.
#   start_run persists warnings → run.params['optional_skipped']
#   (additive key; absent = nothing skipped).
```

All writers management-gated. No other write path exists — the I-1
repo-scan wall (knowledge-model `.objects.create/...` outside
`patterns_ai/services/` = test failure) already covers both new models.

## Write-flow diagram

```
                     (M6 Hub)                     (M7 Approve UI)
                        │                                │
        ┌───────────────┼────────────────┐               │
        ▼               ▼                ▼               ▼
set_fabric_profile  set_piece_optional  set_reference_image  approve_production_layout
        │           └────────┬──────────┘               │
        ▼                    ▼                           ▼
ProductFabricProfile    PatternPiece            ProductionLayout ──PROTECT──▶ immutable
 (defaults only,        (flags only)             (pointer + audit)            saved layout
  never touches                                                                    ▲
  any layout — Rule B)                                                             │
                                                                                   │
Generate ──▶ start_run ──▶ resolve_generation_geometry ──────────────────────────┘
              │   (required missing ⇒ BLOCK by name ·
              │    optional missing ⇒ skip per (piece,size) + warning)
              ▼
        run + candidates (immutable, append-only; warnings persisted
        in run.params['optional_skipped'] — never silent, even historically)
```

## Engineering review (10 rules + Rules A/B)

1. **One writer per table** — mechanical: I-1 wall test; new writers live
   inside `services/`; zero view writes anywhere.
2. **Approve atomic** — `@transaction.atomic` + `select_for_update` on the
   designation + OneToOne unique constraint as the DB race backstop
   (get_or_create retries on IntegrityError internally).
3. **Verified-only** — Rule A implemented exactly: product-match ·
   persisted row · `verification.ok` · non-empty placements. No
   deleted/void state exists on saved layouts (append-only, never
   deleted) — stated honestly rather than fake-checked. Approval never
   re-verifies (eligibility reads recorded facts only).
4. **Pointer-only** — test proves the replaced layout row is
   byte-identical AND not even re-saved (`updated_at` unchanged).
5. **Profile ⊥ designation** — separate modules, neither imports the
   other; Rule-B test changes the profile and asserts run params,
   placements, verification, length and the designation all byte-stable.
6. **Optional honesty** — required blocks by name (unchanged assertion);
   optional skips per (piece, size) with exact warning text; warnings
   persisted in the run's reproducibility spine; `on_fold` still blocks
   even for optional pieces; all-skipped still raises "nothing to nest".
7. **Reference images doc-only** — setter refuses wrong kind /
   cross-product / retired; extraction's kind gate stays source-pinned
   (M2 test); generation reads `PieceSizeGeometry` only.
8. **Idempotent** — same-profile call → same row/values; same-layout
   re-approve → strict no-op (even by a DIFFERENT manager — the
   first-approval audit fact is preserved); piece setters no-op on equal
   state.
9. **No god service** — two new focused modules; generation service
   gained ZERO new responsibilities (rename + semantics only).
10. **API review honored** — F-1..F-6 implemented as approved; the
    rename (`resolve_generation_geometry`) chosen for expressing the
    full responsibility. Grep proves zero stale `collect_confirmed_geometry`
    callers (it was only ever called by `start_run`; no test/view used it).

## Test results
- **M3 suite 21/21** (19 pure-DB + 2 runtime-gated): profile
  set/replace/idempotent/one-row · bounds refusals (width/length/
  spacing/gsm) · gate · **Rule-B byte-identity** · approve happy/audited ·
  **all four Rule-A refusals** (unverified · empty · cross-product ·
  unsaved) · **strict no-op re-approve** · move-with-fresh-audit +
  replaced-layout-untouched · gates · optional toggle idempotent ·
  reference image happy/clear/3-refusals · required-blocks-by-name ·
  optional-piece skip + warning · **per-(piece,size) skip** (M pockets
  cut, XL pocket skipped) · optional-with-designs = no warning ·
  on-fold-blocks-even-optional · all-skipped honest ·
  `run.params['optional_skipped']` persisted · no-skip = no key.
- Two fixture-only fixes during the run (test bugs, not service bugs):
  retired-asset fixture needed `status_reason` (DB CheckConstraint);
  Rule-B snapshot taken before `refresh_from_db` compared `100` vs DB
  `100.00`.

## Browser validation
N/A per plan (service-level milestone — no UI until M4+). The honest
optional-skip note reaches the UI in M5/M6; it is already persisted and
returned from the service today.

## Regression
patterns_ai **256/256 OK** (235 + 21 M3) · full manufacturing suite **1141/1141 OK** (serial, fresh) ·
`makemigrations --check`: **No changes detected** · import contracts: **unchanged — 1 kept, 1 broken(pre-existing target)**
(patterns_ai in zero violations; the broken "target" layering contract =
pre-existing manufacturing-apps aspirational, unchanged) · zero
migrations this milestone (pin stays 17) · vendored code untouched.

**STOPPED — awaiting approval for M4 (smart redirect + entry button).**
