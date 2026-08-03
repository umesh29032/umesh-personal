---
id: docs-ai-pattern-intelligence-phase5-m1-report
type: receipt
status: active
owner: append-only
scope: patterns_ai
anchors: config/patterns_ai/
verified: 2026-07-18
---

# Phase 5 · Milestone 1 REPORT — Optimization engine op (2026-07-07)

**Status: ✅ M1 COMPLETE — STOPPED. M2 will not start without approval.**

## Implementation summary

`op:"optimize"` in the isolated runtime, exactly per DESIGN v4 + the two
approved corrections:

- **Obstacles:** fixed pieces (locked + out-of-scope) are pre-rasterized
  (spacing-buffered) into the BLF occupancy mask — structurally
  immovable; their input dicts pass through to every option verbatim
  (byte-identical, test-asserted).
- **Search:** free pieces placed around the obstacles across K seeded
  orderings (area-sort first, then seeded shuffles); effort map
  Fast/Balanced/Best = 8/30/80 orderings with 3/10/30 s timeboxes.
- **Correction 1 — ranking:** invalid options discarded FIRST (overlap /
  outside width via THE existing verifier on fixed+free together ·
  outside height · moved-fixed impossible by construction and passed
  through verbatim); then valid options sort **utilization desc
  (0.01 %-pt tolerance bucket) → length asc → compactness tie-break
  LAST** (free-centroid spread; provably unable to beat the first two —
  it is the third sort key).
- **Correction 2 — determinism:** fixed iteration order, seeded RNG, no
  wall-clock in results (the timebox only caps ordering count, itself
  deterministic per effort). Test compares **complete returned
  placements JSON**, not metrics.
- De-duplication of identical free layouts; `options_wanted` clamped
  1–8; honest refusals: nothing free ("everything is locked or out of
  the selection"), piece wider than fabric, nothing fits the height
  ("unlock or deselect more pieces, shorten the layout, or increase the
  height") with drop counters reported.

## Changed files
- `compute/patterns_ai/nest.py` — `run_optimize` + `op` dispatch +
  `EFFORT_MAP` + obstacle raster + free-placement pass + compactness
  helper (existing generate/verify ops untouched; vendored code
  untouched).
- `config/patterns_ai/tests/test_phase5_engine.py` — NEW.

## Test results
- **M1 suite: 13/13 OK** (real runtime through the real bridge):
  fixed byte-identical · every option verifier-clean (0 mm² overlap,
  within width) · only free moved, rotations ∈ {0°,180°} · height
  refusal honest with drop counts · too-wide piece refused · empty scope
  refused · **full-placement seed determinism** · cross-seed validity ·
  ranking law asserted pairwise on returned order (utilization bucket →
  length → compactness) · compactness-never-beats-length adversarial
  pass · options_wanted + dedupe · effort search-size ordering + unknown
  effort refused · ≥ spacing gap to the obstacle verified geometrically.
- patterns_ai suite + full manufacturing suite: fresh serial run —
  see regression below.

## Engineering review (hostile pass)
- One verification home preserved: options are validated by the SAME
  `verify_layout` as generation and workspace saves.
- Obstacle raster reuses the proven `_blf_variants`/grid conventions —
  no new geometry math beyond the centroid-spread tie-break.
- Determinism audited: no `time`-dependent branching inside result
  construction; RNG isolated to ordering shuffles.
- Cost: worst case (Best) ≈ 80 obstacle-aware BLF passes — seconds at
  real piece counts; obstacle mask built ONCE per run.
- **Limitation discovered (documented, per discipline):** with locks
  present the search is BLF-only (the vendored nesting core cannot seed
  pre-placed parts without modifying vendored code — stated in the
  design). A denser fixed layout can therefore yield fewer distinct
  options; the drop counters make this visible rather than silent.
- **Future Improvements (NOT implemented):** none proposed beyond the
  design; no design deviations occurred.

## Regression
patterns_ai **201/201 OK** (188 + 13 M1) · full manufacturing suite
**1086/1086 OK** (serial, fresh) · `makemigrations --check`: No changes
detected (zero schema, model pin 15) · import-linter unchanged (the 1
broken = the pre-existing tracking.tests target) · vendored code
untouched · Django venv untouched.

**STOPPED — awaiting approval for M2 (compute-only service + workspace
AJAX endpoint).**
