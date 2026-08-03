# P3 COMPLETION REPORT — Marker Generation & Optimization era (2026-07-07)

**Status: ✅ PHASE 3 COMPLETE — one coherent milestone as ordered. STOPPED.
Phase 4 (AI Pattern Intelligence) will NOT start without explicit owner
approval.**

Companions: [P3_ENGINEERING_REVIEW](P3_ENGINEERING_REVIEW.md) ·
[P3_REGRESSION_REPORT](P3_REGRESSION_REPORT.md) ·
[P3_FREEZE_RECOMMENDATION](P3_FREEZE_RECOMMENDATION.md) ·
[P4_READINESS_REPORT](P4_READINESS_REPORT.md)

## 1. Executive summary

The factory can now **generate markers automatically** from its confirmed
geometry, compare engine candidates honestly, and promote a winner into
the frozen P1 Marker Library — where real usage and outcomes then measure
it against reality. The owner's core principle is enforced in code:
**a generated marker that does not beat the manual baseline cannot be
promoted**, and every promotion carries labeled evidence
(THEORY vs RECORDED REALITY).

Every ordered item is live:

| Ordered | Delivered |
|---|---|
| Automatic marker generation | `start_run` → isolated engines → immutable run + candidates |
| Fabric width selection | per-run `usable_width_mm` (300–3000 bounds), width-band-aware benchmark |
| Grain constraints | pieces nest grain-along-lay; rotations restricted to 0°/180° |
| Fold constraints | on-fold pieces REFUSE honestly by name (fold-edge semantics = annotation era; no silent guessing) |
| Pair constraints | `is_pair` pieces auto-instantiate mirrored (2×/garment) |
| Rotation constraints | allow_180 per piece; engines never rotate off-grain |
| Margin handling | inter-piece spacing (clipper offset / mask buffer, default 3 mm) |
| Collision detection | INDEPENDENT shapely verification of every candidate: pairwise overlap + width containment + true length — engine claims never trusted |
| Piece placement engine | BLF grid bottom-left-fill (deterministic floor, always available) |
| Nesting/packing engine | real NFP nesting via SVGnest core (Minkowski/Clipper NFPs + PlacementWorker) |
| SVGnest = primary | vendored @1248dc2 (MIT) into `compute/patterns_ai/vendor/`, driven headless by `nest_runner.js` (node), seeded + timeboxed |
| BLF fallback | always runs; also the honest answer when node is absent |
| Multiple candidates | `engine=auto` returns every complete verified layout |
| Candidate comparison | run page: length / utilization / waste / per-garment / verify badge, shortest-first |
| Marker scoring | derived-at-read metrics (F6 — NO metric columns exist, schema-asserted by test) |
| Fabric utilization | Σ placed piece areas ÷ (length × width), from the SAME stored rings the cutter would use |
| Waste calculation | 100 − utilization, derived |
| Benchmark vs manual | best ACTUAL avg m/100 among non-generated markers (width-band first, labeled fallback) vs candidate THEORETICAL m/100 — apples-to-oranges stated everywhere |
| Promotion workflow | human-only; refuses unverified layouts, double promotion, and does-not-beat verdicts; evidence frozen into the marker's creation event |
| Candidate history | append-only runs + candidates per product (recent-runs table) |
| Marker versioning | promoted markers are ordinary P1 markers: reference, lineage, supersede, benchmarked_against, biography — all inherited FREE from frozen P1 |
| Browser UI | generate form · run comparison · candidate detail · promotion — canon, @390-first |
| Visualization | `marker_svg`: fabric + color-per-piece layout with tooltips; downloadable SVG export |
| SVG export | `candidates/<pk>/svg/` attachment |
| Testing | +19 tests (147 app; full serial suite green) — real engines, real node |
| Docs + reviews + reports | this package + MANIFEST/GUIDE/index updates |

## 2. Architecture (constitution intact)

- **Isolation (ADR-F):** nesting runs in the SAME isolated runtime as P2
  CV (`nest.py`; node subprocess inside it). Django still imports zero
  engine code; walls re-verified.
- **Single writer:** `marker_generation_service` owns runs/candidates and
  the promotion path; the Marker itself is born through `marker_service`
  (extended additively: `candidate` + `benchmark_evidence` — a GENERATED
  marker REQUIRES its candidate, any other origin refuses one; D11).
- **Append-only:** runs + candidates guard save/delete; refusals recorded
  (`run.errors`, refused promotions raise with numbers).
- **Consumes frozen truth only:** `collect_confirmed_geometry` reads the
  LATEST CONFIRMED version per piece, names every missing piece/size,
  never touches P2 rows. Run params snapshot the exact
  `geometry_row_id`s = full reproducibility spine.
- **Derived at read:** utilization/waste/per-garment/theoretical-m-per-100
  have no columns; pure-python polygon math in Django (no shapely — the
  CV-stack wall holds).

## 3. Live browser proof (screenshots archived)

Real UI walk on LOWER: generate form (ratio S×4, width 900, auto) →
**Run #1: svgnest 101.0 mm (65.68% util) beats blf 102.5 mm (64.72%),
both independently verified PASS** → candidate detail: layout
visualization (4 pieces on fabric), stat chips, **benchmark: "Beats the
manual baseline — theory 2.53 m/100 vs MRK-000002 recorded reality
96.00 m/100 (n=1)"** with the THEORY-vs-REALITY label → promoted as
**MRK-000003** → marker detail (P1 page, free) → **Yield Board shows
MRK-000003 beside the manual marker with honest "— (no facts yet)"** —
reality measurement begins the day it is first used.
`p3_run_{desktop,390}` · `p3_candidate_{desktop,390}` ·
`p3_generate_390` · `p3_promoted_marker_desktop` ·
`p3_yield_with_generated_390`.

## 4. Test summary (patterns_ai **147/147**; +19 P3)

Real-engine goldens: auto-run produces ≥1 verified candidate (pair
handling: 3 pieces/garment asserted) · BLF byte-deterministic across runs ·
width-too-small refuses honestly with NO run row · **crafted overlapping
layout FAILS the independent verifier** (the verifier itself is verified) ·
DXF-style reproducibility params pinned. Service: ratio/width/permission
validations · missing-geometry refusals NAME the pieces · on-fold refusal
NAMES the piece · run+candidate immutability · metrics derived (schema
asserts no metric columns; math cross-checked against hand-computed
area/length) · benchmark verdicts: no_baseline (promotes, honest evidence)
/ does_not_beat (promotion REFUSED, no marker created) / beats (promotes,
`benchmarked_against` set, evidence in the creation event with THEORY
label) · unverified candidates never promote · candidates promote ONCE ·
**promoted marker flows through frozen P1 machinery: usage → outcome →
appears on the Yield Board with real derived metrics** (the era's whole
point, asserted). Views: permission sweep (403/302), tampered ids 404,
generate-via-UI → run page renders derived numbers + PASS badge,
candidate SVG download, promote-via-UI. One conscious P1-test rework:
Block-2B's generated-marker test now supplies a candidate (the new D11
rule) — documented in the test.

## 5. Honest limitations

- Generation is SYNCHRONOUS with a timebox (≤ ~20 s + node startup) —
  right at factory volume; the ADR-B worker remains the designed lever
  when volume demands it (nothing forecloses it; recorded as a conscious
  scope decision, not a violation — the owner's P3 order contained no
  async item).
- On-fold pieces refuse (annotation-era fold-edge semantics needed first).
- SVGnest search is GA-lite (seeded shuffles + rotation sampling,
  ≤201 trials/timebox) — P0-calibrated; more search = better markers
  later, same artifact.
- Benchmark compares theory to reality BY DESIGN and says so everywhere;
  the real test is the promoted marker's own recorded outcomes.
- Multi-width sweep (one run per width) and holes-aware nesting
  (holes stored, engines nest outer rings only) are future levers.

## 6. What P4 stands on

Immutable candidate evidence chains, benchmark verdict data, the decision
spine (SuggestionEvent, still schema-only), and a Marker Library where
generated and manual markers accumulate comparable REALITY (m/100 with
honest n) — exactly the feedback data an assistant era needs.
