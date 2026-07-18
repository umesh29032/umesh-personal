> **ARCHIVED 2026-07-13** — shipped-phase report/review (patterns_ai). Live truth: [PLATFORM_STATUS](../../AI_PATTERN_INTELLIGENCE/PLATFORM_STATUS.md) + [PRODUCT_VISION_V2](../../AI_PATTERN_INTELLIGENCE/PRODUCT_VISION_V2.md) + the app [GUIDE](../../apps/patterns_ai/GUIDE.md). Kept for history (Phase-7 DOCCLEAN-D, D-OR-1). Outbound links reflect its era.

# PLATFORM · PHASE 6C REPORT — Auto Place + AI Optimize
(2026-07-09)

**Status: ✅ 6C COMPLETE — PHASE 6 (the Layout Optimization Engine)
COMPLETE. STOPPED. Phase 7 (Approved Layout Library) will not start
without approval.**

All 8 owner rules honored. ONE engine, reused verbatim — zero engine
code written. Still zero persistence.

## What shipped

**Auto Place ≠ AI — permanently separated (rule 1).**
- **⇓ Auto Place** (workspace header): fast, DETERMINISTIC first-fit —
  area-desc order with stable tie-breaks, same constraint pipeline, no
  randomness, no scoring, no search. Browser-proven determinism: two
  runs from different states → byte-identical coordinates
  (`deterministic:true`).
- **AI Optimize** (toolbar button LIVE — its phase arrived): the
  EXISTING `op:'optimize'` engine through a STATELESS endpoint.

**The endpoint** `table/<pk>/optimize/` (rules 2/3/7): runtime session
in → positions out. Reuses `marker_generation_service.optimize_layout`
verbatim (test-walled WRITES-NOTHING); locked pieces travel as `fixed`
obstacles (rule 4 — the engine's own scope law); grain maps to the
engine's `allow_180` (strict → never rotate; two_way/free → 0/180 —
free's 90/270 freedom = an unused SAFE subset, extension-if-needed
noted, no fork). THE CONTRACT is frozen in the endpoint docstring.

**Honest AI (rule 5)** — all three verdicts live:
- better → apply + "AI improved: +38.06% utilization, −1228 mm length."
- same → "AI found no better layout — current kept." (browser-proven)
- worse → "AI could not improve this layout — current kept."
Plus one more honesty: the engine GUARANTEES no-overlap but its spacing
is best-effort padding — when an applied layout has spots tighter than
the spacing rule, the amber channel shows them and the verdict message
says "n spot(s) tighter than the 3 mm rule — nudge if needed." Never
hidden, never silently relaxed.

**Stages (rule 6):** `Draft → Optimized → (P7) Approved → (P8)
Manufacturing` — a real state machine: AI improvement sets
"Optimized (unsaved)"; ANY operator change reopens "Draft"; the code
carries the literal comment "never 'approved' — human-only".

## The bug my own browser run caught (the milestone's real work)
First AI runs returned "no improvement" on obviously wasteful layouts.
Empirical shell probe against the engine exposed a **coordinate-frame
mismatch**: the engine's `polygon_mm` is `[ALONG-length, ACROSS-width]`
(a 900-deep stack measured `length 310` — first coord = the free axis),
while the workspace world is x-across/y-down. The client now swaps the
frame on send (`toEngineRing`) and swaps back on apply; world mm stay
the only truth. Second catch: integer-rounding applied positions shaved
engine-exact 3.0 mm gaps under the rule → keep 2 dp. After both fixes:
20.6% → 58.0% utilization on the real T-Shirt.

## Tests
NEW `test_phase6c_ai.py` (4): REAL-engine stateless call (row counts
identical across the call — THE zero-writes proof) + response contract
keys · all-locked → honest 400 "locked" (rule 4) · bad JSON 400 / GET
405 / worker 403 · chrome: Auto-vs-AI separation + stage machine +
human-only approval stated in source. Conscious updates (commented
"6C"): toolbar tests ×2 (AI Optimize span → live button).

## Battery (counts from output, serial, fresh — after all fixes)
patterns_ai **398/398** (394+4 exact) · full **1283/1283** (1279+4
exact) · `--check` No changes (zero-migration phase) · contracts
1 kept/1 broken pre-existing baseline.

## Browser (live, REAL T-SHIRT, real engine ~30–40 s per run)
- Auto Place: deterministic (identical coords twice) · 0 violations ·
  58.0% util.
- AI on a wasted layout (piece dragged 230 mm down, one piece LOCKED):
  `"AI improved: +38.06% utilization, −1228 mm length."` · util
  20.6% → 58.0% · locked piece transform byte-identical · stage
  `Optimized (unsaved)` (`p6c_ai_live.png` — the AI-packed marker).
- Same-verdict path: "AI found no better layout — current kept."
- Endpoint probe: 200, `orderings_tried: 8`, deltas born server-side.

**STOPPED — Phase 6 complete (6A physics · 6B manual · 6C auto+AI).
Phase 7 (Approved Layout Library: Save · Approve · Freeze · History ·
Versions · DXF · PDF — the first PERSISTENCE since the DCT began)
awaits your approval.**
