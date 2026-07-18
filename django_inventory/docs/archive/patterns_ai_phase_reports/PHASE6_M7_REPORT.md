> **ARCHIVED 2026-07-13** — shipped-phase report/review (patterns_ai). Live truth: [PLATFORM_STATUS](../../AI_PATTERN_INTELLIGENCE/PLATFORM_STATUS.md) + [PRODUCT_VISION_V2](../../AI_PATTERN_INTELLIGENCE/PRODUCT_VISION_V2.md) + the app [GUIDE](../../apps/patterns_ai/GUIDE.md). Kept for history (Phase-7 DOCCLEAN-D, D-OR-1). Outbound links reflect its era.

# Phase 6 · M7 REPORT — Approve UI + Production Layout Summary (§3f/§3g)
(2026-07-07)

**Status: ✅ M7 COMPLETE — STOPPED. M8 will not start without approval.**

No architecture change: the UI orchestrates the FROZEN
`approve_production_layout` single-writer; the summary is facts +
derived-at-read (`derive_candidate_metrics` — nothing stored); zero
models, zero migrations (pin 17).

## What was built
- **Production Layout Summary (§3f)** on every saved-layout page:
  Fabric width (fact) · Required layer length (fact) · Utilization/Waste
  (derived at read, labeled) · Pattern count (derived) · Size ratio
  (fact). Green ★ variant when the layout IS the production layout,
  with the audit line (approved by / at) and the history promise.
- **The explicit Approve act (§3g + owner refinement 5)** — TWO steps:
  1. `★ Approve for production…` on the layout page → the REVIEW page
     (`/candidates/<pk>/approve/`): the same summary read BEFORE the
     act + an honest statement of consequence ("replaces #X — the
     replaced layout is NOT deleted, it stays in the switcher history";
     or "becomes the FIRST production layout"), verified-status shown.
  2. Explicit POST → the frozen writer moves the pointer → back on the
     layout page with the ★ banner.
  Never bundled with Save; the GET review step writes nothing (tested).
- Unverified layouts: no approve button, honest note; POST refused by
  the service with the message surfaced. Re-approve = service no-op +
  "already the production layout — nothing changed" (audit preserved).
- ★ flows everywhere automatically (no new code): editor context strip,
  Layout switcher head, smart-redirect priority 1, Rule-E log reason.

## Browser walkthrough (DEV-TEE, live)
1. Layout #12 page: Summary panel — 990 mm · 1291.09 mm · 70.53% /
   29.47% · 6 pieces · L×1 · "Current production layout: #11" + Approve
   button (`m7_summary_before.png`).
2. Review step: same summary + exactly *"This replaces layout #11 as
   the production layout. The replaced layout is NOT deleted — it stays
   in the Layout switcher history. Saving edits later creates drafts;
   the designation moves only by this explicit act."*
   (`m7_approve_review.png`).
3. POST → back on #12 with **"★ THE production layout — what production
   cuts from"** + audit line (`m7_approved_star.png`).
4. Everything flipped live: `/patterns/tool/18/` →
   `workspace/12` (`reason="approved layout"` in the Rule-E log);
   context strip `Layout #12 · ★ Production`; switcher now
   `★ Production · #12 ~ Draft · #11 ~ Draft · #10 …` — the replaced
   #11 honestly reachable in history.

## Test results
- **M7 suite 10/10** (9 + 1 runtime-gated): summary values match
  `derive_candidate_metrics` exactly · unverified hides approve ·
  review-step-before-approve (GET writes nothing) · approve moves
  pointer + audited + ★ banner · replace names the old pointer, moves,
  old layout intact and re-approvable · re-approve no-op with honest
  message (approved_at unchanged) · unverified POST refused · worker
  403 (GET+POST) · ★ flips in workspace + switcher head ·
  **§3g law: `save_manual_layout` after approve leaves the designation
  byte-untouched while creating the new draft** (runtime-verified).
- Two test-only fixes (test bugs): an assertion spanned a template
  line-wrap; `save_manual_layout` returns `(run, candidate)` — the test
  forgot to unpack.

## Regression
patterns_ai **311/311 OK** (301 + 10 M7) · full manufacturing suite **1196/1196 OK** (serial, fresh) ·
`makemigrations --check`: **No changes detected** · import contracts **unchanged — 1 kept, 1 broken (pre-existing target)** ·
zero migrations (pin 17) · frozen M3 services untouched · legacy Marker
promotion blocks untouched (frozen-legacy, per the Legacy Code Report).

**STOPPED — awaiting approval for M8 (exports: PDF page-1 summary +
tiled true-scale print + summary stamping). Acceptance validation stays
owner-held until after M9, per instruction.**
