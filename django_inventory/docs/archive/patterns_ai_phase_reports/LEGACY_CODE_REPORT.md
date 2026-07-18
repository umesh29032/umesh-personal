> **ARCHIVED 2026-07-13** — shipped-phase report/review (patterns_ai). Live truth: [PLATFORM_STATUS](../../AI_PATTERN_INTELLIGENCE/PLATFORM_STATUS.md) + [PRODUCT_VISION_V2](../../AI_PATTERN_INTELLIGENCE/PRODUCT_VISION_V2.md) + the app [GUIDE](../../apps/patterns_ai/GUIDE.md). Kept for history (Phase-7 DOCCLEAN-D, D-OR-1). Outbound links reflect its era.

# LEGACY CODE REPORT (2026-07-07) — classification only, NOTHING removed

Scope: `config/patterns_ai/**` + `compute/patterns_ai/**` + the two
production touch points. Criterion: does it serve
Photo → Geometry → Verify → Library → Generate → Editor → Optimize →
Save → Export?

## 1. ACTIVE (the product — used by the workflow every day)

**Models (9 of 15):** CalibrationMat + CalibrationMatCheck ·
CaptureAsset · PatternPiece + PatternPieceVersion · PieceSizeGeometry ·
GeometryExtraction · MarkerGenerationRun + GeneratedMarkerCandidate.
**Services:** capture_service · calibration_service ·
pattern_geometry_service · marker_generation_service (generation +
verify + optimize + save_manual_layout) · compute_bridge · svg_render ·
units.
**Views/templates/URLs:** home · mats (list/detail/register/commission/
recheck/retire) · capture wizard · extraction annotator · piece
library/detail/form · version detail/confirm/reject/next · geometry
editor/svg/dxf/print · dxf import · generate + run + layout pages +
layout SVG · **workspace (the layout editor + optimize + undo/redo)**.
**Compute runtime (all of it):** synth/calibrate/extract/dxf_io/nest
(+verify+optimize ops), vendored SVGnest, lockfile, manifest.
**Ops:** patterns_ai_health · verify_patterns_media · seed command ·
D7 protocol · runbook.
**Tests:** purity/walls + p2/p3(generation-core)/phase4/phase5 suites.

## 2. LEGACY but still referenced (frozen; nothing in ACTIVE breaks without review)

| Code | Referenced by | Note |
|---|---|---|
| **Marker model** (+ MRK refs, status machine) | `Marker.candidate` FK; **promotion path** in marker_generation_service; legacy pages | the "Save Marker for production" concept will map HERE (integration design) — NOT removable |
| marker_service (create/transition) | promotion; legacy marker pages | single-writer for Marker — stays with Marker |
| marker_feedback_service + MarkerUsage/MarkerOutcome | legacy usage/outcome pages; **advisor/insights read them**; yield board | production-memory era; no ACTIVE caller |
| marker_query_service | legacy pages + advisor/insights | read-only |
| MarkerTransitionEvent | marker_service emissions | rides Marker |
| **benchmark/beats-baseline gate inside promotion** | promote_candidate | depends on outcome data; candidate for simplification when "Save Marker" is redefined (owner decision) |
| advisor_service + suggestion_service + SuggestionEvent | AdvisorView only | off-roadmap surface, live URL |
| intelligence_service | InsightsView only | off-roadmap surface, live URL |
| Legacy pages/templates: marker list/detail/manual-create/usage/outcome/void, yield_board, advisor, insights (+ their ~14 URLs of the 37) | direct URLs; tests | removed from home nav in the cleanup pass; pages remain live |
| Adda-detail 3 links (production template) | adda_detail.html | ERP-era entry points; harmless text |
| P1 tests (94) covering the above | CI value: freeze walls | keep while the code exists |

## 3. UNUSED (no runtime reference at all)

**Effectively none.** Every module is reachable from a live URL, a
service call, or the promotion path; every model has rows or FKs.
Closest to unused:
- `pattern_geometry_service` has no dead functions; `marker_feedback_
  service.update_outcome_facts` is service-only (no UI ever) — callable
  but caller-less outside tests.
- `poc/patterns_ai/` — non-production reference harness (kept
  deliberately as executable documentation).
- Legacy DEV data rows (MRK-000001/2/3, suggestion #1, insights history)
  — data, not code.

## 4. Dependency chain for any future removal (owner decisions, NOT actions)

Removing the marker-memory stack would need, in order: ① redefine
"Save Marker" for production use (integration design maps it onto the
Marker container — likely KEEP Marker, simplify promotion by dropping
the beats-baseline gate) → ② retire advisor/insights/yield/usage
surfaces (URL + template + service + their tests) → ③ then
MarkerUsage/MarkerOutcome/SuggestionEvent become droppable (migrations +
pin 15→n). Until decided: everything stays frozen and green (225 app
tests).

**No code was removed or changed by this report. STOPPED.**
