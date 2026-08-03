> **ARCHIVED 2026-07-13** — shipped-phase report/review (patterns_ai). Live truth: [PLATFORM_STATUS](../../AI_PATTERN_INTELLIGENCE/PLATFORM_STATUS.md) + [PRODUCT_VISION_V2](../../AI_PATTERN_INTELLIGENCE/PRODUCT_VISION_V2.md) + the app [GUIDE](../../apps/patterns_ai/GUIDE.md). Kept for history (Phase-7 DOCCLEAN-D, D-OR-1). Outbound links reflect its era.

# PLATFORM · PHASE 8C REPORT — expected pieces + advisory reconciliation
(2026-07-10)

**Status: ✅ 8C COMPLETE — STOPPED. 8D (enforcement, flags default OFF)
will not start without approval.**

The manufacturing contract is now the numbers source — as ADVICE. The
owner's count hierarchy is code: content from the layout, plies from
layering, expected = advisory only, the operator always wins.

## What shipped

**The count hierarchy, structurally separated:**
1. **Marker Content** — the provider now returns
   `content_by_pattern_size` (per-pattern × per-size counts derived
   from the stored placements; piece→pattern resolved patterns_ai-side).
   A test asserts the provider payload contains NO plies/lay_count/
   expected keys — patterns_ai never touches plies (hierarchy #2).
2. **lay_count** — production multiplies by ITS OWN
   `LayeringRecord.lay_count` inside the cutting service.
3. **Expected** — computed in `get_suggested_breakup` (marker branch)
   and `layout_reconciliation`; persisted NOWHERE.

- **Suggestion**: with an active usage → rows = content × lay_count ÷
  colors, per (pattern, size, color) — the marker's own granularity, no
  assignment math. The classic formula is the UNTOUCHED fallback (no
  usage / no provider / provider failure → silent fallback, tested).
  Same return shape; the workspace label is honest:
  *"Suggestion from approved layout LAY-… × lay count (marker content ×
  plies)"* vs the classic wording.
- **Advisory reconciliation** (`layout_reconciliation`): expected per
  size vs Σ live bundle items per size (colors summed — the stated
  grain). Surfaced as WARNING messages after successful completion:
  *"Layout check (LAY-…): size S — expected 30 (marker × plies), cut
  25. **Your numbers stand**; verify against the marker if
  unexpected."* Never blocks, never writes, never edits operator input.
- Zero migrations · zero flags flipped · barcode code untouched
  (refinement 4: it still consumes Breakdown only).

## Tests
NEW `test_phase8c_expected.py` (5): provider = CONTENT-only (plies-free
payload asserted) · source label formula↔layout flip · marker-branch
hand math (3/marker × 12 plies = 36) + fallback intact without usage ·
reconciliation math (expected 20, actual 0, mismatch listed; None
without contract/layering) · exploding provider → silent formula
fallback. All green after fixture fixes (LayeringRecord requires
total_colors/duration; rolls_used = ClothRoll M2M with the
type/color/location/date idiom from the house fixtures).

## Battery (counts from output, serial, fresh)
patterns_ai **424/424** (419+5 exact) · full **1309/1309** (1304+5
exact) · `--check` No changes (zero-migration milestone) · contracts
1 kept/1 broken pre-existing baseline.

## Browser (live — DEV chain only; golden T-SHIRT untouched)
Extended `DEV-P8B-A1`: layering (lay_count 15, one black roll) +
cutting stage. Marker = 2×S pieces.
- Service math live: suggestion `[{pattern, S, black, count: 30}]`
  (2 × 15) · source `{'kind': 'layout', 'uids': ['LAY-DEV-P8B-000001']}`
  · recon expected {S: 30}.
- **The workspace label** (`p8c_suggestion_label.png`): *"Informational
  only. Suggestion from approved layout **LAY-DEV-P8B-000001** × lay
  count (marker content × plies)."* — the contract feeding the numbers,
  named.
- **The WARN, end-to-end**: bundled 25 (deliberate mismatch) → HTTP
  complete → success + *"Layout check (LAY-DEV-P8B-000001): size S —
  expected 30 (marker × plies), cut 25. Your numbers stand…"*
  (`p8c_warn_complete.png`) — and the frozen breakdown row reads
  **25, the operator's number**: verified in DB. Advisory law, lived.

**STOPPED — 8C done and verified. 8D (the two flags, default OFF: the
pattern-stage gate + reconciliation enforcement + the stage-record
stamp + the full-chain E2E) awaits your approval.**
