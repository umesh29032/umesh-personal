> **ARCHIVED 2026-07-13** — shipped-phase report/review (patterns_ai). Live truth: [PLATFORM_STATUS](../../AI_PATTERN_INTELLIGENCE/PLATFORM_STATUS.md) + [PRODUCT_VISION_V2](../../AI_PATTERN_INTELLIGENCE/PRODUCT_VISION_V2.md) + the app [GUIDE](../../apps/patterns_ai/GUIDE.md). Kept for history (Phase-7 DOCCLEAN-D, D-OR-1). Outbound links reflect its era.

# M6 IMPLEMENTATION PLAN — Manufacturing completion
(2026-07-10 · follows MANUFACTURING_INTEGRATION_REVIEW §4 — no new
crossing species; architecture FROZEN; flags ship OFF)

## Scope (the three frozen items)
1. **Layering recommendation (the missing edge).**
   `production/stages/layering/handler.py` gains `LAYOUT_PROVIDER =
   None` (same registry species as cutting_pattern). patterns_ai
   ready() registers `build_layering_recommendation(adda)` →
   `{'groups': [{group, uid, length_mm, layering_type}]}` (derive-at-
   read from ACTIVE usages; plies-free). `_build_layering_context`
   calls it WRAPPED (failure → section absent); the layering template
   shows: "Recommended layer length: 440 mm — from LAY-… (double
   folded)". ADVISORY — the operator's `layer_length_meters` stays the
   fact, nothing prefills it silently.
2. **Stage-record stamp.** `production/stages/cutting/service.py`
   gains `CUTTING_COMPLETE_LISTENERS = []` (the ARCHIVE_VALIDATORS
   inversion). patterns_ai ready() registers a stamper: on cutting
   completion, every ACTIVE un-stamped usage of the adda →
   `stamp_stage_record(usage, cutting SR)` (once-only, idempotent;
   listener wrapped so a failure NEVER breaks cutting — logged).
3. **Enforcement gates (default OFF → soak → owner flips).**
   Settings: `REQUIRE_APPROVED_LAYOUT=False` ·
   `ENFORCE_LAYOUT_RECONCILIATION=False` ·
   `LAYOUT_RECONCILIATION_TOLERANCE=0`. Checks INSIDE
   `complete_cutting_from_bundles` (ERP-side, provider-dict data):
   REQUIRE → refuse completion without an active usage, naming the
   choose page. ENFORCE → refuse when any size |cut − expected| >
   tolerance, naming both numbers. OFF = today's behavior
   byte-identical (advisory WARN untouched).

## Not M6
Flag flips (owner, post-soak) · costing/settlement contact (never) ·
multi-factory work · engine changes · UI redesign.

## Tests (~14, patterns_ai/tests/test_m6_bridge.py)
recommendation dict (uid/length/lay, plies-free) · registry wrapped
(provider raises → layering ctx None, page 200) · template line
renders · stamp on completion (once; second completion cycle
idempotent; pre-stamped refused path) · stamper failure never blocks
cutting · REQUIRE off=noop / on+no-usage=refused naming choose /
on+usage=passes · ENFORCE off=warn-only (existing behavior asserted) /
on+mismatch=refused with numbers / on+within-tolerance=passes ·
flags default OFF asserted · golden/legacy untouched.

## Browser (DEV only)
Fresh DEV-NICKAR Adda (workflow layering→cutting; roll assigned) →
choose LAY-DEV-NICKAR-000002 (browser) → layering workspace shows the
recommendation (screenshot) → operator completes layering with HIS
number → cutting workspace suggestion = content × multiplier-baked ×
lay_count → complete cutting → WARN honesty + DB-verified stamp.
Flags stay OFF in the browser (owner policy); ON paths = tests.

## Acceptance
Edge visible + advisory · stamp once-only + failure-isolated · gates
exact + OFF-inert · battery green · browser journey complete.
