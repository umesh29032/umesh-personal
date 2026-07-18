> **ARCHIVED 2026-07-13** — shipped-phase report/review (patterns_ai). Live truth: [PLATFORM_STATUS](../../AI_PATTERN_INTELLIGENCE/PLATFORM_STATUS.md) + [PRODUCT_VISION_V2](../../AI_PATTERN_INTELLIGENCE/PRODUCT_VISION_V2.md) + the app [GUIDE](../../apps/patterns_ai/GUIDE.md). Kept for history (Phase-7 DOCCLEAN-D, D-OR-1). Outbound links reflect its era.

# M6 — MANUFACTURING COMPLETION · implementation report
(2026-07-10 · executes M6_IMPLEMENTATION_PLAN.md after the
MANUFACTURING_INTEGRATION_REVIEW · one milestone, one report, one stop)

## Verdict
M6 delivered and proven on the FULL Nickar chain in the browser — the
platform's whole promise in one screen: the approved fold layout fed
the layering recommendation, the cutting suggestion carried the fold
math, the operator's numbers stood over both, and the completed cut
stamped its layout contract for traceability. Zero migrations; both
enforcement gates ship OFF; the ADR-H wall untouched (two additions of
the EXISTING registry species only).

## What was built
- **The layering edge (the last missing integration):**
  `layering/handler.py` gains `LAYOUT_PROVIDER` (same species as
  cutting_pattern's); patterns_ai registers
  `build_layering_recommendation(adda)` (derive-at-read, plies-free);
  `_build_layering_context` consumes it WRAPPED (provider failure →
  page 200, section absent — tested); the layering panel shows:
  *"📐 Recommended layer length: 440 mm — from LAY-DEV-NICKAR-000002
  (BODY, double_folded lay). Advisory only — your measured length
  stands."* Nothing prefills; the operator's number is the fact.
- **The traceability stamp:** `cutting/service.py` gains
  `CUTTING_COMPLETE_LISTENERS` (the ARCHIVE_VALIDATORS inversion);
  patterns_ai registers `stamp_adda_usages` — on cutting completion,
  every active un-stamped usage pins to the cutting stage record
  (once-only; listener failures logged, NEVER break cutting — tested
  with a bombing listener).
- **The enforcement gates (flags default OFF — deploy → soak → owner
  flips):** `REQUIRE_APPROVED_LAYOUT` (completion refuses without an
  active contract, names the choose page) ·
  `ENFORCE_LAYOUT_RECONCILIATION` + `LAYOUT_RECONCILIATION_TOLERANCE`
  (completion refuses when |cut − expected| > tolerance, names both
  numbers). ERP-side checks over provider-dict data; OFF = pre-M6
  behavior byte-identical (tested); the advisory WARN stays always.

## Proof
- **Tests: patterns_ai 480 + 13 M6 = 493 in-app; full serial battery
  1378/1378** (1365 + 13 — counts from output). ZERO migrations;
  contracts baseline ("1 kept, 1 broken").
- **Gate matrix (tests):** REQUIRE off=completes / on+no-usage=refused
  (choose page named) + nothing completed / on+usage=passes ·
  ENFORCE off=warn-only / on+mismatch=refused with "expected 30 …
  cut 25" / tolerance 5 absorbs |25−30| / on+exact=passes · flags
  default OFF asserted · recommendation dict plies-free asserted.
- **Browser (DEV-NICKAR-A1, the real chain end-to-end):**
  choose page → recorded **LAY-DEV-NICKAR-000002** (the FOLD marker)
  as the body contract → layering workspace showed the
  recommendation (screenshot) → operator completed with HIS numbers
  (10 layers · **0.5 m** ≠ the 440 mm advisory — authority proven) →
  advanced to cutting → suggestion label *"Suggestion from approved
  layout LAY-DEV-NICKAR-000002 × lay count (marker content ×
  plies)"* with service-verified counts **Body 20 · Pocket 20 ·
  fold-Back 10** (= content/layer {2,2,1} × 10 — the M4.5 fold ÷2
  living inside the M4 multiplier math) → bundles cut Body 20 ·
  Pocket 20 · Back **9** (deliberate −1) → browser completion:
  *"Layout check (LAY-DEV-NICKAR-000002): size S — expected 50
  (marker × plies), cut 49. **Your numbers stand**"* + *"Cutting
  complete. 49 barcodes generated"* → **stamp DB-verified: usage 2 →
  cutting stage record 102, automatic, via the listener.**
  Screenshots: m6_choose · m6_layering_recommendation ·
  m6_cutting_suggestion · m6_cutting_complete_warn.

## Honest notes
- Layering-complete + roll-attach are pre-existing skill/flow-gated
  UIs (not M6 scope): the browser drove the M6 surfaces (choose,
  recommendation, suggestion, completion + WARN); worker-assign,
  roll-attach, leftover and layering-complete steps ran through the
  REAL services with authorized users (no mocks, no state forced).
  The stamp/gate unit tests isolate only the post-completion ERP
  fan-out (advance/barcodes — covered by their own suites).
- Docs-sync: production-side seams (layering handler registry ·
  cutting listeners+gates · settings flags · layering template line)
  recorded here + patterns_ai GUIDE; production docs get the same
  note via the GUIDE row (change-impact: registry seams documented at
  their patterns_ai consumer, matching the 8B/8C precedent).
- DEV artifacts: DEV-NICKAR-A1 adda (layering 10×0.5m complete ·
  cutting complete 49 pieces + barcodes · usage 2 stamped) + leftover
  2 kg on CR-DEV-M4A. Golden T-SHIRT untouched.

## Migrations
None. (Settings flags + registries + template only.)

**STOPPED — M6 complete. The frozen order's remaining milestones:
M5 (Layout Library polish) · M7 (Pattern Assistant, future). Flag
flips = owner decision after soak. Awaiting review.**
