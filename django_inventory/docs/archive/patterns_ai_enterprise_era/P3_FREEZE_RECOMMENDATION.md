# P3 FREEZE RECOMMENDATION (2026-07-07)

## Recommendation: **FREEZE P3 — Marker Generation & Optimization — as
delivered.** ✅ (Same discipline as P1/P2: no refactor/redesign without
explicit owner approval; additive evolution only.)

## What is frozen
- **Schema (migration 0006):** MarkerGenerationRun + GeneratedMarkerCandidate
  (append-only, immutable, guarded) + `Marker.candidate` FK; 15-model pin.
- **The generation truth chain:** confirmed-geometry-only input (exact
  row ids snapshotted) → isolated engines → INDEPENDENT verification →
  immutable candidates → HUMAN promotion through `marker_service` with
  frozen benchmark evidence.
- **The beat-the-baseline law:** promotion refuses `does_not_beat`
  verdicts; evidence (theory vs recorded reality, labeled) rides the
  marker's creation event forever.
- **Engine contract:** `nest.py` protocol (job/candidates JSON), vendored
  SVGnest @1248dc2 + BLF floor, seeded determinism, verification schema.
  Engine improvements = new pipeline_version, old runs stay interpretable.
- **Derived-at-read metrics:** no utilization/waste columns, ever (F6).
- **Walls:** 15-model pin, I-1 scan over the new writers, ADR-F isolation
  scans, the crafted-overlap verifier test.

## Intentionally deferred (not defects)
ADR-B worker (async generation) · holes-aware nesting · deeper SVGnest
search profiles · multi-width sweeps · on-fold generation (needs
annotation-era fold edges) · views.py mechanical split.

## Risks & standing answers
| Risk | Answer |
|---|---|
| Theory-vs-reality benchmark gamed by optimistic theory | promotion evidence is labeled; the promoted marker's OWN outcomes become its real judgment on the Yield Board |
| Engine quality plateau | search depth/timebox are levers on a frozen contract; P0 numbers (75–80% util on real sets) are the calibration |
| Node runtime absent at deploy | honest degradation to BLF floor + recorded error; node enters the deploy runbook (MANIFEST) |
| Sync request length | timeboxed; ADR-B lever pre-designed |

## Readiness statement
patterns_ai 147/147 · full serial suite green · migrations clean ·
contracts unchanged · walls green · browser-proven end-to-end incl. the
refusal paths. **Safe to freeze. Checkpoint commit remains the owner's.**
